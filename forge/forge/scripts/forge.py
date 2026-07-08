#!/usr/bin/env python3
"""forge — 工程流水线的脚手架与产物校验 CLI（forge 技能套件的功能层）。

子命令：
  init      在目标项目创建 .forge/ 工程记忆骨架
  new       创建在途变更 .forge/changes/<slug>/（--full 附 spec.md 与 plan.md）
  list      列出在途变更与任务进度
  check     机械校验变更产物（delta 语法与 specs 对照/任务格式/台账对账/占位符/澄清残留）
  merge     把 spec delta 按 ADDED/MODIFIED/REMOVED/RENAMED 语义合并进 .forge/specs/（幂等）
  recall    按关键词检索工程记忆（lessons/standards/specs/glossary/archive）
  archive   归档已完成变更（会校验 delta 已合并；日期前缀移入 changes/archive/）
  status    工程记忆总览与健康提示

仅用标准库；除 init/new/merge/archive 外全部只读。
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "references" / "templates"

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
CLARIFY_RE = re.compile(r"\[NEEDS CLARIFICATION", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\b(?:TBD|TKTK)\b|待定|待补充|\?\?\?")
CHECKBOX_RE = re.compile(r"^\s*- \[([ xX])\]\s*(.*)$")
TASK_ID_RE = re.compile(r"^T\d+\b")
VERIFY_RE = re.compile(r"(?:→|->)\s*(?:验证|verify)", re.IGNORECASE)
REQUIREMENT_RE = re.compile(r"^### Requirement:\s*(.+)$")
SCENARIO_OK_RE = re.compile(r"^#### Scenario:")
SCENARIO_FUZZY_RE = re.compile(r"^#+\s*Scenario\b", re.IGNORECASE)
MUST_RE = re.compile(r"\bMUST\b|\bSHALL\b|必须")
PRIORITY_SUFFIX_RE = re.compile(r"\s*\(P\d\)\s*$")
BRACKET_TOKEN_RE = re.compile(r"\[([^\[\]]{2,})\]")
RENAME_FROM_RE = re.compile(r"FROM:\s*`?(?:###\s*Requirement:\s*)?([^`]+?)`?\s*$")
RENAME_TO_RE = re.compile(r"TO:\s*`?(?:###\s*Requirement:\s*)?([^`]+?)`?\s*$")
DELTA_SECTIONS = ("ADDED", "MODIFIED", "REMOVED", "RENAMED")


def die(msg: str, code: int = 2):
  print(f"forge: {msg}", file=sys.stderr)
  sys.exit(code)


def today() -> str:
  return dt.date.today().isoformat()


def git_toplevel(start: Path):
  try:
    out = subprocess.run(
      ["git", "rev-parse", "--show-toplevel"],
      cwd=start, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return Path(out) if out else None
  except (subprocess.CalledProcessError, FileNotFoundError):
    return None


def find_forge_root(start: Path):
  """从 start 向上找最近的 .forge/ 目录。"""
  cur = start.resolve()
  for p in (cur, *cur.parents):
    cand = p / ".forge"
    if cand.is_dir():
      return cand
  return None


def require_forge_root() -> Path:
  root = find_forge_root(Path.cwd())
  if root is None:
    die("当前目录（含上级）没有 .forge/。先运行: forge init")
  return root


def read_text(path: Path) -> str:
  return path.read_text(encoding="utf-8", errors="replace")


def render_template(name: str, mapping: dict) -> str:
  src = TEMPLATES_DIR / name
  if not src.is_file():
    die(f"模板缺失: {src}")
  text = read_text(src)
  for key, val in mapping.items():
    text = text.replace("{{" + key + "}}", val)
  return text


def write_if_absent(dest: Path, content: str) -> bool:
  if dest.exists():
    return False
  dest.parent.mkdir(parents=True, exist_ok=True)
  dest.write_text(content, encoding="utf-8")
  return True


def is_guidance_line(line: str) -> bool:
  """模板/文档里的引导行（blockquote、HTML 注释）不参与残留检查。"""
  s = line.lstrip()
  return s.startswith(">") or s.startswith("<!--")


def template_placeholder_tokens() -> set:
  """从模板文件的非引导行提取 `[占位符]` token。

  check 用它发现未替换的脚手架文案；从模板动态推导，改模板不需要同步任何正则。
  新增模板占位符须用 [方括号] 且不放进引导行（> / <!--），否则不会被查到。
  """
  tokens: set = set()
  if not TEMPLATES_DIR.is_dir():
    return tokens
  for tpl in TEMPLATES_DIR.glob("*.md"):
    for line in read_text(tpl).splitlines():
      if is_guidance_line(line):
        continue
      for m in BRACKET_TOKEN_RE.finditer(line):
        tokens.add(m.group(0))
  return tokens


# ---------------------------------------------------------------- init / new

POINTER_LINE = (
  "- `.forge/` 是本项目的工程记忆：constitution(宪法)、standards(规范)、glossary(术语)、"
  "lessons(过往经验)、specs(现行为规格)、changes(在途变更)。"
  "规划/评审/排障前先检索 lessons 与 standards。"
)


def cmd_init(args) -> int:
  if args.dir:
    target = Path(args.dir).resolve()
    if not target.is_dir():
      die(f"目录不存在: {target}")
  elif args.git_root:
    target = git_toplevel(Path.cwd())
    if target is None:
      die("当前目录不在 git 仓库内，无法使用 --git-root")
  else:
    target = Path.cwd().resolve()
  forge_dir = target / ".forge"
  mapping = {"DATE": today()}
  plan = [
    ("constitution.md", forge_dir / "constitution.md"),
    ("standards-index.md", forge_dir / "standards" / "index.md"),
    ("glossary.md", forge_dir / "glossary.md"),
    ("lessons-readme.md", forge_dir / "lessons" / "README.md"),
    ("specs-readme.md", forge_dir / "specs" / "README.md"),
    ("changes-readme.md", forge_dir / "changes" / "README.md"),
  ]
  (forge_dir / "changes" / "archive").mkdir(parents=True, exist_ok=True)
  created, skipped = [], []
  for tpl, dest in plan:
    (created if write_if_absent(dest, render_template(tpl, mapping)) else skipped).append(dest)
  print(f".forge/ @ {target}")
  for p in created:
    print(f"  新建 {p.relative_to(target)}")
  for p in skipped:
    print(f"  已有 {p.relative_to(target)}（未动）")
  print()
  print("下一步：")
  print("  1. 编辑 .forge/constitution.md 立宪（3-7 条可判定的不可协商原则）")
  print("  2. 在项目 CLAUDE.md / AGENTS.md 里加一行指针（没有指针，记忆就是死档案）：")
  print(f"     {POINTER_LINE}")
  return 0


def cmd_new(args) -> int:
  root = require_forge_root()
  slug = args.slug
  if not SLUG_RE.match(slug):
    die(f"slug 需为 kebab-case（小写字母/数字/短横线开头字母数字）: {slug!r}")
  change_dir = root / "changes" / slug
  if change_dir.exists():
    die(f"变更已存在: {change_dir}")
  level = "large" if args.full else "small"
  mapping = {"SLUG": slug, "DATE": today(), "LEVEL": level}
  files = ["proposal.md", "tasks.md", "progress.md"]
  if args.full:
    files += ["spec.md", "plan.md"]
  for name in files:
    dest = change_dir / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_template(name, mapping), encoding="utf-8")
  print(f"已创建变更 {slug}（{level}）:")
  for name in files:
    print(f"  {change_dir.relative_to(root.parent) / name}")
  print()
  print("下一步：用 forge-spec 技能对齐 WHAT（先检索: forge recall <关键词>）。")
  return 0


# ---------------------------------------------------------------- list

def iter_changes(root: Path):
  changes = root / "changes"
  if not changes.is_dir():
    return
  for p in sorted(changes.iterdir()):
    if p.is_dir() and p.name != "archive":
      yield p


def task_progress(change_dir: Path):
  tasks = change_dir / "tasks.md"
  if not tasks.is_file():
    return 0, 0
  done = total = 0
  for line in read_text(tasks).splitlines():
    m = CHECKBOX_RE.match(line)
    if m:
      total += 1
      if m.group(1) in "xX":
        done += 1
  return done, total


def cmd_list(args) -> int:
  root = require_forge_root()
  rows = []
  for change in iter_changes(root):
    done, total = task_progress(change)
    level = "large" if (change / "plan.md").is_file() or (change / "spec.md").is_file() else "small"
    title = ""
    prop = change / "proposal.md"
    if prop.is_file():
      for line in read_text(prop).splitlines():
        if line.startswith("# "):
          title = line[2:].strip()
          break
    if title == change.name:
      title = ""
    flag = "  [✔ 全部完成，可走归档]" if total and done == total else ""
    rows.append((change.name, level, f"{done}/{total}", title, flag))
  if not rows:
    print("没有在途变更。新建: forge new <slug> [--full]")
    return 0
  width = max(len(r[0]) for r in rows)
  for name, level, prog, title, flag in rows:
    print(f"{name:<{width}}  {level:<5}  {prog:>7}  {title}{flag}".rstrip())
  return 0


# ------------------------------------------- spec delta 解析（check/merge/archive 共用）

def norm_title(t: str) -> str:
  """标题归一化：空白不敏感、忽略尾部 (Pn) 优先级标注。"""
  return re.sub(r"\s+", " ", PRIORITY_SUFFIX_RE.sub("", t.strip()))


def parse_spec_blocks(text: str) -> dict:
  """把 spec 文本切成 Requirement 块与 RENAMED 对。

  返回 {blocks, renames, n_from, n_to}；block 含 section（delta 段名或 None）、
  title、norm、start/end（行号半开区间）、lines。
  """
  lines = text.splitlines()
  blocks: list = []
  froms: list = []
  tos: list = []
  section = None
  cur = None

  def close(idx: int):
    nonlocal cur
    if cur is not None:
      cur["end"] = idx
      cur["lines"] = lines[cur["start"]:idx]
      blocks.append(cur)
      cur = None

  for i, line in enumerate(lines):
    if line.startswith("## "):
      close(i)
      head = line[3:].strip().split()
      section = head[0] if head and head[0] in DELTA_SECTIONS else None
      continue
    m = REQUIREMENT_RE.match(line)
    if m:
      close(i)
      cur = {"section": section, "title": m.group(1).strip(),
             "norm": norm_title(m.group(1)), "start": i, "end": 0, "lines": []}
      continue
    if section == "RENAMED" and cur is None:
      mf = RENAME_FROM_RE.search(line)
      if mf:
        froms.append(norm_title(mf.group(1)))
      mt = RENAME_TO_RE.search(line)
      if mt:
        tos.append(norm_title(mt.group(1)))
  close(len(lines))
  return {"blocks": blocks, "renames": list(zip(froms, tos)),
          "n_from": len(froms), "n_to": len(tos)}


def specs_files(root: Path):
  return [p for p in sorted((root / "specs").glob("**/*.md")) if p.name != "README.md"]


def build_specs_index(root: Path) -> dict:
  """norm_title → (path, block)。specs 内不应重名；重名时保留最先命中的。"""
  index: dict = {}
  for path in specs_files(root):
    for b in parse_spec_blocks(read_text(path))["blocks"]:
      index.setdefault(b["norm"], (path, b))
  return index


def norm_block(lines) -> tuple:
  """块内容归一化，用于判断 MODIFIED 是否已合并 / 是否 no-op。"""
  out = []
  for idx, raw in enumerate(lines):
    s = raw.strip()
    if not s:
      continue
    if idx == 0 and s.startswith("### Requirement:"):
      s = "### Requirement: " + norm_title(s[len("### Requirement:"):])
    out.append(s)
  return tuple(out)


# ---------------------------------------------------------------- check

class Report:
  def __init__(self):
    self.fails: list = []
    self.warns: list = []
    self.oks: list = []

  def fail(self, msg: str):
    self.fails.append(msg)

  def warn(self, msg: str):
    self.warns.append(msg)

  def ok(self, msg: str):
    self.oks.append(msg)


def check_proposal(path: Path, rep: Report):
  if not path.is_file():
    rep.fail("proposal.md 缺失（任何变更至少要有 proposal + tasks）")
    return
  text = read_text(path)
  if "## Why" not in text:
    rep.warn("proposal.md: 缺「## Why」（为什么做、为什么是现在）")
  if "成功标准" not in text:
    rep.warn("proposal.md: 缺「成功标准」（可度量、技术无关）")
  if "Out of Scope" not in text and "不做" not in text:
    rep.warn("proposal.md: 缺「Out of Scope」（明确不做什么）")
  rep.ok("proposal.md 存在")


def check_spec(path: Path, rep: Report) -> dict:
  text = read_text(path)
  lines = text.splitlines()
  for i, line in enumerate(lines, 1):
    if SCENARIO_OK_RE.match(line):
      continue
    if SCENARIO_FUZZY_RE.match(line):
      rep.fail(f"spec.md:{i} Scenario 标题格式/层级错误（必须恰好 `#### Scenario:`，否则场景不计数、归档合并会丢内容）")
      continue
    if line.startswith("## "):
      title = line[3:].strip()
      if title and not title.startswith(DELTA_SECTIONS):
        rep.warn(f"spec.md:{i} 非标准 delta 段「{title}」（应为 ADDED/MODIFIED/REMOVED/RENAMED Requirements）")

  delta = parse_spec_blocks(text)
  for b in delta["blocks"]:
    lineno = b["start"] + 1
    body = b["lines"][1:]
    if not any(SCENARIO_OK_RE.match(x) for x in body):
      rep.fail(f"spec.md:{lineno} Requirement「{b['title']}」没有任何 #### Scenario")
    desc = []
    for x in body:
      if SCENARIO_OK_RE.match(x):
        break
      desc.append(x)
    if not any(MUST_RE.search(x) for x in desc):
      rep.warn(f"spec.md:{lineno} Requirement「{b['title']}」描述缺 MUST/SHALL/必须 句式")
    if b["section"] == "REMOVED":
      blob = "\n".join(body)
      if "Reason" not in blob or "Migration" not in blob:
        rep.warn(f"spec.md:{lineno} REMOVED「{b['title']}」缺 Reason（为何废弃）/ Migration（存量怎么办）")
  if delta["n_from"] != delta["n_to"]:
    rep.warn(f"spec.md: RENAMED 段 FROM/TO 数量不匹配（{delta['n_from']} vs {delta['n_to']}）")
  if not delta["blocks"] and not delta["renames"]:
    rep.warn("spec.md: 没有任何「### Requirement:」（空 delta？small 变更可以删掉本文件）")
  else:
    extra = f" + {len(delta['renames'])} 条改名" if delta["renames"] else ""
    rep.ok(f"spec.md: 解析到 {len(delta['blocks'])} 条 Requirement{extra}")
  return delta


def check_delta_vs_specs(delta: dict, rep: Report, root: Path):
  added = [b for b in delta["blocks"] if b["section"] == "ADDED"]
  modified = [b for b in delta["blocks"] if b["section"] == "MODIFIED"]
  removed = [b for b in delta["blocks"] if b["section"] == "REMOVED"]
  renames = delta["renames"]
  for b in delta["blocks"]:
    if b["section"] is None:
      rep.fail(f"spec.md:{b['start'] + 1} Requirement「{b['title']}」不在任何标准 delta 段内——归档合并不知道拿它怎么办")
  index = build_specs_index(root)
  # 逐项收集证据：merged 票 / unmerged 票 / 永远是错的
  votes_merged = votes_unmerged = 0
  added_present, removed_absent = [], []
  modified_missing, modified_match = [], []
  renames_broken = []
  for b in added:
    if b["norm"] in index:
      votes_merged += 1
      added_present.append(b)
    else:
      votes_unmerged += 1
  for b in removed:
    if b["norm"] in index:
      votes_unmerged += 1
    else:
      removed_absent.append(b)  # 已合并 or 从未存在——本身不投票
  for f, t in renames:
    if f in index:
      votes_unmerged += 1
    elif t in index:
      votes_merged += 1
    else:
      renames_broken.append((f, t))
  for b in modified:
    hit = index.get(b["norm"])
    if hit is None:
      modified_missing.append(b)
    elif norm_block(hit[1]["lines"]) == norm_block(b["lines"]):
      votes_merged += 1
      modified_match.append(b)
    else:
      votes_unmerged += 1
  for b in modified_missing:
    rep.fail(f"spec.md:{b['start'] + 1} MODIFIED「{b['title']}」在 specs/ 找不到——合并会落空（若它由其他在途变更新增，先归档那个变更）")
  for f, t in renames_broken:
    rep.fail(f"spec.md: RENAMED「{f}」→「{t}」两个标题都不在 specs/——FROM 写错了？")
  if votes_merged and not votes_unmerged and not modified_missing and not renames_broken:
    rep.ok("delta 已合并进 specs/（待归档状态）")
    return
  # 未合并（前置阶段的正常状态）——按未合并语义报错；RENAMED FROM 存在即正常，无需报
  for b in added_present:
    rep.fail(f"spec.md:{b['start'] + 1} ADDED「{b['title']}」与 specs/ 现有 Requirement 撞名——改行为用 MODIFIED；若 delta 已部分合并，补跑 forge merge")
  for b in removed_absent:
    rep.fail(f"spec.md:{b['start'] + 1} REMOVED「{b['title']}」在 specs/ 找不到——删除会落空（写错标题？若确已合并过可忽略）")
  for b in modified_match:
    rep.warn(f"spec.md:{b['start'] + 1} MODIFIED「{b['title']}」与 specs/ 现状完全相同（已合并过，或 no-op 修改）")


def check_cross_change(delta: dict, rep: Report, root: Path, slug: str):
  mine = {b["norm"] for b in delta["blocks"]} | {f for f, _ in delta["renames"]}
  if not mine:
    return
  hits = []
  for other in iter_changes(root):
    if other.name == slug or not (other / "spec.md").is_file():
      continue
    theirs = parse_spec_blocks(read_text(other / "spec.md"))
    names = {b["norm"] for b in theirs["blocks"]} | {f for f, _ in theirs["renames"]}
    hits.extend((t, other.name) for t in sorted(mine & names))
  for t, name in hits[:5]:
    rep.warn(f"Requirement「{t}」同时出现在在途变更「{name}」的 delta 里——后归档会覆盖先归档，需协调顺序")
  if len(hits) > 5:
    rep.warn(f"…另有 {len(hits) - 5} 处跨变更撞名")


def check_plan(path: Path, rep: Report):
  if not path.is_file():
    return
  lines = read_text(path).splitlines()
  filled = 0
  in_alt = has_body = False
  for line in lines:
    if re.match(r"^### 方案", line):
      filled += 1 if (in_alt and has_body) else 0
      in_alt, has_body = True, False
      continue
    if line.startswith("## ") or re.match(r"^### (?!方案)", line):
      filled += 1 if (in_alt and has_body) else 0
      in_alt = False
      continue
    if in_alt and line.strip() and not is_guidance_line(line):
      has_body = True
  filled += 1 if (in_alt and has_body) else 0
  if filled < 2:
    rep.warn("plan.md: 有实质内容的候选方案不足 2 个（空标题不算；须「最小可行」与「理想架构」同权对比）")
  text = "\n".join(lines)
  if "Constitution" not in text and "宪法" not in text:
    rep.warn("plan.md: 缺 Constitution Check（逐条对照 .forge/constitution.md）")
  rep.ok("plan.md 存在")


def check_tasks(path: Path, rep: Report) -> list:
  if not path.is_file():
    rep.fail("tasks.md 缺失")
    return []
  lines = read_text(path).splitlines()
  total = done = no_id = 0
  no_verify = []
  checked_ids = []
  for i, line in enumerate(lines, 1):
    m = CHECKBOX_RE.match(line)
    if not m:
      continue
    total += 1
    desc = m.group(2)
    tid = TASK_ID_RE.match(desc)
    if m.group(1) in "xX":
      done += 1
      if tid:
        checked_ids.append(tid.group(0))
    if not VERIFY_RE.search(desc):
      no_verify.append(i)
    if not tid:
      no_id += 1
  if total == 0:
    rep.fail("tasks.md: 没有任何任务（须用 `- [ ]` checkbox 格式，否则进度无法追踪）")
    return []
  if no_verify:
    shown = ", ".join(str(n) for n in no_verify[:5])
    more = "…" if len(no_verify) > 5 else ""
    rep.fail(f"tasks.md: {len(no_verify)} 个任务缺「→ 验证:」（行 {shown}{more}）——不可验证的步骤不是步骤")
  if no_id:
    rep.warn(f"tasks.md: {no_id} 个任务缺 Txx 稳定编号（台账与评审靠它追溯）")
  rep.ok(f"tasks.md: {done}/{total} 已完成")
  return checked_ids


def check_ledger(change_dir: Path, checked_ids: list, rep: Report):
  if not checked_ids:
    return
  progress = change_dir / "progress.md"
  logged = set(re.findall(r"\bT\d+\b", read_text(progress))) if progress.is_file() else set()
  missing = [t for t in checked_ids if t not in logged]
  if missing:
    shown = ", ".join(missing[:5]) + ("…" if len(missing) > 5 else "")
    rep.warn(f"progress.md: {len(missing)} 个已勾任务没有台账证据行（{shown}）——台账即真相，光勾选不算")


def check_residue(change_dir: Path, rep: Report):
  clarify_hits, placeholder_hits, template_hits = [], [], []
  tokens = template_placeholder_tokens()
  for md in sorted(change_dir.glob("*.md")):
    for i, line in enumerate(read_text(md).splitlines(), 1):
      if is_guidance_line(line):
        continue
      if CLARIFY_RE.search(line):
        clarify_hits.append(f"{md.name}:{i}")
      if PLACEHOLDER_RE.search(line):
        placeholder_hits.append(f"{md.name}:{i}")
      if any(tok in line for tok in tokens):
        template_hits.append(f"{md.name}:{i}")
  for hit in clarify_hits:
    rep.fail(f"{hit} 残留 [NEEDS CLARIFICATION]——澄清完才准进 build")
  for hit in placeholder_hits[:5]:
    rep.warn(f"{hit} 占位符（TBD/待定/???）——写具体值或删掉")
  if len(placeholder_hits) > 5:
    rep.warn(f"…另有 {len(placeholder_hits) - 5} 处占位符")
  for hit in template_hits[:5]:
    rep.warn(f"{hit} 模板占位符未替换（[能力名]/[命令]/[示例任务…]）——脚手架不是产物")
  if len(template_hits) > 5:
    rep.warn(f"…另有 {len(template_hits) - 5} 处模板占位符")


def cmd_check(args) -> int:
  root = require_forge_root()
  change_dir = root / "changes" / args.slug
  if not change_dir.is_dir():
    die(f"变更不存在: {change_dir}")
  rep = Report()
  const = root / "constitution.md"
  if not const.is_file():
    rep.warn(".forge/constitution.md 缺失（forge init 可补）")
  elif "[原则名]" in read_text(const):
    rep.warn("constitution.md 仍是模板占位——先立宪再开工")
  check_proposal(change_dir / "proposal.md", rep)
  if (change_dir / "spec.md").is_file():
    delta = check_spec(change_dir / "spec.md", rep)
    check_delta_vs_specs(delta, rep, root)
    check_cross_change(delta, rep, root, args.slug)
  check_plan(change_dir / "plan.md", rep)
  checked_ids = check_tasks(change_dir / "tasks.md", rep)
  check_ledger(change_dir, checked_ids, rep)
  check_residue(change_dir, rep)
  for msg in rep.oks:
    print(f"  OK   {msg}")
  for msg in rep.warns:
    print(f"  WARN {msg}")
  for msg in rep.fails:
    print(f"  FAIL {msg}")
  print()
  if rep.fails:
    print(f"check 未通过: {len(rep.fails)} FAIL / {len(rep.warns)} WARN")
    return 1
  if args.strict and rep.warns:
    print(f"check(--strict) 未通过: {len(rep.warns)} WARN")
    return 1
  print(f"check 通过: 0 FAIL / {len(rep.warns)} WARN")
  return 0


# ---------------------------------------------------------------- recall

def recall_targets(root: Path):
  targets = []
  for pattern in ("lessons/**/*.md", "standards/**/*.md", "specs/**/*.md"):
    targets.extend(root.glob(pattern))
  glossary = root / "glossary.md"
  if glossary.is_file():
    targets.append(glossary)
  targets.extend((root / "changes" / "archive").glob("**/*.md"))
  return [t for t in targets if t.name != "README.md"]


def frontmatter_end(lines) -> int:
  if lines and lines[0].strip() == "---":
    for j in range(1, min(len(lines), 40)):
      if lines[j].strip() == "---":
        return j
  return 0


def cmd_recall(args) -> int:
  root = require_forge_root()
  keywords = [k.lower() for k in args.keywords]
  scored = []
  for path in recall_targets(root):
    lines = read_text(path).splitlines()
    fm_end = frontmatter_end(lines)
    rel_parts = [part.lower() for part in path.relative_to(root).parts]
    score = 0
    snippets = []
    snippet_lines = set()
    for kw in keywords:
      if any(kw in part for part in rel_parts):
        score += 4
      hits_fm = hits_head = hits_body = 0
      for i, line in enumerate(lines):
        if kw not in line.lower():
          continue
        if fm_end and i <= fm_end and hits_fm < 2:
          score += 3
          hits_fm += 1
        elif line.lstrip().startswith("#") and hits_head < 2:
          score += 2
          hits_head += 1
        elif hits_body < 3:
          score += 1
          hits_body += 1
        else:
          continue
        if len(snippets) < 3 and i not in snippet_lines:
          snippet_lines.add(i)
          snippets.append(f"{i + 1}: {line.strip()[:110]}")
    if score > 0:
      scored.append((score, path, snippets))
  if not scored:
    print(f"没有命中（关键词: {' '.join(args.keywords)}）。可能还没沉淀过这类经验。")
    return 0
  scored.sort(key=lambda t: (-t[0], str(t[1])))
  base = root.parent
  for score, path, snippets in scored[: args.top]:
    print(f"[{score:>2}] {path.relative_to(base)}")
    for s in snippets:
      print(f"       {s}")
  return 0


# ---------------------------------------------------------------- merge

def delta_unmerged_report(root: Path, change_dir: Path) -> list:
  """delta 与 specs/ 的差距清单；空列表 = 无 delta 或已全部合并。"""
  spec_path = change_dir / "spec.md"
  if not spec_path.is_file():
    return []
  delta = parse_spec_blocks(read_text(spec_path))
  index = build_specs_index(root)
  problems = []
  for b in delta["blocks"]:
    if b["section"] == "ADDED" and b["norm"] not in index:
      problems.append(f"ADDED「{b['title']}」尚未出现在 specs/")
    elif b["section"] == "REMOVED" and b["norm"] in index:
      problems.append(f"REMOVED「{b['title']}」仍留在 specs/")
    elif b["section"] == "MODIFIED":
      hit = index.get(b["norm"])
      if hit is None:
        problems.append(f"MODIFIED「{b['title']}」在 specs/ 找不到")
      elif norm_block(hit[1]["lines"]) != norm_block(b["lines"]):
        problems.append(f"MODIFIED「{b['title']}」specs/ 内容与 delta 不一致")
  for f, t in delta["renames"]:
    if f in index or t not in index:
      problems.append(f"RENAMED「{f}」→「{t}」未生效")
  return problems


def cmd_merge(args) -> int:
  root = require_forge_root()
  change_dir = root / "changes" / args.slug
  if not change_dir.is_dir():
    die(f"变更不存在: {change_dir}")
  spec_path = change_dir / "spec.md"
  if not spec_path.is_file():
    print(f"{args.slug} 没有 spec.md（small 变更无 delta），无需合并。")
    return 0
  delta = parse_spec_blocks(read_text(spec_path))
  if not delta["blocks"] and not delta["renames"]:
    print("spec.md 没有可合并的条目。")
    return 0
  loose = [b for b in delta["blocks"] if b["section"] is None]
  if loose:
    die(f"有 {len(loose)} 条 Requirement 不在标准 delta 段内，先跑 forge check {args.slug} 修格式")

  index = build_specs_index(root)
  added = [b for b in delta["blocks"] if b["section"] == "ADDED"]
  modified = [b for b in delta["blocks"] if b["section"] == "MODIFIED"]
  removed = [b for b in delta["blocks"] if b["section"] == "REMOVED"]
  targets = [b["norm"] for b in modified + removed] + [f for f, _ in delta["renames"]]
  dupes = sorted({t for t in targets if targets.count(t) > 1})
  if dupes:
    die(f"同一 Requirement 被多个 delta 操作命中（{'、'.join(dupes[:3])}）——一个变更里每条需求只能有一种操作")

  target_file = None
  if [b for b in added if b["norm"] not in index]:
    caps = sorted({p.parent.name for p in (root / "specs").glob("*/spec.md")})
    if args.capability:
      cap = args.capability
    elif len(caps) == 1:
      cap = caps[0]
    elif not caps:
      die("specs/ 还没有任何 capability，ADDED 需要 --capability <名> 指明目标（specs/<名>/spec.md）")
    else:
      die(f"specs/ 有多个 capability（{', '.join(caps)}），ADDED 需要 --capability 指明")
    target_file = root / "specs" / cap / "spec.md"

  base = root.parent
  actions = []          # (是否实操, 描述)
  edits: dict = {}      # path → [(start, end, new_lines|None)]
  appends = []          # (path, block)

  def trimmed(lines) -> list:
    out = list(lines)
    while out and not out[-1].strip():
      out.pop()
    return out + [""]

  for b in modified:
    hit = index.get(b["norm"])
    if hit is None:
      die(f"MODIFIED「{b['title']}」在 specs/ 找不到，拒绝合并（先 forge check {args.slug} 体检）")
    path, sb = hit
    if norm_block(sb["lines"]) == norm_block(b["lines"]):
      actions.append((False, f"跳过 MODIFIED「{b['title']}」——specs/ 已是该内容"))
    else:
      edits.setdefault(path, []).append((sb["start"], sb["end"], trimmed(b["lines"])))
      actions.append((True, f"MODIFIED「{b['title']}」→ {path.relative_to(base)} 整块替换"))
  for b in removed:
    hit = index.get(b["norm"])
    if hit is None:
      actions.append((False, f"跳过 REMOVED「{b['title']}」——specs/ 里已不存在"))
    else:
      path, sb = hit
      edits.setdefault(path, []).append((sb["start"], sb["end"], None))
      actions.append((True, f"REMOVED 「{b['title']}」→ {path.relative_to(base)} 删除整块"))
  for f, t in delta["renames"]:
    hit = index.get(f)
    if hit is None:
      if t in index:
        actions.append((False, f"跳过 RENAMED「{f}」→「{t}」——看起来已改名"))
      else:
        die(f"RENAMED FROM「{f}」在 specs/ 找不到，拒绝合并")
    else:
      path, sb = hit
      suffix_m = PRIORITY_SUFFIX_RE.search(sb["title"])
      suffix = suffix_m.group(0) if suffix_m else ""
      new_lines = [f"### Requirement: {t}{suffix}"] + list(sb["lines"][1:])
      edits.setdefault(path, []).append((sb["start"], sb["end"], new_lines))
      actions.append((True, f"RENAMED 「{f}」→「{t}」@ {path.relative_to(base)}"))
  for b in added:
    if b["norm"] in index:
      actions.append((False, f"跳过 ADDED「{b['title']}」——specs/ 已有同名（已合并过？）"))
    else:
      appends.append((target_file, b))
      actions.append((True, f"ADDED   「{b['title']}」→ {target_file.relative_to(base)} 追加"))

  for _, desc in actions:
    print(f"  {desc}")
  n_real = sum(1 for real, _ in actions if real)
  if args.dry_run:
    print(f"\n--dry-run：{n_real} 项待执行，未写入。")
    return 0
  for path, edit_list in edits.items():
    lines = read_text(path).splitlines()
    for start, end, new_lines in sorted(edit_list, key=lambda e: -e[0]):
      lines[start:end] = [] if new_lines is None else new_lines
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
  for path, b in appends:
    if path.is_file():
      text = read_text(path).rstrip("\n")
    else:
      path.parent.mkdir(parents=True, exist_ok=True)
      text = f"# {path.parent.name}\n\n## Requirements"
    text += "\n\n" + "\n".join(trimmed(b["lines"])).rstrip("\n") + "\n"
    path.write_text(text, encoding="utf-8")
  print(f"\n合并完成：{n_real} 项（幂等，可重跑）。抽查 specs/ 后 forge archive {args.slug}。")
  return 0


# ---------------------------------------------------------------- archive / status

def cmd_archive(args) -> int:
  root = require_forge_root()
  src = root / "changes" / args.slug
  if not src.is_dir():
    die(f"变更不存在: {src}")
  done, total = task_progress(src)
  if total and done < total and not args.force:
    die(f"{args.slug} 还有 {total - done}/{total} 个任务未完成；确认要归档加 --force")
  problems = delta_unmerged_report(root, src)
  if problems and not args.force:
    for p in problems[:5]:
      print(f"  ! {p}", file=sys.stderr)
    die(f"{args.slug} 的 spec delta 尚未合并进 specs/（先 forge merge {args.slug}；确认无需合并再 --force）")
  dest_dir = root / "changes" / "archive"
  dest_dir.mkdir(parents=True, exist_ok=True)
  dest = dest_dir / f"{today()}-{args.slug}"
  if dest.exists():
    die(f"归档目标已存在: {dest}")
  shutil.move(str(src), str(dest))
  print(f"已归档 → {dest.relative_to(root.parent)}")
  if problems:
    print("注意：delta 未合并即归档（--force）。需要补救就 mv 回 changes/ 再 forge merge。")
  return 0


def cmd_status(args) -> int:
  root = require_forge_root()
  base = root.parent
  const = root / "constitution.md"
  const_state = "缺失"
  if const.is_file():
    const_state = "模板占位（未立宪）" if "[原则名]" in read_text(const) else "已立"
  n_std = sum(
    1 for p in (root / "standards").glob("*.md") if p.name != "index.md"
  ) if (root / "standards").is_dir() else 0
  n_lessons = sum(
    1 for p in (root / "lessons").glob("**/*.md") if p.name != "README.md"
  ) if (root / "lessons").is_dir() else 0
  n_specs = sum(
    1 for p in (root / "specs").glob("**/*.md") if p.name != "README.md"
  ) if (root / "specs").is_dir() else 0
  changes = list(iter_changes(root))
  n_archive = sum(1 for p in (root / "changes" / "archive").glob("*") if p.is_dir())
  print(f"工程记忆 @ {base}")
  print(f"  宪法    : {const_state}")
  print(f"  规范    : {n_std} 个域文件（standards/）")
  print(f"  经验    : {n_lessons} 条 lesson（lessons/）")
  print(f"  规格    : {n_specs} 个能力 spec（specs/，结算真相）")
  print(f"  在途    : {len(changes)} 个变更；已归档 {n_archive} 个")
  for change in changes:
    done, total = task_progress(change)
    print(f"    - {change.name}: {done}/{total}")
  hints = []
  if const_state != "已立":
    hints.append("先立宪：编辑 .forge/constitution.md（3-7 条可判定原则）")
  if n_archive > 0 and n_lessons == 0:
    hints.append("已有归档却没有任何 lesson——复盘被跳过了？收工走 forge-compound")
  for change in changes:
    done, total = task_progress(change)
    if total and done == total:
      hints.append(f"{change.name} 全部任务已完成：评审→复盘→归档（forge archive {change.name}）")
  if hints:
    print("提示：")
    for h in hints:
      print(f"  * {h}")
  return 0


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
  parser = argparse.ArgumentParser(
    prog="forge",
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )
  sub = parser.add_subparsers(dest="cmd", required=True)

  p = sub.add_parser("init", help="创建 .forge/ 工程记忆骨架")
  target = p.add_mutually_exclusive_group()
  target.add_argument("--dir", help="目标项目目录（默认当前目录）")
  target.add_argument("--git-root", action="store_true", help="在当前 git 仓库根目录创建 .forge/")
  p.set_defaults(func=cmd_init)

  p = sub.add_parser("new", help="创建在途变更")
  p.add_argument("slug", help="kebab-case 变更名，如 add-dark-mode")
  p.add_argument("--full", action="store_true", help="大变更：附 spec.md 与 plan.md")
  p.set_defaults(func=cmd_new)

  p = sub.add_parser("list", help="列出在途变更与进度")
  p.set_defaults(func=cmd_list)

  p = sub.add_parser("check", help="机械校验变更产物（确定性质量门）")
  p.add_argument("slug")
  p.add_argument("--strict", action="store_true", help="WARN 也算失败")
  p.set_defaults(func=cmd_check)

  p = sub.add_parser("merge", help="把 spec delta 合并进 .forge/specs/（幂等；ADDED 目标唯一时自动推断）")
  p.add_argument("slug")
  p.add_argument("--capability", help="ADDED 的目标 capability（specs/<名>/spec.md）")
  p.add_argument("--dry-run", action="store_true", help="只打印将执行的操作，不写入")
  p.set_defaults(func=cmd_merge)

  p = sub.add_parser("recall", help="按关键词检索工程记忆")
  p.add_argument("keywords", nargs="+")
  p.add_argument("--top", type=int, default=10, help="最多显示条数（默认 10）")
  p.set_defaults(func=cmd_recall)

  p = sub.add_parser("archive", help="归档已完成变更")
  p.add_argument("slug")
  p.add_argument("--force", action="store_true", help="任务未全勾也归档")
  p.set_defaults(func=cmd_archive)

  p = sub.add_parser("status", help="工程记忆总览与健康提示")
  p.set_defaults(func=cmd_status)

  args = parser.parse_args(argv)
  return args.func(args)


if __name__ == "__main__":
  sys.exit(main())

#!/usr/bin/env python3
"""ui_taste — 前端 AI 味机械检查（判断层见 SKILL.md 与 references/）。

check    静态扫描可确定判定的 AI 味硬信号（启发式：命中是强信号，未命中≠干净）
contrast WCAG 对比度计算与 AA/AAA 判定

规则与 references/anti-slop.md、craft.md 一一对应；每条给 file:line，
critical 存在时退出码 1（可挂 CI）。纯标准库。
"""

import argparse
import json
import os
import re
import sys

EXTS = {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte",
        ".astro", ".css", ".scss", ".mdx"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out",
             "coverage", ".venv", "__pycache__", ".turbo"}
MARKUP_EXTS = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".mdx"}

_CJK = re.compile(r"[一-鿿　-〿＀-￯]")


def _has_cjk(s):
  return bool(_CJK.search(s))


# 每条规则: (id, severity, 适用扩展集或 None=全部, 行级判定函数, 提示)
# severity: critical / major / minor
def _mk_line_rules():
  r = []

  def add(rule_id, sev, exts, pattern, msg, flags=0, exclude=None):
    rx = re.compile(pattern, flags)
    ex = re.compile(exclude) if exclude else None

    def fn(line, _ctx):
      if ex and ex.search(line):
        return False
      return bool(rx.search(line))

    r.append((rule_id, sev, exts, fn, msg))

  # --- critical ---
  add("transition-all", "critical", None,
      r"transition:\s*['\"]?all\b|[\"'\s]transition-all[\"'\s]",
      "禁 transition: all，逐属性列出（craft.md）")
  add("scroll-listener", "critical", None,
      r"addEventListener\(\s*['\"]scroll['\"]",
      "禁 scroll 事件监听：用 useScroll/ScrollTrigger/IntersectionObserver（motion.md）")
  add("user-scalable", "critical", MARKUP_EXTS,
      r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\.0)?[\"',\s]",
      "禁禁用缩放（craft.md 无障碍）")
  add("block-paste", "critical", MARKUP_EXTS,
      r"onPaste\s*=.*preventDefault",
      "禁 blockPaste（craft.md 表单）")
  add("div-onclick", "critical", MARKUP_EXTS,
      r"<(div|span)\b[^>]*\bonClick",
      "div/span 当按钮：改 <button>（craft.md 语义）")
  add("img-no-alt", "critical", MARKUP_EXTS,
      r"<img\b(?![^>]*\balt\s*=)[^>]*>",
      "img 缺 alt（装饰图用 alt=\"\"）（craft.md）")

  # --- major ---
  add("h-screen", "major", None,
      r"\bh-screen\b|height:\s*100vh",
      "全屏高用 min-h-[100dvh]/h-dvh，h-screen/100vh 在 iOS 跳动（craft.md）")
  add("ai-gradient", "major", None,
      r"(from|via|to)-(purple|violet|fuchsia)-\d|gradient[^;\n]{0,60}(purple|violet|#a855f7|#8b5cf6|#7c3aed)",
      "紫系渐变是 AI 印记；品牌确为紫则体系化使用（anti-slop.md）")
  add("gradient-text", "major", None,
      r"bg-clip-text|background-clip:\s*text",
      "渐变文字默认禁：用单色实色，强调靠字重/字号（anti-slop.md）")
  add("arbitrary-z", "major", None,
      r"z-\[?9{3,}|z-index:\s*9{3,}",
      "z-index 用语义梯 10/20/30/40/50/60，禁 999+（tokens.md）")
  add("side-stripe", "major", None,
      r"border-left:\s*[3-9]px\s+solid|[\"'\s]border-l-[48][\"'\s]",
      "侧色条当强调默认禁：整边框/底色 tint/序号（anti-slop.md）")
  add("tabindex-positive", "major", MARKUP_EXTS,
      r"tabindex\s*=\s*[\"']?[1-9]",
      "禁 tabindex>0（craft.md）")
  add("bounce-easing", "major", None,
      r"cubic-bezier\(\s*0?\.68\s*,\s*-0?\.55|back\.(in|out|inOut)|elastic\.(in|out|inOut)",
      "功能 UI 禁 bounce/elastic 缓动（motion.md）")
  add("placeholder-copy", "major", MARKUP_EXTS,
      r"Lorem ipsum|John Doe|Jane Doe|\bAcme\b",
      "占位内容冒充真内容：换有语境的可信名字/文案（anti-slop.md）",
      re.IGNORECASE)

  # --- minor ---
  add("pure-black", "minor", None,
      r"background(-color)?:\s*#000(000)?\b|[\"'\s]bg-black[\"'\s]|bg-\[#000",
      "大面积纯黑改 off-black（#0a0a0a~zinc-950 档）（tokens.md）")
  add("lucide-import", "minor", None,
      r"from\s+['\"]lucide-react['\"]",
      "lucide 是默认反射：优先 Phosphor/Radix/Tabler，除非项目已有（craft.md）")
  add("inter-font", "minor", None,
      r"fonts\.googleapis\.com[^\"']*Inter|next/font[^\n]*Inter|font-family:[^;\n]*\bInter\b",
      "Inter：产品 UI 合法，营销/展示页换有性格的字体（sources.md 裁决）")
  add("dead-link", "minor", MARKUP_EXTS,
      r"href=[\"']#[\"']",
      "假链接：链到真地址或明确禁用态（redesign.md 审计项）")
  add("autofocus", "minor", MARKUP_EXTS,
      r"\bautoFocus\b|\bautofocus\b",
      "autoFocus 仅桌面单主输入框场景（craft.md）")
  add("filler-words", "minor", MARKUP_EXTS,
      r"\b(Elevate|Seamless(ly)?|Unleash|Next-Gen|Revolutioni[sz]e|Game-changer)\b",
      "营销填充词：写具体动词（anti-slop.md 文案）")
  return r


LINE_RULES = _mk_line_rules()
_EMDASH = re.compile(r"[—–]")
_EYEBROW = re.compile(r"uppercase")
_TRACKING = re.compile(r"tracking-(wide|widest|\[)")
_MOTION_HINT = re.compile(r"@keyframes|animation:|animate-\[|motion/react|framer-motion")
_REDUCED = re.compile(r"prefers-reduced-motion|useReducedMotion")
_OUTLINE_NONE = re.compile(r"outline-none|outline:\s*none")
_FOCUS_VISIBLE = re.compile(r"focus-visible|focus:ring|focus:outline")


def scan_file(path):
  """返回 findings: [(line_no, rule_id, severity, message)]"""
  ext = os.path.splitext(path)[1].lower()
  try:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
      lines = fh.read().splitlines()
  except OSError as e:
    return [(0, "read-error", "minor", str(e))]
  out = []
  eyebrow_hits = 0
  for i, line in enumerate(lines, 1):
    for rule_id, sev, exts, fn, msg in LINE_RULES:
      if exts is not None and ext not in exts:
        continue
      if fn(line, None):
        out.append((i, rule_id, sev, msg))
    if ext in MARKUP_EXTS and _EMDASH.search(line):
      if _has_cjk(line):
        out.append((i, "em-dash", "minor",
                    "破折号：中文语境正常标点（克制即可）；若为英文文案则违反零容忍（anti-slop.md）"))
      else:
        out.append((i, "em-dash", "critical",
                    "英文可见文案禁 em/en-dash：改句号/逗号/改写（anti-slop.md 二值禁令）"))
    if _EYEBROW.search(line) and _TRACKING.search(line):
      eyebrow_hits += 1
  if eyebrow_hits > 3:
    out.append((0, "eyebrow-density", "major",
                f"全大写宽 tracking 眉标出现 {eyebrow_hits} 处：配给 ≤ ceil(节数/3)，多数应删（anti-slop.md）"))
  body = "\n".join(lines)
  if _OUTLINE_NONE.search(body) and not _FOCUS_VISIBLE.search(body):
    out.append((0, "outline-none", "major",
                "outline-none 且无 focus-visible 替代：焦点必须可见（craft.md）"))
  if _MOTION_HINT.search(body) and not _REDUCED.search(body):
    out.append((0, "no-reduced-motion", "minor",
                "有动效但未见 prefers-reduced-motion/useReducedMotion 处理（motion.md）"))
  return out


def iter_files(paths):
  for p in paths:
    if os.path.isfile(p):
      if os.path.splitext(p)[1].lower() in EXTS:
        yield p
      continue
    for root, dirs, files in os.walk(p):
      dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
      for f in sorted(files):
        if os.path.splitext(f)[1].lower() in EXTS:
          yield os.path.join(root, f)


def cmd_check(args):
  findings = []
  n_files = 0
  clean = []
  for path in iter_files(args.paths):
    n_files += 1
    hits = scan_file(path)
    if hits:
      for line_no, rule_id, sev, msg in hits:
        findings.append({"file": path, "line": line_no, "rule": rule_id,
                         "severity": sev, "message": msg})
    else:
      clean.append(path)
  counts = {s: sum(1 for f in findings if f["severity"] == s)
            for s in ("critical", "major", "minor")}
  if args.json:
    print(json.dumps({"files_scanned": n_files, "counts": counts,
                      "findings": findings}, ensure_ascii=False, indent=2))
  else:
    by_file = {}
    for f in findings:
      by_file.setdefault(f["file"], []).append(f)
    for path, fs in by_file.items():
      print(path)
      for f in sorted(fs, key=lambda x: x["line"]):
        loc = f["line"] if f["line"] else "-"
        print(f"  {loc:>4}  [{f['severity']}] {f['rule']}: {f['message']}")
    if not findings:
      print("✓ 未命中任何机械规则（启发式：不等于没有 AI 味，判断层照走）")
    print(f"\n{n_files} 个文件，{len(findings)} 条命中"
          f"（critical {counts['critical']} / major {counts['major']} / minor {counts['minor']}）")
  return 1 if counts["critical"] else 0


# ------------------------------------------------------------------ 对比度 ---
def _parse_color(s):
  s = s.strip()
  m = re.fullmatch(r"#?([0-9a-fA-F]{3})", s)
  if m:
    return tuple(int(c * 2, 16) for c in m.group(1))
  m = re.fullmatch(r"#?([0-9a-fA-F]{6})([0-9a-fA-F]{2})?", s)
  if m:
    h = m.group(1)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
  m = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)[^)]*\)", s)
  if m:
    return tuple(min(255, int(x)) for x in m.groups())
  raise SystemExit(f"无法解析颜色: {s}（支持 #rgb/#rrggbb/rgb(r,g,b)）")


def _lum(rgb):
  def f(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
  r, g, b = (f(c) for c in rgb)
  return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg):
  l1, l2 = sorted((_lum(_parse_color(fg)), _lum(_parse_color(bg))), reverse=True)
  return (l1 + 0.05) / (l2 + 0.05)


def cmd_contrast(args):
  ratio = contrast_ratio(args.fg, args.bg)
  verdicts = {
    "AA 正文(4.5:1)": ratio >= 4.5,
    "AA 大字/UI(3:1)": ratio >= 3.0,
    "AAA 正文(7:1)": ratio >= 7.0,
  }
  if args.json:
    print(json.dumps({"fg": args.fg, "bg": args.bg, "ratio": round(ratio, 2),
                      "pass": {k: v for k, v in verdicts.items()}}, ensure_ascii=False))
  else:
    print(f"{args.fg} on {args.bg}  →  {ratio:.2f}:1")
    for k, v in verdicts.items():
      print(f"  {'✓' if v else '✗'} {k}")
    if not verdicts["AA 正文(4.5:1)"]:
      print("  提示：正文/按钮文字/placeholder 都按 4.5:1 要求（tokens.md）")
  return 0 if verdicts["AA 大字/UI(3:1)"] else 1


def main(argv=None):
  ap = argparse.ArgumentParser(prog="ui_taste",
                               description="前端 AI 味机械检查与对比度计算（启发式，人工裁决为准）")
  sub = ap.add_subparsers(dest="cmd", required=True)
  c = sub.add_parser("check", help="静态扫描文件/目录里的 AI 味硬信号")
  c.add_argument("paths", nargs="+")
  c.add_argument("--json", action="store_true")
  c.set_defaults(func=cmd_check)
  k = sub.add_parser("contrast", help="WCAG 对比度: contrast <前景色> <背景色>")
  k.add_argument("fg")
  k.add_argument("bg")
  k.add_argument("--json", action="store_true")
  k.set_defaults(func=cmd_contrast)
  args = ap.parse_args(argv)
  return args.func(args)


if __name__ == "__main__":
  sys.exit(main())

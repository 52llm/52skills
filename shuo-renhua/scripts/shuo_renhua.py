#!/usr/bin/env python3
"""shuo_renhua — 文本 AI 腔机械检查（判断层见 SKILL.md 与 references/）。

check  扫描可确定判定的 AI 腔硬信号（启发式：命中是强信号，干净≠没有 AI 腔；
       语体豁免——品牌破折号节奏、学术"进行"等——由判断层裁决）
stats  输出可数指标（句长/段长变异、第一人称、数字、引语、破折号、高频词命中），
       供打磨报告引用，治"禁止伪造整数"

规则与 references/zh-patterns.md、en-patterns.md 的 ⚙ 标记一一对应。纯标准库。
"""

import argparse
import json
import os
import re
import sys

EXTS = {".md", ".txt", ".markdown"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "__pycache__", ".venv"}

_CJK = re.compile(r"[一-鿿]")

# 高频词表（zh-patterns B 组 ⚙）
ZH_GAOPIN = ["赋能", "助力", "打造", "护航", "抓手", "闭环", "底层逻辑", "核心竞争力",
             "高质量发展", "全方位", "多维度", "多层次", "全链路", "一站式", "根植于",
             "至关重要", "凝心聚力", "砥砺前行"]
ZH_HUALI = ["璀璨", "熠熠生辉", "画卷", "华章", "扬帆起航", "乘风破浪", "砥砺奋进"]
ZH_DEAD_SLANG = ["yyds", "绝绝子", "栓Q", "家人们谁懂", "姐妹们快冲", "不好吃回来打我", "集美们"]
EN_AI_VOCAB = ["delve", "delves", "delving", "tapestry", "testament", "underscore",
               "underscores", "vibrant", "pivotal", "crucial", "foster", "fostering",
               "showcase", "showcases", "showcasing", "intricate", "intricacies",
               "boasts", "nestled", "groundbreaking", "seamless", "seamlessly",
               "leverage", "leverages", "elevate"]

_EMOJI_BLOCK = re.compile(r"^\s*[✅📍⏰💰🌟🌙❗💡🔥⭐✨🚀]")
_HALF_PUNCT = re.compile(r"[一-鿿][,;!?](?=\s|[一-鿿]|$)")
_HALF_PERIOD = re.compile(r"[一-鿿]\.(?=\s|[一-鿿]|$)")
_ASCII_ELLIPSIS = re.compile(r"[一-鿿]\.{3}|\.{3}[一-鿿]")
_ZH_DASH = re.compile(r"——|(?<![—-])—(?![—-])")
_EN_DASH = re.compile(r"[—–]")


def _mk_line_rules():
  """行级规则: (id, severity, lang, regex, message)。lang: zh/en/all"""
  R = []

  def add(rid, sev, lang, pattern, msg, flags=0):
    R.append((rid, sev, lang, re.compile(pattern, flags), msg))

  # --- 硬证据（全语言，critical）---
  add("ai-url", "critical", "all",
      r"utm_source=(chatgpt|claude|gemini|perplexity|openai)",
      "AI 来源 URL 残留（zh-patterns I 组硬证据）")
  add("assistant-zh", "critical", "zh",
      r"希望对您有帮助|希望这能帮到|如有疑问请|祝您生活愉快|很高兴为您服务|作为(一个)?\s*AI\s*(语言模型|助手)?[，,]|截至我的知识",
      "助手/客服腔残留：内容不是聊天记录（zh-patterns D 组）")
  add("assistant-en", "critical", "en",
      r"I hope this helps|As an AI language model|as of my (last|latest) (knowledge|training)|Would you like me to|Let me know if you",
      "chatbot 残留（en-patterns 4 组）", re.IGNORECASE)
  add("placeholder", "critical", "zh",
      r"XX[路街区县市镇]|X号线|X月X日|\{\{[^}]{1,40}\}\}|\[(产品名|公司名|品牌名|姓名|日期)\]",
      "模板占位符残留：标注[占位符请核对]或删除，不发明具体值（zh-patterns I 组）")

  # --- 中文 major ---
  add("dead-slang", "major", "zh",
      "|".join(map(re.escape, ZH_DEAD_SLANG)),
      "已入土流行语：出现即高警觉（registers.md 半衰期表；直播带货话术除外）")
  add("halfwidth-punct", "major", "zh", _HALF_PUNCT.pattern,
      "中文正文混入半角标点（，。？！应全角；代码/URL 除外）")
  add("halfwidth-period", "major", "zh", _HALF_PERIOD.pattern,
      "中文句子用了半角句号（zh-patterns F 组）")

  # --- 中文 minor ---
  add("ascii-ellipsis", "minor", "zh", _ASCII_ELLIPSIS.pattern,
      "中文省略号应为……（两个 U+2026），且基线≈0（registers.md 标点节）")
  add("shidai-opening", "minor", "zh",
      r"随着.{1,15}的(不断|快速|迅猛|飞速)?发展",
      "时代背景开场套路（zh-patterns A 组）")
  add("kong-jiewei", "minor", "zh",
      r"未来可期|前景光明|大有可为|让我们拭目以待|谱写新的?篇章",
      "空洞积极结尾（zh-patterns D 组）")

  # --- 英文 ---
  add("signposting", "major", "en",
      r"Let'?s dive|Without further ado|Here'?s what you need to know|Let'?s break (this|it) down",
      "signposting/throat-clearing（en-patterns 4 组）", re.IGNORECASE)
  add("negative-parallelism", "minor", "en",
      r"It'?s not (just|merely) [^.\n]{0,60}[,;] it'?s|Not only [^.\n]{0,80} but also",
      "negative parallelism 句壳（en-patterns 3 组；聚簇才定罪）", re.IGNORECASE)
  return R


LINE_RULES = _mk_line_rules()


def _lang_of(text):
  cjk = len(_CJK.findall(text))
  latin_words = len(re.findall(r"[A-Za-z]{2,}", text))
  langs = set()
  if cjk >= 20:
    langs.add("zh")
  if latin_words >= 60 and (cjk < 20 or latin_words > cjk):
    langs.add("en")
  if not langs:
    langs.add("zh" if cjk > 0 else "en")
  return langs


def _cluster_findings(text, langs):
  """文件级聚簇规则（zh 高频词/华丽词、en AI 词表、破折号密度、emoji 微模板）。"""
  out = []
  if "zh" in langs:
    hits = sorted({w for w in ZH_GAOPIN if w in text})
    if len(hits) >= 3:
      out.append(("gaopin-cluster", "major",
                  f"AI 高频词聚簇 ≥3：{'、'.join(hits[:8])}（zh-patterns B 组，聚簇定罪）"))
    hl = sorted({w for w in ZH_HUALI if w in text})
    if len(hl) >= 2:
      out.append(("huali-cluster", "major",
                  f"华丽意象词堆砌：{'、'.join(hl)}（zh-patterns B 组）"))
    dash_n = len(_ZH_DASH.findall(text))
    if dash_n >= 2 and dash_n / max(len(text), 1) > 1 / 400:
      out.append(("dash-density", "major",
                  f"破折号 {dash_n} 处，超出真人基线（≈0）；杂文/特稿/品牌语体豁免由判断层裁决"))
    emoji_lines = sum(1 for ln in text.splitlines() if _EMOJI_BLOCK.search(ln))
    if emoji_lines >= 3:
      out.append(("emoji-infoblock", "major",
                  f"emoji 信息块微模板 {emoji_lines} 行（✅📍⏰…，zh-patterns H 组小红书）"))
    shuniu = re.findall(r"值得注意的是|需要注意的是|真正的问题是|核心在于|归根结底", text)
    if len(shuniu) >= 2:
      out.append(("kong-shuniu", "minor",
                  f"空枢纽 {len(shuniu)} 处：删枢纽直接说（zh-patterns B 组）"))
  if "en" in langs:
    low = text.lower()
    hits = sorted({w for w in EN_AI_VOCAB
                   if re.search(r"\b" + re.escape(w) + r"\b", low)})
    if len(hits) >= 3:
      out.append(("en-vocab-cluster", "major",
                  f"AI-word cluster ≥3: {', '.join(hits[:8])} (en-patterns group 2)"))
    if "zh" not in langs:
      dash_n = len(_EN_DASH.findall(text))
      if dash_n >= 2:
        out.append(("em-dash-en", "major",
                    f"em/en dash ×{dash_n}: near-binary tell in EN copy (en-patterns group 5)"))
  return out


def scan_text(text):
  langs = _lang_of(text)
  findings = []
  for i, line in enumerate(text.splitlines(), 1):
    stripped = line.strip()
    if stripped.startswith("```") or stripped.startswith("    "):
      continue  # 代码块粗略跳过（fenced 开关行与缩进代码）
    for rid, sev, lang, rx, msg in LINE_RULES:
      if lang != "all" and lang not in langs:
        continue
      if rx.search(line):
        findings.append((i, rid, sev, msg))
  for rid, sev, msg in _cluster_findings(text, langs):
    findings.append((0, rid, sev, msg))
  return findings, langs


def iter_files(paths):
  for p in paths:
    if os.path.isfile(p):
      yield p
      continue
    for root, dirs, files in os.walk(p):
      dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
      for f in sorted(files):
        if os.path.splitext(f)[1].lower() in EXTS:
          yield os.path.join(root, f)


def cmd_check(args):
  findings_all = []
  n = 0
  for path in iter_files(args.paths):
    n += 1
    try:
      text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
      findings_all.append({"file": path, "line": 0, "rule": "read-error",
                           "severity": "minor", "message": str(e)})
      continue
    fs, langs = scan_text(text)
    for line, rid, sev, msg in fs:
      findings_all.append({"file": path, "line": line, "rule": rid,
                           "severity": sev, "message": msg})
  counts = {s: sum(1 for f in findings_all if f["severity"] == s)
            for s in ("critical", "major", "minor")}
  if args.json:
    print(json.dumps({"files": n, "counts": counts, "findings": findings_all},
                     ensure_ascii=False, indent=2))
  else:
    by_file = {}
    for f in findings_all:
      by_file.setdefault(f["file"], []).append(f)
    for path, fs in by_file.items():
      print(path)
      for f in sorted(fs, key=lambda x: x["line"]):
        loc = f["line"] or "-"
        print(f"  {loc:>4}  [{f['severity']}] {f['rule']}: {f['message']}")
    if not findings_all:
      print("✓ 未命中机械规则（启发式：结构性 AI 腔要靠判断层，流程照走）")
    print(f"\n{n} 个文件，{len(findings_all)} 条命中"
          f"（critical {counts['critical']} / major {counts['major']} / minor {counts['minor']}）")
  return 1 if counts["critical"] else 0


# ------------------------------------------------------------------ stats ---
def text_stats(text):
  paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
  para_lens = [len(re.sub(r"\s", "", p)) for p in paras] or [0]
  sentences = [s for s in re.split(r"[。！？!?]+|(?<=[a-z0-9])\.\s", text) if s.strip()]
  sent_lens = [len(re.sub(r"\s", "", s)) for s in sentences] or [0]
  zh_first = len(re.findall(r"我们?", text))
  en_first = len(re.findall(r"\b(I|we|We)\b", text))
  numbers = len(re.findall(r"\d+(?:\.\d+)?%?", text))
  numbers += len(re.findall(
    r"[一二三四五六七八九十百千万两零]+(?=[多余]?[次个条张只年月日天分秒块元件位人场步笔篇章道遍趟回倍])",
    text))
  quotes = len(re.findall(r"「[^」]{2,}」|“[^”]{2,}”|\"[^\"\n]{4,}\"", text))
  dashes = len(re.findall(r"——|[—–]", text))
  gaopin = sorted({w for w in ZH_GAOPIN if w in text})
  en_vocab = sorted({w for w in EN_AI_VOCAB
                     if re.search(r"\b" + re.escape(w) + r"\b", text.lower())})
  return {
    "chars_no_space": len(re.sub(r"\s", "", text)),
    "paragraphs": len(paras),
    "para_len_min": min(para_lens), "para_len_max": max(para_lens),
    "sentences": len(sentences),
    "sent_len_avg": round(sum(sent_lens) / len(sent_lens), 1),
    "sent_len_min": min(sent_lens), "sent_len_max": max(sent_lens),
    "first_person_zh": zh_first, "first_person_en": en_first,
    "numbers": numbers, "quoted_speech": quotes, "dashes": dashes,
    "zh_gaopin_hits": gaopin, "en_vocab_hits": en_vocab,
  }


def cmd_stats(args):
  text = (sys.stdin.read() if args.file == "-"
          else open(args.file, encoding="utf-8", errors="replace").read())
  s = text_stats(text)
  if args.json:
    print(json.dumps(s, ensure_ascii=False, indent=2))
    return 0
  print(f"字符（去空白）: {s['chars_no_space']}   段落: {s['paragraphs']}"
        f"（最短 {s['para_len_min']} / 最长 {s['para_len_max']} 字）")
  print(f"句子: {s['sentences']}（均 {s['sent_len_avg']} 字，短 {s['sent_len_min']} / 长 {s['sent_len_max']}）")
  print(f"第一人称: 我/我们 {s['first_person_zh']} 处，I/we {s['first_person_en']} 处")
  print(f"具体数字: {s['numbers']} 处   引语: {s['quoted_speech']} 处   破折号: {s['dashes']} 处")
  if s["zh_gaopin_hits"]:
    print(f"AI 高频词命中: {'、'.join(s['zh_gaopin_hits'])}")
  if s["en_vocab_hits"]:
    print(f"EN AI-vocab hits: {', '.join(s['en_vocab_hits'])}")
  return 0


def main(argv=None):
  ap = argparse.ArgumentParser(prog="shuo_renhua",
                               description="文本 AI 腔机械检查与可数指标（启发式，判断层为准）")
  sub = ap.add_subparsers(dest="cmd", required=True)
  c = sub.add_parser("check", help="扫描文件/目录里的 AI 腔硬信号")
  c.add_argument("paths", nargs="+")
  c.add_argument("--json", action="store_true")
  c.set_defaults(func=cmd_check)
  s = sub.add_parser("stats", help="可数指标（供打磨报告引用）：stats <文件|->")
  s.add_argument("file")
  s.add_argument("--json", action="store_true")
  s.set_defaults(func=cmd_stats)
  args = ap.parse_args(argv)
  return args.func(args)


if __name__ == "__main__":
  sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""针对 curriculum.py 中仍为「空话模板」的数学子知识点，用本地 Ollama(qwen2.5:7b)
批量生成详细讲解(具体定义/公式/例题) + 题目，并【精准合并】回 curriculum_gen.json。

合并规则：按 cid + sub 精确匹配，只覆盖/新增缺失的子点，绝不破坏已有好内容。
- 整章未生成过 → 新建该 cid 条目，subs 为本次生成的子点；
- 部分子点缺失 → 仅把生成的子点按 sub 名合并进已有 subs 列表（替换同名、补充缺失）；
- 已生成条目为 None（旧失败标记）→ 当作未生成处理。

支持断点续跑：每次运行先重新扫描 curriculum_gen.json，已填好的子点会被 find_empty 自动排除。
增量落盘：每完成一个 topic 立即写盘，崩溃不丢进度。
"""
import sys, os, json, time, argparse, urllib.request, re
import curriculum as C

MODEL = "qwen2.5:7b"
OLLAMA = "http://localhost:11434/api/chat"
OUT = os.path.join(os.path.dirname(__file__), "curriculum_gen.json")
CALC_SUBJECTS = {"物理", "化学", "生物", "地理", "数学"}
TEMPLATE_PHRASE = "理解基本概念"

STRICT_TAIL = (
    "\n\n【重要】你刚才输出的内容存在严重质量问题：\n"
    "(1) 讲解正文必须是具体知识本身（具体定义、公式、例子），"
    "绝不能再出现\"理解基本概念\"\"记住核心公式\"\"做典型例题\"\"注意易错点\"这类空泛指导语；\n"
    "(2) 题目必须是具体可算/可判断的考试级真题，题干给具体数据或场景，选项为完整具体陈述句；\n"
    "(3) 请严格按格式重新输出高质量 JSON。"
)


def build_fill_prompt(subject, title, subs):
    subs_json = json.dumps(subs, ensure_ascii=False)
    calc_ok = subject in CALC_SUBJECTS
    if calc_ok:
        type_line = (
            "题型混合 choice / fill / calc：\n"
            "- calc 题：必须含具体数字的计算（不是概念默写），答案为数值或表达式；\n"
            "- choice 题：4 个选项必须是完整的具体陈述句（带数字/数值/公式的优先）；\n"
            "- fill 题：填关键术语、单位、公式、数值。"
        )
        content_line = (
            "讲解中出现公式或数量关系时用 $公式=数值$ 书写（如 $面积=长×宽$、"
            "$速度=路程÷时间$、$1公顷=10000平方米$），方便出计算题。"
        )
    else:
        type_line = (
            "题型只用 choice 和 fill（禁止 calc）：选项必须是完整的具体陈述句，禁止空洞名词。"
        )
        content_line = "讲解用具体例子、人物、事件细节，禁止 $公式$ 符号。"
    return (
        f"你是一位资深{subject}学科教师，正在为中小学生编写一节具体的「知识讲解」微课。\n\n"
        f"【章节主题】《{title}》\n"
        f"【请逐一讲解以下子知识点】（务必全部覆盖，不要遗漏）：\n{subs_json}\n\n"
        f"对每一个子知识点，请写一段 120~200 字的讲解文本，必须包含：\n"
        f"1. 具体的【定义/概念】——说清楚到底是什么，不能只写\"理解基本概念\"；\n"
        f"2. 具体的【公式 / 数量关系 / 方法步骤】（如适用）；\n"
        f"3. 1 个【具体的小例子】或【易错提醒】，帮助学生真正学懂。\n\n"
        f"【严禁套话】讲解里不得出现\"理解基本概念\"\"记住核心公式\"\"做典型例题\""
        f"\"注意易错点\"\"考察学生对…的理解\"这类空泛指导语；直接讲知识本身，像真人老师板书。\n\n"
        f"【聚焦子点本身】每个子点只讲它自己，不要串台：例如子点名是\"9 的口诀\"，"
        f"就只列 9 的乘法口诀（一九得九、二九十八……九九八十一），"
        f"不要混进其他数的口诀或泛泛的乘法总表；子点名是\"公顷\"就只讲公顷的定义与换算。\n\n"
        f"【{subject}学科特殊要求】\n{type_line}\n{content_line}\n\n"
        f"同时为每个子知识点出 2 道具体题目（两道题型尽量不同；数学必须有含数字的计算或具体公式题）。\n\n"
        f"【输出格式】只返回 JSON（不要 markdown 代码块标记）：\n"
        f'{{"subs":[{{"sub":"子点名","content":"120-200字详细讲解(含定义/公式/例子)",'
        f'"questions":[{{"type":"choice|fill|calc",'
        f'"stem":"具体题干(含数字/场景)","options":["A完整句","B完整句","C完整句","D完整句"],'
        f'"answer":0~3或字符串,"explanation":"解析"}}]}}]}}'
    )


def call_ollama(prompt, timeout=300):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 3200},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode("utf-8"))
    return resp["message"]["content"]


_LEAK_PAT = re.compile(
    r"本部分[将通]?.*?(包含|通过|有|设有).*?(选择题|计算题|填空题|题目)|"
    r"考察学生对|以下是题目|题目如下|请作答|请回答|本部分包含|本知识点包含|"
    r"理解基本概念|记住核心公式|做典型例题|注意易错点"
)


def _sanitize_content(text):
    if not text:
        return text
    sents = re.split(r"(?<=[。！？\n])", text)
    kept = [s for s in sents if not _LEAK_PAT.search(s)]
    return "".join(kept).strip()


def validate_fill(obj, subs, subject):
    """校验并规整。与 _gen_content.validate 不同：content 是必须项，
    questions 变为【可选】——有就收，没有也不丢弃正文（用户最关心的是详细讲解）。"""
    if not isinstance(obj, dict) or "subs" not in obj:
        return None
    calc_ok = subject in CALC_SUBJECTS
    raw = obj["subs"]
    if isinstance(raw, list) and len(raw) == len(subs):
        for i, s in enumerate(raw):
            if isinstance(s, dict):
                s["sub"] = subs[i]
    out = []
    for s in raw:
        if not isinstance(s, dict) or "content" not in s:
            continue
        content = str(s.get("content", "")).strip()
        if not calc_ok:
            content = re.sub(r"\$[^$]*\$", "", content).strip()
        content = _sanitize_content(content)
        if not content or len(content) < 30:
            continue
        qs = []
        for q in (s.get("questions") or []):
            if not isinstance(q, dict):
                continue
            t = q.get("type")
            if t not in ("choice", "fill", "calc"):
                continue
            if t == "calc" and not calc_ok:
                continue
            stem = str(q.get("stem", "")).strip()
            opts = q.get("options") or []
            ans = q.get("answer")
            if t == "choice":
                opts = [str(o).strip() for o in opts]
                if len(opts) != 4 or any(not o for o in opts) or len(set(opts)) < 3:
                    continue
                if not isinstance(ans, int) or not (0 <= ans < 4):
                    continue
                qs.append({"type": t, "stem": stem, "options": opts,
                           "answer": ans, "explanation": str(q.get("explanation", "")).strip()})
            else:
                if not isinstance(ans, str) or not ans.strip():
                    continue
                a = ans.strip()
                if "[" in a or "$" in a or "\\" in a or len(a) > 30:
                    continue
                qs.append({"type": t, "stem": stem, "options": [],
                           "answer": a, "explanation": str(q.get("explanation", "")).strip()})
        out.append({"sub": str(s.get("sub", "")), "content": content, "questions": qs})
    return out if out else None


def process_one(cid, topic, empty_subs):
    subject = topic.get("subject", "")
    title = topic.get("title", "")
    prompt = build_fill_prompt(subject, title, empty_subs)
    best = None
    last_err = None
    for attempt in range(3):
        try:
            raw = call_ollama(prompt if attempt == 0 else prompt + STRICT_TAIL)
            obj = json.loads(raw)
            valid = validate_fill(obj, empty_subs, subject)
            if valid:
                if len(valid) == len(empty_subs):
                    return valid
                best = valid
        except Exception as e:
            last_err = e
            time.sleep(3 * (attempt + 1))
    if best is None:
        sys.stderr.write(f"FAIL {cid}: {last_err}\n")
    return best


def find_empty():
    """返回 {cid: (topic, [empty_subs])}，仅数学、仅仍为模板的子点。"""
    C.reload_gen()
    empty = {}
    for cid, t in list(C.TOPIC_INDEX.items()):
        if t.get("stage") not in ("小学", "初中", "高中"):
            continue
        subject = t.get("subject", "")
        if subject != "数学":
            continue
        title = t.get("title", "")
        empty_subs = []
        for sub in (t.get("sub") or []):
            body = C._SUBTOPIC_CONTENT.get((title, sub), {}).get("body", "")
            if not body:
                gen = C.GEN_CONTENT.get(cid) or C.LAZY_CONTENT.get(cid)
                if gen:
                    for _s in gen.get("subs", []):
                        if _s.get("sub") == sub and _s.get("content"):
                            body = _s["content"]
                            break
            if body:
                continue
            body = C._gen_math_content(title, sub, "", subject)
            if TEMPLATE_PHRASE in body and "记住核心公式" in body:
                empty_subs.append(sub)
        if empty_subs:
            empty[cid] = (t, empty_subs)
    return empty


def load_existing():
    if os.path.exists(OUT):
        try:
            with open(OUT, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def merge(existing, cid, title, subject, new_subs):
    entry = existing.get(cid)
    if not isinstance(entry, dict):
        existing[cid] = {"title": title, "subject": subject, "subs": list(new_subs)}
        return existing
    old = {s.get("sub"): s for s in entry.get("subs", []) if isinstance(s, dict)}
    for ns in new_subs:
        old[ns["sub"]] = ns
    entry["subs"] = list(old.values())
    entry["title"] = title
    entry["subject"] = subject
    return existing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="只跑前 2 个章节用于质量验证")
    ap.add_argument("--topic", type=str, default="", help="只处理指定 cid")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    empty = find_empty()
    print(f"扫描到需补全的章节数: {len(empty)}，缺失子点合计: "
          f"{sum(len(v[1]) for v in empty.values())}", flush=True)

    if args.topic:
        empty = {args.topic: empty[args.topic]} if args.topic in empty else {}
    if args.pilot:
        # 选 1 个整章未生成 + 1 个可能部分缺失，便于看两类效果
        keys = list(empty.keys())[:2]
        empty = {k: empty[k] for k in keys}

    existing = load_existing()
    print(f"已加载 curriculum_gen.json 现有条目: {len(existing)}", flush=True)

    items = list(empty.items())
    if args.pilot:
        for cid, (t, subs) in items:
            t0 = time.time()
            res = process_one(cid, t, subs)
            dt = time.time() - t0
            if res:
                existing = merge(existing, cid, t.get("title"), t.get("subject"), res)
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(existing, f, ensure_ascii=False)
                print(f"\n##### {cid} | {t.get('title')} | 缺失{len(subs)}子点 | 用时 {dt:.1f}s #####", flush=True)
                for s in res[:3]:
                    print(f"  -- {s['sub']} | content[:120]: {s['content'][:120]}")
                    for q in s["questions"]:
                        print(f"     [{q['type']}] {q['stem'][:60]} ans={q['answer']}")
            else:
                print(f"\n## {cid} 生成失败，跳过", flush=True)
        return

    from concurrent.futures import ThreadPoolExecutor, as_completed
    done = 0
    ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut_map = {ex.submit(process_one, cid, t, subs): cid for cid, (t, subs) in items}
        for fut in as_completed(fut_map):
            cid = fut_map[fut]
            t, subs = empty[cid]
            res = fut.result()
            if res:
                existing = merge(existing, cid, t.get("title"), t.get("subject"), res)
                ok += 1
            done += 1
            if done % 1 == 0:  # 每完成一个即落盘，保证断点续跑
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(existing, f, ensure_ascii=False)
            if done % 5 == 0:
                print(f"进度 {done}/{len(items)} 成功 {ok} 已落盘", flush=True)
    print(f"补全完成: 成功 {ok}/{len(items)} 个章节", flush=True)


if __name__ == "__main__":
    main()

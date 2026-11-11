#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为「拓展与素养 · 英语学习方法」全模块（eng-*，41 章）用本地 Ollama(qwen2.5:7b)
批量生成详细讲解(具体方法/步骤/例子) + 每节 1 道选择题，合并进 curriculum_gen.json。

- 每次运行先清掉旧的 eng-* 条目（含旧的 eng-m* 小学英语），再写入新内容；
- 增量落盘：每完成一个 course 立即写盘；
- 每个子点 1 道 choice 题（4 个完整具体选项），答案 0~3 下标；
- 纯中文讲解，禁用 $公式$ 符号，禁用空泛指导语。
"""
import sys, os, json, time, re, urllib.request
import curriculum as C

MODEL = "qwen2.5:7b"
OLLAMA = "http://localhost:11434/api/chat"
OUT = os.path.join(os.path.dirname(__file__), "curriculum_gen.json")
SUBJECT = "英语学习方法"

_LEAK_PAT = re.compile(
    r"理解基本概念|记住核心公式|做典型例题|注意易错点|考察学生对|题目如下|请作答|请回答|"
    r"本部分包含|本知识点包含|以下是题目"
)


def build_prompt(title, subs):
    subs_json = json.dumps(subs, ensure_ascii=False)
    return (
        "你是一位资深英语学习方法导师，为全学段（小学到成人）英语学习者写一节"
        "「英语学习方法」微课。\n\n"
        f"【章节主题】《{title}》\n"
        f"【请逐一讲解以下子知识点】（务必全部覆盖、顺序一致、不要遗漏、不要串台）：\n{subs_json}\n\n"
        "对每一个子知识点，写一段 120~200 字讲解，必须包含：\n"
        "1. 具体的【方法 / 步骤 / 定义】——说清楚到底怎么做、是什么；\n"
        "2. 说明【为什么有效】或【适用场景】；\n"
        "3. 1 个【具体小例子】或【易错提醒】，帮助学生真正学会。\n\n"
        "【严禁套话】讲解里不得出现\"理解基本概念\"\"记住核心公式\"\"做典型例题\""
        "\"注意易错点\"\"考察学生对…的理解\"这类空泛指导语；直接讲方法本身，像真人老师板书。\n\n"
        "【纯中文】不要使用 $公式$ 等数学符号；可用英文单词举例（如 phonics、skimming、collocation）。\n\n"
        "同时为每一个子知识点出 1 道 choice 选择题：题干具体，4 个选项为完整具体的陈述句，"
        "答案用 0~3 的下标，并给解析。\n\n"
        "【输出格式】只返回 JSON（不要 markdown 代码块标记）：\n"
        '{"subs":[{"sub":"子点名","content":"120-200字详细讲解(含方法/例子)","questions":'
        '[{"type":"choice","stem":"具体题干","options":["A完整句","B完整句","C完整句","D完整句"],'
        '"answer":0,"explanation":"解析"}]}]}'
    )


def call_ollama(prompt, timeout=300):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 3000},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode("utf-8"))
    return resp["message"]["content"]


def _sanitize(text):
    if not text:
        return text
    sents = re.split(r"(?<=[。！？\n])", text)
    return "".join(s for s in sents if not _LEAK_PAT.search(s)).strip()


def validate(obj, subs):
    if not isinstance(obj, dict) or "subs" not in obj:
        return None
    raw = obj["subs"]
    if not isinstance(raw, list) or len(raw) != len(subs):
        return None
    out = []
    for i, s in enumerate(raw):
        if not isinstance(s, dict) or "content" not in s:
            return None
        content = str(s.get("content", "")).strip()
        content = re.sub(r"\$[^$]*\$", "", content).strip()
        content = _sanitize(content)
        if not content or len(content) < 30:
            return None
        qs = []
        for q in (s.get("questions") or []):
            if not isinstance(q, dict):
                continue
            if q.get("type") != "choice":
                continue
            stem = str(q.get("stem", "")).strip()
            opts = [str(o).strip() for o in (q.get("options") or [])]
            ans = q.get("answer")
            if len(opts) != 4 or any(not o for o in opts) or len(set(opts)) < 3:
                continue
            if not isinstance(ans, int) or not (0 <= ans < 4):
                continue
            qs.append({"type": "choice", "stem": stem, "options": opts,
                       "answer": ans, "explanation": str(q.get("explanation", "")).strip()})
        if not qs:
            return None
        out.append({"sub": subs[i], "content": content, "questions": qs})
    return out if len(out) == len(subs) else None


def main():
    eng = [(cid, t) for cid, t in C.TOPIC_INDEX.items() if cid.startswith("eng-")]
    eng.sort(key=lambda x: x[0])
    print(f"共找到 {len(eng)} 个英语学习方法章节")

    # 读取已有数据并清掉旧 eng-* 条目
    data = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            data = json.load(f)
    old_eng = [k for k in data if k.startswith("eng-")]
    for k in old_eng:
        data.pop(k, None)
    print(f"已清除旧 eng 条目 {len(old_eng)} 个")

    done = 0
    for cid, t in eng:
        title = t.get("title", "")
        subs = t.get("sub") or []
        prompt = build_prompt(title, subs)
        valid = None
        for attempt in range(3):
            try:
                raw = call_ollama(prompt)
                valid = validate(json.loads(raw), subs)
                if valid:
                    break
            except Exception as e:
                print(f"  [{cid}] 第{attempt+1}次失败: {e}")
                time.sleep(2)
        if not valid:
            print(f"  [跳过] {cid} {title} 生成校验未通过")
            continue
        data[cid] = {"title": title, "subject": SUBJECT, "subs": valid}
        done += 1
        # 增量落盘
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print(f"  [完成 {done}/{len(eng)}] {cid} {title}  ({len(valid)} 子点)")

    print(f"\n全部完成：成功 {done}/{len(eng)} 章，写入 {OUT}")


if __name__ == "__main__":
    main()

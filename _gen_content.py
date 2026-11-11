#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用本地 Ollama(qwen2.5:7b) 批量生成全学科课件内容+题目, 萺盘为 curriculum_gen.json。
支持断点续跑(resume): 已生成的 topic 跳过。

v2 升级：
- 模型从 3b → 7b，质量大幅提升
- 提示词重写：强制每道题必须是「具体可计算/可判断」的考试级真题
- 禁止泛泛模板题（如"以下哪项正确"+"三边关系"/"内角外角"式选项）
"""
import sys, os, json, time, argparse, urllib.request, re
import curriculum as C

MODEL = "qwen2.5:3b"
OLLAMA = "http://localhost:11434/api/chat"
OUT = os.path.join(os.path.dirname(__file__), "curriculum_gen.json")

CALC_SUBJECTS = {"物理", "化学", "生物", "地理", "数学"}
STRICT_TAIL = (
    "\n\n【重要】你刚才输出的题目存在严重质量问题：\n"
    "(1) 题干不能是泛泛的'关于XXX下列哪项正确'——必须给出具体数据、数值、公式或场景；\n"
    "(2) 选项不能是空洞名词(如'三边关系''内角外角')——每个选项必须是完整的具体陈述句；\n"
    "(3) 选择题4个选项必须互不相同且都有一定迷惑性；\n"
    "(4) 数学/物理必须有具体数字的计算或推理；\n"
    "(5) 请严格按格式重新输出高质量 JSON。"
)


def _exam_examples(subject):
    """给出该学科的考试级例题示范，引导模型输出同等质量。"""
    ex = {
        "数学": [
            {
                "type": "choice",
                "stem": "在△ABC中，∠A=50°, ∠B=65°，则∠C的度数是（　　）",
                "options": ["55°", "60°", "65°", "70°"],
                "answer": 2,
                "explanation": "三角形内角和为180°，∠C=180°−50°−65°=65°。"
            },
            {
                "type": "calc",
                "stem": "用因式分解法解方程：x²−5x+6=0（写出两个根）",
                "options": [],
                "answer": "x₁=2, x₂=3",
                "explanation": "(x−2)(x−3)=0 → x₁=2, x₂=3。"
            },
            {
                "type": "fill",
                "stem": "若等腰三角形的一个底角是40°，则其顶角度数是______°。",
                "options": [],
                "answer": "100",
                "explanation": "顶角=180°−2×40°=100°。"
            },
        ],
        "物理": [
            {
                "type": "calc",
                "stem": "一辆汽车以20m/s的速度匀速行驶10秒，通过的路程是多少米？",
                "options": [],
                "answer": "200 m",
                "explanation": "s = vt = 20 × 10 = 200 m。"
            },
            {
                "type": "choice",
                "stem": "关于惯性，下列说法正确的是（　　）",
                "options": ["物体速度越大惯性越大", "静止的物体没有惯性",
                          "惯性是物体的固有属性与运动状态无关", "只有受力物体才有惯性"],
                "answer": 2,
                "explanation": "惯性是物体的固有属性，一切物体在任何情况下都有惯性。"
            },
        ],
        "化学": [
            {
                "type": "fill",
                "stem": "电解水实验中，正极产生的气体是______，负极产生的是______，体积比约为______:______。",
                "options": [],
                "answer": "氧气(O₂), 氢气(H₂), 1, 2",
                "explanation": "电解水：「正氧负氢」，O₂:H₂体积比=1:2。"
            },
            {
                "type": "choice",
                "stem": "下列物质在空气中燃烧，有白色火焰的是（　　）",
                "options": ["硫(S)", "铁丝", "红磷(P)", "镁条(Mg)"],
                "answer": 3,
                "explanation": "镁条燃烧发出耀眼的白光（白色火焰），硫发蓝紫色火焰，铁丝火星四射。"
            },
        ],
        "语文": [
            {
                "type": "choice",
                "stem": "\"床前明月光\"中\"明月光\"的意思是（　　）",
                "options": ["明亮的月光", "月亮的光辉很明亮", "月光如水一样清澈", "月亮很圆很亮"],
                "answer": 0,
                "explanation": "\"明月光\"即明亮的月光，形容月光洒在床前的样子。"
            },
            {
                "type": "fill",
                "stem": "《静夜思》的作者是唐代诗人______。",
                "options": [],
                "answer": "李白",
                "explanation": "《静夜思》是李白的代表作之一，表达了诗人的思乡之情。"
            },
        ],
        "英语": [
            {
                "type": "choice",
                "stem": "— What's this in English?\n— It's ______ eraser.",
                "options": ["a", "an", "the", "/"],
                "answer": 1,
                "explanation": "eraser以元音音素开头，不定冠词用an。"
            },
            {
                "type": "fill",
                "stem": "将中文翻译成英文：这是我的尺子。\n___________________________",
                "options": [],
                "answer": "This is my ruler.",
                "explanation": "指示代词this + be动词is + 形容词性物主代词my + 名词ruler。"
            },
        ],
    }
    # 找最接近的学科示例
    if subject in ex:
        return ex[subject]
    if subject in ("历史", "道法", "政治"):
        return ex["语文"]
    if subject in ("生物", "地理"):
        return ex["物理"]
    return ex["数学"]  # 默认


def build_prompt(subject, title, subs):
    calc_ok = subject in CALC_SUBJECTS
    examples = json.dumps(_exam_examples(subject), ensure_ascii=False, indent=2)
    subs_json = json.dumps(subs, ensure_ascii=False)

    if calc_ok:
        type_line = (
            "题型混合 choice / fill / calc：\n"
            "- calc 题：必须含具体数字的计算（不是概念默写），答案为数值或表达式；\n"
            "- fill 题：填关键术语、单位、公式、数值；\n"
            "- choice 题：4 个选项必须是完整的具体陈述句（带数字/数值/公式的优先）。"
        )
        content_line = (
            "内容中必须包含 $公式=数值$ 或 $量关系$（如 $v=\\frac{s}{t}$、$F=ma$、"
            "$I=\\frac{U}{R}$、$1mol=6.02×10^{23}$个），方便出计算题。"
        )
    else:
        type_line = (
            "题型只用 choice 和 fill（禁止 calc）：\n"
            "- choice 题：4 个选项必须是完整的具体陈述句，禁止空洞名词（错误❌ A.三边关系 B.内角外角）；\n"
            "- fill 题：答案是简短可评判的文字（词语/短句/英文单词），不要拼音。"
        )
        content_line = (
            "禁止使用 $公式$ 符号；讲解要包含具体例子、人物、事件细节。"
        )

    return (
        f"你是一位资深{subject}学科命题专家，熟悉中国中小学课标和考试出题规范。\n\n"
        f"【任务】为知识点《{title}》编写课件内容和练习题。\n\n"
        f"【子知识点列表】（请逐一覆盖）：\n{subs_json}\n\n"
        f"【质量要求 —— 最重要！】\n"
        f"1. 每道题都必须像真正的考试题：\n"
        f"   ✅ 正确范例（数学）：\"在Rt△ABC中，∠C=90°, a=3, b=4，求斜边c=\" → 有具体数字可算\n"
        f"   ❌ 错误范例（禁止）：\"关于三角形，下列说法正确的是？A.三边关系 B.内角外角\" → 泛泛模板\n"
        f"2. 选择题的4个选项必须:\n"
        f"   - 是完整的句子或表达式（不是1-2个字的名词）\n"
        f"   - 含有具体数字、数值、公式或明确的事实描述\n"
        f"   - 3个干扰项要有迷惑性但不能太离谱\n"
        f"3. 填空/计算题:\n"
        f"   - 必须能根据题目信息计算出唯一确定答案\n"
        f"   - 答案简短明确（数字/单词/短语）\n"
        f"4. 每个子点恰好 2 道题，两道题型不同\n\n"
        f"5. **讲解正文禁令**：content 字段只写给学生看的「知识讲解本身」，"
        f"严禁把出题指令写进正文——不得出现\"本部分包含选择题/计算题\"\"考察学生对…的理解\""
        f"\"以下是题目\"等给系统的说明性文字；也不得出现\"关于XXX下列说法正确的是\"之类的套话开头。"
        f"直接讲知识（定义、事实、例子、推导），像真人老师板书。\n\n"

        f"【{subject}学科出题参考范例】\n```json\n{examples}\n```\n\n"

        f"【{subject}学科特殊要求】\n"
        f"{type_line}\n"
        f"{content_line}\n\n"

        f"【输出格式】只返回JSON（不要markdown代码块标记）：\n"
        f'{{"subs":[{{"sub":"子点名","content":"150-260字讲解文本",'
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
        "options": {"temperature": 0.4, "num_predict": 2400},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode("utf-8"))
    return resp["message"]["content"]


_LEAK_PAT = re.compile(
    r"本部分[将通]?.*?(包含|通过|有|设有).*?(选择题|计算题|填空题|题目)|"
    r"考察学生对|以下是题目|题目如下|请作答|请回答|本部分包含|本知识点包含"
)


def _sanitize_content(text):
    """删除正文里混进的「出题说明」类句子（如'本部分将通过选择题和计算题考察…'），
    只保留给学生看的知识讲解。按句切分，丢弃含泄漏短语的整句。"""
    if not text:
        return text
    sents = re.split(r"(?<=[。！？\n])", text)
    kept = [s for s in sents if not _LEAK_PAT.search(s)]
    return "".join(kept).strip()


def validate(obj, subject, subs):
    """校验并规整。返回 subs 列表，无效子点丢弃；全无效返回 None。
    v2 新增：检测并拒绝泛泛模板题；v3 新增：清洗正文里的出题说明泄漏。
    """
    if not isinstance(obj, dict) or "subs" not in obj:
        return None
    calc_ok = subject in CALC_SUBJECTS
    raw_subs = obj["subs"]

    # 按索引对齐子点名
    if isinstance(raw_subs, list) and len(raw_subs) == len(subs):
        for i, s in enumerate(raw_subs):
            if isinstance(s, dict):
                s["sub"] = subs[i]

    out = []
    for s in raw_subs:
        if not isinstance(s, dict) or "content" not in s:
            continue
        content = str(s.get("content", "")).strip()
        if not calc_ok:
            content = re.sub(r"\$[^$]*\$", "", content).strip()
        content = _sanitize_content(content)  # 清洗出题说明泄漏
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

            # ── v2 质量门控：拒绝泛泛模板题 ──
            if t == "choice":
                # 题干不能是纯模板
                bad_stems = ("关于.*下列说法正确", "以下哪项正确", "下列.*的是")
                is_template = any(re.search(pat, stem) for pat in bad_stems)
                # 选项不能太短（<4字符视为空洞名词）
                short_opts = sum(1 for o in opts if len(str(o).strip()) < 4)

                opts = [str(o).strip() for o in opts]
                if len(opts) != 4 or any(not o for o in opts):
                    continue
                if len(set(opts)) < 3:  # 至少3个不同选项
                    continue
                if not isinstance(ans, int) or not (0 <= ans < 4):
                    continue
                # v2：如果检测到模板题干 + 短选项组合，跳过
                if is_template and short_opts >= 2:
                    continue

                qs.append({"type": t, "stem": stem,
                           "options": opts, "answer": ans,
                           "explanation": str(q.get("explanation", "")).strip()})
            else:
                if not isinstance(ans, str) or not ans.strip():
                    continue
                a = ans.strip()
                if "[" in a or "$" in a or "\\" in a or len(a) > 30:
                    continue
                qs.append({"type": t, "stem": stem,
                           "options": [], "answer": a,
                           "explanation": str(q.get("explanation", "")).strip()})

        if not qs:
            continue
        out.append({"sub": str(s.get("sub", "")), "content": content, "questions": qs})

    if not out:
        return None
    return out


def process_one(cid, topic):
    subs = topic.get("sub") or [topic.get("title", "")]
    subject = topic.get("subject", "")
    prompt = build_prompt(subject, topic.get("title", ""), subs)
    best = None
    last_err = None
    for attempt in range(3):  # v2: 增加重试次数
        try:
            raw = call_ollama(prompt if attempt == 0 else prompt + STRICT_TAIL)
            obj = json.loads(raw)
            valid = validate(obj, subject, subs)
            if valid:
                if len(valid) == len(subs):
                    return valid
                best = valid
        except Exception as e:
            last_err = e
            time.sleep(3 * (attempt + 1))  # 渐进退避
    if best is None:
        sys.stderr.write(f"FAIL {cid}: {last_err}\n")
    return best


# 优先生成“内容稀薄、引擎无法出题”的人文学科（这些学科最依赖 Gen 内容）；
# 理科（含公式）已由出题引擎较好覆盖，可用 --all 强制全量生成。
PRIORITY_SUBJECTS = {"语文", "历史", "英语", "道德与法治", "思想政治"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--all", action="store_true", help="生成全部学科（不复限于人文学科）")
    args = ap.parse_args()

    existing = {}
    if os.path.exists(OUT):
        try:
            with open(OUT, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    items = list(C.TOPIC_INDEX.items())
    if args.pilot:
        items = [it for it in items if it[0] in ("ju-math-g8-u1", "pe-math-g7-u1", "ju-phy-g8-u1")][:3]

    todo = [(cid, t) for cid, t in items if cid not in existing]
    if not args.all:
        ptodo = [(cid, t) for cid, t in todo if t.get("subject") in PRIORITY_SUBJECTS]
        if ptodo:
            todo = ptodo
    print(f"已生成 {len(existing)} 个, 待生成 {len(todo)} 个, 模型={MODEL}"
          + ("" if args.all else f"（优先人文学科 {len(PRIORITY_SUBJECTS)} 类）"), flush=True)

    if args.pilot:
        for cid, t in todo:
            t0 = time.time()
            res = process_one(cid, t)
            dt = time.time() - t0
            existing[cid] = {"title": t.get("title"), "subject": t.get("subject"), "subs": res} if res else None
            print(f"\n##### {cid} | {t.get('title')} | {t.get('subject')} | 用时 {dt:.1f}s #####")
            if res:
                for s in res[:2]:
                    print(f"  -- {s['sub']} | c[:80]: {s['content'][:80]}")
                    for q in s["questions"]:
                        print(f"     [{q['type']}] {q['stem'][:72]}")
                        if q.get("options"): print(f"       opts={q['options']}")
                        print(f"       ans={q['answer']}")
            else:
                print("  !! 生成失败")
        return

    from concurrent.futures import ThreadPoolExecutor, as_completed
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut_map = {ex.submit(process_one, cid, t): cid for cid, t in todo}
        for fut in as_completed(fut_map):
            cid = fut_map[fut]
            res = fut.result()
            if res:
                existing[cid] = {"title": C.TOPIC_INDEX[cid].get("title"),
                                 "subject": C.TOPIC_INDEX[cid].get("subject"), "subs": res}
            done += 1
            if done % 10 == 0:
                with open(OUT, "w", encoding="utf-8") as f:
                    json.dump(existing, f, ensure_ascii=False)
                print(f"进度 {done}/{len(todo)} 已落盘", flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False)
    print("全量生成完成, 共", len(existing), "个 topic", flush=True)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""AL 学习机模式 · AI 学伴（小艾）核心逻辑

对标科大讯飞 AI 学习机的「AI 1对1 伴学」：
  1) 开机主动开口（opening）：按学情自动生成开场白 + 3 个可点动作；
  2) 随时可问（chat）：带上下文的学伴对话，复用现有 call_llm / mock 降级。

本模块只做「纯逻辑」，不碰 Handler，方便单测与复用。
"""

import json
import re



# ================================================================
# 📚 本地知识引擎（无大模型也能「讲得清、考得了」）
# ================================================================
# 演示模式 / 断网 / 没配 Key 时，学伴不再只会说套话：
#   讲知识点 → 从 637 个知识点的讲义正文里取真实内容
#   出题判分 → 从每课自带的 quiz 题库里出，判对错 + 讲解析
# 全部本地读取，零网络依赖，平板断网也能用。
_KB = {"lesson_fn": None, "topic_index": None}


def bind_knowledge(lesson_fn, topic_index):
    """由 server.py 注入 curriculum 的取课函数与索引（避免本模块硬依赖）。"""
    _KB["lesson_fn"] = lesson_fn
    _KB["topic_index"] = topic_index


def _lesson(cid):
    fn = _KB.get("lesson_fn")
    if not fn or not cid:
        return None
    try:
        return fn(cid)
    except Exception:
        return None


def _topics():
    return _KB.get("topic_index") or {}


def find_topic_by_text(text, ctx=None):
    """从一句话里认出孩子想学的知识点（按标题命中 / 子点命中 / 上下文）。"""
    text = (text or "").strip()
    idx = _topics()
    # 1) 当前正在学的那一课优先（孩子说「讲讲这个」时）
    if ctx:
        cur = ctx.get("course_id") or ctx.get("now_course_id")
        if cur and cur in idx:
            if _wants_current(text):
                return cur
    # 2) 标题直接命中（最长匹配优先）
    best = None
    for cid, t in idx.items():
        title = (t.get("title") or "").strip()
        if not title:
            continue
        core = re.split(r"[·（(]", title)[0].strip()
        for cand in {title, core}:
            if cand and len(cand) >= 2 and cand in text:
                if best is None or len(cand) > best[1]:
                    best = (cid, len(cand))
    if best:
        return best[0]
    # 3) 子点命中（"什么是勾股定理" → 命中含"勾股定理"的知识点）
    for cid, t in idx.items():
        for sub in (t.get("sub") or []):
            if sub and len(sub) >= 3 and sub in text:
                return cid
    return None


def _wants_current(text):
    return any(w in text for w in ["这个", "这课", "这节", "刚才", "上一课", "当前", "继续"])


def pick_recommend_topic(ctx):
    """没指定就先推最该学的一课：当前课程 > 系统推荐 > 第一课。"""
    ctx = ctx or {}
    cur = ctx.get("course_id") or ctx.get("now_course_id")
    if cur and cur in _topics():
        return cur
    pc = ctx.get("pending_course") or {}
    if pc.get("course_id") and pc["course_id"] in _topics():
        return pc["course_id"]
    idx = _topics()
    for cid in idx.keys():
        return cid
    return None


def explain_topic(cid, section_idx=None, detail="full"):
    """把知识点讲义变成「学伴口吻」的讲解。
    detail: brief(一句话懂) / key(重点) / full(完整讲解)"""
    L = _lesson(cid)
    if not L:
        return None
    sections = L.get("sections") or []
    title = L.get("title") or ""
    goals = L.get("goals") or ""

    def _grab(body, tag):
        m = re.search(r"【" + tag + r"[^】]*】([\s\S]*?)(?=【|$)", body or "")
        return (m.group(1).strip() if m else "").strip()

    def _clean(s, limit=None):
        s = re.sub(r"\s+", " ", s or "").strip()
        if limit and len(s) > limit:
            s = s[:limit].rstrip("，。；、 ") + "…"
        return s

    if not sections:
        return {"title": title, "text": (goals or "这节课我们慢慢来。"), "topic_id": cid,
                "section_idx": 0, "section_total": 0}

    si = 0 if section_idx is None else max(0, min(int(section_idx), len(sections) - 1))
    sec = sections[si] or {}
    body = sec.get("body") or ""
    one = _grab(body, "一句话懂")
    why = _grab(body, "为什么重要")
    how = _grab(body, "具体怎么做")
    tip = sec.get("tip") or ""

    head = "【%s】" % (sec.get("heading") or title)
    if detail == "brief":
        parts = [head, "简单说：" + (_clean(one, 90) or _clean(body, 90))]
    elif detail == "key":
        parts = [head, "重点是：" + (_clean(one, 80) or _clean(body, 80))]
        if why:
            parts.append("为什么重要：" + _clean(why, 90))
    else:
        parts = [head]
        if one:
            parts.append("一句话懂：" + _clean(one, 140))
        if why:
            parts.append("为什么重要：" + _clean(why, 160))
        if how:
            parts.append("具体怎么做：" + _clean(how, 200))
        if not (one or why or how):
            parts.append(_clean(body, 320))
    if tip and detail != "brief":
        parts.append("小提示：" + _clean(tip, 100))
    return {
        "title": title,
        "heading": sec.get("heading") or title,
        "text": "\n".join(parts),
        "topic_id": cid,
        "section_idx": si,
        "section_total": len(sections),
        "has_next": si + 1 < len(sections),
    }


def topic_summary(cid):
    """整课概览：这节课讲什么、有哪几个小节。"""
    L = _lesson(cid)
    if not L:
        return None
    title = L.get("title") or ""
    subj = L.get("subject") or ""
    grade = L.get("grade") or ""
    goals = L.get("goals") or ""
    heads = [s.get("heading") for s in (L.get("sections") or []) if s.get("heading")]
    lines = ["《%s》%s %s" % (title, subj, grade)]
    if goals:
        lines.append("这节课要掌握：" + goals.strip())
    if heads:
        lines.append("一共 %d 个部分：%s" % (len(heads), "、".join(heads[:8])))
    return {"title": title, "text": "\n".join(lines), "topic_id": cid,
            "section_total": len(heads)}


def get_quiz(cid):
    """取本课题库（统一成内部结构）。"""
    L = _lesson(cid)
    if not L:
        return []
    out = []
    for q in (L.get("quiz") or []):
        stem = (q.get("stem") or "").strip()
        if not stem:
            continue
        opts = q.get("options") or []
        ans = q.get("answer")
        # 题型归一：choice 有 options；calc 的 options 可能为空
        if opts and isinstance(ans, int):
            kind = "choice"
        elif opts and isinstance(ans, str) and len(ans) == 1 and ans.isalpha():
            kind = "choice_letter"
            ans = ord(ans.upper()) - 65
        else:
            kind = "open"
        out.append({
            "id": q.get("id") or ("%s-%d" % (cid, len(out))),
            "stem": stem,
            "options": opts,
            "answer": ans,
            "explanation": (q.get("explanation") or "").strip(),
            "sub": q.get("sub") or "",
            "kind": kind,
        })
    return out


def quiz_present(cid, seq_no=0):
    """把第 seq_no 题包装成「学伴出题」文案。"""
    qs = get_quiz(cid)
    if not qs:
        return None
    q = qs[seq_no % len(qs)]
    L = _lesson(cid) or {}
    head = "第 %d 题（共 %d 题）" % (seq_no + 1, len(qs))
    lines = [head]
    if q["sub"]:
        lines.append("考点：" + q["sub"])
    lines.append(q["stem"])
    for o in (q["options"] or []):
        lines.append("  " + str(o))
    if not q["options"]:
        lines.append("（直接说出你的答案）")
    return {
        "topic_id": cid,
        "quiz_index": seq_no % len(qs),
        "quiz_total": len(qs),
        "stem": q["stem"],
        "options": q["options"],
        "kind": q["kind"],
        "text": "\n".join(lines),
        "title": L.get("title") or "",
    }


def quiz_grade(cid, quiz_index, user_answer):
    """判分：支持选项序号 / 字母 / 文本包含。返回 verdict 与解析。"""
    qs = get_quiz(cid)
    if not qs:
        return None
    q = qs[int(quiz_index) % len(qs)]
    ans = q["answer"]
    ua = (user_answer or "").strip()
    correct = False
    if q["kind"] == "choice":
        num = None
        m = re.search(r"\b([A-Da-d])\b", ua)
        if m:
            num = ord(m.group(1).upper()) - 65
        else:
            m2 = re.search(r"(\d+)", ua)
            if m2:
                num = int(m2.group(1)) - 1
        if num is not None and num == int(ans):
            correct = True
        # 也可能是孩子直接念出了选项内容
        if not correct and isinstance(ans, int) and 0 <= ans < len(q["options"] or []):
            opt_text = re.sub(r"^[A-Da-d][.．、]\s*", "", str(q["options"][ans]))
            if opt_text and opt_text in ua:
                correct = True
    elif q["kind"] == "choice_letter":
        correct = ua.upper().startswith(str(ans))
    else:
        a = re.sub(r"\s+", "", str(ans or ""))
        u = re.sub(r"\s+", "", ua)
        correct = bool(a and u and (a == u or a in u or u in a))
    return {
        "correct": correct,
        "answer": ans,
        "explanation": q["explanation"],
        "stem": q["stem"],
        "options": q["options"],
        "kind": q["kind"],
        "text": ("答对啦！%s\n解析：%s" % ("", q["explanation"])) if correct
                else ("再想想～ %s\n解析：%s" % (_answer_text(q), q["explanation"])),
    }


def _answer_text(q):
    ans = q["answer"]
    if isinstance(ans, int) and q["options"] and 0 <= ans < len(q["options"]):
        return "正确答案是：" + str(q["options"][ans])
    return "正确答案是：" + str(ans)


def topic_tips(cid):
    """本课易错点（讲完知识点后顺带提醒）。"""
    L = _lesson(cid)
    tips = (L or {}).get("mistakes") or []
    return [t for t in tips if t][:3]


def search_topics(keyword, limit=5):
    """按关键词检索知识点（孩子问「有没有讲分数的」时用）。"""
    kw = (keyword or "").strip()
    if not kw or len(kw) < 2:
        return []
    hits = []
    for cid, t in _topics().items():
        title = t.get("title") or ""
        pool = title + " " + " ".join(t.get("sub") or []) + " " + (t.get("goals") or "")
        if kw in pool:
            hits.append({
                "topic_id": cid,
                "title": title,
                "subject": t.get("subject") or "",
                "grade": t.get("grade") or "",
                "score": 2 if kw in title else 1,
            })
    hits.sort(key=lambda x: -x["score"])
    return hits[:limit]


# ---------------- 学伴人格 Prompt ----------------
COMPANION_PROMPT = """你是「小艾」，一台儿童 AI 学习机里的 AI 学伴老师，正在陪 <<CHILD>> 学习。

# 你的性格
- 温暖、有活力、像一位懂你的大姐姐/大哥哥；说话口语化、短句、有画面感。
- 每次回复控制在 1-3 句（最多 60 字），关键时可用一个 emoji，但不要每句都用。
- 你永远不训斥、不比较、不说"你怎么这么笨"这类话；孩子表现差时先共情再给台阶。

# 你的任务（AI 学伴，不是答题机器）
1. 主动张罗学习：告诉孩子现在最该做什么（继续上次、复习错题、练几题、学新课）。
2. 用苏格拉底式提问引导，不直接给最终答案；孩子先说思路，你再一步步追问。
3. 孩子说累/烦/不想学时：先接住情绪 → 降低难度或提议休息 2 分钟 → 给一个小到不可能失败的任务。
4. 孩子做完一件事（答对、学完一课）：具体表扬 + 顺势推下一步。

# 当前学情（真实数据，用它来开场和推进，不要编造）
<<CONTEXT>>

<<COURSE>>

# 输出格式（只输出一个 JSON 对象，不要 Markdown 代码块、不要多余文字）
{
  "reply": "你要对孩子说的话（中文口语，1-3 句）",
  "emotion": "curiosity|confusion|frustration|excitement|satisfaction|boredom|anxiety|neutral 之一",
  "suggest": [{"label": "按钮文字(<=6字)", "action": "continue|practice|review|learn_new|rest|explain|none"}],
  "speak": true
}
"""


def _fmt_min(sec):
    try:
        return max(0, int(sec or 0) // 60)
    except Exception:
        return 0


def _fmt_duration(sec):
    m = _fmt_min(sec)
    if m < 60:
        return "%d 分钟" % m
    return "%d 小时 %d 分钟" % (m // 60, m % 60)


def _describe_resume(r):
    """把断点快照翻译成一句人话："上次在学《XXX》"。"""
    if not isinstance(r, dict):
        return ""
    ss = r.get("ss") or {}
    prec = r.get("prec") or {}
    if ss.get("cid"):
        title = ss.get("title") or "上一课"
        where = ss.get("subject") or ""
        if ss.get("grade"):
            where = (where + " " + str(ss.get("grade"))).strip()
        return "《%s》%s" % (title, ("（" + where + "）") if where else "")
    if prec.get("practice"):
        p = prec["practice"]
        return "%s 的练习《%s》" % (prec.get("subject") or "", p.get("title") or "上一次" )
    if prec.get("diag"):
        return "%s 的精准学诊断" % (prec.get("subject") or "上一次")
    if prec.get("subject"):
        return "%s 的精准学" % prec["subject"]
    return ""


def build_context_text(ctx):
    """把学情 dict 渲染成给模型看的多行文本。"""
    ctx = ctx or {}
    lines = []
    lines.append("- 孩子：%s" % (ctx.get("child") or "小朋友"))
    lines.append("- 今天已学：%d 分钟（目标 %d 分钟）" %
                 (_fmt_min(ctx.get("today_sec")), int(ctx.get("daily_max") or 30)))
    lines.append("- 连续学习：%d 天；累计星星：%d 颗" %
                 (int(ctx.get("streak") or 0), int(ctx.get("stars") or 0)))
    lines.append("- 已掌握知识点：%d 个；待复习错题：%d 道" %
                 (int(ctx.get("mastered") or 0), int(ctx.get("mistake_todo") or 0)))
    rs = _describe_resume(ctx.get("resume"))
    if rs:
        lines.append("- 上次学到：%s（可以让他接着学）" % rs)
    if ctx.get("weak"):
        _wk = [(x.get("title") if isinstance(x, dict) else str(x)) for x in ctx["weak"][:3]]
        lines.append("- 薄弱知识点：%s" % "、".join([w for w in _wk if w]))
    if ctx.get("pending_course"):
        pc = ctx["pending_course"]
        lines.append("- 系统推荐的下一课：《%s》（%s %s）" %
                     (pc.get("title") or "", pc.get("subject") or "", pc.get("grade") or ""))
    if ctx.get("view"):
        lines.append("- 孩子当前所在页面：%s" % ctx.get("view"))
    if ctx.get("now_course"):
        lines.append("- 孩子正在看的课程：《%s》" % ctx.get("now_course"))
    return "\n".join(lines)


def _greet_word(hour):
    if 5 <= hour < 11:
        return "早上好"
    if 11 <= hour < 14:
        return "中午好"
    if 14 <= hour < 18:
        return "下午好"
    if 18 <= hour < 23:
        return "晚上好"
    return "这么晚还在学呀"


def build_opening(ctx, hour=9):
    """生成学伴主动开场白 + 动作按钮（纯本地规则，无需大模型，秒回）。

    优先级：断点续学 > 错题待复习 > 薄弱知识点 > 今日目标未达 > 首次引导。
    """
    ctx = ctx or {}
    child = ctx.get("child") or "小朋友"
    name = child[-2:] if len(child) > 2 else child
    greeting = "%s，%s！" % (_greet_word(hour), name)
    today_min = _fmt_min(ctx.get("today_sec"))
    daily_max = int(ctx.get("daily_max") or 30)
    streak = int(ctx.get("streak") or 0)
    stars = int(ctx.get("stars") or 0)
    mistake_todo = int(ctx.get("mistake_todo") or 0)
    mastered = int(ctx.get("mastered") or 0)
    resume = ctx.get("resume")
    weak = ctx.get("weak") or []
    pending = ctx.get("pending_course") or {}

    actions = []
    mood = "guide"
    opening = ""

    resume_desc = _describe_resume(resume)
    # ① 断点续学
    if resume_desc:
        mood = "encourage"
        opening = ("%s 我们上次在学 %s，还差一点点就成功了，今天把它拿下好不好？") % (name, resume_desc)
        actions.append({"id": "resume", "label": "继续学习", "icon": "▶", "type": "route", "target": "resume"})
    # ② 错题待复习
    if mistake_todo > 0:
        if not opening:
            mood = "remind"
            opening = ("%s 你有 %d 道错题还在等着被攻克，攻克它们就像打 BOSS，敢不敢试试？") % (name, mistake_todo)
        actions.append({"id": "review", "label": "温习错题", "icon": "🔄", "type": "route",
                        "target": "mistakes"})
    # ③ 薄弱知识点 → 练几题
    if weak:
        wk = weak[0] if isinstance(weak[0], str) else (weak[0].get("title") or "")
        if not opening:
            mood = "remind"
            opening = ("%s 我发现你在《%s》上还有一点小疙瘩，我们练几道题把它捋顺吧？") % (name, wk)
        actions.append({"id": "practice", "label": "练几道题", "icon": "📝", "type": "route",
                        "target": "practice", "course_id": (weak[0].get("id") if isinstance(weak[0], dict) else "")})
    # ④ 今日目标 / 学习建议
    if not opening:
        if today_min >= daily_max:
            mood = "congratulate"
            opening = ("%s 你今天已经学了 %d 分钟，超过目标啦，真棒！要不要再挑战一个新知识点？") % (name, today_min)
        elif today_min > 0:
            mood = "encourage"
            opening = ("%s 你今天已经学了 %d 分钟，再坚持 %d 分钟就完成目标了，我们继续？") % (
                name, today_min, max(1, daily_max - today_min))
        else:
            mood = "guide"
            if streak >= 2:
                opening = ("%s 你已经连续学习 %d 天啦，今天也来开个头吧（只要 5 分钟）？") % (name, streak)
            else:
                opening = ("%s 今天想从哪里开始？我推荐先学一新课，或者我们直接聊天，你想学什么都可以问我。") % name
    # 主推荐动作（保证 >=2 个）
    if pending.get("course_id"):
        actions.append({"id": "learn_new", "label": "学新课", "icon": "📖", "type": "route",
                        "target": "learn", "course_id": pending.get("course_id"),
                        "title": pending.get("title") or ""})
    if not actions:
        actions.append({"id": "learn_new", "label": "学新课", "icon": "📖", "type": "route",
                        "target": "selfstudy"})
    if len(actions) < 2:
        actions.append({"id": "chat", "label": "和我说说", "icon": "💬", "type": "chat",
                        "text": "我想随便聊聊"})
    if len(actions) < 3:
        actions.append({"id": "practice2", "label": "随便练练", "icon": "✏️", "type": "route",
                        "target": "practice"})
    actions = actions[:3]

    return {
        "greeting": greeting,
        "opening": opening,
        "mood": mood,
        "actions": actions,
        "done_today": today_min >= daily_max,
        "context": {
            "child": child,
            "today_min": today_min,
            "daily_max": daily_max,
            "streak": streak,
            "stars": stars,
            "mastered": mastered,
            "mistake_todo": mistake_todo,
            "resume_desc": resume_desc,
        },
    }


def build_companion_messages(ctx, history, user_message, course_context=None):
    """构造学伴对话 messages。history 为 [{"role","content"}]。"""
    ctx = ctx or {}
    child = ctx.get("child") or "小朋友"
    course_txt = ""
    if ctx.get("now_course") or course_context:
        course_txt = "# 孩子当前正在学的课程\n" + (course_context or ("《%s》" % ctx.get("now_course")))
    system = (COMPANION_PROMPT
              .replace("<<CHILD>>", child)
              .replace("<<CONTEXT>>", build_context_text(ctx))
              .replace("<<COURSE>>", course_txt))
    msgs = [{"role": "system", "content": system}]
    for h in (history or []):
        role = h.get("role") if isinstance(h, dict) else None
        content = h.get("content") if isinstance(h, dict) else None
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    if user_message:
        msgs.append({"role": "user", "content": user_message})
    return msgs


def mock_companion(ctx, user_message):
    """演示模式 / 断网 / 没配 Key 时的学伴：优先走本地知识引擎，不靠大模型也能讲能考。

    处理优先级：判分 > 情绪安抚 > 讲知识点 > 出题 > 学习建议 > 错题 > 检索 > 兜底。
    """
    ctx = ctx or {}
    child = ctx.get("child") or "小朋友"
    name = child[-2:] if len(child) > 2 else child
    msg = (user_message or "").strip()
    low = msg.lower()
    quiz_state = ctx.get("quiz_state") or {}

    def reply(text, emotion="curiosity", suggest=None, card=None):
        out = {"reply": text, "emotion": emotion, "suggest": suggest or [],
               "speak": True, "offline_engine": True}
        if card:
            out["card"] = card
        return json.dumps(out, ensure_ascii=False)

    def _topic_from_msg():
        return find_topic_by_text(msg, ctx) or ctx.get("course_id") or ctx.get("now_course_id")

    if not msg:
        return reply("%s，今天想学点什么？你说，我陪你。" % name)

    # ---------- (1) 有未判分的题：先把这句当答案判 ----------
    if quiz_state.get("topic_id") and quiz_state.get("awaiting") and len(msg) <= 40:
        g = quiz_grade(quiz_state["topic_id"], quiz_state.get("quiz_index", 0), msg)
        if g:
            if g["correct"]:
                return reply("答对啦！\n" + (g["explanation"] or ""),
                             "satisfaction",
                             [{"label": "再练一题", "action": "quiz"},
                              {"label": "学下一节", "action": "learn_new"}],
                             card={"type": "quiz_result", "correct": True,
                                   "answer": g["answer"], "explanation": g["explanation"]})
            return reply("别急，我们再来一次。\n" + g["text"],
                         "confusion",
                         [{"label": "再想一题", "action": "quiz"},
                          {"label": "讲讲这节", "action": "explain"}],
                         card={"type": "quiz_result", "correct": False,
                               "answer": g["answer"], "explanation": g["explanation"]})

    # ---------- (2) 情绪优先：累了先接住，再给最小任务 ----------
    if any(k in msg for k in ["累", "烦", "不想", "困", "讨厌", "太难", "不会做"]):
        tgt = _topic_from_msg()
        act = [{"label": "休息一下", "action": "rest"}]
        tail = ""
        if tgt and _lesson(tgt):
            s = topic_summary(tgt)
            if s:
                tail = "\n等你回来，我们只学一小段：《%s》。" % (s.get("title") or "")
                act.append({"label": "学一小段", "action": "explain", "topic_id": tgt})
        if len(act) < 2:
            act.append({"label": "来道简单的", "action": "practice"})
        return reply("%s 先喘口气，累的时候学不进去很正常。休息 2 分钟，回来只做一点点就行。%s" % (name, tail),
                     "frustration", act)

    # ---------- (3) 要讲知识点：用真实讲义讲 ----------
    wants_explain = any(k in msg for k in ["讲", "解释", "是什么", "是啥", "说说", "介绍",
                                           "学一下", "教我", "怎么回事", "什么意", "意思是"])
    if wants_explain or _wants_current(msg):
        tgt = _topic_from_msg()
        if tgt:
            sec_idx = int(ctx.get("section_idx") or 0)
            ex = explain_topic(tgt, sec_idx)
            if ex:
                qs = get_quiz(tgt)
                act = []
                if ex.get("has_next"):
                    act.append({"label": "下一部分", "action": "explain_next", "topic_id": tgt,
                                "section_idx": ex["section_idx"] + 1})
                if qs:
                    act.append({"label": "考考我", "action": "quiz", "topic_id": tgt})
                if len(act) < 2:
                    act.append({"label": "看整课", "action": "learn_new", "course_id": tgt})
                tips = topic_tips(tgt)
                body = ex["text"]
                if tips and ex["section_idx"] == ex["section_total"] - 1:
                    body += "\n注意别踩坑：" + "；".join(tips[:2])
                return reply(body, "curiosity", act[:3],
                             card={"type": "lesson", "topic_id": tgt,
                                   "title": ex.get("title"), "heading": ex.get("heading"),
                                   "section_idx": ex["section_idx"],
                                   "section_total": ex["section_total"]})
        else:
            return reply("%s 你说的这个我暂时没找到对应课程。你可以说个更具体的，比如「讲讲分数」，或者去「同步学」里挑。" % name,
                         "confusion", [{"label": "去同步学", "action": "learn_new"}])

    # ---------- (4) 要出题 / 练题：从题库真出题 ----------
    if any(k in msg for k in ["题", "练习", "做题", "练", "考我", "测验", "测试"]) or ctx.get("want_quiz"):
        tgt = _topic_from_msg()
        q = quiz_present(tgt, int(ctx.get("quiz_index") or 0)) if tgt else None
        if q:
            return reply("来，我给你出一道关于《%s》的题，先说你的答案，我再讲。\n\n%s" % (q["title"], q["text"]),
                         "curiosity",
                         [{"label": "换一题", "action": "quiz"},
                          {"label": "不会，讲讲", "action": "explain", "topic_id": tgt}],
                         card={"type": "quiz", "topic_id": tgt, "quiz_index": q["quiz_index"],
                               "quiz_total": q["quiz_total"], "stem": q["stem"],
                               "options": q["options"], "kind": q["kind"]})
        return reply("这个知识点还没配题库，我们先读一遍讲义再来考，好不好？",
                     "curiosity", [{"label": "讲讲这节", "action": "explain"}])

    # ---------- (5) 学什么 / 计划 ----------
    if any(k in msg for k in ["学什么", "学点啥", "今天", "开始", "计划", "安排"]):
        rs = _describe_resume(ctx.get("resume"))
        if rs:
            return reply("%s 我建议先把上次的 %s 收个尾，只要几分钟，然后奖励你一个新知识点！" % (name, rs),
                         "curiosity", [{"label": "继续学习", "action": "continue"},
                                       {"label": "学新课", "action": "learn_new"}])
        pc = ctx.get("pending_course") or {}
        if pc.get("course_id"):
            s = topic_summary(pc["course_id"])
            body = "%s 我们今天从《%s》开始吧。" % (name, pc.get("title") or "")
            if s:
                body += "\n" + s["text"]
            return reply(body, "curiosity",
                         [{"label": "开始学", "action": "explain", "topic_id": pc["course_id"]},
                          {"label": "考考我", "action": "quiz", "topic_id": pc["course_id"]}])
        return reply("%s 我们先学一新课吧，你想学哪科？" % name, "curiosity",
                     [{"label": "学新课", "action": "learn_new"}])

    # ---------- (6) 错题复习 ----------
    if any(k in msg for k in ["错题", "复习", "温习", "回顾"]):
        todo = int(ctx.get("mistake_todo") or 0)
        if todo:
            return reply("你手上有 %d 道错题等着被攻克，咱们一道一道来，我陪你。" % todo,
                         "remind", [{"label": "去错题本", "action": "review"},
                                    {"label": "先练几题", "action": "practice"}])
        return reply("你的错题本现在是空的，说明之前学得挺扎实！那我们去学点新东西吧。",
                     "satisfaction", [{"label": "学新课", "action": "learn_new"}])

    # ---------- (7) 找课程：用户提到了某科某内容 ----------
    hits = search_topics(msg)
    if hits:
        h = hits[0]
        s = topic_summary(h["topic_id"])
        body = "我找到这节课：《%s》%s %s" % (h["title"], h["subject"], h["grade"])
        if s and s.get("text"):
            body += "\n" + s["text"]
        acts = [{"label": "学这节", "action": "explain", "topic_id": h["topic_id"]},
                {"label": "考考我", "action": "quiz", "topic_id": h["topic_id"]}]
        return reply(body, "curiosity", acts)

    # ---------- (8) 答对了 / 打招呼 ----------
    if any(k in msg for k in ["谢谢", "明白了", "懂了", "会了", "知道了"]):
        return reply("太棒了！能自己想明白，比听我讲十遍都值。要不要我考考你？",
                     "satisfaction", [{"label": "考考我", "action": "quiz"},
                                      {"label": "学下一节", "action": "learn_new"}])
    if "你好" in msg or "hi" in low or "hello" in low:
        return reply("%s 你好呀！我是小艾。你可以说「讲讲上学歌」，或者说「考考我」，我都能接住。" % name)

    # ---------- (9) 兜底：给出可点的事，而不是只说空话 ----------
    tgt = _topic_from_msg()
    acts = [{"label": "讲一课", "action": "explain"}]
    if tgt and get_quiz(tgt):
        acts.append({"label": "考考我", "action": "quiz", "topic_id": tgt})
    if len(acts) < 2:
        acts.append({"label": "去同步学", "action": "learn_new"})
    return reply("我在听呢。你可以直接说：「讲讲分数」「考考我」「我有点累」，或者点下面的按钮。",
                 "neutral", acts[:2])


def parse_companion_reply(text, fallback_ctx=None):
    """解析模型输出 → {reply, emotion, suggest, speak}；异常时用纯文本兜底。"""
    if not text:
        return {"reply": "我在呢，你说吧～", "emotion": "neutral", "suggest": [], "speak": True}
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()
    obj = None
    try:
        obj = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
    if not isinstance(obj, dict):
        return {"reply": raw[:400], "emotion": "neutral", "suggest": [], "speak": True}
    reply = (obj.get("reply") or "").strip() or raw[:400]
    emotion = obj.get("emotion") or "neutral"
    valid = ("curiosity", "confusion", "frustration", "excitement", "satisfaction",
             "boredom", "anxiety", "neutral")
    if emotion not in valid:
        emotion = "neutral"
    suggest = []
    for s in (obj.get("suggest") or [])[:3]:
        if isinstance(s, dict) and s.get("label"):
            item = {"label": str(s.get("label"))[:8], "action": s.get("action") or "none"}
            # 透传定位信息，前端按钮才能直接跳到对应知识点/小节
            for k in ("topic_id", "course_id", "section_idx"):
                if s.get(k) not in (None, ""):
                    item[k] = s.get(k)
            suggest.append(item)
        elif isinstance(s, str) and s.strip():
            suggest.append({"label": s.strip()[:8], "action": "none"})
    out = {"reply": reply, "emotion": emotion, "suggest": suggest,
           "speak": bool(obj.get("speak", True))}
    if isinstance(obj.get("card"), dict):
        out["card"] = obj["card"]
    if obj.get("offline_engine"):
        out["offline_engine"] = True
    return out

# -*- coding: utf-8 -*-
"""测量全学科课后自测题的“泛化模板题”占比，定位 _subject_quiz 未覆盖的子点。"""
import curriculum as C
import server as S
import importlib

# 重新加载以确保用最新代码
importlib.reload(S)

# 判定为“垃圾选项（学习方法废话）”的强信号：选项文本片段
GARBAGE_OPT = [
    "只需要背结论", "背结论就能", "与前后知识没有任何联系", "考试时一定不会出现",
    "只需了解大概", "记住关键词就能得满分", "考前突击", "抄写例题就算学会",
    "只背结论不求甚解", "完全依赖老师讲解不思考", "只看答案不理解过程", "死记硬背所有术语",
    "只看一遍就会", "不需要任何练习", "可跳过", "极少出现", "不必重点练习", "不需要注意任何细节",
    "凭直觉即可", "与其他内容完全相同", "只要记住公式就不会出错", "不考虑适用条件", "可以混用",
    "只要套用", "无需重点", "就能解决所有问题", "得满分", "了解大概即可", "只需了解",
    "不必深入", "了解皮毛", "不求甚解", "只背结论", "只要套用", "不需要考虑适用条件",
    "只看答案不理解", "死记硬背所有", "只记名称", "最不重要的部分", "完全不同的另一门学科",
    "只需记住名称", "不必深入理解", "可略过", "无需深入理解",
]

# 仅作“弱模板”统计：题干为纯泛化模板、且未嵌入任何具体事实。
# 注：「关于易错点，下列说法正确的是」现已承载真实易错提醒（题干嵌入具体提醒），属实质题，不再计弱。
WEAK_STEM = [
    "」中的「",            # “关于「标题」中的「子点」”（未嵌入具体事实的纯泛化模板）
    "学习「",
    "若想真正掌握",
    "的说法中，错误的是",
]


def is_garbage(q):
    """返回 (是否垃圾选项, 原因)。垃圾=选项含学习方法废话。"""
    if not q:
        return True, "EMPTY"
    opts = q.get("options") or []
    for o in opts:
        for frag in GARBAGE_OPT:
            if frag in str(o):
                return True, f"OPT:{frag}"
    return False, "OK"


def is_weak(q):
    """返回 (是否弱模板题干, 原因)。弱模板=题干是泛化模板，但选项为真实内容（可接受但不完美）。"""
    if not q:
        return False, ""
    stem = q.get("stem", "")
    for frag in WEAK_STEM:
        if frag in stem:
            return True, f"STEM:{frag}"
    return False, ""


def main():
    total = 0
    garbage = 0
    weak = 0
    by_subject = {}
    examples = []
    for tid, topic in C.TOPIC_INDEX.items():
        subject = topic.get("subject", "")
        title = topic.get("title", "")
        subs = topic.get("sub") or [title]
        for si in range(len(subs)):
            total += 1
            q = S.mock_test_q(topic, si, course_id=tid)
            g, why = is_garbage(q)
            wk, _ = is_weak(q)
            rec = by_subject.setdefault(subject, {"n": 0, "gar": 0, "weak": 0})
            rec["n"] += 1
            if g:
                rec["gar"] += 1
                garbage += 1
                if len(examples) < 60:
                    examples.append((subject, subs[si], why, q.get("stem", "")[:60]))
            elif wk:
                rec["weak"] += 1
                weak += 1
    print(f"=== 全量课后自测质量扫描（mock_test_q 兜底路径，无 Gen 内容）===")
    print(f"总子点题数: {total}  垃圾选项题: {garbage} ({garbage/total*100:.1f}%)  "
          f"弱模板题: {weak} ({weak/total*100:.1f}%)  实质题: {total-garbage-weak} ({(total-garbage-weak)/total*100:.1f}%)\n")
    print(f"{'学科':<8}{'子点数':>8}{'垃圾':>8}{'弱模板':>9}")
    print("-" * 36)
    for subj, rec in sorted(by_subject.items(), key=lambda x: -x[1]["gar"]):
        n, gar, wk = rec["n"], rec["gar"], rec["weak"]
        print(f"{subj:<8}{n:>8}{gar:>8}{wk:>9}")
    print("\n=== 残留垃圾题样例（前60）===")
    for subj, sub, why, stem in examples:
        print(f"[{subj}|{sub}|{why}] {stem}")


if __name__ == "__main__":
    main()

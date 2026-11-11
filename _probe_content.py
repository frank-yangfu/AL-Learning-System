# -*- coding: utf-8 -*-
import curriculum as C
import server as S
import importlib
importlib.reload(S)

probes = [
    ("语文", "青蛙写诗"),
    ("语文", "曹冲称象"),
    ("语文", "观潮"),
    ("物理", "速度"),
    ("物理", "浮力"),
    ("历史", "鸦片战争"),
    ("地理", "地球自转"),
    ("生物", "细胞"),
    ("化学", "二氧化碳"),
]
for subject, sub in probes:
    # find a topic whose sub contains this
    found = None
    for tid, t in C.TOPIC_INDEX.items():
        if t.get("subject") == subject and sub in (t.get("sub") or []):
            found = t
            break
    if not found:
        print(f"### {subject}/{sub}: NOT FOUND")
        continue
    text = C._explain_sub(found["title"], subject, sub, course_id=found["id"]) or ""
    print(f"### {subject}/{sub}  (title={found['title']})  len={len(text)}")
    print(text[:500].replace("\n", " ⏎ "))
    print("-" * 60)

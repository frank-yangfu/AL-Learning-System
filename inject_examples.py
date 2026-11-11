#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一批「例题讲解」注入到 curriculum_gen.json 对应子点正文。
输入 JSON 文件格式：[{"key":<course_id>, "sub":<子点名>, "example":<例题文本>}, ...]
按 (key, sub) 精确匹配；若已含例题标记则跳过。幂等可重跑。
"""
import json, os, sys

GEN = "curriculum_gen.json"
MARK = "【📝 例题讲解】"

def main():
    if len(sys.argv) < 2:
        print("usage: inject_examples.py <batch_json_file>")
        sys.exit(1)
    batch_file = sys.argv[1]
    batch = json.load(open(batch_file, encoding="utf-8"))
    if isinstance(batch, dict):
        batch = batch.get("items", [])

    data = json.load(open(GEN, encoding="utf-8"))
    total = len(batch)
    injected = 0
    skipped = 0
    notfound = 0
    for item in batch:
        key = item["key"]
        sub = item["sub"]
        example = (item.get("example") or "").strip()
        if not example:
            skipped += 1
            continue
        course = data.get(key)
        if not isinstance(course, dict):
            notfound += 1
            continue
        hit = False
        for s in course.get("subs", []):
            if s.get("sub") == sub:
                hit = True
                c = s.get("content") or ""
                if MARK in c or "例题讲解" in c:
                    skipped += 1
                else:
                    s["content"] = c.rstrip() + "\n\n" + MARK + "\n\n" + example + "\n"
                    injected += 1
                break
        if not hit:
            notfound += 1

    # 原子写
    tmp = GEN + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, GEN)
    print(f"batch={os.path.basename(batch_file)} total={total} injected={injected} skipped={skipped} notfound={notfound}")

if __name__ == "__main__":
    main()

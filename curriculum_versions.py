# -*- coding: utf-8 -*-
"""教材版本管理（新旧版本分开）。

设计要点：
  1) 每个版本一份独立的课程树，互不影响；
  2) 新版知识点的 id 带版本后缀（如 -n24），因此掌握度/错题/学习进度
     按 course_id 天然隔离——切换版本不会串数据；
  3) 旧版 = 现有 curriculum.CURRICULUM 原样保留（不改动一个字）；
  4) 新版内容放在 NEW_CURRICULUM_2024.json，热加载、可持续补充。

版本清单由 /api/curriculum/versions 返回，前端在自学页顶部切换。
"""
from __future__ import annotations
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_NEW_JSON = os.path.join(BASE_DIR, "curriculum_2024.json")

# ---------------- 版本元数据 ----------------
# id 用于接口参数与本地存储；legacy 为默认，保证现有用户打开还是原来的课
VERSIONS = [
    {
        "id": "legacy",
        "name": "旧版教材（现行·人教版/统编版）",
        "short": "旧版",
        "year": "2019 及以前",
        "textbook": "人教版 / 统编版",
        "standard": "依据《义务教育课程方案（2022年版）》之前的教材体系整理",
        "note": "系统原有课程，共 637 个知识点，含讲义与小测。",
        "is_default": True,
        "status": "stable",
    },
    {
        "id": "n24",
        "name": "2024 新课标版（统编/人教新版）",
        "short": "2024 新版",
        "year": "2024 年起分年级铺开",
        "textbook": "统编版 2024 / 人教版 2024（新课标）",
        "standard": "依据《义务教育课程方案和课程标准（2022年版）》修订",
        "note": "按新课标修订的新教材，逐年替换，与旧版分开存放。",
        "is_default": False,
        "status": "stable",
    },
]

VERSION_INDEX = {v["id"]: v for v in VERSIONS}
DEFAULT_VERSION = "legacy"


def list_versions():
    return [dict(v) for v in VERSIONS]


def get_version(vid):
    return VERSION_INDEX.get(vid or DEFAULT_VERSION) or VERSION_INDEX[DEFAULT_VERSION]


# ---------------- 新版课程树（外部 JSON，热加载） ----------------
_NEW_CACHE = {"mtime": 0, "data": []}


def load_new_curriculum():
    """读取 curriculum_2024.json，返回 [ 学段 -> 学科 -> 年级 -> 知识点 ]。"""
    try:
        mt = os.path.getmtime(_NEW_JSON)
    except OSError:
        return []
    if mt == _NEW_CACHE["mtime"] and _NEW_CACHE["data"]:
        return _NEW_CACHE["data"]
    try:
        with open(_NEW_JSON, "r", encoding="utf-8") as f:
            obj = json.load(f)
        data = obj.get("curriculum", obj) if isinstance(obj, dict) else obj
        if not isinstance(data, list):
            data = []
        _NEW_CACHE["data"] = data
        _NEW_CACHE["mtime"] = mt
        return data
    except Exception:
        return []


def new_topic_count():
    n = 0
    for st in load_new_curriculum():
        for subj in st.get("subjects", []):
            for g in subj.get("grades", []):
                n += len(g.get("topics", []))
    return n


def build_version_index(base_index, version_id):
    """把某版本的课程树展开成 {id: topic}。旧版直接复用原索引。"""
    if version_id == "legacy":
        return dict(base_index)
    out = {}
    for st in load_new_curriculum():
        stage = st.get("stage", "")
        for subj in st.get("subjects", []):
            subject = subj.get("name", "")
            for g in subj.get("grades", []):
                grade = g.get("grade", "")
                for tp in g.get("topics", []):
                    t = dict(tp)
                    t["stage"] = stage
                    t["subject"] = subject
                    t["grade"] = grade
                    t["lang"] = subj.get("lang", t.get("lang", "zh"))
                    t["version"] = version_id
                    out[t["id"]] = t
    return out


def curriculum_for(version_id):
    """返回该版本完整课程树（供前端目录使用）。

    legacy 返回 None（调用方用原有 C.CURRICULUM）；
    其他版本 = 新版树 + 跨版本的「拓展与素养」（素养课不属于任一本教材，
    两个版本下都可见、进度 id 相同，不会重复计算）。
    """
    if version_id == "legacy":
        return None
    tree = load_new_curriculum()
    try:
        import curriculum as _C   # 延迟导入，避免循环依赖
        extra = getattr(_C, "EXTRA_CURRICULUM", None) or []
        if extra:
            tree = list(tree) + list(extra)
    except Exception:
        pass
    return tree

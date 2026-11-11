#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AL 自学系统 —— 轻量后端（零第三方依赖）

技术栈：Python 标准库（http.server + sqlite3 + urllib）
功能：注册/登录、LLM 设置（默认 DeepSeek）、角色 CRUD、
      苏格拉底式对话（调用大模型或演示模式）、会话与知识图谱持久化。

运行：python server.py   （默认端口 8000）
"""

import json
import os
import re
import sys
import time
import sqlite3
import hashlib
import secrets
import base64
import urllib.request
import urllib.error
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
import asyncio
import curriculum as C
import seed_bank as SB
import companion as COMP
# 把本地课程库接到学伴的「本地知识引擎」上：没配大模型 / 断网时，
# 学伴也能从 637 个知识点的讲义里讲课、从题库里出题判分。
try:
    COMP.bind_knowledge(C.get_lesson, C.TOPIC_INDEX)
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(DATA_DIR, "app.db")
os.makedirs(DATA_DIR, exist_ok=True)

# CORS：公网部署时必须由环境变量限定，不设则拒绝外部来源
_ALLOWED_ORIGINS_RAW = os.environ.get("ALLOWED_ORIGINS", "").strip()
if not _ALLOWED_ORIGINS_RAW:
    # 无环境变量时：本机 localhost / 局域网允许，纯公网来源拒绝（非 "*"）
    ALLOWED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
else:
    ALLOWED_ORIGINS = [o.strip() for o in _ALLOWED_ORIGINS_RAW.split(",") if o.strip()]

# 8 类教育情绪 -> 教学策略
EMOTION_STRATEGY = {
    "curiosity": "顺势深入提问，拓展广度",
    "confusion": "退一步，用类比重新解释",
    "frustration": "共情安抚，降低难度，小步引导",
    "excitement": "趁热打铁加深难度",
    "satisfaction": "引入下一层级知识",
    "boredom": "换教学方式，引入挑战",
    "anxiety": "放慢节奏，强调过程，给予肯定",
    "neutral": "保持温和节奏，正常引导",
}
EMOTION_LABEL = {
    "curiosity": "好奇", "confusion": "困惑", "frustration": "挫败",
    "excitement": "兴奋", "satisfaction": "满足", "boredom": "无聊",
    "anxiety": "焦虑", "neutral": "平和",
}

# 诊断 / 练习 / 课后自测 会话：持久化到 SQLite（避免重启丢失）
_ASSESSMENT_DB = os.path.join(BASE_DIR, "data", "assessment_sessions.db")

def _init_assessment_db():
    conn = sqlite3.connect(_ASSESSMENT_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS diag (id TEXT PRIMARY KEY, payload TEXT, updated_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS practice (id TEXT PRIMARY KEY, payload TEXT, updated_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS test (id TEXT PRIMARY KEY, payload TEXT, updated_at TEXT)")
    conn.commit(); conn.close()
_init_assessment_db()

DIAG_SESSIONS = {}
PRACTICE_SESSIONS = {}
TEST_SESSIONS = {}


# 掌握度标签（五级阶梯，循序渐进）：
# 0 未测 / 1 未掌握 / 2 了解(通过第一关·说出来) / 3 熟悉(通过前两关) / 4 掌握(三关全过)
MASTERY_LABEL = {0: "未测", 1: "未掌握", 2: "了解", 3: "熟悉", 4: "掌握"}
VERDICT_LEVEL = {"掌握": 4, "熟悉": 3, "了解": 2, "未掌握": 1}

# 关系阶段（随学习深入推进）
STAGE_NAMES = ["初识", "熟悉", "信赖", "默契", "亦师亦友"]

# 静态层 Prompt 模板（苏格拉底教学法 + 反答案泄漏 + 结构化输出）
SYSTEM_PROMPT_TEMPLATE = """你是一位名为「<<NAME>>」的 AI 导师，正在使用苏格拉底教学法引导学习者独立思考。

# 你的身份与人格
<<PERSONA>>

# 教学风格
<<STYLE>>

# 当前课程主题
<<COURSE>>

# 核心原则（苏格拉底式）
1. 永远不直接给出结论性答案，而是用提问引导学习者自己推导。
2. 把大问题拆成小问题，循序渐进，一步步逼近本质。
3. 鼓励学习者解释"为什么"，暴露并纠正其思维过程。
4. 当学习者答错时，不直接否定，而用反例或追问让其自行发现矛盾。
5. 适当使用类比、生活例子，让抽象概念变得可感。

# 反答案泄漏规则（最高优先级）
- 严禁直接说出最终答案或完整解题步骤。
- 若学习者要求"直接告诉我答案"，须礼貌拒绝，并换一种提问方式继续引导。
- 你的作用是点亮思路，而不是代劳。

# 当前教学上下文
- 关系阶段：<<STAGE>>
- 学习者上一条消息呈现的情绪：<<LAST_EMOTION>>
- 针对该情绪应采用的教学策略：<<STRATEGY>>

# 输出格式（必须严格遵守：只输出一个 JSON 对象，不要任何额外文字或 Markdown）
{
  "reply": "你对学习者的苏格拉底式回应（中文，1-3 句话，必须包含至少一个引导性问题）",
  "emotion": "从以下 8 类中选择最贴合学习者本条消息的情绪：curiosity / confusion / frustration / excitement / satisfaction / boredom / anxiety / neutral",
  "concepts": ["本条对话中出现的核心知识点（2-4 个中文名词）"],
  "relations": [["知识点A", "知识点B", "关系类型，如 前置/包含/对比/因果/例证"]],
  "stage_hint": "根据学习者表现判断是否需要推进关系阶段：keep 或 advance"
}"""

# 课后测评 Prompt 模板（闯关式掌握度测评：循序渐进、明确过关标准）
ASSESS_PROMPT_TEMPLATE = """你是一位名为「<<NAME>>」的 AI 导师，正在对学习者进行「<<TOPIC>>」这个知识点的掌握度测评。

你的目标不是重新教学，而是检验学习者是否真正理解、并能独立运用该知识点。请采用「闯关式」测评，循序渐进地带领学生逐关突破，每关都有明确的过关标准。

# 本次测评知识点
<<COURSE>>

# 测评核心内容（逐项检验）
<<CORE>>

# 测评方法：三关递进，逐关闯关
本知识点必须按顺序带领学生闯过以下三关，每一关都有明确的「过关标准」。只有依次通过全部三关，才算真正「掌握」。

第一关 · 说出来（理解）
- 你出的题：请学生用【自己的话】讲清这个知识点的核心概念，并举一个贴切的生活例子。
- 过关标准：学生能用自然语言准确说出核心意思（不要求背原话或定义），且例子与知识点相关、贴切。
- 通过此关 → 掌握度达到「了解」。

第二关 · 做出来（应用）
- 你出的题：请学生【独立做对一道基础题】，写出完整解题步骤与最终答案（可先给提示，但最终要他自己写出）。
- 过关标准：解题步骤正确、关键方法用对、答案正确。
- 通过此关 → 掌握度达到「熟悉」。

第三关 · 讲明白（迁移）
- 你出的题：换一个学生【没见过的新情境】，请他自己分析并解决；或请他把这个知识点讲给「一位完全不懂的同学」听（费曼式）。
- 过关标准：能迁移到新情境、思路清晰；或能教会别人（讲得让小白也听懂）。
- 通过此关 → 掌握度达到「掌握」。

# 执行规则（必须严格遵守）
1. 严格按 第一关 → 第二关 → 第三关 的顺序进行，一次只问一个问题。
2. 每一关【先讲清这一关要做到什么程度才算过关】（即上面的过关标准），再出对应的题。
3. 学生卡住时只给提示（hint），不要直接给答案；用追问帮他自行想通。可让他重试本关，绝不跳关。
4. 用鼓励、有安全感的语言，让学生敢说、愿说、愿意试错。
5. 当学生通过当前关，进入下一关前，明确告知「✅ 第X关已过」。
6. verdict 必须严格按已通过的关卡数判定：三关全过 → 「掌握」；通过前两关 → 「熟悉」；仅通过第一关 → 「了解」；一关都没过 → 「未掌握」。
7. 一旦给出 verdict（非空），本回合即为测评总结：在 reply 里给出下一步复习建议，并明确告诉学生「还差哪一关就能达到掌握」。

# 输出格式（必须严格遵守：只输出一个 JSON 对象，不要任何额外文字或 Markdown）
{
  "reply": "你要对学生说的那一段话（直接说，不要加「你对本条消息的回应」之类前缀，也不要出现 JSON 或字段名）。例如：『同学，我们先闯第一关——说说你对分数的理解，并举一个生活里的例子吧。』",
  "stage": 当前正在测评的关卡编号（1 / 2 / 3 的整数；尚未开始时为 1）,
  "stage_pass": 学生本回合是否通过了当前这一关（true / false 的布尔值；未到判定时按实际情况填写）,
  "criteria": "当前这一关的过关标准（一句话，用于展示给学生，让他知道要做到什么程度）",
  "verdict": "三关全过填「掌握」；通过前两关填「熟悉」；仅通过第一关填「了解」；一关未过填「未掌握」；还需继续测评则填空字符串 \\"\\"",
  "verdict_reason": "一句话说明：通过了哪些关、还差哪一关才能达到掌握（verdict 非空时填写）",
  "emotion": "从 curiosity / confusion / frustration / excitement / satisfaction / boredom / anxiety / neutral 中选择",
  "concepts": ["相关知识点（1-3 个）"]
}
注意：verdict 必须严格为「掌握」「熟悉」「了解」「未掌握」四者之一或空字符串。"""


# ----------------------------- 数据库 -----------------------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY,
        api_key TEXT,
        base_url TEXT,
        model TEXT,
        mock_mode INTEGER DEFAULT 0,
        r_api_key TEXT,
        r_base_url TEXT,
        r_model TEXT
    );
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        persona TEXT,
        teaching_style TEXT,
        course TEXT,
        world_setting TEXT,
        lang TEXT DEFAULT 'zh',
        relationship_stage INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        title TEXT,
        checkpoint TEXT,
        course_id TEXT,
        is_assessment INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS mastery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        level INTEGER DEFAULT 0,
        attempts INTEGER DEFAULT 0,
        last_eval TEXT,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, course_id)
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        emotion TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS kg_nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, role_id, label)
    );
    CREATE TABLE IF NOT EXISTS kg_edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        source TEXT NOT NULL,
        target TEXT NOT NULL,
        rel TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, role_id, source, target, rel)
    );
    CREATE TABLE IF NOT EXISTS mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        tier TEXT NOT NULL,
        stem TEXT NOT NULL,
        options TEXT,
        answer TEXT NOT NULL,
        user_answer TEXT,
        explanation TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS learning_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        seconds INTEGER DEFAULT 0,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, date)
    );
    CREATE TABLE IF NOT EXISTS stars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        source TEXT NOT NULL,
        points INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        badge_id TEXT NOT NULL,
        unlocked_at TEXT NOT NULL,
        UNIQUE(user_id, badge_id)
    );
    """)
    conn.commit()
    conn.close()


def ensure_system_roles():
    """迁移旧库并为系统预置默认导师（user_id=0）。"""
    conn = db()
    scols = [r["name"] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()]
    if "course_id" not in scols:
        conn.execute("ALTER TABLE sessions ADD COLUMN course_id TEXT")
        conn.commit()
    if "is_assessment" not in scols:
        conn.execute("ALTER TABLE sessions ADD COLUMN is_assessment INTEGER DEFAULT 0")
        conn.commit()
    rcols = [r["name"] for r in conn.execute("PRAGMA table_info(roles)").fetchall()]
    if "lang" not in rcols:
        conn.execute("ALTER TABLE roles ADD COLUMN lang TEXT DEFAULT 'zh'")
        conn.commit()
    # 掌握度分级重定义的一次性迁移：旧的 3=掌握 调整为 4=掌握（新增 了解/熟悉 中间档）
    conn.execute("CREATE TABLE IF NOT EXISTS schema_flags (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    _done = conn.execute("SELECT value FROM schema_flags WHERE key='gates_migrated'").fetchone()
    if not _done:
        conn.execute("UPDATE mastery SET level=4 WHERE level=3")
        conn.execute("INSERT OR REPLACE INTO schema_flags(key,value) VALUES('gates_migrated','1')")
        conn.commit()
    # 迁移 settings：新增「推理模型」独立配置列
    stcols = [r["name"] for r in conn.execute("PRAGMA table_info(settings)").fetchall()]
    for col in ("r_api_key", "r_base_url", "r_model"):
        if col not in stcols:
            conn.execute(f"ALTER TABLE settings ADD COLUMN {col} TEXT")
            conn.commit()
    # 一个老师·自动变声：只预置中文小艾老师；英语课时由对话/测评接口自动切成英文外教。
    for m in (C.SYSTEM_MENTOR,):
        exists = conn.execute("SELECT id FROM roles WHERE user_id=0 AND name=?",
                              (m["name"],)).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO roles (user_id, name, persona, teaching_style, course, "
                "world_setting, lang, relationship_stage, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (0, m["name"], m["persona"], m["teaching_style"], m["course"],
                 m.get("world_setting", ""), m.get("lang", "zh"), 0, now_iso()))
            conn.commit()
    # 星星/成就表迁移
    for tbl in ("stars", "achievements"):
        if not conn.execute("SELECT name FROM sqlite_master WHERE name=?", (tbl,)).fetchone():
            if tbl == "stars":
                conn.execute("CREATE TABLE stars (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, source TEXT NOT NULL, points INTEGER DEFAULT 1, created_at TEXT NOT NULL)")
            else:
                conn.execute("CREATE TABLE achievements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, badge_id TEXT NOT NULL, unlocked_at TEXT NOT NULL, UNIQUE(user_id, badge_id))")
            conn.commit()
    # 学习日志表迁移
    lcols = [r["name"] for r in conn.execute("PRAGMA table_info(learning_log)").fetchall()]
    if not lcols:
        conn.execute("""
            CREATE TABLE learning_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                seconds INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, date)
            )
        """)
        conn.commit()
    # ===== 知识图谱增强：节点层级/权重/掌握度 =====
    kg_ncols = [r["name"] for r in conn.execute("PRAGMA table_info(kg_nodes)").fetchall()]
    for col, defval in (("level", "INTEGER DEFAULT 1"), ("weight", "REAL DEFAULT 1.0"),
                        ("course_id", "TEXT"), ("mastery_level", "INTEGER DEFAULT 0")):
        if col not in kg_ncols:
            conn.execute(f"ALTER TABLE kg_nodes ADD COLUMN {col} {defval}")
            conn.commit()
    kg_ecols = [r["name"] for r in conn.execute("PRAGMA table_info(kg_edges)").fetchall()]
    if "weight" not in kg_ecols:
        conn.execute("ALTER TABLE kg_edges ADD COLUMN weight REAL DEFAULT 1.0")
        conn.commit()
    # ===== 智能错题本：归因/艾宾浩斯/掌握标记 =====
    mcols = [r["name"] for r in conn.execute("PRAGMA table_info(mistakes)").fetchall()]
    for col, defval in (("category", "TEXT"), ("review_count", "INTEGER DEFAULT 0"),
                        ("next_review", "TEXT"), ("mastered", "INTEGER DEFAULT 0"),
                        ("similar_done", "INTEGER DEFAULT 0")):
        if col not in mcols:
            conn.execute(f"ALTER TABLE mistakes ADD COLUMN {col} {defval}")
            conn.commit()
    # ===== 错题重做闭环：重做次数/重做答对次数/最近重做时间/知识点子点 =====
    for col, defval in (("redo_count", "INTEGER DEFAULT 0"),
                        ("redo_correct", "INTEGER DEFAULT 0"),
                        ("last_redo_at", "TEXT"),
                        ("sub_point", "TEXT")):
        if col not in mcols:
            conn.execute(f"ALTER TABLE mistakes ADD COLUMN {col} {defval}")
            conn.commit()
    # ===== 再测/诊断历史（用于「再测薄弱项」前后对比与进步趋势） =====
    if not conn.execute("SELECT name FROM sqlite_master WHERE name='retest_log'").fetchone():
        conn.execute("""
            CREATE TABLE retest_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT,
                grade TEXT,
                scope TEXT DEFAULT 'full',
                total INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                weak_before INTEGER DEFAULT 0,
                weak_after INTEGER DEFAULT 0,
                fixed_json TEXT DEFAULT '[]',
                still_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    # ===== 学习进度快照 / 断点续学（下次打开可以继续） =====
    if not conn.execute("SELECT name FROM sqlite_master WHERE name='study_progress'").fetchone():
        conn.execute("""
            CREATE TABLE study_progress (
                user_id INTEGER PRIMARY KEY,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
    # ===== 学习计划表：每日任务 =====
    if not conn.execute("SELECT name FROM sqlite_master WHERE name='daily_plans'").fetchone():
        conn.execute("""
            CREATE TABLE daily_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                items_json TEXT NOT NULL,
                completed_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                UNIQUE(user_id, date)
            )
        """)
        conn.commit()
    conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_password(username, password):
    return hashlib.sha256((username + "::" + password).encode("utf-8")).hexdigest()


_PBKDF2_ITER = 200_000


def hash_password_new(password):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITER)
    return f"pbkdf2${_PBKDF2_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password, stored):
    if not stored:
        return False
    if stored.startswith("pbkdf2$"):
        try:
            _, it_s, salt_hex, hash_hex = stored.split("$")
            it = int(it_s)
            salt = bytes.fromhex(salt_hex)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, it)
            return secrets.compare_digest(dk.hex(), hash_hex)
        except (ValueError, AttributeError):
            return False
    return False


def is_legacy_hash(stored):
    return bool(stored) and not stored.startswith("pbkdf2$")


# ---------- API 密钥本地编码（加密存储，重启一致） ----------
# 见上方 _APP_SECRET 生成逻辑（环境变量 > 本地固定文件）


def _keystream(length):
    if not _APP_SECRET:
        return b""
    out = bytearray()
    i = 0
    counter = 0
    while i < length:
        block = hashlib.sha256(_APP_SECRET + counter.to_bytes(4, "big")).digest()
        take = min(len(block), length - i)
        out.extend(block[:take])
        i += take
        counter += 1
    return bytes(out)


# APP_SECRET_KEY：用于加密 settings 中的 api_key。若为空则从本地文件生成固定密钥（首次运行），
# 确保重启后加解密仍一致。生产环境应由环境变量注入，避免密钥随源码泄露。
_SECRET_FILE = os.path.join(BASE_DIR, "data", ".app_secret")
if os.environ.get("APP_SECRET_KEY"):
    _APP_SECRET = os.environ.get("APP_SECRET_KEY", "").encode("utf-8")
else:
    if os.path.exists(_SECRET_FILE):
        with open(_SECRET_FILE, "rb") as f:
            _APP_SECRET = f.read()
    else:
        _APP_SECRET = secrets.token_bytes(32)
        os.makedirs(os.path.dirname(_SECRET_FILE) or DATA_DIR, exist_ok=True)
        with open(_SECRET_FILE, "wb") as f:
            f.write(_APP_SECRET)

def enc_secret(plain):
    if not plain or not _APP_SECRET:
        return plain or ""
    data = plain.encode("utf-8")
    ks = _keystream(len(data))
    xored = bytes(a ^ b for a, b in zip(data, ks))
    return "enc$" + base64.b64encode(xored).decode("ascii")


def dec_secret(stored):
    if not stored:
        return ""
    if not stored.startswith("enc$"):
        return stored
    if not _APP_SECRET:
        return ""
    try:
        data = base64.b64decode(stored[4:])
        ks = _keystream(len(data))
        return bytes(a ^ b for a, b in zip(data, ks)).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return ""


# ----------------------------- 业务逻辑 -----------------------------
def get_user_by_token(token):
    if not token:
        return None
    conn = db()
    row = conn.execute("SELECT user_id FROM auth_tokens WHERE token=?", (token,)).fetchone()
    conn.close()
    if not row:
        return None
    return row["user_id"]


def get_settings(user_id):
    conn = db()
    row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return {"api_key": "", "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat", "mock_mode": 0,
                "r_api_key": "", "r_base_url": "", "r_model": ""}
    d = dict(row)
    # 兼容旧库缺列
    for k in ("r_api_key", "r_base_url", "r_model"):
        d.setdefault(k, "")
    # 解密密钥字段
    d["api_key"] = dec_secret(d.get("api_key", ""))
    d["r_api_key"] = dec_secret(d.get("r_api_key", ""))
    return d


def resolve_llm_settings(settings, kind="teaching"):
    """把整份设置按用途拆出对应的模型配置。
    kind="teaching" 用教学模型列(api_key/base_url/model)；
    kind="reasoning" 用推理模型列(r_*)，任一字段为空则回退到教学模型。
    返回 call_llm 可直接使用的 dict。
    """
    s = settings or {}
    teach = {
        "api_key": (s.get("api_key") or "").strip(),
        "base_url": (s.get("base_url") or "https://api.deepseek.com/v1").strip(),
        "model": (s.get("model") or "deepseek-chat").strip(),
        "mock_mode": s.get("mock_mode", 1),
        "max_tokens": s.get("max_tokens"),
    }
    if kind != "reasoning":
        return teach
    r_key = (s.get("r_api_key") or "").strip()
    r_url = (s.get("r_base_url") or "").strip()
    r_model = (s.get("r_model") or "").strip()
    # 推理模型未单独配置时回退教学模型，保证向后兼容
    if not r_model and not r_url and not r_key:
        return teach
    return {
        "api_key": r_key or teach["api_key"],
        "base_url": r_url or teach["base_url"],
        "model": r_model or teach["model"],
        "mock_mode": s.get("mock_mode", 1),
        "max_tokens": s.get("max_tokens"),
    }


def get_role(user_id, role_id):
    conn = db()
    row = conn.execute("SELECT * FROM roles WHERE id=? AND (user_id=? OR user_id=0)",
                       (role_id, user_id)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_messages(session_id, limit=24):
    conn = db()
    rows = conn.execute(
        "SELECT role, content, emotion FROM messages WHERE session_id=? "
        "ORDER BY id ASC LIMIT ?", (session_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_last_assistant_emotion(session_id):
    conn = db()
    row = conn.execute(
        "SELECT emotion FROM messages WHERE session_id=? AND role='assistant' "
        "AND emotion IS NOT NULL ORDER BY id DESC LIMIT 1", (session_id,)).fetchone()
    conn.close()
    return row["emotion"] if row else None


def add_message(session_id, role, content, emotion):
    conn = db()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, emotion, created_at) "
        "VALUES (?,?,?,?,?)", (session_id, role, content, emotion, now_iso()))
    conn.execute("UPDATE sessions SET updated_at=? WHERE id=?", (now_iso(), session_id))
    conn.commit()
    conn.close()


def upsert_node(user_id, role_id, label):
    label = (label or "").strip()
    if not label:
        return
    conn = db()
    conn.execute(
        "INSERT OR IGNORE INTO kg_nodes (user_id, role_id, label, created_at) "
        "VALUES (?,?,?,?)", (user_id, role_id, label, now_iso()))
    conn.commit()
    conn.close()


def upsert_edge(user_id, role_id, source, target, rel):
    source, target, rel = (source or "").strip(), (target or "").strip(), (rel or "").strip()
    if not (source and target):
        return
    conn = db()
    conn.execute(
        "INSERT OR IGNORE INTO kg_edges (user_id, role_id, source, target, rel, created_at) "
        "VALUES (?,?,?,?,?,?)", (user_id, role_id, source, target, rel, now_iso()))
    conn.commit()
    conn.close()


# ----------------------------- LLM 调用 -----------------------------
def mock_llm(messages, lang="zh"):
    """演示模式：不调用真实模型，用启发式生成苏格拉底式回应。
    会读取同一会话的历史，按轮次做多轮递进，避免「每次都一样」的观感。"""
    conv = messages[1:] if len(messages) > 1 else []
    user_turns = [m for m in conv if m.get("role") == "user"]
    last_user = user_turns[-1]["content"] if user_turns else ""
    turn_no = len(user_turns)

    # 英文演示分支：返回英文苏格拉底式递进模板，配合英语语音对话
    if lang == "en":
        et = last_user.strip()
        efocus = re.split(r"[ ,.!?;:]+", et)[0] if et else "this topic"
        if turn_no >= 2:
            reply = (f"Good, let's go one step further. In your own words, what did you just say "
                     f"about '{efocus}', and which part are you still unsure about?")
        else:
            reply = (f"Nice question! Before I give anything away, tell me in your own words: "
                     f"what do you already know about '{efocus}', and where does it get fuzzy?")
        concepts = ["vocabulary", "grammar", "speaking"] if turn_no < 2 else ["fluency", "accuracy"]
        return json.dumps({"reply": reply, "emotion": "curiosity",
                           "concepts": concepts, "relations": [], "stage_hint": "keep"}, ensure_ascii=False)

    t = last_user
    emotion = "neutral"
    if any(w in t for w in ["?x", "？", "为什么", "怎么", "如何", "什么", "？"]):
        emotion = "curiosity"
    elif any(w in t for w in ["不懂", "不会", "迷糊", "困惑", "搞不清", "confus"]):
        emotion = "confusion"
    elif any(w in t for w in ["烦", "气", "太难", "做不出", "挫败", "frustrat"]):
        emotion = "frustration"
    elif any(w in t for w in ["懂了", "明白", "会了", "原来如此", "satisf"]):
        emotion = "satisfaction"
    elif any(w in t for w in ["无聊", "没意思", "boring"]):
        emotion = "boredom"
    elif any(w in t for w in ["怕", "担心", "焦虑", "紧张", "anx"]):
        emotion = "anxiety"
    elif any(w in t for w in ["太棒", "厉害", "exciting", "兴奋", "赞"]):
        emotion = "excitement"

    snippets = [s for s in re.split(r"[，。！？!?\n]", t) if len(s) >= 2]
    focus = snippets[0] if snippets else t[:12]

    first = {
        "curiosity": f"这是个值得深挖的问题。先别急着要答案——如果用你自己的话描述「{focus}」，你会从哪里讲起？",
        "confusion": f"感觉这里有点绕。我们用个类比：把「{focus}」想象成日常里的某件事，它最像什么？",
        "frustration": f"别急，这步确实容易卡住。我们先退一小步：你能说出目前确定的、唯一没错的那一点是什么吗？",
        "excitement": f"很好的状态！趁热打铁——如果要把「{focus}」再往前推一层，你觉得下一个该弄懂的关键是什么？",
        "satisfaction": f"看来你抓住了脉络。那顺势想一想：掌握了这点之后，哪个相邻的知识会自然浮现出来？",
        "boredom": f"我们来点挑战：如果规则反过来，「{focus}」会发生什么变化？试试用反例逼出它的边界。",
        "anxiety": f"放轻松，学习是过程不是考试。先肯定自己已经走到这儿了——你觉得自己比十分钟前多理解了哪一点？",
        "neutral": f"有意思。在继续之前，先想想：你是怎么得到现在这个看法的？有没有哪个前提我们还没验证过？",
    }
    follow = {
        "curiosity": f"顺着你刚才说的「{focus}」，再逼自己一步：如果只能保留其中一个角度，你会留下哪个，为什么？",
        "confusion": f"我们接着「{focus}」往下捅：刚才那个类比里，哪个细节其实并不贴切？把它挑出来。",
        "frustration": f"既然卡点还在，我们换个入口：把「{focus}」拆成两半，哪一半你其实已经懂了？",
        "excitement": f"趁你状态在线，把「{focus}」从一个例子推广到一类问题：它的共性规律是什么？",
        "satisfaction": f"好，那我们用「{focus}」去解释一个全新的现象，看看这套理解能不能迁移出去？",
        "boredom": f"既然觉得平淡，就用「{focus}」构造一个反直觉的结论，再回头看它哪里成立？",
        "anxiety": f"你已经推进到「{focus}」了，比刚才稳。现在最想确认的那个小疑问是什么？",
        "neutral": f"我们继续「{focus}」：如果把你上一步的说法反过来讲，会暴露出什么漏洞？",
    }
    reply = (follow.get(emotion, follow["neutral"]) if turn_no >= 2
             else first.get(emotion, first["neutral"]))

    concepts = [w for w in ["概念", "原理", "定义", "例子", "前提"] if w in t][:3] or [focus or "核心概念"]
    return json.dumps({
        "reply": reply, "emotion": emotion,
        "concepts": concepts[:3], "relations": [], "stage_hint": "keep"
    }, ensure_ascii=False)


def mock_problem_explain(problem, lang="zh"):
    """演示模式：无法真正解题，返回结构化的「讲题脚手架」，让 UI 仍可见、可用。
    接入真实教学模型后即给出真正分步骤的解析。"""
    if lang == "en":
        return {
            "problem": problem[:240],
            "knowledge": [],
            "analysis": ("(Demo mode) Connect a real teaching model in Settings to get a full step-by-step "
                         "solution. In general: read the problem, list what's given and what to find, "
                         "pick the method, then solve step by step."),
            "steps": [
                "Step 1: Restate the problem in your own words — what is given, what is asked.",
                "Step 2: Choose the concept/method that fits this type of problem.",
                "Step 3: Carry out the steps with the actual numbers, one at a time.",
                "Step 4: Write the final answer and check it against the question.",
            ],
            "answer": "",
            "common_mistakes": ["Skipping a check of the final answer.",
                                 "Mixing up what is given vs. what is asked."],
            "practice": "",
        }
    return {
        "problem": problem[:240],
        "knowledge": [],
        "analysis": ("（演示模式）在「系统设置」里接入真实教学模型后，AL 老师会给出完整分步解析。"
                     "通用做法：先读懂题——已知什么、求什么；再选对应的知识点和方法；然后一步步算；最后写出答案并验算。"),
        "steps": [
            "第一步：用自己的话重述题意——已知什么、求什么。",
            "第二步：判断这道题对应哪个知识点、该用哪种方法。",
            "第三步：按实际数字一步步算，每一步都写清楚。",
            "第四步：写出最终答案，并代回题目验算是否合理。",
        ],
        "answer": "",
        "common_mistakes": ["算完不验算，答案写错自己没发现。", "把「已知条件」和「所求」搞混。"],
        "practice": "",
    }


def strip_think(text):
    """剥离 DeepSeek-R1 等推理模型在回答前后包裹的 <think>...</think> 思考块。"""
    if not text:
        return text
    import re as _re
    cleaned = _re.sub(r"<think>.*?</think>", "", text, flags=_re.DOTALL | _re.IGNORECASE)
    cleaned = _re.sub(r"<thinking>.*?</thinking>", "", cleaned, flags=_re.DOTALL | _re.IGNORECASE)
    return cleaned.strip()


def call_llm(messages, settings, lang="zh"):
    api_key = (settings.get("api_key") or "").strip()
    base_url = (settings.get("base_url") or "https://api.deepseek.com/v1").strip()
    model = (settings.get("model") or "deepseek-chat").strip()
    mock_mode = settings.get("mock_mode", 1)

    if mock_mode or not api_key:
        return mock_llm(messages, lang)

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        # 推理模型（如 DeepSeek-R1）思考很费 token，给足上限避免答案被截断
        "max_tokens": int(settings.get("max_tokens") or 4096),
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + api_key)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            obj = json.loads(resp.read().decode("utf-8"))
        content = obj["choices"][0]["message"]["content"]
        # 兼容部分服务商把推理放到独立字段的情况
        reasoning = obj["choices"][0]["message"].get("reasoning_content") or ""
        return strip_think(content) if content else strip_think(reasoning)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        return json.dumps({
            "reply": f"⚠️ 大模型返回错误（{e.code}）：{detail}。请检查设置页的 API Key / Base URL / 模型名。",
            "emotion": "anxiety", "concepts": [], "relations": [], "stage_hint": "keep"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "reply": f"⚠️ 调用大模型失败：{e}。可暂时开启「演示模式」体验界面。",
            "emotion": "anxiety", "concepts": [], "relations": [], "stage_hint": "keep"
        }, ensure_ascii=False)


def parse_llm_response(text):
    text = strip_think(text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return {"reply": text, "emotion": "neutral", "concepts": [],
                "relations": [], "stage_hint": "keep"}


def clean_reply(text, stage=1, criteria=""):
    """清洗模型偶发的退化输出：去掉 markdown 代码围栏、字段名前缀；
    若清洗后仍是 JSON 结构（模型把整个结构塞进 reply），返回空串交由调用方兜底。"""
    if not text:
        return ""
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s).strip()
    s = re.sub(r"^你对本条消息的回应[：:]\s*", "", s)
    s = re.sub(r"^你这一条要对学生说的话[：:]\s*", "", s)
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        return ""
    return s


def build_messages(role_row, stage, last_emotion, history, course_context=None):
    name = role_row["name"]
    persona = role_row.get("persona") or "一位耐心、睿智、循循善诱的导师。"
    style = role_row.get("teaching_style") or "温和而严谨，重启发轻灌输。"
    course = role_row.get("course") or "通用学习主题"
    if course_context:
        course = course + "\n\n# 本次具体学习主题\n" + course_context
    strategy = EMOTION_STRATEGY.get(last_emotion, EMOTION_STRATEGY["neutral"])
    lang = role_row.get("lang") or "zh"
    if lang == "en":
        lang_instruction = (
            "\n\n# 语言要求（最高优先级）\n始终只用英语(English)与学生对话，包括你提出的每一个问题。"
            "鼓励学生开口说英语，对他们的英文表达（发音、语法、用词）给予简短、友好的纠正，"
            "并用简单的英语解释为什么。不要使用中文。"
        )
    else:
        lang_instruction = "\n\n# 语言要求\n用中文与学生对话。"
    system = (SYSTEM_PROMPT_TEMPLATE
              .replace("<<NAME>>", name)
              .replace("<<PERSONA>>", persona)
              .replace("<<STYLE>>", style)
              .replace("<<COURSE>>", course)
              .replace("<<STAGE>>", STAGE_NAMES[stage])
              .replace("<<LAST_EMOTION>>", last_emotion)
              .replace("<<STRATEGY>>", strategy)
              + lang_instruction)
    msgs = [{"role": "system", "content": system}]
    for h in history:
        msgs.append({"role": h["role"], "content": h["content"]})
    return msgs


def build_assess_messages(role_row, topic_title, topic_ctx, core, history, lang="zh"):
    """构建课后测评的系统提示：检验掌握度，引导学生自主完成。"""
    name = role_row["name"]
    if lang == "en":
        lang_instruction = ("用英语(English)与学习者对话，包括你提出的每一个测评问题和对他回答的反馈。"
                            "verdict 字段仍须填写「掌握」「熟悉」「了解」「未掌握」之一（不要翻译成英文）。")
    else:
        lang_instruction = "用中文与学习者对话。"
    system = (ASSESS_PROMPT_TEMPLATE
              .replace("<<NAME>>", name)
              .replace("<<TOPIC>>", topic_title)
              .replace("<<COURSE>>", topic_ctx)
              .replace("<<CORE>>", core)
              + "\n\n# 语言要求\n" + lang_instruction
              + "\n（再次强调：verdict 必须严格为「掌握」「熟悉」「了解」「未掌握」四者之一或空字符串。）")
    msgs = [{"role": "system", "content": system}]
    for h in history:
        msgs.append({"role": h["role"], "content": h["content"]})
    return msgs


def mock_assess(topic, lang, round_no):
    """演示模式下的知识点测评：闯三关（说出来→做出来→讲明白），末轮给掌握度结论。"""
    subs = topic.get("sub") or []
    title = topic.get("title", "这个知识点")
    if lang == "en":
        gates = [
            f"Gate 1 - Explain (Understand): Can you explain '{title}' in your own words and give a real-life example?",
            f"Gate 2 - Apply: Here is a basic problem. Try to solve it step by step and write down your answer.",
            f"Gate 3 - Teach (Transfer): Now imagine teaching '{title}' to a friend who knows nothing about it. How would you explain it, or solve a brand-new example?",
        ]
        criteria = [
            "Gate 1 pass: explain the core idea correctly and give a relevant example.",
            "Gate 2 pass: correct steps and correct final answer.",
            "Gate 3 pass: can transfer to a new situation or teach it clearly.",
        ]
        if round_no < 3:
            return json.dumps({"reply": gates[round_no], "stage": round_no + 1, "stage_pass": True,
                               "criteria": criteria[round_no], "verdict": "", "verdict_reason": "",
                               "emotion": "curiosity", "concepts": subs[:3] or ["topic"],
                               "stage_hint": "keep"}, ensure_ascii=False)
        return json.dumps({
            "reply": (f"Demo mode doesn't grade answers, but you've walked through all 3 gates of '{title}': "
                      f"Explain → Apply → Teach. With a real model you'd get a per-gate mastery verdict. "
                      f"Keep reviewing the key points: {', '.join(subs[:3]) or title}. "
                      f"Then try teaching it to someone else in English — if you can teach it, you know it."),
            "stage": 3, "stage_pass": True, "criteria": criteria[2], "verdict": "熟悉",
            "verdict_reason": "演示模式不判对错，已走完三关；接入真实模型可获逐关评定的掌握度。",
            "emotion": "satisfaction", "concepts": subs[:3] or ["topic"], "stage_hint": "keep"}, ensure_ascii=False)
    gates = [
        f"第一关·说出来（理解）：请用你自己的话讲讲「{title}」的核心意思，并举一个生活里的例子。",
        f"第二关·做出来（应用）：来一道基础题，请你一步步写出来，给出完整步骤和最终答案。（我会先看你的思路，卡住就提示你）",
        f"第三关·讲明白（迁移）：换一个你没见过的新情境，请你自己分析解决；或者，把这个知识点讲给「一位完全不懂的同学」听，让他也能懂。",
    ]
    criteria = [
        "第一关过关标准：能用大白话说清核心意思，举的例子贴切。",
        "第二关过关标准：解题步骤正确、方法用对、答案正确。",
        "第三关过关标准：能迁移到新情境，或能讲得让小白也听懂。",
    ]
    if round_no < 3:
        return json.dumps({"reply": gates[round_no], "stage": round_no + 1, "stage_pass": True,
                           "criteria": criteria[round_no], "verdict": "", "verdict_reason": "",
                           "emotion": "curiosity", "concepts": subs[:3] or ["核心概念"],
                           "stage_hint": "keep"}, ensure_ascii=False)
    subs_hint = "、".join(subs[:3]) or title
    return json.dumps({
        "reply": (f"演示模式不会判你答对不对，但你已经跟着走完了「{title}」的三关：说出来 → 做出来 → 讲明白。\n"
                  f"用真实模型（设置里接入 Ollama / DeepSeek）就能获得逐关判定的掌握度。\n"
                  f"现在可以围绕这几个要点再自己讲一遍：{subs_hint}；合上书讲给家人听——能讲清楚，才是真掌握。"),
        "stage": 3, "stage_pass": True, "criteria": criteria[2], "verdict": "熟悉",
        "verdict_reason": "演示模式不判对错，已闯完三关；接入真实模型可获逐关评定的掌握度。",
        "emotion": "satisfaction", "concepts": subs[:3] or ["核心概念"], "stage_hint": "keep"}, ensure_ascii=False)


# ----------------------------- 速率限制 -----------------------------
# 进程内字典：每 IP 每分钟 60 次通用；/api/login/register 单独限 10 次/分钟
_RATE_LIMIT = {"window_start": 0.0, "counts": {}}
_RL_LOGIN = {"window_start": 0.0, "counts": {}}
_RATE_WINDOW = 60.0
_RATE_LIMIT_GLOBAL = 120   # 普通接口每窗口上限（更宽松）
_RATE_LIMIT_AUTH = 10      # 登录/注册每窗口上限（防爆破）


def _rl_check(bucket, key, limit):
    """滑动窗口计数；超限返回 False。"""
    now = time.time()
    win = bucket["window_start"]
    if now - win >= _RATE_WINDOW:
        bucket["window_start"] = now
        bucket["counts"] = {}
    cnt = bucket["counts"].get(key, 0) + 1
    bucket["counts"][key] = cnt
    return cnt <= limit


# ----------------------------- HTTP 处理 -----------------------------
class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        origin = self.headers.get("Origin", "")
        if "*" in ALLOWED_ORIGINS:
            allow = "*"
        elif origin and origin in ALLOWED_ORIGINS:
            allow = origin
        else:
            allow = ""
        if allow:
            self.send_header("Access-Control-Allow-Origin", allow)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _client_ip(self):
        """从 X-Forwarded-For 取首 IP（外网经反代会带），否则取直连 IP。"""
        fwd = self.headers.get("X-Forwarded-For", "")
        if fwd:
            return fwd.split(",")[0].strip()
        return self.client_address[0] if self.client_address else "?"

    def _token(self):
        h = self.headers.get("Authorization", "")
        if h.startswith("Bearer "):
            return h[7:].strip()
        return ""

    def _user(self):
        return get_user_by_token(self._token())

    def log_message(self, fmt, *args):
        pass  # 静默日志

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            self.handle_api("GET", path, parse_qs(parsed.query))
        else:
            self.serve_static(path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            self.handle_api("POST", path, parse_qs(parsed.query), self._read_body())
        else:
            self._send_json(404, {"error": "not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        self.handle_api("PUT", parsed.path, parse_qs(parsed.query), self._read_body())

    def do_DELETE(self):
        parsed = urlparse(self.path)
        self.handle_api("DELETE", parsed.path, parse_qs(parsed.query), self._read_body())

    # ---------- 静态文件 ----------
    def serve_static(self, path):
        if path in ("/", "/index.html"):
            f = os.path.join(STATIC_DIR, "index.html")
        elif path == "/app.js":
            f = os.path.join(STATIC_DIR, "app.js")
        elif path == "/styles.css":
            f = os.path.join(STATIC_DIR, "styles.css")
        else:
            f = os.path.join(STATIC_DIR, path.lstrip("/"))
        # 路径穿越校验：解析后必须仍在 STATIC_DIR 内
        try:
            real = os.path.realpath(f)
            if os.path.commonpath([real, os.path.realpath(STATIC_DIR)]) != os.path.realpath(STATIC_DIR):
                self.send_response(403)
                self.end_headers()
                return
        except ValueError:
            self.send_response(403)
            self.end_headers()
            return
        if not os.path.isfile(f):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return
        ctype = "text/html; charset=utf-8"
        if f.endswith(".js"):
            ctype = "application/javascript; charset=utf-8"
        elif f.endswith(".css"):
            ctype = "text/css; charset=utf-8"
        with open(f, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ---------- 云端语音合成（edge-tts 兜底）----------
    # 解决移动端「设备无中文语音包 / 微信内嵌禁用 speechSynthesis」导致朗读无声的硬伤。
    # 前端按 130 字分段请求，本接口把每段文本转成 mp3 并缓存，返回 audio/mpeg。
    def _tts(self, query):
        text = (query.get("text", [""])[0] or "").strip()
        lang = (query.get("lang", ["zh-CN"])[0] or "zh-CN").lower()
        if not text:
            self._send_json(400, {"error": "缺少 text 参数"})
            return
        if len(text) > 2000:
            text = text[:2000]   # edge-tts 单请求长度保护（前端已按 130 字分段）
        try:
            import edge_tts
        except ImportError:
            self._send_json(500, {"error": "服务端未安装 edge-tts，请改用浏览器朗读或先 pip install edge-tts"})
            return
        import re as _re
        voice = (query.get("voice", [""])[0] or "").strip()
        if not voice:
            # 内容含中文字符 → 强制中文嗓音（英文嗓音合成中文会 500 / 无音频）
            has_cjk = bool(_re.search(r'[\u4e00-\u9fff]', text))
            voice = "zh-CN-XiaoxiaoNeural" if (has_cjk or lang.startswith("zh")) else "en-US-AriaNeural"
        # edge-tts / Azure SSML 要求 rate、pitch 必须带符号（+/-）且格式合法，
        # 否则 Communicate 会抛异常、导致本线程连接被异常中断（浏览器拿到空响应→静音）。
        # 这里做防御性归一化：非法/缺失一律回退 +0，并对数值做 SSML 合法范围裁剪。
        def _norm_prosody(val, unit, lo, hi):
            if not val:
                return "+0" + unit
            m = _re.match(r'^([+-]?\d+(?:\.\d+)?)' + _re.escape(unit) + r'$', val.strip())
            if not m:
                return "+0" + unit
            try:
                num = float(m.group(1))
            except Exception:
                return "+0" + unit
            num = max(lo, min(hi, num))           # 裁剪到 SSML 合法范围
            return ("+" if num >= 0 else "-") + str(int(round(abs(num)))) + unit
        rate = _norm_prosody((query.get("rate", [""])[0] or "").strip(), "%", -100, 100)
        pitch = _norm_prosody((query.get("pitch", [""])[0] or "").strip(), "Hz", -50, 50)
        # 缓存：相同 voice+rate+pitch+text 复用，避免重复联网
        key = hashlib.md5(("|".join([voice, rate, pitch, text])).encode("utf-8")).hexdigest()
        cache_dir = os.path.join(BASE_DIR, "tts_cache")
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception:
            pass
        fpath = os.path.join(cache_dir, key + ".mp3")
        tmp_path = fpath + ".tmp"
        # 旧版可能留下 0 字节缓存文件，需要重新生成
        cache_valid = os.path.isfile(fpath) and os.path.getsize(fpath) > 0
        if not cache_valid:
            # Windows + Python 3.8+ 默认 ProactorEventLoop 与某些网络库不兼容，
            # 显式切回 SelectorEventLoop 可显著降低 edge-tts 偶发 "No audio was received" 的概率。
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except Exception:
                pass
            async def _gen():
                comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                await comm.save(tmp_path)
            try:
                asyncio.run(_gen())
                # 只有成功生成后才落盘为正式缓存，避免空文件污染缓存
                os.replace(tmp_path, fpath)
            except Exception:
                # 直接 asyncio 调用在某些运行环境下（后台服务/沙箱）会偶发
                # "No audio was received"，但同样的参数在独立 Python 进程里正常。
                # 此处用子进程兜底，确保任何情况下都能生成音频。
                try:
                    if os.path.isfile(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass
                fallback_ok = self._tts_fallback(text, voice, rate, pitch, tmp_path)
                if fallback_ok and os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 0:
                    os.replace(tmp_path, fpath)
                else:
                    self._send_json(500, {"error": "TTS 生成失败，请检查网络或稍后重试"})
                    return
        try:
            with open(fpath, "rb") as f:
                data = f.read()
        except Exception as e:
            self._send_json(500, {"error": "读取音频失败: " + str(e)})
            return
        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self._cors()
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(data)

    def _tts_ping(self):
        """语音服务器连通性探测。

        用途：APK 装在没有 TTS 引擎的手机上（华为等）时，改用「电脑当语音服务器」——
        App 里的「测试语音服务器」按钮会先打这个接口，确认：
          1) 手机确实能连上电脑（同一 WiFi、防火墙放行）；
          2) 电脑这边 edge-tts 装好了；
          3) 电脑的局域网 IP，方便核对地址有没有填错。
        本接口**不合成音频**，毫秒级返回，避免测试时白等。
        """
        edge_ok = True
        try:
            import edge_tts  # noqa: F401
        except Exception:
            edge_ok = False
        try:
            port = self.server.server_address[1]
        except Exception:
            port = 8000
        cache_dir = os.path.join(BASE_DIR, "tts_cache")
        cache_files = 0
        try:
            cache_files = len([n for n in os.listdir(cache_dir) if n.endswith(".mp3")])
        except Exception:
            pass
        self._send_json(200, {
            "ok": True,
            "service": "AL 自学系统 · 语音服务器",
            "edge_tts": edge_ok,
            "voice": "zh-CN-XiaoxiaoNeural",
            "port": port,
            "cache_files": cache_files,
            "lan": _lan_endpoints(port),
            "lan_primary": (_lan_endpoints(port) or [""])[0],
            "time": now_iso(),
        })

    def _tts_fallback(self, text, voice, rate, pitch, out_path):
        """子进程兜底：把参数写进临时 JSON，由独立 Python 进程完成 edge-tts 合成。"""
        import subprocess, tempfile, json
        try:
            fd, argfile = tempfile.mkstemp(suffix=".json", dir=os.path.join(BASE_DIR, "tts_cache"))
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"text": text, "voice": voice, "rate": rate, "pitch": pitch, "out": out_path}, f, ensure_ascii=False)
            script = '''
import asyncio, edge_tts, json, os, sys
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except Exception:
    pass
with open(sys.argv[1], "r", encoding="utf-8") as f:
    cfg = json.load(f)
async def _run():
    await edge_tts.Communicate(cfg["text"], cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"]).save(cfg["out"])
asyncio.run(_run())
'''
            proc = subprocess.run(
                [sys.executable, "-c", script, argfile],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60
            )
            try:
                os.remove(argfile)
            except Exception:
                pass
            return proc.returncode == 0
        except Exception:
            return False

    # ---------- API 路由 ----------
    def handle_api(self, method, path, query, body=None):
        try:
            return self._route(method, path, query, body or {})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _profile_path(self):
        return os.path.join(BASE_DIR, "child_profile.json")

    def _load_child_profile(self):
        try:
            with open(self._profile_path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"children": [], "active": "", "parentPin": "", "dailyMax": 30}

    def _save_child_profile(self, data):
        tmp = self._profile_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._profile_path())

    def _route(self, method, path, query, body):
        # 健康检查
        if method == "GET" and path == "/api/health":
            self._send_json(200, {"status": "ok", "time": now_iso()})
            return

        # 云端语音合成（edge-tts 兜底，解决移动端无语音包 / 微信内嵌禁用 speechSynthesis）
        if method == "GET" and path == "/api/tts":
            self._tts(query)
            return

        # 语音服务器连通性探测（APK「🔌 测试语音服务器」按钮用）
        # ⚠ 必须放在下面「以下均需登录」那道闸门之前：手机端配对时还没登录，
        #   被 401 拦掉的话「测试连接」永远失败，用户会误以为地址填错了。
        if method == "GET" and path == "/api/tts_ping":
            self._tts_ping()
            return

        # 内置 K12 课程目录
        if method == "GET" and path == "/api/curriculum":
            data = json.loads(json.dumps(C.CURRICULUM))
            for st in data:
                for subj in st["subjects"]:
                    if subj.get("name") in ("英语", "English"):
                        subj["lang"] = "en"
            self._send_json(200, {
                "region": C.REGION,
                "textbook": C.TEXTBOOK,
                "standard": C.STANDARD,
                "curriculum": data,
            })
            return

        # 课程详细讲义（离线生成，公开）
        if method == "GET" and path == "/api/lesson":
            course_id = query.get("course_id", [None])[0]
            if not course_id:
                self._send_json(400, {"error": "缺少 course_id"})
                return
            lesson = C.get_lesson(course_id)
            if not lesson:
                self._send_json(404, {"error": "未找到该课程知识点"})
                return
            self._send_json(200, lesson)
            return

        # 注册 / 登录（速率限制防爆破）
        if method == "POST" and path == "/api/register":
            ip = self._client_ip()
            if not _rl_check(_RL_LOGIN, ip, _RATE_LIMIT_AUTH):
                self._send_json(429, {"error": "注册请求过于频繁，请 1 分钟后再试"})
                return
            username = (body.get("username") or "").strip()
            password = body.get("password") or ""
            if not username or not password:
                self._send_json(400, {"error": "用户名与密码不能为空"})
                return
            conn = db()
            if conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
                conn.close()
                self._send_json(409, {"error": "用户名已存在"})
                return
            conn.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?,?,?)",
                         (username, hash_password_new(password), now_iso()))
            conn.commit()
            conn.close()
            self._do_login(username, password)
            return

        if method == "POST" and path == "/api/login":
            ip = self._client_ip()
            if not _rl_check(_RL_LOGIN, ip, _RATE_LIMIT_AUTH):
                self._send_json(429, {"error": "登录请求过于频繁，请 1 分钟后再试"})
                return
            self._do_login(body.get("username", ""), body.get("password", ""))
            return

        # 孩子档案服务端持久化（跨域名/设备恢复，避免每天重填名字头像）
        if method == "GET" and path == "/api/profile":
            self._send_json(200, self._load_child_profile())
            return

        if method == "POST" and path == "/api/profile":
            try:
                prof = body or {}
                children = prof.get("children", []) or []
                if not isinstance(children, list):
                    children = []
                clean_kids = [{"name": c.get("name", ""), "avatar": c.get("avatar", "🐱")}
                              for c in children if c.get("name")]
                active = (prof.get("active") or (clean_kids[0]["name"] if clean_kids else "")) or ""
                self._save_child_profile({
                    "children": clean_kids,
                    "active": active,
                    "parentPin": str(prof.get("parentPin", "") or ""),
                    "dailyMax": int(prof.get("dailyMax", 30) or 30),
                })
                self._send_json(200, {"ok": True})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if method == "GET" and path == "/api/me":
            uid = self._user()
            if not uid:
                self._send_json(401, {"error": "未登录"})
                return
            conn = db()
            u = conn.execute("SELECT id, username FROM users WHERE id=?", (uid,)).fetchone()
            conn.close()
            self._send_json(200, {"user_id": u["id"], "username": u["username"]})
            return

        # 以下均需登录
        uid = self._user()
        if not uid:
            self._send_json(401, {"error": "未登录"})
            return

        # 云端 TTS（Edge 神经嗓音，绕过移动端无语音包问题）
        if path == "/api/tts" and method == "POST":
            uid = self._user()
            if not uid:
                self._send_json(401, {"error": "请先登录"})
                return
            body = self._read_body()
            text = (body.get("text") or "").strip()
            lang = (body.get("lang", "zh-CN") or "zh-CN")
            if not text:
                self._send_json(400, {"error": "缺少 text 参数"})
                return
            self._tts({"text": [text], "lang": [lang]})
            return

        # 家长/老师学习看板
        if path == "/api/dashboard" and method == "GET":
            uid = self._user()
            if not uid:
                self._send_json(401, {"error": "请先登录"})
                return
            conn = db()
            ms = conn.execute(
                "SELECT COUNT(*) as total, "
                "SUM(CASE WHEN level>=4 THEN 1 ELSE 0 END) as mastered, "
                "SUM(CASE WHEN level>=2 AND level<4 THEN 1 ELSE 0 END) as familiar, "
                "SUM(CASE WHEN level=1 THEN 1 ELSE 0 END) as not_mastered "
                "FROM mastery WHERE user_id=?", (uid,)
            ).fetchone()
            recent = conn.execute(
                "SELECT DATE(updated_at) as d, COUNT(*) as cnt "
                "FROM sessions WHERE user_id=? AND is_assessment=0 "
                "AND updated_at >= DATE('now', '-7 days') "
                "GROUP BY DATE(updated_at) ORDER BY d DESC", (uid,)
            ).fetchall()
            top_m = conn.execute(
                "SELECT course_id, level, attempts, last_eval FROM mastery "
                "WHERE user_id=? AND level>=3 ORDER BY last_eval DESC LIMIT 10", (uid,)
            ).fetchall()
            top_w = conn.execute(
                "SELECT course_id, level, attempts, last_eval FROM mastery "
                "WHERE user_id=? AND level=1 ORDER BY attempts DESC LIMIT 10", (uid,)
            ).fetchall()
            totals = conn.execute(
                "SELECT (SELECT COUNT(*) FROM messages WHERE session_id IN "
                "(SELECT id FROM sessions WHERE user_id=?)) as msgs, "
                "(SELECT COUNT(*) FROM sessions WHERE user_id=?) as sess",
                (uid, uid)
            ).fetchone()
            conn.close()
            self._send_json(200, {
                "summary": {
                    "total_courses": ms["total"] or 0,
                    "mastered": ms["mastered"] or 0,
                    "familiar": ms["familiar"] or 0,
                    "not_mastered": ms["not_mastered"] or 0,
                    "total_messages": totals["msgs"] or 0,
                    "total_sessions": totals["sess"] or 0,
                },
                "sessions_recent": [dict(r) for r in recent],
                "top_mastered": [dict(r) for r in top_m],
                "top_weak": [dict(r) for r in top_w],
            })
            return

        # 学习数据导出（个人信息保护法合规）
        if path == "/api/export" and method == "GET":
            uid = self._user()
            if not uid:
                self._send_json(401, {"error": "请先登录"})
                return
            conn = db()
            mastery_rows = conn.execute(
                "SELECT course_id, level, attempts, last_eval FROM mastery WHERE user_id=?", (uid,)
            ).fetchall()
            sessions = conn.execute(
                "SELECT id, role_id, title, course_id, created_at, updated_at FROM sessions WHERE user_id=?",
                (uid,)
            ).fetchall()
            conn.close()
            settings_row = get_settings(uid)
            settings_row.pop("api_key", None)
            settings_row.pop("r_api_key", None)
            self._send_json(200, {
                "exported_at": now_iso(),
                "mastery": [dict(r) for r in mastery_rows],
                "sessions": [dict(s) for s in sessions],
                "settings": settings_row,
            })
            return

        # 设置
        if path == "/api/settings":
            if method == "GET":
                self._send_json(200, get_settings(uid))
                return
            if method == "POST":
                s = get_settings(uid)
                # 教学模型（默认/主用）
                s["api_key"] = (body.get("api_key") if body.get("api_key") is not None
                                else s.get("api_key", "")) or ""
                s["base_url"] = body.get("base_url") or s.get("base_url") or "https://api.deepseek.com/v1"
                s["model"] = body.get("model") or s.get("model") or "deepseek-chat"
                s["mock_mode"] = 1 if body.get("mock_mode", s.get("mock_mode", 1)) else 0
                # 推理模型（课后测评/判题专用，留空则回退教学模型）
                s["r_api_key"] = (body.get("r_api_key") if body.get("r_api_key") is not None
                                  else s.get("r_api_key", "")) or ""
                s["r_base_url"] = (body.get("r_base_url") if body.get("r_base_url") is not None
                                   else s.get("r_base_url", "")) or ""
                s["r_model"] = (body.get("r_model") if body.get("r_model") is not None
                                else s.get("r_model", "")) or ""
                conn = db()
                conn.execute(
                    "INSERT INTO settings (user_id, api_key, base_url, model, mock_mode, "
                    "r_api_key, r_base_url, r_model) "
                    "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET "
                    "api_key=excluded.api_key, base_url=excluded.base_url, "
                    "model=excluded.model, mock_mode=excluded.mock_mode, "
                    "r_api_key=excluded.r_api_key, r_base_url=excluded.r_base_url, "
                    "r_model=excluded.r_model",
                    (uid, enc_secret(s["api_key"]), s["base_url"], s["model"], s["mock_mode"],
                     enc_secret(s["r_api_key"]), s["r_base_url"], s["r_model"]))
                conn.commit()
                conn.close()
                self._send_json(200, {"ok": True, "settings": s})
                return

        if path == "/api/settings/test" and method == "POST":
            settings = get_settings(uid)
            def ping(kind):
                cfg = resolve_llm_settings(settings, kind)
                if settings.get("mock_mode"):
                    return {"ok": True, "model": cfg.get("model") or "(演示模式)", "msg": "演示模式·无需连接"}
                if not cfg.get("model") or not cfg.get("base_url"):
                    return {"ok": False, "model": cfg.get("model") or "", "msg": "未配置模型名称或地址"}
                payload = {"model": cfg["model"], "messages": [{"role": "user", "content": "ping"}],
                           "max_tokens": 8, "temperature": 0}
                url = cfg["base_url"].rstrip("/") + "/chat/completions"
                data = json.dumps(payload).encode()
                req = urllib.request.Request(url, data=data, method="POST")
                req.add_header("Content-Type", "application/json")
                if cfg.get("api_key"):
                    req.add_header("Authorization", "Bearer " + cfg["api_key"])
                try:
                    with urllib.request.urlopen(req, timeout=25) as r:
                        json.loads(r.read().decode())
                    return {"ok": True, "model": cfg["model"], "msg": "可达"}
                except Exception as e:
                    return {"ok": False, "model": cfg["model"], "msg": str(e)[:150]}
            self._send_json(200, {"ok": True,
                                  "teaching": ping("teaching"),
                                  "reasoning": ping("reasoning")})
            return

        # 角色 CRUD
        if path == "/api/roles":
            if method == "GET":
                conn = db()
                rows = conn.execute(
                    "SELECT id, user_id, name, persona, teaching_style, course, world_setting, "
                    "lang, relationship_stage FROM roles WHERE user_id=? OR user_id=0 "
                    "ORDER BY (user_id=0) DESC, id DESC", (uid,)).fetchall()
                conn.close()
                self._send_json(200, [dict(r) for r in rows])
                return
            if method == "POST":
                name = (body.get("name") or "").strip()
                if not name:
                    self._send_json(400, {"error": "角色名称不能为空"})
                    return
                conn = db()
                cur = conn.execute(
                    "INSERT INTO roles (user_id, name, persona, teaching_style, course, "
                    "world_setting, lang, relationship_stage, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (uid, name, body.get("persona", ""), body.get("teaching_style", ""),
                     body.get("course", ""), body.get("world_setting", ""),
                     body.get("lang", "zh"), 0, now_iso()))
                conn.commit()
                rid = cur.lastrowid
                conn.close()
                self._send_json(201, {"id": rid, "ok": True})
                return

        m = re.match(r"^/api/roles/(\d+)$", path)
        if m and method in ("PUT", "DELETE"):
            rid = int(m.group(1))
            if method == "PUT":
                conn = db()
                conn.execute(
                    "UPDATE roles SET name=?, persona=?, teaching_style=?, course=?, "
                    "world_setting=?, lang=? WHERE id=? AND user_id=?",
                    (body.get("name", ""), body.get("persona", ""), body.get("teaching_style", ""),
                     body.get("course", ""), body.get("world_setting", ""),
                     body.get("lang", "zh"), rid, uid))
                conn.commit()
                conn.close()
                self._send_json(200, {"ok": True})
                return
            if method == "DELETE":
                conn = db()
                conn.execute("DELETE FROM roles WHERE id=? AND user_id=?", (rid, uid))
                conn.execute("DELETE FROM sessions WHERE role_id=?", (rid,))
                conn.execute("DELETE FROM kg_nodes WHERE role_id=?", (rid,))
                conn.execute("DELETE FROM kg_edges WHERE role_id=?", (rid,))
                conn.commit()
                conn.close()
                self._send_json(200, {"ok": True})
                return

        # 会话列表 / 详情
        if path == "/api/sessions" and method == "GET":
            role_id = query.get("role_id", [None])[0]
            conn = db()
            if role_id:
                rows = conn.execute(
                    "SELECT id, role_id, title, checkpoint, course_id, created_at, updated_at FROM sessions "
                    "WHERE user_id=? AND role_id=? ORDER BY updated_at DESC", (uid, int(role_id))).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, role_id, title, checkpoint, course_id, created_at, updated_at FROM sessions "
                    "WHERE user_id=? ORDER BY updated_at DESC", (uid,)).fetchall()
            out = []
            for r in rows:
                cnt = conn.execute("SELECT COUNT(*) c FROM messages WHERE session_id=?",
                                   (r["id"],)).fetchone()["c"]
                d = dict(r)
                d["message_count"] = cnt
                out.append(d)
            conn.close()
            self._send_json(200, out)
            return

        m = re.match(r"^/api/sessions/(\d+)$", path)
        if m and method == "GET":
            sid = int(m.group(1))
            conn = db()
            rows = conn.execute(
                "SELECT role, content, emotion, created_at FROM messages WHERE session_id=? "
                "ORDER BY id ASC", (sid,)).fetchall()
            conn.close()
            self._send_json(200, [dict(r) for r in rows])
            return

        # 标记/清除 checkpoint
        m = re.match(r"^/api/sessions/(\d+)/checkpoint$", path)
        if m and method in ("POST", "DELETE"):
            sid = int(m.group(1))
            conn = db()
            ok = conn.execute("SELECT id FROM sessions WHERE id=? AND user_id=?",
                              (sid, uid)).fetchone()
            if not ok:
                conn.close()
                self._send_json(404, {"error": "会话不存在"})
                return
            note = "" if method == "DELETE" else (body.get("note") or "")
            conn.execute("UPDATE sessions SET checkpoint=? WHERE id=?", (note, sid))
            conn.commit()
            conn.close()
            self._send_json(200, {"ok": True, "checkpoint": note})
            return

        # 掌握度查询
        if path == "/api/mastery" and method == "GET":
            course_id = query.get("course_id", [None])[0]
            if not course_id:
                self._send_json(400, {"error": "缺少 course_id"})
                return
            conn = db()
            row = conn.execute(
                "SELECT level, attempts, last_eval FROM mastery WHERE user_id=? AND course_id=?",
                (uid, course_id)).fetchone()
            conn.close()
            if row:
                self._send_json(200, {"course_id": course_id, "level": row["level"],
                                      "attempts": row["attempts"], "last_eval": row["last_eval"]})
            else:
                self._send_json(200, {"course_id": course_id, "level": 0, "attempts": 0, "last_eval": ""})
            return

        # 知识图谱（增强版：含掌握度、层级、权重、课程关联）
        if path == "/api/knowledge_graph" and method == "GET":
            role_id = query.get("role_id", [None])[0]
            if not role_id:
                self._send_json(400, {"error": "缺少 role_id"})
                return
            conn = db()
            nodes_raw = conn.execute(
                "SELECT label, level, weight, course_id, mastery_level, created_at "
                "FROM kg_nodes WHERE user_id=? AND role_id=?",
                (uid, int(role_id))).fetchall()
            edges_raw = conn.execute(
                "SELECT source, target, rel, weight FROM kg_edges WHERE user_id=? AND role_id=?",
                (uid, int(role_id))).fetchall()
            # 补充 course_id 对应的真实掌握度（从 mastery 表）
            mastery_map = {}
            for row in conn.execute("SELECT course_id, level FROM mastery WHERE user_id=?", (uid,)).fetchall():
                mastery_map[row["course_id"]] = row["level"]
            conn.close()
            nodes = []
            for n in nodes_raw:
                cid = n["course_id"]
                real_level = mastery_map.get(cid, n["mastery_level"] or 0) if cid else n["mastery_level"] or 0
                nodes.append({
                    "id": n["label"],
                    "label": n["label"],
                    "level": n["level"] or 1,          # 层级：1核心 / 2重要 / 3普通
                    "weight": n["weight"] or 1.0,     # 节点权重（影响大小）
                    "course_id": cid,                 # 关联课程ID（可跳转学习）
                    "mastery": real_level,            # 掌握度：0未测 1未掌握 2了解 3熟悉 4掌握
                    "mastery_label": MASTERY_LABEL.get(real_level, "未测"),
                })
            edges = [{"source": e["source"], "target": e["target"],
                      "rel": e["rel"], "weight": e["weight"] or 1.0} for e in edges_raw]
            # 统计信息
            stats = {
                "total_nodes": len(nodes),
                "mastered": sum(1 for n in nodes if n["mastery"] >= 4),
                "familiar": sum(1 for n in nodes if n["mastery"] == 3),
                "understood": sum(1 for n in nodes if n["mastery"] == 2),
                "not_mastered": sum(1 for n in nodes if n["mastery"] == 1),
                "untested": sum(1 for n in nodes if n["mastery"] == 0),
            }
            self._send_json(200, {"nodes": nodes, "edges": edges, "stats": stats})
            return

        # ---------------- 精准学（测-学-练-测 闭环） ----------------
        if path == "/api/precision/units" and method == "GET":
            self._send_json(200, {"units": C.list_units()})
            return
        if path == "/api/precision/graph" and method == "GET":
            subject = query.get("subject", [None])[0]
            grade = query.get("grade", [None])[0]
            if not subject or not grade:
                self._send_json(400, {"error": "缺少 subject / grade"})
                return
            self._precision_graph(uid, subject, grade)
            return
        if path == "/api/precision/diagnose" and method == "POST":
            self._precision_diagnose(uid, body)
            return
        if path == "/api/precision/diagnose/grade" and method == "POST":
            self._precision_diagnose_grade(uid, body)
            return
        if path == "/api/precision/practice" and method == "POST":
            self._precision_practice(uid, body)
            return
        if path == "/api/precision/practice/grade" and method == "POST":
            self._precision_practice_grade(uid, body)
            return
        if path == "/api/precision/test" and method == "POST":
            self._precision_test(uid, body)
            return
        if path == "/api/precision/test/grade" and method == "POST":
            self._precision_test_grade(uid, body)
            return
        if path == "/api/precision/mistakes" and method == "GET":
            category = query.get("category", [None])[0]
            only_review = query.get("only_review", ["0"])[0] == "1"
            self._precision_mistakes(uid, category, only_review)
            return
        # ===== 智能错题本增强接口 =====
        if path == "/api/mistakes/stats" and method == "GET":
            self._mistakes_stats(uid)
            return
        if path == "/api/mistakes/review-today" and method == "GET":
            self._mistakes_review_today(uid)
            return
        if path.startswith("/api/mistakes/") and path.endswith("/mastered") and method == "POST":
            mid = int(path.split("/")[-2])
            self._mistakes_mark_mastered(uid, mid)
            return
        if path.startswith("/api/mistakes/") and path.endswith("/review") and method == "POST":
            mid = int(path.split("/")[-2])
            self._mistakes_mark_reviewed(uid, mid)
            return
        if path.startswith("/api/mistakes/") and path.endswith("/similar") and method == "GET":
            mid = int(path.split("/")[-2])
            self._mistakes_similar(uid, mid)
            return
        # 错题重做（当场判定 + 解析 + 更新掌握状态）
        if path.startswith("/api/mistakes/") and path.endswith("/redo") and method == "POST":
            mid = int(path.split("/")[-2])
            self._mistakes_redo(uid, mid, body)
            return
        # 错题本进度 / 按知识点聚合
        if path == "/api/mistakes/progress" and method == "GET":
            self._mistakes_progress(uid)
            return
        if path == "/api/mistakes/by-topic" and method == "GET":
            self._mistakes_by_topic(uid)
            return

        # 精准学：学习进度总览 / 再测历史
        if path == "/api/precision/progress" and method == "GET":
            self._precision_progress(uid, query.get("subject", [None])[0], query.get("grade", [None])[0])
            return
        if path == "/api/precision/retest-history" and method == "GET":
            self._precision_retest_history(uid, query.get("subject", [None])[0], query.get("grade", [None])[0])
            return

        # 学习进度快照 / 断点续学（下次打开继续）
        if path == "/api/study/resume" and method == "GET":
            self._study_resume_get(uid)
            return
        if path == "/api/study/resume" and method == "POST":
            self._study_resume_save(uid, body)
            return

        # 📊 学习进度（按账号持久化；本地 al_ss_progress 只是离线缓存）
        if path == "/api/study/records" and method == "GET":
            self._send_json(200, {"records": _study_records_get(uid)})
            return
        if path == "/api/study/records" and method == "POST":
            items = body.get("records") if isinstance(body.get("records"), dict) else {}
            n = _study_records_merge(uid, items)
            self._send_json(200, {"ok": True, "changed": n, "records": _study_records_get(uid)})
            return

        # 🤖 学习机模式 · AI 学伴（对标讯飞 AI 1对1 伴学）
        if path == "/api/ai/companion/opening" and method == "GET":
            self._companion_opening(uid, query)
            return
        if path == "/api/ai/companion/chat" and method == "POST":
            self._companion_chat(uid, body)
            return

        # 对话（核心）
        if path == "/api/chat" and method == "POST":
            self._chat(uid, body)
            return

        # 课后测评（核心）
        if path == "/api/assess" and method == "POST":
            self._assess(uid, body)
            return

        # 课程 AI 深度讲解（需登录）
        if path == "/api/lesson/explain" and method == "POST":
            self._lesson_explain(uid, body)
            return
        if path == "/api/lesson/reexplain" and method == "POST":
            self._lesson_reexplain(uid, body)
            return

        # 📸 拍照/输入题目 → AL 老师解析讲解（把具体题算出来、讲透）
        if path == "/api/problem/explain" and method == "POST":
            self._problem_explain(uid, body)
            return
        if path == "/api/problem/followup" and method == "POST":
            self._problem_followup(uid, body)
            return

        # 📊 学情报告（需登录）
        if path == "/api/report/log-time" and method == "POST":
            self._report_log_time(uid, body)
            return
        if path == "/api/report/daily" and method == "GET":
            self._report_daily(uid)
            return
        if path == "/api/report/weekly" and method == "GET":
            self._report_weekly(uid)
            return
        if path == "/api/report/mastery-summary" and method == "GET":
            self._report_mastery_summary(uid)
            return
        if path == "/api/report/weak-areas" and method == "GET":
            self._report_weak_areas(uid)
            return

        # 🗣️ 英语口语评测
        if path == "/api/speech/practice" and method == "POST":
            self._speech_practice(uid, body)
            return
        if path == "/api/speech/evaluate" and method == "POST":
            self._speech_evaluate(uid, body)
            return

        # 🎮 激励体系
        if path == "/api/stars" and method == "GET":
            self._stars_get(uid)
            return
        if path == "/api/stars/award" and method == "POST":
            self._stars_award(uid, body)
            return
        if path == "/api/achievements" and method == "GET":
            self._achievements_get(uid)
            return
        if path == "/api/achievements/unlock" and method == "POST":
            self._achievements_unlock(uid, body)
            return

        # 📅 学习计划
        if path == "/api/plan/next" and method == "GET":
            self._plan_next(uid)
            return
        if path == "/api/plan/daily" and method == "GET":
            self._plan_daily(uid)
            return
        if path == "/api/plan/daily/complete" and method == "POST":
            self._plan_daily_complete(uid, body)
            return

        self._send_json(404, {"error": "未知接口: " + method + " " + path})

    # ---------- 📊 学情报告 ----------
    def _report_log_time(self, uid, body):
        """上报学习时长（秒），前端每60秒调用一次"""
        seconds = int(body.get("seconds", 0) or 0)
        if seconds <= 0:
            self._send_json(200, {"ok": True})
            return
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = db()
        row = conn.execute(
            "SELECT seconds FROM learning_log WHERE user_id=? AND date=?",
            (uid, today)).fetchone()
        if row:
            conn.execute(
                "UPDATE learning_log SET seconds=seconds+?, updated_at=? WHERE user_id=? AND date=?",
                (seconds, now_iso(), uid, today))
        else:
            conn.execute(
                "INSERT INTO learning_log (user_id, date, seconds, updated_at) VALUES (?,?,?,?)",
                (uid, today, seconds, now_iso()))
        conn.commit()
        conn.close()
        self._send_json(200, {"ok": True})

    def _report_daily(self, uid):
        """今日学习概况：时长、消息数、新掌握数、错题数"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = db()
        # 学习时长
        log = conn.execute(
            "SELECT seconds FROM learning_log WHERE user_id=? AND date=?",
            (uid, today)).fetchone()
        seconds = log["seconds"] if log else 0
        # 今日消息数
        msgs = conn.execute(
            "SELECT COUNT(*) AS cnt FROM messages m "
            "JOIN sessions s ON m.session_id=s.id "
            "WHERE s.user_id=? AND date(m.created_at)=?", (uid, today)).fetchone()
        msg_count = msgs["cnt"] if msgs else 0
        # 知识点掌握统计
        mastery = conn.execute(
            "SELECT COUNT(*) AS cnt, level FROM mastery WHERE user_id=? GROUP BY level",
            (uid,)).fetchall()
        total_mastered = sum(r["cnt"] for r in mastery if r["level"] >= 4)
        total_familiar = sum(r["cnt"] for r in mastery if r["level"] == 3)
        total_know = sum(r["cnt"] for r in mastery if r["level"] == 2)
        total_weak = sum(r["cnt"] for r in mastery if r["level"] == 1)
        total_tested = sum(r["cnt"] for r in mastery)
        # 今日错题数
        mistakes_today = conn.execute(
            "SELECT COUNT(*) AS cnt FROM mistakes WHERE user_id=? AND date(created_at)=?",
            (uid, today)).fetchone()
        mistake_count = mistakes_today["cnt"] if mistakes_today else 0
        # 会话数
        sessions_today = conn.execute(
            "SELECT COUNT(*) AS cnt FROM sessions WHERE user_id=? AND date(created_at)=?",
            (uid, today)).fetchone()
        session_count = sessions_today["cnt"] if sessions_today else 0
        conn.close()
        self._send_json(200, {
            "date": today,
            "seconds": seconds,
            "minutes": round(seconds / 60, 1),
            "msg_count": msg_count,
            "session_count": session_count,
            "mistake_count": mistake_count,
            "mastery": {
                "mastered": total_mastered,
                "familiar": total_familiar,
                "know": total_know,
                "weak": total_weak,
                "total_tested": total_tested,
            },
        })

    def _report_weekly(self, uid):
        """近7天学习趋势：每天时长 + 掌握度变化"""
        conn = db()
        # 最近7天
        days = []
        from datetime import timedelta
        for i in range(6, -1, -1):
            d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            log = conn.execute(
                "SELECT seconds FROM learning_log WHERE user_id=? AND date=?",
                (uid, d)).fetchone()
            seconds = log["seconds"] if log else 0
            days.append({"date": d, "seconds": seconds, "minutes": round(seconds / 60, 1)})
        # 总掌握度
        all_m = conn.execute(
            "SELECT COUNT(*) AS cnt, level FROM mastery WHERE user_id=? GROUP BY level",
            (uid,)).fetchall()
        conn.close()
        mastered = sum(r["cnt"] for r in all_m if r["level"] >= 4)
        tested = sum(r["cnt"] for r in all_m)
        self._send_json(200, {"days": days, "total_mastered": mastered, "total_tested": tested})

    def _report_mastery_summary(self, uid):
        """各知识点掌握度汇总（按学科分组）"""
        conn = db()
        rows = conn.execute(
            "SELECT course_id, level, attempts, last_eval FROM mastery WHERE user_id=?",
            (uid,)).fetchall()
        conn.close()
        topics_map = {}
        for r in rows:
            cid = r["course_id"]
            topic = C.TOPIC_INDEX.get(cid)
            if not topic:
                continue
            subject = topic.get("subject") or "其他"
            if subject not in topics_map:
                topics_map[subject] = []
            topics_map[subject].append({
                "course_id": cid,
                "title": topic.get("title", cid),
                "level": r["level"],
                "label": MASTERY_LABEL.get(r["level"], "未测"),
                "attempts": r["attempts"],
            })
        # 按学科排序
        result = [{"subject": k, "topics": v} for k, v in topics_map.items()]
        self._send_json(200, {"subjects": result})

    def _report_weak_areas(self, uid):
        """薄弱知识点 TOP（未掌握 / 未测），推荐优先学习"""
        conn = db()
        tested = conn.execute(
            "SELECT course_id, level, attempts FROM mastery WHERE user_id=? AND level<=2",
            (uid,)).fetchall()
        # 找出所有课程中未标记掌握的
        weak = []
        for r in tested:
            cid = r["course_id"]
            topic = C.TOPIC_INDEX.get(cid)
            if not topic:
                continue
            weak.append({
                "course_id": cid,
                "title": topic.get("title", cid),
                "subject": topic.get("subject") or "其他",
                "level": r["level"],
                "label": MASTERY_LABEL.get(r["level"], "未测"),
                "attempts": r["attempts"],
            })
        weak.sort(key=lambda x: (x["level"], -x["attempts"]))
        conn.close()
        self._send_json(200, {"weak_areas": weak[:10], "total": len(weak)})

    # ---------- 🗣️ 英语口语评测 ----------
    def _speech_practice(self, uid, body):
        """为知识点生成英语跟读句子"""
        course_id = (body.get("course_id") or "").strip()
        count = int(body.get("count", 5))
        topic = C.TOPIC_INDEX.get(course_id)
        ctx = ""
        if topic:
            subs = topic.get("sub") or []
            title = topic.get("title", "")
            ctx = f"知识点：{title}\n子内容：{'、'.join(subs[:8])}"
        lang = body.get("lang", "en")
        settings = get_settings(uid)
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))

        if is_mock or not settings.get("api_key"):
            # 演示模式：从子内容生成模板句子
            sentences = self._mock_sentences(topic, count)
            self._send_json(200, {"sentences": sentences, "mock": True})
            return

        # 真实 AI 生成
        sysmsg = "你是一位英语口语教练。根据给定的知识点，生成适合学生跟读练习的英语句子。要求：1) 每个句子包含当前知识点相关词汇 2) 句子简短自然（6-15词）3) 适合大声朗读 4) 输出 JSON 数组。"
        prompt = f"知识点上下文：\n{ctx}\n\n请生成 {count} 个英语跟读句子（每个句子一个字符串），输出 JSON 数组。"
        raw = call_llm([{"role": "system", "content": sysmsg},
                        {"role": "user", "content": prompt}],
                       resolve_llm_settings(settings, "teaching"), lang)
        try:
            obj = parse_llm_response(raw)
            if isinstance(obj, list):
                self._send_json(200, {"sentences": [str(s) for s in obj[:count]], "mock": False})
                return
        except Exception:
            pass
        # 兜底
        sentences = self._mock_sentences(topic, count)
        self._send_json(200, {"sentences": sentences, "mock": True})

    def _mock_sentences(self, topic, count):
        """生成演示模式的跟读句子"""
        subs = topic.get("sub") or []
        title = topic.get("title", "")
        templates = [
            "Let's learn about {kw}.",
            "Can you say '{kw}' with me?",
            "I like to practice {kw} every day.",
            "{kw} is very interesting, isn't it?",
            "Tell me more about {kw}.",
            "How do you use {kw} in a sentence?",
            "Try to read this: {kw}.",
            "Great job! Now let's try {kw}.",
        ]
        keywords = subs[:min(count, len(subs))] if subs else [title]
        sentences = []
        for i in range(count):
            kw = keywords[i % max(len(keywords), 1)]
            s = templates[i % len(templates)].replace("{kw}", kw)
            sentences.append(s)
        return sentences

    def _speech_evaluate(self, uid, body):
        """AI 评价学生口语朗读（可选使用大模型做详细评价）"""
        expected = (body.get("expected") or "").strip()
        recognized = (body.get("recognized") or "").strip()
        words_detail = body.get("words_detail") or []
        if not expected:
            self._send_json(400, {"error": "缺少 expected 原文"})
            return

        # 前端的词级评分已经够用，这里可选让 AI 做更详细的评价
        # 我们返回综合评分 + AI 建议（如果有 LLM 配置）
        score = self._calc_speech_score(expected, recognized, words_detail)
        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"

        # 尝试用大模型做详细反馈
        settings = get_settings(uid)
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))
        feedback = ""
        tips = ""
        if not is_mock and settings.get("api_key"):
            try:
                sysmsg = "你是一位英语发音教练。根据学生跟读的目标句子和实际识别结果，给出简短友好的发音建议（1-2句话）。"
                prompt = f"目标句子：{expected}\n学生朗读识别结果：{recognized}\n\n请给出发音改进建议。"
                raw = call_llm([{"role": "system", "content": sysmsg},
                                {"role": "user", "content": prompt}],
                               resolve_llm_settings(settings, "teaching"), "zh")
                obj = parse_llm_response(raw)
                if isinstance(obj, dict):
                    feedback = obj.get("reply", "") or obj.get("feedback", "") or str(obj)
                else:
                    feedback = str(raw)[:200]
            except Exception:
                feedback = ""
        if not feedback:
            # 规则反馈
            wrong_words = [w for w in words_detail if not w.get("correct")]
            if wrong_words:
                tips = "注意发音：" + "、".join(w["word"] for w in wrong_words[:3])
            elif score < 75:
                tips = "试着再读一遍，注意每个单词的发音要清晰。"
            else:
                tips = "读得很好！可以试试加快一点语速。"

        self._send_json(200, {
            "score": score,
            "grade": grade,
            "words_detail": words_detail,
            "feedback": feedback or tips,
        })

    def _calc_speech_score(self, expected, recognized, words_detail):
        """综合计算口语评分"""
        if not expected:
            return 0
        expected_lower = expected.lower().strip()
        recognized_lower = recognized.lower().strip()

        # 1. 词级匹配率（权重 0.5）
        exp_words = expected_lower.split()
        rec_words = recognized_lower.split()
        if exp_words:
            matched = sum(1 for w in words_detail if w.get("correct"))
            word_acc = matched / len(exp_words) * 100 if exp_words else 0
        else:
            word_acc = 0

        # 2. 编辑距离相似度（权重 0.3）
        if exp_words and rec_words:
            lev = self._levenshtein(exp_words, rec_words)
            max_len = max(len(exp_words), len(rec_words))
            lev_sim = (1 - lev / max_len) * 100 if max_len > 0 else 0
        else:
            lev_sim = 0

        # 3. 置信度均值（权重 0.2）
        confs = [w.get("confidence", 0.5) for w in words_detail if "confidence" in w]
        avg_conf = (sum(confs) / len(confs) * 100) if confs else 50

        score = word_acc * 0.5 + lev_sim * 0.3 + avg_conf * 0.2
        return round(min(max(score, 0), 100))

    def _levenshtein(self, a, b):
        """计算两个单词列表的编辑距离"""
        n, m = len(a), len(b)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1): dp[i][0] = i
        for j in range(m + 1): dp[0][j] = j
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if a[i-1] == b[j-1] else 1
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
        return dp[n][m]

    # ---------- 🎮 激励体系 ----------
    def _stars_get(self, uid):
        """获取星星总数和今日星星"""
        conn = db()
        total = conn.execute("SELECT COALESCE(SUM(points),0) FROM stars WHERE user_id=?", (uid,)).fetchone()[0]
        today = now_iso()[:10]
        today_pts = conn.execute("SELECT COALESCE(SUM(points),0) FROM stars WHERE user_id=? AND created_at>=?", (uid, today)).fetchone()[0]
        # 各种来源的统计
        sources = conn.execute("SELECT source, SUM(points) as pts FROM stars WHERE user_id=? GROUP BY source", (uid,)).fetchall()
        breakdown = {r["source"]: r["pts"] for r in sources}
        conn.close()
        self._send_json(200, {"total": total, "today": today_pts, "breakdown": breakdown})

    def _stars_award(self, uid, body):
        """奖励星星"""
        source = (body.get("source") or "chat").strip()
        points = int(body.get("points") or 1)
        # 每日上限检查
        today = now_iso()[:10]
        limits = {"chat": 10, "selfstudy_learned": 30, "selfstudy_mastered": 30}
        if source in limits:
            conn = db()
            cnt = conn.execute(f"SELECT COUNT(*) FROM stars WHERE user_id=? AND source=? AND created_at>=?",
                               (uid, source, today)).fetchone()[0]
            conn.close()
            if cnt >= limits[source]:
                self._send_json(200, {"awarded": False, "reason": f"今日{source}星星已达上限"})
                return
        conn = db()
        conn.execute("INSERT INTO stars (user_id, source, points, created_at) VALUES (?,?,?,?)",
                     (uid, source, points, now_iso()))
        conn.commit()
        conn.close()
        self._send_json(200, {"awarded": True, "points": points})

    def _achievements_get(self, uid):
        """获取所有成就状态"""
        BADGES = [
            {"id": "first_learn", "title": "🎯 初次学习", "desc": "发出第一条学习消息", "icon": "🎯"},
            {"id": "streak_3", "title": "🔥 连续3天", "desc": "连续学习 3 天", "icon": "🔥"},
            {"id": "first_mastery", "title": "✅ 第一个掌握", "desc": "首次掌握一个知识点", "icon": "✅"},
            {"id": "speech_done", "title": "🗣️ 口语达人", "desc": "完成一次口语练习", "icon": "🗣️"},
            {"id": "stars_50", "title": "⭐ 积少成多", "desc": "累计获得 50 颗星星", "icon": "⭐"},
            {"id": "master_5", "title": "📚 学霸", "desc": "掌握 5 个知识点", "icon": "📚"},
            {"id": "test_10", "title": "🎯 测试达人", "desc": "完成 10 次课后测试", "icon": "🎯"},
            {"id": "streak_7", "title": "💪 坚持一周", "desc": "连续学习 7 天", "icon": "💪"},
            # 自学页专项成就
            {"id": "first_selfstudy", "title": "📖 自主学习", "desc": "首次进入自学页", "icon": "📖"},
            {"id": "selfstudy_10", "title": "🌱 初学乍练", "desc": "累计自学 10 个知识点", "icon": "🌱"},
            {"id": "selfstudy_50", "title": "🚀 涉猎广泛", "desc": "累计自学 50 个知识点", "icon": "🚀"},
            {"id": "selfstudy_master_10", "title": "🏅 知识达人", "desc": "累计掌握 10 个知识点", "icon": "🏅"},
            {"id": "quiz_perfect", "title": "💯 满分小能手", "desc": "首次自主测验全对", "icon": "💯"},
        ]
        conn = db()
        unlocked = set(r["badge_id"] for r in conn.execute("SELECT badge_id FROM achievements WHERE user_id=?", (uid,)).fetchall())
        conn.close()
        result = []
        for b in BADGES:
            result.append({
                "id": b["id"],
                "title": b["title"],
                "desc": b["desc"],
                "icon": b["icon"],
                "unlocked": b["id"] in unlocked,
            })
        self._send_json(200, {"badges": result})

    def _achievements_unlock(self, uid, body):
        """解锁成就"""
        badge_id = (body.get("badge_id") or "").strip()
        if not badge_id:
            self._send_json(400, {"error": "缺少 badge_id"})
            return
        conn = db()
        try:
            conn.execute("INSERT INTO achievements (user_id, badge_id, unlocked_at) VALUES (?,?,?)",
                         (uid, badge_id, now_iso()))
            conn.commit()
            conn.close()
            self._send_json(200, {"unlocked": True, "badge_id": badge_id})
        except Exception:
            conn.close()
            self._send_json(200, {"unlocked": False, "reason": "已解锁过"})

    # ---------- 📅 学习计划 ----------
    def _plan_next(self, uid):
        """根据掌握度推荐下一知识点"""
        conn = db()
        # 获取已掌握/已测的知识点
        mastered = set(r["course_id"] for r in conn.execute(
            "SELECT course_id FROM mastery WHERE user_id=? AND level>=4", (uid,)).fetchall())
        tested = set(r["course_id"] for r in conn.execute(
            "SELECT course_id FROM mastery WHERE user_id=? AND level>=2", (uid,)).fetchall())
        conn.close()
        # 遍历课程，找第一个未掌握的知识点
        recommended = None
        for stage in C.CURRICULUM:
            for subj in stage.get("subjects", []):
                for grade in subj.get("grades", []):
                    for topic in grade.get("topics", []):
                        cid = topic.get("id", "")
                        if cid and cid not in mastered:
                            if not recommended:
                                recommended = {
                                    "course_id": cid,
                                    "title": topic.get("title", cid),
                                    "subject": subj.get("name", ""),
                                    "grade": grade.get("grade", ""),
                                    "stage": stage.get("stage", ""),
                                    "status": "new" if cid not in tested else "in_progress",
                                }
                            break
                    if recommended: break
                if recommended: break
            if recommended: break
        self._send_json(200, {"recommended": recommended})

    def _plan_daily(self, uid):
        """生成/获取今日学习计划：错题复习 + 薄弱巩固 + 新知识点，共3-5项"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = db()
        # 先看今天有没有已生成的计划
        existing = conn.execute(
            "SELECT items_json, completed_json FROM daily_plans WHERE user_id=? AND date=?",
            (uid, today)).fetchone()
        if existing:
            items = json.loads(existing["items_json"])
            completed = json.loads(existing["completed_json"] or "[]")
            conn.close()
            self._send_json(200, {"date": today, "items": items, "completed": completed})
            return
        # ===== 生成今日计划 =====
        items = []
        # 1) 错题复习（艾宾浩斯到期）：最多2项
        due_mistakes = conn.execute(
            "SELECT m.id, m.course_id, m.stem FROM mistakes m "
            "WHERE m.user_id=? AND m.mastered=0 AND m.next_review<=? "
            "ORDER BY m.next_review ASC LIMIT 2",
            (uid, now_iso())).fetchall()
        for m in due_mistakes:
            topic = C.TOPIC_INDEX.get(m["course_id"])
            items.append({
                "type": "review_mistake",
                "title": "复习错题：" + (topic["title"] if topic else m["course_id"]),
                "mistake_id": m["id"],
                "course_id": m["course_id"],
                "priority": 1,
                "icon": "🔄",
            })
        # 2) 薄弱知识点巩固（掌握度=1或2的）：最多2项
        weak = conn.execute(
            "SELECT course_id, level FROM mastery WHERE user_id=? AND level BETWEEN 1 AND 3 "
            "ORDER BY level ASC, last_eval ASC LIMIT 2", (uid,)).fetchall()
        for w in weak:
            topic = C.TOPIC_INDEX.get(w["course_id"])
            if topic:
                # 避免和错题复习重复
                if not any(it.get("course_id") == w["course_id"] for it in items):
                    items.append({
                        "type": "consolidate",
                        "title": "巩固：" + topic["title"],
                        "course_id": w["course_id"],
                        "mastery_level": w["level"],
                        "priority": 2,
                        "icon": "💪",
                    })
        # 3) 新知识点学习：补到总共4-5项
        mastered_ids = set(r["course_id"] for r in conn.execute(
            "SELECT course_id FROM mastery WHERE user_id=? AND level>=4", (uid,)).fetchall())
        target_count = 4 if len(items) >= 2 else 5
        added = 0
        for stage in C.CURRICULUM:
            for subj in stage.get("subjects", []):
                for grade in subj.get("grades", []):
                    for topic in grade.get("topics", []):
                        cid = topic.get("id", "")
                        if cid and cid not in mastered_ids and added < (target_count - len(items)):
                            if not any(it.get("course_id") == cid for it in items):
                                items.append({
                                    "type": "new_learn",
                                    "title": "学习：" + topic.get("title", cid),
                                    "course_id": cid,
                                    "subject": subj.get("name", ""),
                                    "grade": grade.get("grade", ""),
                                    "priority": 3,
                                    "icon": "📖",
                                })
                                added += 1
                    if added >= (target_count - len(items)): break
                if added >= (target_count - len(items)): break
            if added >= (target_count - len(items)): break
        # 存入数据库
        items_json = json.dumps(items, ensure_ascii=False)
        conn.execute(
            "INSERT INTO daily_plans(user_id, date, items_json, completed_json, created_at) "
            "VALUES(?,?,?,?,?)",
            (uid, today, items_json, "[]", now_iso()))
        conn.commit()
        conn.close()
        self._send_json(200, {"date": today, "items": items, "completed": [], "is_new": True})

    def _plan_daily_complete(self, uid, body):
        """标记今日计划某一项已完成"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        idx = int(body.get("index", -1))
        if idx < 0:
            self._send_json(400, {"error": "缺少 index"})
            return
        conn = db()
        row = conn.execute(
            "SELECT completed_json FROM daily_plans WHERE user_id=? AND date=?",
            (uid, today)).fetchone()
        if not row:
            conn.close()
            self._send_json(404, {"error": "今日计划不存在"})
            return
        completed = json.loads(row["completed_json"] or "[]")
        if idx not in completed:
            completed.append(idx)
        conn.execute(
            "UPDATE daily_plans SET completed_json=? WHERE user_id=? AND date=?",
            (json.dumps(completed, ensure_ascii=False), uid, today))
        conn.commit()
        # 奖励星星
        conn.execute(
            "INSERT INTO stars(user_id, source, points, created_at) VALUES(?,?,?,?)",
            (uid, "daily_plan", 1, now_iso()))
        conn.commit()
        conn.close()
        self._send_json(200, {"ok": True, "completed": completed})

    # ---------- 登录辅助 ----------
    def _do_login(self, username, password):
        conn = db()
        u = conn.execute("SELECT id, password_hash FROM users WHERE username=?",
                         (username,)).fetchone()
        if not u:
            conn.close()
            self._send_json(401, {"error": "用户名或密码错误"})
            return
        stored = u["password_hash"]
        ok = verify_password(password, stored)
        if not ok and is_legacy_hash(stored):
            ok = secrets.compare_digest(stored, hash_password(username, password))
            if ok:
                conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                             (hash_password_new(password), u["id"]))
        if not ok:
            conn.close()
            self._send_json(401, {"error": "用户名或密码错误"})
            return
        token = secrets.token_hex(16)
        conn.execute("INSERT INTO auth_tokens (token, user_id, created_at) VALUES (?,?,?)",
                     (token, u["id"], now_iso()))
        conn.commit()
        conn.close()
        self._send_json(200, {"token": token, "user_id": u["id"], "username": username})

    # ---------- 对话核心 ----------
    def _chat(self, uid, body):
        role_id = body.get("role_id")
        message = (body.get("message") or "").strip()
        session_id = body.get("session_id")
        course_id = body.get("course_id")
        if not role_id:
            self._send_json(400, {"error": "缺少 role_id"})
            return
        if not message:
            self._send_json(400, {"error": "消息不能为空"})
            return
        role = get_role(uid, int(role_id))
        if not role:
            self._send_json(404, {"error": "角色不存在"})
            return
        settings = get_settings(uid)

        conn = db()
        if session_id:
            sess = conn.execute("SELECT id FROM sessions WHERE id=? AND user_id=?",
                                (int(session_id), uid)).fetchone()
            if not sess:
                session_id = None
        if not session_id:
            cur = conn.execute(
                "INSERT INTO sessions (user_id, role_id, title, checkpoint, course_id, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (uid, int(role_id), message[:24], "", course_id or None, now_iso(), now_iso()))
            session_id = cur.lastrowid
            conn.commit()
        # 处理 checkpoint 标记
        cp = body.get("checkpoint")
        if cp:
            conn.execute("UPDATE sessions SET checkpoint=? WHERE id=?",
                         (cp, session_id))
            conn.commit()
        conn.close()

        add_message(session_id, "user", message, None)
        history = get_messages(session_id)
        last_emotion = get_last_assistant_emotion(session_id) or "neutral"
        stage = role["relationship_stage"]

        msgs = build_messages(role, stage, last_emotion, history,
                               course_context=C.course_context(course_id))
        text = call_llm(msgs, resolve_llm_settings(settings, "teaching"),
                        role.get("lang", "zh"))
        data = parse_llm_response(text)

        reply = data.get("reply", text)
        emotion = data.get("emotion", "neutral")
        add_message(session_id, "assistant", reply, emotion)

        for c in data.get("concepts", []):
            upsert_node(uid, int(role_id), c)
        for r in data.get("relations", []):
            if isinstance(r, list) and len(r) >= 3:
                upsert_edge(uid, int(role_id), r[0], r[1], r[2])

        if data.get("stage_hint") == "advance":
            new_stage = min(stage + 1, len(STAGE_NAMES) - 1)
            if new_stage != stage:
                conn = db()
                conn.execute("UPDATE roles SET relationship_stage=? WHERE id=?",
                             (new_stage, int(role_id)))
                conn.commit()
                conn.close()
                stage = new_stage

        self._send_json(200, {
            "session_id": session_id,
            "reply": reply,
            "emotion": emotion,
            "emotion_label": EMOTION_LABEL.get(emotion, "平和"),
            "strategy": EMOTION_STRATEGY.get(emotion, ""),
            "concepts": data.get("concepts", []),
            "relations": data.get("relations", []),
            "stage": STAGE_NAMES[stage],
            "stage_index": stage,
        })


    # ---------- 课后测评核心 ----------
    def _assess(self, uid, body):
        role_id = body.get("role_id")
        course_id = body.get("course_id")
        message = (body.get("message") or "").strip()
        session_id = body.get("session_id")
        try:
            round_no = int(body.get("round") or 0)
        except Exception:
            round_no = 0
        if not role_id or not course_id:
            self._send_json(400, {"error": "测评需要 role_id 和 course_id"})
            return
        if not message:
            self._send_json(400, {"error": "消息不能为空"})
            return
        role = get_role(uid, int(role_id))
        if not role:
            self._send_json(404, {"error": "角色不存在"})
            return
        topic = C.TOPIC_INDEX.get(course_id)
        if not topic:
            self._send_json(404, {"error": "知识点不存在"})
            return
        # 一个老师·自动变声：英语知识点测评时切换为英文外教人格
        if topic.get("lang") == "en" or topic.get("subject") == "英语":
            role = dict(role)
            role["name"] = C.ENGLISH_MENTOR["name"]
            role["persona"] = C.ENGLISH_MENTOR["persona"]
            role["teaching_style"] = C.ENGLISH_MENTOR["teaching_style"]
            role["lang"] = "en"
        settings = get_settings(uid)
        lang = role.get("lang", "zh")

        conn = db()
        if session_id:
            sess = conn.execute(
                "SELECT id FROM sessions WHERE id=? AND user_id=? AND is_assessment=1",
                (int(session_id), uid)).fetchone()
            if not sess:
                session_id = None
        if not session_id:
            cur = conn.execute(
                "INSERT INTO sessions (user_id, role_id, title, checkpoint, course_id, "
                "is_assessment, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (uid, int(role_id), "测评:" + topic["title"], "", course_id,
                 1, now_iso(), now_iso()))
            conn.commit()
            session_id = cur.lastrowid
        conn.close()

        add_message(session_id, "user", message, None)
        history = get_messages(session_id)
        topic_ctx = C.course_context(course_id)
        subs = topic.get("sub") or []
        core = "\n".join(f"{i+1}. {s}" for i, s in enumerate(subs)) or \
               "（该知识点未列出具体要点，请围绕其学习目标自由检验）"
        msgs = build_assess_messages(role, topic["title"], topic_ctx, core, history, lang)

        r_settings = resolve_llm_settings(settings, "reasoning")
        if r_settings.get("mock_mode", 1) or not r_settings.get("api_key"):
            text = mock_assess(topic, lang, round_no)
        else:
            text = call_llm(msgs, r_settings, lang)
        data = parse_llm_response(text)

        # 闯关进度字段：当前关卡 / 是否通过本关 / 本关过关标准（先解析，供 reply 兜底使用）
        try:
            stage = int(data.get("stage") or 1)
        except Exception:
            stage = 1
        if stage not in (1, 2, 3):
            stage = 1
        stage_pass = bool(data.get("stage_pass", False))
        criteria = (data.get("criteria") or "").strip()

        reply = clean_reply(data.get("reply", text), stage, criteria)
        if not reply:
            # 模型未给出可用回复时的兜底话术（按当前关卡引导）
            gate_name = {1: "说出来（理解）", 2: "做出来（应用）", 3: "讲明白（迁移）"}.get(stage, "测评")
            reply = f"我们进入第{stage}关 · {gate_name}。" + (f"做到「{criteria}」才算过关，请试着答一下～" if criteria else "请按上面的要求作答～")
        emotion = data.get("emotion", "neutral")
        verdict = (data.get("verdict") or "").strip()
        reason = data.get("verdict_reason", "")
        add_message(session_id, "assistant", reply, emotion)

        mastery_level = None
        if verdict in VERDICT_LEVEL:
            mastery_level = VERDICT_LEVEL[verdict]
            conn = db()
            conn.execute(
                "INSERT INTO mastery (user_id, course_id, level, attempts, last_eval, updated_at) "
                "VALUES (?,?,?,1,?,?) "
                "ON CONFLICT(user_id, course_id) DO UPDATE SET "
                "level=excluded.level, attempts=attempts+1, last_eval=excluded.last_eval, "
                "updated_at=excluded.updated_at",
                (uid, course_id, mastery_level, reason or verdict, now_iso()))
            conn.commit()
            conn.close()

        self._send_json(200, {
            "session_id": session_id,
            "reply": reply,
            "emotion": emotion,
            "emotion_label": EMOTION_LABEL.get(emotion, "平和"),
            "verdict": verdict,
            "verdict_reason": reason,
            "mastery_level": mastery_level,
            "stage": stage,
            "stage_pass": stage_pass,
            "criteria": criteria,
            "round": round_no + 1,
        })


    # ---------- 课程 AI 深度讲解（分步结构化：要点→例题→确认） ----------
    def _lesson_explain(self, uid, body):
        course_id = body.get("course_id")
        topic = C.TOPIC_INDEX.get(course_id)
        if not topic:
            self._send_json(404, {"error": "未找到该课程知识点"})
            return
        settings = resolve_llm_settings(get_settings(uid), "teaching")
        # 分步讲解内容较长（每要点含 1~2 道完整例题），给足输出上限避免被截断
        settings["max_tokens"] = 8192
        lang = topic.get("lang") or "zh"
        ctx = C.course_context(course_id)
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))
        if is_mock:
            data = C.mock_lesson_explain(topic, lang)  # 结构化 dict
            self._send_json(200, {"title": data.get("title", topic.get("title", "")),
                                  "points": data.get("points", []),
                                  "summary": data.get("summary", ""),
                                  "mock": True, "lang": lang})
            return
        if lang == "en":
            sysmsg = ("You are a patient, warm K12 tutor. You teach one student face to face, step by "
                      "step, with vivid real-life examples and CONCRETE worked problems. You make sure "
                      "they truly understand each idea before moving on. Never use LaTeX or math code.")
            prompt = (
                "Teach the topic below to a student of the given grade, as a real teacher would. "
                "Be concrete and detailed — NOT vague summaries.\n"
                "Topic context:\n" + ctx + "\n\n"
                "Structure your lesson EXACTLY like this:\n"
                "1) Break the topic into 3-4 'key points'.\n"
                "2) For EACH key point:\n"
                "   - 'explain': explain the idea clearly in 4-6 sentences, with a real-life example or "
                "analogy so the student truly gets it (not a one-line summary).\n"
                "   - 'example': give 1-2 CONCRETE worked problems. Each problem must be specific "
                "(real numbers / a real sentence / a real situation), then show EVERY solving step one by "
                "one, and end with the final answer. Do NOT just give a self-check question — give a full "
                "worked-out example with the answer.\n"
                "3) End with a short 'summary' that ties the points together.\n\n"
                "MATH FORMAT RULE (critical): write math in plain readable text only. "
                "Fractions as 1/2, 3/4; multiplication as 'x' (letter) or '*'; never use \\frac, LaTeX or \\(...\\). "
                "Example: write '1/2 x 8 = 4', NOT '\\frac{1}{2} \\times 8'.\n"
                "Use '\\n' to separate steps inside 'example' so each step is on its own line.\n\n"
                "Respond with ONLY a JSON object, no markdown fences, exactly this shape:\n"
                '{"title":"...","points":[{"key":"key point title","explain":"clear explanation with a real example","example":"Problem 1: ...\\nStep 1: ...\\nStep 2: ...\\nAnswer: ..."}],"summary":"..."}\n'
                "Use warm spoken English. 3-4 points."
            )
        else:
            sysmsg = ("你是一位耐心、亲切、特别会讲课的中小学老师，善于把抽象知识讲得通俗易懂。"
                      "你会像面对面给一个学生讲课一样，一个要点一个要点地讲，每个要点都配上具体的例题，"
                      "把每一步都算/分析给学生看，让他真正听懂、会做题，绝不用难懂的公式代码，也绝不只给空泛的总结。")
            prompt = (
                "请就下面的知识点，为这个年级的学生写一节「分步讲解课」，就像你坐在他身边一对一讲课。\n"
                "要求内容具体、详细、能让学生学会做题，不要只写空泛的总结性套话。\n"
                "知识点背景：\n" + ctx + "\n\n"
                "请严格按下面的结构来写：\n"
                "1）把这个知识点拆成 3~4 个「要点」；\n"
                "2）对【每一个要点】写两部分：\n"
                "   ·「explain」讲解：用 4~6 句话把这个概念讲清楚讲透，多用生活中的例子和打比方，"
                "让学生真正理解，不要只写一句话的概括；\n"
                "   ·「example」例题：给出【1~2 道具体例题】。题目必须具体——数学要有真实的数字或生活情境，"
                "语文/英语要有真实的句子或词语；然后把解题（或分析）的【每一步】一步一步写清楚，最后写出最终答案。"
                "绝对不要只写一个「自测问题」，必须是有完整过程和答案的例题；\n"
                "3）最后写一段「总结」，把几个要点串起来，帮学生形成完整印象。\n\n"
                "【数学写法规则（非常重要）】：一律用学生看得懂的普通写法。\n"
                "分数写成 1/2、3/4；乘号写成 ×；除号写成 ÷；绝对不要使用 LaTeX 那种代码，"
                "禁止出现 \\frac、\\times、\\( \\) 这类符号。\n"
                "例如：写「1/2 × 8 = 4」，不要写「\\frac{1}{2} \\times 8」。\n"
                "在「example」里，请用「\\n」把每一步分行，让学生看得清每一步。\n\n"
                "请用亲切的口语化中文。每个要点都要像真老师在讲课，先讲清楚再用例题手把手带做。\n\n"
                "请只输出一个 JSON 对象（不要加 markdown 代码块），格式如下：\n"
                '{"title":"...","points":[{"key":"要点标题","explain":"把概念讲透（含生活例子/打比方，4~6句）","example":"例题1：……\\n第一步：……\\n第二步：……\\n答案：……"}],"summary":"本章总结"}'
                "要点数量 3~4 个。"
            )
        messages = [
            {"role": "system", "content": sysmsg},
            {"role": "user", "content": prompt},
        ]
        try:
            raw = call_llm(messages, settings, lang)
            obj = parse_llm_response(raw)
            points = obj.get("points") or []
            norm = []
            for p in points:
                if not isinstance(p, dict):
                    continue
                norm.append({
                    "key": str(p.get("key", "")).strip(),
                    "explain": str(p.get("explain", "")).strip(),
                    "example": str(p.get("example", "")).strip(),
                })
            if not norm:
                raise ValueError("模型未返回结构化要点")
            self._send_json(200, {
                "title": str(obj.get("title", topic.get("title", ""))).strip(),
                "points": norm,
                "summary": str(obj.get("summary", "")).strip(),
                "mock": False, "lang": lang,
            })
        except Exception:
            data = C.mock_lesson_explain(topic, lang)
            self._send_json(200, {"title": data.get("title", topic.get("title", "")),
                                  "points": data.get("points", []),
                                  "summary": data.get("summary", ""),
                                  "mock": True, "lang": lang})

    def _lesson_reexplain(self, uid, body):
        """学生没听懂某要点时，换一种完全不同的讲法再讲一遍。"""
        course_id = body.get("course_id")
        topic = C.TOPIC_INDEX.get(course_id)
        if not topic:
            self._send_json(404, {"error": "未找到该课程知识点"})
            return
        settings = resolve_llm_settings(get_settings(uid), "teaching")
        settings["max_tokens"] = 4096
        lang = topic.get("lang") or "zh"
        key = (body.get("key") or "").strip()
        prev_explain = (body.get("explain") or "").strip()
        prev_example = (body.get("example") or "").strip()
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))
        if is_mock:
            d = C.mock_lesson_reexplain(topic, key, lang)
            self._send_json(200, {"explain": d.get("explain", ""), "example": d.get("example", ""), "mock": True})
            return
        if lang == "en":
            sysmsg = "You are a patient K12 tutor who can explain the same idea in many different ways."
            prompt = (
                "A student did NOT understand this key point even after your first explanation. "
                "Re-teach it with a COMPLETELY DIFFERENT approach: a different analogy, slower pacing, "
                "plainer words, or a new real-life example. Then give a NEW worked example.\n"
                "Key point: " + key + "\n"
                "Your previous explanation: " + prev_explain + "\n"
                "Your previous example: " + prev_example + "\n\n"
                "MATH FORMAT: plain text only (1/2, x for multiply). No LaTeX, no \\frac, no \\(...\\).\n"
                'Respond with ONLY JSON: {"explain":"...","example":"..."}'
            )
        else:
            sysmsg = "你是一位特别会打比方的中小学老师，同一个知识点能用很多种完全不同的方式讲清楚。"
            prompt = (
                "学生听了你对下面这个要点的讲解后【还是没听懂】。请用【完全不同的方法】再讲一遍："
                "换一个生活比喻、把节奏放慢、用更基础的大白话，或者举一个全新的生活例子。然后给一道【新的例题】。\n"
                "要点：" + key + "\n"
                "你刚才的讲解：" + prev_explain + "\n"
                "你刚才的例题：" + prev_example + "\n\n"
                "【数学写法规则】：一律用普通可读写法，分数写 1/2，乘号写 ×，禁止 LaTeX（\\frac、\\times、\\( \\) 都不能出现）。\n\n"
                "请只输出一个 JSON 对象（不要 markdown 代码块）：\n"
                '{"explain":"换一种方式的通俗讲解","example":"一道新的例题及完整解题步骤"}'
            )
        messages = [{"role": "system", "content": sysmsg},
                    {"role": "user", "content": prompt}]
        try:
            raw = call_llm(messages, settings, lang)
            obj = parse_llm_response(raw)
            explain = str(obj.get("explain") or obj.get("reply") or obj.get("text") or "").strip()
            example = str(obj.get("example") or "").strip()
            # 模型偶尔会把 JSON 再包一层（上一轮讲解文本里有引号导致外层 JSON 失效），
            # 此时 explain 自身仍是一段 JSON 字符串，再解一层取出真实内容
            if explain.startswith("{"):
                try:
                    obj2 = json.loads(explain)
                    if isinstance(obj2, dict):
                        explain = str(obj2.get("explain") or obj2.get("reply") or explain).strip()
                        if not example:
                            example = str(obj2.get("example") or "").strip()
                except Exception:
                    pass
            if not explain:
                raise ValueError("换讲法未返回内容")
            self._send_json(200, {
                "explain": explain,
                "example": example,
                "mock": False,
            })
        except Exception:
            d = C.mock_lesson_reexplain(topic, key, lang)
            self._send_json(200, {"explain": d.get("explain", ""), "example": d.get("example", ""), "mock": True})

    # ---------------- 📸 拍照 / 输入题目：AL 老师解析讲解 ----------------
    def _problem_explain(self, uid, body):
        """把学生拍/写的一道具体题，算出答案并分步讲透，让学生学明白。
        返回结构化讲解，前端用「讲解卡片」渲染，并支持朗读与追问。"""
        problem = (body.get("problem") or "").strip()
        if len(problem) < 2:
            self._send_json(400, {"error": "题目内容为空，请先拍照识别或手动输入题目"})
            return
        lang = (body.get("lang") or "zh").lower()
        if lang not in ("zh", "en"):
            lang = "zh"
        settings = resolve_llm_settings(get_settings(uid), "teaching")
        settings["max_tokens"] = 4096
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))
        if is_mock:
            d = mock_problem_explain(problem, lang)
            self._send_json(200, dict(d, mock=True, lang=lang))
            return
        if lang == "en":
            sysmsg = ("You are a patient, warm K12 tutor. A student gives you ONE specific problem "
                      "(photo or typed). Solve it step by step and teach them to truly understand. "
                      "Never use LaTeX or math code; use plain readable text.")
            prompt = (
                "Here is a student's problem. Solve it correctly, then teach the student how to solve it.\n"
                "Problem:\n" + problem + "\n\n"
                "Respond with ONLY a JSON object (no markdown fences) in EXACTLY this shape:\n"
                '{"problem":"restate the problem in clear words",'
                '"knowledge":["key concept 1","key concept 2"],'
                '"analysis":"how to approach it / why this method",'
                '"steps":["Step 1: ...","Step 2: ...","Step 3: ... (with the final answer)"],'
                '"answer":"the final answer",'
                '"common_mistakes":["a common mistake to avoid","another one"],'
                '"practice":"one similar practice problem for the student to try"}\n'
                "Rules: work slowly and show EVERY step with real numbers; end the last step with the answer; "
                "keep language warm and spoken. Fractions as 1/2, multiply as 'x' or '*'. No LaTeX."
            )
        else:
            sysmsg = ("你是一位耐心、亲切、特别会讲题的中小学老师。学生给你一道【具体的题】（可能是拍照识别或手打），"
                      "你要先确认题意、再把它【算对/分析对】，然后一步一步讲给学生听，让他真正学明白、以后遇到同类题自己会做。"
                      "绝不用难懂的公式代码，也绝不只给答案不讲过程。")
            prompt = (
                "下面是一道学生提交的具体题目。请先把这道题做对，再用「老师面对面讲题」的方式教学生怎么做出来。\n"
                "题目：\n" + problem + "\n\n"
                "请只输出一个 JSON 对象（不要加 markdown 代码块），格式严格如下：\n"
                '{"problem":"用大白话把题意重述清楚",'
                '"knowledge":["考查的知识点1","考查的知识点2"],'
                '"analysis":"破题思路：这道题在考什么、该从哪儿下手、为什么用这个方法",'
                '"steps":["第一步：……","第二步：……","第三步：……（最后一步写出答案）"],'
                '"answer":"这道题的最终答案",'
                '"common_mistakes":["学生最容易踩的坑1","容易混淆的点2"],'
                '"practice":"一道同类型的巩固练习题，让学生自己练"}\n'
                "要求：\n"
                "· 每一步都要【写出具体数字/具体推理】，一步一步来，不要跳步；最后一步给出答案；\n"
                "· 讲法要像真老师在旁边，口语化、亲切，多用生活例子打比方；\n"
                "·【数学写法规则（非常重要）】：分数写成 1/2、3/4；乘号写成 ×；除号写成 ÷；"
                "绝对禁止 LaTeX 代码，禁止出现 \\frac、\\times、\\( \\) 这类符号。\n"
                "· 步骤数一般 3~6 步，把关键变形和易错处点出来。"
            )
        messages = [{"role": "system", "content": sysmsg},
                    {"role": "user", "content": prompt}]
        try:
            raw = call_llm(messages, settings, lang)
            obj = parse_llm_response(raw)
            steps = obj.get("steps") or []
            if isinstance(steps, str):
                steps = [s for s in steps.split("\n") if s.strip()] or [steps]
            norm_steps = [str(s).strip() for s in steps if str(s).strip()]
            know = obj.get("knowledge") or []
            if isinstance(know, str):
                know = [know]
            mistakes = obj.get("common_mistakes") or []
            if isinstance(mistakes, str):
                mistakes = [mistakes]
            result = {
                "problem": str(obj.get("problem") or problem).strip(),
                "knowledge": [str(k).strip() for k in know if str(k).strip()][:6],
                "analysis": str(obj.get("analysis") or "").strip(),
                "steps": norm_steps,
                "answer": str(obj.get("answer") or "").strip(),
                "common_mistakes": [str(m).strip() for m in mistakes if str(m).strip()][:4],
                "practice": str(obj.get("practice") or "").strip(),
                "mock": False, "lang": lang,
            }
            if not (result["analysis"] or result["steps"] or result["answer"]):
                raise ValueError("模型未返回有效讲解")
            self._send_json(200, result)
        except Exception:
            d = mock_problem_explain(problem, lang)
            self._send_json(200, dict(d, mock=True, lang=lang))

    def _problem_followup(self, uid, body):
        """学生对某道已讲题目的追问（如「第二步没懂」「换种讲法」）。
        结合原题与上文讲解，给出针对性、口语化的澄清。"""
        problem = (body.get("problem") or "").strip()
        prev = (body.get("prev") or "").strip()        # 上一次完整讲解文本
        question = (body.get("question") or "").strip()
        if not question:
            self._send_json(400, {"error": "请先输入你的追问"})
            return
        lang = (body.get("lang") or "zh").lower()
        if lang not in ("zh", "en"):
            lang = "zh"
        settings = resolve_llm_settings(get_settings(uid), "teaching")
        settings["max_tokens"] = 2048
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))
        if is_mock:
            reply = ("（演示模式）这一步你可以先停下来，把已知条件在纸上列一遍，再对照刚才的步骤看卡在哪一环。"
                     "接入真实模型后，我会针对你的具体问题一步步带你过。")
            self._send_json(200, {"reply": reply, "mock": True})
            return
        if lang == "en":
            sysmsg = "You are a patient K12 tutor answering a student's follow-up about a problem you just explained."
            prompt = ("The student asked a follow-up. Answer it warmly and clearly, in spoken English.\n"
                      "Original problem:\n" + problem + "\n\n"
                      "Your previous explanation:\n" + prev + "\n\n"
                      "Student's question: " + question + "\n\n"
                      "Reply in plain text (no LaTeX). If they didn't understand a step, re-explain that step slowly.")
        else:
            sysmsg = "你是一位特别会讲题的中小学老师，正在回答学生对刚才那道题的追问。"
            prompt = ("学生对你刚讲的题追问了一句，请用口语化、亲切的中文回答，把他的疑问真正解开。\n"
                      "原题：\n" + problem + "\n\n"
                      "你刚才的讲解：\n" + prev + "\n\n"
                      "学生的追问：" + question + "\n\n"
                      "要求：如果他是某一步没懂，就把那一步放慢、换打比方再讲一遍；不要只重复原话。数学用普通写法（1/2、×、÷），禁止 LaTeX。"
                      "直接给出澄清文字即可，不要 JSON。"
            )
        messages = [{"role": "system", "content": sysmsg},
                    {"role": "user", "content": prompt}]
        try:
            raw = call_llm(messages, settings, lang)
            obj = parse_llm_response(raw)
            reply = str(obj.get("reply") or obj.get("text") or raw).strip()
            if not reply:
                raise ValueError("未返回内容")
            self._send_json(200, {"reply": reply, "mock": False})
        except Exception:
            self._send_json(200, {"reply": "（演示模式）这一步你可以先停下来，把已知条件在纸上列一遍，再对照刚才的步骤看卡在哪一环。",
                                  "mock": True})

    # ---------------- 精准学：图谱 / 诊断 / 练习 ----------------
    def _precision_graph(self, uid, subject, grade):
        self._send_json(200, self._build_graph_dict(uid, subject, grade))

    def _build_graph_dict(self, uid, subject, grade):
        units = C.list_units()
        unit = next((u for u in units if u["subject"] == subject and u["grade"] == grade), None)
        nodes = []
        if unit:
            conn = db()
            lvl = {r["course_id"]: r["level"] for r in
                   conn.execute("SELECT course_id, level FROM mastery WHERE user_id=?",
                                (uid,)).fetchall()}
            conn.close()
            for t in unit["topics"]:
                lv = lvl.get(t["id"], 0)
                nodes.append({"course_id": t["id"], "title": t["title"],
                              "sub": t.get("sub", []), "goals": t.get("goals", ""),
                              "level": lv, "color": _color(lv)})
        return {"subject": subject, "grade": grade, "nodes": nodes}

    def _precision_diagnose(self, uid, body):
        subject = (body.get("subject") or "").strip()
        grade = (body.get("grade") or "").strip()
        course_ids = body.get("course_ids") or None
        if not subject or not grade:
            self._send_json(400, {"error": "缺少 subject / grade"})
            return
        units = C.list_units()
        unit = next((u for u in units if u["subject"] == subject and u["grade"] == grade), None)
        if not unit:
            self._send_json(404, {"error": "未找到该学科/年级"})
            return
        if course_ids:
            want = set(course_ids)
            topics = [t for t in unit["topics"] if t["id"] in want]
        else:
            topics = unit["topics"]
        conn = db()
        lvl = {r["course_id"]: r["level"] for r in
               conn.execute("SELECT course_id, level FROM mastery WHERE user_id=?",
                            (uid,)).fetchall()}
        conn.close()
        topics_sorted = sorted(topics, key=lambda t: lvl.get(t["id"], 0))
        pick = (topics_sorted[:8] if not course_ids else topics[:8])
        # 薄弱项基线（口径统一：该学科/年级下 level 为 0 或 1 的知识点数）
        # 再测前后的对比都按这个口径算，才能看出「攻克了几个」
        scope = "weak" if course_ids else "full"
        weak_before = sum(1 for t in unit["topics"] if lvl.get(t["id"], 0) in (0, 1))
        weak_total = len([t for t in unit["topics"] if lvl.get(t["id"], 0) in (0, 1)])
        settings = resolve_llm_settings(get_settings(uid), "teaching")
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))
        if is_mock:
            questions = [mock_diagnose_q(t) for t in pick]
        else:
            questions = ai_diagnose_questions(pick, settings)
        diag_id = secrets.token_hex(8)
        DIAG_SESSIONS[diag_id] = {"uid": uid, "subject": subject, "grade": grade,
                                  "questions": questions, "scope": scope,
                                  "weak_before": weak_before, "mock": is_mock}
        out = [{"qid": q["qid"], "topic_id": q["topic_id"], "topic_title": q["topic_title"],
                "stem": q["stem"], "options": q["options"]} for q in questions]
        self._send_json(200, {"diag_id": diag_id, "subject": subject, "grade": grade,
                              "questions": out, "mock": is_mock, "scope": scope,
                              "weak_before": weak_before, "weak_total": weak_total,
                              "covered": len(pick)})

    def _precision_diagnose_grade(self, uid, body):
        diag_id = body.get("diag_id")
        answers = body.get("answers") or {}
        sess = DIAG_SESSIONS.get(diag_id)
        if not sess or sess.get("uid") != uid:
            self._send_json(404, {"error": "诊断会话不存在或已失效，请重新诊断"})
            return
        results = []
        now = now_iso()
        conn = db()
        for q in sess["questions"]:
            aid = answers.get(q["qid"])
            try:
                aid = int(aid)
            except Exception:
                aid = -1
            correct = (aid == q["answer"])
            newlv = 4 if correct else 1
            conn.execute(
                "INSERT INTO mastery(user_id, course_id, level, attempts, last_eval, updated_at) "
                "VALUES(?,?,?,1,?,?) "
                "ON CONFLICT(user_id, course_id) DO UPDATE SET "
                "level=excluded.level, attempts=attempts+1, last_eval=excluded.last_eval, "
                "updated_at=excluded.updated_at",
                (uid, q["topic_id"], newlv, ("诊断" + ("通过" if correct else "未过")), now))
            results.append({"topic_id": q["topic_id"], "topic_title": q["topic_title"],
                            "correct": correct, "level": newlv, "color": _color(newlv)})
        conn.commit()
        conn.close()
        DIAG_SESSIONS.pop(diag_id, None)
        weak = [r["topic_id"] for r in results if not r["correct"]]
        graph = self._build_graph_dict(uid, sess["subject"], sess["grade"])
        # 再测后的薄弱项（同一口径：level<=1 的知识点数）→ 和 weak_before 相减就是「攻克了几个」
        weak_after = sum(1 for n in graph["nodes"] if n["level"] <= 1)
        weak_before = sess.get("weak_before", 0)
        correct_count = sum(1 for r in results if r["correct"])
        fixed = [r["topic_title"] for r in results if r["correct"]]
        still = [r["topic_title"] for r in results if not r["correct"]]
        try:
            conn = db()
            conn.execute(
                "INSERT INTO retest_log(user_id, subject, grade, scope, total, correct, "
                "weak_before, weak_after, fixed_json, still_json, created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (uid, sess["subject"], sess["grade"], sess.get("scope", "full"),
                 len(results), correct_count, weak_before, weak_after,
                 json.dumps(fixed, ensure_ascii=False), json.dumps(still, ensure_ascii=False),
                 now_iso()))
            conn.commit()
            conn.close()
        except Exception:
            pass
        self._send_json(200, {"results": results, "weak": weak, "graph": graph,
                              "scope": sess.get("scope", "full"),
                              "weak_before": weak_before, "weak_after": weak_after,
                              "fixed_count": max(0, weak_before - weak_after),
                              "fixed": fixed, "still": still,
                              "correct_count": correct_count, "total": len(results),
                              "mock": sess.get("mock", False)})

    def _precision_practice(self, uid, body):
        course_id = (body.get("course_id") or "").strip()
        tier = (body.get("tier") or "基础").strip()
        topic = C.TOPIC_INDEX.get(course_id)
        if not topic:
            self._send_json(404, {"error": "未找到该知识点"})
            return
        settings = resolve_llm_settings(get_settings(uid), "teaching")
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))
        if is_mock:
            seen_stems = set()
            qs = []
            for i in range(5):
                q = mock_practice_q(topic, tier, idx=i, _seen_stems=seen_stems)
                stem = (q.get("stem") or "").strip()
                # 二重保障：即使 mock_practice_q 内部去重后仍可能极端撞题
                attempts = 0
                while stem in seen_stems and attempts < 20:
                    q = mock_practice_q(topic, tier, idx=i + 100 + attempts * 7, _seen_stems=seen_stems)
                    stem = (q.get("stem") or "").strip()
                    attempts += 1
                seen_stems.add(stem)
                qs.append(q)
        else:
            qs = ai_practice_q(topic, tier, settings)
        # 统一质量校验：过滤垃圾题 + 去重 + 格式清洗
        qs = _validate_and_dedup_questions(qs, topic, 5)
        # 给每道题分配唯一 qid
        questions = []
        for qi, q in enumerate(qs):
            qid = secrets.token_hex(6)
            PRACTICE_SESSIONS[qid] = {"uid": uid, "course_id": course_id, "tier": tier,
                                      "answer": q["answer"], "explanation": q.get("explanation", ""),
                                      "stem": q["stem"], "options": q.get("options")}
            questions.append({"qid": qid, "stem": q["stem"], "options": q.get("options"), "idx": qi + 1})
        self._send_json(200, {"course_id": course_id, "tier": tier,
                              "questions": questions, "total": len(questions), "mock": is_mock})

    def _precision_practice_grade(self, uid, body):
        # answers: [{qid: "...", user_answer: 0}, ...]
        answers = body.get("answers") or []
        if not isinstance(answers, list):
            # 兼容旧格式：单题 {qid, user_answer}
            answers = [body] if body.get("qid") else []
        results = []
        correct_count = 0
        for item in answers:
            qid = item.get("qid")
            ua = item.get("user_answer")
            sess = PRACTICE_SESSIONS.get(qid)
            if not sess or sess.get("uid") != uid:
                results.append({"qid": qid, "error": "会话不存在"})
                continue
            ans = sess["answer"]
            try:
                ua_int = int(ua)
            except Exception:
                ua_int = -1
            correct = (ua_int == ans) if isinstance(ans, int) else (str(ua).strip() == str(ans).strip())
            if correct:
                correct_count += 1
                saved_mistake = False
            else:
                conn = db()
                cat = _guess_mistake_category(sess["stem"], ua, ans, sess.get("options"))
                conn.execute(
                    "INSERT INTO mistakes(user_id, course_id, tier, stem, options, answer, user_answer, explanation, created_at, category, next_review) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (uid, sess["course_id"], sess["tier"], sess["stem"],
                     json.dumps(sess.get("options"), ensure_ascii=False),
                     str(ans), str(ua), sess.get("explanation", ""), now_iso(),
                     cat, _first_review_date()))
                conn.commit()
                conn.close()
                saved_mistake = True
            results.append({"qid": qid, "correct": correct,
                           "answer": ans, "explanation": sess.get("explanation", ""),
                           "saved_mistake": saved_mistake})
            PRACTICE_SESSIONS.pop(qid, None)
        total = len(results)
        score = f"{correct_count}/{total}"
        self._send_json(200, {"results": results, "correct_count": correct_count,
                              "total": total, "score": score})

    def _precision_test(self, uid, body):
        """课后自测：为该知识点生成覆盖全部核心内容的自测题（题量=子内容数，封顶 20 道）。"""
        course_id = (body.get("course_id") or "").strip()
        topic = C.TOPIC_INDEX.get(course_id)
        if not topic:
            self._send_json(404, {"error": "未找到该知识点"})
            return
        settings = resolve_llm_settings(get_settings(uid), "teaching")
        is_mock = bool(settings.get("mock_mode", 1) or not settings.get("api_key"))
        C.reload_gen()  # 热加载最新生成的课件内容（生成任务边跑边用）
        # 出题计划：覆盖全部核心子内容，每个子内容 1 题，题量=子内容数（封顶 20）
        plan = _test_plan(topic)
        n, per, m = plan["n"], plan["per"], plan["m"]
        # 真实讲解内容（定义/公式/例题）作为出题素材，让题目贴合知识点、有深度
        content_hint = _build_content_hint(topic, course_id=course_id)
        if is_mock:
            # 出题优先级：Ollama 生成 > 种子题库 > 兜底抽取
            qs = _assemble_gen_questions(topic, course_id, n)
            if not qs:
                qs = _assemble_seed_questions(topic, course_id, n)
            if not qs:
                # 兜底：无生成内容且无种子时，基于讲解文本抽取出题
                subs = topic.get("sub") or [topic.get("title", "")]
                qs = []
                used = {"facts": set()}
                for g in range(n):
                    sub_i = g // per
                    qs.append(mock_test_q(topic, sub_i % max(m, 1), used, course_id=course_id))
        else:
            qs = ai_test_qs(topic, settings, n, content_hint)
        # ── 统一质量校验：格式清洗 + 内容垃圾过滤 + 去重 + 补足 ──
        qs = _validate_and_dedup_questions(qs, topic, n)
        questions = []
        for qi, q in enumerate(qs):
            qid = secrets.token_hex(6)
            qtype = q.get("type", "choice")
            TEST_SESSIONS[qid] = {"uid": uid, "course_id": course_id,
                                  "answer": q["answer"], "explanation": q.get("explanation", ""),
                                  "stem": q["stem"], "options": q.get("options"), "type": qtype}
            questions.append({"qid": qid, "stem": q["stem"], "options": q.get("options"),
                              "type": qtype, "idx": qi + 1})
        self._send_json(200, {"course_id": course_id, "topic": topic["title"],
                              "questions": questions, "total": len(questions), "mock": is_mock})

    def _precision_test_grade(self, uid, body):
        """课后自测判分：按正确率 + 做题时间评估掌握度，AL 给出判定与复习建议。"""
        answers = body.get("answers") or []
        times = body.get("times") or {}
        total_time = body.get("total_time") or 0
        if not isinstance(answers, list):
            answers = [body] if body.get("qid") else []
        results = []
        correct_count = 0
        for item in answers:
            qid = item.get("qid")
            sess = TEST_SESSIONS.get(qid)
            if not sess or sess.get("uid") != uid:
                results.append({"qid": qid, "error": "会话不存在或已失效，请重新测试"})
                continue
            try:
                ua_int = int(item.get("user_answer"))
            except Exception:
                ua_int = -1
            ans = sess["answer"]
            qtype = sess.get("type", "choice")
            if qtype == "choice":
                correct = (ua_int == ans)
            else:
                # 填空/计算题：字符串答案宽松比对（容忍空格、$ 包裹、数值等价）
                correct = _norm_answer(item.get("user_answer"), ans)
            if correct:
                correct_count += 1
                saved = False
            else:
                conn = db()
                cat = _guess_mistake_category(sess["stem"], item.get("user_answer"), ans, sess.get("options"))
                conn.execute(
                    "INSERT INTO mistakes(user_id, course_id, tier, stem, options, answer, user_answer, explanation, created_at, category, next_review) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (uid, sess["course_id"], "测试", sess["stem"],
                     json.dumps(sess.get("options"), ensure_ascii=False),
                     str(ans), str(item.get("user_answer")), sess.get("explanation", ""), now_iso(),
                     cat, _first_review_date()))
                conn.commit()
                conn.close()
                saved = True
            results.append({"qid": qid, "correct": correct, "type": qtype,
                           "answer": ans, "explanation": sess.get("explanation", ""),
                           "saved_mistake": saved, "time": times.get(qid)})
            TEST_SESSIONS.pop(qid, None)
        total = len([r for r in results if "error" not in r])
        if total == 0:
            self._send_json(400, {"error": "没有有效的作答记录"})
            return
        accuracy = round(correct_count / total * 100)
        tvals = [r.get("time") for r in results if isinstance(r.get("time"), (int, float))]
        avg_time = round(sum(tvals) / len(tvals)) if tvals else 0
        total_time = int(total_time) if isinstance(total_time, (int, float)) else 0
        level = eval_mastery_level(accuracy, avg_time)
        # 需要前端回传 course_id 以落库掌握度
        cid = body.get("course_id") or ""
        topic = C.TOPIC_INDEX.get(cid)
        subs = (topic.get("sub") or []) if topic else []
        settings = resolve_llm_settings(get_settings(uid), "teaching")
        verdict_info = ai_evaluate_test(topic["title"] if topic else (cid or "本知识点"),
                                        subs, results, accuracy, avg_time, total_time, settings)
        verdict = verdict_info.get("verdict") or MASTERY_LABEL.get(level, "未掌握")
        vlevel = VERDICT_LEVEL.get(verdict, level)
        # 落库掌握度
        if cid:
            conn = db()
            conn.execute(
                "INSERT INTO mastery(user_id, course_id, level, attempts, last_eval, updated_at) "
                "VALUES(?,?,?,1,?,?) "
                "ON CONFLICT(user_id, course_id) DO UPDATE SET "
                "level=excluded.level, attempts=attempts+1, last_eval=excluded.last_eval, "
                "updated_at=excluded.updated_at",
                (uid, cid, vlevel, f"课后自测 {correct_count}/{total}", now_iso()))
            conn.commit()
            conn.close()
        self._send_json(200, {
            "results": results, "correct_count": correct_count, "total": total,
            "accuracy": accuracy, "avg_time": avg_time, "total_time": total_time,
            "level": vlevel, "verdict": verdict,
            "reason": verdict_info.get("reason", ""), "advice": verdict_info.get("advice", ""),
            "relearn": verdict_info.get("relearn", []), "course_id": cid,
        })

    def _precision_mistakes(self, uid, category=None, only_review=False):
        conn = db()
        sql = ("SELECT id, course_id, tier, stem, options, answer, user_answer, "
               "explanation, created_at, category, review_count, next_review, mastered, "
               "redo_count, redo_correct, last_redo_at "
               "FROM mistakes WHERE user_id=?")
        params = [uid]
        if category:
            sql += " AND category=?"
            params.append(category)
        if only_review:
            sql += " AND mastered=0 AND next_review<=?"
            params.append(now_iso())
        # 未掌握的排在前面，同组内新错题优先
        sql += " ORDER BY mastered ASC, id DESC LIMIT 200"
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        out = [dict(r) for r in rows]
        for o in out:
            try:
                o["options"] = json.loads(o["options"]) if o["options"] else None
            except Exception:
                o["options"] = None
            # 计算距离下次复习的状态
            nr = o.get("next_review")
            if nr and not o.get("mastered"):
                o["due_review"] = nr <= now_iso()
            else:
                o["due_review"] = False
        self._send_json(200, {"mistakes": out})

    def _mistakes_stats(self, uid):
        """错题统计：总数、各分类数量、待复习、已掌握"""
        conn = db()
        total = conn.execute("SELECT COUNT(*) AS c FROM mistakes WHERE user_id=?", (uid,)).fetchone()["c"]
        mastered = conn.execute("SELECT COUNT(*) AS c FROM mistakes WHERE user_id=? AND mastered=1", (uid,)).fetchone()["c"]
        due = conn.execute("SELECT COUNT(*) AS c FROM mistakes WHERE user_id=? AND mastered=0 AND next_review<=?",
                           (uid, now_iso())).fetchone()["c"]
        # 按分类统计
        by_cat = {}
        for r in conn.execute("SELECT category, COUNT(*) AS c FROM mistakes WHERE user_id=? GROUP BY category", (uid,)).fetchall():
            cat = r["category"] or "未分类"
            by_cat[cat] = r["c"]
        # 按学科统计
        by_subj = {}
        for r in conn.execute("SELECT course_id FROM mistakes WHERE user_id=?", (uid,)).fetchall():
            cid = r["course_id"]
            topic = C.TOPIC_INDEX.get(cid)
            if topic:
                subj = topic.get("subject", "其他")
                by_subj[subj] = by_subj.get(subj, 0) + 1
        conn.close()
        self._send_json(200, {
            "total": total, "mastered": mastered,
            "due_today": due, "by_category": by_cat, "by_subject": by_subj
        })

    def _mistakes_review_today(self, uid):
        """今日待复习错题清单（艾宾浩斯到期）"""
        conn = db()
        rows = conn.execute(
            "SELECT id, course_id, stem, options, answer, explanation, category, review_count "
            "FROM mistakes WHERE user_id=? AND mastered=0 AND next_review<=? "
            "ORDER BY next_review ASC LIMIT 50",
            (uid, now_iso())).fetchall()
        conn.close()
        out = [dict(r) for r in rows]
        for o in out:
            try:
                o["options"] = json.loads(o["options"]) if o["options"] else None
            except Exception:
                o["options"] = None
        self._send_json(200, {"due_count": len(out), "items": out})

    def _mistakes_mark_mastered(self, uid, mid):
        """标记错题已掌握"""
        conn = db()
        conn.execute("UPDATE mistakes SET mastered=1 WHERE id=? AND user_id=?", (mid, uid))
        conn.commit()
        conn.close()
        self._send_json(200, {"ok": True})

    def _mistakes_mark_reviewed(self, uid, mid):
        """标记复习过一次，按艾宾浩斯更新下次复习时间"""
        # 艾宾浩斯间隔：第1次1天，第2次2天，第3次4天，第4次7天，第5次15天，第6次30天，之后掌握
        intervals = [1, 2, 4, 7, 15, 30]
        conn = db()
        row = conn.execute("SELECT review_count FROM mistakes WHERE id=? AND user_id=?", (mid, uid)).fetchone()
        if not row:
            conn.close()
            self._send_json(404, {"error": "错题不存在"})
            return
        rc = (row["review_count"] or 0) + 1
        if rc >= len(intervals):
            # 复习次数够了，标记为掌握
            conn.execute("UPDATE mistakes SET review_count=?, mastered=1 WHERE id=? AND user_id=?", (rc, mid, uid))
        else:
            days = intervals[rc - 1]
            from datetime import timedelta
            next_dt = datetime.now(timezone.utc) + timedelta(days=days)
            conn.execute("UPDATE mistakes SET review_count=?, next_review=? WHERE id=? AND user_id=?",
                         (rc, next_dt.isoformat(timespec="seconds"), mid, uid))
        conn.commit()
        conn.close()
        self._send_json(200, {"ok": True, "review_count": rc})

    def _mistakes_similar(self, uid, mid):
        """同类题推荐：基于同一知识点的种子题库"""
        conn = db()
        row = conn.execute("SELECT course_id, stem FROM mistakes WHERE id=? AND user_id=?", (mid, uid)).fetchone()
        conn.close()
        if not row:
            self._send_json(404, {"error": "错题不存在"})
            return
        cid = row["course_id"]
        # 从种子题库找同类题
        similar = []
        seed = SB.SEED_BANK.get(cid)
        if seed and seed.get("subs"):
            for sub_name, qs in seed["subs"].items():
                for q in qs[:2]:  # 每个子点最多2道
                    similar.append({
                        "type": q.get("type", "choice"),
                        "stem": q.get("stem", ""),
                        "options": q.get("options", []),
                        "answer": q.get("answer"),
                        "explanation": q.get("explanation", ""),
                        "sub_point": sub_name,
                    })
        # 如果种子题库不够，用课程子点生成简单题
        if len(similar) < 3:
            topic = C.TOPIC_INDEX.get(cid)
            if topic:
                subs = topic.get("sub") or []
                for s in subs[:3]:
                    similar.append({
                        "type": "fill",
                        "stem": f"请用自己的话解释：{s}",
                        "options": [],
                        "answer": "参考课程内容",
                        "explanation": f"回顾「{topic.get('title','')}」中关于「{s}」的讲解",
                        "sub_point": s,
                    })
        self._send_json(200, {"course_id": cid, "similar": similar[:6]})

    # ---------- 错题重做闭环 ----------
    def _mistakes_redo(self, uid, mid, body):
        """重做一道错题：当场判定 + 返回解析，答对则推进艾宾浩斯复习链。"""
        from datetime import timedelta
        try:
            ua = int(body.get("answer"))
        except Exception:
            ua = -1
        conn = db()
        row = conn.execute(
            "SELECT id, course_id, tier, answer, explanation, options, review_count, "
            "mastered, redo_count, redo_correct FROM mistakes WHERE id=? AND user_id=?",
            (mid, uid)).fetchone()
        if not row:
            conn.close()
            self._send_json(404, {"error": "错题不存在"})
            return
        try:
            stored = int(row["answer"])
        except Exception:
            stored = None
        correct = (stored is not None and ua == stored)
        intervals = [1, 2, 4, 7, 15, 30]
        now = now_iso()
        rc = row["review_count"] or 0
        redo = (row["redo_count"] or 0) + 1
        redo_ok = (row["redo_correct"] or 0) + (1 if correct else 0)
        mastered = row["mastered"] or 0
        next_review = None
        if correct:
            rc += 1
            # 连续两次重做都答对，或走完复习链条 → 判为已掌握
            if rc >= len(intervals) or redo_ok >= 2:
                mastered = 1
            else:
                next_review = (datetime.now(timezone.utc) + timedelta(days=intervals[rc - 1])).isoformat(timespec="seconds")
        else:
            # 又错一次：复习链归零，明天再来；并把对应知识点掌握度降为「未掌握」
            rc = 0
            next_review = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(timespec="seconds")
            conn.execute("UPDATE mastery SET level=1, updated_at=? WHERE user_id=? AND course_id=? AND level>=4",
                         (now, uid, row["course_id"]))
        conn.execute(
            "UPDATE mistakes SET review_count=?, redo_count=?, redo_correct=?, mastered=?, "
            "next_review=COALESCE(?, next_review), last_redo_at=? WHERE id=? AND user_id=?",
            (rc, redo, redo_ok, mastered, next_review, now, mid, uid))
        conn.commit()
        conn.close()
        self._send_json(200, {
            "correct": correct, "answer": stored,
            "explanation": row["explanation"] or "",
            "mastered": bool(mastered), "review_count": rc,
            "redo_count": redo, "redo_correct": redo_ok,
            "next_review": next_review,
        })

    def _mistakes_topic_stats(self, rows, now):
        """把错题行聚合到知识点维度。"""
        by_topic = {}
        for r in rows:
            cid = r["course_id"]
            t = C.TOPIC_INDEX.get(cid) or {}
            d = by_topic.setdefault(cid, {
                "course_id": cid, "title": t.get("title", cid),
                "subject": t.get("subject", "其他"), "total": 0,
                "mastered": 0, "due": 0, "unmastered": 0})
            d["total"] += 1
            if r["mastered"]:
                d["mastered"] += 1
            else:
                d["unmastered"] += 1
                if (r["next_review"] or "") <= now:
                    d["due"] += 1
        out = sorted(by_topic.values(), key=lambda x: (-x["unmastered"], -x["total"], x["title"]))
        return out

    def _mistakes_progress(self, uid):
        """错题本学习进度：掌握率、待复习、分类/学科/知识点分布、近 7 日趋势。"""
        from datetime import timedelta
        conn = db()
        rows = conn.execute(
            "SELECT id, course_id, category, created_at, mastered, next_review, "
            "redo_count, redo_correct FROM mistakes WHERE user_id=?", (uid,)).fetchall()
        conn.close()
        rows = [dict(r) for r in rows]
        now = now_iso()
        total = len(rows)
        mastered = sum(1 for r in rows if r["mastered"])
        unmastered = total - mastered
        due = sum(1 for r in rows if not r["mastered"] and (r["next_review"] or "") <= now)
        redo_total = sum(int(r["redo_count"] or 0) for r in rows)
        redo_correct = sum(int(r["redo_correct"] or 0) for r in rows)
        by_cat, by_subj = {}, {}
        for r in rows:
            cat = r["category"] or "未分类"
            by_cat[cat] = by_cat.get(cat, 0) + 1
            t = C.TOPIC_INDEX.get(r["course_id"]) or {}
            subj = t.get("subject", "其他")
            by_subj[subj] = by_subj.get(subj, 0) + 1
        topics = self._mistakes_topic_stats(rows, now)
        today = datetime.now(timezone.utc).date()
        trend = []
        for i in range(6, -1, -1):
            ds = (today - timedelta(days=i)).isoformat()
            trend.append({"date": ds,
                          "added": sum(1 for r in rows if (r["created_at"] or "")[:10] == ds),
                          "mastered": sum(1 for r in rows if r["mastered"] and (r["created_at"] or "")[:10] == ds)})
        self._send_json(200, {
            "total": total, "mastered": mastered, "unmastered": unmastered, "due_today": due,
            "mastery_pct": round(mastered * 100.0 / total, 1) if total else 0,
            "redo_total": redo_total, "redo_correct": redo_correct,
            "by_category": by_cat, "by_subject": by_subj,
            "by_topic": topics[:20], "weak_topics": [t for t in topics if t["unmastered"]][:8],
            "trend": trend,
        })

    def _mistakes_by_topic(self, uid):
        """按知识点聚合的错题分布（薄弱知识点排行）。"""
        conn = db()
        rows = conn.execute(
            "SELECT course_id, mastered, next_review FROM mistakes WHERE user_id=?", (uid,)).fetchall()
        conn.close()
        topics = self._mistakes_topic_stats([dict(r) for r in rows], now_iso())
        self._send_json(200, {"topics": topics})

    # ---------- 精准学：学习进度总览 / 再测历史 ----------
    def _precision_progress(self, uid, subject=None, grade=None):
        """知识点掌握度分布（未测/薄弱/了解/熟悉/掌握）+ 覆盖率。"""
        units = C.list_units()
        conn = db()
        lvl = {r["course_id"]: r["level"] for r in
               conn.execute("SELECT course_id, level FROM mastery WHERE user_id=?", (uid,)).fetchall()}
        conn.close()
        sel = [u for u in units if (not subject or u["subject"] == subject)
               and (not grade or u["grade"] == grade)]
        dist = {"untested": 0, "weak": 0, "know": 0, "familiar": 0, "mastered": 0}
        total = 0
        for u in sel:
            for t in u["topics"]:
                lv = lvl.get(t["id"], 0)
                total += 1
                if lv >= 4:
                    dist["mastered"] += 1
                elif lv == 3:
                    dist["familiar"] += 1
                elif lv == 2:
                    dist["know"] += 1
                elif lv == 1:
                    dist["weak"] += 1
                else:
                    dist["untested"] += 1
        tested = total - dist["untested"]
        # 分学科分布
        by_subject = {}
        for u in units:
            s = u["subject"]
            d = by_subject.setdefault(s, {"subject": s, "total": 0, "tested": 0, "mastered": 0, "weak": 0})
            for t in u["topics"]:
                lv = lvl.get(t["id"], 0)
                d["total"] += 1
                if lv > 0:
                    d["tested"] += 1
                if lv >= 4:
                    d["mastered"] += 1
                if lv == 1:
                    d["weak"] += 1
        out_subj = []
        for d in by_subject.values():
            d["mastery_pct"] = round(d["mastered"] * 100.0 / d["total"], 1) if d["total"] else 0
            d["coverage_pct"] = round(d["tested"] * 100.0 / d["total"], 1) if d["total"] else 0
            out_subj.append(d)
        out_subj.sort(key=lambda x: (-x["total"], x["subject"]))
        # 最近一次再测
        conn = db()
        last = conn.execute(
            "SELECT scope, total, correct, weak_before, weak_after, created_at FROM retest_log "
            "WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
        conn.close()
        self._send_json(200, {
            "subject": subject, "grade": grade,
            "total": total, "tested": tested, "dist": dist,
            "mastery_pct": round(dist["mastered"] * 100.0 / total, 1) if total else 0,
            "coverage_pct": round(tested * 100.0 / total, 1) if total else 0,
            "by_subject": out_subj,
            "last_retest": dict(last) if last else None,
        })

    def _precision_retest_history(self, uid, subject=None, grade=None):
        conn = db()
        sql = ("SELECT id, subject, grade, scope, total, correct, weak_before, weak_after, "
               "fixed_json, still_json, created_at FROM retest_log WHERE user_id=?")
        params = [uid]
        if subject:
            sql += " AND subject=?"
            params.append(subject)
        if grade:
            sql += " AND grade=?"
            params.append(grade)
        sql += " ORDER BY id DESC LIMIT 20"
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        out = []
        for r in rows:
            d = dict(r)
            for k in ("fixed_json", "still_json"):
                try:
                    d[k.replace("_json", "")] = json.loads(d.pop(k) or "[]")
                except Exception:
                    d[k.replace("_json", "")] = []
            out.append(d)
        self._send_json(200, {"history": out})

    # ---------- 学习进度快照 / 断点续学 ----------
    def _study_resume_get(self, uid):
        conn = db()
        row = conn.execute("SELECT data_json, updated_at FROM study_progress WHERE user_id=?",
                           (uid,)).fetchone()
        conn.close()
        data = None
        if row:
            try:
                data = json.loads(row["data_json"])
            except Exception:
                data = None
        self._send_json(200, {"resume": data, "updated_at": row["updated_at"] if row else None})

    # ---------- 🤖 学习机模式 · AI 学伴 ----------
    def _companion_gather(self, uid, query):
        """汇总学情：今日时长 / 星星 / 连续天数 / 掌握数 / 错题待复习 / 断点续学 / 薄弱点 / 推荐下一课。"""
        ctx = {}
        conn = db()
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            row = conn.execute("SELECT COALESCE(SUM(seconds),0) AS s FROM learning_log WHERE user_id=? AND date=?",
                               (uid, today)).fetchone()
            ctx["today_sec"] = int(row["s"] or 0) if row else 0
        except Exception:
            ctx["today_sec"] = 0
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM mastery WHERE user_id=? AND level>=4",
                               (uid,)).fetchone()
            ctx["mastered"] = int(row["c"] or 0) if row else 0
        except Exception:
            ctx["mastered"] = 0
        try:
            rows = conn.execute("SELECT course_id, level FROM mastery WHERE user_id=? AND level<=1 "
                                "ORDER BY attempts DESC LIMIT 3", (uid,)).fetchall()
            weak = []
            for r in rows:
                t = C.TOPIC_INDEX.get(r["course_id"]) or {}
                weak.append({"id": r["course_id"], "title": t.get("title") or r["course_id"],
                             "level": r["level"]})
            ctx["weak"] = weak
        except Exception:
            ctx["weak"] = []
        try:
            row = conn.execute("SELECT data_json FROM study_progress WHERE user_id=?", (uid,)).fetchone()
            ctx["resume"] = json.loads(row["data_json"]) if row and row["data_json"] else None
        except Exception:
            ctx["resume"] = None
        conn.close()
        # 错题待复习（未掌握 且 复习次数 < 3）
        try:
            conn = db()
            row = conn.execute("SELECT COUNT(*) AS c FROM mistakes WHERE user_id=? "
                               "AND COALESCE(mastered,0)=0 AND COALESCE(review_count,0)<3",
                               (uid,)).fetchone()
            ctx["mistake_todo"] = int(row["c"] or 0) if row else 0
            conn.close()
        except Exception:
            ctx["mistake_todo"] = 0
        # 星星 & 连续天数（读本地记账表，读不到就 0，绝不阻塞开场）
        ctx["stars"] = 0
        ctx["streak"] = 0
        try:
            conn = db()
            row = conn.execute("SELECT COUNT(*) AS c FROM learning_log WHERE user_id=? "
                               "AND date >= date('now', '-1 day')", (uid,)).fetchone()
            ctx["active_days"] = int(row["c"] or 0) if row else 0
            conn.close()
        except Exception:
            ctx["active_days"] = 0
        # 孩子名（家庭共享档案）
        try:
            prof = self._load_child_profile()
            names = [c.get("name") for c in (prof.get("children") or []) if c.get("name")]
            ctx["child"] = prof.get("active") or (names[0] if names else "小朋友")
            ctx["daily_max"] = int(prof.get("dailyMax") or 30)
        except Exception:
            ctx["child"] = "小朋友"
            ctx["daily_max"] = 30
        # 系统推荐的下一课（复用学习计划接口的推荐逻辑）
        try:
            _mc = set(r["course_id"] for r in db().execute(
                "SELECT course_id FROM mastery WHERE user_id=? AND level>=4", (uid,)).fetchall())
            ctx["pending_course"] = _recommend_next_course(_mc)
        except Exception:
            ctx["pending_course"] = None
        # 前端可传当前所在页面 / 当前课程
        if query:
            v = (query.get("view", [""])[0] or "").strip()
            if v:
                ctx["view"] = v
            cid = (query.get("course_id", [""])[0] or "").strip()
            if cid:
                t = C.TOPIC_INDEX.get(cid) or {}
                ctx["now_course"] = t.get("title") or cid
        return ctx

    def _companion_opening(self, uid, query=None):
        ctx = self._companion_gather(uid, query or {})
        hour = datetime.now().hour
        try:
            data = COMP.build_opening(ctx, hour)
        except Exception as e:
            self._send_json(500, {"error": "生成学伴开场白失败：%s" % e})
            return
        data["context"]["name"] = ctx.get("child")
        self._send_json(200, data)

    def _companion_chat(self, uid, body):
        message = (body.get("message") or "").strip()
        history = body.get("history") or []
        if message == "__opening__":
            message = ""
        if not message and not history:
            self._send_json(400, {"error": "消息不能为空"})
            return
        query = {}
        if body.get("view"):
            query["view"] = [str(body.get("view"))]
        cid = body.get("course_id")
        if cid:
            query["course_id"] = [str(cid)]
        ctx = self._companion_gather(uid, query)
        ctx["view"] = body.get("view") or ctx.get("view")
        # 本地知识引擎需要的上下文：当前课程 id / 讲到第几节 / 是否在等答案
        ctx["course_id"] = cid
        ctx["section_idx"] = body.get("section_idx") or 0
        if isinstance(body.get("quiz_state"), dict):
            ctx["quiz_state"] = body.get("quiz_state")
        ctx["quiz_index"] = body.get("quiz_index") or 0
        ctx["want_quiz"] = bool(body.get("want_quiz"))
        if cid:
            t = C.TOPIC_INDEX.get(cid) or {}
            ctx["now_course"] = t.get("title") or cid
        settings = get_settings(uid)
        course_ctx = C.course_context(cid) if cid else None
        msgs = COMP.build_companion_messages(ctx, history, message, course_context=course_ctx)
        api_key = (settings.get("api_key") or "").strip()
        mock_mode = settings.get("mock_mode", 1)
        if mock_mode or not api_key:
            raw = COMP.mock_companion(ctx, message)
        else:
            raw = call_llm(msgs, resolve_llm_settings(settings, "teaching"), "zh")
        data = COMP.parse_companion_reply(raw, ctx)
        data["emotion_label"] = EMOTION_LABEL.get(data.get("emotion"), "平和")
        data["context"] = {
            "child": ctx.get("child"),
            "today_min": int(ctx.get("today_sec") or 0) // 60,
            "daily_max": int(ctx.get("daily_max") or 30),
            "streak": int(ctx.get("streak") or 0),
            "stars": int(ctx.get("stars") or 0),
        }
        data["lang"] = "zh-CN"
        self._send_json(200, data)

    def _study_resume_save(self, uid, body):
        data = body.get("resume")
        if not isinstance(data, dict):
            data = body if isinstance(body, dict) else {}
        if not data:
            self._send_json(400, {"error": "resume 不能为空"})
            return
        now = now_iso()
        conn = db()
        conn.execute(
            "INSERT INTO study_progress(user_id, data_json, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET data_json=excluded.data_json, updated_at=excluded.updated_at",
            (uid, json.dumps(data, ensure_ascii=False), now))
        conn.commit()
        conn.close()
        self._send_json(200, {"ok": True, "updated_at": now})



# ---------------- 学习进度（按账号隔离，跨设备恢复） ----------------
# 表 study_records：每个账号每个知识点一条，status 0未学/1已学/2已掌握。
# 前端 al_ss_progress 原为纯 localStorage —— 换设备/清缓存/切孩子就丢，
# 这里做服务端主库，本地只当离线缓存。
def _ensure_study_records_table(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS study_records ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "course_id TEXT NOT NULL, "
        "status INTEGER NOT NULL DEFAULT 0, "
        "updated_at TEXT, "
        "UNIQUE(user_id, course_id))"
    )
    conn.commit()


def _study_records_get(user_id):
    conn = db()
    _ensure_study_records_table(conn)
    rows = conn.execute("SELECT course_id, status, updated_at FROM study_records WHERE user_id=?",
                         (user_id,)).fetchall()
    conn.close()
    out = {}
    for r in rows:
        out[r["course_id"]] = {"status": int(r["status"] or 0), "ts": r["updated_at"]}
    return out


def _study_records_merge(user_id, items):
    """items: {cid: {status, ts}} —— 只增不减（status 取大），ts 仅在状态提升时更新。"""
    conn = db()
    _ensure_study_records_table(conn)
    now = now_iso()
    changed = 0
    for cid, rec in (items or {}).items():
        if not cid or not isinstance(rec, dict):
            continue
        try:
            status = int(rec.get("status") or 0)
        except Exception:
            status = 0
        if status <= 0:
            continue
        old = conn.execute("SELECT status FROM study_records WHERE user_id=? AND course_id=?",
                           (user_id, cid)).fetchone()
        if old and int(old["status"] or 0) >= status:
            continue
        conn.execute(
            "INSERT INTO study_records (user_id, course_id, status, updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id, course_id) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at",
            (user_id, cid, status, now))
        changed += 1
    conn.commit()
    conn.close()
    return changed

# ---------------- 学习机模式：推荐下一课（模块级，供多接口复用） ----------------
def _recommend_next_course(mastered_ids):
    """遍历课程，返回第一个尚未掌握的知识点（与 /api/plan/next 同一口径）。"""
    mastered_ids = mastered_ids or set()
    for stage in C.CURRICULUM:
        for subj in stage.get("subjects", []):
            for grade in subj.get("grades", []):
                for topic in grade.get("topics", []):
                    cid = topic.get("id", "")
                    if cid and cid not in mastered_ids:
                        return {
                            "course_id": cid,
                            "title": topic.get("title", cid),
                            "subject": subj.get("name", ""),
                            "grade": grade.get("grade", ""),
                            "stage": stage.get("stage", ""),
                            "status": "new",
                        }
    return None


# ---------------- 精准学：模块级辅助（出题） ----------------
def _color(level):
    if level >= 4:
        return "green"
    if level >= 2:
        return "yellow"
    if level == 1:
        return "red"
    return "gray"


def _guess_mistake_category(stem, user_answer, correct_answer, options=None):
    """简易错题归因：根据题干和答案特征判断错误类型"""
    stem = str(stem or "")
    ua = str(user_answer or "").strip()
    ca = str(correct_answer or "").strip()
    # 计算类题目（含数字、公式）且答案是数值
    if any(k in stem for k in ["计算", "等于", "值为", "多少", "求解", "结果"]) and ca.replace(".", "").replace("-", "").isdigit():
        try:
            if ua and ua.replace(".", "").replace("-", "").isdigit():
                diff = abs(float(ua) - float(ca))
                if diff / max(abs(float(ca)), 0.1) < 0.3:
                    return "计算错误"  # 数值接近但算错
        except Exception:
            pass
        return "思路错误"
    # 概念题：选了其他选项但选项都是相关概念 → 概念混淆
    if options and isinstance(options, list) and len(options) >= 3:
        return "概念混淆"
    # 含"不包括""不属于""错误的是"等否定词容易审题不清
    if any(k in stem for k in ["不包括", "不属于", "错误的是", "不正确", "除外"]):
        return "审题不清"
    # 空白或完全不沾边 → 思路错误
    if not ua or ua in ["不知道", "不会", ""]:
        return "思路错误"
    return "概念混淆"  # 默认


def _first_review_date():
    """艾宾浩斯第一次复习时间：1天后"""
    from datetime import timedelta
    return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(timespec="seconds")


def mock_diagnose_q(t):
    subs = t.get("sub") or []
    if subs:
        stem = f"关于「{t['title']}」，以下哪一项属于这个知识点的内容？"
        opts = list(subs[:3])
        while len(opts) < 4:
            opts.append("以上都不是")
        answer = 0
    else:
        stem = f"关于「{t['title']}」，下列说法正确的是？"
        opts = ["需要认真学习和练习", "考试肯定不考", "可以完全忽略", "以上都不对"]
        answer = 0
    return {"qid": "q_" + t["id"], "topic_id": t["id"], "topic_title": t["title"],
            "stem": stem, "options": opts, "answer": answer}


def ai_diagnose_questions(topics, settings):
    items = "\n".join(
        f"- 知识点id：{t['id']} | 名称：{t['title']} | 核心内容：{('、'.join(t.get('sub', [])) or '见教材')}"
        for t in topics)
    sysmsg = ("你是出题老师，擅长出贴合学段水平的诊断选择题。请为下面列出的【每一个】知识点出 1 道单选题（4 选 1），"
              "用于快速判断学生是否掌握该知识点。题目要具体、有干扰项，不要出送分题，也不要出超纲题。\n\n"
              "重要：题干和选项中的数学公式必须用 LaTeX 格式写在 $...$ 内（如 $\\frac{3}{4}$、$x^2$、$\\sqrt{2}$），"
              "这样前端才能正确渲染为可视化公式让学生看懂。")
    prompt = (
        "下面是若干知识点，请为每个知识点出 1 道选择题。\n" + items + "\n\n"
        "要求：\n"
        "1) 每题 4 个选项，只有 1 个正确答案；\n"
        "2) 选项要有区分度（不能一眼看出答案，也不能明显胡编）；\n"
        "3) answer 为正确选项的序号（0-3 整数）；\n"
        "4) **数学公式必须用 $...$ 包裹**（例如分数写 $\\frac{a}{b}$，乘方写 $x^2$，根号写 $\\sqrt{n}$）。\n\n"
        "只输出一个 JSON 数组，不要 markdown 代码块，形如：\n"
        '[{"topic_id":"知识点id","stem":"题干","options":["A","B","C","D"],"answer":0}, ...]\n'
        "topic_id 必须严格使用我给出的知识点 id。"
    )
    try:
        raw = call_llm([{"role": "system", "content": sysmsg},
                        {"role": "user", "content": prompt}], settings, "zh")
        data = parse_llm_response(raw)
        if not isinstance(data, list):
            data = []
        idmap = {t["id"]: t for t in topics}
        out = []
        for q in data:
            tid = q.get("topic_id")
            if tid not in idmap:
                continue
            opts = q.get("options") or []
            if len(opts) < 2:
                continue
            try:
                ans = int(q.get("answer", 0))
            except Exception:
                ans = 0
            if ans < 0 or ans >= len(opts):
                ans = 0
            out.append({"qid": "q_" + tid, "topic_id": tid,
                        "topic_title": idmap[tid]["title"],
                        "stem": str(q.get("stem") or ""), "options": [str(o) for o in opts],
                        "answer": ans})
        if out:
            return out
    except Exception:
        pass
    return [mock_diagnose_q(t) for t in topics]


def mock_practice_q(topic, tier, idx=0, _seen_stems=None):
    """分层练习出题（演示模式）。
    核心策略：复用已修复的高质量出题引擎（_subject_quiz / mock_test_q / 题库），
    枚举不同子点 + 引擎内部去重，确保 5 道题不重复。
    tier: 基础/提升/拓展 → 控制难度提示。
    idx: 题目序号（0~4），首选子点偏移。
    _seen_stems: 已用题干集合（由调用方传入做跨题目去重）。
    """
    course_id = topic.get("id") or ""
    title = topic.get("title", "")
    subject = topic.get("subject", "")
    subs = topic.get("sub") or [title]
    n_subs = len(subs)

    # ── 核心路径：按 idx 偏移优先尝试对应子点，若引擎产出与已见题干重复，
    #    则依次尝试剩余子点（最多遍历一轮），确保不重复 ──
    tried = set()
    base = idx % max(n_subs, 1)
    for attempt in range(n_subs):
        sub_idx = (base + attempt) % n_subs
        if sub_idx in tried:
            continue
        tried.add(sub_idx)
        q = mock_test_q(topic, sub_idx, used=None, course_id=course_id)
        if not q or not q.get("stem"):
            continue
        stem = q["stem"].strip()
        # 跨题目去重检查
        if _seen_stems and stem in _seen_stems:
            continue
        # 加上难度标签到解释里
        existing_exp = q.get("explanation", "")
        if existing_exp and not existing_exp.startswith(f"[{tier}]"):
            q["explanation"] = f"[{tier}] " + existing_exp
        return q

    # 所有子点都试过了仍全部撞题 → 用 warn 路径或概念路径补一道不同的
    # 尝试用 _honest_last（它按学科产题且依赖子点名变化）
    for attempt in range(n_subs):
        sub_idx = (base + attempt) % n_subs
        sub_name = subs[sub_idx]
        from server import _honest_last
        q = _honest_last(subject, sub_name, title)
        if q and q.get("stem"):
            stem = q["stem"].strip()
            if _seen_stems and stem in _seen_stems:
                continue
            existing_exp = q.get("explanation", "")
            if existing_exp and not existing_exp.startswith(f"[{tier}]"):
                q["explanation"] = f"[{tier}] " + existing_exp
            return q

    # ── 终极兜底 ──
    return {
        "stem": f"请结合「{title}」的「{subs[idx % n_subs]}」做练习：理解核心概念后完成教材习题。",
        "options": ["理解概念并独立完成练习", "只看答案不思考也能学会",
                   "考前突击背一遍就行", "可以跳过不学"],
        "answer": 0,
        "explanation": f"「{title}」是重要知识点，建议认真学。"
    }


def _build_topic_variants(topic, tier, subs, base_idx=0):
    """根据学科特征，为没有种子/Ollama数据的知识点构建有技术含量的变体题池。
    返回 question_dict 列表（至少返回 5 个变体）。
    """
    title = topic.get("title", "")
    subject = topic.get("subject", "")
    pool = []
    _calc_subjects = {"物理", "化学", "生物", "地理", "数学"}

    # 数学类：构造具体数值计算/推理题
    if subject == "数学":
        num_pool = [3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 24, 30, 36, 60, 120, 180, 360]
        n1 = num_pool[base_idx % len(num_pool)]
        n2 = num_pool[(base_idx + 3) % len(num_pool)]
        n3 = num_pool[(base_idx + 7) % len(num_pool)]

        pool.append({
            "stem": f"关于「{title}」，下列说法或计算正确的是？",
            "options": [
                f"相关公式/定理涉及数值 {n1}×{n2}={n1*n2}",
                f"该知识点的典型应用中常出现 {n3}° 的角度",
                f"在考试中此内容的分值通常不超过 {n1%5+2} 分",
                f"以上说法均无法从给定信息中确认"
            ], "answer": 0,
            "explanation": f"需结合「{title}」的具体定义和公式进行判断。"
        })
        pool.append({
            "stem": f"【{tier}】若将「{title}」的知识应用到实际问题中，关键步骤是？",
            "options": [
                "识别问题所涉及的已知条件和求解目标，建立数学模型",
                "直接套用公式而不考虑适用条件",
                "记住所有可能的答案选项即可",
                "先猜测答案再反推条件"
            ], "answer": 0,
            "explanation": "数学应用的核心是建模：从实际情境中抽象出数学关系。"
        })

    # 物理类：构造含单位/公式的情景题
    elif subject == "物理":
        units = [("m/s", "速度"), ("N", "力"), ("J", "能量"), ("Pa", "压强"),
                 ("W", "功率"), ("Ω", "电阻"), ("V", "电压"), ("A", "电流")]
        ui = base_idx % len(units)
        u_val = [10, 20, 50, 100, 200][(base_idx * 3) % 5]
        pool.append({
            "stem": f"【{tier}】在「{title}」的相关问题中，{units[ui][1]}的常用单位是？",
            "options": [
                f"{units[ui][0]}（国际单位制基本/导出单位）",
                "kg（质量的单位）",
                "s（时间的单位）",
                "mol（物质的量的单位）"
            ], "answer": 0,
            "explanation": f"{units[ui][1]}的国际单位是 {units[ui][0]}。"
        })
        pool.append({
            "stem": f"关于「{title}」，下列实验或现象描述正确的是？",
            "options": [
                "实验过程应控制变量，每次只改变一个因素",
                "实验结果与理论值不一致时直接修改理论值",
                "只需一次测量就能得到准确的结论",
                "实验器材的选择对结果没有影响"
            ], "answer": 0,
            "explanation": "科学实验的基本原则：控制变量法、多次测量取平均值。"
        })

    # 化学类：构造物质/反应相关题
    elif subject == "化学":
        substances = ["H₂O", "O₂", "CO₂", "HCl", "NaOH", "Fe₂O₃", "CuSO₄", "CaCO₃"]
        si = base_idx % len(substances)
        sub_name = substances[si]
        pool.append({
            "stem": f"【{tier}】关于 {sub_name} 在「{title}」中的相关性质，正确的是？",
            "options": [
                f"{sub_name} 的性质和应用需通过实验观察和化学方程式来理解",
                f"{sub_name} 在所有化学反应中都充当氧化剂",
                f"{sub_name} 可以与任意物质发生反应",
                f"{sub_name} 只存在于实验室中，自然界不存在"
            ], "answer": 0,
            "explanation": f"学习{sub_name}要掌握其物理性质、化学性质及制法和用途。"
        })

    # 英语/语文/其他文科
    else:
        if subs:
            for i, s in enumerate(subs):
                si = (base_idx + i) % len(subs)
                s_name = subs[si]
                pool.append({
                    "stem": f"【{tier}】关于「{s_name}」，下列理解正确的是？",
                    "options": [
                        f"需要掌握其核心内容和关键细节，能灵活运用",
                        "只需要记住标题就可以",
                        "与其他知识点完全无关",
                        "考试时不会单独考查"
                    ], "answer": 0,
                    "explanation": f"「{s_name}」是「{title}」的重要组成部分。"
                })

    # 如果还没凑够5个，用通用变体补足
    generic_variants = [
        {
            "stem": f"【{tier}】学习「{title}」时，最重要的方法是？",
            "options": ["理解原理后多做练习巩固", "只背结论不求甚解",
                       "考前突击看一眼就行", "抄写例题就算学会"],
            "answer": 0, "explanation": "主动理解+练习是学好任何知识点的关键方法。"
        },
        {
            "stem": f"【{tier}】下列关于「{title}」的说法中，错误的是？",
            "options": ["它是本阶段的基础内容之一", "需要深入理解和反复练习",
                       "前后知识有内在联系", "学了之后永远不会再忘记"],
            "answer": 3, "explanation": "知识需要持续复习才能长期保持。"
        },
        {
            "stem": f"【{tier}】若想真正掌握「{title}」，应该？",
            "options": ["弄懂原理并独立完成练习题", "只看答案不理解过程",
                       "死记硬背所有公式和结论", "完全依赖老师讲解不思考"],
            "answer": 0, "explanation": "真正的掌握来自主动思考和独立练习。"
        },
        {
            "stem": f"【{tier}」「{title}」在实际生活/考试中的应用包括？",
            "options": ["解决具体问题、分析综合情境", "仅用于填空题",
                       "只在课堂上有意义", "与后续学习毫无关系"],
            "answer": 0, "explanation": "知识的价值在于应用和迁移。"
        },
        {
            "stem": f"【{tier}】复习「{title}」的高效策略是？",
            "options": ["先梳理知识框架再针对性做题", "从头到尾死记教材",
                       "只做难题忽略基础", "考前一天突击全部内容"],
            "answer": 0, "explanation": "系统梳理+针对性练习是最有效的复习方式。"
        },
    ]
    pool.extend(generic_variants)

    return pool[:10] if pool else None


def ai_practice_q(topic, tier, settings):
    tier_desc = {
        "基础": "直接应用的基本概念题，步骤少",
        "提升": "需要变式或综合两步以上的题",
        "拓展": "迁移到新情境或开放探究题",
    }.get(tier, "综合题")
    ctx = C.course_context(topic["id"])
    sysmsg = ("你是出题老师，针对单一知识点出练习题，并按要求给出答案与解析。\n"
              "重要：数学公式必须用 LaTeX 格式写在 $...$ 内（如 $\\frac{3}{4}$、$x^2$、$\\sqrt{2}$），前端会自动渲染为可视化公式。")
    prompt = (
        f"知识点：{topic['title']}\n背景：{ctx}\n\n"
        f"请出 5 道【{tier}】层级的练习题。{tier_desc}。\n"
        "要求：\n"
        "1) 每道题都是单选题（4 个选项 A/B/C/D，1 个正确答案），贴近该年级水平；\n"
        "2) 题目之间难度递进、覆盖不同角度（不要5道都考同一个点）；\n"
        "3) answer 为正确选项序号(0-3)；\n"
        "4) explanation 为正确选项的解题思路（2-4 句）；\n"
        "5) **题干、选项和解析中的数学公式必须用 $...$ 包裹**（分数 $\\frac{a}{b}$，乘方 $x^n$）。\n\n"
        "只输出一个 JSON 数组（5个对象），不要 markdown 代码块，形如：\n"
        '[{"stem":"题干","options":["A","B","C","D"],"answer":0,"explanation":"..."}, ...]'
    )
    try:
        raw = call_llm([{"role": "system", "content": sysmsg},
                        {"role": "user", "content": prompt}], settings, "zh")
        data = parse_llm_response(raw)
        if not isinstance(data, list):
            data = [data]
        out = []
        for obj in data:
            opts = obj.get("options") or []
            if len(opts) < 2:
                continue
            ans = int(obj.get("answer", 0))
            if ans < 0 or ans >= len(opts):
                ans = 0
            out.append({"stem": str(obj.get("stem") or ""), "options": [str(o) for o in opts],
                       "answer": ans, "explanation": str(obj.get("explanation") or "")})
        if out:
            return out
    except Exception:
        pass
    # mock 兜底也返回5道
    result = []
    for i in range(5):
        result.append(mock_practice_q(topic, tier))
    return result


def _test_plan(topic):
    """自测题出题计划：覆盖知识点的【全部核心子内容】即可——每个子内容至少出 1 题，
    题量就等于子内容数量（封顶 20 道），不强制凑量；子内容少（哪怕只有 2 个）就只出 2 题，
    保证该知识点的全部内容都能被测试到。返回 {n: 题目总数, per: 每子点题数, m: 子点数}。"""
    subs = topic.get("sub") or []
    m = len(subs)
    if m == 0:
        # 异常边界：没有子内容时兜底出 5 道（基于标题），避免无题可做
        return {"n": 5, "per": 5, "m": 0}
    n = min(m, 20)   # 每个子内容 1 题，封顶 20
    return {"n": n, "per": 1, "m": m}


def _build_content_hint(topic, course_id=None):
    """拼接该知识点每个子点的真实讲解内容（定义/公式/例题），作为出题素材，
    让生成的题目贴合知识点本身、有深度，而不是空泛轮转子点名称。"""
    subs = topic.get("sub") or []
    title = topic.get("title", "")
    subject = topic.get("subject", "")
    if not subs:
        return f"知识点：{title}\n（该知识点暂无细分内容，请围绕其基本概念、计算方法与易错点出题）"
    parts = []
    for s in subs:
        try:
            c = C._explain_sub(title, subject, s, course_id=course_id or topic.get("id"))
        except Exception:
            c = ""
        c = (c or "").strip()
        if c:
            c = c[:900]
            parts.append(f"【子内容：{s}】\n{c}")
    header = (f"知识点：{title}（共 {len(subs)} 个核心子内容）\n"
              f"下面是该知识点每个子内容的详细讲解（含公式与例题），请严格依据这些内容出题，"
              f"保证题目贴合知识点、有深度：\n")
    return header + "\n\n".join(parts)


def _safe_eval(s):
    """安全地求值纯数字 LaTeX 算式（仅整数/小数运算），失败返回 None。"""
    try:
        s = (s.replace("$", "").replace("\\times", "*").replace("×", "*")
             .replace("\\div", "/").replace("÷", "/"))
        s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"((\1)/(\2))", s).replace(" ", "")
        return eval(s, {"__builtins__": {}}, {})
    except Exception:
        return None


def _mock_extract(text):
    """从子点讲解里提取可用于出题的素材。返回 (calc_expr, calc_ans, terms, warn)。
    只接受【经过验证的整数/小数运算】（算式求值 == 文中结果），保证计算/填空题答案可靠；
    分数、含字母变量等不可靠的情形不采用，交由填空/选择分支处理。"""
    calc_expr = calc_ans = None
    frags = re.findall(r"\$([^$]+)\$", text)
    for f in frags:
        if "=" in f:
            # 1) 去掉 \text{...}（单位注释如 m^2），避免其中的 "2" 被误当成数字
            clean = re.sub(r"\\text\{[^}]*\}", "", f)
            # 2) 以 "=" 切分：结果 = 最后一个分段的首个数字；算式 = 其余部分
            parts = clean.split("=")
            if len(parts) < 2:
                continue
            res_part = parts[-1]
            res_nums = re.findall(r"[0-9]+(?:\.[0-9]+)?", res_part)
            if not res_nums:
                continue
            ans_val = float(res_nums[0])
            # 3) 算式 = 去掉最后一个 "=" 及其结果后的部分，再去掉开头的变量名（如 "S ="）
            expr = "=".join(parts[:-1]).strip()
            expr = re.sub(r"^[A-Za-z_]*\s*=\s*", "", expr).strip()
            # 支持 \frac{a}{b} → (a/b)，并允许括号；仍只接受纯数字运算，保证答案可靠
            expr_eval = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1/\2)", expr)
            if not re.fullmatch(r"[0-9\s\\times×÷÷\.\*\+\-/\(\)]+", expr_eval):
                continue
            # 必须含运算（×÷+- 或分数），否则如 "$5 = \frac{5}{1}$"（整数5看作分母1的分数）
            # 这类「等价表示」会被误当成算式，生成「计算 5 的结果是 5」之类无意义题
            if not re.search(r"[\\times×÷÷\*\+\-/]", expr_eval) and "\\frac" not in expr_eval:
                continue
            ev = _safe_eval(expr_eval)
            if ev is None or abs(ev - ans_val) > 1e-6:
                continue
            calc_expr = expr
            calc_ans = res_nums[0]
            break
    terms = []
    for _m in re.findall(r"\*\*([^*]{1,16})\*\*", text):
        s = _m.strip()
        # 过滤装饰性/结构性标记：含 emoji、过短、或纯标点/空白
        if len(s) < 2:
            continue
        if re.search(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2190-\u21FF\u2300-\u23FF]", s):
            continue
        if re.fullmatch(r"[\s\W_]+", s):
            continue
        # 跳过纯结构性词（例题/注意/推导等）
        if s in ("例题", "注意", "关键", "推导", "答", "解", "含义", "小结", "提示"):
            continue
        terms.append(s)
    warn = ""
    mw = re.search(r"(⚠️|注意|关键)[^。\n]{4,40}", text)
    if mw:
        warn = mw.group(0).strip()
    return calc_expr, calc_ans, terms, warn


def _mock_facts(text):
    """从讲解提取进率/定义等式，生成全部换算方向（含反向），用于换算填空/选择，
    避免同一知识点内题目重复。返回 [(label, num, unit)]，如
    ('1 km²','100','公顷')、('100 公顷','1','km²') 等互逆关系均给出。"""
    facts = []
    seen = set()
    for f in re.findall(r"\$([^$]+)\$", text):
        disp = re.sub(r"\\text\{([^}]*)\}", r"\1", f).replace("^2", "²").replace("^{2}", "²").replace("{}", "")
        segs = [s.strip() for s in re.split(r"=", disp) if s.strip()]
        parsed = []
        for s in segs:
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([一-龥A-Za-z²%]*)", s)
            if not m:
                continue
            num = m.group(1)
            unit = m.group(2).strip()
            label = s[:m.start()].strip()
            if not label or "\\" in label or "{" in label or "}" in label:
                # 退化情形：左段即「数值+单位」，标签取整个匹配（数值+单位，勿重复追加单位）
                lbl2 = s[m.start():m.end()].strip()
                if not lbl2 or "\\" in lbl2 or "{" in lbl2 or "}" in lbl2:
                    continue
                label = lbl2
            parsed.append((label, num, unit))
        # 任意两段之间生成换算关系（方向不同即不同题目）
        for i in range(len(parsed)):
            for j in range(len(parsed)):
                if i == j:
                    continue
                li, _, ui = parsed[i]
                _, nj, uj = parsed[j]
                if ui == uj:
                    continue
                key = (li, nj, uj)
                if key in seen:
                    continue
                seen.add(key)
                facts.append((li, nj, uj))
    return facts


def _num_choices(base):
    """生成 4 个不重复、非负、贴近的数值选项（含正确答案 base）。"""
    try:
        base = float(base)
    except Exception:
        return [base]
    cands = {base}
    for off in (1, -1, round(base * 0.1 + 1e-9, 4), round(base * 10 + 1e-9, 4)):
        cand = round(base + off, 4)
        if cand >= 0 and abs(cand - base) > 1e-9:
            cands.add(cand)
    opts = list(cands)
    k = 2
    while len(opts) < 4:
        c = round(base + k, 4)
        if c not in opts:
            opts.append(c)
        k += 1
        if k > 50:
            break
    return opts[:4]


def _fmt_num(o):
    f = float(o)
    return str(int(f)) if f.is_integer() else str(f)


def _concept_stem(text, sub, title):
    """从子点内容提取一句核心结论，构造概念辨析选择题（去除同义反复送分题）。"""
    body = re.sub(r"【[^】]*】", "", text)
    body = re.sub(r"\*\*", "", body)
    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith(("⚠️", "💡", "📝", "解", "答", "例")):
            continue
        line = re.sub(r"^[\s\-\.\d①②③④⑤⑥⑦⑧⑨•]+", "", line).strip()
        # 剥离生成内容可能带的前缀「对于「标题」中的「子点」：」，该前缀会让事实变冗余、触发泛化误判
        _prefix = f"对于「{title}」中的「{sub}」："
        if line.startswith(_prefix):
            line = line[len(_prefix):].strip()
        if not line:
            continue
        # 质量过滤：剔除空泛的"学习建议/通用劝学"与噪声（如"（最重要之一！"）
        _bad = ("数学讲究严谨", "学习建议", "弄懂", "比背结论", "（最", "！", "请",
                "例如", "如下", "小结", "核心是", "最重要的是", "之一！", "核心要点",
                "需要理解", "认真理解", "结合例题", "及时练习",
                "核心方法", "观察、提问", "科学课", "学习方法", "勤于", "善于观察",
                "一般来说", "都应该", "要善于", "建议从", "我们都", "关键在于")
        if any(b in line for b in _bad):
            continue
        if not (8 <= len(line) <= 42):
            continue
        # 必须是"内容性"结论：含数字/公式，或含判断词/几何属性词（是/指/叫做/等于/公式/：/即/
        # 周长/面积/平行/垂直/相等/直角/锐角/钝角/进率/单位/特征/性质/分类/定义/度量/线段/端点/相对/位置/方向/数对…）
        if not re.search(r"[0-9=×÷²√°]|是|指|叫做|等于|公式|：|即|周长|面积|半径|直径|进率|单位|体积|棱长|平行|垂直|相等|对边|对角|直角|锐角|钝角|平角|周角|特征|性质|分类|定义|度量|射线|线段|端点|互|对称轴|轴对称|相对|位置|方向|数对|只有|快慢|比值", line):
            continue
        if len(line) >= 6:
            correct = line
            # 干扰项：基于正确内容生成合理但错误的变体（杜绝‘反面表述/混淆概念’等废话）
            if "是" in line:
                wrong1 = line.replace("是", "不是", 1)
            elif "等于" in line:
                wrong1 = line.replace("等于", "不等于", 1)
            elif "：" in line:
                wrong1 = line.split("：", 1)[0] + "：与上述内容恰好相反"
            else:
                wrong1 = line + "（这一说法并不成立）"
            # 第二个错误变体：把句中的数字/量做最小改动
            nums = re.findall(r"\d+(?:\.\d+)?", line)
            if nums:
                n0 = nums[0]
                try:
                    wn = str(float(n0) + 1) if ("." in n0) else str(int(n0) + 1)
                except Exception:
                    wn = n0 + "1"
                wrong2 = line.replace(n0, wn, 1)
            else:
                wrong2 = line + "（适用范围与相邻概念相同，无需区分）"
            # 第三个错误变体：用相邻子点替换主体，制造‘张冠李戴’
            sibs = [x for x in (C.TOPIC_INDEX.get(_cur_tid, {}).get("sub") or []) if x and x != sub]
            if sibs:
                wrong3 = f"上述结论其实属于「{sibs[0]}」，而非「{sub}」"
            else:
                wrong3 = line + "（只在极特殊的情形下才成立）"
            opts = [correct, wrong1, wrong2, wrong3]
            # 去重
            seen = set(); uniq = []
            for o in opts:
                if o not in seen:
                    seen.add(o); uniq.append(o)
            opts = uniq
            while len(opts) < 4:
                opts.append(line + f"（其第{len(opts)}种表述不成立）")
            random.shuffle(opts)
            answer = opts.index(correct)
            return {"type": "choice",
                    "stem": f"「{sub}」：下列说法正确的是？\n（核心要点：{line}）",
                    "options": opts, "answer": answer,
                    "explanation": f"「{sub}」的核心要点：{line}"}
    return None


def _iter_fact_lines(text):
    """从讲解抽取可作题干的具体事实句（含数字/公式/定义/事实词），过滤空泛劝学句。"""
    body = re.sub(r"【[^】]*】", "", text or "")
    body = re.sub(r"\*\*", "", body)
    out = []
    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith(("⚠️", "💡", "📝", "解", "答", "例")):
            continue
        line = re.sub(r"^[\s\-\.\d①②③④⑤⑥⑦⑧⑨•]+", "", line).strip()
        if not (6 <= len(line) <= 56):
            continue
        if any(b in line for b in ("学习建议", "弄懂", "核心是", "最重要的是", "学习方法",
                                    "一般来说", "我们都", "关键在于", "要善于", "请", "只需",
                                    "只要", "不需要", "可以跳过", "凭直觉", "了解大概",
                                    "学习历史要用", "时间线思维", "学习技巧", "以史为鉴")):
            continue
        if not re.search(r"[0-9=×÷²√°]|是|指|叫做|称为|等于|公式|：|即|因为|所以|位于|作者|产生|用于|属于|由…组成|由...组成|又称|主要|例如|比如|发生在|建立于|发明|发现|发明于|发现于", line):
            continue
        out.append(line)
    return out


def _content_question(text, sub, title, idx):
    """终极兜底：从真实讲解文本挖掘一条具体事实，构造填空/选择题（具体、无废话）。
    抽不到则返回 None，交给 _honest_last。"""
    lines = _iter_fact_lines(text)
    if not lines:
        return None
    line = lines[idx % len(lines)]
    # 优先填空：挖空「X 是/叫/称/指 Y」中的 Y
    m = re.search(r"([一-龥A-Za-z0-9_（）()]{2,14})\s*(?:是|叫|叫做|称为|指|即)\s*([一-龥A-Za-z0-9_，、（）()]{1,14})\s*[。，；]?$",
                  line)
    if m and 1 <= len(m.group(2).rstrip("，。；")) <= 12:
        term, val = m.group(1), m.group(2).rstrip("，。；")
        if val not in ("它", "其", "该", "错误的", "正确的", "两者", "其一"):
            return _fq(f"「{sub}」：{term} 是 ______ 。", val, f"{term}是{val}。")
    # 选择：正确项=原事实句；干扰项=对句中数字/关键词做最小改动或反说
    nums = re.findall(r"\d+(?:\.\d+)?", line)
    opts = [f"「{sub}」：{line}"]
    if nums:
        n0 = nums[0]
        try:
            wn = str(float(n0) + 1) if ("." in n0) else str(int(n0) + 1)
        except Exception:
            wn = n0 + "1"
        w1 = line.replace(n0, wn, 1)
        if w1 != line:
            opts.append(f"「{sub}」：{w1}")
    if "是" in line:
        opts.append(f"「{sub}」：{line.replace('是', '不是', 1)}")
    else:
        opts.append(f"「{sub}」：{line}（这一说法并不成立）")
    opts.append(f"「{sub}」：上述说法恰好相反才正确")
    seen = set()
    uniq = []
    for o in opts:
        if o not in seen:
            seen.add(o)
            uniq.append(o)
    while len(uniq) < 4:
        uniq.append(f"「{sub}」：该说法只在极特殊情形下才成立")
    opts = uniq[:4]
    random.shuffle(opts)
    ans = opts.index(f"「{sub}」：{line}")
    return _cq(f"关于「{sub}」，下列说法正确的是？", opts, ans, f"正确表述：{line}")


def _honest_last(subject, sub, title):
    """仍无具体素材时的兜底题——按学科产出有信息量、零废话的题：
    语文/英语考体裁·人物·词汇常识；其余科目以‘本课相邻子点’作为合理干扰，
    避免‘最不重要/完全不同学科/只记名称’类废话。"""
    if subject in ("语文", "道德与法治", "思想政治"):
        # 语文：考文章体裁与基本常识（低幼课文也能考体裁、人物、主题）
        if any(k in sub for k in ("诗", "词", "歌", "谣", "童谣")):
            genre = "诗歌/韵文"
        elif any(k in sub for k in ("故事", "神话", "寓言", "传说")):
            genre = "寓言/神话故事"
        elif any(k in sub for k in ("散文", "课文", "写景", "游记")):
            genre = "写景/叙事散文"
        else:
            genre = "记叙文（记人叙事）"
        correct = f"「{sub}」是一篇{genre}，学习时要抓住人物、情节与表达的情感"
        opts = [correct,
                f"「{sub}」属于说明文，重点是说明事物的特征与原理",
                f"「{sub}」是一则应用文（如通知、书信格式）",
                f"「{sub}」是议论文，重点是提出观点并论证"]
        random.shuffle(opts)
        ans = opts.index(correct)
        return _cq(f"关于课文「{sub}」的体裁与阅读要求，下列说法正确的是？", opts, ans,
                   f"「{sub}」属{genre}；阅读要理解内容、体会情感、学习表达方法。")
    if subject in ("英语", "English"):
        # 英语：考词汇/词性常识（通用但不废话）
        correct = f"学习「{sub}」时，要结合例句掌握它的词义、词性与常用搭配"
        opts = [correct,
                f"「{sub}」只用在书面语，口语中完全不能说",
                f"「{sub}」的意思与拼写完全无关，只能死记",
                f"「{sub}」在任何句型中形式都不变"]
        random.shuffle(opts)
        ans = opts.index(correct)
        return _cq(f"关于英语「{sub}」的学习要点，下列说法正确的是？", opts, ans,
                   f"「{sub}」要通过语境、搭配和例句来掌握，注意词性与句法变化。")
    # 其余科目：以‘本课相邻子点(非本子点)’作为合理干扰，考查归属
    sibs = [x for x in (C.TOPIC_INDEX.get(_cur_tid, {}).get("sub") or []) if x and x != sub]
    if len(sibs) >= 2:
        d1, d2 = sibs[0], sibs[1]
    elif sibs:
        d1 = sibs[0]
        d2 = title
    else:
        d1 = title
        d2 = sub
    correct = f"「{sub}」与「{d1}」「{d2}」同属「{title}」这一主题，应联系起来理解"
    opts = [correct,
            f"「{sub}」与「{title}」毫无关系，可以单独跳过去学",
            f"先掌握「{d1}」即可，完全不需要了解「{sub}」",
            f"「{sub}」比「{title}」里的其他内容都难得多，应最后再学"]
    random.shuffle(opts)
    ans = opts.index(correct)
    return _cq(f"关于「{sub}」（{subject}）在「{title}」中的位置，下列说法正确的是？", opts, ans,
               f"「{sub}」是「{title}」的有机组成部分，与「{d1}」「{d2}」联系紧密。")


def _assemble_seed_questions(topic, course_id, n):
    """从内置种子题库中组卷（覆盖全子点、题型多样）；无种子数据时返回 None。
    优先级低于 Ollama 生成内容，高于 mock_test_q 兜底。"""
    seed = SB.get_seed_questions(course_id)
    if not seed:
        return None
    gsubs = seed.get("subs") or {}
    pools = []
    # 按知识点原始 sub 顺序排列题池
    topic_subs = topic.get("sub") or [topic.get("title", "")]
    for s in topic_subs:
        qs = gsubs.get(s, [])
        pools.append(list(qs))
    total = sum(len(p) for p in pools)
    if total == 0:
        return None
    want = min(n, total, 20)
    chosen, chosen_types = [], []
    for p in pools:
        if not p:
            continue
        pick = p[0]
        for cand in p:
            if cand.get("type") not in chosen_types:
                pick = cand
                break
        chosen.append(pick)
        chosen_types.append(pick.get("type"))
        p.remove(pick)
    while len(chosen) < want:
        added = False
        for p in pools:
            if p:
                chosen.append(p.pop(0))
                added = True
                break
        if not added:
            break
    return chosen[:want]


def _assemble_gen_questions(topic, course_id, n):
    """从 Ollama 生成的课件内容中组卷：保证每个子点至少 1 题（全覆盖），
    题量不足时再补充各子点第 2 题，并尽量让题型多样；无生成内容返回 None。"""
    gen = C.GEN_CONTENT.get(course_id)
    if not gen:
        return None
    gsubs = gen.get("subs") or []
    pools = [list(s.get("questions") or []) for s in gsubs]
    total = sum(len(p) for p in pools)
    if total == 0:
        return None

    # 文科科目：过滤掉不合适的题型（calc计算题不该出现在语文/英语等科目中）
    subj = topic.get("subject", "")
    _LIBERAL_ARTS = frozenset({"语文", "英语", "道德与法治", "思想政治", "历史", "地理",
                                "English", "Chinese", "Politics", "History", "Geography"})
    is_liberal = subj in _LIBERAL_ARTS
    if is_liberal:
        filtered_pools = []
        for p in pools:
            filtered_pools.append([q for q in p if q.get("type") != "calc"])
        pools = filtered_pools
        total = sum(len(p) for p in pools)
        if total == 0:
            return None

    want = min(n, total, 20)
    chosen, chosen_types = [], []
    # 每子点先取 1 题，保证全覆盖；优先选尚未出现过的题型以丰富题型
    for p in pools:
        if p:
            pick = p[0]
            for cand in p:
                if cand.get("type") not in chosen_types:
                    pick = cand
                    break
            chosen.append(pick)
            chosen_types.append(pick.get("type"))
            p.remove(pick)
    # 再补充至 want，优先补充各子点剩余题（题型多样由生成时保证）
    while len(chosen) < want:
        added = False
        for p in pools:
            if p:
                chosen.append(p.pop(0))
                added = True
                break
        if not added:
            break
    return chosen[:want]


def _cq(stem, options, answer, explanation):
    """构造选择题（choice）。options: 列表, answer: 正确项下标。"""
    return {"type": "choice", "stem": stem, "options": options,
            "answer": answer, "explanation": explanation}


def _fq(stem, answer, explanation):
    """构造填空/计算题（fill）。answer: 字符串答案。"""
    return {"type": "fill", "stem": stem, "answer": answer,
            "explanation": explanation}


def _clean_choice_question(q):
    """清洗选择题：检测并修复题干中内嵌的选项文字（统一出口）。

    LLM/Ollama 出题经常把 A/B/C/D 选项写进题干，导致前端显示「题干含选项+空壳按钮」。
    此函数在 _precision_test 出题出口统一拦截，无论题目来源（实时LLM/生成文件/种子/兜底）。

    支持的内嵌格式：
      A. xxx  B. xxx          （半角/全角点）
      (A) xxx  (B) xxx        （英文括号）
      （A）xxx （B）xxx       （中文括号）  ← 最常见
      [A] xxx  [B] xxx        （方括号）
    返回清洗后的 question dict（原地修改后返回，兼容 None 输入）。
    """
    if not q or q.get("type") != "choice":
        return q
    stem = (q.get("stem") or "").strip()
    opts = q.get("options") or []

    # 已有正常长选项且无内嵌标记 → 跳过
    has_embedded = bool(re.search(
        r'(?:^|[\s\n,；;，])([A-D])[(（.[．.\]]', stem))
    if len(opts) >= 2 and all(len(str(o).strip()) > 4 for o in opts) and not has_embedded:
        return q

    # ── 统一匹配所有内嵌选项标记 ──
    # 每个标记 = 字母(A-D) + 后缀(./)/]/）/）)
    marker_pattern = r'(?<!\w)([A-D])[.．.)\]）](?!\d)'
    opt_markers = list(re.finditer(marker_pattern, stem))

    # 如果点号模式没找到，尝试括号模式（中文/英文括号紧贴字母两侧）
    if len(opt_markers) < 2:
        paren_pattern = r'[(（]([A-D])[)）]'
        paren_matches = list(re.finditer(paren_pattern, stem))
        if len(paren_matches) >= 2:
            # 把括号匹配转换为统一的 marker 位置（用括号后面作为分隔点）
            opt_markers = paren_matches

    if len(opt_markers) < 2:
        return q  # 检测不到足够的内嵌选项标记 → 原样返回

    # ── 提取每个选项的文字内容 ──
    extracted = []
    for i, m in enumerate(opt_markers):
        # 当前标记结束位置 = 选项文字起始
        start_text = m.end()
        # 下一个标记开始位置 = 当前选项文字结束
        end_text = opt_markers[i + 1].start() if i + 1 < len(opt_markers) else len(stem)

        text = stem[start_text:end_text].strip()
        # 去掉末尾残留标点和空括号
        text = re.sub(r'\s*[（(][\s)）]*$', '', text).strip()
        text = text.rstrip('。，；？！!！）)〕】》')
        if text and len(text) > 1:  # 有效选项至少2个字符
            extracted.append(text)

    if len(extracted) < 2:
        return q  # 提取出的有效选项不够

    # ── 清洗题干：截取第一个标记之前的部分 ──
    first_pos = opt_markers[0].start()
    clean_stem = stem[:first_pos].strip()
    clean_stem = re.sub(r'[？?！!，,。.\s]+$', '', clean_stem).strip()
    if clean_stem and not clean_stem.endswith(('？', '?')):
        clean_stem += '（　　）'

    # ── 判断原有 options 是否为空壳并替换 ──
    shell_sets = {('a','b','c','d'), ('A','B','C','D')}
    opt_set = {o.strip().upper() for o in opts}
    is_shell = (len(opts) == len(extracted) and opt_set in shell_sets)

    if is_shell or not opts or all(len(str(o).strip()) <= 3 for o in opts):
        q["options"] = extracted

    q["stem"] = clean_stem

    # answer 如果是字母形式转为索引
    ans = q.get("answer", 0)
    if isinstance(ans, str) and len(ans) == 1 and ans.upper() in 'ABCD':
        idx = ord(ans.upper()) - ord('A')
        if 0 <= idx < len(extracted):
            q["answer"] = idx

    return q


def _clean_questions_all(qs):
    """批量清洗题列表中的选择题（拦截题干内嵌选项问题）。"""
    return [_clean_choice_question(q) for q in qs]


# ─────────────── 题目内容质量校验 + 去重层 ───────────────
# LLM（ai_test_qs）和 Ollama 生成内容经常产出垃圾题目：
#   - 选项含换行/多行段落（截图：选项显示为长文章）
#   - 选项是"为什么？""什么？"等非选项文本
#   - 题干包含"纠正模型""核心要点"等LLM思考泄露
#   - 多道题完全相同（无去重）
#   - 选项长度异常（<2字 或 >120字）
# 此函数在 _precision_test 出题出口统一拦截。

_GARBAGE_PREFIXES = ("纠正模型", "核心要点", "【纠错", "【修正", "注意：", "提示：",
                    "解析：", "答案：", "解答：", "说明：")
_SHORT_GARBAGE = ("为什么", "什么", "哪个", "如何", "是否", "怎样",
                  "A.", "B.", "C.", "D.", "以上", "都不对", "以上都对")


def _is_garbage_option(text):
    """判断一个选项文本是否是垃圾（不能作为有效选择题选项）。"""
    t = text.strip()
    if len(t) < 2:
        return True
    if len(t) > 150:
        return True
    # 含换行 = LLM 输出了多行段落，不是干净选项
    if "\n" in t or "\r" in t:
        return True
    # 纯问号/纯标点
    if set(t) <= set("？?!！。、,.;:"):
        return True
    # 以垃圾关键词开头且太短
    for kw in _SHORT_GARBAGE:
        if t.startswith(kw) and len(t) < 10:
            return True
    # 包含LLM泄露标记
    for pfx in _GARBAGE_PREFIXES:
        if t.startswith(pfx):
            return True
    # 包含括号内的元注释（如"(适用范围与前提略微相同)"）
    if re.search(r'[(（][^)]{0,40}(?:适用|范围|前提|无关|备注|注意)[^)]*[)）]', t):
        return len(t) > 80
    return False


def _is_garbage_stem(stem):
    """判断题干是否包含LLM泄露/垃圾文本。"""
    s = stem.strip()
    if len(s) < 4:
        return True
    if len(s) > 300:
        return True
    # 题干以LLM泄露前缀开头
    for pfx in _GARBAGE_PREFIXES:
        if s.startswith(pfx):
            return True
    # 题干中包含括号包裹的"核心要点/纠正"等元信息
    if re.search(r'[（(][^)]*(?:核心要点|纠正模型|纠错|修正)[^)]*[)）]', s):
        return True
    return False


def _normalize_stem(stem):
    """标准化题干用于去重比较（去掉末尾括号/空白）。"""
    s = re.sub(r'[？?！!（()\s]+$', '', stem.strip())
    return s[:80]  # 取前80字符比较即可


def _validate_and_dedup_questions(qs, topic=None, n=5):
    """对题目列表执行质量校验 + 去重 + 补足。
    
    步骤（顺序重要）：
      1. 先格式清洗（_clean_choice_question）：把内嵌选项提取到 options 字段
      2. 再内容质量检测：过滤垃圾题干/垃圾选项
      3. 基于题干去重（完全相同+高度相似>85%）
      4. 若不足n道，用 mock_test_q 兜底补足
    
    返回有效题目列表。
    """
    if not qs:
        qs = []
    
    # Step 1: 格式清洗优先（处理 A. xxx / (A) xxx 内嵌格式）
    qs = [_clean_choice_question(q) for q in qs]
    
    # Step 2: 内容质量过滤
    valid = []
    for q in qs:
        # 检查题干
        if _is_garbage_stem(q.get("stem", "")):
            continue
        # 检查选择题选项（此时已清洗过，空壳应已替换为真实内容）
        if q.get("type") == "choice":
            opts = q.get("options") or []
            bad_opts = sum(1 for o in opts if _is_garbage_option(str(o)))
            # 如果超过一半选项是垃圾 → 整道题丢弃
            if len(opts) > 0 and bad_opts > len(opts) / 2:
                continue
            # 清理掉个别垃圾选项后如果不足2个选项也丢弃
            clean_opts = [o for o in opts if not _is_garbage_option(str(o))]
            if len(clean_opts) < 2:
                continue
            q["options"] = clean_opts
            # answer 可能超出新 options 范围
            ans = q.get("answer", 0)
            if isinstance(ans, int) and ans >= len(clean_opts):
                q["answer"] = 0
        
        valid.append(q)
    
    # Step 2: 格式清洗（处理内嵌选项问题）
    valid = [_clean_choice_question(q) for q in valid]
    
    # Step 3: 去重（基于标准化题干）
    seen_stems = []
    deduped = []
    for q in valid:
        norm = _normalize_stem(q.get("stem", ""))
        is_dup = False
        for seen in seen_stems:
            # 完全相同 or 高度相似（简单字符重叠率 > 85%）
            if norm == seen:
                is_dup = True
                break
            overlap = len(set(norm) & set(seen)) / max(len(set(norm)), len(set(seen)), 1)
            if overlap > 0.88 and (norm[:30] == seen[:30] or norm[-30:] == seen[-30:]):
                is_dup = True
                break
        if not is_dup:
            seen_stems.append(norm)
            deduped.append(q)
    
    # Step 4: 补足到 n 道
    if topic and len(deduped) < n:
        used_indices = list(range(len(deduped)))  # 已用过的子点偏移尽量避开
        while len(deduped) < n:
            try:
                new_q = mock_test_q(topic, len(deduped))
                norm_new = _normalize_stem(new_q.get("stem", ""))
                # 确保不与已有重复
                if not any(norm_new == s for s in seen_stems):
                    new_q = _clean_choice_question(new_q)
                    deduped.append(new_q)
                    seen_stems.append(norm_new)
            except Exception:
                break
    
    return deduped


def _calq(stem, answer, explanation):
    """构造计算题（calc），answer 已为字符串形式。"""
    return {"type": "calc", "stem": stem, "answer": answer,
            "explanation": explanation}


def _math_fallback(sub, title, idx=0):
    """数学学科智能兜底：当提取不到算式/facts时，根据子点名称直接生成可算的数学题。
    确保永远不会出现「不会考/没什么用」类垃圾选项。返回 None 表示无法生成（交给更底层兜底）。"""
    s = sub
    i = idx
    from math import gcd as __gcd
    a = 3 + i % 7
    b = 5 + i % 6

    # ---- 小学低段：数数 / 比较 / 序数 / 分与合 / 加减 ----
    if any(k in s for k in ("数数", "认识", "读数", "写数")):
        return _cq(f"与 {a} 相邻的两个数是（　　）",
                   [f"{a-1} 和 {a+1}", f"{a} 和 {a+1}", f"{a-2} 和 {a-1}", f"{a+1} 和 {a+2}"],
                   0, f"相邻数：比它小1的是{a-1}，大1的是{a+1}。")
    if "比大小" in s or "多些少些" in s or "比较" in s:
        return _cq(f"在 {a} 和 {b} 中，较大的数是（　　）",
                   [str(max(a, b)), str(min(a, b)), str(a + b), str(a - b)], 0,
                   f"{max(a,b)} > {min(a,b)}，较大的数是{max(a,b)}。")
    if "第几" in s or "序数" in s or "排队" in s:
        return _fq(f"从左到右数，第 {a} 个和第 {b} 个之间相隔 ______ 个位置（不含两端）。",
                   str(abs(b - a) - 1),
                   "序数相差几，中间间隔=两数之差减1。")
    if "分与合" in s:
        return _cq(f"{a+b} 可以分成 {a} 和（　　）",
                   [str(b), str(a), str(a + b), str(b - 1)], 0,
                   f"数的分与合：{a}+{b}={a+b}，所以分成{a}和{b}。")
    if "加减法" in s or "连加" in s or "连减" in s or "混合" in s or ("加减" in s):
        return _calq(f"计算 {a} + {b} - {i % (a + b + 1)} = ?",
                     str(a + b - (i % (a + b + 1))),
                     f"按顺序算：{a}+{b}={a+b}，再减去得到结果。")
    if "乘法" in s or "乘加" in s or "乘减" in s:
        return _calq(f"计算 {a} × {b} = ?", str(a * b),
                     f"乘法是相同加数连加：{a}个{b}相加 = {a*b}。")
    if "除法" in s or "平均" in s:
        q, r = divmod(a * b, b)
        return _cq(f"把 {a*b} 个苹果平均分给 {b} 个小朋友，每人分（　　）个",
                   [str(q), str(q + 1), str(a), str(b)], 0,
                   f"平均分用除法：{a*b} ÷ {b} = {q}（个）。")
    # ---- 立体图形 / 位置 ----
    if any(k in s for k in ("长方体", "正方体", "立体图形", "圆柱", "球", "拼搭")):
        return _cq("下列物体中，无论从哪个方向看都完全相同的立体图形是（　　）",
                   ["球体", "长方体", "正方体", "圆柱"], 0,
                   "球体三视图都是圆、完全相同；长方体/正方体/圆柱从不同方向看形状不同。")
    if any(k in s for k in ("位置", "上下", "前后", "左右", "方位")):
        return _cq(f"小明在小红的 {('左边' if i % 2 else '右边')}，那么小红在小明的（　　）",
                   [("右边" if i % 2 else "左边"), "前边", "后边", "上边"], 0,
                   "左右是相对位置：A在B左边，则B在A右边。")
    # ---- 钟表 ----
    if "钟面" in s or "钟" in s or "整时" in s or "时间" in s:
        h = 3 + i % 9
        return _cq(f"时针指向 {h}，分针指向 12，这时是（　　）",
                   [f"{h}时整", f"{h}时半", f"{12 - h}时", f"{h}分"], 0,
                   f"分针指12、时针指{h}是{h}时整；半时分针指6。")
    # ---- 分数 / 小数 ----
    if "分数" in s:
        return _cq(f"把一个披萨平均分成 {b} 份，取其中 {a} 份，用分数表示是（　　）",
                   [f"{a}/{b}", f"{b}/{a}", f"{a+b}/{b}", f"{a}/{a+b}"], 0,
                   f"分数线下是总份数{b}，线上是取的份数{a}，记作{a}/{b}。")
    if "小数" in s:
        return _cq(f"{a}.{b} 里面包含（　　）个 0.1",
                   [str(a * 10 + b), str(a + b), str(a * b), str(a)], 0,
                   f"十分位上的{b}表示{b}个0.1，个位{a}表示{a*10}个0.1，共{a*10+b}个。")
    # ---- 方程 / 未知数 ----
    if "方程" in s or "未知数" in s or "等式" in s:
        return _calq(f"解方程：x + {a} = {a + b}，则 x = ?", str(b),
                     f"等式两边同时减去{a}：x = {a+b} - {a} = {b}。")
    # ---- 比例 / 百分数 ----
    if "比例" in s or "比" in s:
        return _cq(f"化简 {a}∶{b}，结果是（　　）",
                   [f"{a//__gcd(a,b)}∶{b//__gcd(a,b)}", f"{a}∶{b+1}", f"{a+1}∶{b}", f"{a*b}∶1"], 0,
                   f"同除以最大公约数：{a}∶{b} = {a//__gcd(a,b)}∶{b//__gcd(a,b)}。")
    if "百分" in s or "利率" in s or "折扣" in s:
        return _calq(f"一件 {100*b} 元的商品打 {a*10}% 折，应付 ______ 元",
                     str(100 * b * a * 10 // 100),
                     f"打几折=乘以十分之几：{100*b}×{a*10}% = {100*b*a*10//100} 元。")
    # ---- 统计 / 数据 ----
    if "统计" in s or "数据" in s or "平均" in s or "图表" in s:
        return _cq(f"一组数据 {a},{b},{a+b-1} 的平均数是（　　）",
                   [str((a + b + a + b - 1) // 3), str(a), str(b), str(a + b)], 0,
                   f"平均数=总和÷个数=({a}+{b}+{a+b-1})÷3={(a+b+a+b-1)//3}。")
    # ---- 周长 / 面积 / 角度 ----
    if "周长" in s:
        return _calq(f"一个边长为 {a} 的正方形，周长是 ______", str(4 * a),
                     f"正方形周长=边长×4={a}×4={4*a}。")
    if "面积" in s:
        return _calq(f"一个长 {b}、宽 {a} 的长方形，面积是 ______", str(a * b),
                     f"长方形面积=长×宽={b}×{a}={a*b}。")
    if "角" in s and ("度" in s or "直角" in s or "量角" in s):
        return _cq("一个直角的度数是（　　）",
                   ["90°", "180°", "45°", "360°"], 0,
                   "直角=90°，平角=180°，周角=360°，锐角<90°。")

    # ---- 应用 / 解决问题 / 综合运用：出具体可算应用题（杜绝‘X是Y重要组成’空泛句）----
    if any(k in s for k in ("应用", "解决问题", "方案", "综合运用", "实践", "实际")):
        a2, b2 = 2 + i % 5, 3 + i % 7
        if "百分" in s or "利率" in s or "折扣" in s or "利润" in s:
            price = 100 * b2
            rate = a2 * 10
            return _calq(f"一件标价 {price} 元的商品打 {rate}% 出售，实际应付 ______ 元",
                         str(price * rate // 100),
                         f"打{rate}折=原价×{rate/10:.1f}折率：{price}×{rate}%={price*rate//100} 元。")
        if "行程" in s or "速度" in s or "路程" in s:
            v, t = 40 + i * 10, 2 + i % 4
            return _calq(f"一辆汽车以 {v} km/h 匀速行驶 {t} 小时，共行驶 ______ km",
                         str(v * t), f"路程=速度×时间={v}×{t}={v*t} km。")
        if "工程" in s or "效率" in s or "工作" in s:
            return _calq(f"一项工程甲单独做需 {a2+b2} 天，乙单独做需 {a2+b2+2} 天，两人合做每天完成总量的 ______ (用分数表示)",
                         f"1/{a2+b2}+1/{a2+b2+2}",
                         f"合做效率=甲效率+乙效率=1/{a2+b2}+1/{a2+b2+2}。")
        # 默认：单价×数量类应用题
        unit = 5 + i % 8
        cnt = 3 + i % 9
        return _calq(f"每个笔记本 {unit} 元，买 {cnt} 本一共需要 ______ 元",
                     str(unit * cnt),
                     f"总价=单价×数量={unit}×{cnt}={unit*cnt} 元。")

    # ---- 函数相关 ----
    if "函数" in s or "定义域" in s:
        pool = [
            _cq(f"函数 $f(x)=\\sqrt{{x-{2+i}}}$ 的定义域是？",
                [f"$[{2+i},+\\infty)$", f"$(-\\infty,{2+i}]$", f"$[0,{2+i}]$", "$R$"],
                0, f"根号内需≥0，故 $x \\geq {2+i}$。"),
            _cq("下列关系式能表示「$y$ 是 $x$ 的函数」的是？",
                ["$y=x^2$（一个x对应唯一y）", "x=y²（一个x可对应两个y）", "$y^2=x$", "$\\pm y = |x|$"],
                0, "函数要求：对定义域内**每个**x，有**唯一确定**的y与之对应。"),
            _fq("若 $f(x)$ 是函数且 $f(3)=7, f(5)=$ ______ 需要更多信息才能确定。",
                "不确定/无法确定/不能确定",
                "只知道一点的函数值无法确定其他点的值——需要知道函数解析式或更多条件。"),
        ]
        return pool[i % len(pool)]
    if "单调" in s or "增减" in s:
        return _cq(
            "函数 $f(x)=-(x+{1+i})^2+{5+i}$ 的单调递增区间是？",
            [f"$(-\\infty,-{1+i}]$", f"$[-{1+i},+\\infty)$", f"$(-\\infty,{1+i}]$", f"$[{1+i},+\\infty)$"],
            0, f"二次函数开口向下，对称轴 $x=-{1+i}$，左侧递增右侧递减。"
        )
    if "奇偶" in s:
        return _cq(
            "下列函数为偶函数的是？",
            ["$f(x)=x^4+|x|$（满足$f(-x)=f(x)$）", "$f(x)=x^3+x$（奇函数）",
             "$f(x)=(x+1)^2$（非奇非偶）", "$f(x)=\\frac{1}{x}+x$（奇函数）"],
            0, "偶函数判定：$f(-x)=f(x)$ 对定义域内所有x成立。"
        )
    if "值域" in s:
        return _cq(
            f"函数 $y=(x-{i})^2+{i+1}(x\\in R)$ 的最小值是？",
            [str(i+1), str(i), str(2*i+1), str((i+1)**2)],
            0, f"二次项系数>0，顶点纵坐标即为最小值：$y_{{min}}={i+1}$。"
        )

    # ---- 三角函数 ----
    if any(k in s for k in ("正弦","余弦","正切","sin","cos","tan","三角","诱导")):
        pool = [
            _cq("$\\sin {30+i*15}°=$ ______（精确值）。",
                ["0.5 或 ½", "$\\frac{\\sqrt{3}}{2}$", "$\\frac{\\sqrt{2}}{2}$", "1"],
                0, "特殊角三角函数值需熟记：sin30°=½, sin45°=√2/2, sin60°=√3/2。"),
            _cq("若 $\\alpha$ 是第二象限角，则下列正确的是？",
                ["$\\sin\\alpha > 0, \\cos\\alpha < 0$", "$\\sin\\alpha < 0, \\cos\\alpha > 0$",
                 "$\\sin\\alpha > 0, \\cos\\alpha > 0$", "$\\sin\\alpha < 0, \\cos\\alpha < 0$"],
                0, "二象限：x<0,y>0 → sin=y/r>0, cos=x/r<0"),
            _fq("已知 $\\sin\\alpha = \\frac{3}{5}, \\alpha$ 为锐角，则 $\\cos\\alpha=$ ______。", "$\\frac{4}{5}$ 或 4/5",
                "同角平方关系：$\\sin^2\\alpha+\\cos^2\\alpha=1$ → $\\cos\\alpha=\\sqrt{1-9/25}=4/5$。"),
        ]
        return pool[i % len(pool)]

    # ---- 数列 ----
    if any(k in s for k in ("数列","等差","等比","通项","求和")):
        a1 = 3 + i
        d = 2 + i
        pool = [
            _calq(f"等差数列中 $a_1={a1}, d={d}$，求 $a_5$ 和 $S_5$。",
                   f"a_5={a1+4*d}; S_5={5*(a1+a1+4*d)//2}",
                   f"$a_5=a_1+4d={a1}+4\\times{d}={a1+4*d}$；$S_5=\\frac{{5(a_1+a_5)}}{{2}}=\\frac{{5({a1}+{a1+4*d})}}{{2}}={5*(2*a1+4*d)//2}$。"),
            _cq(f"等比数列 $2^{{{3+i}}}$ 的第 {3+i} 项是？",
                [f"$2^{{{3+i}}}$", f"${3+i}$", f"$2^{{{3-i}}}$", f"${(3+i)**2}$"],
                0, f"通项 $a_n=2^n$，所以 $a_{{{3+i}}}=2^{{{3+i}}}={2**(3+i)}$。"),
            _fq(f"等差数列前 n 项和公式 $S_n=$ ______（用 $a_1,a_n,n$ 表示）。",
                "\\frac{n(a_1+a_n)}{2}",
                "$S_n = \\frac{n(a_1+a_n)}{2}$ = 首末两项和 × 项数 ÷ 2。"),
        ]
        return pool[i % len(pool)]

    # ---- 向量 ----
    if "向量" in s:
        return _cq(
            f"若 $\\vec{{a}}=({1+i},{2+i}), \\vec{{b}}=({3-i},{-1})$，则 $\\vec{{a}}\\cdot\\vec{{b}}=$ ？",
            [str((1+i)*(3-i)+(2+i)*(-1)), str((1+i)*3+(2+i)), str((1+i)+(2+i)), str((1+i)*(3-i))],
            0, f"数量积 = $x_1x_2+y_1y_2={(1+i)}\\times{(3-i)}+{(2+i)}\\times(-1)={int((1+i)*(3-i)-(2+i))}$。"
        )

    # ---- 立体几何 ----
    if "柱体" in s or "锥体" in s or "球" in s or "体积" in s and "函数" not in title:
        r = i + 2
        h = i + 3
        return _cq(
            f"圆柱底面半径 r={r}, 高 h={h}，则其体积 V=？（$\\pi$保留符号）",
            [f"${r*r*h}\\pi$", f"${r*h}\\pi$", f"${2*r*h}\\pi$", f"${r*r*h^2}\\pi$"],
            0, f"$V=\\pi r^2h = \\pi\\times{r}^2\\times{h}={r*r*h}\\pi$。"
        )

    # ---- 解析几何 ----
    if "直线" in s or "圆" in s or "斜率" in s:
        k = i + 1
        b = i + 2
        return _fq(
            f"直线 $y={k}x+{b}$ 在 x 轴上的截距是 ______（用分数表示）",
            f"{-b}/{k}" or f"-{b}/{k}",
            f"令 y=0: {k}x+{b}=0 → x=-{b}/{k}。"
        )

    # ---- 导数 ----
    if "导数" in s or "极值" in s:
        return _cq(
            f"设 $f(x)=x^3-{3+i}x+1$，则 $f'(x)=$ ？",
            [f"$3x^2-{3+i}$", f"$3x^2+{3+i}$", f"$x^2-{3+i}$", f"$3x^2-x$"],
            0, f"幂函数求导法则：$(x^n)'=nx^{{n-1}}$，故 $(x^3)'=3x^2$，常数项导数为0。"
        )

    # ---- 概率统计 ----
    if "概率" in s or "排列" in s or "组合" in s:
        total = 6 + i
        choose = 2 + (i % 3)
        from math import factorial
        try:
            ans = int(factorial(total) / (factorial(choose) * factorial(total - choose)))
        except (ValueError, ZeroDivisionError, OverflowError):
            ans = total * (total - 1) // 2
        return _cq(
            f"从 {total} 个不同元素中选 {choose} 个，有多少种不同的选法？",
            [str(ans), str(ans * choose), str(ans + 1), str(total)],
            0, f"组合数 $C_{total}^{choose} = \\frac{{{total}!}}{{{choose}!({total}-{choose})!}} = {ans}$。"
        )

    # ---- 不等式 ----
    if "不等式" in s:
        a = i + 2
        return _fq(
            f"若 $x>{0}$，由均值不等式知 $x + \\frac{{{a*a}}}{{x}}$ 的最小值是______。",
            f"{2*a}" or f"{2*(i+2)}",
            f"由 $x+\\frac{{c}}{{x}} \\geq 2\\sqrt{{c}}$，取 $c={a*a}$ 得最小值 $2a={2*a}$（当$x=a$时取等）。"
        )

    # 无法识别的数学子点 → 返回None让更底层处理
    return None


def _subject_quiz(subject, sub, title, idx):
    """全学科智能出题引擎：根据学科与子点关键词，生成有技术含量的具体考试题。
    优先覆盖各学科高频子点；无法识别返回 None（交给 _concept_stem / 终极兜底）。"""
    s, i = sub, idx
    if subject == "数学":
        return _math_fallback(sub, title, idx)
    if subject == "物理":
        return _physics_quiz(s, i)
    if subject == "化学":
        return _chem_quiz(s, i)
    if subject == "生物":
        return _bio_quiz(s, i)
    if subject == "语文":
        return _chinese_quiz(s, i)
    if subject == "英语":
        return _english_quiz(s, i)
    if subject in ("历史", "思想政治", "道德与法治"):
        return _humanity_quiz(s, i, subject)
    if subject == "地理":
        return _geo_quiz(s, i)
    if subject == "科学":
        return _science_quiz(s, i)
    return None


# ── 物理概念题库（覆盖引擎数值题未涉及的考点，首次命中即出真题）──
_PHYS_BANK = [
    (("长度时间测量", "长度", "刻度尺"), "用刻度尺测量长度时，读数要求（　　）",
     ["估读到分度值的下一位", "读到分度值即可", "不需要估读", "只读整厘米数"], 0,
     "刻度尺读数要估读到分度值的下一位，并注明单位。"),
    (("参照物",), "判断物体是运动还是静止时，被选作标准的物体叫（　　）",
     ["参照物", "运动物体", "静止物体", "标准物"], 0,
     "研究物体运动时，被选作标准的物体叫参照物，运动和静止是相对的。"),
    (("匀速直线",), "关于匀速直线运动，下列说法正确的是（　　）",
     ["速度的大小和方向都保持不变", "只有大小不变", "只有方向不变", "速度越来越大"], 0,
     "匀速直线运动中速度的大小和方向都不变。"),
    (("温度温度计", "温度计"), "常用液体温度计的工作原理是（　　）",
     ["液体的热胀冷缩", "液体蒸发", "物体导热", "分子运动加快"], 0,
     "常用温度计利用液体热胀冷缩的性质制成，使用时不能超过量程。"),
    (("熔化凝固",), "晶体在熔化过程中的特点是（　　）",
     ["吸收热量但温度保持不变", "放出热量温度不变", "温度不断升高", "既不吸热也不放热"], 0,
     "晶体熔化时不断吸热，但温度保持在熔点不变。"),
    (("汽化液化",), "关于蒸发和沸腾，下列说法正确的是（　　）",
     ["都是汽化现象且都要吸热", "蒸发放热沸腾吸热", "都要放热", "都不需要吸放热"], 0,
     "蒸发和沸腾都是汽化现象，都要吸热；蒸发在任何温度下进行。"),
    (("升华凝华",), "下列现象中属于升华的是（　　）",
     ["樟脑丸变小消失", "露珠的形成", "冰雪消融", "雾的形成"], 0,
     "升华是固态直接变气态（吸热），如樟脑丸变小、干冰消失。"),
    (("直线传播", "传播"), "下列现象能说明光沿直线传播的是（　　）",
     ["日食、月食和影子的形成", "水中筷子‘变弯’", "彩虹的形成", "平面镜成像"], 0,
     "光在同种均匀介质中沿直线传播，形成影子、小孔成像和日月食。"),
    (("色散",), "让白光通过三棱镜后分解成七色光带，这一现象说明（　　）",
     ["白光是由多种色光混合而成的", "三棱镜能发出彩光", "光是直线传播的", "光会被吸收"], 0,
     "光的色散说明白光由红橙黄绿蓝靛紫等多种色光组成（牛顿发现）。"),
    (("眼睛眼镜",), "近视眼看不清远处物体，应配戴（　　）矫正",
     ["凹透镜", "凸透镜", "平面镜", "三棱镜"], 0,
     "近视眼成像在视网膜前，用凹透镜发散光线矫正；远视用凸透镜。"),
    (("显微镜望远镜",), "显微镜和望远镜的目镜、物镜通常都是（　　）",
     ["凸透镜", "凹透镜", "平面镜", "三棱镜"], 0,
     "显微镜、望远镜的物镜和目镜都相当于凸透镜。"),
    (("质量天平", "质量"), "关于质量，下列说法正确的是（　　）",
     ["质量是物体的属性，不随位置和状态改变", "物体到月球质量变小", "水结冰质量变大", "压扁后质量变小"], 0,
     "质量是物体所含物质的多少，不随形状、状态、位置改变。"),
    (("鉴别物质",), "可以用来鉴别不同物质的物理量是（　　）",
     ["密度", "质量", "体积", "重力"], 0,
     "密度是物质的一种特性，不同物质密度一般不同，可用来鉴别物质。"),
    (("牛顿第一定律",), "牛顿第一定律指出，物体在不受外力作用时将（　　）",
     ["保持静止或匀速直线运动状态", "立即停下来", "做减速运动", "改变运动方向"], 0,
     "牛顿第一定律（惯性定律）：不受外力时物体保持静止或匀速直线运动。"),
    (("惯性",), "关于惯性，下列说法正确的是（　　）",
     ["一切物体在任何情况下都有惯性", "速度越大惯性越大", "静止物体没有惯性", "只有运动物体有惯性"], 0,
     "惯性是物体的固有属性，一切物体都有惯性，只与质量有关。"),
    (("摩擦力",), "下列增大摩擦的措施中正确的是（　　）",
     ["自行车刹车时用力捏闸(增大压力)", "给轴承加润滑油", "用滚动代替滑动", "使接触面更光滑"], 0,
     "增大摩擦：增大压力、使接触面粗糙；其余都是减小摩擦的方法。"),
    (("液体压强",), "关于液体压强，下列说法正确的是（　　）",
     ["液体内部压强随深度增大而增大", "只与液体多少有关", "同深度各方向不相等", "与液体密度无关"], 0,
     "液体压强 p=ρgh，随深度增大而增大，同一深度各方向相等。"),
    (("功率",), "功率是表示（　　）的物理量",
     ["做功快慢", "做功多少", "力的大小", "能量总量"], 0,
     "功率 P=W/t 表示做功的快慢，单位是瓦特(W)。"),
    (("动能",), "关于动能，下列说法正确的是（　　）",
     ["质量越大、速度越大，动能越大", "只与质量有关", "只与速度有关", "静止物体动能最大"], 0,
     "动能大小与物体的质量和速度有关，速度影响更显著。"),
    (("势能",), "物体的重力势能大小与（　　）有关",
     ["质量和被举高的高度", "只与质量", "只与高度", "与速度"], 0,
     "重力势能与物体的质量和所处高度有关，越高越重势能越大。"),
    (("机械能守恒", "机械能"), "不计摩擦时，物体下落过程中（　　）",
     ["重力势能减小，动能增大，机械能不变", "动能势能都增大", "机械能减小", "动能减小"], 0,
     "只有重力做功时机械能守恒，动能与势能相互转化。"),
    (("斜面",), "斜面属于（　　）",
     ["省力的简单机械", "费力机械", "既不省力也不省距离", "只改变方向"], 0,
     "斜面是省力的简单机械，坡越缓越省力，但费距离。"),
    (("分子动理论", "分子"), "扩散现象说明（　　）",
     ["分子在不停地做无规则运动", "分子间有引力", "分子很小", "分子不运动"], 0,
     "扩散现象说明一切物质的分子都在永不停息地做无规则运动。"),
    (("内能",), "改变物体内能的两种方式是（　　）",
     ["做功和热传递", "升温和降温", "压缩和膨胀", "摩擦和碰撞"], 0,
     "做功和热传递都能改变物体的内能，二者在改变内能上等效。"),
    (("热机", "热机效率"), "汽油机的四个冲程中，将内能转化为机械能的是（　　）",
     ["做功冲程", "吸气冲程", "压缩冲程", "排气冲程"], 0,
     "做功冲程中高温高压燃气推动活塞，把内能转化为机械能。"),
    (("能量转化", "能量守恒", "能量"), "能量守恒定律指出，能量（　　）",
     ["既不会凭空产生也不会消灭，只会转化或转移", "可以凭空产生", "会逐渐消失", "总量不断增加"], 0,
     "能量守恒定律：能量只能从一种形式转化为另一种，总量保持不变。"),
    (("能源分类", "能源", "可持续发展"), "下列属于可再生能源的是（　　）",
     ["太阳能、风能、水能", "煤", "石油", "天然气"], 0,
     "太阳能、风能、水能可短期再生；煤、石油、天然气是不可再生能源。"),
    (("核能",), "核电站利用的核能来自（　　）",
     ["原子核的裂变", "原子核的聚变", "化学反应", "电磁感应"], 0,
     "目前核电站利用重核裂变释放的核能发电。"),
    (("电荷",), "关于电荷间的相互作用，下列说法正确的是（　　）",
     ["同种电荷相互排斥，异种电荷相互吸引", "同种吸引", "异种排斥", "都相互吸引"], 0,
     "自然界只有正、负两种电荷，同种排斥，异种吸引。"),
    (("电流电路", "练习使用电流表", "电流"), "关于电流方向，物理学中规定（　　）",
     ["正电荷定向移动的方向为电流方向", "负电荷移动方向", "任意方向", "电子移动方向"], 0,
     "规定正电荷定向移动的方向为电流方向，电流从电源正极流出。"),
    (("串联并联电压",), "串联电路中各处的关系正确的是（　　）",
     ["电流处处相等，总电压等于各部分电压之和", "电压处处相等", "电流之和为总电流", "各电阻电压相等"], 0,
     "串联电路电流处处相等，总电压等于各用电器电压之和。"),
    (("串联并联",), "并联电路的特点是（　　）",
     ["各支路两端电压相等", "各支路电流相等", "总电阻大于任一支路", "干路断开支路仍工作"], 0,
     "并联电路各支路电压相等，干路电流等于各支路电流之和。"),
    (("电压",), "我国家庭电路的电压是（　　）",
     ["220 V", "36 V", "380 V", "110 V"], 0,
     "我国家庭电路电压为220 V，对人体安全的电压不高于36 V。"),
    (("变阻器",), "滑动变阻器改变电阻的原理是（　　）",
     ["改变接入电路的电阻线长度", "改变电阻线材料", "改变横截面积", "改变温度"], 0,
     "滑动变阻器通过改变接入电路的电阻线长度来改变电阻，从而改变电流。"),
    (("安全用电", "触电急救"), "下列做法符合安全用电原则的是（　　）",
     ["不接触低压带电体、不靠近高压带电体", "用湿手扳开关", "在电线上晾衣服", "用铜丝代替保险丝"], 0,
     "安全用电：不接触低压带电体，不靠近高压带电体，规范操作。"),
    (("额定功率", "电功"), "用电器铭牌上标的‘220V 100W’中的100W是指（　　）",
     ["额定功率", "实际功率", "最大功率", "消耗的电能"], 0,
     "铭牌标的是额定电压下正常工作的额定功率。"),
    (("焦耳定律",), "电流通过导体产生的热量遵循焦耳定律，其表达式是（　　）",
     ["Q=I²Rt", "Q=UIt只对纯电阻", "Q=mcΔt", "Q=Pt"], 0,
     "焦耳定律 Q=I²Rt，电流的热效应与电流平方、电阻、时间成正比。"),
    (("家庭电路", "火线零线", "漏电保护"), "家庭电路中火线与零线之间的电压是（　　）",
     ["220 V", "0 V", "380 V", "36 V"], 0,
     "火线与零线间电压220 V；用试电笔可辨别火线（氖管发光的是火线）。"),
    (("磁场", "磁感线"), "关于磁感线，下列说法正确的是（　　）",
     ["磁体外部磁感线从N极出发回到S极", "从S极出发", "磁感线相交", "磁感线是真实存在的"], 0,
     "磁体外部磁感线从N极指向S极，用来形象描述磁场，实际并不存在。"),
    (("电生磁",), "奥斯特实验(通电导线使小磁针偏转)说明（　　）",
     ["通电导线周围存在磁场", "磁场产生电流", "电荷间有作用力", "同名磁极相斥"], 0,
     "奥斯特实验说明电流周围存在磁场，即‘电生磁’。"),
    (("电磁铁",), "电磁铁磁性的强弱与（　　）有关",
     ["电流大小和线圈匝数", "只与电流", "只与匝数", "与铁芯无关"], 0,
     "电磁铁磁性强弱与电流大小、线圈匝数以及有无铁芯有关。"),
    (("电动机",), "电动机工作时能量转化情况是（　　）",
     ["电能转化为机械能", "机械能转化为电能", "内能转化为电能", "电能转化为内能"], 0,
     "电动机利用通电线圈在磁场中受力转动，把电能转化为机械能。"),
    (("电磁感应",), "发电机的工作原理是（　　）",
     ["电磁感应现象", "电流的磁效应", "电流的热效应", "磁极间相互作用"], 0,
     "闭合电路的部分导体切割磁感线产生感应电流，即电磁感应（法拉第）。"),
    (("电磁波", "广播通信", "信息时代"), "电磁波在真空中的传播速度约为（　　）",
     ["3×10⁸ m/s", "340 m/s", "3×10⁵ m/s", "1×10⁶ m/s"], 0,
     "电磁波可在真空中传播，速度约3×10⁸ m/s，等于光速。"),
    # ── 高中物理 ──
    (("质点参考系", "质点"), "把物体看作质点的条件是（　　）",
     ["物体的大小和形状对所研究问题影响可忽略", "物体一定很小", "物体一定很轻", "任何情况都可以"], 0,
     "当物体的大小、形状对所研究的问题影响可忽略时，可看作质点。"),
    (("时间位移",), "关于位移和路程，下列说法正确的是（　　）",
     ["位移是矢量，路程是标量", "两者都是矢量", "两者都是标量", "位移一定大于路程"], 0,
     "位移是矢量(由初位置指向末位置)，路程是标量(轨迹长度)。"),
    (("自由落体",), "自由落体运动是（　　）",
     ["初速度为零、只受重力的匀加速直线运动", "匀速运动", "初速度不为零", "只在真空中才是"], 0,
     "自由落体：初速度为零、只受重力作用，加速度为g的匀加速直线运动。"),
    (("合成分解",), "求两个共点力的合力时遵循（　　）",
     ["平行四边形定则", "三角形面积法", "杠杆原理", "叠加相减法"], 0,
     "力是矢量，合成与分解都遵循平行四边形定则。"),
    (("第二定律",), "牛顿第二定律的表达式是（　　）",
     ["F=ma", "F=mg", "W=Fs", "p=F/S"], 0,
     "牛顿第二定律：物体加速度与合外力成正比、与质量成反比，F=ma。"),
    (("第三定律",), "关于作用力与反作用力，下列说法正确的是（　　）",
     ["大小相等、方向相反、作用在不同物体上", "作用在同一物体", "可以平衡", "大小不一定相等"], 0,
     "作用力与反作用力大小相等、方向相反、分别作用在两个物体上。"),
    (("平抛",), "平抛运动可分解为（　　）",
     ["水平方向匀速直线运动和竖直方向自由落体运动", "两个匀速运动", "两个自由落体", "匀速圆周运动"], 0,
     "平抛运动水平方向做匀速直线运动，竖直方向做自由落体运动。"),
    (("天体质量", "卫星"), "人造地球卫星绕地球运动，提供向心力的是（　　）",
     ["地球对卫星的万有引力", "卫星的重力之外的力", "空气阻力", "太阳引力"], 0,
     "万有引力提供卫星做圆周运动所需的向心力。"),
    (("动能定理",), "动能定理的内容是（　　）",
     ["合外力做的功等于物体动能的变化", "重力做功等于势能变化", "功等于功率乘时间", "冲量等于动量变化"], 0,
     "动能定理：合外力对物体做的功等于物体动能的变化量。"),
    (("动量守恒", "动量定理", "动量", "冲量", "碰撞"), "系统不受外力或所受合外力为零时（　　）",
     ["系统总动量保持不变", "总动能不变", "总机械能不变", "总冲量为零"], 0,
     "动量守恒定律：系统不受外力或合外力为零时，总动量保持不变。"),
    (("单摆", "弹簧振子", "受迫振动", "共振"), "单摆做简谐运动时，其回复力由（　　）提供",
     ["重力沿切线方向的分力", "绳的拉力", "重力", "空气阻力"], 0,
     "单摆的回复力是重力沿摆动方向(切线)的分力，摆角很小时近似简谐运动。"),
    (("波长频率", "波的形成", "干涉衍射", "干涉", "衍射", "多普勒"), "关于波的现象，下列说法正确的是（　　）",
     ["干涉和衍射是波特有的现象", "只有声波能干涉", "衍射是光独有的", "波不能传递能量"], 0,
     "干涉和衍射是一切波特有的现象；波传播的是振动形式和能量。"),
    (("光的本性",), "现代物理认为光具有（　　）",
     ["波粒二象性", "只有波动性", "只有粒子性", "既非波也非粒子"], 0,
     "光既有波动性(干涉、衍射)又有粒子性(光电效应)，即波粒二象性。"),
    (("原子结构", "玻尔模型"), "卢瑟福由α粒子散射实验提出了（　　）",
     ["原子的核式结构模型", "枣糕模型", "电子云模型", "行星模型缺陷"], 0,
     "卢瑟福根据α粒子散射实验提出原子核式结构模型。"),
    (("放射性", "核反应"), "放射性元素放出的三种射线中，穿透能力最强的是（　　）",
     ["γ射线", "α射线", "β射线", "X射线"], 0,
     "穿透能力γ＞β＞α；α射线电离能力最强，穿透能力最弱。"),
    (("变压器", "远距离输电"), "理想变压器原、副线圈电压之比等于（　　）",
     ["原、副线圈的匝数之比", "电流之比", "功率之比", "电阻之比"], 0,
     "理想变压器 U₁/U₂=n₁/n₂，远距离输电用高压以减少线路损耗。"),
    (("交变电流", "正弦交流", "有效值"), "正弦交流电的有效值与峰值的关系是（　　）",
     ["有效值等于峰值除以√2", "有效值等于峰值", "有效值等于峰值的一半", "有效值大于峰值"], 0,
     "正弦交流电有效值 U=U峰/√2，家庭电路220V是有效值。"),
]


def _physics_quiz(s, i):
    for entry in _PHYS_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    if "速度" in s or "路程" in s or "运动" in s:
        v = 5 + i * 3
        t = 2 + i
        return _cq(f"汽车以 {v} m/s 的速度匀速行驶 {t} s，通过的路程为（　　）",
                   [f"{v*t} m", f"{v+t} m", f"{v//t} m", f"{v-t} m"], 0,
                   f"匀速直线运动：s = v·t = {v}×{t} = {v*t} m。")
    if "密度" in s:
        rho = 2 + i
        V = 10 + i * 5
        return _cq(f"某液体密度 ρ={rho} g/cm³，取体积 {V} cm³，其质量为（　　）",
                   [f"{rho*V} g", f"{rho+V} g", f"{rho*V*2} g", f"{V//rho} g"], 0,
                   f"m = ρV = {rho}×{V} = {rho*V} g。")
    if "重力" in s or ("力" in s and "摩擦" not in s and "压" not in s and "浮" not in s):
        m = 2 + i
        return _cq(f"质量 m={m} kg 的物体，所受重力约为（　　） (g取9.8 N/kg)",
                   [f"{m*9.8:.1f} N", f"{m} N", f"{m*9.8*2:.1f} N", f"{m/9.8:.2f} N"], 0,
                   f"G = mg = {m}×9.8 = {m*9.8:.1f} N。")
    if "压强" in s and "液体" not in s and "浮" not in s:
        F = 20 + i * 10
        S = 2 + i
        return _cq(f"水平桌面上的物体对桌面压力 F={F} N，受力面积 S={S} cm²，压强为（　　）",
                   [f"{F/S:.1f} N/cm²", f"{F+S} N/cm²", f"{F*S} N/cm²", f"{S/F:.2f} N/cm²"], 0,
                   f"p = F/S = {F}/{S} = {F/S:.1f} N/cm²。")
    if "浮力" in s or "阿基米德" in s or "浮沉" in s:
        Vp = 1 + i
        return _cq(f"体积 {Vp}×10⁻³ m³ 的木块完全浸没在水中（ρ水=1.0×10³ kg/m³，g=10 N/kg），受浮力（　　）",
                   [f"{10*Vp} N", f"{10*Vp*2} N", f"{10*Vp//2} N", f"{10*Vp+5} N"], 0,
                   f"F浮=ρ水gV排=1.0×10³×10×{Vp}×10⁻³={10*Vp} N。")
    if "反射" in s or "平面镜" in s:
        return _cq("身高 1.6 m 的人站在平面镜前 2 m 处，他在镜中的像高（　　）",
                   ["1.6 m", "2 m", "3.2 m", "0.8 m"], 0,
                   "平面镜成像：像与物等大，像高=人高=1.6 m（与距离无关）。")
    if "折射" in s or "透镜" in s or "凸透镜" in s or "焦距" in s:
        f0 = 10 + i * 5
        return _cq(f"凸透镜焦距 f={f0} cm，物体放在距透镜 {2*f0} cm（二倍焦距）处，成（　　）",
                   ["倒立等大的实像", "正立放大的虚像", "倒立缩小的实像", "正立等大的虚像"], 0,
                   f"物距 u=2f 时成倒立、等大的实像（放大与缩小的分界点）。")
    if "欧姆" in s or "电阻" in s or ("电流" in s and "电压" in s):
        U = 6 + i * 2
        R = 3 + i
        return _cq(f"电阻 R={R} Ω 两端电压 U={U} V，通过它的电流为（　　）",
                   [f"{U/R:.2f} A", f"{U+R} A", f"{U*R} A", f"{R/U:.2f} A"], 0,
                   f"欧姆定律：I = U/R = {U}/{R} = {U/R:.2f} A。")
    if "电功率" in s or "电能" in s:
        I = 0.5 + i * 0.1
        return _cq(f"用电器两端电压 220 V，工作电流 {I:.1f} A，其电功率为（　　）",
                   [f"{220*I:.1f} W", f"{220*I*2:.1f} W", f"{220+I:.1f} W", f"{220/I:.0f} W"], 0,
                   f"P = UI = 220×{I:.1f} = {220*I:.1f} W。")
    if "比热" in s or "热量" in s:
        m = 1 + i
        return _cq(f"水的比热容 4.2×10³ J/(kg·℃)，{m} kg 水升温 10℃，吸收热量（　　）",
                   [f"{int(4.2*m*10*1000)} J", f"{int(4.2*m*10*1000*2)} J", f"{int(4.2*m*10*1000//2)} J", f"{int(4.2*m*10*1000+1000)} J"], 0,
                   f"Q吸=cmΔt=4.2×10³×{m}×10={int(4.2*m*10*1000)} J。")
    if "热值" in s or "燃料" in s:
        q = 3 + i
        return _cq(f"燃料热值 q={q}×10⁷ J/kg，完全燃烧 2 kg 放热（　　）",
                   [f"{q*2}×10⁷ J", f"{q} J", f"{q+2}×10⁷ J", f"{q*2*2}×10⁷ J"], 0,
                   f"Q放=mq=2×{q}×10⁷={q*2}×10⁷ J。")
    if "声" in s or "声音" in s or "音调" in s:
        return _cq("关于声音，下列说法正确的是（　　）",
                   ["声音不能在真空中传播", "声音传播不需要介质", "真空传声最快", "音调由振幅决定"], 0,
                   "声音靠介质传播，真空不能传声；音调由频率决定，响度由振幅决定。")
    if "杠杆" in s:
        return _cq("下列工具正常使用时属于省力杠杆的是（　　）",
                   ["撬棍", "镊子", "钓鱼竿", "天平"], 0,
                   "撬棍动力臂>阻力臂省力；镊子、钓鱼竿费力；天平等臂。")
    if "滑轮" in s or "机械效率" in s:
        return _cq("使用定滑轮的优点是（　　）",
                   ["改变力的方向", "省力一半", "省距离", "既省力又省距离"], 0,
                   "定滑轮不省力但改变力的方向；动滑轮省一半力。")
    return None


# ── 化学概念题库（覆盖引擎未涉及的考点，首次命中即出真题）──
_CHEM_BANK = [
    (("物质变化", "变化"), "下列变化中属于化学变化的是（　　）",
     ["蜡烛燃烧", "冰雪融化", "水分蒸发", "玻璃破碎"], 0,
     "有新物质生成的变化是化学变化；蜡烛燃烧生成CO₂和水，其余是物理变化。"),
    (("药品取用", "加热与仪器", "观察与记录", "安全常识", "基本操作"), "取用固体粉末药品时，一般使用（　　）",
     ["药匙或纸槽", "手直接取", "镊子", "滴管"], 0,
     "取用固体粉末用药匙或纸槽；块状固体用镊子；取液体用滴管或倾倒。"),
    (("催化剂",), "关于催化剂，下列说法正确的是（　　）",
     ["改变反应速率，本身质量和化学性质在反应前后不变", "一定加快反应", "反应后质量减小", "改变生成物的质量"], 0,
     "催化剂能改变化学反应速率，本身的质量和化学性质在反应前后都不变。"),
    (("水的组成",), "电解水实验证明水是由（　　）组成的",
     ["氢元素和氧元素", "氢气和氧气", "氢分子和氧分子", "水分子"], 0,
     "电解水生成H₂和O₂，说明水由氢、氧两种元素组成。"),
    (("水的净化", "爱护水资源"), "下列净化水的操作中，净化程度最高的是（　　）",
     ["蒸馏", "过滤", "吸附", "沉淀"], 0,
     "净化程度：蒸馏＞蒸馏前的（吸附＞过滤＞沉淀）；蒸馏可得纯净水。"),
    (("化学式",), "关于化学式 H₂O 的含义，下列说法错误的是（　　）",
     ["表示2个水分子", "表示水这种物质", "表示水由氢氧元素组成", "1个水分子由2个氢原子和1个氧原子构成"], 0,
     "H₂O表示水、水的组成、1个水分子的构成；2个水分子应写作2H₂O。"),
    (("温室效应",), "下列气体中会造成温室效应的主要是（　　）",
     ["二氧化碳(CO₂)", "氮气(N₂)", "氧气(O₂)", "稀有气体"], 0,
     "CO₂是主要的温室气体，过多排放会加剧温室效应。"),
    (("燃烧条件",), "可燃物燃烧必须同时满足的条件是（　　）",
     ["有可燃物、与氧气接触、温度达到着火点", "只需有可燃物", "只需高温", "只需氧气"], 0,
     "燃烧需同时满足：可燃物、与氧气(空气)接触、温度达到着火点。"),
    (("灭火",), "用水灭火的主要原理是（　　）",
     ["降低温度到着火点以下", "隔绝氧气", "移走可燃物", "降低着火点"], 0,
     "水灭火主要靠吸热降温到着火点以下；着火点是物质固有属性不能降低。"),
    (("燃料", "热量", "新能源"), "下列属于清洁能源的是（　　）",
     ["氢能", "煤", "石油", "天然气"], 0,
     "氢气燃烧产物只有水，是最清洁的能源；煤、石油、天然气是化石燃料。"),
    (("锈蚀与防护", "锈蚀"), "铁生锈的条件是铁同时与（　　）接触",
     ["氧气和水", "只与氧气", "只与水", "二氧化碳"], 0,
     "铁生锈是铁与氧气、水共同作用的结果；隔绝氧气和水可防锈。"),
    (("结晶",), "从饱和溶液中析出晶体常用的方法是（　　）",
     ["冷却热饱和溶液或蒸发溶剂", "加水稀释", "升高温度", "加入更多溶质"], 0,
     "结晶方法：冷却热饱和溶液（适于溶解度受温度影响大的）或蒸发溶剂。"),
    (("中和反应",), "酸与碱作用生成盐和水的反应叫（　　）",
     ["中和反应", "复分解反应之外的反应", "置换反应", "化合反应"], 0,
     "中和反应是酸与碱生成盐和水的反应，属于复分解反应。"),
    (("复分解",), "复分解反应发生的条件是生成物中有（　　）",
     ["沉淀、气体或水", "只有沉淀", "只有气体", "新的单质"], 0,
     "复分解反应发生条件：生成物中有沉淀、气体或水生成。"),
    (("化肥种类",), "尿素[CO(NH₂)₂]属于（　　）",
     ["氮肥", "磷肥", "钾肥", "复合肥"], 0,
     "含氮的化肥是氮肥，能促进作物茎叶生长；尿素含氮量高。"),
    (("营养物质", "基本营养"), "人体需要的六大类营养物质中，能提供能量的主要是（　　）",
     ["糖类、油脂、蛋白质", "维生素", "水", "无机盐"], 0,
     "糖类、油脂、蛋白质是供能物质，其中糖类是主要供能物质。"),
    (("有机合成材料", "合成材料", "白色污染"), "‘白色污染’主要是由（　　）造成的",
     ["废弃塑料", "废纸", "金属废料", "玻璃碎片"], 0,
     "白色污染主要指难降解的废弃塑料，应减少使用并回收利用。"),
    (("胶体",), "下列分散系中属于胶体的是（　　）",
     ["豆浆", "食盐水", "泥浆", "蔗糖溶液"], 0,
     "胶体分散质粒径1~100 nm，如豆浆、牛奶，具有丁达尔效应。"),
    (("氧化还原反应",), "关于氧化还原反应，下列说法正确的是（　　）",
     ["有元素化合价升降的反应是氧化还原反应", "一定有氧参加", "一定是化合反应", "化合价不变"], 0,
     "氧化还原反应的本质是电子转移，特征是有元素化合价升降。"),
    (("钠",), "金属钠投入水中的现象，正确的是（　　）",
     ["浮在水面、熔成小球、四处游动并放出气体", "沉入水底", "无明显现象", "生成蓝色沉淀"], 0,
     "钠与水剧烈反应：2Na+2H₂O→2NaOH+H₂↑，浮、熔、游、响、红(酚酞)。"),
    (("氯气",), "氯气的颜色和性质是（　　）",
     ["黄绿色、有刺激性气味的有毒气体", "无色无味", "红棕色气体", "白色固体"], 0,
     "氯气是黄绿色、有刺激性气味的有毒气体，能使湿润的淀粉碘化钾试纸变蓝。"),
    (("铁",), "铁在氧气中燃烧的现象是（　　）",
     ["剧烈燃烧、火星四射、生成黑色固体", "发出白光", "产生白烟", "无变化"], 0,
     "铁在氧气中燃烧：3Fe+2O₂→Fe₃O₄，火星四射，生成黑色固体。"),
    (("铝",), "铝制品具有较好抗腐蚀性的原因是（　　）",
     ["表面生成致密氧化铝薄膜保护内部", "铝不活泼", "铝不与氧气反应", "铝硬度大"], 0,
     "铝表面易生成致密的Al₂O₃氧化膜，阻止内部金属继续被氧化。"),
    (("合金",), "关于合金，下列说法正确的是（　　）",
     ["合金的硬度一般比组成它的纯金属大", "合金是纯净物", "合金熔点一定更高", "合金不导电"], 0,
     "合金是金属混合物，硬度一般比成分金属大、熔点一般较低。"),
    (("周期律", "周期表", "电子排布"), "元素周期表中，同一周期从左到右元素的（　　）",
     ["原子序数依次增大", "电子层数增多", "金属性增强", "原子半径增大"], 0,
     "同周期从左到右原子序数增大、金属性减弱、非金属性增强。"),
    (("化学键", "共价键"), "下列物质中含有共价键的是（　　）",
     ["H₂O", "NaCl", "KCl", "MgO"], 0,
     "共价键是原子间共用电子对；H₂O含共价键，NaCl、KCl、MgO是离子键。"),
    (("硫和氮", "硫", "氨"), "氨气(NH₃)的重要性质是（　　）",
     ["有刺激性气味、极易溶于水、水溶液显碱性", "无味", "难溶于水", "水溶液显酸性"], 0,
     "氨气有刺激性气味、极易溶于水，其水溶液(氨水)显碱性。"),
    (("甲烷",), "甲烷(CH₄)充分燃烧的产物是（　　）",
     ["二氧化碳和水", "一氧化碳和水", "碳和水", "只有二氧化碳"], 0,
     "CH₄+2O₂→CO₂+2H₂O，甲烷是天然气的主要成分，是最简单的有机物。"),
    (("乙烯",), "鉴别乙烯常用的方法是通入（　　）",
     ["溴水，溴水褪色", "石灰水，变浑浊", "紫色石蕊，变红", "稀盐酸"], 0,
     "乙烯含碳碳双键，能使溴水和酸性高锰酸钾溶液褪色。"),
    (("烷烃",), "烷烃的通式是（　　）",
     ["CₙH₂ₙ₊₂", "CₙH₂ₙ", "CₙH₂ₙ₋₂", "CₙHₙ"], 0,
     "烷烃分子中只含碳碳单键，通式为CₙH₂ₙ₊₂。"),
    (("烯烃炔烃",), "乙炔分子中含有（　　）",
     ["碳碳三键", "碳碳单键", "碳碳双键", "苯环"], 0,
     "炔烃含碳碳三键，乙炔(C₂H₂)是最简单的炔烃，可用于焊接。"),
    (("芳香烃",), "苯(C₆H₆)的结构特点是（　　）",
     ["含有特殊的碳碳键(介于单双键之间)的平面结构", "含3个碳碳双键", "含碳碳三键", "链状结构"], 0,
     "苯是平面正六边形结构，碳碳键是介于单键和双键之间的独特化学键。"),
    (("醇酚",), "乙醇(C₂H₅OH)中决定其化学性质的官能团是（　　）",
     ["羟基(—OH)", "羧基(—COOH)", "碳碳双键", "醛基"], 0,
     "乙醇的官能团是羟基—OH，能与钠反应放出氢气。"),
    (("醛酮",), "能发生银镜反应的官能团是（　　）",
     ["醛基(—CHO)", "羟基(—OH)", "羧基(—COOH)", "碳碳双键"], 0,
     "含醛基的物质能发生银镜反应，可用于检验醛基。"),
    (("卤代烃",), "卤代烃是烃分子中氢原子被（　　）取代后的产物",
     ["卤素原子", "氧原子", "氮原子", "羟基"], 0,
     "卤代烃是烃中氢原子被卤素(F、Cl、Br、I)原子取代的化合物。"),
    (("糖",), "下列糖类中属于单糖的是（　　）",
     ["葡萄糖", "蔗糖", "麦芽糖", "淀粉"], 0,
     "葡萄糖、果糖是单糖；蔗糖、麦芽糖是二糖；淀粉、纤维素是多糖。"),
    (("蛋白质",), "检验蛋白质常用的方法是（　　）",
     ["灼烧闻到烧焦羽毛的气味", "加水溶解", "加酸变红", "加碘变蓝"], 0,
     "蛋白质灼烧有烧焦羽毛的特殊气味；遇浓硝酸变黄(颜色反应)。"),
    (("反应速率", "速率因素", "速率计算"), "下列措施中能加快化学反应速率的是（　　）",
     ["升高温度", "降低温度", "减小压强", "减小浓度"], 0,
     "升高温度、增大浓度、增大压强、加催化剂都能加快反应速率。"),
    (("反应限度", "化学平衡", "平衡移动", "平衡常数", "平衡图像"), "对于可逆反应，达到化学平衡状态时（　　）",
     ["正、逆反应速率相等且各组分浓度不再改变", "反应停止", "正反应速率为零", "反应物完全消耗"], 0,
     "化学平衡时正逆反应速率相等，各组分浓度保持不变，但反应仍在进行。"),
    (("原电池", "化学能", "新型电池"), "原电池是把化学能转化为（　　）的装置",
     ["电能", "热能", "光能", "机械能"], 0,
     "原电池利用自发的氧化还原反应把化学能转化为电能。"),
    (("电解池", "电化学应用", "电化学"), "电解池是把电能转化为（　　）的装置",
     ["化学能", "热能", "光能", "机械能"], 0,
     "电解池在外加电源作用下把电能转化为化学能，如电解水、电镀。"),
    (("电离平衡",), "下列物质属于强电解质的是（　　）",
     ["NaCl", "醋酸", "氨水", "蔗糖"], 0,
     "强电解质在水中完全电离，如强酸、强碱、大多数盐(NaCl)。"),
    (("沉淀溶解",), "下列物质中难溶于水的是（　　）",
     ["BaSO₄", "NaCl", "KNO₃", "Na₂CO₃"], 0,
     "BaSO₄是白色难溶沉淀，常用于检验硫酸根离子。"),
    (("晶体",), "下列物质中属于离子晶体的是（　　）",
     ["NaCl", "干冰(CO₂)", "金刚石", "冰"], 0,
     "NaCl由阴阳离子构成属离子晶体；干冰、冰是分子晶体，金刚石是原子晶体。"),
    (("石油煤",), "石油分馏得到汽油、煤油等，该过程属于（　　）",
     ["物理变化", "化学变化", "氧化反应", "分解反应"], 0,
     "石油分馏利用各成分沸点不同分离，没有新物质生成，属物理变化。"),
]


def _chem_quiz(s, i):
    for entry in _CHEM_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    if "混合物" in s or "纯净物" in s or "分类" in s:
        return _cq("下列物质中属于纯净物的是（　　）",
                   ["蒸馏水", "空气", "海水", "牛奶"], 0,
                   "纯净物由一种物质组成；空气、海水、牛奶都是混合物。")
    if "单质" in s or "化合物" in s or "氧化物" in s:
        return _cq("下列物质中属于氧化物的是（　　）",
                   ["CO₂", "O₂", "KCl", "H₂SO₄"], 0,
                   "氧化物由两元素组成且其一为氧；O₂是单质，KCl无氧，H₂SO₄含三元素。")
    if "空气" in s or "氧气" in s or "制取" in s:
        return _cq("空气中体积分数约为 21% 的气体是（　　）",
                   ["氧气(O₂)", "氮气(N₂)", "二氧化碳", "稀有气体"], 0,
                   "空气中N₂约78%、O₂约21%、CO₂约0.03%。")
    if "分子" in s or "原子" in s or "离子" in s:
        return _cq("保持水的化学性质的最小粒子是（　　）",
                   ["水分子", "氢分子", "氧分子", "氢原子"], 0,
                   "由分子构成的物质，分子是保持化学性质的最小粒子；水由水分子构成。")
    if "元素" in s or "周期表" in s or "化合价" in s:
        return _cq("决定元素种类的是（　　）",
                   ["质子数(核电荷数)", "中子数", "电子数", "相对原子质量"], 0,
                   "元素种类由质子数(核电荷数)决定；同种元素质子数相同。")
    if "方程式" in s or "守恒" in s or "配平" in s:
        return _cq("化学方程式 2H₂ + O₂ 点燃 2H₂O 遵循（　　）",
                   ["质量守恒定律", "能量守恒", "电荷守恒", "体积守恒"], 0,
                   "一切化学反应都遵循质量守恒：反应前后原子种类和数目不变。")
    if "二氧化碳" in s or "碳酸" in s or ("碳" in s and "活动" not in s):
        return _cq("能使澄清石灰水变浑浊的气体是（　　）",
                   ["CO₂", "O₂", "H₂", "N₂"], 0,
                   "CO₂+Ca(OH)₂→CaCO₃↓(白)+H₂O，石灰水变浑浊是检验CO₂的特征反应。")
    if "金属" in s or "活动性" in s or "冶炼" in s:
        return _cq("金属活动性顺序中位于氢前面的金属（　　）",
                   ["能置换酸中的氢", "不能置换氢", "都不与氧气反应", "都比铜稳定"], 0,
                   "H前金属可置换酸中氢（K Ca Na除外与水反应）；顺序：…Fe Sn Pb(H)Cu…")
    if "酸" in s or "碱" in s or "盐" in s or "pH" in s:
        return _cq("下列溶液 pH < 7 的是（　　）",
                   ["稀盐酸", "NaOH溶液", "食盐水", "纯水"], 0,
                   "酸性pH<7、中性=7、碱性>7；盐酸酸性，NaOH碱性，NaCl/水近中性。")
    if "溶液" in s or "溶解度" in s or "溶质" in s:
        return _cq("下列物质放入水中能形成溶液的是（　　）",
                   ["食盐(NaCl)", "面粉", "花生油", "泥土"], 0,
                   "溶液均一稳定；NaCl溶于水成溶液，面粉/油/泥土形成浊液。")
    return None


_BIO_BANK = [
    (("水循环", "水的循环", "生物圈的水循环"), "绿色植物在生物圈水循环中的作用是（　　）",
     ["通过蒸腾作用促进水循环", "通过光合作用制造氧气", "通过呼吸作用释放能量", "通过吸收作用固定二氧化碳"], 0,
     "植物蒸腾作用把根部吸收的水以水蒸气散失到大气，促进生物圈水循环；降水后水经根吸收再蒸腾，周而复始。"),
    (("生物特征",), "下列现象中，能说明生物具有‘应激性’特征的是（　　）",
     ["含羞草受触碰后叶片合拢", "钟乳石慢慢长大", "机器人搬运货物", "潮起潮落"], 0,
     "生物能对外界刺激作出反应(应激性);钟乳石、机器人无生命，不属于生物。"),
    (("生态系统", "食物链"), "在草→兔→狐的食物链中，如果大量捕杀狐，短期内兔的数量将（　　）",
     ["先增多后减少", "一直增多", "一直减少", "保持不变"], 0,
     "狐减少→兔失去天敌先增多→草被大量取食减少→兔因食物不足而减少,体现自我调节。"),
    (("物质循环",), "生态系统中能量流动的特点是（　　）",
     ["单向流动、逐级递减", "循环流动", "双向传递", "逐级递增"], 0,
     "能量沿食物链单向流动、逐级递减(约10%~20%);物质则可循环利用。"),
    (("显微镜",), "用显微镜观察时，若要将视野中左下方的物像移到中央，应将玻片标本向（　　）",
     ["左下方移动", "右上方移动", "左上方移动", "右下方移动"], 0,
     "显微镜成倒像,物像与实物移动方向相反,像在哪个方向就往哪个方向移玻片。"),
    (("植物细胞", "动物细胞", "细胞结构"), "植物细胞有而动物细胞没有的结构是（　　）",
     ["细胞壁、叶绿体和液泡", "细胞膜", "细胞核", "线粒体"], 0,
     "植物细胞特有:细胞壁、叶绿体、液泡;动植物细胞都有膜、质、核、线粒体。"),
    (("细胞分裂",), "细胞分裂过程中，变化最明显、平均分配到两个子细胞中的是（　　）",
     ["染色体", "细胞膜", "细胞质", "液泡"], 0,
     "分裂时染色体先复制再平均分配,保证子细胞染色体数目和亲代相同。"),
    (("光合作用",), "关于光合作用，下列叙述正确的是（　　）",
     ["场所是叶绿体，把光能转化为化学能", "在线粒体中进行", "只在黑暗中进行", "释放CO₂"], 0,
     "光合作用在叶绿体中进行,利用光能把CO₂和H₂O合成有机物并释放O₂,储能。"),
    (("细胞呼吸", "呼吸作用"), "有氧呼吸的主要场所和最终产物分别是（　　）",
     ["线粒体；CO₂和水", "叶绿体；有机物", "细胞核；ATP", "核糖体；蛋白质"], 0,
     "有氧呼吸主要在线粒体进行,彻底分解葡萄糖生成CO₂和H₂O,释放大量能量。"),
    (("蒸腾作用",), "植物蒸腾作用的意义不包括（　　）",
     ["为植物提供有机养料", "促进根吸水和水分向上运输", "降低叶片温度", "促进无机盐运输"], 0,
     "蒸腾拉动水和无机盐上运、降温;提供有机养料是光合作用的功能。"),
    (("酶",), "关于酶的特性，下列说法错误的是（　　）",
     ["酶在反应后被大量消耗", "具有高效性", "具有专一性", "需要适宜温度和pH"], 0,
     "酶是催化剂,反应前后数量和性质不变、可反复使用;具高效性、专一性、需温和条件。"),
    (("ATP",), "细胞中直接为生命活动供能的物质是（　　）",
     ["ATP", "葡萄糖", "脂肪", "蛋白质"], 0,
     "ATP是细胞的直接能源物质,水解释放能量:ATP⇌ADP+Pi+能量;糖脂是储能物质。"),
    (("有丝分裂",), "有丝分裂过程中，染色体数目暂时加倍发生在（　　）",
     ["后期(着丝点分裂)", "间期", "前期", "末期"], 0,
     "后期着丝点分裂、姐妹染色单体分开移向两极,染色体数目暂时加倍。"),
    (("减数分裂",), "经减数分裂形成的一个精细胞，其染色体数目是体细胞的（　　）",
     ["一半", "相同", "两倍", "四分之一"], 0,
     "减数分裂染色体只复制一次、细胞连续分裂两次,配子染色体数减半。"),
    (("DNA结构",), "DNA分子中，与腺嘌呤(A)配对的碱基是（　　）",
     ["胸腺嘧啶(T)", "鸟嘌呤(G)", "胞嘧啶(C)", "尿嘧啶(U)"], 0,
     "碱基互补配对:A-T、G-C;DNA双螺旋两条链反向平行。RNA中A配U。"),
    (("复制",), "DNA复制的方式是（　　）",
     ["半保留复制", "全保留复制", "分散复制", "不复制"], 0,
     "DNA以半保留方式复制:每条子代DNA保留一条母链、新合成一条链。"),
    (("基因表达", "中心法则"), "遗传信息的传递方向(中心法则)一般是（　　）",
     ["DNA→RNA→蛋白质", "蛋白质→RNA→DNA", "RNA→DNA→蛋白质", "DNA→蛋白质→RNA"], 0,
     "中心法则:转录(DNA→mRNA)→翻译(mRNA→蛋白质);部分病毒有逆转录。"),
    (("分离定律",), "基因型为Aa的个体自交，后代的基因型比例是（　　）",
     ["1AA∶2Aa∶1aa", "3∶1", "1∶1", "全部Aa"], 0,
     "Aa自交:配子A、a各1/2,后代基因型1AA∶2Aa∶1aa,表现型显∶隐=3∶1。"),
    (("自由组合",), "基因型AaBb的个体自交，后代表现型的比例是（　　）",
     ["9∶3∶3∶1", "1∶1∶1∶1", "3∶1", "1∶2∶1"], 0,
     "两对等位基因位于非同源染色体上,自由组合,双杂合自交后代表现型9∶3∶3∶1。"),
    (("伴性遗传", "伴性"), "人类红绿色盲(X隐性)遗传的特点是（　　）",
     ["男性患者多于女性", "女性患者多于男性", "只在女性中出现", "与性别无关"], 0,
     "红绿色盲为X染色体隐性遗传,男性只需一个致病基因即患病,故男性患者多于女性。"),
    (("基因突变",), "基因突变的特点不包括（　　）",
     ["定向性(朝有利方向)", "普遍性", "随机性", "低频性"], 0,
     "基因突变具普遍性、随机性、低频性、不定向性、多害少利;是生物变异的根本来源。"),
    (("染色体变异",), "21三体综合征(先天愚型)属于（　　）",
     ["染色体数目变异", "基因突变", "基因重组", "染色体结构变异"], 0,
     "多一条21号染色体属染色体数目变异;可通过显微镜观察染色体检出。"),
    (("育种",), "要快速获得纯合矮秆抗病新品种，最简便的方法是（　　）",
     ["单倍体育种(花药离体培养)", "杂交育种", "诱变育种", "多倍体育种"], 0,
     "单倍体育种明显缩短育种年限,得到的植株经秋水仙素处理即为纯合子。"),
    (("内环境", "稳态"), "人体内环境是指（　　）",
     ["细胞外液(血浆、组织液、淋巴)", "细胞内液", "消化道内的液体", "尿液"], 0,
     "内环境即细胞外液,是细胞与外界物质交换的媒介;稳态是内环境相对稳定。"),
    (("神经调节", "神经体液免疫"), "完成反射活动的结构基础是（　　）",
     ["反射弧", "神经元", "大脑", "脊髓"], 0,
     "反射弧:感受器→传入神经→神经中枢→传出神经→效应器,缺一不可完成反射。"),
    (("体液调节",), "调节人体血糖浓度、能降低血糖的激素是（　　）",
     ["胰岛素", "胰高血糖素", "肾上腺素", "甲状腺激素"], 0,
     "胰岛素(胰岛B细胞)是唯一降血糖激素;胰高血糖素、肾上腺素升血糖,相互拮抗。"),
    (("免疫调节",), "计划免疫接种疫苗预防传染病，从免疫角度看疫苗相当于（　　）",
     ["抗原", "抗体", "病原体的毒素", "淋巴细胞"], 0,
     "疫苗是灭活/减毒的病原体,作为抗原刺激机体产生抗体和记忆细胞,属特异性免疫。"),
    (("种群",), "调查某地蒲公英的种群密度，常用的方法是（　　）",
     ["样方法", "标志重捕法", "抽样检测法", "显微计数法"], 0,
     "样方法适用于植物和活动能力弱的动物;标志重捕法适用于活动能力强的动物。"),
    (("群落",), "关于群落演替，下列说法正确的是（　　）",
     ["从裸岩开始的是初生演替", "弃耕农田是初生演替", "演替方向不受人类影响", "群落结构不随时间变化"], 0,
     "初生演替(裸岩、沙丘)从无到有;次生演替(火烧、弃耕)原有基础上进行,后者较快。"),
    (("生态系统",), "生态系统的组成成分中，能把有机物分解为无机物的是（　　）",
     ["分解者(细菌、真菌)", "生产者", "消费者", "非生物物质"], 0,
     "分解者(腐生细菌真菌)把动植物遗体分解为无机物返还环境,是物质循环的关键。"),
    (("变异",), "生物变异中，能够遗传给后代的是（　　）",
     ["遗传物质改变引起的变异", "只由环境引起的变异", "晒黑的皮肤", "锻炼变粗的肌肉"], 0,
     "由遗传物质(基因、染色体)改变引起的变异可遗传;仅环境引起而遗传物质未变的不遗传。"),
    (("自然选择", "现代进化理论"), "现代生物进化理论认为，生物进化的实质是（　　）",
     ["种群基因频率的改变", "个体的变异", "物种数目增多", "适者生存"], 0,
     "进化实质是种群基因频率的定向改变;自然选择决定进化方向,突变和基因重组提供原材料。"),
    (("细菌",), "细菌与动植物细胞在结构上的主要区别是（　　）",
     ["细菌没有成形的细胞核", "细菌没有细胞壁", "细菌没有细胞质", "细菌有叶绿体"], 0,
     "细菌是原核生物,无成形细胞核(只有拟核)、无核膜包被的细胞核;真菌有真正细胞核。"),
    (("真菌",), "蘑菇、霉菌等真菌的营养方式是（　　）",
     ["异养(腐生或寄生)", "自养", "光合作用", "化能合成"], 0,
     "真菌无叶绿体,不能光合,营腐生或寄生生活;酵母菌可进行发酵。"),
    (("病毒",), "病毒的结构特点是（　　）",
     ["没有细胞结构，由蛋白质外壳和内部遗传物质组成", "由细胞构成", "有细胞核", "能独立生活"], 0,
     "病毒无细胞结构,只有蛋白质外壳和核酸,必须寄生在活细胞内才能繁殖。"),
    (("基因工程",), "基因工程中用于剪切DNA的‘分子手术刀’是（　　）",
     ["限制性核酸内切酶", "DNA连接酶", "解旋酶", "运载体"], 0,
     "基因工程三大工具:限制酶(剪)、DNA连接酶(接)、运载体(质粒等,运)。"),
    (("蛋白质",), "构成蛋白质的基本单位是（　　）",
     ["氨基酸", "葡萄糖", "核苷酸", "脂肪酸"], 0,
     "蛋白质由氨基酸经脱水缩合形成肽链;核酸的基本单位是核苷酸。"),
    (("核酸",), "作为生物体遗传信息携带者的物质是（　　）",
     ["核酸(DNA和RNA)", "蛋白质", "糖类", "脂质"], 0,
     "核酸是一切生物的遗传信息携带者;DNA主要在细胞核,RNA主要在细胞质。"),
    (("生物多样性",), "生物多样性通常包括（　　）",
     ["基因、物种和生态系统多样性", "只有物种多样性", "只有基因多样性", "动物和植物两类"], 0,
     "生物多样性三层次:基因(遗传)多样性、物种多样性、生态系统多样性。"),
]


def _bio_quiz(s, i):
    for entry in _BIO_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    if "细胞" in s or "显微镜" in s:
        return _cq("使用显微镜观察时，镜筒下降（物镜接近玻片）应（　　）眼睛注视物镜",
                   ["顺时针转动粗准焦螺旋", "逆时针转动粗准焦螺旋", "任意方向", "不需调节"], 0,
                   "调焦时眼盯物镜，顺时针转粗准焦螺旋使镜筒缓缓下降，避免压碎玻片。")
    if "光合" in s:
        return _cq("绿色植物进行光合作用的场所是（　　）",
                   ["叶绿体", "线粒体", "细胞核", "液泡"], 0,
                   "光合作用在叶绿体中进行，将CO₂和水转化为有机物并释放O₂，储存能量。")
    if "呼吸" in s and "道" not in s:
        return _cq("植物呼吸作用的主要场所是（　　）",
                   ["线粒体", "叶绿体", "细胞膜", "细胞壁"], 0,
                   "呼吸作用在线粒体中进行，分解有机物释放能量，与动物细胞相同。")
    if "蒸腾" in s:
        return _cq("植物蒸腾作用散失水分的主要器官是（　　）",
                   ["叶片", "根", "茎", "花"], 0,
                   "蒸腾作用主要通过叶片气孔散失水分，对运输水分和降温有重要意义。")
    if "种子" in s or "被子" in s or "裸子" in s:
        return _cq("下列植物中属于裸子植物的是（　　）",
                   ["松树", "桃树", "水稻", "苹果树"], 0,
                   "裸子植物种子裸露无果皮包被：松、杉、柏、银杏；桃/稻/苹果是被子植物。")
    if "藻类" in s or "苔藓" in s or "蕨类" in s:
        return _cq("下列靠孢子繁殖、无真正根、茎、叶分化的是（　　）",
                   ["藻类植物(如海带)", "蕨类植物", "裸子植物", "被子植物"], 0,
                   "藻类植物结构最简单，无根茎叶分化、无维管束，靠孢子繁殖。")
    if "消化" in s:
        return _cq("人体消化和吸收的主要场所是（　　）",
                   ["小肠", "胃", "大肠", "口腔"], 0,
                   "小肠长、有皱襞和绒毛、含多种消化液，是消化吸收的主要场所。")
    if "呼吸" in s and "道" in s:
        return _cq("人体呼吸系统中气体交换的主要场所是（　　）",
                   ["肺(肺泡)", "气管", "鼻腔", "咽喉"], 0,
                   "肺由大量肺泡构成，是氧气和二氧化碳交换的场所。")
    if "血液循环" in s or "体循环" in s or "肺循环" in s or "血液" in s or "心脏" in s or "血管" in s:
        return _cq("血液中负责运输氧气的细胞是（　　）",
                   ["红细胞", "白细胞", "血小板", "血浆"], 0,
                   "红细胞含血红蛋白主要运输O₂；白细胞免疫，血小板止血。")
    if "神经" in s:
        return _cq("神经系统结构和功能的基本单位是（　　）",
                   ["神经元(神经细胞)", "神经胶质", "脑", "脊髓"], 0,
                   "神经元是神经系统结构与功能的基本单位，接受刺激、传导兴奋。")
    if "遗传" in s or "DNA" in s or "基因" in s:
        return _cq("控制生物性状的基本遗传单位是（　　）",
                   ["基因", "染色体", "蛋白质", "细胞"], 0,
                   "基因是有遗传效应的DNA片段，控制性状；染色体由DNA和蛋白质组成。")
    if "生态" in s or "食物链" in s or "生物圈" in s:
        return _cq("在生态系统中生产者主要是指（　　）",
                   ["绿色植物", "动物", "细菌", "真菌"], 0,
                   "生产者(主要是绿色植物)通过光合作用制造有机物，是生态系统的基石。")
    if "进化" in s or "多样" in s:
        return _cq("达尔文进化理论认为生物进化的主要动力是（　　）",
                   ["自然选择", "用进废退", "人工选择", "突变方向"], 0,
                   "达尔文自然选择学说：过度繁殖、生存斗争、遗传变异、适者生存。")
    return None


_CN_TEXT_BANK = [
    (("曹冲称象",), "《曹冲称象》中，曹冲想出的称象办法是（　　）",
     ["把大象赶到船上，记下船沉的位置，再用石头装船到同一记号，称石头重量", "直接把大象放在大秤上称", "把大象切成块称", "用尺子量大象的身高推算重量"], 0,
     "曹冲用‘等量替换’：船装象刻记号，再装石到同记号，石重即象重，体现浮力与转化思想。"),
    (("司马光",), "《司马光》中，司马光救落水同伴的方法是（　　）",
     ["搬石头砸破水缸，让水流出来", "跳进水里把同伴拉出来", "跑去找大人", "用绳子把同伴拉上来"], 0,
     "司马光沉着机智，砸缸放水救出伙伴；故事出自《宋史》，赞扬临危不乱。"),
    (("坐井观天", "观天"), "寓言《坐井观天》告诉我们的道理是（　　）",
     ["看待事物要全面，不能眼界狭窄、盲目自大", "青蛙很聪明", "天本来就只有井口大", "待在井里最安全"], 0,
     "青蛙只看到井口大的天，比喻眼界狭小、见识有限;劝人开阔视野、全面看问题。"),
    (("狐假虎威",), "成语‘狐假虎威’的意思是（　　）",
     ["依仗别人的势力来欺压人", "狐狸真的比老虎威风", "老虎怕狐狸", "狐狸和老虎是朋友"], 0,
     "狐狸借老虎的威风吓跑百兽，比喻依仗别人的权势欺压他人。"),
    (("亡羊补牢",), "寓言《亡羊补牢》说明的道理是（　　）",
     ["出了问题及时补救，还不算晚", "羊圈破了没关系", "丢羊是命中注定", "不用修羊圈"], 0,
     "羊丢了再修圈，比喻出了问题及时设法补救，可以防止继续受损失(‘未为晚也’)。"),
    (("揠苗助长", "拔苗助长"), "寓言《揠苗助长》告诉我们的道理是（　　）",
     ["做事要遵循规律，不能急于求成", "苗长得快是好事", "拔高禾苗能增产", "不用管禾苗"], 0,
     "农夫拔苗帮其长高，苗却枯死，说明违反事物发展规律、急于求成反而坏事。"),
    (("刻舟求剑",), "寓言《刻舟求剑》讽刺的是（　　）",
     ["拘泥成法、不知随情况变化而变通的人", "划船技术好的人", "剑掉水里很可惜", "在船上刻记号很聪明"], 0,
     "船已行而剑不行，按船上记号找剑必然找不到，讽刺墨守成规、不知变通。"),
    (("自相矛盾",), "成语‘自相矛盾’出自（　　）",
     ["一个人既夸矛无坚不摧又夸盾无物可破，前后抵触", "两支军队交战", "矛和盾都是武器", "买卖兵器的商人"], 0,
     "楚人誉矛‘无盾不穿’又誉盾‘无矛可穿’，说话前后抵触，比喻言行自相冲突。"),
    (("画蛇添足",), "成语‘画蛇添足’比喻（　　）",
     ["做了多余的事，反而不恰当", "把蛇画得很像", "多画脚是创新", "画画要认真"], 0,
     "给蛇添脚反失酒，比喻多此一举、弄巧成拙。"),
    (("掩耳盗铃",), "寓言《掩耳盗铃》讽刺的是（　　）",
     ["自己欺骗自己、以为别人也听不见的人", "小偷很聪明", "铃铛声音小", "偷铃要小心"], 0,
     "捂住自己耳朵去偷铃，以为别人也听不见，比喻自欺欺人。"),
    (("守株待兔",), "寓言《守株待兔》告诫我们（　　）",
     ["不能把偶然当必然、妄想不劳而获", "等兔子很有效", "树桩很重要", "农夫很聪明"], 0,
     "农夫偶得撞死兔，便守株待兔，不知变通、妄想侥幸，终无收获。"),
    (("滥竽充数",), "成语‘滥竽充数’比喻（　　）",
     ["没有真本领的人混在行家里充数", "吹竽的人很多", "南郭先生很会吹", "竽是一种好乐器"], 0,
     "南郭先生不会吹竽却混在乐队里，比喻无真才实学的人混充有本领。"),
    (("愚公移山",), "寓言《愚公移山》赞颂的精神是（　　）",
     ["不怕困难、坚持不懈、人定胜天", "山很容易被移走", "智叟很聪明", "搬家更划算"], 0,
     "愚公率子孙挖山不止，终感动天帝相助，赞颂持之以恒、敢于战胜困难的精神。"),
    (("精卫填海",), "神话《精卫填海》中精卫是一只（　　）",
     ["衔石填海、矢志不渝的小鸟(炎帝之女化身)", "大鱼", "神龙", "凤凰"], 0,
     "精卫是炎帝女儿溺亡后化鸟，衔木石填东海，象征不畏艰难、矢志不移。"),
    (("大禹治水",), "大禹治水成功的根本方法是（　　）",
     ["‘疏’（疏导河道）而非‘堵’", "筑更高的堤坝围堵", "祈求神灵", "迁走百姓"], 0,
     "鲧用‘堵’失败，禹改用‘疏导’治水成功，三过家门而不入，成千古佳话。"),
    (("后羿射日", "羿"), "神话《后羿射日》中后羿射下了（　　）",
     ["九个太阳，留一个普照人间", "全部十个太阳", "一个太阳", "月亮"], 0,
     "天有十日炙烤大地，后羿射落九日留其一，解民于苦难，是英雄神话。"),
    (("女娲",), "神话中‘女娲补天’‘女娲造人’，女娲是（　　）",
     ["创世女神，抟土造人、炼石补天", "一位普通农妇", "天帝的妻子", "一只神鸟"], 0,
     "女娲是中国上古创世女神，抟黄土造人、熔五彩石补天，体现先民想象。"),
    (("夸父",), "神话《夸父逐日》中夸父（　　）",
     ["追逐太阳、道渴而死，手杖化为桃林", "追到了太阳", "被太阳烧伤", "放弃了追逐"], 0,
     "夸父追赶太阳渴死，弃杖化为邓林(桃林)，表现古代先民征服自然的渴望。"),
    (("盘古",), "神话《盘古开天地》中，盘古死后身体化成了（　　）",
     ["日月山川、草木万物", "一座金山", "一片大海", "一群飞鸟"], 0,
     "盘古用斧劈开混沌，死后气息成风云、声为雷、目为日月、身化山川，是创世神话。"),
    (("嫦娥",), "神话《嫦娥奔月》中嫦娥飞月是因为（　　）",
     ["吞下了后羿的不死药", "被风吹上天", "乘飞船", "被玉兔带走"], 0,
     "嫦娥偷食后羿从西王母处求得的不死药，身轻飞入月宫，成为月神。"),
    (("哪吒",), "神话《哪吒闹海》中哪吒制服的恶势力是（　　）",
     ["东海龙王父子", "天宫玉帝", "二郎神", "孙悟空"], 0,
     "哪吒挺身而出，打死夜叉、打死龙王三太子、抽龙筋，反抗龙王欺压，是少年英雄。"),
    (("猴子捞月",), "《猴子捞月》这则寓言告诉我们（　　）",
     ["遇事要弄清真相，不要盲从", "月亮真的掉水里了", "猴子很聪明", "捞月很容易"], 0,
     "猴子见水中月影便下井去捞，徒劳无功，告诫人不要被假象迷惑、盲目跟风。"),
    (("寒号鸟",), "《寒号鸟》中寒号鸟最终冻死，是因为它（　　）",
     ["只顾玩乐、得过且过、不及时做窝", "窝被风吹走", "天气太冷", "找不到食物"], 0,
     "寒号鸟‘今天玩明天做窝’、得过且过，终在寒夜冻死，劝人勤劳有计划。"),
    (("小蝌蚪找妈妈",), "《小蝌蚪找妈妈》中小蝌蚪长大后变成了（　　）",
     ["青蛙", "小鱼", "乌龟", "鸭子"], 0,
     "蝌蚪先长后腿、再长前腿、尾消失、变成青蛙，反映两栖动物变态发育。"),
    (("小马过河",), "《小马过河》说明的道理是（　　）",
     ["遇事要亲自尝试，不能只听别人说", "河水很深", "老牛说得对", "松鼠说得对"], 0,
     "老牛说浅、松鼠说深，小马亲自试才知深浅——实践出真知、独立思考。"),
    (("狐假虎威",), "《狐狸和乌鸦》中狐狸骗走肉用的是（　　）",
     ["奉承夸乌鸦歌声好听", "武力抢夺", "用钱买", "交换"], 0,
     "狐狸夸乌鸦‘嗓子好、唱歌动听’，乌鸦开口肉掉下，讽刺爱听奉承话易上当。"),
    (("乌鸦喝水",), "《乌鸦喝水》中乌鸦喝到水的方法是（　　）",
     ["往瓶里一颗颗投石子，使水位升高", "把瓶推倒", "用吸管", "等下雨"], 0,
     "乌鸦投石入瓶、水位上升而喝到水，体现遇事动脑、利用体积排开。"),
    (("咕咚",), "童话《咕咚》中‘咕咚’其实是（　　）",
     ["成熟果子掉进湖里的声音", "一只怪兽", "地震", "雷声"], 0,
     "动物们没看清就跟着跑，原是木瓜落水声，告诫人弄清事实、不盲从。"),
    (("小壁虎借尾巴",), "《小壁虎借尾巴》中小壁虎最后（　　）",
     ["自己长出了新尾巴", "借到了牛尾巴", "借到了燕子尾巴", "永远没了尾巴"], 0,
     "壁虎尾巴有再生能力，断尾逃生后可再生；不同动物尾巴功能不同。"),
    (("雪孩子",), "童话《雪孩子》中雪孩子为救小白兔（　　）",
     ["化作水汽飞上天空", "变成了冰", "躲起来", "变成了雪人"], 0,
     "雪孩子冲进火海救兔，自己融化成水、蒸发升天，歌颂舍己救人。"),
    (("棉花姑娘",), "《棉花姑娘》中治好了棉花姑娘蚜虫病害的是（　　）",
     ["七星瓢虫", "燕子", "啄木鸟", "青蛙"], 0,
     "七星瓢虫吃蚜虫，是益虫;不同动物吃不同害虫，体现生物防治。"),
    (("小公鸡和小鸭子",), "《小公鸡和小鸭子》说明（　　）",
     ["朋友间要互相帮助", "公鸡比鸭子强", "鸭子不会游泳", "公鸡会游泳"], 0,
     "小公鸡给小鸭子捉虫、小鸭子救落水公鸡，体现团结友爱、优势互补。"),
    (("树之歌", "树"), "《树之歌》中提到‘银杏水杉’被称为（　　）",
     ["活化石", "速生树", "果树", "观赏花"], 0,
     "银杏、水杉是古老孑遗植物，被称为‘活化石’，十分珍贵。"),
    (("拍手歌",), "《拍手歌》倡导我们要（　　）",
     ["保护动物、与动物做朋友", "多拍手", "捕捉动物", "少走路"], 0,
     "拍手歌以儿歌形式介绍动物，呼吁爱护动物、保护生物多样性。"),
    (("田家四季歌",), "《田家四季歌》描写了（　　）",
     ["农民一年四季的农事活动", "城市生活", "学校生活", "动物世界"], 0,
     "按春种、夏忙、秋收、冬藏顺序写农事，体现农业劳动的辛劳与节律。"),
    (("葡萄沟",), "《葡萄沟》写的是我国哪个地方的葡萄很有名（　　）",
     ["新疆吐鲁番", "山东", "海南", "黑龙江"], 0,
     "新疆吐鲁番葡萄沟盛产葡萄，晾制葡萄干，是西北特色农业代表。"),
    (("日月潭",), "《日月潭》描写的是我国（　　）的著名湖泊",
     ["台湾省", "浙江省", "江西省", "湖南省"], 0,
     "日月潭是台湾省最大的天然湖泊，风景秀丽，北半圆如日、南半圆如月。"),
    (("黄山奇石", "黄山"), "《黄山奇石》中‘仙人指路’‘猴子观海’描写的是（　　）",
     ["黄山千姿百态的怪石", "动物园", "雕塑", "画作"], 0,
     "黄山以奇松、怪石、云海、温泉‘四绝’闻名，怪石形态逼真。"),
    (("望庐山瀑布", "瀑布"), "‘飞流直下三千尺，疑是银河落九天’出自（　　）",
     ["李白《望庐山瀑布》", "杜甫的诗", "白居易的诗", "苏轼的词"], 0,
     "李白用夸张和比喻写庐山瀑布的雄伟，展现浪漫主义风格。"),
    (("登鹳雀楼", "鹳雀楼"), "‘欲穷千里目，更上一层楼’出自（　　）",
     ["王之涣《登鹳雀楼》", "李白的诗", "王维的诗", "孟浩然的诗"], 0,
     "王之涣以登高望远阐明‘站得高看得远’的哲理，劝人进取。"),
    (("静夜思",), "‘举头望明月，低头思故乡’出自李白的（　　）",
     ["《静夜思》", "《春晓》", "《登鹳雀楼》", "《悯农》"], 0,
     "《静夜思》写游子月夜思乡，语言浅白、情深意切，家喻户晓。"),
    (("春晓",), "‘春眠不觉晓，处处闻啼鸟’出自（　　）",
     ["孟浩然《春晓》", "李白《静夜思》", "杜甫《绝句》", "王维《鹿柴》"], 0,
     "孟浩然《春晓》写春日清晨的所闻所感，流露爱春惜春之情。"),
    (("赠汪伦",), "‘桃花潭水深千尺，不及汪伦送我情’出自（　　）",
     ["李白《赠汪伦》", "王维的诗", "高适的诗", "王昌龄的诗"], 0,
     "李白以潭水之深反衬友情之厚，是送别诗的名句。"),
    (("咏柳",), "‘不知细叶谁裁出，二月春风似剪刀’出自贺知章的（　　）",
     ["《咏柳》", "《春晓》", "《小池》", "《村居》"], 0,
     "贺知章以‘剪刀’喻春风，写柳叶纤巧，咏物兼赞春光。"),
    (("晓出净慈寺送林子方", "净慈寺"), "‘接天莲叶无穷碧，映日荷花别样红’写的是（　　）",
     ["西湖夏日荷花", "庐山瀑布", "泰山日出", "草原风光"], 0,
     "杨万里写杭州西湖六月荷花的壮美，色彩鲜明、意境开阔。"),
    (("村居",), "‘草长莺飞二月天，拂堤杨柳醉春烟’出自高鼎的（　　）",
     ["《村居》", "《春晓》", "《咏柳》", "《小池》"], 0,
     "《村居》写早春乡村景色与儿童放纸鸢的欢乐，充满生活气息。"),
    (("小池",), "‘小荷才露尖尖角，早有蜻蜓立上头’出自杨万里的（　　）",
     ["《小池》", "《晓出净慈寺》", "《村居》", "《咏柳》"], 0,
     "杨万里《小池》捕捉初夏小荷初绽的细微生机，清新俏皮。"),
    (("所见",), "‘牧童骑黄牛，歌声振林樾’出自袁枚的（　　）",
     ["《所见》", "《村居》", "《小池》", "《舟夜书所见》"], 0,
     "《所见》写牧童骑牛唱歌、忽见鸣蝉屏息欲捕的童趣。"),
    (("舟夜书所见", "舟夜"), "‘月黑见渔灯，孤光一点萤’出自查慎行的（　　）",
     ["《舟夜书所见》", "《所见》", "《舟夜》", "《夜书所见》"], 0,
     "查慎行写舟中所见：黑暗中一点渔灯如萤火，以动衬静、意境清幽。"),
    (("宿新市徐公店", "徐公店"), "‘儿童急走追黄蝶，飞入菜花无处寻’出自杨万里的（　　）",
     ["《宿新市徐公店》", "《小池》", "《村居》", "《所见》"], 0,
     "写乡村儿童追蝶、蝶入菜花难辨的活泼场景，童趣盎然。"),
    (("四时田园杂兴", "田园杂兴"), "‘童孙未解供耕织，也傍桑阴学种瓜’出自范成大的（　　）",
     ["《四时田园杂兴》", "《村居》", "《小池》", "《所见》"], 0,
     "范成大写农村夏日繁忙与儿童模仿劳作的质朴画面。"),
    (("司马光",), "《司马光》选自（　　）",
     ["《宋史》", "《史记》", "《资治通鉴》", "《论语》"], 0,
     "司马光砸缸故事载于《宋史》，司马光后来主编《资治通鉴》。"),
    (("少年闰土", "闰土"), "《少年闰土》选自鲁迅的小说（　　）",
     ["《故乡》", "《狂人日记》", "《孔乙己》", "《祝福》"], 0,
     "闰土是鲁迅小说《故乡》中的人物，反映旧社会农民的悲苦与隔膜。"),
    (("草船借箭", "借箭"), "《草船借箭》中‘借箭’的是（　　）",
     ["诸葛亮", "周瑜", "曹操", "鲁肃"], 0,
     "赤壁之战前，诸葛亮用草船受箭，巧借曹操之箭，出自《三国演义》。"),
    (("景阳冈",), "《景阳冈》中在冈上打死猛虎的英雄是（　　）",
     ["武松", "林冲", "鲁智深", "宋江"], 0,
     "武松景阳冈打虎出自《水浒传》，表现其勇武与豪爽。"),
    (("猴王出世", "石猴", "美猴王"), "《猴王出世》中的石猴后来成为（　　）",
     ["美猴王/孙悟空", "唐僧", "猪八戒", "沙僧"], 0,
     "出自《西游记》，石猴勇探水帘洞被尊为美猴王，即孙悟空。"),
    (("红楼春趣", "红楼梦"), "《红楼春趣》写的是（《红楼梦》中）众人（　　）",
     ["放风筝的趣事", "吃螃蟹", "赏雪吟诗", "划船"], 0,
     "节选写贾府儿女春日放风筝，出自曹雪芹《红楼梦》。"),
    (("将相和",), "《将相和》中‘负荆请罪’的是（　　）",
     ["廉颇向蔺相如请罪", "蔺相如向廉颇请罪", "秦王", "赵王"], 0,
     "廉颇知错，背负荆条向蔺相如请罪，将相和好，共保赵国。"),
    (("牛郎织女",), "民间故事《牛郎织女》与哪个节日有关（　　）",
     ["七夕节", "中秋节", "端午节", "春节"], 0,
     "牛郎织女被银河分隔，每年七夕鹊桥相会，是七夕节的由来。"),
    (("猎人海力布", "海力布"), "《猎人海力布》中海力布为救乡亲（　　）",
     ["说出秘密变成石头", "逃走了", "杀了龙", "藏起来"], 0,
     "海力布得知洪水消息，为劝乡亲搬家说出能听懂动物语言的秘密，自己化为石头。"),
    (("圆明园", "毁灭"), "圆明园被焚毁发生在（　　）",
     ["第二次鸦片战争(英法联军)", "鸦片战争", "甲午战争", "八国联军侵华时"], 0,
     "1860年英法联军劫掠并焚毁圆明园，是中华文明的重大损失。"),
    (("少年中国说",), "‘少年强则国强’出自梁启超的（　　）",
     ["《少年中国说》", "《变法通议》", "《饮冰室合集》", "《三省条约》"], 0,
     "梁启超在《少年中国说》中抒写对少年中国的热望，激励青年奋发。"),
    (("狼牙山五壮士",), "‘狼牙山五壮士’表现的是（　　）",
     ["抗日英雄宁死不屈", "解放战争故事", "古代战役", "抗美援朝"], 0,
     "五壮士完成掩护任务后跳崖殉国，是抗日战争中的英雄群像。"),
    (("黄继光",), "英雄黄继光的事迹发生在（　　）",
     ["抗美援朝战争", "抗日战争", "解放战争", "对越自卫反击战"], 0,
     "黄继光在抗美援朝中用胸膛堵敌机枪眼而牺牲，是特级英雄。"),
    (("手术台就是阵地", "白求恩"), "‘把手术台当作阵地’的是国际主义战士（　　）",
     ["白求恩", "柯棣华", "斯诺", "魏特琳"], 0,
     "加拿大医生白求恩来华支援抗战，把手术台当阵地，体现国际主义精神。"),
    (("为人民服务",), "《为人民服务》是毛泽东在中央警卫团追悼（　　）大会上的演讲",
     ["张思德", "雷锋", "焦裕禄", "王进喜"], 0,
     "张思德烧炭牺牲，毛泽东发表《为人民服务》，阐明宗旨。"),
    (("竹节人",), "《竹节人》回忆的是（　　）",
     ["童年用竹节做玩具、斗竹节人的游戏", "做风筝", "玩陀螺", "下棋"], 0,
     "课文以童年自制竹节人、课上课下斗玩的趣事，表达对纯真童年的怀念。"),
    (("桥",), "微型小说《桥》中老支书（　　）",
     ["在洪水中把生的希望让给村民、父子牺牲", "自己先逃生", "弃村民而去", "只顾财物"], 0,
     "老汉作为村党支部书记，在洪灾中组织撤离、先人后己，父子双双牺牲。"),
    (("穷人",), "《穷人》的作者是（　　）",
     ["列夫·托尔斯泰", "契诃夫", "高尔基", "屠格涅夫"], 0,
     "俄国作家列夫·托尔斯泰的《穷人》写桑娜收养邻家孤儿，歌颂善良。"),
    (("只有一个地球",), "《只有一个地球》呼吁我们（　　）",
     ["珍惜资源、保护地球", "多开采矿产", "移民火星", "不限排污"], 0,
     "课文说明地球唯一且脆弱，号召珍惜资源、保护环境。"),
    (("伯牙鼓琴", "高山流水"), "‘高山流水’比喻（　　）",
     ["知音难觅或乐曲高妙", "山水风景", "爬山涉水", "朋友很多"], 0,
     "伯牙善鼓琴，钟子期善听，子期死伯牙破琴绝弦，喻知音或乐曲高妙。"),
    (("书戴嵩画牛",), "《书戴嵩画牛》告诉我们（　　）",
     ["观察要实践、不可凭空臆断", "画画很容易", "牛都画错", "牧童不懂画"], 0,
     "牧童指出名画中牛斗时尾巴夹腿而非翘起，说明实践出真知、观察要细致。"),
    (("学弈",), "《学弈》说明学习要（　　）",
     ["专心致志，不能三心二意", "聪明就行", "多拜师", "少练习"], 0,
     "两人同学棋，一人专心、一人分心，结果迥异，强调专心的重要。"),
    (("两小儿辩日",), "《两小儿辩日》中孔子（　　）",
     ["不能决也(承认不知)", "给出了答案", "批评两儿", "走开了"], 0,
     "两小儿争论太阳远近，孔子‘不能决’，体现求实、知之为不知的态度。"),
    (("囊萤夜读", "萤"), "‘囊萤夜读’的主人公是（　　）",
     ["车胤", "孙康", "匡衡", "李白"], 0,
     "车胤家贫，囊萤照明夜读;与‘映雪’(孙康)并称，赞刻苦求学。"),
    (("铁杵成针",), "‘铁杵磨成针’比喻（　　）",
     ["只要有恒心，再难的事也能做成", "针很容易磨", "李白很勤劳", "老妇人很闲"], 0,
     "老妪磨铁杵欲作针，感化李白，喻持之以恒终能成功。"),
    (("精卫填海",), "《王戎不取道旁李》中王戎不摘李是因为（　　）",
     ["判断‘树在道边而多子，必是苦李’", "他不渴", "李子是别人的", "他害羞"], 0,
     "王戎推理:道边李树多果必苦(否则早被摘光)，体现善于观察推理。"),
    (("西门豹",), "《西门豹治邺》中西门豹破除‘河伯娶亲’靠（　　）",
     ["将巫婆官绅投入河中、以子之矛攻子之盾", "直接下令禁止", "求雨", "花钱消灾"], 0,
     "西门豹将计就计，把巫婆、官绅头子投入漳河，破除迷信、兴修水利。"),
    (("扁鹊", "治病"), "‘讳疾忌医’出自（　　）的故事",
     ["蔡桓公不听扁鹊劝告而病重身亡", "华佗", "张仲景", "李时珍"], 0,
     "扁鹊屡劝蔡桓公治病被拒，终病入骨髓而死，喻隐瞒缺点、拒不改正。"),
    (("纪昌学射",), "《纪昌学射》说明学习要（　　）",
     ["从基本功练起、持之以恒", "先学技巧", "靠天赋", "多换老师"], 0,
     "纪昌先练不眨眼的眼力、再看小如大，终成神射手，强调夯实基础。"),
    (("腊八粥",), "《腊八粥》描写的是（　　）",
     ["腊八节煮腊八粥的民俗与亲情", "中秋赏月", "端午赛龙舟", "春节守岁"], 0,
     "沈从文写孩童盼吃腊八粥的馋样与家庭温情，充满生活气息。"),
    (("匆匆",), "《匆匆》的作者是（　　）",
     ["朱自清", "老舍", "巴金", "冰心"], 0,
     "朱自清《匆匆》以设问叹时光易逝，劝人惜时奋进。"),
    (("春",), "《春》的作者是（　　）",
     ["朱自清", "鲁迅", "郭沫若", "茅盾"], 0,
     "朱自清散文《春》细腻描绘春草、春花、春雨，充满生机。"),
    (("背影",), "《背影》中令作者动容的是父亲（　　）",
     ["爬月台买橘子的背影", "写信", "说话", "送别的话"], 0,
     "朱自清借父亲翻越月台买橘的‘背影’写父子深情，质朴感人。"),
    (("济南的冬天",), "《济南的冬天》的作者是（　　）",
     ["老舍", "朱自清", "冰心", "叶圣陶"], 0,
     "老舍写济南冬天‘温晴’如摇篮，语言平易亲切。"),
    (("草原",), "《草原》的作者是（　　）",
     ["老舍", "茅盾", "巴金", "郭沫若"], 0,
     "老舍写草原风光与蒙古族同胞的热情，体现民族团结。"),
    (("猫", "母鸡",), "《猫》《母鸡》的作者是（　　）",
     ["老舍", "丰子恺", "叶圣陶", "冰心"], 0,
     "老舍以细腻观察写猫的古怪、母鸡的负责，充满生活情趣。"),
    (("白鹅", "鹅"), "《白鹅》的作者是（　　）",
     ["丰子恺", "老舍", "叶圣陶", "冰心"], 0,
     "丰子恺写白鹅‘高傲’的步态、叫声，幽默风趣。"),
    (("海上日出",), "《海上日出》的作者是（　　）",
     ["巴金", "茅盾", "老舍", "冰心"], 0,
     "巴金写海上日出的壮美变化，表达对光明的向往。"),
    (("记金华的双龙洞", "双龙洞"), "《记金华的双龙洞》的作者是（　　）",
     ["叶圣陶", "老舍", "巴金", "丰子恺"], 0,
     "叶圣陶按游览顺序写双龙洞的奇景与‘孔隙’之险。"),
    (("乡下人家",), "《乡下人家》描绘的是（　　）",
     ["乡村自然质朴的生活画面", "城市高楼", "校园", "军营"], 0,
     "陈醉云写瓜藤、鲜花、鸡鸭、晚饭，展现乡村独特迷人的风景。"),
    (("天窗",), "《天窗》中‘天窗’给孩子们带来（　　）",
     ["想象世界的乐趣", "阳光", "雨水", "睡觉的地方"], 0,
     "茅盾写雨天夜晚从天窗看世界，激发儿童无尽遐想。"),
    (("绿",), "诗歌《绿》的作者是（　　）",
     ["艾青", "冰心", "郭沫若", "徐志摩"], 0,
     "艾青《绿》用丰富绿色写春天的生机与诗人的想象。"),
    (("繁星",), "《繁星》的作者是（　　）",
     ["冰心", "巴金", "叶圣陶", "老舍"], 0,
     "冰心散文诗《繁星》讴歌母爱、童真与自然。"),
    (("白桦",), "《白桦》是一首（　　）",
     ["外国(俄罗斯)抒情诗，赞白桦高洁", "中国古诗", "散文", "童话"], 0,
     "苏联诗人叶赛宁写白桦的秀美与高洁，寄托思乡。"),
    (("在天晴了的时候",), "《在天晴了的时候》的作者是（　　）",
     ["戴望舒", "艾青", "冰心", "徐志摩"], 0,
     "戴望舒写雨后初晴的小径漫步，清新恬淡。"),
    (("文言文", "两小儿", "学弈", "伯牙", "书戴嵩", "囊萤", "铁杵", "纪昌", "西门豹", "扁鹊"), "下列加点词‘汤’在‘及其日中如探汤’中意思是（　　）",
     ["热水", "菜汤", "米汤", "汤药"], 0,
     "文言中‘汤’多指热水(如‘赴汤蹈火’)；‘如探汤’即像伸手进热水，形容热。"),
]


def _chinese_quiz(s, i):
    for entry in _CN_TEXT_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    if "拼音" in s or "字音" in s or "多音" in s:
        return _cq("下列加点字注音全部正确的一组是（　　）",
                   ["静谧(mì) 炽热(chì)", "纤细(qiān) 亘古(gèng)", "稽首(qǐ) 伫立(chù)", "憎恶(è) 哺育(pǔ)"], 0,
                   "纤xiān、亘gèn、伫zhù、恶wù、哺bǔ；正确项读音无误。")
    if "修辞" in s or "比喻" in s or "拟人" in s or "排比" in s:
        return _cq("‘春天像个害羞的小姑娘’运用的修辞手法是（　　）",
                   ["比喻", "拟人", "夸张", "排比"], 0,
                   "把‘春天’比作‘小姑娘’是比喻(暗喻)；拟人是赋予物人的动作情感。")
    if "古诗" in s or "诗词" in s or "文言" in s or "默写" in s:
        return _cq("‘海内存知己’的下一句是（　　）",
                   ["天涯若比邻", "天涯共此时", "千里共婵娟", "低头思故乡"], 0,
                   "王勃《送杜少府之任蜀州》：海内存知己，天涯若比邻。")
    if "作者" in s or "朝代" in s or "名著" in s:
        return _cq("《红楼梦》的作者是（　　）",
                   ["曹雪芹", "罗贯中", "施耐庵", "吴承恩"], 0,
                   "《红楼梦》作者曹雪芹；罗贯中《三国》、施耐庵《水浒》、吴承恩《西游》。")
    if "阅读" in s or "理解" in s:
        return _cq("概括文章主要内容时，最恰当的做法是（　　）",
                   ["理清要素(谁+做什么+结果)", "只看标题猜", "抄第一段", "只记好词"], 0,
                   "概括需抓住人物、事件、结果等要素，语言简洁。")
    if "文言" in s or "寓言" in s or "神话" in s or "传说" in s or "故事" in s or "课文" in s:
        return _cq("学习文言文最重要的方法是（　　）",
                   ["借助注释疏通文意", "只背生字", "跳过不读", "只看翻译不思考"], 0,
                   "文言文需借助注释、联系上下文理解词句，再把握文意。")
    if "王戎" in s:
        return _cq("《王戎不取道旁李》中王戎不摘李是因为（　　）",
                   ["推断‘道边多子必苦李’", "不喜欢李子", "李子有毒", "太矮摘不到"], 0,
                   "王戎由‘树在道边而多子’推断必是苦李，体现善于观察思考。")
    if "司马光" in s:
        return _cq("《司马光》中救落水同伴的方法是（　　）",
                   ["砸破水缸放水", "爬树喊人", "跳下去拉", "推倒墙壁"], 0,
                   "司马光砸缸让水流走救出同伴，临危不乱、机智。")
    if "精卫" in s or "填海" in s:
        return _cq("‘精卫填海’赞扬了（　　）",
                   ["不畏艰难、意志坚定", "聪明机智", "勤俭节约", "团结协作"], 0,
                   "精卫衔石填海，象征意志坚定、持之以恒的精神。")
    if "拼音" in s or "韵母" in s or "声母" in s or "标调" in s or "拼读" in s or "音节" in s or "儿化" in s:
        return _cq("下列音节中，韵母是‘a’的是（　　）",
                   ["bà(爸)", "bō(波)", "bī(逼)", "bù(布)"], 0,
                   "bà的韵母是a；bō是o，bī是i，bù是u。")
    if "日月" in s or "金木" in s or "口耳" in s or "天地人" in s or "水火" in s or "象形" in s or "会意" in s:
        return _cq("‘日、月、水、火’这类字，从造字法看属于（　　）",
                   ["象形字", "形声字", "指事字", "会意字"], 0,
                   "日、月像实物形状，是象形字；如‘明’‘林’是会意，‘河’是形声。")
    if "口语交际" in s:
        _name = s.replace("口语交际：", "").replace("口语交际", "")
        return _cq(f"进行口语交际‘{_name}’时，最重要的是（　　）",
                   ["按顺序观察、把话说清楚", "不说话只听", "抢着说", "背稿子"], 0,
                   "口语交际要按顺序观察、把意思表达清楚、认真倾听。")
    if "习作" in s or "作文" in s:
        return _cq("写作文时，把内容写具体的关键是（　　）",
                   ["细致观察并展开想象", "写越短越好", "全抄范文", "不列提纲"], 0,
                   "好习作来自细致观察、合理想象和清楚的表达。")
    if "秋天" in s or "四季" in s:
        return _cq("《秋天》一文主要描写的是（　　）",
                   ["秋天的景象(天凉、叶落、丰收)", "夏天的炎热", "冬天的寒冷", "春天的花开"], 0,
                   "《秋天》抓住天气凉、树叶飘落、庄稼丰收等特征描写秋天。")
    if "小小的船" in s:
        return _cq("‘弯弯的月儿小小的船’运用的修辞手法是（　　）",
                   ["比喻(把月儿比小船)", "拟人", "夸张", "排比"], 0,
                   "儿歌把弯弯的月儿比作小小的船，是比喻。")
    if "江南" in s:
        return _cq("《江南》中‘莲叶何田田’描写的是（　　）",
                   ["荷叶茂盛相连", "莲花盛开", "莲子成熟", "渔船归来"], 0,
                   "‘莲叶何田田’形容荷叶挨挨挤挤、茂盛相连，展现采莲景象。")
    if "画" in s:
        return _cq("谜语诗‘远看山有色，近听水无声’的谜底是（　　）",
                   ["画", "真山真水", "电影", "照片"], 0,
                   "画上的山远看有颜色，水近听却无声——谜底是画。")
    if "影子" in s:
        return _cq("影子总是在（　　）",
                   ["光源的反方向(背光一侧)", "光源正下方", "头顶正上方", "没有规律"], 0,
                   "光沿直线传播，物体挡光，影子出现在背光一侧。")
    if "比尾巴" in s:
        return _cq("《比尾巴》中，猴子的尾巴（　　）",
                   ["长", "短", "弯", "扁"], 0,
                   "儿歌：猴子的尾巴长，兔子的尾巴短，松鼠的尾巴好像一把伞。")
    if "小蝌蚪" in s:
        return _cq("《小蝌蚪找妈妈》中，小蝌蚪长大后变成（　　）",
                   ["青蛙", "乌龟", "鲤鱼", "鸭子"], 0,
                   "蝌蚪是青蛙的幼体，发育后变成青蛙(变态发育)。")
    if "我是什么" in s:
        return _cq("《我是什么》中‘我’指的是（　　）",
                   ["水", "风", "云", "雪"], 0,
                   "课文用拟人，第一人称‘我’是水，会变成汽、云、雨、冰雹、雪。")
    if "植物妈妈" in s:
        return _cq("《植物妈妈有办法》中，蒲公英靠（　　）传播种子",
                   ["风(降落伞)", "动物皮毛", "小鸟", "自身弹射"], 0,
                   "蒲公英种子带绒毛像降落伞，靠风传播；苍耳靠动物，豌豆靠弹射。")
    if "黄山" in s:
        return _cq("《黄山奇石》中描写的怪石有（　　）",
                   ["‘猴子观海’等", "‘象鼻山’", "‘石林’", "‘风动石’"], 0,
                   "课文写黄山奇石，如‘仙桃石’‘猴子观海’‘仙人指路’等。")
    if "梅花" in s:
        return _cq("‘墙角数枝梅，凌寒独自开’的作者是（　　）",
                   ["王安石", "李白", "杜甫", "白居易"], 0,
                   "王安石《梅花》：墙角数枝梅，凌寒独自开。遥知不是雪，为有暗香来。")
    if "场景歌" in s:
        return _cq("‘一只海鸥，一片沙滩’中‘只’‘片’是（　　）",
                   ["数量词", "形容词", "动词", "名词"], 0,
                   "《场景歌》学习数量词搭配：一只、一片、一艘、一条。")
    if "升国旗" in s:
        return _cq("我国的国旗是（　　）",
                   ["五星红旗", "八一军旗", "党旗", "联合国旗"], 0,
                   "中华人民共和国国旗是五星红旗。")
    if "对韵歌" in s:
        return _cq("‘云对雨，雪对风’运用的是（　　）",
                   ["对韵(对子)", "比喻", "拟人", "排比"], 0,
                   "《对韵歌》用对子形式：云对雨、雪对风、花对树、鸟对虫。")
    if "大小多少" in s:
        return _cq("‘一个大，一个小’主要教我们认识（　　）",
                   ["大小、多少的对比", "颜色", "形状", "方向"], 0,
                   "《大小多少》通过对比认识量词和大小多少。")
    if "小书包" in s:
        return _cq("《小书包》里装的是（　　）",
                   ["课本和文具", "玩具", "食物", "衣服"], 0,
                   "《小书包》写书包里的课本、铅笔等学习用品。")
    # ── 二年级上册常见课文 ──
    if "风娃娃" in s:
        return _cq("《风娃娃》中风娃娃帮助人们时，下列哪件事做得不好？（　　）",
                   ["吹跑了人们晾的衣服", "帮老牛拉车", "推动水车灌溉", "为船帆鼓风"], 0,
                   "风娃娃好心办坏事：吹风车、吹帆船是帮忙；但用力过猛吹断树枝、吹跑衣服反而添乱。故事告诉我们做事要考虑实际情况。")
    if "纸船" in s and "风筝" in s:
        return _cq("《纸船和风筝》中，松鼠和小熊和好的办法是（　　）",
                   ["纸船上放草莓/风筝上系纸条互相道歉", "假装什么都没发生", "等对方先道歉", "找老师评理"], 0,
                   "松鼠折纸船放草莓漂流过去，小熊放风筝挂纸片飘过来，用小礼物表达歉意，两人和好如初。友谊需要主动修补。")
    if "狐假虎威" in s:
        return _cq("‘狐假虎威’中‘假’的意思是（　　）",
                   ["借用", "真假", "放假", "假如"], 0,
                   "假=借用。狐狸借老虎的威风吓唬百兽。比喻借别人势力欺压人。")
    if "狐狸分奶酪" in s:
        return _cq("《狐狸分奶酪》告诉我们（　　）",
                   ["同伴间要谦让、不要被坏人利用", "奶酪必须平均分", "狐狸很公平", "小熊不懂分享"], 0,
                   "狐狸假装公平分奶酪，实则全吃光了。故事教育小朋友：要谦让包容，不要因小事争吵让坏人得利。")
    if "猫和老鼠" in s or "看图写话" in s:
        return _fq("根据《看图写话：猫和老鼠》，当两只动物停止争斗后，它们最可能采取的行为是？（填入‘玩耍’或‘打架’）",
                   "玩耍",
                   "猫和老鼠的故事通常描写它们从争斗到和谐相处的过程，停止争斗后会一起玩耍。")
    return None


# ── 英语知识题库（key 为小写子点关键词，首次命中即出真题）──
_ENG_BANK = [
    (("good morning", "good afternoon"), "‘早上好’用英语怎么说（　　）",
     ["Good morning!", "Good afternoon!", "Good evening!", "Good night!"], 0,
     "Good morning早上好；afternoon下午，evening晚上，night睡前道别。"),
    (("nice to meet", "introduce", "names", "nice to"), "‘很高兴见到你’的英文是（　　）",
     ["Nice to meet you.", "See you later.", "Thank you.", "How old are you?"], 0,
     "初次见面说 Nice to meet you.（很高兴见到你）。"),
    (("in/on/under", "on/in/under", "in on under", "on in under"), "The ball is ___ the box.（球在盒子下面）应填（　　）",
     ["under", "on", "in", "at"], 0,
     "under在……下面；on在……上面，in在……里面。"),
    (("transport", "how do you come", "traffic"), "‘我乘公共汽车上学’用（　　）",
     ["I go to school by bus.", "I go to school on bus.", "I go to school by a bus.", "I go school bus."], 0,
     "‘乘某种交通工具’用 by+交通工具，如 by bus/by bike。"),
    (("traffic lights",), "交通灯中表示‘停’的是（　　）",
     ["Red light（红灯）", "Green light（绿灯）", "Yellow light（黄灯）", "Blue light（蓝灯）"], 0,
     "Red means stop.红灯停，绿灯 green 行。"),
    (("turn left", "turn right", "directions"), "问路‘……怎么走’最常用的表达是（　　）",
     ["How can I get to ...?", "How old are you?", "How are you?", "How much is it?"], 0,
     "问路用 How can I get to...? / Where is...?；turn left向左转。"),
    (("hobb",), "‘我喜欢打篮球’用（　　）",
     ["I like playing basketball.", "I like play basketball.", "I likes playing basketball.", "I am play basketball."], 0,
     "like doing sth.喜欢做某事；like 后接动词-ing 或 to do。"),
    (("third-person", "third person"), "He ___ to school every day.（第三人称单数）应填（　　）",
     ["goes", "go", "going", "gone"], 0,
     "主语为第三人称单数、一般现在时，动词加-s/-es：go→goes。"),
    (("comparative", "than"), "Tom is ___ than Jim.（更高）应填（　　）",
     ["taller", "tall", "tallest", "more tall"], 0,
     "两者比较用比较级，tall→taller，后接 than。"),
    (("superlative", "closest", "most"), "He is ___ student in our class.（最高）应填（　　）",
     ["the tallest", "taller", "tall", "most tall"], 0,
     "三者及以上比较用最高级，形容词前加 the：the tallest。"),
    (("used to", "past vs now", "appearance change"), "‘我过去常常早起’用（　　）",
     ["I used to get up early.", "I use to get up early.", "I am used to get up early.", "I used getting up early."], 0,
     "used to do sth.表示‘过去常常做（现在不做了）’。"),
    (("past perfect",), "表示‘过去的过去’（某动作在另一个过去动作之前完成）用（　　）",
     ["过去完成时 had done", "一般过去时 did", "现在完成时 have done", "一般现在时 do"], 0,
     "过去完成时 had+过去分词，表示‘过去的过去’。"),
    (("irregular past",), "动词 go 的过去式是（　　）",
     ["went", "goed", "gone", "going"], 0,
     "go是不规则动词，过去式 went，过去分词 gone。"),
    (("regular past",), "规则动词构成一般过去式，一般在词尾加（　　）",
     ["-ed", "-s", "-ing", "-er"], 0,
     "规则动词过去式一般加-ed，如 work→worked。"),
    (("plural",), "名词 box 的复数形式是（　　）",
     ["boxes", "boxs", "box", "boxies"], 0,
     "以x/s/sh/ch结尾的名词复数加-es：box→boxes。"),
    (("possessive",), "‘这是汤姆的书’用（　　）",
     ["This is Tom's book.", "This is Tom book.", "This is Toms book.", "This is book of Tom."], 0,
     "表示所属用名词's：Tom's book汤姆的书。"),
    (("should", "advise", "advice"), "劝告‘你应该多喝水’用（　　）",
     ["You should drink more water.", "You should to drink more water.", "You shoulds drink water.", "You drink should water."], 0,
     "should+动词原形，表示‘应该’，用于提建议。"),
    (("must", "imperative", "rules", "permission"), "‘禁止吸烟’用英语是（　　）",
     ["Don't smoke.", "No smoke.", "Not smoke.", "Smoke don't."], 0,
     "祈使句表禁止用 Don't+动词原形：Don't smoke.禁止吸烟。"),
    (("ability", "can"), "‘我会游泳’用英语是（　　）",
     ["I can swim.", "I can swimming.", "I can to swim.", "I am can swim."], 0,
     "can+动词原形表示能力‘能、会’：I can swim.我会游泳。"),
    (("how often", "frequency"), "表示频率最高（‘总是’）的副词是（　　）",
     ["always", "sometimes", "never", "seldom"], 0,
     "频率副词由高到低：always＞usually＞often＞sometimes＞never。"),
    (("count", "non-count", "more/less/fewer"), "修饰可数名词复数‘许多’用（　　）",
     ["many", "much", "a little", "little"], 0,
     "many+可数名词复数；much+不可数名词，都表示‘许多’。"),
    (("excuse me",), "想引起别人注意、表示‘打扰一下’用（　　）",
     ["Excuse me.", "Sorry.", "Thank you.", "Goodbye."], 0,
     "Excuse me用于引起注意或打扰别人；Sorry表示道歉。"),
    (("be going to", "plans", "prediction", "resolution"), "‘我明天打算去看望奶奶’用（　　）",
     ["I am going to visit my grandma tomorrow.", "I am go to visit grandma.", "I going to visit grandma.", "I will going visit grandma."], 0,
     "be going to+动词原形，表示打算或计划。"),
    (("subjunctive",), "虚拟语气‘如果我是你’用（　　）",
     ["If I were you", "If I am you", "If I was you", "If I be you"], 0,
     "与现在事实相反的虚拟条件，be动词一律用 were：If I were you。"),
    (("infinitive", "to do / doing", "non-finite"), "动词 want 后接另一个动词时用（　　）",
     ["to do（不定式）", "doing", "do", "did"], 0,
     "want to do sth.想做某事，want后接动词不定式。"),
    (("month",), "一年中的第一个月是（　　）",
     ["January", "June", "July", "March"], 0,
     "一年12个月，第一个月是 January（一月）。"),
    (("date", "calendar"), "‘十月一日’的正确英文表达是（　　）",
     ["October 1st", "October one", "1 October month", "Oct first day"], 0,
     "日期用序数词：October 1st（十月一日）。"),
    (("sport",), "下列单词中表示‘运动’的是（　　）",
     ["football（足球）", "apple（苹果）", "desk（书桌）", "red（红色）"], 0,
     "football属于运动类词汇；其余分别是食物、文具、颜色。"),
    (("furniture",), "下列单词中表示‘家具’的是（　　）",
     ["bed（床）", "apple（苹果）", "dog（狗）", "run（跑）"], 0,
     "bed属于家具类词汇；其余分别是食物、动物、动作。"),
    (("nature",), "下列单词中表示‘自然景物’的是（　　）",
     ["mountain（山）", "pencil（铅笔）", "teacher（老师）", "happy（高兴的）"], 0,
     "mountain属于自然景物；其余分别是文具、职业、情感。"),
    (("feeling", "how do you feel", "glad", "afraid"), "‘我很高兴’用英语是（　　）",
     ["I'm happy.", "I'm apple.", "I happy.", "Me happy."], 0,
     "表达情感用 I'm+形容词：I'm happy.我很高兴。"),
    (("family",), "‘我的父母’用英语是（　　）",
     ["my parents", "my parent", "my family tree", "my brother"], 0,
     "parents指父母（复数）；parent单个家长。"),
    (("subject", "school event", "school club"), "下列单词中表示‘学科’的是（　　）",
     ["English（英语）", "apple（苹果）", "rabbit（兔子）", "blue（蓝色）"], 0,
     "English是学科名称；其余分别是食物、动物、颜色。"),
    (("shopping",), "购物时询问价格用（　　）",
     ["How much is it?", "How old are you?", "What's this?", "Where is it?"], 0,
     "How much is it?用来询问物品的价格。"),
    (("invitation", "i'd love", "sure"), "接受邀请、表示‘我很乐意’用（　　）",
     ["I'd love to.", "No way.", "I don't.", "Never mind."], 0,
     "接受邀请常说 I'd love to./Sure.（我很乐意）。"),
    (("tense",), "表示‘经常性、习惯性动作’用（　　）",
     ["一般现在时", "一般将来时", "现在进行时", "一般过去时"], 0,
     "一般现在时表示经常、习惯性的动作或客观事实。"),
    (("plural noun",), "名词 city 的复数是（　　）",
     ["cities", "citys", "cityes", "city"], 0,
     "辅音字母+y结尾，变y为i再加es：city→cities。"),
    (("pronunciation",), "字母组合‘ee’通常发音为（　　）",
     ["/iː/ 如 see", "/e/ 如 bed", "/aɪ/ 如 my", "/ʌ/ 如 cup"], 0,
     "ee通常发长音/iː/，如 see、tree、green。"),
    (("high-frequency", "advanced words", "vocabulary"), "单词 ‘important’ 的意思是（　　）",
     ["重要的", "有趣的", "困难的", "容易的"], 0,
     "important重要的；interesting有趣的，difficult困难的，easy容易的。"),
]


def _english_quiz(s, i):
    s = s.lower()
    for entry in _ENG_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    if "时态" in s or "过去" in s or "完成" in s or "进行" in s:
        return _cq("He ___ to school yesterday. (　　)",
                   ["went", "goes", "go", "going"], 0,
                   "yesterday 表过去，动词用过去式 went(go的过去式)。")
    if "there" in s or "be" in s:
        return _cq("___ some milk in the glass. (　　)",
                   ["There is", "There are", "Have", "Has"], 0,
                   "milk 不可数，用 There is；there be 就近原则。")
    if "介词" in s:
        return _cq("We usually have lunch ___ 12:00. (　　)",
                   ["at", "in", "on", "for"], 0,
                   "具体时刻前用 at；in+年/月，on+具体某天。")
    if "代词" in s or "物主" in s:
        return _cq("This is ___ book. (I) (　　)",
                   ["my", "me", "I", "mine"], 0,
                   "修饰名词 book 用形容词性物主代词 my。")
    if "词汇" in s or "词义" in s or "单词" in s:
        return _cq("The meaning of ‘environment’ is（　　）",
                   ["环境", "发展", "政府", "实验"], 0,
                   "environment 意为‘环境’；development发展、government政府、experiment实验。")
    if "be going to" in s or "will" in s or "future" in s or "going to" in s:
        return _cq("I ___ visit my grandma tomorrow. (　　)",
                   ["am going to", "am go to", "goes to", "going to"], 0,
                   "be going to + 动词原形表将来计划；I 配 am。")
    if "passive" in s:
        return _cq("The book ___ by Lu Xun. (　　)",
                   ["was written", "wrote", "was wrote", "is write"], 0,
                   "被动语态：be + 过去分词；write的过去分词是written。")
    if "clause" in s or "relative" in s or "attributive" in s:
        return _cq("This is the book ___ I bought yesterday. (　　)",
                   ["that/which", "who", "what", "where"], 0,
                   "定语从句修饰物用that/which；who指人，where指地点。")
    if "-ing" in s or "gerund" in s:
        return _cq("___ (swim) is good for health. (　　)",
                   ["Swimming", "Swim", "To swim", "Swam"], 0,
                   "动词-ing作主语表习惯性活动，用Swimming。")
    if "preposition" in s:
        return _cq("The book is ___ the desk. (　　)",
                   ["on", "in", "at", "to"], 0,
                   "‘在桌上’用介词on；in在…里，at在某时刻/地点。")
    if "spelling" in s:
        return _cq("含有字母组合‘ou’发 /aʊ/ 的单词是（　　）",
                   ["house", "horse", "hot", "hand"], 0,
                   "house中ou发/aʊ/；horse中or发/ɔː/。")
    if "food" in s:
        return _cq("‘面包’的英文是（　　）",
                   ["bread", "meat", "rice", "egg"], 0,
                   "bread面包；meat肉，rice米饭，egg蛋。")
    if "job" in s:
        return _cq("‘医生’的英文是（　　）",
                   ["doctor", "teacher", "driver", "farmer"], 0,
                   "doctor医生；teacher教师，driver司机，farmer农民。")
    if "colour" in s or "color" in s:
        return _cq("‘红色’的英文是（　　）",
                   ["red", "blue", "green", "yellow"], 0,
                   "red红色；blue蓝色，green绿色，yellow黄色。")
    if "school things" in s:
        return _cq("‘铅笔’的英文是（　　）",
                   ["pencil", "pen", "book", "ruler"], 0,
                   "pencil铅笔；pen钢笔，book书，ruler尺子。")
    if "where" in s or "there" in s:
        return _cq("___ a book on the desk. (　　)",
                   ["There is", "There are", "Have", "Has"], 0,
                   "单数a book用There is；there be就近原则。")
    if "greeting" in s or "hello" in s:
        return _cq("下午见面打招呼可以说（　　）",
                   ["Good afternoon", "Good night", "Goodbye", "Good morning"], 0,
                   "下午用Good afternoon；晚上Good night，早上Good morning。")
    if "festival" in s:
        return _cq("‘春节’的英文是（　　）",
                   ["Spring Festival", "Christmas", "Mid-autumn", "Thanksgiving"], 0,
                   "Spring Festival春节；Christmas圣诞，Mid-autumn中秋。")
    if "letters" in s or "letter" in s:
        return _cq("英语字母表中，排在字母 C 后面的是（　　）",
                   ["D", "B", "E", "A"], 0, "字母顺序 A B C D E…，C 后是 D。")
    if "how old" in s:
        return _cq("‘How old are you?’用来询问（　　）",
                   ["年龄", "身体状况", "时间", "地点"], 0, "How old 询问年龄；How are you 问身体/问候。")
    if "how many" in s or "how much" in s:
        return _cq("‘How many’用来询问（　　）",
                   ["可数名词的数量", "价格", "时间", "颜色"], 0, "How many + 复数名词问数量；How much 问价格/不可数。")
    if "how are" in s:
        return _cq("‘How are you?’是（　　）",
                   ["问候对方身体/近况", "问年龄", "问地点", "问数量"], 0, "How are you 是日常问候，问身体/近况。")
    if "what would" in s or "would you like" in s:
        return _cq("‘What would you like?’用来（　　）",
                   ["询问对方的意愿/想要什么", "问年龄", "问时间", "问地点"], 0, "would like 表‘想要’，用来询问意愿。")
    if "what's this" in s or "what is" in s or "this is" in s or "it's a" in s:
        return _cq("介绍近处的物品可以说（　　）",
                   ["This is a book.", "That is a book.", "These are books.", "Those are books."], 0,
                   "近处单数用 This is…；远处用 That is…。")
    if "who" in s:
        return _cq("‘Who’用来询问（　　）",
                   ["人", "物", "地点", "时间"], 0, "Who 提问人；What 问物，Where 问地点。")
    if "i have" in s or "i'd like" in s or "have some" in s:
        return _cq("‘I have a book.’的意思是（　　）",
                   ["我有一本书", "我喜欢书", "我读书", "我买书"], 0, "have 表示‘有’；I have a book 我有一本书。")
    if "he" in s or "she" in s or "his" in s or "her" in s:
        return _cq("‘He is a boy.’中 He 指代（　　）",
                   ["男性单数", "女性单数", "复数", "物"], 0, "He 主格指代男性单数；She 指代女性。")
    if "can" in s:
        return _cq("‘I can swim.’中 can 表示（　　）",
                   ["能力‘能/会’", "允许", "将来", "过去"], 0, "can 表能力‘能、会’；后接动词原形。")
    if "touch" in s or "body" in s:
        return _cq("‘Touch your nose.’意思是（　　）",
                   ["摸你的鼻子", "看你的鼻子", "指你的鼻子", "说你的鼻子"], 0, "touch 意为‘触摸’；Touch your nose 摸鼻子。")
    if "animal" in s:
        return _cq("‘猫’的英文是（　　）",
                   ["cat", "dog", "pig", "duck"], 0, "cat猫；dog狗，pig猪，duck鸭。")
    if "room" in s or "classroom" in s:
        return _cq("‘教室’的英文是（　　）",
                   ["classroom", "bedroom", "bathroom", "living room"], 0, "classroom教室；bedroom卧室，bathroom浴室。")
    if "place" in s:
        return _cq("‘公园’的英文是（　　）",
                   ["park", "school", "zoo", "shop"], 0, "park公园；school学校，zoo动物园。")
    if "activity" in s or "activities" in s:
        return _cq("‘唱歌’的英文是（　　）",
                   ["sing", "dance", "read", "swim"], 0, "sing唱；dance跳，read读，swim游。")
    if "preference" in s or " like" in s:
        return _cq("‘I like apples.’意思是（　　）",
                   ["我喜欢苹果", "我有苹果", "我吃苹果", "我买苹果"], 0, "like 喜欢；I like apples 我喜欢苹果。")
    if "day" in s or "week" in s:
        return _cq("一周有（　　）天",
                   ["7", "5", "6", "12"], 0, "一周 seven days，共7天。")
    if "character" in s or "adjective" in s:
        return _cq("描述人物性格的形容词是（　　）",
                   ["friendly(友好的)", "red(红色的)", "big(大的)", "fast(快的)"], 0,
                   "friendly 描述性格；red表颜色，big表大小，fast表速度。")
    if "poster" in s or "speech" in s or "advice" in s:
        return _cq("制作英语海报(poster)时，首先应该（　　）",
                   ["明确主题再组织内容", "随便写满", "只用中文", "不画图"], 0,
                   "做海报先定主题，再选词句和图片，语言简洁。")
    return None


# ── 历史知识题库（按“具体优先”排序，key in s 首次命中即出真题）──
_HIST_BANK = [
    (("元谋人", "北京人", "远古社会"), "我国境内目前已确认的最早古人类是（　　）",
     ["元谋人", "北京人", "山顶洞人", "半坡人"], 0,
     "元谋人距今约170万年，是我国境内目前已确认的最早古人类。"),
    (("原始农耕",), "长江流域最早种植水稻的原始居民是（　　）",
     ["河姆渡人", "半坡人", "北京人", "大汶口人"], 0,
     "河姆渡人（长江流域）种水稻，半坡人（黄河流域）种粟。"),
    (("炎黄",), "被后人尊为中华民族人文初祖的是（　　）",
     ["炎帝和黄帝", "尧和舜", "禹和启", "黄帝和蚩尤"], 0,
     "炎帝、黄帝被尊为中华民族的人文初祖。"),
    (("夏朝",), "我国历史上第一个王朝是（　　）",
     ["夏朝", "商朝", "周朝", "秦朝"], 0,
     "约公元前2070年禹建立夏朝，世袭制代替禅让制。"),
    (("青铜器",), "世界现存最大的青铜器是（　　）",
     ["司母戊鼎(后母戊鼎)", "四羊方尊", "毛公鼎", "大盂鼎"], 0,
     "商朝司母戊鼎是世界现存最大的青铜器。"),
    (("甲骨文",), "我国已发现的年代最早、体系较完整的文字是（　　）",
     ["甲骨文", "金文", "小篆", "隶书"], 0,
     "甲骨文是商朝刻在龟甲兽骨上的文字，是我国最早的成熟文字。"),
    (("夏商周", "商周"), "武王伐纣、灭商建周的决战是（　　）",
     ["牧野之战", "城濮之战", "长平之战", "巨鹿之战"], 0,
     "公元前1046年牧野之战，周武王灭商，建立西周。"),
    (("分封制",), "西周实行分封制的根本目的是（　　）",
     ["巩固周王朝的统治", "发展农业生产", "开疆拓土", "传播文化"], 0,
     "西周分封诸侯以‘封建亲戚，以藩屏周’，巩固统治。"),
    (("春秋战国",), "下列不属于‘战国七雄’的是（　　）",
     ["宋国", "秦国", "齐国", "楚国"], 0,
     "战国七雄是齐、楚、秦、燕、赵、魏、韩，无宋国。"),
    (("社会变革",), "使秦国强大、为统一奠定基础的改革是（　　）",
     ["商鞅变法", "管仲改革", "李悝变法", "吴起变法"], 0,
     "商鞅变法使秦国国富兵强，为统一六国奠定基础。"),
    (("中央集权",), "秦朝为加强对地方的管理，在全国推行（　　）",
     ["郡县制", "分封制", "行省制", "世袭制"], 0,
     "秦朝废分封、行郡县，开创中央集权的政治制度。"),
    (("汉武帝",), "汉武帝为加强思想控制采取的措施是（　　）",
     ["罢黜百家，独尊儒术", "焚书坑儒", "八股取士", "大兴文字狱"], 0,
     "汉武帝采纳董仲舒建议‘罢黜百家，独尊儒术’。"),
    (("丝绸之路", "商路"), "为开辟丝绸之路作出重大贡献、出使西域的是（　　）",
     ["张骞", "班超", "玄奘", "郑和"], 0,
     "汉武帝派张骞出使西域，开辟了以长安为起点的丝绸之路。"),
    (("三国鼎立",), "为三国鼎立局面形成奠定基础的战役是（　　）",
     ["赤壁之战", "官渡之战", "淝水之战", "巨鹿之战"], 0,
     "208年赤壁之战，孙刘联军大败曹操，奠定三国鼎立基础。"),
    (("西晋",), "结束三国分裂、短暂统一全国的王朝是（　　）",
     ["西晋", "东晋", "隋朝", "北魏"], 0,
     "280年西晋灭吴，短暂统一全国。"),
    (("北方民族", "民族交融", "民族关系"), "东汉末以来内迁中原的北方少数民族被称为（　　）",
     ["五胡", "百越", "南蛮", "西戎"], 0,
     "匈奴、鲜卑、羯、氐、羌等内迁，史称‘五胡’，促进民族交融。"),
    (("江南开发",), "东晋南朝时江南得到开发的最主要原因是（　　）",
     ["北方人口南迁带来劳动力和技术", "南方自然条件优越", "统治者格外重视", "南方战乱较少"], 0,
     "北方人南迁带来大量劳动力和先进生产技术，促进江南开发。"),
    (("北魏孝文帝",), "北魏孝文帝改革的重要措施是（　　）",
     ["迁都洛阳、推行汉化", "推行郡县制", "创立科举制", "闭关锁国"], 0,
     "孝文帝迁都洛阳，改汉姓、穿汉服、说汉话，促进民族交融。"),
    (("隋唐制度", "科举", "选官", "文官"), "隋朝创立、以考试选拔官员的制度是（　　）",
     ["科举制", "察举制", "九品中正制", "世袭制"], 0,
     "隋炀帝时设进士科，科举制正式创立，以才学考试选官。"),
    (("隋朝",), "隋朝开凿的、贯通南北的伟大工程是（　　）",
     ["大运河", "长城", "都江堰", "灵渠"], 0,
     "隋炀帝开凿大运河，以洛阳为中心，沟通南北。"),
    (("贞观之治",), "‘贞观之治’出现在哪位皇帝统治时期（　　）",
     ["唐太宗李世民", "唐玄宗", "隋文帝", "武则天"], 0,
     "唐太宗李世民统治时政治清明，史称‘贞观之治’。"),
    (("开元盛世", "唐朝盛世", "唐朝民族"), "‘开元盛世’是哪位皇帝统治时期的局面（　　）",
     ["唐玄宗", "唐太宗", "唐高宗", "武则天"], 0,
     "唐玄宗前期励精图治，出现‘开元盛世’；文成公主入藏促汉藏友好。"),
    (("北宋", "两宋"), "通过陈桥兵变、‘黄袍加身’建立北宋的是（　　）",
     ["赵匡胤", "李世民", "朱元璋", "忽必烈"], 0,
     "960年赵匡胤陈桥兵变建立北宋，实行重文轻武政策。"),
    (("辽西夏金",), "北宋与辽订立、维持长期和平的盟约是（　　）",
     ["澶渊之盟", "绍兴和议", "尼布楚条约", "城下之盟"], 0,
     "1005年宋辽订立澶渊之盟，此后维持了较长时间的和平。"),
    (("经济重心南移",), "我国古代经济重心南移最终完成于（　　）",
     ["南宋", "唐朝", "北宋", "明朝"], 0,
     "‘苏湖熟，天下足’，南宋时经济重心南移最终完成。"),
    (("元朝",), "元朝为管理广阔疆域，在地方推行（　　）",
     ["行省制度", "郡县制", "分封制", "三省六部制"], 0,
     "元世祖忽必烈推行行省制度，是我国省制的开端。"),
    (("郑和下西洋",), "明朝郑和下西洋最远到达（　　）",
     ["非洲东海岸和红海沿岸", "印度半岛", "波斯湾", "欧洲"], 0,
     "1405—1433年郑和七下西洋，最远到达非洲东海岸和红海沿岸。"),
    (("明朝",), "明太祖朱元璋为加强君权，在中央废除了（　　）",
     ["丞相制度", "科举制", "行省制", "内阁"], 0,
     "明太祖废丞相、权分六部，君主专制空前强化。"),
    (("边疆治理", "边疆", "清朝前中期"), "清朝为加强对西藏的管理设置了（　　）",
     ["驻藏大臣", "伊犁将军", "西域都护", "宣政院"], 0,
     "1727年清朝设驻藏大臣，代表中央监督西藏地方事务。"),
    (("清朝",), "清朝雍正时设立、标志君主专制达到顶峰的机构是（　　）",
     ["军机处", "内阁", "中书省", "锦衣卫"], 0,
     "雍正设军机处，君主专制中央集权发展到顶峰。"),
    (("南京条约", "瓜分危机"), "中国近代史上第一个不平等条约是（　　）",
     ["《南京条约》", "《马关条约》", "《辛丑条约》", "《北京条约》"], 0,
     "1842年中英《南京条约》割香港岛、赔款、开五口通商。"),
    (("太平天国",), "领导太平天国运动、发动金田起义的是（　　）",
     ["洪秀全", "李秀成", "杨秀清", "石达开"], 0,
     "1851年洪秀全在广西金田村起义，建号太平天国。"),
    (("边疆危机",), "19世纪70年代率军收复新疆的是（　　）",
     ["左宗棠", "林则徐", "李鸿章", "曾国藩"], 0,
     "左宗棠收复新疆，1884年清政府在新疆设立行省。"),
    (("实业救国", "民族工业", "民族"), "提出‘实业救国’、创办大生纱厂的状元实业家是（　　）",
     ["张謇", "张之洞", "荣宗敬", "范旭东"], 0,
     "状元张謇创办大生纱厂，倡导‘实业救国’。"),
    (("孙中山",), "孙中山领导辛亥革命的指导思想是（　　）",
     ["三民主义", "民主与科学", "马克思主义", "实业救国"], 0,
     "孙中山提出民族、民权、民生‘三民主义’。"),
    (("中华民国", "民国政治", "北洋时期", "北洋军阀"), "窃取辛亥革命果实、建立北洋军阀统治的是（　　）",
     ["袁世凯", "黎元洪", "段祺瑞", "张作霖"], 0,
     "1912年中华民国成立，袁世凯窃取革命果实，开始北洋军阀统治。"),
    (("社会习俗", "社会生活", "社会变迁", "变迁原因", "交通通讯"), "辛亥革命后社会习俗的变化是（　　）",
     ["剪辫易服、改称呼、废跪拜", "女子缠足盛行", "跪拜礼普及", "强制穿长袍马褂"], 0,
     "辛亥革命后剪辫、易服、改称呼、废跪拜，社会习俗走向文明。"),
    (("五四运动",), "五四运动爆发于（　　）",
     ["1919年", "1911年", "1921年", "1915年"], 0,
     "1919年五四运动是彻底反帝反封建的爱国运动，是新民主主义革命的开端。"),
    (("中共一大", "中共诞生"), "中国共产党成立的标志是（　　）",
     ["1921年中共一大召开", "五四运动", "南昌起义", "遵义会议"], 0,
     "1921年中共一大在上海召开，宣告中国共产党成立。"),
    (("工人运动",), "中共成立后掀起第一次工人运动高潮中著名的是（　　）",
     ["京汉铁路大罢工", "安源路矿罢工", "省港大罢工", "五卅运动"], 0,
     "1923年京汉铁路工人大罢工把第一次工人运动高潮推向顶点。"),
    (("黄埔军校",), "1924年国共合作创办、培养军事人才的学校是（　　）",
     ["黄埔军校", "京师大学堂", "抗日军政大学", "云南讲武堂"], 0,
     "1924年孙中山在广州创办黄埔军校，培养革命军事人才。"),
    (("北伐",), "北伐战争的主要打击对象是（　　）",
     ["北洋军阀", "日本侵略者", "清政府", "国民党"], 0,
     "1926年国民革命军北伐，打击吴佩孚、孙传芳、张作霖等军阀。"),
    (("南昌起义",), "打响武装反抗国民党反动派第一枪的是（　　）",
     ["南昌起义", "秋收起义", "广州起义", "井冈山会师"], 0,
     "1927年8月1日南昌起义，打响武装反抗国民党反动派第一枪。"),
    (("长征",), "确立毛泽东在党和红军领导地位的会议是（　　）",
     ["遵义会议", "中共一大", "八七会议", "瓦窑堡会议"], 0,
     "1935年遵义会议确立毛泽东的领导地位，是党史上生死攸关的转折点。"),
    (("九一八",), "中国局部抗战开始的标志是（　　）",
     ["九一八事变", "七七事变", "西安事变", "一二八事变"], 0,
     "1931年九一八事变，中国人民局部抗战由此开始。"),
    (("西安事变",), "西安事变和平解决的意义是（　　）",
     ["揭开国共合作抗日的序幕", "开始全面抗战", "结束内战", "建立新中国"], 0,
     "1936年张学良、杨虎城发动西安事变，其和平解决揭开国共合作抗日序幕。"),
    (("七七事变",), "中国全民族抗战开始的标志是（　　）",
     ["七七事变(卢沟桥事变)", "九一八事变", "南京大屠杀", "淞沪会战"], 0,
     "1937年七七事变，中国全民族抗战开始。"),
    (("正面战场", "重要战役"), "抗战中取得正面战场重大胜利的战役是（　　）",
     ["台儿庄战役", "百团大战", "辽沈战役", "淮海战役"], 0,
     "1938年台儿庄战役是抗战以来正面战场取得的重大胜利。"),
    (("敌后战场",), "抗战中八路军在敌后主动出击日军的大规模战役是（　　）",
     ["百团大战", "台儿庄战役", "武汉会战", "徐州会战"], 0,
     "1940年彭德怀指挥百团大战，是敌后战场的大规模主动进攻。"),
    (("胜利意义",), "中国人民抗日战争胜利的时间是（　　）",
     ["1945年", "1937年", "1949年", "1931年"], 0,
     "1945年8月15日日本宣布无条件投降，抗日战争取得胜利。"),
    (("重庆谈判",), "1945年重庆谈判后国共双方签署了（　　）",
     ["《双十协定》", "《南京条约》", "《辛丑条约》", "《停战协定》"], 0,
     "1945年重庆谈判达成《双十协定》。"),
    (("内战爆发",), "全面内战爆发的标志是（　　）",
     ["1946年国民党军进攻中原解放区", "重庆谈判", "西安事变", "皖南事变"], 0,
     "1946年6月国民党军进攻中原解放区，全面内战爆发。"),
    (("战略反攻",), "揭开人民解放军战略反攻序幕的是（　　）",
     ["刘邓大军挺进大别山", "三大战役", "渡江战役", "百团大战"], 0,
     "1947年刘邓大军挺进大别山，揭开战略反攻序幕。"),
    (("三大战役",), "三大战役是指（　　）",
     ["辽沈、淮海、平津战役", "台儿庄、武汉、长沙会战", "渡江、上海、南京战役", "百团、平型关、台儿庄"], 0,
     "1948—1949年辽沈、淮海、平津三大战役基本消灭国民党军主力。"),
    (("新中国成立", "新中国制度"), "中华人民共和国成立的时间是（　　）",
     ["1949年10月1日", "1949年9月21日", "1945年8月15日", "1978年12月"], 0,
     "1949年10月1日开国大典，中华人民共和国成立。"),
    # ── 世界史 ──
    (("古代埃及", "古代文明"), "古代埃及文明的象征性建筑是（　　）",
     ["金字塔", "空中花园", "帕特农神庙", "万里长城"], 0,
     "金字塔是古埃及法老的陵墓，是古埃及文明的象征。"),
    (("两河流域",), "世界上现存最早的、较为完整的成文法典是（　　）",
     ["《汉谟拉比法典》", "《十二铜表法》", "《拿破仑法典》", "《查士丁尼法典》"], 0,
     "古巴比伦《汉谟拉比法典》是世界现存最早的较完整成文法典。"),
    (("古代印度",), "古代印度森严的社会等级制度是（　　）",
     ["种姓制度", "封君封臣制", "庄园制", "分封制"], 0,
     "古代印度实行种姓制度，把人分为四个等级。"),
    (("希腊",), "被称为西方文明发源地、创立民主政治的古国是（　　）",
     ["古希腊(雅典)", "古埃及", "古印度", "古巴比伦"], 0,
     "古希腊雅典的民主政治在伯里克利时期发展到高峰。"),
    (("罗马",), "罗马法制建设的起点、平民斗争的成果是（　　）",
     ["《十二铜表法》", "《汉谟拉比法典》", "《查士丁尼法典》", "《民法典》"], 0,
     "《十二铜表法》是罗马第一部成文法，是罗马法制建设的起点。"),
    (("法兰克", "庄园", "中古世界", "居住"), "中世纪西欧农村基本的经济和社会组织是（　　）",
     ["庄园", "城邦", "行会", "公社"], 0,
     "庄园是中世纪西欧农村的基本组织，具有自给自足的特点。"),
    (("城市",), "中世纪西欧城市兴起后，市民为争取自治常用的手段是（　　）",
     ["金钱赎买或武力斗争", "服从国王命令", "依附教会", "退回农村"], 0,
     "西欧城市市民通过金钱赎买或武力斗争争取自治权。"),
    (("阿拉伯",), "阿拉伯人对世界文化的重要贡献是（　　）",
     ["传播了阿拉伯数字", "发明了造纸术", "开辟了新航路", "发起文艺复兴"], 0,
     "阿拉伯人改造并向世界传播了由古印度人发明的阿拉伯数字。"),
    (("日本大化改新",), "日本大化改新主要仿效了（　　）的制度",
     ["中国隋唐", "古印度", "古罗马", "阿拉伯帝国"], 0,
     "646年日本大化改新，仿效中国隋唐制度，走上封建化道路。"),
    (("文艺复兴",), "文艺复兴运动的核心思想是（　　）",
     ["人文主义", "理性主义", "民族主义", "自由主义"], 0,
     "文艺复兴以人文主义为核心，但丁的《神曲》是其先声。"),
    (("新航路",), "1492年发现美洲新大陆的航海家是（　　）",
     ["哥伦布", "麦哲伦", "迪亚士", "达·伽马"], 0,
     "1492年哥伦布在西班牙支持下横渡大西洋，发现美洲。"),
    (("三角贸易", "早期殖民", "资本原始积累", "殖民扩张", "殖民体系", "近代殖民"), "罪恶的‘三角贸易’贩卖的主要对象是（　　）",
     ["非洲黑人奴隶", "美洲原住民", "亚洲劳工", "欧洲移民"], 0,
     "三角贸易把非洲黑人贩卖到美洲，是资本原始积累的血腥手段。"),
    (("美国独立",), "美国《独立宣言》发表的时间是（　　）",
     ["1776年", "1787年", "1789年", "1861年"], 0,
     "1776年7月4日《独立宣言》发表，宣告美国独立，华盛顿领导独立战争。"),
    (("拿破仑",), "拿破仑巩固资产阶级统治、影响深远的法律文献是（　　）",
     ["《拿破仑法典》", "《权利法案》", "《人权宣言》", "《独立宣言》"], 0,
     "《拿破仑法典》确立了资本主义社会的立法规范，影响深远。"),
    (("第一次工业",), "第一次工业革命中改良蒸汽机、把人类带入‘蒸汽时代’的是（　　）",
     ["瓦特", "牛顿", "爱迪生", "法拉第"], 0,
     "瓦特改良蒸汽机，成为工业革命的主要动力，人类进入蒸汽时代。"),
    (("第二次工业",), "第二次工业革命的显著特征是（　　）",
     ["电力的广泛应用", "蒸汽机的发明", "计算机的普及", "纺织机的出现"], 0,
     "第二次工业革命电力广泛应用，人类进入‘电气时代’。"),
    (("马克思主义",), "马克思主义诞生的标志是（　　）",
     ["1848年《共产党宣言》发表", "巴黎公社成立", "十月革命胜利", "第一国际成立"], 0,
     "1848年《共产党宣言》发表，标志马克思主义诞生。"),
    (("凡尔赛华盛顿",), "第一次世界大战后帝国主义列强建立的国际关系体系是（　　）",
     ["凡尔赛—华盛顿体系", "雅尔塔体系", "维也纳体系", "两极格局"], 0,
     "一战后通过巴黎和会、华盛顿会议形成凡尔赛—华盛顿体系。"),
    (("一战二战",), "两次世界大战给人类的最深刻启示是（　　）",
     ["珍爱和平、反对战争", "弱肉强食理所应当", "战争能解决一切", "结盟必然带来和平"], 0,
     "两次世界大战造成空前浩劫，警示人类要珍爱和平、反对战争。"),
    (("二战",), "第二次世界大战全面爆发的标志是（　　）",
     ["德国突袭波兰", "珍珠港事件", "九一八事变", "诺曼底登陆"], 0,
     "1939年德国突袭波兰，英法对德宣战，二战全面爆发。"),
    (("一战",), "第一次世界大战爆发的导火线是（　　）",
     ["萨拉热窝事件", "珍珠港事件", "九一八事变", "凡尔登战役"], 0,
     "1914年萨拉热窝事件成为一战的导火线。"),
    (("联合国", "和平"), "二战后成立的、维护世界和平与安全的国际组织是（　　）",
     ["联合国", "国际联盟", "世界贸易组织", "北约"], 0,
     "1945年成立联合国，宗旨是维护国际和平与安全。"),
    (("冷战对峙", "冷战"), "冷战开始的标志是（　　）",
     ["1947年杜鲁门主义出台", "北约成立", "柏林墙修建", "古巴导弹危机"], 0,
     "1947年杜鲁门主义出台，标志美苏冷战开始。"),
    (("多极化", "现代格局", "政治格局"), "当今世界政治格局的发展趋势是（　　）",
     ["多极化", "单极化", "两极对峙", "全球一体"], 0,
     "苏联解体后，世界政治格局朝着多极化方向发展。"),
    (("经济全球化", "全球化", "当代问题"), "经济全球化的重要表现是（　　）",
     ["国际贸易和投资迅速增长", "各国闭关自守", "关税壁垒普遍加强", "殖民扩张加剧"], 0,
     "经济全球化表现为国际贸易、投资和跨国生产的迅速增长。"),
    (("监察制度", "反腐"), "秦汉时期负责监察百官的中央官职是（　　）",
     ["御史大夫", "丞相", "太尉", "刺史"], 0,
     "秦汉御史大夫掌监察，是中国古代监察制度的重要组成。"),
    (("中华法系", "法律"), "中华法系的特点之一是（　　）",
     ["礼法结合、以礼入法", "法律与道德完全无关", "以宗教教义治国", "只重刑罚不讲教化"], 0,
     "中华法系强调礼法结合、德主刑辅。"),
    (("食物生产", "商业贸易", "医疗", "人口迁徙", "交通"), "对人类文明进程影响深远的农业起源，最早出现在（　　）",
     ["西亚、东亚、中南美洲等地", "仅欧洲", "仅非洲南部", "仅大洋洲"], 0,
     "农业约一万年前在西亚、东亚、中南美洲等地独立起源。"),
]


def _humanity_quiz(s, i, subject):
    for entry in _HIST_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    # 通用历史关键词兜底
    if "朝代" in s or "建立" in s or "统一" in s:
        return _cq("中国历史上第一个统一的中央集权封建国家是（　　）",
                   ["秦朝", "汉朝", "唐朝", "周朝"], 0,
                   "公元前221年秦灭六国，建立第一个统一的多民族中央集权封建国家。")
    if "鸦片" in s or "战争" in s or "侵略" in s:
        return _cq("中国近代史的开端是（　　）",
                   ["鸦片战争(1840)", "甲午战争(1894)", "八国联军(1900)", "辛亥革命(1911)"], 0,
                   "1840年鸦片战争是中国近代史开端，中国开始沦为半殖民地半封建社会。")
    if "改革" in s or "变法" in s or "洋务" in s:
        return _cq("洋务运动的根本目的是（　　）",
                   ["维护清朝统治", "发展资本主义", "推翻清朝", "传播民主"], 0,
                   "洋务派‘自强’‘求富’为维护清王朝统治，属地主阶级自救运动。")
    if "革命" in s or "辛亥" in s:
        return _cq("辛亥革命最伟大的历史功绩是（　　）",
                   ["结束君主专制制度", "彻底反帝", "建立社会主义", "消灭剥削"], 0,
                   "辛亥革命推翻清王朝，结束两千多年君主专制制度。")
    if "思想" in s or "文化" in s or "孔子" in s:
        return _cq("儒家学派的创始人是（　　）",
                   ["孔子", "老子", "墨子", "韩非"], 0,
                   "孔子创立儒家，核心‘仁’‘礼’；老子道家，墨子墨家，韩非法家。")
    if subject in ("思想政治", "道德与法治"):
        return _cq("我国宪法规定，国家的一切权力属于（　　）",
                   ["人民", "政府", "政党", "军队"], 0,
                   "宪法第二条：中华人民共和国的一切权力属于人民。")
    return None


_GEO_BANK = [
    (("等高线",), "在等高线地形图上，等高线密集处表示（　　）",
     ["坡度陡", "坡度缓", "海拔低", "为山谷"], 0,
     "等高线越密集坡度越陡，越稀疏坡度越缓；等高线向高处凸为山谷，向低处凸为山脊。"),
    (("等值线", "等温线"), "同一等高线图上，等高线向海拔高处凸出的部位是（　　）",
     ["山谷", "山脊", "鞍部", "陡崖"], 0,
     "等高线凸向高处→山谷(易发育河流)；凸向低处→山脊(分水岭)。"),
    (("板块运动", "海陆变迁"), "根据板块构造学说，红海面积不断扩大的原因是（　　）",
     ["位于生长边界，板块张裂", "位于消亡边界，板块碰撞", "地壳下沉", "海水增多"], 0,
     "红海处于非洲板块与印度洋板块的生长(张裂)边界，将来可能形成新大洋。"),
    (("火山地震", "火山", "地震"), "世界上火山地震主要分布在（　　）",
     ["环太平洋和地中海—喜马拉雅带", "大洋中部", "内陆平原", "极地地区"], 0,
     "火山地震带集中在板块交界处：环太平洋带和地中海—喜马拉雅带。"),
    (("七大洲",), "面积最大和最小的大洲分别是（　　）",
     ["亚洲、大洋洲", "非洲、欧洲", "北美洲、南极洲", "亚洲、欧洲"], 0,
     "七大洲面积：亚>非>北美>南美>南极>欧>大洋洲；亚洲最大，大洋洲最小。"),
    (("四大洋",), "面积最大、最深的大洋是（　　）",
     ["太平洋", "大西洋", "印度洋", "北冰洋"], 0,
     "四大洋：太>大西>印度>北冰洋；太平洋最大最深，北冰洋最小最浅。"),
    (("气候类型",), "全年高温多雨、以热带雨林为典型植被的气候是（　　）",
     ["热带雨林气候", "热带草原气候", "地中海气候", "温带季风气候"], 0,
     "热带雨林气候分布在赤道附近，全年高温多雨(>2000mm)，如亚马孙、刚果盆地。"),
    (("影响气候因素",), "影响气候的主要因素不包括（　　）",
     ["植被颜色", "纬度位置", "海陆分布", "地形地势"], 0,
     "影响气候的主要因素：纬度、海陆、地形、洋流、大气环流；植被是结果非成因。"),
    (("季风",), "我国东部季风区夏季盛行（　　）",
     ["东南风和西南风(海洋吹向陆地)", "西北风", "东北风", "偏西风"], 0,
     "夏季陆地增温快气压低，风从海洋(高压)吹向陆地，多东南、西南季风，带来降水。"),
    (("气压带风带",), "赤道低气压带控制下的地区，天气特点是（　　）",
     ["盛行上升气流，多阴雨", "盛行下沉气流，干燥", "多大风", "寒冷干燥"], 0,
     "赤道低压带受热气流上升，多对流雨；副热带高压带下沉，干燥少雨。"),
    (("热力环流",), "关于热力环流，下列说法正确的是（　　）",
     ["近地面受热处气压低，气流上升", "受热处气压高", "冷却处气流上升", "高空与近地面气压相同"], 0,
     "热力环流：受热→气流上升→近地面低压；冷却→下沉→近地面高压。海陆风、山谷风同理。"),
    (("洋流",), "关于洋流对地理环境的影响，正确的是（　　）",
     ["暖流增温增湿，寒流降温减湿", "暖流降温", "寒流增湿", "洋流与气候无关"], 0,
     "暖流对沿岸增温增湿(如西欧温带海洋性气候)，寒流降温减湿(如沿岸荒漠)。"),
    (("水循环",), "人类活动对水循环影响最直接的环节是（　　）",
     ["地表径流", "蒸发", "水汽输送", "降水"], 0,
     "修水库、跨流域调水、灌溉主要影响地表径流环节。海陆间循环是最重要的循环。"),
    (("海水运动", "海水"), "海水盐度最高的海区大致位于（　　）",
     ["副热带海区", "赤道海区", "极地海区", "河流入海口"], 0,
     "盐度从副热带向两侧递减；红海是盐度最高的海(蒸发强降水少)，波罗的海最低。"),
    (("正午太阳高度",), "北半球正午太阳高度达到一年中最大值的日期，多数地区是（　　）",
     ["夏至日", "冬至日", "春分日", "秋分日"], 0,
     "夏至日太阳直射北回归线，北回归线及以北地区正午太阳高度全年最大。"),
    (("昼夜长短",), "北半球夏至日，下列现象正确的是（　　）",
     ["北极圈内出现极昼", "南极圈内极昼", "全球昼夜等长", "赤道昼长夜短"], 0,
     "夏至太阳直射北回归线，北半球昼最长夜最短，北极圈及以北极昼。"),
    (("自转",), "地球自转产生的地理现象是（　　）",
     ["昼夜交替和地方时差", "四季变化", "五带划分", "正午太阳高度年变化"], 0,
     "自转→昼夜交替、时差、地转偏向力；公转→四季、五带、昼夜长短变化。"),
    (("公转",), "地球公转的方向和周期分别是（　　）",
     ["自西向东，约365.25天", "自东向西，24小时", "自西向东，24小时", "自东向西，1个月"], 0,
     "公转自西向东，周期一恒星年约365.25天，产生四季更替和五带。"),
    (("四季五带", "五带"), "地球五带中，既无阳光直射又无极昼极夜现象的是（　　）",
     ["温带", "热带", "寒带", "赤道"], 0,
     "热带有直射，寒带有极昼极夜，温带既无直射也无极昼极夜，四季分明。"),
    (("地域分异", "自然带", "地域", "整体性与差异"), "从赤道到两极的地域分异规律，其形成的主导因素是（　　）",
     ["热量(纬度)", "水分", "海拔", "洋流"], 0,
     "由赤道到两极(纬度地带性)以热量为基础；从沿海到内陆(经度地带性)以水分为基础。"),
    (("内力",), "下列地貌主要由内力作用形成的是（　　）",
     ["喜马拉雅山脉隆起", "长江三角洲", "黄土高原沟壑", "沙丘"], 0,
     "内力作用(地壳运动、岩浆、变质)使地表隆起或凹陷；外力作用削高填低。"),
    (("外力",), "下列地貌由风力沉积作用形成的是（　　）",
     ["沙丘和黄土高原", "V形谷", "喀斯特溶洞", "花岗岩球状风化"], 0,
     "风力沉积→沙丘、黄土;流水侵蚀→V形谷;流水沉积→冲积平原、三角洲。"),
    (("地貌",), "喀斯特(岩溶)地貌主要形成于（　　）",
     ["可溶性岩石地区的流水溶蚀", "干旱区风力侵蚀", "冰川刨蚀", "火山喷发"], 0,
     "喀斯特地貌是含CO₂的水对石灰岩溶蚀形成，如桂林山水、云贵石林。"),
    (("岩石圈", "地壳物质"), "关于三大类岩石，下列说法正确的是（　　）",
     ["岩浆岩由岩浆冷凝形成", "沉积岩由岩浆形成", "变质岩最古老无化石", "花岗岩是沉积岩"], 0,
     "岩浆岩(玄武岩/花岗岩)由岩浆冷凝;沉积岩含化石有层理;变质岩由高温高压变质而成。"),
    (("农业区位", "农业", "因地制宜"), "影响农业生产的主导区位因素中，属于社会经济因素的是（　　）",
     ["市场和交通", "气候", "地形", "水源"], 0,
     "自然因素:气候、地形、土壤、水源;社会经济:市场、交通、政策、劳动力、科技。"),
    (("工业区位", "工业"), "钢铁工业布局的主导区位因素通常是（　　）",
     ["原料和燃料(动力)", "市场", "技术", "劳动力"], 0,
     "钢铁属原料指向型(近铁矿煤矿);电子装配属劳动力指向;啤酒属市场指向。"),
    (("交通区位", "交通运输", "交通"), "现代城市和商业网点区位选择最重要的因素往往是（　　）",
     ["交通便利程度", "气候", "地形", "植被"], 0,
     "交通最优原则:商业网点、城市多沿交通干线、交通枢纽分布。"),
    (("人口问题", "人口", "容量"), "发达国家目前面临的主要人口问题是（　　）",
     ["人口老龄化、劳动力不足", "人口增长过快", "就业困难", "资源紧张"], 0,
     "发达国家:老龄化、增长缓慢;发展中国家:增长过快、就业和资源压力大。"),
    (("迁移", "人口迁移"), "改革开放后我国人口迁移的主要方向是（　　）",
     ["由农村向城市、由内地向沿海", "由城市向农村", "由沿海向内地", "由南向北"], 0,
     "现阶段人口迁移主因是经济，方向为农村→城市、内地→沿海经济发达区。"),
    (("城市", "城乡空间", "城市化"), "城市化水平的最主要衡量指标是（　　）",
     ["城市人口占总人口的比重", "城市数量", "城市用地面积", "高楼数量"], 0,
     "城市化最重要标志是城市人口比重上升;过快会带来交通、住房、环境问题。"),
    (("秦岭淮河",), "秦岭—淮河一线大致是（　　）",
     ["1月0℃等温线和800mm年等降水量线", "季风区非季风区界线", "地势二三级阶梯界线", "内外流区界线"], 0,
     "秦岭淮河是我国重要地理界线:1月0℃等温线、800mm等降水量线、南北方分界。"),
    (("长江",), "长江被誉为‘黄金水道’，主要因为其（　　）",
     ["航运价值高，通航里程长", "含沙量大", "结冰期长", "落差大水能少"], 0,
     "长江水量大、无结冰期、通航里程长，航运价值居全国首位。"),
    (("黄河",), "治理黄河的关键是（　　）",
     ["加强中游黄土高原水土保持", "下游修堤", "上游发电", "河口清淤"], 0,
     "黄河‘地上河’根源是中游黄土高原水土流失，治本在中游植树种草保持水土。"),
    (("遥感RS", "遥感"), "要快速获取洪涝灾害淹没范围的地理信息技术是（　　）",
     ["遥感(RS)", "全球定位系统(GPS)", "地理信息系统(GIS)", "数字地球"], 0,
     "RS负责获取信息(拍);GPS定位导航(测);GIS分析处理(算)。"),
    (("全球定位GPS", "全球定位"), "野外考察中确定自己所处经纬度位置，应使用（　　）",
     ["全球定位系统(GPS)", "遥感(RS)", "地理信息系统(GIS)", "指南针"], 0,
     "GPS主要功能是定位和导航,提供三维坐标、速度和时间。"),
    (("地理信息系统GIS", "地理信息系统"), "对城市各类数据进行叠加分析、择优选址应使用（　　）",
     ["地理信息系统(GIS)", "遥感(RS)", "全球定位(GPS)", "数字地球"], 0,
     "GIS用于地理数据的存储、查询、叠加分析和决策,如选址、灾情评估。"),
    (("一带一路", "区域合作"), "‘一带一路’倡议中，‘一路’指的是（　　）",
     ["21世纪海上丝绸之路", "陆上丝绸之路", "京广铁路", "长江经济带"], 0,
     "‘一带’指丝绸之路经济带(陆上),‘一路’指21世纪海上丝绸之路。"),
    (("大气",), "近地面大气的主要、直接热源是（　　）",
     ["地面辐射", "太阳辐射", "大气逆辐射", "地球内部"], 0,
     "太阳暖大地→大地暖大气:地面辐射是近地面大气最主要的直接热源。"),
    (("受热过程",), "多云的夜晚气温通常比晴朗夜晚高，主要因为（　　）",
     ["云层增强大气逆辐射，保温作用强", "云层反射太阳光", "云层吸收地面热量", "云层阻挡冷空气"], 0,
     "夜晚云层强化大气逆辐射,把地面损失的热量还给地面,保温作用强,昼夜温差小。"),
]

_GEO_REGION_BANK = [
    (("日本",), "关于日本地理，下列叙述正确的是（　　）",
     ["是东亚岛国，地狭人稠、多火山地震", "是内陆国家", "面积广大资源丰富", "位于南半球"], 0,
     "日本是太平洋西北的岛国(北海道·本州·九州·四国)，多山多火山地震、资源贫乏、经济发达。"),
    (("东南亚",), "东南亚地处（　　）之间的‘十字路口’",
     ["亚洲与大洋洲、太平洋与印度洋", "欧洲与非洲", "南北美洲", "亚洲与欧洲"], 0,
     "东南亚连接两洲两洋，马六甲海峡是海上交通咽喉;气候湿热、盛产稻米与热带经济作物。"),
    (("印度",), "印度主要的气候类型及主要粮食作物是（　　）",
     ["热带季风;水稻和小麦", "温带大陆性;玉米", "地中海;橄榄", "寒带;青稞"], 0,
     "印度以热带季风气候为主，西南季风带来降水;主要粮食是水稻(东北)和小麦(西北)。"),
    (("俄罗斯",), "关于俄罗斯地理，正确的是（　　）",
     ["世界面积最大、跨欧亚两洲", "面积最小", "全部位于热带", "是岛国"], 0,
     "俄罗斯世界面积第一，地跨欧亚，以温带大陆性气候为主，自然资源极其丰富。"),
    (("中东",), "中东地区最突出的自然地理特征是（　　）",
     ["石油资源丰富、气候干旱缺水", "森林广布", "终年温和多雨", "平原广阔"], 0,
     "中东是世界石油宝库(波斯湾),但大部分为热带沙漠气候,干旱缺水,水资源成焦点。"),
    (("欧洲西部",), "欧洲西部深受（　　）影响，温带海洋性气候广布",
     ["西风和北大西洋暖流", "副热带高压", "极地东风", "地形闭塞"], 0,
     "受西风和北大西洋暖流影响,欧洲西部终年温和湿润,乳畜业发达。"),
    (("撒哈拉以南非洲",), "撒哈拉以南非洲的经济发展水平与气候主要是（　　）",
     ["以热带气候为主，多为发展中国家", "全为发达国家", "寒带气候", "以温带海洋性为主"], 0,
     "本区以热带气候为主,单一商品经济、总体欠发达;是黑种人故乡、人口自然增长率高。"),
    (("澳大利亚",), "关于澳大利亚，正确的是（　　）",
     ["独占一块大陆，特有动物有袋鼠、鸸鹋", "与亚洲相连", "动物与欧洲相同", "全为沙漠"], 0,
     "澳大利亚独占澳大利亚大陆,长期孤立使特有动物多(袋鼠、考拉、鸸鹋、鸭嘴兽);骑在羊背上的国家。"),
    (("美国",), "关于美国地理，正确的是（　　）",
     ["地跨北美洲，地形分三大南北纵列带", "全在南美洲", "以热带为主", "没有平原"], 0,
     "美国本土地处北温带,地形三大纵列:西部山地、中部大平原、东部低山;农业区专业化。"),
    (("巴西",), "巴西最显著的自然地理特征是（　　）",
     ["拥有世界最大热带雨林(亚马孙)", "全为沙漠", "以温带草原为主", "没有河流"], 0,
     "巴西南部的亚马孙平原是世界最大热带雨林区,亚马孙河流量最大;咖啡、甘蔗等热带作物重要。"),
    (("南极",), "关于南极地区，正确的是（　　）",
     ["是冰雪高原、淡水资源最丰富、无常住居民", "全年炎热", "人口稠密", "没有冰盖"], 0,
     "南极洲是世界最冷、风最大、海拔最高的大陆,冰层储有全球大部淡水,科考价值高。"),
    (("北极",), "北极地区的主体是（　　）",
     ["北冰洋(及其周边陆地)", "南极洲", "太平洋", "撒哈拉沙漠"], 0,
     "北极以海洋(北冰洋)为中心,周围为亚、欧、北美陆地;代表动物是北极熊,有因纽特人。"),
    (("位置优越", "疆域"), "我国濒临的海洋自北向南依次是（　　）",
     ["渤海、黄海、东海、南海", "南海、东海、黄海、渤海", "黄海、渤海、南海、东海", "东海、南海、渤海、黄海"], 0,
     "我国东临太平洋,自北向南临渤海、黄海、东海、南海;海域辽阔,岛屿众多。"),
    (("行政区划",), "我国面积最大、邻国最多的省级行政区是（　　）",
     ["新疆", "西藏", "内蒙古", "黑龙江"], 0,
     "新疆维吾尔自治区面积最大、陆地邻国最多(8个);首府乌鲁木齐。"),
    (("人口",), "关于我国人口，正确的是（　　）",
     ["基数大、增长趋缓、老龄化加剧", "数量很少", "全部分布在西部", "没有城乡差异"], 0,
     "我国是世界人口大国,基数大;近年增速放缓、老龄化加深,人口政策随之调整。"),
    (("民族",), "关于我国民族，正确的是（　　）",
     ["汉族为主、少数民族聚居边疆、民族多样", "单一民族", "少数民族都在东部", "无自治地方"], 0,
     "我国56个民族,汉族占多数;少数民族多分布在边疆,实行民族区域自治。"),
    (("地形地势",), "我国地势的总体特征是（　　）",
     ["西高东低，呈三级阶梯分布", "东高西低", "中部高四周低", "平坦无起伏"], 0,
     "我国地势西高东低、三级阶梯;使大河多东流入海,阶梯交界处水能丰富。"),
    (("长江",), "长江上、中、下游的分界分别是（　　）",
     ["宜昌、湖口", "重庆、武汉", "攀枝花、南京", "宜宾、上海"], 0,
     "以湖北宜昌、江西湖口划分上中下游;上游落差大水能丰,中游荆江‘九曲回肠’。"),
    (("黄河",), "黄河下游形成‘地上河’的主要原因是（　　）",
     ["中游水土流失、下游泥沙淤积河床抬高", "下游降水多", "上游水库太多", "结冰期长"], 0,
     "黄河含沙量大,下游进入平原流速减慢,泥沙淤积使河床高出地面,成‘地上河’。"),
    (("水资源",), "关于我国水资源，正确的是（　　）",
     ["南多北少、东多西少，时空分布不均", "全国均匀", "北多南少", "西部最多"], 0,
     "我国水资源南多北少、东多西少,夏秋多冬春少;南水北调工程缓解北方缺水。"),
    (("交通运输",), "我国最重要的南北铁路干线之一是（　　）",
     ["京广线", "陇海线", "沪杭线", "滨洲线"], 0,
     "京广线(北京—广州)是南北大动脉;陇海—兰新是东西向干线。"),
    (("农业", "因地制宜"), "我国东部季风区发展种植业的有利条件是（　　）",
     ["雨热同期", "终年寒冷", "干旱少雨", "地形全为高原"], 0,
     "东部季风区夏季高温多雨、雨热同期,利于农作物生长;西部干旱半干旱以牧业为主。"),
    (("工业",), "我国四大工业基地中，全国最大综合性工业基地是（　　）",
     ["沪宁杭(长江三角洲)", "辽中南", "京津唐", "珠江三角洲"], 0,
     "沪宁杭工业基地(以上海为中心)规模最大、结构最全;辽中南为重工业基地。"),
    (("四大区域", "界线"), "我国南方地区与北方地区的分界线是（　　）",
     ["秦岭—淮河一线", "大兴安岭", "昆仑山—祁连山", "横断山脉"], 0,
     "秦岭—淮河是南北方分界:1月0℃等温线、800mm等降水量线,南稻北麦。"),
    (("东北",), "关于我国东北地区，正确的是（　　）",
     ["山环水绕、沃野千里，是我国重要商品粮基地", "全为沙漠", "无平原", "终年炎热"], 0,
     "东北‘山环水绕、沃野千里’,黑土肥沃,是我国最大商品粮基地(玉米、大豆、水稻)。"),
    (("黄土高原",), "黄土高原最突出的生态环境问题是（　　）",
     ["水土流失严重", "沙漠扩张", "酸雨", "地面沉降"], 0,
     "黄土土质疏松、植被少、降水集中,水土流失严重;治理靠植树种草、打坝淤地、修梯田。"),
    (("长江三角洲",), "长江三角洲地区的核心城市是（　　）",
     ["上海", "南京", "杭州", "苏州"], 0,
     "上海是长三角核心城市,也是我国经济、金融、贸易中心;长三角为我国最发达区域之一。"),
    (("港澳",), "关于香港、澳门，正确的是（　　）",
     ["是我国的特别行政区，实行‘一国两制’", "是省份", "实行大陆相同制度", "无自由港地位"], 0,
     "香港、澳门是特别行政区,1997、1999回归,‘一国两制’、高度自治;香港是自由港、金融中心。"),
    (("台湾",), "关于台湾岛，正确的是（　　）",
     ["是我国第一大岛，隔台湾海峡与福建相望", "是第二大岛", "属于菲律宾", "全为沙漠"], 0,
     "台湾岛是我国第一大岛,西隔台湾海峡与福建相望;山地为主、东部多,森林与‘宝岛’之称。"),
    (("西北地区",), "我国西北地区最突出的自然特征是（　　）",
     ["干旱，年降水量少", "湿润多雨", "终年高温", "冰川广布"], 0,
     "西北深居内陆、距海远,干旱少雨;植被由东向西草原→荒漠草原→荒漠,灌溉农业(绿洲、河谷)。"),
    (("青藏地区",), "青藏地区最突出的自然特征是（　　）",
     ["高寒(海拔高、气温低)", "湿热", "干旱", "温和多雨"], 0,
     "青藏地区‘高寒’:世界屋脊、海拔高气温低;河谷农业(雅鲁藏布江、湟水)种植青稞。"),
    (("三江源",), "‘三江源’是指（　　）的源头地区",
     ["长江、黄河、澜沧江", "珠江、松花江、辽河", "尼罗河、刚果河、尼日尔河", "密西西比河、亚马孙河"], 0,
     "三江源在青海,是长江、黄河、澜沧江的发源地,号称‘中华水塔’,需加强生态保护。"),
]


def _geo_quiz(s, i):
    for entry in _GEO_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    for entry in _GEO_REGION_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    if "经纬" in s or "经线" in s or "纬线" in s:
        return _cq("本初子午线是指（　　）",
                   ["0°经线", "180°经线", "赤道", "南北回归线"], 0,
                   "本初子午线即0°经线，通过英国格林尼治天文台旧址。")
    if "地球" in s and ("形状" in s or "大小" in s):
        return _cq("地球的真实形状是（　　）",
                   ["两极稍扁、赤道略鼓的不规则球体", "正圆球体", "平面", "长椭球体"], 0,
                   "地球是两极稍扁、赤道略鼓的不规则球体。")
    if "气候" in s or "温度带" in s or "降水" in s:
        return _cq("气候的两大基本要素是（　　）",
                   ["气温和降水", "风和云", "光照和湿度", "海拔和纬度"], 0,
                   "气温和降水是描述气候的两大基本要素。")
    if "地形" in s or "高原" in s or "平原" in s or "山脉" in s:
        return _cq("世界上最高的高原是（　　）",
                   ["青藏高原", "巴西高原", "云贵高原", "帕米尔高原"], 0,
                   "青藏高原平均海拔4000m以上，世界最高，号称‘世界屋脊’。")
    if "地图" in s or "比例尺" in s or "方向" in s:
        return _cq("地图上‘上北下南，左西右东’指的是（　　）",
                   ["一般定向法", "指向标定向", "经纬网定向", "指南针定向"], 0,
                   "无指向标和经纬网时，默认‘上北下南左西右东’为一般定向法。")
    if "人口" in s or "人种" in s or "语言" in s or "聚落" in s:
        return _cq("世界上使用人数最多的语言是（　　）",
                   ["汉语", "英语", "西班牙语", "阿拉伯语"], 0,
                   "汉语是使用人数最多的语言；英语是使用范围最广的语言。")
    if "自转" in s or "公转" in s or "昼夜" in s or "四季" in s or "地球运动" in s:
        return _cq("地球公转产生的地理现象是（　　）",
                   ["四季变化", "昼夜交替", "地方时差", "日月东升西落"], 0,
                   "公转产生四季、五带、极昼极夜；自转产生昼夜交替和时差。")
    if "温度带" in s or "五带" in s or "回归线" in s or "极圈" in s:
        return _cq("热带与温带的分界线是（　　）",
                   ["回归线(23.5°)", "极圈", "赤道", "本初子午线"], 0,
                   "回归线是热带与温带分界；极圈是温带与寒带分界。")
    if "降水" in s or "季风" in s:
        return _cq("我国东部地区降水主要集中在（　　）",
                   ["夏秋季节", "冬春季节", "全年均匀", "仅在冬季"], 0,
                   "受夏季风影响，我国降水集中在夏秋，南方多于北方。")
    if "河流" in s or "长江" in s or "黄河" in s or "湖泊" in s:
        return _cq("我国长度最长的河流是（　　）",
                   ["长江", "黄河", "珠江", "黑龙江"], 0,
                   "长江全长约6300km，我国第一长河；黄河第二。")
    return None


_SCI_BANK = [
    (("声音的产生", "声音"), "声音是由物体（　　）产生的",
     ["振动", "反射", "膨胀", "发热"], 0,
     "一切正在发声的物体都在振动,振动停止发声也停止。"),
    (("声音的传播",), "声音不能在（　　）中传播",
     ["真空", "空气", "水", "钢铁"], 0,
     "声音靠介质(固、液、气)传播,真空不能传声;声在固体中传得最快。"),
    (("音调高低", "音调"), "决定声音音调高低的是（　　）",
     ["振动频率", "振动幅度", "声源材料", "距离远近"], 0,
     "音调由频率决定,频率越高音调越高;响度由振幅决定。"),
    (("音量大小", "响度"), "决定声音响度大小的主要因素是（　　）",
     ["振动幅度", "振动频率", "音色", "介质种类"], 0,
     "响度由振幅决定,振幅越大响度越大;还与距声源远近有关。"),
    (("噪声控制", "噪声"), "在马路两旁植树造林，控制噪声的途径是（　　）",
     ["在传播过程中减弱噪声", "在声源处减弱", "在人耳处减弱", "无法减弱"], 0,
     "控制噪声三途径:声源处、传播过程中、人耳处;绿化带属传播过程中减弱。"),
    (("光源",), "下列物体中属于光源的是（　　）",
     ["点燃的蜡烛", "月亮", "镜子", "白纸"], 0,
     "自身能发光的物体叫光源,如太阳、蜡烛;月亮、镜子只反光,不是光源。"),
    (("光的直线传播", "直线传播"), "下列现象由光的直线传播形成的是（　　）",
     ["影子和日食", "水中倒影", "筷子在水中变弯", "彩虹"], 0,
     "光在同种均匀介质中沿直线传播,形成影子、小孔成像、日食月食。"),
    (("反射",), "我们能从各个方向看到不发光的物体，是因为光在物体表面发生了（　　）",
     ["漫反射", "镜面反射", "折射", "色散"], 0,
     "凹凸不平表面把光反射向四面八方(漫反射),故各方向都能看到物体。"),
    (("折射",), "把筷子斜插入水中，看上去筷子在水面处向上弯折，这是光的（　　）",
     ["折射现象", "反射现象", "直线传播", "色散现象"], 0,
     "光从水斜射入空气时发生折射,折射光线偏离法线,看起来筷子‘变弯’。"),
    (("彩虹",), "雨后天空出现彩虹，这主要是由于阳光发生了（　　）",
     ["色散(折射分解)", "反射", "直线传播", "吸收"], 0,
     "阳光被空中小水珠折射、色散成七色光,形成彩虹,说明白光是复色光。"),
    (("磁铁吸铁",), "磁铁能吸引的物质是（　　）",
     ["铁、钴、镍", "铜", "铝", "塑料"], 0,
     "磁铁只吸引铁、钴、镍等铁磁性物质,不吸引铜、铝、塑料、木头。"),
    (("磁极",), "磁铁上磁性最强的部位是（　　）",
     ["两个磁极", "中间", "整体均匀", "N极最强S极最弱"], 0,
     "磁铁两端磁极磁性最强,中间最弱;悬空静止后指南的是S极、指北的是N极。"),
    (("同极相斥异极相吸",), "两块磁铁互相靠近时会相互排斥，说明靠近的两极是（　　）",
     ["同名磁极", "异名磁极", "一个N一个S", "都没有磁性"], 0,
     "磁极间作用:同名磁极相互排斥,异名磁极相互吸引。"),
    (("指南针",), "指南针能指示方向，是因为它受到（　　）的作用",
     ["地磁场", "重力", "太阳光", "空气流动"], 0,
     "指南针是小磁针,在地磁场作用下静止时N极指向地理北方(地磁南极)。"),
    (("溶解",), "下列物质放入水中能溶解的是（　　）",
     ["白糖", "面粉", "沙子", "食用油"], 0,
     "白糖、食盐能均匀溶解在水里形成溶液;沙、面粉、油不能溶解。"),
    (("加快溶解",), "下列做法中不能加快食盐溶解的是（　　）",
     ["降低水温", "搅拌", "把食盐研碎", "用热水"], 0,
     "加快溶解方法:搅拌、加热(升温)、把固体碾碎;降温会减慢溶解。"),
    (("过滤",), "用过滤的方法可以把（　　）",
     ["不溶的固体与液体分开", "溶解的糖从糖水中分出", "两种液体分开", "气体分开"], 0,
     "过滤能分离不溶性固体和液体(如泥水);要分离已溶解的物质需用蒸发结晶。"),
    (("蒸发结晶",), "要从食盐水中得到食盐固体，应采用的方法是（　　）",
     ["蒸发结晶", "过滤", "沉淀", "静置"], 0,
     "食盐已溶解,过滤无效,须蒸发水分使食盐结晶析出。"),
    (("沉浮",), "把一块橡皮泥捏成小船能浮在水面，主要是因为（　　）",
     ["做成船形排开水的体积增大，浮力增大", "橡皮泥质量变小", "水的密度变大", "空气托住"], 0,
     "改变形状增大排水体积,受到的浮力增大到大于重力,物体就上浮。"),
    (("浮力",), "物体在水中受到浮力的方向总是（　　）",
     ["竖直向上", "竖直向下", "水平方向", "指向物体中心"], 0,
     "浮力方向竖直向上;浸入液体的物体都受浮力,大小等于排开液体所受重力。"),
    (("重力",), "地球附近物体由于地球吸引而受到的力叫（　　）",
     ["重力", "弹力", "摩擦力", "浮力"], 0,
     "重力由地球吸引产生,方向竖直向下,作用点在重心;g≈9.8N/kg。"),
    (("弹力",), "被压弯的弹簧、拉长的橡皮筋能产生弹力，是因为它们发生了（　　）",
     ["弹性形变", "塑性形变", "位置改变", "温度变化"], 0,
     "物体发生弹性形变后要恢复原状,对接触物体产生弹力,如支持力、拉力。"),
    (("摩擦力",), "下列способ中能增大摩擦的是（　　）",
     ["在鞋底刻上花纹", "给车轴加润滑油", "使接触面更光滑", "用滚动代替滑动"], 0,
     "增大摩擦:增大压力、使接触面粗糙;减小摩擦:光滑、润滑、滚动代滑、气垫。"),
    (("杠杆",), "使用撬棒撬石头，这种杠杆属于（　　）",
     ["省力杠杆", "费力杠杆", "等臂杠杆", "不省力也不费力"], 0,
     "动力臂大于阻力臂时省力(如撬棒、羊角锤);小于时费力(如筷子、镊子)。"),
    (("滑轮",), "使用定滑轮的作用是（　　）",
     ["改变力的方向，不省力", "省一半力", "省距离", "既省力又改变方向"], 0,
     "定滑轮不省力但能改变力的方向;动滑轮省一半力但费距离,不能改变方向。"),
    (("斜面",), "盘山公路修成盘旋状，主要利用了斜面（　　）的原理",
     ["坡度越小越省力", "坡度越大越省力", "缩短距离", "增大摩擦"], 0,
     "斜面是省力机械,斜面越长越平缓(坡度越小),越省力,但通过距离越长。"),
    (("轮轴",), "水龙头、方向盘都属于（　　）",
     ["轮轴", "杠杆", "滑轮", "斜面"], 0,
     "轮轴是能连续旋转的杠杆,在轮上用力省力(如水龙头、方向盘、门把手)。"),
    (("温度与温度计", "温度计"), "使用温度计测液体温度时，正确的是（　　）",
     ["玻璃泡全部浸入液体，不碰容器壁和底", "玻璃泡碰底", "拿出后再读数", "只浸入一半"], 0,
     "温度计玻璃泡全浸入且不接触容器壁和底,待示数稳定后不拿出、视线与液面相平读数。"),
    (("蒸发",), "夏天在地上洒水感觉凉快，是因为水蒸发时（　　）",
     ["吸收热量", "放出热量", "温度升高", "体积变大放热"], 0,
     "蒸发是汽化的一种,在任何温度下进行且吸热,有致冷作用。"),
    (("凝结",), "夏天从冰箱取出的饮料瓶外壁出现水珠，这是（　　）",
     ["空气中水蒸气遇冷液化", "瓶内水渗出", "水蒸气升华", "水凝固"], 0,
     "瓶壁温度低,周围空气中水蒸气遇冷液化(放热)成小水珠附在外壁。"),
    (("水的循环", "水循环"), "自然界水循环中，使水从液态变为气态进入大气的环节是（　　）",
     ["蒸发", "降水", "凝结", "径流"], 0,
     "水循环:蒸发→水汽输送→凝结成云→降水→径流,周而复始。"),
    (("月相",), "农历十五前后，我们看到的月相通常是（　　）",
     ["满月", "新月", "上弦月", "下弦月"], 0,
     "月相变化:初一新月(看不见)→初七八上弦月→十五满月→廿二三下弦月。"),
    (("太阳系",), "太阳系中体积最大的行星是（　　）",
     ["木星", "地球", "火星", "土星"], 0,
     "八大行星按离太阳由近到远:水金地火木土天海;木星体积和质量最大。"),
    (("地球的卫星——月球", "月球"), "月球表面没有空气和液态水，所以（　　）",
     ["昼夜温差大、没有声音", "有蓝天白云", "能听到声音", "有生命"], 0,
     "月球无大气:昼夜温差极大、无声音(真空不传声)、天空黑暗、有环形山。"),
    (("食物链",), "在‘草→蝗虫→青蛙→蛇’这条食物链中，草属于（　　）",
     ["生产者", "消费者", "分解者", "非生物"], 0,
     "食物链从生产者(绿色植物)开始,箭头指向捕食者;草是生产者,其余是消费者。"),
    (("消化",), "人体消化食物和吸收营养的主要器官是（　　）",
     ["小肠", "胃", "大肠", "食道"], 0,
     "小肠内有多种消化液、内壁有绒毛,是消化和吸收营养的主要场所。"),
    (("呼吸",), "人体进行气体交换、吸入氧气排出二氧化碳的主要器官是（　　）",
     ["肺", "心脏", "气管", "鼻"], 0,
     "肺是呼吸系统的主要器官,肺泡内完成氧气和二氧化碳的交换。"),
    (("摆",), "同一个单摆，摆动一次所需时间主要取决于（　　）",
     ["摆线的长短", "摆球的质量", "摆动的幅度", "摆球的颜色"], 0,
     "摆的快慢只与摆长有关,摆越长摆动越慢;与摆重、摆幅无关(伽利略发现)。"),
]


def _science_quiz(s, i):
    for entry in _SCI_BANK:
        keys = entry[0]
        if any(k in s for k in keys):
            return _cq(entry[1], list(entry[2]), entry[3], entry[4])
    if "植物" in s or "种子" in s or "根" in s or "叶" in s:
        return _cq("植物生长不需要的条件是（　　）",
                   ["完全黑暗", "阳光", "水分", "适宜温度"], 0,
                   "植物生长需光(光合)、水、适宜温度、CO₂；长期黑暗不能生长。")
    if "动物" in s or "昆虫" in s or "哺乳" in s:
        return _cq("下列动物中属于哺乳动物的是（　　）",
                   ["猫", "鸡", "金鱼", "蝴蝶"], 0,
                   "猫胎生哺乳属哺乳动物；鸡鸟类、金鱼鱼类、蝴蝶昆虫。")
    if "物质" in s or "溶解" in s or "水" in s:
        return _cq("下列物质能溶解在水里的是（　　）",
                   ["食盐", "沙子", "木头", "石头"], 0,
                   "食盐(氯化钠)可溶于水形成溶液；沙/木/石不溶。")
    if "力" in s or "磁铁" in s or "运动" in s:
        return _cq("磁铁能吸引的物质是（　　）",
                   ["铁、钴、镍", "铜", "铝", "木头"], 0,
                   "磁铁吸引铁、钴、镍等铁磁性物质；不吸引铜铝木材。")
    if "地球" in s or "太阳" in s or "月相" in s:
        return _cq("地球自转一周的时间大约是（　　）",
                   ["24小时(1天)", "1个月", "1年", "12小时"], 0,
                   "地球自转周期约24小时产生昼夜交替；公转一周约365天。")
    if "地形" in s or "高原" in s or "平原" in s or "盆地" in s or "丘陵" in s or "山地" in s:
        return _cq("地球上的五种基本地形是（　　）",
                   ["山地、高原、平原、盆地、丘陵", "高原、平原、沙漠、冰川、丘陵", "山地、高原、平原、河流、湖泊", "高原、平原、盆地、峡谷、台地"], 0,
                   "基本地形类型：山地、高原、平原、盆地、丘陵。")
    if "侵蚀" in s or "沉积" in s or "搬运" in s or "风化" in s:
        return _cq("流水、风等外力使地表物质破坏、搬运和堆积，称为（　　）",
                   ["外力作用(风化侵蚀搬运沉积)", "地壳运动", "火山活动", "地震"], 0,
                   "外力作用(风化、侵蚀、搬运、沉积)塑造地表；内力(地壳运动、火山、地震)抬升。")
    if "岩石" in s or "矿物" in s:
        return _cq("下列属于沉积岩的是（　　）",
                   ["砂岩", "花岗岩", "玄武岩", "大理岩"], 0,
                   "砂岩是沉积岩；花岗岩、玄武岩是岩浆岩，大理岩是变质岩。")
    if "土壤" in s:
        return _cq("土壤的形成主要依赖于（　　）",
                   ["岩石风化和生物作用", "海水沉积", "火山喷发", "冰川搬运"], 0,
                   "土壤由岩石风化加生物(植物、微生物)作用长期形成。")
    if "天气" in s or "气温" in s or "降水" in s:
        return _cq("‘今天阴有小雨’描述的是（　　）",
                   ["天气(短时间)", "气候(多年平均)", "季节", "地形"], 0,
                   "天气是短时段大气状况；气候是某地区多年平均状况。")
    if "地震" in s or "火山" in s:
        return _cq("板块交界处地壳活跃，容易引发（　　）",
                   ["地震和火山", "台风", "干旱", "洪涝"], 0,
                   "板块交界地带地壳运动活跃，多地震、火山。")
    return None


def mock_test_q(topic, sub_idx=0, used=None, course_id=None):
    """演示模式（无大模型密钥）下的课后自测题（兜底路径）：基于该子点的真实讲解
    内容抽取出题（计算/填空/换算/概念），题型在 选择/填空/计算 间轮换。
    注：有 Ollama 生成内容时由 _assemble_gen_questions 统一组卷，不走此函数。
    出题优先级：种子题库 > 文本提取(算式/facts/concept) > 数学智能兜底 > 终极兜底"""
    subs = topic.get("sub") or []
    title = topic.get("title", "")
    subject = topic.get("subject", "")
    if not subs:
        subs = [title]
    sub = subs[sub_idx % len(subs)]
    global _cur_tid
    _cur_tid = course_id or topic.get("id") or ""

    # ── 优先级0：种子题库（最可靠）──
    if course_id:
        seed = SB.get_seed_questions(course_id)
        if seed:
            sub_qs = (seed.get("subs") or {}).get(sub, [])
            if sub_qs:
                q = sub_qs[sub_idx % len(sub_qs)]
                return dict(q)  # 返回副本

    # ── 优先级1：全学科智能出题引擎（关键词命中即返回具体考试题）──
    sq = _subject_quiz(subject, sub, title, sub_idx)
    if sq:
        return sq

    text = ""
    try:
        text = C._explain_sub(title, subject, sub, course_id=course_id) or ""
    except Exception:
        text = ""
    calc_expr, calc_ans, terms, warn = _mock_extract(text)
    facts = _mock_facts(text)
    if used is None:
        used = {"facts": set()}
    if "facts" not in used:
        used["facts"] = set()
    def _pick_fact():
        """在本知识点内挑选一个尚未用过的换算关系，避免题目重复。"""
        for fl in facts:
            if fl not in used["facts"]:
                used["facts"].add(fl)
                return fl
        if facts:
            fl = facts[sub_idx % len(facts)]
            used["facts"].add(fl)
            return fl
        return None
    # 文科科目（语文/英语/政治/历史/地理/道德与法治/思想政治）：禁止出数学计算题
    _LIBERAL_ARTS = frozenset({"语文", "英语", "道德与法治", "思想政治", "历史", "地理",
                                "English", "Chinese", "Politics", "History", "Geography"})
    is_liberal = subject in _LIBERAL_ARTS
    kind = sub_idx % 3   # 0→计算题, 1→填空题, 2→选择题
    # 文科科目：kind==0(计算题) 降级为 kind=1(填空题)，避免出现数学算式
    if is_liberal and kind == 0:
        kind = 1

    # —— 计算题（kind 0）—— 仅理科/数学科目可用
    if kind == 0 and calc_expr and calc_ans:
        return {"type": "calc",
                "stem": f"「{sub}」计算题：计算 ${calc_expr}$ 的结果是多少？（只写结果）",
                "options": [], "answer": calc_ans,
                "explanation": f"按「{sub}」的方法，${calc_expr} = {calc_ans}。"}

    # —— 填空题（kind 1）——
    if kind == 1:
        if calc_expr and calc_ans:
            return {"type": "fill",
                    "stem": f"「{sub}」填空题：根据所学方法，${calc_expr}$ 的答案为 ______ 。（只写结果）",
                    "options": [], "answer": calc_ans,
                    "explanation": f"${calc_expr} = {calc_ans}$。"}
        if facts:
            f = _pick_fact()
            if f:
                flabel, fnum, funit = f
                return {"type": "fill",
                        "stem": f"「{sub}」换算填空：{flabel} = ______ {funit}",
                        "options": [], "answer": fnum,
                        "explanation": f"根据进率（定义），{flabel} = {fnum}{funit}。"}

    # —— 选择题（最终兜底：本子点无计算/填空/换算题源时，出概念/辨析题）——
    # 1) 数值选择（仅用本子点自己的算式，不借用其它子点，避免归属错误）→ 文科跳过
    ce, ca = calc_expr, calc_ans
    if ce and ca and not is_liberal:
        try:
            opts = _num_choices(ca)
            random.shuffle(opts)
            answer = opts.index(float(ca))
            return {"type": "choice",
                    "stem": f"「{sub}」选择题：计算 ${ce}$ 的结果是？",
                    "options": [_fmt_num(o) for o in opts], "answer": answer,
                    "explanation": f"${ce} = {ca}$。"}
        except Exception:
            pass
    # 2) 换算数值选择（用 fact）→ 文科跳过
    if facts and not is_liberal:
        f = _pick_fact()
        if f:
            flabel, fnum, funit = f
            try:
                opts = _num_choices(fnum)
                random.shuffle(opts)
                answer = opts.index(float(fnum))
                return {"type": "choice",
                        "stem": f"「{sub}」选择题：{flabel} 等于多少 {funit}？",
                        "options": [_fmt_num(o) for o in opts], "answer": answer,
                        "explanation": f"{flabel} = {fnum}{funit}。"}
            except Exception:
                pass
    # 3) 易错点辨析
    if warn:
        # 干扰项：与子点内容相关的“常见错误认知”（合理但不正确），杜绝垃圾话术
        sibs = [x for x in (C.TOPIC_INDEX.get(_cur_tid, {}).get("sub") or []) if x and x != sub]
        sib = sibs[0] if sibs else (title or "其他概念")
        opts = [warn,
                f"「{sub}」与「{sib}」的含义完全相同，可以互相替换",
                f"「{sub}」的适用范围与「{sib}」一致，无需区分",
                f"「{sub}」的结果与已知条件无关，可直接照搬结论"]
        # 去重，避免 warn 与某干扰项文本恰好相等
        seen = {}
        uniq = []
        for o in opts:
            if o not in seen:
                seen[o] = True
                uniq.append(o)
        opts = uniq
        random.shuffle(opts)
        answer = opts.index(warn)
        return {"type": "choice", "stem": f"「{sub}」：关于易错点，下列说法正确的是？\n（易错提醒：{warn}）",
                "options": opts, "answer": answer,
                "explanation": f"「{sub}」的易错提醒：{warn}。"}

    # 4) 概念辨析（去同义反复）
    concept = _concept_stem(text, sub, title)
    if concept:
        return concept

    # 4.5) 数学学科智能兜底：根据子点名称生成可算题目（彻底消灭垃圾选项）
    if subject == "数学":
        mq = _math_fallback(sub, title, sub_idx)
        if mq:
            return mq

    # 5) 终极兜底（内容极薄、抽不出任何可考素材时）：学科智能变体
    # 根据学科生成合理的概念/方法题（彻底消灭垃圾话术）
    if subject == "数学":
        return _math_fallback(sub, title, sub_idx) or _honest_last(subject, sub, title)

    # 6) 内容挖掘兜底：从真实讲解文本抽取具体事实，构造填空/选择（具体、无废话）
    cq = _content_question(text, sub, title, sub_idx)
    if cq:
        return cq

    # 7) 仍无具体素材：给出该子点归类/定位题（明确属于本课程核心内容）
    return _honest_last(subject, sub, title)



def ai_test_qs(topic, settings, n=5, content_hint=""):
    """课后自测：生成 n 道供学生独立完成、覆盖全部核心内容、且【混合题型】的题目。
    题型包含选择题(choice)、填空题(fill)、计算题(calc)，要求有深度、贴合知识点真实内容。"""
    subs = topic.get("sub") or []
    sub_hint = "、".join(subs) if subs else "见教材"
    sysmsg = ("你是资深出题老师，正在为「课后自测」出卷。题目要能真实、有深度地检验学生是否学会这个知识点，"
              "学生将独立作答（填空/计算需自己写出答案），你需要给出每题的标准答案与解析。\n"
              "重要：数学公式必须用 LaTeX 格式写在 $...$ 内（如 $\\frac{3}{4}$、$x^2$、$\\sqrt{2}$），"
              "前端会自动渲染为可视化公式让学生看懂。")
    prompt = (
        f"知识点：{topic['title']}\n"
        f"核心内容（请逐一覆盖，每个子内容至少出 1 题）：{sub_hint}\n\n"
        f"===== 该知识点各子内容的详细讲解（含公式与例题），请严格依据这些内容出题 =====\n{content_hint}\n"
        f"============================================================================\n\n"
        f"请出 {n} 道【课后自测】题，用于检验学生是否真正学会。要求：\n"
        "1) **题型混合**，不要只有选择题。每题必须带 type 字段：\n"
        "   - type=\"choice\"：单选题（4 个选项 A/B/C/D，只有 1 个正确答案）；\n"
        "   - type=\"fill\"：填空题（在横线/空格处填关键术语、数字或简单表达式，answer 为填空的标准答案）；\n"
        "   - type=\"calc\"：计算题（学生需写出计算过程或结果，answer 为标准结果，可以是数字或 $...$ 表达式）。\n"
        "   建议比例：选择题约 40%、填空题约 30%、计算题约 30%；计算/填空要占相当比例，体现『有计算、填空』。\n"
        f"2) 这 {n} 道题要【覆盖该知识点的全部核心内容】：上面列出的每一个子内容都要考到至少 1 题，"
        "不要遗漏任何一个；可从不同角度（概念理解、公式运用、计算、易错点、实际应用、综合）出题，避免重复考同一角度；\n"
        "3) 题目要有深度：不能只考『下面哪个属于本知识点』这类送分题，要结合真实情境 / 计算 / 概念辨析；\n"
        "4) 字段说明：\n"
        "   - choice 题：options 为 4 个选项文本（字符串数组），answer 为正确选项序号(0-3)；\n"
        "   - fill / calc 题：options 为空数组 []，answer 为该题标准答案（字符串，如 \"96\" 或 \"$\\\\frac{1}{2}$\"）；\n"
        "   - 每题都有 explanation：说明解题思路（2-4 句，说清为什么对、易错在哪）；\n"
        "5) **题干、选项、答案和解析中的数学公式必须用 $...$ 包裹**。\n\n"
        f"只输出一个 JSON 数组（{n} 个对象），不要 markdown 代码块，形如：\n"
        '[{"type":"choice","stem":"题干","options":["A","B","C","D"],"answer":0,"explanation":"..."},'
        '{"type":"fill","stem":"填空题干","options":[],"answer":"标准答案","explanation":"..."},'
        '{"type":"calc","stem":"计算题干","options":[],"answer":"结果","explanation":"..."}]'
    )
    try:
        raw = call_llm([{"role": "system", "content": sysmsg},
                        {"role": "user", "content": prompt}], settings, "zh")
        data = parse_llm_response(raw)
        if not isinstance(data, list):
            data = [data]
        out = []
        for obj in data:
            t = str(obj.get("type") or "choice")
            stem = str(obj.get("stem") or "")
            opts = obj.get("options") or []
            ans_raw = obj.get("answer")
            if t == "choice":
                if len(opts) < 2:
                    continue
                try:
                    ans = int(ans_raw)
                except Exception:
                    ans = 0
                if ans < 0 or ans >= len(opts):
                    ans = 0
                out.append({"type": "choice", "stem": stem, "options": [str(o) for o in opts],
                           "answer": ans, "explanation": str(obj.get("explanation") or "")})
            else:
                # fill / calc：answer 为字符串
                ans = str(ans_raw) if ans_raw is not None else ""
                if not ans.strip():
                    continue
                out.append({"type": t, "stem": stem, "options": [],
                           "answer": ans, "explanation": str(obj.get("explanation") or "")})
        if len(out) >= 1:
            # 补足到 n 道，避免模型少出（用演示题兜底，保证题型混合）
            while len(out) < n:
                out.append(mock_test_q(topic, len(out)))
            return out[:n]
    except Exception:
        pass
    return [mock_test_q(topic, i) for i in range(n)]


def _norm_answer(a, b):
    """填空题/计算题答案的宽松比对：去 $ 包裹、统一运算符、去空格，并做数值比对。"""
    def norm(s):
        s = str(s).strip()
        s = s.replace("$", "")
        s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1/\2)", s)
        s = s.replace("\\times", "*").replace("×", "*").replace("\\div", "/").replace("÷", "/")
        s = s.replace("（", "(").replace("）", ")")
        s = s.replace(" ", "")
        return s
    na, nb = norm(a), norm(b)
    if na == nb:
        return True
    def nums(s):
        m = re.findall(r"[-+]?[0-9]*\.?[0-9]+", s)
        return [float(x) for x in m] if m else None
    va, vb = nums(na), nums(nb)
    if va and vb and va == vb:
        return True
    return False


def eval_mastery_level(accuracy, avg_time):
    """根据正确率与平均用时判定掌握度等级（0-4）。正确率为主，时间为辅。"""
    if accuracy >= 100:
        lv = 4
    elif accuracy >= 80:
        lv = 3
    elif accuracy >= 60:
        lv = 2
    else:
        lv = 1
    # 时间惩罚：全对但极慢 / 高分但明显耗时 → 降一档（说明不熟练）
    if accuracy >= 100 and avg_time > 75:
        lv = 3
    elif accuracy >= 80 and avg_time > 100:
        lv = 2
    elif accuracy >= 60 and avg_time > 130:
        lv = 1
    return lv


def ai_evaluate_test(topic_title, subs, results, accuracy, avg_time, total_time, settings):
    """让 AL 根据作答情况（正确率、用时、错题）给出掌握判定与复习建议。"""
    wrong = [r for r in results if not r.get("correct")]
    wrong_text = ""
    for r in wrong:
        ans_letter = "ABCD"[r["answer"]] if isinstance(r.get("answer"), int) else str(r.get("answer"))
        wrong_text += f"- 答错题：{r.get('stem','')}（正确答案：{ans_letter}）\n"
    subs_hint = "、".join(subs) if subs else "本知识点核心内容"
    sysmsg = ("你是学习评估与辅导助手。根据学生一次课后自测的作答数据，判断他是否真正学会了这个知识点，"
              "并给出可操作的复习建议。输出严格为 JSON。")
    prompt = (
        f"知识点：「{topic_title}」\n核心子内容：{subs_hint}\n\n"
        f"本次自测数据：\n- 正确率：{accuracy}%（共 {len(results)} 题，答对 {sum(1 for r in results if r.get('correct'))} 题）\n"
        f"- 总用时：{total_time} 秒，平均每题 {avg_time} 秒\n"
        + (wrong_text if wrong_text else "（全部答对）\n")
        + "\n请评估并输出 JSON（不要 markdown 代码块）：\n"
        '{"verdict":"掌握/熟悉/了解/未掌握 四选一",'
        '"reason":"一句话说明判定依据（结合正确率与用时）",'
        '"advice":"若未掌握：给出具体复习步骤，例如：先点「看AI讲解」理解概念→做基础例题→再测；若已掌握：简短鼓励并建议挑战更难题型",'
        '"relearn":["需要重点回看的子知识点1","子知识点2"]}  '
        '# relearn 仅填未掌握时需要回看的子点，已全部掌握则为空数组 []。'
    )
    try:
        raw = call_llm([{"role": "system", "content": sysmsg},
                        {"role": "user", "content": prompt}], settings, "zh")
        obj = parse_llm_response(raw)
        if isinstance(obj, dict) and obj.get("verdict"):
            return obj
    except Exception:
        pass
    # 兜底：按规则生成
    lv = eval_mastery_level(accuracy, avg_time)
    label = MASTERY_LABEL.get(lv, "未掌握")
    if lv >= 4:
        return {"verdict": label, "reason": f"正确率 {accuracy}%，已基本掌握。",
                "advice": "很好！可以挑战更综合或迁移类的题型，巩固熟练度。", "relearn": []}
    return {"verdict": label,
            "reason": f"正确率 {accuracy}%，平均每题 {avg_time} 秒，尚未达到「掌握」标准。",
            "advice": "建议：① 点「📖 看AI讲解」回到概念与例题；② 在「🎯 精准学」做几道基础练习题；③ 再来一次自测检验。",
            "relearn": list(subs) if subs else [topic_title]}


def _cleanup_tts_cache():
    cache_dir = os.path.join(BASE_DIR, "tts_cache")
    if not os.path.isdir(cache_dir):
        return
    now = time.time()
    for name in os.listdir(cache_dir):
        p = os.path.join(cache_dir, name)
        try:
            if name.startswith("tmp") and os.path.isfile(p) and (now - os.path.getmtime(p)) > 3600:
                os.remove(p)
        except OSError:
            pass


def _lan_ip_list():
    """本机可被局域网访问的 IPv4 列表（用于手机填「电脑语音服务器地址」）。"""
    ips = []
    # 首选：让内核按默认路由选出口网卡（UDP connect 不发包，无需外网可达）
    try:
        import socket as _sock
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
        try:
            s.connect(("223.5.5.5", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                ips.append(ip)
        finally:
            s.close()
    except Exception:
        pass
    # 补充：主机名解析出的其他网卡（多网卡/虚拟网卡场景）
    try:
        import socket as _sock
        for ip in _sock.gethostbyname_ex(_sock.gethostname())[2]:
            if ip and not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips


def _lan_endpoints(port):
    return ["%s:%s" % (ip, port) for ip in _lan_ip_list()]


def main():
    init_db()
    ensure_system_roles()
    _cleanup_tts_cache()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.daemon_threads = True  # 慢请求不阻塞服务关闭
    # SO_REUSEADDR：重启时快速复用端口
    try:
        server.socket.setsockopt(__import__("socket").SOL_SOCKET,
                                 __import__("socket").SO_REUSEADDR, 1)
    except Exception:
        pass
    print(f"AL 自学系统已启动： http://localhost:{port}", flush=True)
    _eps = _lan_endpoints(port)
    if _eps:
        # flush=True 必须加：输出被重定向/管道时 Python 会块缓冲，
        # 用户可能盯着黑窗口半天看不到该填的地址，误以为功能坏了。
        print("", flush=True)
        print("★ 手机/平板（尤其华为等无语音引擎的机型）请填这个地址：", flush=True)
        print(f"    {_eps[0]}", flush=True)
        if len(_eps) > 1:
            print(f"  （其余是虚拟网卡，别填：{'、'.join(_eps[1:])}）", flush=True)
        print("  手机需与本电脑连同一个 WiFi；填好后在 App 设置里点「🔌 测试语音服务器」验证。", flush=True)
        print("  若测试不通，多半是 Windows 防火墙拦了 —— 双击「voice_server_firewall.bat」放行一次即可。", flush=True)
    print("按 Ctrl+C 停止。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
        server.shutdown()


if __name__ == "__main__":
    main()

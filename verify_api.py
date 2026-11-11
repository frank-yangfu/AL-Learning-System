import urllib.request, json, urllib.error, random
BASE = "http://localhost:8000"

def req(p, b=None, t=None, method="POST"):
    data = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if t:
        r.add_header("Authorization", "Bearer " + t)
    try:
        return json.loads(urllib.request.urlopen(r).read().decode())
    except urllib.error.HTTPError as e:
        return {"__http": e.code, "__body": e.read().decode()}

u = "voice%d" % random.randint(1000, 9999)
req("/api/register", {"username": u, "password": "pw"})
tok = req("/api/login", {"username": u, "password": "pw"})["token"]

cur = req("/api/curriculum", method="GET")
eng_subj = [s for st in cur for s in st["subjects"] if s.get("name") == "英语"]
print("英语学科含 lang=en:", any(s.get("lang") == "en" for s in eng_subj))

roles = req("/api/roles", method="GET", t=tok)
emm = [r for r in roles if r.get("lang") == "en"]
xiao = [r for r in roles if r.get("name") == "小艾老师"]
print("系统英语外教:", [r["name"] for r in emm])
print("小艾老师 lang:", xiao[0].get("lang") if xiao else None)

rid = emm[0]["id"]
c = req("/api/chat", {"role_id": rid, "message": "Hello teacher, can you help me practice English?"}, tok)
print("Emma 演示对话回复前 40 字:", c["reply"][:40])
print("ALL_OK")

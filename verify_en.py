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

u = "en%d" % random.randint(1000, 9999)
req("/api/register", {"username": u, "password": "pw"})
tok = req("/api/login", {"username": u, "password": "pw"})["token"]
roles = req("/api/roles", method="GET", t=tok)
rid = [r for r in roles if r.get("lang") == "en"][0]["id"]
c = req("/api/chat", {"role_id": rid, "message": "Hello, I want to practice English speaking."}, tok)
print("Emma 演示回复:", c["reply"])
print("含英文模板(Nice question):", "Nice question" in c["reply"])
print("emotion:", c["emotion"])

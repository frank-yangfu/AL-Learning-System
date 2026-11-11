import sqlite3, importlib.util, os

_HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("srv", os.path.join(_HERE, "server.py"))
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)
conn = sqlite3.connect(os.path.join(_HERE, "data", "app.db"))
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id,name,lang FROM roles WHERE user_id=0").fetchall()
print("system roles:", [(r["name"], r["lang"]) for r in rows])
conn.close()
print("mock en:", srv.mock_llm([{"role": "user", "content": "Hello teacher"}], lang="en"))
print("mock zh[:40]:", srv.mock_llm([{"role": "user", "content": "你好"}], lang="zh")[:40])

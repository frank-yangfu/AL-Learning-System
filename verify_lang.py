import importlib.util
spec = importlib.util.spec_from_file_location("srv", "server.py")
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)
zh = srv.build_messages({"name": "小艾", "lang": "zh", "persona": "p",
                          "teaching_style": "s", "course": "c"}, 0, "neutral", [])
en = srv.build_messages({"name": "Emma", "lang": "en", "persona": "p",
                          "teaching_style": "s", "course": "c"}, 0, "neutral", [])
print("中文导师含[用中文与学生对话]:", "用中文与学生对话" in zh[0]["content"])
print("英文导师含[始终只用英语]:", "始终只用英语" in en[0]["content"])

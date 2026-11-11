# -*- coding: utf-8 -*-
"""
AL 自学系统 - cpolar 外网入口助手

功能:
  1. 从 cpolar 服务日志中解析当前已建立的隧道 (隧道名 / 公网地址 / 本地地址)
  2. 定位指向本地 8000 端口的那条隧道 (AL 自学系统)
  3. 生成二维码 PNG 与中文入口页 外网入口.html
  4. 把最终公网地址打印到 stdout, 供 bat 读取显示

用法:
  python al_cpolar_url.py            # 解析 + 生成入口页
  python al_cpolar_url.py --plain    # 只打印地址, 不生成文件
"""

import os
import re
import sys
import glob
import datetime
import socket

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Administrator"), ".cpolar", "logs")
QR_PNG = os.path.join(BASE, "qr_cpolar.png")
OUT_HTML = os.path.join(BASE, "外网入口.html")

LOCAL_PORT_KEY = "8000"          # AL 自学系统本地端口
PREFER_NAMES = ("alstudy", "自学", "自学系统")

# 日志中的 JSON 是转义过的: {\"Type\":\"NewTunnel\",...}
# 字段顺序: ID -> TunnelName -> ... -> Url -> Protocol -> LocalAddr -> Error -> StatusCode
RE_TUNNEL = re.compile(
    r'\\"Type\\":\\"NewTunnel\\".*?'
    r'\\"ID\\":\\"(?P<tid>[^\\]*)\\",\\"TunnelName\\":\\"(?P<name>[^\\]*)\\"'
    r'.*?\\"Url\\":\\"(?P<url>https?://[^\\]+)\\"'
    r'.*?\\"LocalAddr\\":\\"(?P<local>[^\\]+)\\",\\"Error\\":\\"(?P<err>[^\\]*)\\"'
)
RE_ESTABLISHED = re.compile(r'Tunnel established at (https?)://([^\s"\']+)')


def latest_log():
    """返回今天的 cpolar 服务日志; 若不存在则取最新的一份"""
    today = datetime.date.today().strftime("%Y%m%d")
    p = os.path.join(LOG_DIR, "cpolar_service.log." + today)
    if os.path.exists(p):
        return p
    cands = sorted(glob.glob(os.path.join(LOG_DIR, "cpolar_service.log.*")), key=os.path.getmtime)
    cands = [c for c in cands if not c.endswith(".master.log")]
    return cands[-1] if cands else None


def parse_tunnels(log_path):
    """返回 [(name, url, localaddr)]，仅成功建立(Error空)的记录，按日志时间后覆盖前"""
    if not log_path or not os.path.exists(log_path):
        return []
    txt = open(log_path, encoding="utf-8", errors="ignore").read()
    out = {}  # tid -> (name, url, local)
    for m in RE_TUNNEL.finditer(txt):
        if m.group("err") != "" or not m.group("tid") or not m.group("url"):
            continue  # 失败/超限的记录不收
        tid = m.group("tid")
        url = m.group("url")
        prev = out.get(tid)
        # 同一隧道 http/https 两条记录: 已有 https 则不被后面的 http 覆盖
        if prev and prev[1].startswith("https://") and url.startswith("http://"):
            continue
        out[tid] = (m.group("name"), url, m.group("local"))
    return list(out.values())


def probe(url, timeout=8):
    """直接探测公网地址是否真的在线(cpolar 服务端可能已回收旧域名并返回 404)"""
    try:
        import urllib.request
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 绕过系统代理
        req = urllib.request.Request(url + "/", headers={"User-Agent": "al-cpolar-check"})
        with opener.open(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def pick_al(tunnels):
    """指向本地 8000 的候选隧道，按日志时间倒序（最新在前），并实测可用性"""
    cand = [t for t in tunnels if (":" + LOCAL_PORT_KEY) in t[2]]
    if not cand:
        return None
    cand.reverse()
    best_dead = None
    for t in cand:
        url = t[1]
        if url.startswith("http://"):
            url = "https://" + url.split("://", 1)[1]
            t = (t[0], url, t[2])
        code = probe(url)
        if code == 200:
            return t
        if code == 404:   # cpolar 已回收该域名
            best_dead = best_dead or t
            continue
        if best_dead is None:
            best_dead = t
    return best_dead


def port_open(port=8000, host="127.0.0.1"):
    s = socket.socket()
    s.settimeout(1.5)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def make_qr(url, path):
    try:
        import qrcode
        img = qrcode.make(url)
        img.save(path)
        return True
    except Exception as e:
        sys.stderr.write("qrcode failed: %s\n" % e)
        return False


HTML_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AL 自学系统 · 外网入口</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
       background:linear-gradient(160deg,#eef2ff,#f8fafc);color:#1e293b;
       min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
  .card{background:#fff;border-radius:20px;box-shadow:0 20px 60px rgba(15,23,42,.12);
        padding:36px 40px;max-width:560px;width:100%;text-align:center}
  h1{font-size:22px;margin-bottom:6px;color:#0f172a}
  .sub{font-size:13px;color:#64748b;margin-bottom:22px}
  .qr{background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:18px;
      display:inline-block;margin-bottom:18px}
  .qr img{width:220px;height:220px;display:block}
  .urlbox{display:flex;gap:8px;align-items:stretch;margin-bottom:14px}
  input{flex:1;font-size:14px;padding:11px 14px;border:1px solid #cbd5e1;
        border-radius:10px;background:#f8fafc;color:#0f172a;font-family:ui-monospace,Menlo,Consolas,monospace}
  button{border:0;border-radius:10px;padding:11px 18px;font-size:14px;cursor:pointer;
         background:#4f46e5;color:#fff;font-weight:600;transition:.15s}
  button:hover{background:#4338ca}
  .btns{display:flex;gap:10px;justify-content:center;margin-bottom:20px}
  .btns a{text-decoration:none}
  .ghost{background:#fff;color:#4f46e5;border:1px solid #c7d2fe}
  .ghost:hover{background:#eef2ff}
  .meta{font-size:12.5px;color:#64748b;line-height:1.9;text-align:left;
        background:#f8fafc;border-radius:12px;padding:14px 18px;border:1px solid #e2e8f0}
  .meta b{color:#334155}
  .ok{color:#16a34a;font-weight:700}
  .bad{color:#dc2626;font-weight:700}
  .tip{margin-top:14px;font-size:12px;color:#94a3b8;line-height:1.7}
</style>
</head>
<body>
<div class="card">
  <h1>AL 自学系统 · 外网入口</h1>
  <div class="sub">扫码或点击链接，在平板 / 手机 / 微信上打开</div>

  <div class="qr"><img src="qr_cpolar.png" alt="访问二维码"></div>

  <div class="urlbox">
    <input id="u" value="__URL__" readonly>
    <button onclick="cp()">复制</button>
  </div>

  <div class="btns">
    <a href="__URL__" target="_blank"><button>在本机打开</button></a>
    <a href="__URL__" target="_blank"><button class="ghost">新窗口预览</button></a>
  </div>

  <div class="meta">
    <div>本地服务：<b class="__LOCALCLS__">__LOCALTXT__</b></div>
    <div>隧道名称：<b>__NAME__</b>　本地地址：<b>__LOCALADDR__</b></div>
    <div>通道类型：<b>cpolar 内网穿透</b>　更新时间：<b>__TIME__</b></div>
  </div>

  <div class="tip">
    提示：cpolar 免费版域名约每 24 小时会变化一次，地址变动后重新双击
    <b>外网访问-cpolar.bat</b> 即可刷新本页与二维码。<br>
    若微信内打不开，请改用系统浏览器；遇到“已停止访问该网页”多为域名被拦截，换用浏览器或重新获取地址即可。
  </div>
</div>
<script>
function cp(){
  var i=document.getElementById('u');
  i.select(); i.setSelectionRange(0,99999);
  navigator.clipboard.writeText(i.value).then(function(){
    var b=document.querySelector('.urlbox button'),o=b.innerText;
    b.innerText='已复制'; setTimeout(function(){b.innerText=o;},1500);
  });
}
</script>
</body>
</html>
"""


def write_html(url, name, localaddr):
    local_ok = port_open(8000)
    html = (HTML_TPL
            .replace("__URL__", url)
            .replace("__NAME__", name or "-")
            .replace("__LOCALADDR__", localaddr or "-")
            .replace("__LOCALCLS__", "ok" if local_ok else "bad")
            .replace("__LOCALTXT__", "已运行 (127.0.0.1:8000)" if local_ok else "未运行，请先启动服务")
            .replace("__TIME__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    open(OUT_HTML, "w", encoding="utf-8").write(html)
    return OUT_HTML


def main():
    plain = "--plain" in sys.argv
    log = latest_log()
    tunnels = parse_tunnels(log)
    al = pick_al(tunnels)

    if not al:
        print("NO_TUNNEL")
        if not plain:
            sys.stderr.write(
                "[!] 日志中未找到指向 8000 端口的隧道。\n"
                "    请在浏览器打开 http://localhost:9200 登录 cpolar，新建一条指向 8000 的隧道。\n"
                "    免费版可能有隧道数量上限，需先删掉不用的隧道。\n")
        return 2

    name, url, localaddr = al
    if not url.startswith("https://"):
        url_h = "https://" + url.split("://", 1)[1]
    else:
        url_h = url

    if plain:
        print(url_h)
        return 0

    make_qr(url_h, QR_PNG)
    html = write_html(url_h, name, localaddr)
    if "--open" in sys.argv:
        try:
            import webbrowser
            webbrowser.open("file:///" + html.replace("\\", "/"))
        except Exception:
            pass

    print("URL=" + url_h)
    print("NAME=" + name)
    print("LOCAL=" + localaddr)
    print("LOCAL_SERVICE=" + ("RUNNING" if port_open(8000) else "DOWN"))
    print("PROBE=" + str(probe(url_h)))
    print("HTML=" + html)
    print("QR=" + QR_PNG)
    print("ALL_TUNNELS=" + ("; ".join("%s->%s" % (t[0], t[2]) for t in tunnels)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

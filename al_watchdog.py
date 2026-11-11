# -*- coding: utf-8 -*-
"""
AL 自学系统 - 服务看门狗

常驻后台, 每 CHECK_INTERVAL 秒检查 127.0.0.1:8000:
  - 通   -> 什么都不做
  - 不通 -> 用隔离 venv 的 python 重新启动 server.py (保证 edge-tts 可用, 朗读不哑)

由 AL看门狗启动.vbs 以 pythonw.exe 无窗口方式拉起,
建议把该 vbs 的快捷方式放进 Windows 启动文件夹实现开机自启。

日志: al_watchdog.log (同目录)
"""

import os
import sys
import time
import socket
import subprocess
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(os.path.dirname(sys.executable), "python.exe")   # 同解释器(pythonw -> python)
SERVER = os.path.join(BASE, "server.py")
LOGFILE = os.path.join(BASE, "al_watchdog.log")
PORT = int(os.environ.get("AL_PORT", "8000"))
CHECK_INTERVAL = 12


def log(msg):
    line = "[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def port_open(port=PORT, host="127.0.0.1", timeout=1.5):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def start_server():
    try:
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        logf = open(os.path.join(BASE, "server_watchdog.log"), "ab")
        subprocess.Popen([PY, SERVER], cwd=BASE, creationflags=creationflags,
                         stdout=logf, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, close_fds=True)
        return True
    except Exception as e:
        log("启动失败: %s" % e)
        return False


def main():
    log("看门狗启动 (python=%s)" % PY)
    fails = 0
    while True:
        try:
            if port_open():
                fails = 0
            else:
                fails += 1
                log("端口 %d 未响应, 第 %d 次重启服务" % (PORT, fails))
                start_server()
                time.sleep(6)
                log("服务状态: %s" % ("已恢复" if port_open() else "仍未起来"))
        except Exception as e:
            log("异常: %s" % e)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""QA：为四套后台各取一个登录 token，写到 deploy/tmp/qa_tokens.json，
供无头浏览器注入 localStorage（key: bahar-admin-token）后直接进列表页。

登录要走图形验证码，明文落在 Redis 对应 db 的 uuid key 里，这里直接读出来回填。
用法: python deploy/tmp/qa_login_tokens.py
"""
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request

USER = "bahar"
PWD = "123456"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa_tokens.json")

PORTS = [
    ("retail", 8081, 0),
    ("car", 8082, 1),
    ("food", 8083, 2),
    ("health", 8084, 3),
]

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Redis:
    def __init__(self, host="127.0.0.1", port=6379):
        self.s = socket.create_connection((host, port), timeout=5)
        self.fp = self.s.makefile("rb")

    def _cmd(self, *args):
        out = b"*%d\r\n" % len(args)
        for a in args:
            b = a.encode() if isinstance(a, str) else a
            out += b"$%d\r\n%s\r\n" % (len(b), b)
        self.s.sendall(out)
        return self._read()

    def _read(self):
        line = self.fp.readline()
        if not line:
            raise RuntimeError("redis 连接断开")
        t, rest = line[:1], line[1:-2]
        if t == b"+":
            return rest.decode()
        if t == b"-":
            raise RuntimeError("redis 错误: " + rest.decode())
        if t == b":":
            return int(rest)
        if t == b"$":
            n = int(rest)
            if n == -1:
                return None
            return self.fp.read(n + 2)[:-2].decode("utf-8", "replace")
        if t == b"*":
            return [self._read() for _ in range(int(rest))]
        raise RuntimeError("未知回复类型 " + t.decode())

    def get(self, key, db=0):
        self._cmd("SELECT", str(db))
        return self._cmd("GET", key)

    def keys(self, pattern, db=0):
        self._cmd("SELECT", str(db))
        return self._cmd("KEYS", pattern)


def http(port, method, path, data=None, token=None, headers=None):
    url = "http://127.0.0.1:%d%s" % (port, path)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if token:
        req.add_header("Access-Token", token)
    try:
        with _OPENER.open(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode("utf-8", "replace")}
    except Exception as e:  # noqa: BLE001
        return {"_error": str(e)}


def login(port, db):
    cap = http(port, "GET", "/backendApi/captcha/getLoginCode")
    uuid = (cap.get("data") or {}).get("uuid")
    if not uuid:
        return None, "取验证码失败: " + json.dumps(cap, ensure_ascii=False)[:200]
    try:
        r = Redis()
        code = r.get(uuid, db)
        if code is None:
            for k in r.keys("*%s*" % uuid, db) or []:
                code = r.get(k, db)
                if code:
                    break
        code = (code or "").strip().strip('"')
    except Exception as e:  # noqa: BLE001
        return None, "读 Redis 失败: %s" % e
    login = http(port, "POST", "/backendApi/login/doLogin",
                 {"username": USER, "password": PWD, "captchaCode": code, "uuid": uuid})
    token = (login.get("data") or {}).get("token")
    if not token:
        return None, "登录失败: " + json.dumps(login, ensure_ascii=False)[:300]
    return token, None


def main():
    out = {}
    ok = True
    for name, port, db in PORTS:
        for attempt in range(1, 4):
            try:
                token, err = login(port, db)
            except Exception as e:  # noqa: BLE001
                token, err = None, str(e)
            if token:
                out[str(port)] = {"name": name, "port": port, "db": db, "token": token}
                print("[OK] %s %d token=%s..." % (name, port, token[:16]))
                break
            print("[retry %d] %s %d -> %s" % (attempt, name, port, err))
            time.sleep(2)
        else:
            ok = False
            print("[FAIL] %s %d 拿不到 token" % (name, port))
    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print("已写入 %s，共 %d 个端口" % (OUT, len(out)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

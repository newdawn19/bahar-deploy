# -*- coding: utf-8 -*-
import json, re, sys
import urllib.request, urllib.error
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
BASE = "http://127.0.0.1:%s" % (sys.argv[1] if len(sys.argv) > 1 else "8091")
LOG = "D:/logs/bahar-verify/server.log"
TOKEN = None

def req(url, payload=None, method=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    m = method or ("POST" if payload is not None else "GET")
    h = {"Content-Type": "application/json", "platform": "PC"}
    if TOKEN: h["Access-Token"] = TOKEN
    r = urllib.request.Request(url, data=data, headers=h, method=m)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

def read_log():
    return open(LOG, encoding="utf-8", errors="ignore").read()

def login():
    global TOKEN
    st, b = req(BASE + "/clientApi/captcha/getCode")
    uuid = (b.get("data") or {}).get("uuid")
    cap = None
    for _ in range(20):          # 日志是异步落盘的，多读几次
        for mm in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", read_log()):
            if mm.group(2).strip() == uuid.strip():
                cap = mm.group(1).strip()
        if cap: break
        import time; time.sleep(0.5)
    if not cap:
        print("[FAIL] 取不到验证码 uuid=%s" % uuid); return False
    st, b = req(BASE + "/backendApi/login/doLogin",
                {"username": "bahar", "password": "123456", "captchaCode": cap, "uuid": uuid})
    TOKEN = (b.get("data") or {}).get("token")
    print("[OK ] 登录 token=%s..." % (TOKEN or "")[:16])
    return bool(TOKEN)

if not login(): sys.exit(1)

for label, payload in [
        ("按 id 查详情  id=900311", {"id": 900311, "code": ""}),
        ("按 code 查详情 code=C3001", {"id": 0, "code": "C3001"}),
        ("已核销过的券 id=900312(status=B)", {"id": 900312, "code": ""}),
        ("不存在的券 id=999999", {"id": 999999, "code": ""})]:
    st, b = req(BASE + "/backendApi/doConfirm/info", payload)
    print("\n--- %s ---" % label)
    print("HTTP %s" % st)
    print(json.dumps(b, ensure_ascii=False)[:600])

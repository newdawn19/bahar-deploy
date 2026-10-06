# -*- coding: utf-8 -*-
"""最终验收（跑在 8091 验证实例上）：
   bug1 余额充值：本金 + 赠送 都要入账，且商户号取会员所属商户（不能是 0）
   bug2 卡券核销详情：不再 404
"""
import json, re, sys, time
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
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

def login():
    global TOKEN
    st, b = req(BASE + "/clientApi/captcha/getCode")
    uuid = (b.get("data") or {}).get("uuid")
    cap = None
    for _ in range(30):
        txt = open(LOG, encoding="utf-8", errors="ignore").read()
        for mm in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", txt):
            if mm.group(2).strip() == uuid.strip():
                cap = mm.group(1).strip()
        if cap: break
        time.sleep(0.5)
    if not cap:
        print("[FAIL] 取不到验证码"); return False
    st, b = req(BASE + "/backendApi/login/doLogin",
                {"username": "bahar", "password": "123456", "captchaCode": cap, "uuid": uuid})
    TOKEN = (b.get("data") or {}).get("token")
    if not TOKEN:
        print("[FAIL] 登录: %s" % str(b)[:200]); return False
    st, b = req(BASE + "/backendApi/login/getInfo", None, "GET")
    info = (b.get("data") or {}).get("accountInfo") or {}
    print("[OK ] 登录 %s  merchantId=%s" % (info.get("accountName"), info.get("merchantId")))
    return True

if not login(): sys.exit(1)

print("\n--- bug1 余额充值 userId=105 本金1000 赠送50 ---")
st, b = req(BASE + "/backendApi/balance/doRecharge",
            {"userId": 105, "amount": 1000, "type": 1, "giftAmount": 50,
             "remark": "支付方式：现金支付"})
print("HTTP %s  %s" % (st, json.dumps(b, ensure_ascii=False)[:200]))

print("\n--- bug2 卡券核销详情 id=900311 ---")
st, b = req(BASE + "/backendApi/doConfirm/info", {"id": 900311, "code": ""})
d = (b.get("data") or {}) if isinstance(b, dict) else {}
ci = d.get("couponInfo") or {}
print("HTTP %s code=%s" % (st, b.get("code") if isinstance(b, dict) else "?"))
print("couponInfo = %s" % json.dumps(ci, ensure_ascii=False)[:400])
print("userInfo   姓名=%s 余额=%s" % ((d.get("userInfo") or {}).get("name"),
                                     (d.get("userInfo") or {}).get("balance")))
print("typeList   条数=%d" % len(d.get("typeList") or []))

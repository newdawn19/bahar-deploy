#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""探查收银端真实链路：登录 -> getInfo -> cashier/init/{userId} -> searchGoods"""
import json, os, re, sys, urllib.request

BASE = os.environ.get("SMOKE_BASE", "http://127.0.0.1:8081")
LOG = os.environ.get("SMOKE_LOG", r"D:\git-double\bahar\deploy\logs\bahar-shop.jar.log")
TOKEN = None


def req(url, payload=None, method=None):
    data = None
    h = {"platform": "PC", "Content-Type": "application/json"}
    if TOKEN:
        h["Access-Token"] = TOKEN
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    m = method or ("POST" if payload is not None else "GET")
    r = urllib.request.Request(url, data=data, headers=h, method=m)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)


def read_log():
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            with open(LOG, encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


st, b = req(BASE + "/clientApi/captcha/getCode")
uuid = (b.get("data") or {}).get("uuid")
captcha = None
for mm in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", read_log()):
    if mm.group(2).strip() == (uuid or "").strip():
        captcha = mm.group(1).strip()
print("uuid=%s captcha=%s" % (uuid, captcha))

st, b = req(BASE + "/backendApi/login/doLogin",
            {"username": "bahar", "password": "123456",
             "captchaCode": captcha, "uuid": uuid})
TOKEN = (b.get("data") or {}).get("token")
print("login code=%s token=%s" % (b.get("code"), (TOKEN or "")[:20]))

st, b = req(BASE + "/backendApi/login/getInfo", None, "GET")
info = b.get("data") or {}
print("getInfo code=%s" % b.get("code"))
print("getInfo keys=%s" % list(info.keys()))
print("getInfo data=%s" % json.dumps(info, ensure_ascii=False)[:600])

uid = info.get("userId") or info.get("id") or (info.get("user") or {}).get("id")
print("=> userId =", uid)

if uid:
    st, b = req(BASE + "/backendApi/cashier/init/%s?cateId=&page=1&pageSize=10" % uid, None, "GET")
    print("[cashier/init] status=%s code=%s" % (st, b.get("code") if isinstance(b, dict) else b))
    d = (b.get("data") or {}) if isinstance(b, dict) else {}
    print("  data keys=%s" % list(d.keys())[:12])
    print("  data=%s" % json.dumps(d, ensure_ascii=False)[:400])

st, b = req(BASE + "/backendApi/cashier/searchGoods", {"keyword": "", "page": 1, "pageSize": 10})
print("[cashier/searchGoods] status=%s code=%s" % (st, b.get("code") if isinstance(b, dict) else b))

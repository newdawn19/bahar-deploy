#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
收银端（baharCashier / Electron）登录 + 收银台链路冒烟。

与后台 Admin 的区别：
  - 验证码走 clientApi/captcha/getCode（不是 backendApi 的 getLoginCode）
  - 所有请求带 platform: PC，令牌头为 Access-Token
  - 核心业务是 backendApi/cashier/*（init / searchGoods / getMemberInfo / 挂单）

注意：零售 bahar(8081) 不带 BackendCashierController，收银台接口会 404；
      汽车 8082 / 餐饮 8083 / 康养 8084 三套才有收银台模块。

用法：
  SMOKE_BASE=http://127.0.0.1:8082 SMOKE_LOG=<java日志> python smoke-cashier.py
"""
import json
import os
import re
import sys
import urllib.request

BASE = os.environ.get("SMOKE_BASE", "http://127.0.0.1:8082")
LOG = os.environ.get("SMOKE_LOG", r"D:\git-double\bahar\deploy\logs\bahar-car.jar.log")
USER = os.environ.get("SMOKE_USER", "bahar")
PWD = os.environ.get("SMOKE_PWD", "123456")

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


def main():
    global TOKEN
    print("=" * 64)
    print("收银端冒烟：", BASE)
    print("=" * 64)
    ok = True

    st, b = req(BASE + "/clientApi/captcha/getCode")
    uuid = (b.get("data") or {}).get("uuid") if isinstance(b, dict) else None
    if not uuid:
        print("[FAIL] 验证码接口: %s" % str(b)[:200])
        return 1
    print("[OK]   验证码 uuid =", uuid)

    captcha = None
    for mm in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", read_log()):
        if mm.group(2).strip() == uuid.strip():
            captcha = mm.group(1).strip()
    if not captcha:
        print("[FAIL] 日志中找不到该 uuid 的验证码")
        return 1
    print("[OK]   验证码明文 =", captcha)

    st, b = req(BASE + "/backendApi/login/doLogin",
                {"username": USER, "password": PWD,
                 "captchaCode": captcha, "uuid": uuid})
    TOKEN = (b.get("data") or {}).get("token") if isinstance(b, dict) else None
    if not TOKEN:
        print("[FAIL] 登录: %s" % str(b)[:200])
        return 1
    print("[OK]   登录 token =", TOKEN[:20] + "...")

    st, b = req(BASE + "/backendApi/login/getInfo", None, "GET")
    info = (b.get("data") or {}).get("accountInfo") or {}
    uid = info.get("id")
    print("[OK]   getInfo 账号=%s 商户=%s 门店=%s" %
          (info.get("accountName"), info.get("merchantName"), info.get("storeName")))

    if uid is None:
        print("[FAIL] getInfo 取不到账号 id")
        return 1

    # 收银台核心链路
    cases = [
        ("收银台初始化", "GET",
         BASE + "/backendApi/cashier/init/%s?page=1&pageSize=10" % uid, None),
        ("搜索商品", "POST", BASE + "/backendApi/cashier/searchGoods",
         {"keyword": "", "page": 1, "pageSize": 10}),
        ("挂单列表", "GET", BASE + "/backendApi/cashier/getHangUpList", None),
    ]
    for name, m, url, payload in cases:
        st, b = req(url, payload, m)
        c = b.get("code") if isinstance(b, dict) else None
        good = (c == 200)
        ok = ok and good
        extra = ""
        if good and isinstance(b, dict) and isinstance(b.get("data"), dict):
            extra = "  keys=%s" % list(b["data"].keys())[:8]
        print("[%s] %-12s code=%s%s" % ("OK  " if good else "FAIL", name, c, extra))

    print("=" * 64)
    print("结果:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

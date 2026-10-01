#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""演示数据落库后的应用层冒烟：登录后台，拉会员 / 商品 / 订单三个列表，看条数。

目的：数据在库里不等于后台能看到。列表接口通常带 is_staff='N' 之类等值过滤、
以及按 merchant/store 隔离，写错字段会导致"数据都在但列表是空的"，必须实测。

用法（需先启动四套实例）：
    python deploy/smoke-data.py
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(BASE_DIR, "logs")

INSTANCES = [
    ("零售", 8081, "bahar-shop.jar", "post"),
    ("汽车", 8082, "bahar-car.jar", "post"),
    ("餐饮", 8083, "bahar-food.jar", "get"),
    ("康养", 8084, "bahar-health.jar", "post"),
]

USER, PWD = "bahar", "123456"


def req(url, payload=None, method=None, token=None):
    data = None
    h = {"platform": "PC", "Content-Type": "application/json"}
    if token:
        h["Access-Token"] = token
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    m = method or ("POST" if payload is not None else "GET")
    r = urllib.request.Request(url, data=data, headers=h, method=m)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"code": e.code, "_raw": e.read().decode("utf-8", "ignore")[:200]}
    except Exception as e:
        return {"code": 0, "_raw": str(e)}


def read_log(path):
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError, IOError):
            continue
    return ""


def count_of(body):
    """列表响应把分页包在 data.paginationResponse 里（totalElements / content），
    同时带上 typeList、payTypeList 等字典，直接找 data.total 会永远找不到。"""
    d = body.get("data")
    if isinstance(d, dict):
        pr = d.get("paginationResponse")
        if isinstance(pr, dict):
            if isinstance(pr.get("totalElements"), int):
                return pr["totalElements"]
            if isinstance(pr.get("content"), list):
                return len(pr["content"])
        for k in ("total", "totalCount", "count"):
            if isinstance(d.get(k), int):
                return d[k]
        for k in ("list", "records", "rows"):
            if isinstance(d.get(k), list):
                return len(d[k])
    if isinstance(d, list):
        return len(d)
    return 0


def run(name, port, jar, goods_method):
    base = "http://127.0.0.1:%d" % port
    log = os.path.join(LOGS, jar + ".log")
    print("=" * 62)
    print("%s  %s" % (name, base))
    print("=" * 62)

    b = req(base + "/clientApi/captcha/getCode")
    uuid = (b.get("data") or {}).get("uuid")
    if not uuid:
        print("  [FAIL] 验证码接口: %s" % str(b)[:160])
        return False
    captcha = None
    for mm in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", read_log(log)):
        if mm.group(2).strip() == uuid.strip():
            captcha = mm.group(1).strip()
    if not captcha:
        print("  [FAIL] 日志中找不到验证码")
        return False

    b = req(base + "/backendApi/login/doLogin",
            {"username": USER, "password": PWD, "captchaCode": captcha, "uuid": uuid})
    token = (b.get("data") or {}).get("token")
    if not token:
        print("  [FAIL] 登录: %s" % str(b)[:160])
        return False
    print("  [OK] 登录成功")

    ok = True
    cases = [
        ("会员列表", "get", base + "/backendApi/member/list?page=1&pageSize=10", None),
        ("商品列表", goods_method,
         base + "/backendApi/goods/goods/list", {"page": 1, "pageSize": 10}),
        ("订单列表", "post", base + "/backendApi/order/list", {"page": 1, "pageSize": 10}),
    ]
    for label, m, url, payload in cases:
        if m == "get":
            body = req(url, None, "GET", token)
        else:
            body = req(url, payload or {"page": 1, "pageSize": 10}, "POST", token)
        code = body.get("code")
        n = count_of(body)
        good = (code == 200 and n > 0)
        ok = ok and good
        print("  [%s] %-8s code=%s  条数=%s" % ("OK  " if good else "FAIL", label, code, n))
    return ok


if __name__ == "__main__":
    all_ok = True
    for name, port, jar, gm in INSTANCES:
        all_ok = run(name, port, jar, gm) and all_ok
    print("=" * 62)
    print("总体结果:", "PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)

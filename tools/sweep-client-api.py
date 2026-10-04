# -*- coding: utf-8 -*-
"""会员端（uniapp）接口体检：四套后端各用真实会员账号登录，逐个打 clientApi。

为什么单独写：后台有 smoke-menus.py + sweep-admin.js，会员端一直没验过。
会员端调的是 clientApi/* 而不是 backendApi/*，登录走 sign/signIn（账号+密码+图形验证码），
请求还要带 merchantNo 头——和后台完全不是一套，不能复用后台脚本。

判定标准：接口 200 且 data 非空才算过。"表为空"在演示现场等于"功能没做完"。

用法: python deploy/tools/sweep-client-api.py [port...]
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 登录账号用手机号：后端 queryMemberByName() 只在查到**恰好 1 条**时返回会员，
# 演示数据里曾经有 5 组重名（已由 db/16-fix-dup-member-names.py 修掉），
# 用姓名登录一旦撞重名就报"账号或密码有误"。手机号才是稳定唯一键。
ACCOUNT = "13800000001"
# 顺带验一下"姓名登录"这条链路还活着（重名修复的回归用例）
ACCOUNT_BY_NAME = "张伟"
PASSWORD = "123456"
MERCHANT_NO = "10001"

# 端口 -> (实例名, logback 日志路径候选)
_DRIVE = (os.path.splitdrive(BASE_DIR)[0] or "C:") + os.sep


def _log(app):
    return os.path.join(_DRIVE, "logs", app, "server.log")


LOG_MAP = {
    8081: [_log("bahar-shop"), _log("bahar")],
    8082: [_log("bahar-car")],
    8083: [_log("bahar-food")],
    8084: [_log("bahar-health")],
}

# 通用能力 + 按端口追加的行业能力
BASE_APIS = [
    ("首页", "clientApi/page/home", {}),
    ("商品分类", "clientApi/goodsApi/cateList", {}),
    ("商品列表", "clientApi/goodsApi/list", {}),
    ("文章公告", "clientApi/article/list", {"page": 1, "pageSize": 10}),
    ("购物车", "clientApi/cart/list", {"page": 1, "pageSize": 10}),
    ("我的订单", "clientApi/order/list", {"page": 1, "pageSize": 10}),
    ("待处理数", "clientApi/order/todoCounts", {}),
    ("我的卡券", "clientApi/myCoupon/list", {}),
    ("领券中心", "clientApi/coupon/list", {"page": 1, "pageSize": 10}),
    ("收货地址", "clientApi/address/list", {}),
    ("积分明细", "clientApi/points/list", {"page": 1, "pageSize": 10}),
    ("余额明细", "clientApi/balance/list", {"page": 1, "pageSize": 10}),
    ("会员资料", "clientApi/user/info", {}),
    ("会员资产", "clientApi/user/asset", {}),
]
EXTRA_APIS = {
    8082: [("预约项目", "clientApi/book/list", {"page": 1, "pageSize": 10}),
           ("分销概览", "clientApi/commission/overview", {})],
    8083: [("预约项目", "clientApi/book/list", {"page": 1, "pageSize": 10}),
           ("分销概览", "clientApi/commission/overview", {})],
    8084: [("预约项目", "clientApi/book/list", {"page": 1, "pageSize": 10}),
           ("分销概览", "clientApi/commission/overview", {})],
}


def req(url, data=None, headers=None, method=None):
    """GET 优先，405 自动回退 POST（后端 GlobalExceptionHandler 会把 405 变成 200+code=201）。

    请求头必须照抄会员端 utils/request/index.js 的那几个，否则拿到的是空数据：
      merchantNo / storeId / platform / Access-Token
    尤其 storeId —— getStoreGoodsList() 先查门店，storeId=0 查不到门店直接返回空列表，
    商品分类和商品列表就会"看起来没数据"，其实是没传店。
    """
    h = {"User-Agent": "bahar-client-smoke",
         "merchantNo": MERCHANT_NO,
         "storeId": "1",
         "platform": "H5"}
    h.update(headers or {})
    for m in ([method] if method else ["get", "post"]):
        body = None
        u = url
        if data:
            if m == "get":
                u = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(data, encoding="utf-8")
            else:
                # @RequestBody 的接口不带 body 会报 "Required request body is missing"，
                # 所以 POST 一律发 {}，不能因为 data 是空 dict 就省掉
                body = json.dumps(data if data else {}).encode("utf-8")
                h2 = dict(h)
                h2["Content-Type"] = "application/json"
                h = h2
        r = urllib.request.Request(u, data=body, method=m.upper())
        for k, v in h.items():
            r.add_header(k, v)
        try:
            with urllib.request.urlopen(r, timeout=20) as resp:
                j = json.loads(resp.read().decode("utf-8", "replace"))
        except Exception as e:
            last = e
            continue
        # 405 被 GlobalExceptionHandler 吃成 200 + code=201，所以必须看 message 再回退
        if j.get("code") == 201 and "not supported" in str(j.get("message", "")):
            last = j.get("message")
            continue
        return j
    return {"code": -1, "msg": str(last)}


def read_log(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def login(port):
    base = "http://127.0.0.1:%d" % port
    b = req(base + "/clientApi/captcha/getCode")
    uuid = ""
    d = b.get("data") or {}
    if isinstance(d, dict):
        uuid = d.get("uuid") or ""
    if not uuid and isinstance(d, str):
        uuid = d
    if not uuid:
        return None, "取不到 uuid: %s" % json.dumps(b, ensure_ascii=False)[:120]
    captcha = None
    for path in LOG_MAP.get(port, []):
        for m in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", read_log(path)):
            if m.group(2).strip() == uuid:
                captcha = m.group(1).strip()
        if captcha:
            break
    if not captcha:
        return None, "日志中找不到验证码（试过：%s）" % "、".join(LOG_MAP.get(port, []))
    r = req(base + "/clientApi/sign/signIn",
            {"account": ACCOUNT, "password": PASSWORD,
             "captchaCode": captcha, "uuid": uuid}, method="post")
    tok = ""
    data = r.get("data")
    if isinstance(data, dict):
        tok = data.get("token") or ""
    elif isinstance(data, str) and data:
        try:
            tok = json.loads(data).get("token", "")
        except Exception:
            tok = ""
    if not tok:
        return None, "登录失败: %s" % json.dumps(r, ensure_ascii=False)[:160]
    return tok, None


def count(data):
    if data is None:
        return 0
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for k in ("content", "dataList", "list", "records"):
            v = data.get(k)
            if isinstance(v, list):
                return len(v)
        # 首页那种聚合结构：有任意非空业务键就算有数据
        return 1 if any(v for k, v in data.items()
                        if k.lower() not in ("total", "page", "pagesize", "pagenum")) else 0
    return 1


def run(port):
    print("=" * 60)
    print("会员端 %d（merchantNo=%s，账号 %s）" % (port, MERCHANT_NO, ACCOUNT))
    print("=" * 60)
    tok, err = login(port)
    if err:
        print("  [FAIL] %s" % err)
        return False, ["登录"]
    print("  登录成功，token=%s..." % tok[:12])
    bad = []
    # 回归：姓名登录曾因会员重名必失败（queryMemberByName 要求恰好 1 条），盯着别再坏
    globals()["ACCOUNT"] = ACCOUNT_BY_NAME
    _, err2 = login(port)
    globals()["ACCOUNT"] = "13800000001"
    if err2:
        print("  [FAIL] 姓名登录: %s" % err2)
        bad.append("姓名登录")
    else:
        print("  姓名登录 OK")
    for title, path, p in BASE_APIS + EXTRA_APIS.get(port, []):
        r = req("http://127.0.0.1:%d/%s" % (port, path), p,
                headers={"Access-Token": tok})
        n = count(r.get("data"))
        ok = (r.get("code") == 200) and n > 0
        flag = "    " if ok else "<<< "
        print("  [%s] %-10s %-32s code=%s 条数=%s %s" %
              ("OK" if ok else "--", title, path, r.get("code"), n, flag))
        if not ok:
            bad.append(title)
    return len(bad) == 0, bad


def main():
    ports = [int(x) for x in sys.argv[1:]] or [8081, 8082, 8083, 8084]
    allbad = []
    for p in ports:
        ok, bad = run(p)
        if bad:
            allbad.append((p, bad))
    print("=" * 60)
    if allbad:
        print("问题 %d 组 -> %s" % (len(allbad),
              " / ".join("%d %s" % (p, ",".join(b)) for p, b in allbad)))
    else:
        print("总体: 会员端接口全部有数据")


if __name__ == "__main__":
    main()

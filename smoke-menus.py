#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把后台左侧每个菜单的列表接口都跑一遍，看哪些是空的。

目的：数据库里有数据 ≠ 后台能看到。菜单背后的接口可能指向别的表、
或者被 merchant/store 过滤掉。写数据脚本时只顾了几张主表，
其余菜单空着，演示时一眼就假。

用法（需先启动实例）：
    python deploy/smoke-menus.py            # 四套都测
    python deploy/smoke-menus.py 8081       # 只测指定端口

验证码从实例日志里抓（/">/logs/<APP_NAME>/server.log"），见 LOG_MAP；
没起监听的端口会 [SKIP] 跳过，不算失败。
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(BASE_DIR, "logs")

# 别再读 deploy/logs 了：日志配置统一改成 LOG_HOME 占位符之后，四套实例
# 实际写在 /logs/<APP_NAME>/server.log。还按老路径找，四套会全部报
# 「日志中找不到验证码」——那是**路径错**，不是服务挂也不是没数据。
# 8081 给两个候选：start-all.sh 起的名字是 bahar-shop，手敲
# APP_NAME=bahar 直接 java -jar 时是 bahar。
_DRIVE = (os.path.splitdrive(BASE_DIR)[0] or "C:") + os.sep


def _log(app):
    return os.path.join(_DRIVE, "logs", app, "server.log")


LOG_MAP = {
    8081: [_log("bahar-shop"), _log("bahar")],
    8082: [_log("bahar-car")],
    8083: [_log("bahar-food")],
    8084: [_log("bahar-health")],
    8085: [_log("bahar-shop-8085")],
}

INSTANCES = [
    ("零售", 8081, "bahar-shop.jar"),
    ("汽车", 8082, "bahar-car.jar"),
    ("餐饮", 8083, "bahar-food.jar"),
    ("康养", 8084, "bahar-health.jar"),
    # 8081 被 IDEA 里的实例占着时，把零售 jar 起在 8085 验证同一个库
    ("零售8085", 8085, "bahar-shop-8085.jar"),
]

# (菜单名, 接口) —— 取自 deploy/admin/js/modules.js
MENUS = [
    ("会员管理", "member/list"),
    ("会员等级", "userGrade/list"),
    ("会员分组", "memberGroup/list"),
    ("会员标签", "userTag/list"),
    ("商品管理", "goods/goods/list"),
    ("商品分类", "goods/cate/list"),
    ("库存管理", "stock/list"),
    ("卡券管理", "coupon/list"),
    ("会员领券", "userCoupon/list"),
    ("订单中心", "order/list"),
    ("门店管理", "store/list"),
    ("员工管理", "staff/list"),
    ("打印机", "printer/list"),
    ("商户信息", "merchant/list"),
    ("文章公告", "article/list"),
    ("轮播图", "banner/list"),
    ("账号管理", "account/list"),
    ("职务角色", "duty/list"),
    ("操作日志", "actlog/list"),
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
        return {"code": e.code, "_raw": e.read().decode("utf-8", "ignore")[:120]}
    except Exception as e:
        return {"code": 0, "_raw": str(e)}


def read_log(path):
    """日志里定时任务（CouponExpireJob/MessageJob）每 5 分钟刷一屏，
    偶尔夹带非 UTF-8 字节。原来按 utf-8 -> gbk -> latin-1 整体回退，
    一旦回退到 latin-1，中文「生成验证码」就成了乱码，正则永远匹配不到。
    改成始终 utf-8 + errors=ignore，坏字节丢掉即可，中文照常匹配。"""
    for enc in ("utf-8", "gbk"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def port_open(port, timeout=3):
    import socket
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def count_of(body):
    """各接口包分页的 key 并不统一：有的叫 paginationResponse（商品/会员），
    有的叫 dataList（文章/轮播），还有的直接是 list。
    所以遍历 data 下所有值，找到含 totalElements / content 的那个。"""
    d = body.get("data")
    if isinstance(d, list):
        return len(d)
    if not isinstance(d, dict):
        return 0
    # 有的接口 data 本身就是分页对象（actlog / account / duty）
    if isinstance(d.get("totalElements"), int):
        return d["totalElements"]
    if isinstance(d.get("content"), list):
        return len(d["content"])
    pr = d.get("paginationResponse") or d.get("dataList")
    if isinstance(pr, dict):
        if isinstance(pr.get("totalElements"), int):
            return pr["totalElements"]
        if isinstance(pr.get("content"), list):
            return len(pr["content"])
    for v in d.values():
        if isinstance(v, dict):
            if isinstance(v.get("totalElements"), int):
                return v["totalElements"]
            if isinstance(v.get("content"), list):
                return len(v["content"])
    for k in ("list", "records", "rows"):
        if isinstance(d.get(k), list):
            return len(d[k])
    return 0


def call(base, path, token):
    """四套工程同名接口的 GET/POST 不一致，两个都试一遍"""
    url = base + "/backendApi/" + path
    for m, payload in (("GET", None), ("POST", {"page": 1, "pageSize": 10})):
        body = req(url, payload, m, token)
        raw = str(body.get("_raw", ""))
        code = body.get("code")
        if code == 200:
            return code, count_of(body), m
        if code in (201, 405) or "not supported" in raw:
            continue
        if code:
            return code, 0, m
    return None, 0, "-"


def run(label, port, jar):
    base = "http://127.0.0.1:%d" % port
    # 候选日志：新路径优先，老路径兜底；一个都不存在就报得明白一点
    logs = LOG_MAP.get(port, []) + [os.path.join(LOGS, jar + ".log")]
    print("=" * 58)
    print("%s  %s" % (label, base))
    print("=" * 58)

    b = req(base + "/clientApi/captcha/getCode")
    uuid = (b.get("data") or {}).get("uuid")
    if not uuid:
        # 实例没起和验证码坏了，报的错一模一样，很容易误判成"出问题了"。
        # INSTANCES 里有 8085 这种备选项，平时就不在跑 —— 没监听就直接跳过。
        if not port_open(port):
            print("  [SKIP] 该实例没起（%d 无响应），跳过" % port)
            return True
        print("  [FAIL] 验证码接口取不到 uuid")
        return False
    captcha = None
    for path in logs:
        if not os.path.exists(path):
            continue
        for mm in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", read_log(path)):
            if mm.group(2).strip() == uuid.strip():
                captcha = mm.group(1).strip()
        if captcha:
            break
    if not captcha:
        print("  [FAIL] 日志中找不到验证码（试过：%s）" % "，".join(logs))
        return False

    b = req(base + "/backendApi/login/doLogin",
            {"username": USER, "password": PWD, "captchaCode": captcha, "uuid": uuid})
    token = (b.get("data") or {}).get("token")
    if not token:
        print("  [FAIL] 登录失败")
        return False

    empty = []
    for name, path in MENUS:
        code, n, method = call(base, path, token)
        flag = "OK  " if (code == 200 and n > 0) else "空!!"
        if not (code == 200 and n > 0):
            empty.append(name)
        print("  [%s] %-10s %-22s code=%-5s 条数=%-4s %s"
              % (flag, name, path, code, n, method))
    if empty:
        print("  --> 没数据的菜单: %s" % "、".join(empty))
    return not empty


if __name__ == "__main__":
    args = sys.argv[1:]
    targets = INSTANCES if not args else [i for i in INSTANCES if str(i[1]) in args]
    all_ok = True
    for label, port, jar in targets:
        all_ok = run(label, port, jar) and all_ok
    print("=" * 58)
    print("总体:", "全部菜单都有数据" if all_ok else "存在空菜单，见上方清单")
    sys.exit(0 if all_ok else 1)

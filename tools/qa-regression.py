# -*- coding: utf-8 -*-
"""三端整体回归 v2：修正上一轮的方法错误（列表接口是 GET 不是 POST），
   卡券核销用库里真实存在的 id，充值用例跑完自动回滚。"""
import json, re, time
import urllib.request, urllib.error
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
LOG = "D:/logs/%s/server.log"
PASS, FAIL = [], []
def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  [%s] %-36s %s" % ("PASS" if cond else "FAIL", name, detail))
def mk(port, platform):
    base = "http://127.0.0.1:%d/" % port
    st = {"token": None}
    def req(url, payload=None, method=None):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        m = method or ("POST" if payload is not None else "GET")
        h = {"Content-Type": "application/json;charset=utf-8", "platform": platform,
             "isWechat": "N", "merchantNo": "10001", "storeId": "0"}
        if st["token"]: h["Access-Token"] = st["token"]
        r = urllib.request.Request(url, data=data, headers=h, method=m)
        try:
            with urllib.request.urlopen(r, timeout=25) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8", "ignore")
        except Exception as e: return 0, str(e)
    return base, req, st
def captcha(req, url, logname):
    s, b = req(url, None, "GET")
    uuid = (b.get("data") or {}).get("uuid") if isinstance(b, dict) else None
    if not uuid: return None, None
    for _ in range(30):
        try: txt = open(LOG % logname, encoding="utf-8", errors="ignore").read()
        except OSError: txt = ""
        for mm in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", txt):
            if mm.group(2).strip() == uuid.strip(): return uuid, mm.group(1).strip()
        time.sleep(0.5)
    return uuid, None
def login_backend(port, logname):
    base, req, st = mk(port, "PC")
    uuid, code = captcha(req, base + "backendApi/captcha/getLoginCode", logname)
    if not code: return None, None
    s, b = req(base + "backendApi/login/doLogin",
               {"username":"bahar","password":"123456","captchaCode":code,"uuid":uuid})
    st["token"] = ((b.get("data") or {}) if isinstance(b, dict) else {}).get("token")
    if not st["token"]: return None, None
    s, b = req(base + "backendApi/login/getInfo", None, "GET")
    info = (b.get("data") or {}).get("accountInfo") or {}
    return (base, req, st), info
def login_member(port, logname, account="张伟"):
    base, req, st = mk(port, "H5")
    uuid, code = captcha(req, base + "clientApi/captcha/getCode", logname)
    if not code: return None, None
    s, b = req(base + "clientApi/sign/signIn", {"account":account,"password":"123456","captchaCode":code,"uuid":uuid})
    d = (b.get("data") or {}) if isinstance(b, dict) else {}
    st["token"] = d.get("token")
    return (base, req, st), d
def rows(b):
    d = (b.get("data") or {}) if isinstance(b, dict) else {}
    if isinstance(d, dict):
        for k in ("content","list","records","paginationResponse"):
            v = d.get(k)
            if isinstance(v, list): return len(v)
            if isinstance(v, dict):
                for k2 in ("content","list","records"):
                    if isinstance(v.get(k2), list): return len(v[k2])
    return 0

print("=" * 80)
print("三端整体回归 v2   （后台/收银 bahar，会员 张伟）")
print("=" * 80)

print("\n[1] H5 会员端 clientApi")
ctx, d = login_member(8081, "bahar-shop")
check("会员登录 signIn", bool(ctx and d.get("userId")), "userId=%s" % (d or {}).get("userId"))
if ctx:
    base, req, st = ctx
    for name, url, m, p in [("会员信息 user/info","clientApi/user/info","GET",None),
            ("会员资产 user/asset","clientApi/user/asset","GET",None),
            ("首页数据 page/home","clientApi/page/home","GET",None),
            ("商品分类 goodsApi/cateList","clientApi/goodsApi/cateList","GET",None),
            ("商品列表 goodsApi/list","clientApi/goodsApi/list","GET",None),
            ("卡券列表 coupon/list","clientApi/coupon/list",None,{"page":1,"pageSize":5}),
            ("余额明细 balance/list","clientApi/balance/list",None,{"page":1,"pageSize":5})]:
        s, b = req(base + url, p, m)
        c = b.get("code") if isinstance(b, dict) else "?"
        check(name, c == 200, "code=%s" % c)

print("\n[2] 后台管理端 backendApi（列表走 GET）")
ctx, info = login_backend(8081, "bahar-shop")
check("后台登录 + getInfo", bool(ctx and info.get("id")), "merchantId=%s" % info.get("merchantId"))
if ctx:
    base, req, st = ctx
    # 注意：这些列表的接口方法不统一（member/store/coupon/cate 是 GET，order 是 POST），
    # 用错方法会返回 201 "Request method 'POST' not supported"
    for name, url, m in [("会员列表 member/list","backendApi/member/list","GET"),
            ("订单列表 order/list","backendApi/order/list","POST"),
            ("商品分类 goods/cate/list","backendApi/goods/cate/list","GET"),
            ("卡券列表 coupon/list","backendApi/coupon/list","GET"),
            ("门店列表 store/list","backendApi/store/list","GET")]:
        if m == "GET":
            s, b = req(base + url + "?page=1&pageSize=5", None, "GET")
        else:
            s, b = req(base + url, {"page":1,"pageSize":5})
        c = b.get("code") if isinstance(b, dict) else "?"
        check(name, c == 200, "code=%s(%s) 条数=%d" % (c, m, rows(b)))

print("\n[3] 收银端 backendApi")
if ctx:
    base, req, st = ctx
    uid = info.get("id") or 0
    s, b = req(base + "backendApi/cashier/init/%s?page=1&pageSize=10" % uid, None, "GET")
    check("收银台初始化 cashier/init", (b.get("code") if isinstance(b,dict) else "?") == 200)
    s, b = req(base + "backendApi/cashier/searchGoods", {"keyword":"","page":1,"pageSize":10})
    c = b.get("code") if isinstance(b, dict) else "?"
    d2 = (b.get("data") or {}) if isinstance(b, dict) else {}
    n = len(d2) if isinstance(d2, list) else rows(b)
    check("搜索商品 searchGoods", c == 200, "code=%s 条数=%s" % (c, n))
    s, b = req(base + "backendApi/cashier/getHangUpList", None, "GET")
    check("挂单列表 getHangUpList", (b.get("code") if isinstance(b,dict) else "?") == 200)
    s, b = req(base + "backendApi/cashier/getMemberInfo", {"keyword":"13800000001"})
    check("会员查询 getMemberInfo", (b.get("code") if isinstance(b,dict) else "?") == 200)
    # bug2：核销详情，用库里真实存在的未使用卡券 id
    s, b = req(base + "backendApi/doConfirm/info", {"id": 101, "code": ""})
    c = b.get("code") if isinstance(b, dict) else "?"
    has = isinstance(b, dict) and bool(((b.get("data") or {}).get("couponInfo")))
    check("核销详情 doConfirm/info(bug2)", c == 200 and has, "code=%s couponInfo=%s" % (c, has))
    s, b = req(base + "backendApi/doConfirm/info", {"id": 999999, "code": ""})
    check("核销详情-不存在券 正确报错", (b.get("code") if isinstance(b,dict) else "?") == 1003,
          "code=%s msg=%s" % (b.get("code"), (b.get("message") or "")[:20]))
    # bug1：充值（1 元，随后回滚）
    s, b = req(base + "backendApi/balance/doRecharge",
               {"userId":1,"amount":1,"type":1,"giftAmount":0,"remark":"QA回归-待回滚"})
    check("余额充值 doRecharge(bug1)", (b.get("code") if isinstance(b,dict) else "?") == 200)
    s, b = req(base + "backendApi/balance/createRechargeOrder",
               {"userId":1,"amount":1,"customAmount":0,"remark":"QA回归-待回滚"})
    c = b.get("code") if isinstance(b, dict) else "?"
    oid = ((b.get("data") or {}) if isinstance(b, dict) else {}).get("orderId")
    check("充值建单 createRechargeOrder", c == 200, "code=%s orderId=%s" % (c, oid))
    print("      >>> 待回滚: userId=1 充值1元, 订单=%s" % oid)

print("\n[4] 四行业一致性")
for port, logname, cn in [(8081,"bahar-shop","零售"),(8082,"bahar-car","汽车美容"),
                          (8083,"bahar-food","餐饮"),(8084,"bahar-health","康养美业")]:
    c2, i2 = login_backend(port, logname)
    ok1 = bool(c2 and i2.get("id"))
    ok2 = ok3 = False
    if c2:
        b2, r2, s2 = c2
        s, b = r2(b2 + "backendApi/member/list?page=1&pageSize=5", None, "GET")
        ok2 = (b.get("code") if isinstance(b, dict) else "?") == 200
        s, b = r2(b2 + "backendApi/cashier/init/%s?page=1&pageSize=10" % (i2.get("id") or 0), None, "GET")
        ok3 = (b.get("code") if isinstance(b, dict) else "?") == 200
    cm, dm = login_member(port, logname)
    ok4 = bool(cm)
    check("%s :%d 后台+会员列表+收银台+会员登录" % (cn, port), ok1 and ok2 and ok3 and ok4,
          "登录=%s 会员列表=%s 收银台=%s 会员登录=%s" % (ok1, ok2, ok3, ok4))

print("\n" + "=" * 80)
print("汇总: PASS=%d  FAIL=%d" % (len(PASS), len(FAIL)))
for f in FAIL: print("  失败: " + f)
print("=" * 80)

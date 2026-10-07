# -*- coding: utf-8 -*-
"""支付链路 mock 验证：不依赖真实微信商户号，验证「下单 -> 支付成功回调 -> 入账」全链路。

做法：
1) 用后台/收银账号建一笔充值订单（createRechargeOrder，此时订单为未支付、余额不变）
2) 按微信支付通知格式构造 XML，用配置的 partnerKey(wxpay.apiV2) 计算 MD5 签名
3) POST 到 clientApi/pay/weixinCallback —— 后端 WxPayKit.verifyNotify 验签通过后会
   走 paymentService.paymentCallback() 真实入账
4) 校验：订单状态/支付状态、会员余额增量、是否生成支付流水

启动后端时需追加 mock 配置：
  --spring.config.additional-location=file:D:/git-double/bahar/deploy/tmp/mock-wxpay.yml
"""
import json, re, time, hashlib, urllib.parse
import urllib.request, urllib.error
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

BASE = "http://127.0.0.1:8081/"
LOG = "D:/logs/bahar-shop/server.log"
PARTNER_KEY = "MOCKQA20261007PARTNERKEY"   # 必须与 mock-wxpay.yml 的 wxpay.apiV2 一致
USER_ID = 1
AMOUNT = 1          # 元
PASS, FAIL = [], []
def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  [%s] %-32s %s" % ("PASS" if cond else "FAIL", name, detail))

TOKEN = None
def req(url, payload=None, method=None, raw=None, ctype=None):
    data = raw if raw is not None else (json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None)
    m = method or ("POST" if payload is not None or raw is not None else "GET")
    h = {"Content-Type": ctype or "application/json;charset=utf-8", "platform": "PC",
         "isWechat": "N", "merchantNo": "10001", "storeId": "0"}
    if TOKEN: h["Access-Token"] = TOKEN
    r = urllib.request.Request(url, data=data, headers=h, method=m)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

def wx_sign(params, key):
    """微信支付 MD5 签名：非空、排除 sign，按 key 字典序拼接后附 &key=xxx，MD5 大写"""
    ks = sorted([k for k, v in params.items() if v not in (None, "") and k != "sign"])
    sb = "&".join("%s=%s" % (k, params[k]) for k in ks)
    sb += "&key=" + key
    return hashlib.md5(sb.encode("utf-8")).hexdigest().upper()

print("=" * 76)
print("支付链路 mock 验证   （下单 -> 伪造微信回调 -> 入账）")
print("=" * 76)

# 1) 后台登录
s, b = req(BASE + "backendApi/captcha/getLoginCode", None, "GET")
uuid = (json.loads(b).get("data") or {}).get("uuid")
code = None
for _ in range(30):
    txt = open(LOG, encoding="utf-8", errors="ignore").read()
    for mm in re.finditer(r"生成验证码\s*=\s*(\S+?),\s*uuid\s*=\s*(\S+)", txt):
        if mm.group(2).strip() == uuid.strip(): code = mm.group(1).strip()
    if code: break
    time.sleep(0.5)
s, b = req(BASE + "backendApi/login/doLogin",
           {"username":"bahar","password":"123456","captchaCode":code,"uuid":uuid})
TOKEN = (json.loads(b).get("data") or {}).get("token")
check("后台登录", bool(TOKEN))

# 2) 建充值订单
s, b = req(BASE + "backendApi/balance/createRechargeOrder",
           {"userId": USER_ID, "amount": AMOUNT, "customAmount": 0, "remark": "支付链路mock"})
d = (json.loads(b).get("data") or {}) if s == 200 else {}
order_id, order_sn = d.get("orderId"), d.get("orderSn")
check("建充值订单 createRechargeOrder", bool(order_id and order_sn),
      "orderId=%s orderSn=%s" % (order_id, order_sn))

# 3) 伪造微信支付成功通知
params = {
    "return_code": "SUCCESS",
    "return_msg": "OK",
    "appid": "mockappid",
    "mch_id": "mockmchid",
    "out_trade_no": order_sn,
    "transaction_id": "MOCKTXN" + str(int(time.time())),
    "total_fee": str(AMOUNT * 100),      # 微信单位是分
    "result_code": "SUCCESS",
    "trade_type": "JSAPI",
}
params["sign"] = wx_sign(params, PARTNER_KEY)
xml = "<xml>" + "".join("<{0}><![CDATA[{1}]]></{0}>".format(k, v) for k, v in params.items()) + "</xml>"
print("\n  回调 XML（签名=%s…）" % params["sign"][:16])
s, body = req(BASE + "clientApi/pay/weixinCallback", raw=xml.encode("utf-8"),
              method="POST", ctype="application/xml")
check("回调接口响应", s == 200, "HTTP=%s body=%s" % (s, (body or "")[:40].replace("\n"," ")))

# 4) 校验入账结果
time.sleep(1)
import subprocess, os
MY = "C:/Program Files/MySQL/MySQL Server 8.0/bin/mysql.exe"
def sql(q):
    p = subprocess.run([MY, "-uroot", "-p" + "rootAdmin@0731", "-D", "bahar-db",
                        "--default-character-set=utf8", "-e", q],
                       capture_output=True, text=True)
    return p.stdout
out = sql("SELECT ID,STATUS,PAY_STATUS,AMOUNT,PAY_AMOUNT FROM mt_order WHERE ID=%s;" % order_id)
print("\n  订单: %s" % out.replace("\n", " | ").strip())
paid = ("B" in out.split("\n")[1]) if len(out.split("\n")) > 1 else False
check("订单变为已支付", paid, out.replace("\n", " ")[:80])
bal = sql("SELECT balance FROM mt_user WHERE ID=%d;" % USER_ID)
print("  会员余额: %s" % bal.replace("\n", " ").strip())
check("余额已入账", bal.strip().split("\n")[-1] not in ("0.00", ""), bal.replace("\n"," ").strip()[:40])
bl = sql("SELECT COUNT(*) FROM mt_balance WHERE order_sn='%s';" % order_sn)
check("生成余额流水", bl.strip().split("\n")[-1] != "0", bl.replace("\n"," ").strip()[:40])

print("\n" + "=" * 76)
print("汇总: PASS=%d  FAIL=%d" % (len(PASS), len(FAIL)))
for f in FAIL: print("  失败: " + f)
print("待清理: mt_order.id=%s  会员%d 余额增量 %d 元" % (order_id, USER_ID, AMOUNT))
print("=" * 76)

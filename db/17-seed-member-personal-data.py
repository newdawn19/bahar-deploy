# -*- coding: utf-8 -*-
"""给会员端演示账号补"个人数据"：订单、购物车、卡券、积分、余额。

背景（实测出来的，不是猜的）：
  会员端默认登录账号是 ID=1（张伟 / 13800000001）。但演示数据生成器把订单、
  卡券、积分全随机分给了 ID 103+ 的会员，ID 1 名下**一条都没有**：
    mt_order  80 条，USER_ID 最小是 103
    mt_user_coupon 30 条，最小 103
    mt_point  27 条，最小 105
    mt_cart   0 条（全库空）
  结果就是会员端登录后「我的订单 / 我的卡券 / 积分明细 / 购物车」全是空白页——
  恰恰是演示现场最想点开的几页。

做法：不改已有数据，只新增。
  - 订单：挑 6 条现有订单整单复制（含 mt_order_goods 明细），换 ID / 订单号，
    USER_ID 设为目标会员，状态覆盖 A/B/D/E/F/I，让"我的订单"有东西可分栏看。
  - 购物车 / 卡券 / 积分 / 余额：直接按表结构插入。

幂等：每次先删掉本脚本造的 ID 段（>= 900000）再插，可重复执行。

用法: set DB_PASSWORD=... && python deploy/db/17-seed-member-personal-data.py
"""
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
USER = os.environ.get("DB_USER", "root")
PWD = os.environ.get("DB_PASSWORD", "")

# 库 -> 演示账号（前三个会员，销售最可能输入的就这几个）
INSTANCES = [
    ("bahar-db", [1, 2, 3]),
    ("bahar-car", [1, 2, 3]),
    ("bahar-catering", [1, 2, 3]),
    ("bahar-health", [1, 2, 3]),
]

# 必须有 A（待支付），否则会员端"待处理"角标永远是 0，看着像没数据
ORDER_STATUS_PLAN = ["I", "I", "F", "E", "D", "A"]  # 已完成×2/待收货/已发货/待发货/待支付
NEW_ID_BASE = 900000  # 本脚本造的数据统一用这个 ID 段，便于幂等清理


def q(db, sql):
    cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p", "-N", "-B",
           "--default-character-set=utf8mb4", "-D", db, "-e", sql]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [SQL 失败] %s | %s" % (sql[:80], p.stderr.strip()[:160]))
        return []
    return [l.split("\t") for l in p.stdout.splitlines() if l.strip()]


def exec_sql(db, sql):
    cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p",
           "--default-character-set=utf8mb4", "-D", db]
    p = subprocess.run(cmd, input=sql, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [执行失败] %s" % p.stderr.strip()[:300])
        return False
    return True


def columns(db, table):
    return [r[0] for r in q(db, "DESC `%s`" % table)]


def esc(v):
    if v is None or v == "NULL":
        return "NULL"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def insert(db, table, cols, rows):
    if not rows:
        return 0
    sql = "INSERT INTO `%s` (`%s`) VALUES " % (table, "`,`".join(cols))
    parts = []
    for r in rows:
        parts.append("(" + ",".join(esc(v) for v in r) + ")")
    sql += ",".join(parts) + ";"
    return len(rows) if exec_sql(db, sql) else 0


def copy_orders(db, uid, mobile):
    """复制现有订单给目标会员：整单复制 + 明细复制。"""
    ocols = columns(db, "mt_order")
    src = q(db, "SELECT `ID` FROM mt_order WHERE `USER_ID` > 0 ORDER BY `ID` LIMIT 6")
    if not src:
        return 0
    gcols = columns(db, "mt_order_goods")
    now = datetime.now()
    made = 0
    next_id = NEW_ID_BASE + 1000 + uid * 10
    for i, (oid,) in enumerate(src):
        rows = q(db, "SELECT * FROM mt_order WHERE ID=%s" % oid)
        if not rows:
            continue
        vals = list(rows[0])
        idx = {c: n for n, c in enumerate(ocols)}
        new_id = next_id + i
        vals[idx["ID"]] = str(new_id)
        vals[idx["USER_ID"]] = str(uid)
        vals[idx["ORDER_SN"]] = "D%s%04d" % (now.strftime("%Y%m%d"), new_id % 10000)
        vals[idx["STATUS"]] = ORDER_STATUS_PLAN[i % len(ORDER_STATUS_PLAN)]
        if "PAY_STATUS" in idx and ORDER_STATUS_PLAN[i % len(ORDER_STATUS_PLAN)] != "A":
            vals[idx["PAY_STATUS"]] = "B"
        if "IS_VISITOR" in idx:
            vals[idx["IS_VISITOR"]] = "N"
        if "OPERATOR" in idx:
            vals[idx["OPERATOR"]] = "system"
        vals[idx["CREATE_TIME"]] = (now - timedelta(days=20 - i * 3)).strftime("%Y-%m-%d %H:%M:%S")
        vals[idx["UPDATE_TIME"]] = vals[idx["CREATE_TIME"]]
        if not insert(db, "mt_order", ocols, [vals]):
            continue
        # 明细
        gidx = {c: n for n, c in enumerate(gcols)}
        grows = q(db, "SELECT * FROM mt_order_goods WHERE ORDER_ID=%s" % oid)
        new_goods = []
        for j, g in enumerate(grows):
            gv = list(g)
            gv[gidx["ID"]] = str(new_id * 100 + j)
            gv[gidx["ORDER_ID"]] = str(new_id)
            new_goods.append(gv)
        if new_goods:
            insert(db, "mt_order_goods", gcols, new_goods)
        made += 1
    return made


def seed_commission(db, uid, merchant_id=1, store_id=1):
    """分销：会员端 commission/overview 依赖 mt_commission_relation（分销关系）+ 有效佣金流水。

    实测两个坑：
      1. mt_commission_relation 全库是空的 —— 没有"下线"关系，概览里 userCount 恒为 0
      2. 之前造的佣金流水里会员 1 那条 STATUS='C'（已作废），不计入统计
    """
    now = datetime.now()
    n = 0
    # 分销关系：给目标会员挂 3 个下线
    cols = columns(db, "mt_commission_relation")
    rows = []
    for i, sub in enumerate([101, 102, 103]):
        v = {k: "NULL" for k in cols}
        v["ID"] = str(NEW_ID_BASE + uid * 100 + 40 + i)
        v["MERCHANT_ID"] = str(merchant_id)
        v["USER_ID"] = str(uid)
        v["LEVEL"] = "1"
        v["INVITE_CODE"] = "INV%s%03d" % (uid, i)
        v["SUB_USER_ID"] = str(sub)
        v["DESCRIPTION"] = "演示分销关系"
        v["CREATE_TIME"] = (now - timedelta(days=30 - i * 5)).strftime("%Y-%m-%d %H:%M:%S")
        v["UPDATE_TIME"] = v["CREATE_TIME"]
        v["STATUS"] = "A"
        v["OPERATOR"] = "system"
        rows.append([v[k] for k in cols])
    n = insert(db, "mt_commission_relation", cols, rows)

    # 佣金流水：把作废的那条改成有效，并补几条
    exec_sql(db, "UPDATE mt_commission_log SET STATUS='B' WHERE USER_ID=%d AND STATUS='C';" % uid)
    cols = columns(db, "mt_commission_log")
    rows = []
    for i, (typ, amt, st) in enumerate([("goods", 68.50, "A"), ("payment", 120.00, "B"),
                                        ("recharge", 45.00, "B")]):
        v = {k: "NULL" for k in cols}
        v["ID"] = str(NEW_ID_BASE + uid * 100 + 50 + i)
        v["MERCHANT_ID"] = str(merchant_id)
        v["TARGET"] = "member"
        v["TYPE"] = typ
        v["LEVEL"] = "1"
        v["USER_ID"] = str(uid)
        v["STORE_ID"] = str(store_id)
        v["AMOUNT"] = str(amt)
        v["DESCRIPTION"] = "演示佣金"
        v["CREATE_TIME"] = (now - timedelta(days=12 - i * 4)).strftime("%Y-%m-%d %H:%M:%S")
        v["UPDATE_TIME"] = v["CREATE_TIME"]
        v["STATUS"] = st
        v["OPERATOR"] = "system"
        rows.append([v[k] for k in cols])
    insert(db, "mt_commission_log", cols, rows)
    return n


def seed_simple(db, uid, mobile, merchant_id=1, store_id=1):
    now = datetime.now()
    n = {"cart": 0, "coupon": 0, "point": 0, "balance": 0}

    # 购物车：挑 4 个真实商品
    goods = q(db, "SELECT ID FROM mt_goods WHERE STATUS='A' ORDER BY ID LIMIT 4")
    if goods:
        cols = columns(db, "mt_cart")
        rows = []
        for i, (gid,) in enumerate(goods):
            v = {c: "NULL" for c in cols}
            v["ID"] = str(NEW_ID_BASE + uid * 100 + i)
            v["USER_ID"] = str(uid)
            v["MERCHANT_ID"] = str(merchant_id)
            v["STORE_ID"] = str(store_id)
            v["IS_VISITOR"] = "N"
            v["HANG_NO"] = ""
            v["SKU_ID"] = "0"
            # 餐饮库的 mt_cart 多一个 TABLE_ID 列，且查询会按它过滤；
            # 留 NULL 会被过滤掉（会员端购物车显示 0 条），这里显式给 0 = 未开台
            if "TABLE_ID" in v:
                v["TABLE_ID"] = "0"
            v["GOODS_ID"] = str(gid)
            v["NUM"] = str(random.choice([1, 2, 1, 3]))
            v["CREATE_TIME"] = now.strftime("%Y-%m-%d %H:%M:%S")
            v["UPDATE_TIME"] = v["CREATE_TIME"]
            v["STATUS"] = "A"
            rows.append([v[c] for c in cols])
        n["cart"] = insert(db, "mt_cart", cols, rows)

    # 我的卡券
    cps = q(db, "SELECT ID,NAME,AMOUNT FROM mt_coupon WHERE STATUS='A' ORDER BY ID LIMIT 3")
    if cps:
        cols = columns(db, "mt_user_coupon")
        rows = []
        for i, c in enumerate(cps):
            cid = c[0]
            amount = c[2] if len(c) > 2 and c[2] not in (None, "NULL") else "10.00"
            v = {k: "NULL" for k in cols}
            v["ID"] = str(NEW_ID_BASE + uid * 100 + 10 + i)
            v["TYPE"] = "C"
            v["CODE"] = "C%s%03d" % (uid, i)  # 非空，且要唯一，否则核销时扫不出来
            v["GROUP_ID"] = "1"
            v["COUPON_ID"] = str(cid)
            v["MOBILE"] = mobile
            v["USER_ID"] = str(uid)
            v["MERCHANT_ID"] = str(merchant_id)
            v["STORE_ID"] = str(store_id)
            v["AMOUNT"] = amount
            # 前两张未使用（余额=面额），第三张已用（余额 0）
            used = (i == 2)
            v["BALANCE"] = "0.00" if used else amount
            v["STATUS"] = "B" if used else "A"
            v["USED_TIME"] = now.strftime("%Y-%m-%d %H:%M:%S") if used else "NULL"
            v["CREATE_TIME"] = (now - timedelta(days=15 - i * 4)).strftime("%Y-%m-%d %H:%M:%S")
            v["UPDATE_TIME"] = v["CREATE_TIME"]
            v["EXPIRE_TIME"] = (now + timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
            v["OPERATOR"] = "system"
            v["UUID"] = "DEMO%s%d" % (uid, i)
            rows.append([v[k] for k in cols])
        n["coupon"] = insert(db, "mt_user_coupon", cols, rows)

    # 积分明细
    cols = columns(db, "mt_point")
    rows = []
    for i, (desc, amt) in enumerate([("消费赠送积分", 120), ("积分兑换扣减", -50),
                                     ("会员日活动奖励", 200), ("签到赠送", 5)]):
        v = {k: "NULL" for k in cols}
        v["ID"] = str(NEW_ID_BASE + uid * 100 + 20 + i)
        v["MERCHANT_ID"] = str(merchant_id)
        v["STORE_ID"] = str(store_id)
        v["USER_ID"] = str(uid)
        v["AMOUNT"] = str(amt)
        v["DESCRIPTION"] = desc
        v["CREATE_TIME"] = (now - timedelta(days=18 - i * 4)).strftime("%Y-%m-%d %H:%M:%S")
        v["UPDATE_TIME"] = v["CREATE_TIME"]
        v["OPERATOR"] = "system"
        v["STATUS"] = "A"
        rows.append([v[k] for k in cols])
    n["point"] = insert(db, "mt_point", cols, rows)

    # 余额明细
    cols = columns(db, "mt_balance")
    rows = []
    for i, (desc, amt) in enumerate([("会员充值", 500.00), ("到店消费", -128.50),
                                     ("会员充值", 300.00)]):
        v = {k: "NULL" for k in cols}
        v["ID"] = str(NEW_ID_BASE + uid * 100 + 30 + i)
        v["MERCHANT_ID"] = str(merchant_id)
        v["STORE_ID"] = str(store_id)
        v["MOBILE"] = mobile
        v["USER_ID"] = str(uid)
        v["AMOUNT"] = str(amt)
        v["DESCRIPTION"] = desc
        v["CREATE_TIME"] = (now - timedelta(days=16 - i * 5)).strftime("%Y-%m-%d %H:%M:%S")
        v["UPDATE_TIME"] = v["CREATE_TIME"]
        v["OPERATOR"] = "system"
        v["STATUS"] = "A"
        rows.append([v[k] for k in cols])
    n["balance"] = insert(db, "mt_balance", cols, rows)
    return n


def main():
    random.seed(20261004)
    ok = True
    for db, uids in INSTANCES:
        print("=" * 60)
        print(db)
        print("=" * 60)
        # 幂等：先清掉本脚本上次造的数据
        exec_sql(db, "DELETE FROM mt_order WHERE ID >= %d;" % NEW_ID_BASE)
        # mt_order_goods 的 ID 是"订单ID*100+序号"，不在 900000 段里，
        # 所以只能按 ORDER_ID 清，按 ID 清会漏掉、再跑就主键冲突
        exec_sql(db, "DELETE FROM mt_order_goods WHERE ORDER_ID >= %d;" % NEW_ID_BASE)
        for t in ("mt_cart", "mt_user_coupon", "mt_point", "mt_balance",
                  "mt_commission_relation", "mt_commission_log"):
            exec_sql(db, "DELETE FROM `%s` WHERE ID >= %d;" % (t, NEW_ID_BASE))
        for uid in uids:
            mob = q(db, "SELECT MOBILE FROM mt_user WHERE ID=%d" % uid)
            mobile = mob[0][0] if mob else ""
            o = copy_orders(db, uid, mobile)
            n = seed_simple(db, uid, mobile)
            c = seed_commission(db, uid)
            print("  会员 %d(%s): 订单 %d / 购物车 %d / 卡券 %d / 积分 %d / 余额 %d / 分销关系 %d"
                  % (uid, mobile, o, n["cart"], n["coupon"], n["point"], n["balance"], c))
            if o == 0:
                ok = False
    print("=" * 60)
    print("总体: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""给增值能力菜单灌演示数据：分销佣金记录 + 预约项目（汽车/餐饮/康养三库）。

背景：后台新挂了 分销佣金 / 预约项目 菜单，但 mt_commission_log、mt_book 全是 0 行，
页面打开就是空表 —— 挂了菜单等于没挂。本脚本按固定 ID 段先删后插，可重复执行。

枚举对齐（抄自 baharCar common/enums）：
  - CommissionStatusEnum：A=待结算 B=已结算 C=已作废
  - CommissionTargetEnum：member=会员分销 staff=员工提成
  - CommissionTypeEnum：goods=商品订单 payment=付款订单 recharge=充值订单
  - 预约项目 mt_book.STATUS='A' 启用（logo 由 13-gen-images.py 统一生成填充）

用法：
    set DB_PASSWORD=...
    python deploy/db/15-seed-value-data.py
"""
import os
import subprocess
from datetime import datetime, timedelta

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
USER = os.environ.get("DB_USER", "root")
PWD = os.environ.get("DB_PASSWORD", "")
NOW = datetime(2026, 10, 3, 19, 0, 0)

BOOKS = {
    # 库 -> [(名称, 类型, 排序, 服务日期样例, 描述)]
    "bahar-car": [
        ("精致洗车", "service", 1, "2026-10-05,2026-10-06,2026-10-07", " exterior清洗+吸尘+轮胎养护".strip()),
        ("打蜡养护", "service", 2, "2026-10-05,2026-10-08", "巴西棕榈蜡手工打蜡，持久 60 天"),
        ("深度保养", "service", 3, "2026-10-06,2026-10-09", "机油机滤更换 + 21 项安全检测"),
        ("内饰除菌", "service", 4, "2026-10-07,2026-10-10", "高温蒸汽除菌除螨"),
    ],
    "bahar-catering": [
        ("周末家宴预约", "table", 1, "2026-10-07,2026-10-08", "4-6 人家庭套餐，提前 1 天预订"),
        ("生日宴预约", "table", 2, "2026-10-05,2026-10-06", "赠长寿面 + 包厢布置"),
        ("商务宴请预约", "table", 3, "2026-10-09,2026-10-10", "10 人包厢，含茶位"),
        ("下午茶预约", "table", 4, "2026-10-04,2026-10-05", "户外卡座，双人下午茶"),
    ],
    "bahar-health": [
        ("香薰 SPA", "service", 1, "2026-10-05,2026-10-06,2026-10-07", "60 分钟全身香薰理疗"),
        ("肩颈理疗", "service", 2, "2026-10-05,2026-10-08", "30 分钟肩颈放松，适合久坐人群"),
        ("面部深层清洁", "service", 3, "2026-10-06,2026-10-09", "小气泡清洁 + 补水面膜"),
        ("头疗养护", "service", 4, "2026-10-07,2026-10-10", "45 分钟头皮护理"),
    ],
}

COMMISSION = [
    # (target, type, level, status, 说明)
    ("member", "goods", 1, "A", "一级会员分销佣金"),
    ("member", "goods", 2, "A", "二级会员分销佣金"),
    ("member", "payment", 1, "B", "会员付款订单佣金"),
    ("member", "recharge", 1, "B", "会员充值推广佣金"),
    ("staff", "goods", 1, "A", "店员销售提成"),
    ("staff", "goods", 1, "B", "店员销售提成（已结算）"),
    ("member", "goods", 1, "B", "一级会员分销佣金（已结算）"),
    ("member", "goods", 1, "C", "退款订单佣金作废"),
]


def q(db, sql):
    cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p", "-N", "-B",
           "--default-character-set=utf8mb4", "-D", db, "-e", sql]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [SQL 失败] %s" % p.stderr.strip()[:200])
        return []
    return [l.split("\t") for l in p.stdout.splitlines() if l.strip()]


def esc(s):
    return (s or "").replace("\\", "\\\\").replace("'", "''")


def dt(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


def main():
    ok = True
    for db, books in BOOKS.items():
        print("=== %s 佣金记录 + 预约项目" % db)
        users = [r[0] for r in q(db, "SELECT ID FROM mt_user WHERE IS_STAFF='N' ORDER BY ID LIMIT 8")]
        orders = [r[0] for r in q(db, "SELECT ID FROM mt_order ORDER BY ID LIMIT 8")]
        stores = [r[0] for r in q(db, "SELECT ID FROM mt_store LIMIT 3")]
        if not users:
            print("  [FAIL] 没有会员可挂")
            ok = False
            continue
        sql = ["DELETE FROM mt_commission_log WHERE ID BETWEEN 1 AND 99;",
               "DELETE FROM mt_book WHERE ID BETWEEN 1 AND 99;"]
        # 佣金 8 条：金额 8.8 - 128.8，状态 A/B 为主、1 条 C 作废
        for i, (target, typ, level, status, desc) in enumerate(COMMISSION, 1):
            amount = round(8.8 + i * 15.3, 2)
            uid = users[i % len(users)]
            oid = orders[(i - 1) % len(orders)] if orders else 0
            sid = stores[i % len(stores)] if stores else 1
            created = dt(NOW - timedelta(days=20 - i * 2, hours=i % 6))
            is_cash = "Y" if status == "B" else "N"
            cash_time = "NULL" if status != "B" else "'%s'" % dt(NOW - timedelta(days=18 - i * 2))
            sql.append(
                "INSERT INTO mt_commission_log (ID,MERCHANT_ID,TARGET,TYPE,LEVEL,USER_ID,STORE_ID,"
                "STAFF_ID,ORDER_ID,AMOUNT,RULE_ID,RULE_ITEM_ID,DESCRIPTION,SETTLE_UUID,CASH_ID,"
                "IS_CASH,CASH_TIME,CREATE_TIME,UPDATE_TIME,STATUS,OPERATOR) VALUES "
                "(%d,1,'%s','%s',%d,%s,%s,0,%s,'%s',0,0,'%s','%s',0,'%s',%s,'%s','%s','%s','system');"
                % (i, target, typ, level, uid, sid, oid, amount,
                   esc(desc), "settle-demo-%03d" % i if status == "B" else "",
                   is_cash, cash_time, created, created, status))
        # 预约项目 4 条（logo 先留空，由 13-gen-images.py 补图）
        for i, (name, typ, sort, dates, desc) in enumerate(books, 1):
            sql.append(
                "INSERT INTO mt_book (ID,MERCHANT_ID,STORE_ID,GOODS_ID,SERVICE_DATES,"
                "SERVICE_TIMES,SERVICE_STAFF_IDS,DESCRIPTION,CREATE_TIME,UPDATE_TIME,OPERATOR,"
                "STATUS,name,type,logo,cate_id,sort) VALUES "
                "(%d,1,1,0,'%s','10:00-11:00,14:00-15:00','','%s','%s','%s','system','A','%s','%s','',0,%d);"
                % (i, esc(dates), esc(desc), dt(NOW - timedelta(days=10)), dt(NOW - timedelta(days=1)),
                   esc(name), typ, sort))
        out_sql = "USE `%s`;\nSET NAMES utf8mb4;\n%s\n" % (db, "\n".join(sql))
        cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p",
               "--default-character-set=utf8mb4"]
        p = subprocess.run(cmd, input=out_sql, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if p.returncode != 0:
            print("  [执行失败] %s" % p.stderr.strip()[:300])
            ok = False
        else:
            print("  [OK] 佣金 8 条 + 预约项目 %d 条" % len(books))
    print("=" * 56)
    print("总体:", "PASS" if ok else "有失败项")


if __name__ == "__main__":
    main()

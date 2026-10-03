# -*- coding: utf-8 -*-
"""灌行业特色数据 + 订单状态多样化 + 账号角色区分。

背景（2026-10-03 复检结论）：行业表全空（mt_vehicle 0 行、mt_table 0 行…）、
80 笔订单全是「已完成+已支付」看不到状态流转、三个账号全挂超级管理员角色。
演示时客户点开行业亮点页全是空的，状态流转也讲不了。

枚举对齐（写错就显示不出来，全部抄自各工程 enums）：
  - 车辆订单 VehicleOrderStatusEnum：A=已提交 B=服务中 C=已完成
  - 车辆类型 VehicleTypeEnum：存中文值（轿车/SUV/MPV/跑车/皮卡/其他）
  - 桌台 TableUseStatusEnum：A=未开台 B=已开台 C=就餐中
  - 订单 OrderStatusEnum：A待支付 B已支付 C已取消 D待发货 E已发货 F已收货 G已删除 H已退款 I已完成
  - 退款 RefundStatusEnum：A待审核 B已同意 C已拒绝 D已取消 E已完成；TYPE: return/exchange
幂等：固定 ID 段先 DELETE 再 INSERT，可重复执行。

用法：
    set DB_PASSWORD=...
    python deploy/db/14-gen-industry-data.py
"""
import os
import subprocess
from datetime import datetime, timedelta

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
USER = os.environ.get("DB_USER", "root")
PWD = os.environ.get("DB_PASSWORD", "")

NOW = datetime(2026, 10, 3, 18, 0, 0)

CARS = [
    ("奔驰 E300L", "轿车", "粤B·8D102", "曜岩黑", "奔驰", "WDDZH4GB2JJ123451"),
    ("宝马 X5 xDrive30i", "SUV", "粤B·7C668", "矿石白", "宝马", "WBAJA5C59KB123452"),
    ("奥迪 A4L 40TFSI", "轿车", "粤B·5E810", "冰川白", "奥迪", "LFV3A28W8K3123453"),
    ("特斯拉 Model Y", "SUV", "粤B·D10086", "珍珠白", "特斯拉", "LRW3E7EK5MC123454"),
    ("比亚迪 汉 EV", "轿车", "粤B·F2024", "赤帝红", "比亚迪", "LGXCE6CB1M0123455"),
    ("别克 GL8 ES", "MPV", "粤B·9F315", "墨玉黑", "别克", "LSGKE8384S A123456" .replace(" ", "")),
    ("保时捷 718", "跑车", "粤B·GT666", "迈阿密蓝", "保时捷", "WP0ZZZ98ZJS123457"),
    ("长城 炮", "皮卡", "粤B·P8899", "工程黄", "长城", "LGWCEA969M2123458"),
    ("丰田 赛那", "MPV", "粤B·3H257", "钛辉银", "丰田", "LVGBH4L90MP123459"),
    ("理想 L7", "SUV", "粤B·L7007", "紫色", "理想", "LZZ5444C2ND123460"),
    ("小鹏 P7i", "轿车", "粤B·G2121", "星阙绿", "小鹏", "LZSDAA1W8N1123461"),
    ("问界 M7", "SUV", "粤B·M7777", "深空灰", "问界", "LZZDBAD44SD123462"),
]

TABLES = [
    # (编号, 区域, 坐人数, 使用状态)
    ("A01", 1, 4, "A"), ("A02", 1, 4, "A"), ("A03", 1, 4, "C"), ("A04", 1, 4, "C"),
    ("A05", 1, 6, "A"), ("A06", 1, 6, "B"),
    ("B01", 2, 8, "B"), ("B02", 2, 8, "A"), ("B03", 2, 10, "A"), ("B04", 2, 8, "A"),
    ("C01", 3, 2, "C"), ("C02", 3, 2, "C"), ("C03", 3, 2, "A"), ("C04", 3, 4, "A"),
    ("C05", 3, 4, "A"), ("C06", 3, 4, "A"),
]

ORDER_STATUS_PLAN = [
    # (条数, 订单STATUS, PAY_STATUS, 说明)
    (6, "A", "A", "待支付"),
    (6, "C", "A", "已取消"),
    (6, "D", "B", "待发货"),
    (6, "E", "B", "已发货"),
    (6, "F", "B", "已收货"),
    (6, "H", "B", "已退款"),
]
# 打乱状态时要跳过的 ID（车辆订单要用到部分订单? 不用；车辆订单独立生成）


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


def days_ago(n, h=10, m=30):
    return dt(NOW - timedelta(days=n, hours=0, minutes=0)).replace("10:30:00", "%02d:%02d:00" % (h, m))


def gen_car():
    """汽车：车辆档案 12 台 + 车辆订单 12 单（状态 A/B/C 铺开）。"""
    db = "bahar-car"
    print("=== %s 车辆档案 + 车辆订单" % db)
    users = [r[0] for r in q(db, "SELECT ID FROM mt_user WHERE IS_STAFF='N' ORDER BY ID LIMIT 12")]
    if not users:
        print("  [FAIL] 没有可用会员")
        return
    sql = ["DELETE FROM mt_vehicle WHERE ID BETWEEN 1 AND 99;",
           "DELETE FROM mt_vehicle_order WHERE ID BETWEEN 1 AND 99;"]
    for i, (model, vtype, plate, color, brand, vin) in enumerate(CARS, 1):
        sql.append(
            "INSERT INTO mt_vehicle (ID,USER_ID,MERCHANT_ID,VEHICLE_MODEL,VEHICLE_TYPE,"
            "VEHICLE_PLATE_NO,VEHICLE_COLOR,VEHICLE_BRAND,VIN,STATUS,IS_DEFAULT,OPERATOR,"
            "CREATE_TIME,UPDATE_TIME) VALUES "
            "(%d,%s,1,'%s','%s','%s','%s','%s','%s','A','%s','system','%s','%s');"
            % (i, users[i % len(users)], esc(model), vtype, esc(plate), esc(color),
               esc(brand), vin, "Y" if i <= 2 else "N", days_ago(40 - i * 2, 9, 15), days_ago(3, 16, 0)))
    # 车辆订单：A 已提交 2 / B 服务中 4 / C 已完成 6
    plan = ["A", "A", "B", "B", "B", "B", "C", "C", "C", "C", "C", "C"]
    for i, st in enumerate(plan, 1):
        plate = CARS[i - 1][2]
        uid = users[i % len(users)]
        created = days_ago(30 - i * 2, 9 + i % 8, 15)
        updated = days_ago(max(0, 29 - i * 2), 14 + i % 6, 0)
        sql.append(
            "INSERT INTO mt_vehicle_order (ID,USER_ID,MERCHANT_ID,STORE_ID,ORDER_SN,"
            "VEHICLE_PLATE_NO,STATUS,SCAN_CODE,REMARK,OPERATOR,CREATE_TIME,UPDATE_TIME) VALUES "
            "(%d,%s,1,1,'VO2026%05d','%s','%s','','%s','system','%s','%s');"
            % (i, uid, 70000 + i, esc(plate), st,
               esc({0: ""}.get(0, "") or ("常规保养" if st != "A" else "客户已预约，待进店")),
               created, updated))
    return sql, db


def gen_catering():
    """餐饮：桌台区域 3 个 + 桌台 16 张 + 骑手 4 名。"""
    db = "bahar-catering"
    print("=== %s 桌台区域 + 桌台 + 骑手" % db)
    users = [r[0] for r in q(db, "SELECT ID FROM mt_user WHERE IS_STAFF='N' ORDER BY ID LIMIT 8")]
    sql = ["DELETE FROM mt_table_area WHERE ID BETWEEN 1 AND 99;",
           "DELETE FROM mt_table WHERE ID BETWEEN 1 AND 99;",
           "DELETE FROM mt_rider WHERE id BETWEEN 1 AND 99;"]
    areas = [(1, "大厅", "散台为主，靠窗位置视野好"),
             (2, "包厢", "8-10 人商务包厢，配独立电视"),
             (3, "户外卡座", "露天卡座，适合下午茶")]
    for aid, name, desc in areas:
        sql.append(
            "INSERT INTO mt_table_area (ID,NAME,MERCHANT_ID,STORE_ID,DESCRIPTION,"
            "CREATE_TIME,UPDATE_TIME,OPERATOR,SORT,STATUS) VALUES "
            "(%d,'%s',1,1,'%s','%s','%s','system',%d,'A');"
            % (aid, name, esc(desc), days_ago(50, 9, 0), days_ago(3, 15, 0), aid))
    for i, (code, area, ppl, use) in enumerate(TABLES, 1):
        use_time = "NULL" if use == "A" else "'%s'" % days_ago(0, 11 + i % 6, 30)
        sql.append(
            "INSERT INTO mt_table (CODE,AREA_ID,MERCHANT_ID,STORE_ID,MAX_PEOPLE,DESCRIPTION,"
            "CREATE_TIME,UPDATE_TIME,OPERATOR,SORT,STATUS,use_status,use_time) VALUES "
            "('%s',%d,1,1,%d,'%s人桌','%s','%s','system',%d,'A','%s',%s);"
            % (code, area, ppl, ppl, days_ago(50, 9, 0), days_ago(1, 18, 0), i, use, use_time))
    riders = [("R2026%04d" % (1001 + i),) for i in range(4)]
    for i, (rno,) in enumerate(riders):
        uid = users[i % len(users)] if users else 101
        sql.append(
            "INSERT INTO mt_rider (id,user_id,rider_no,merchant_id,store_id,id_card,"
            "id_card_front,id_card_back,health_cert,status,description,create_time,update_time) "
            "VALUES (%d,%s,'%s',1,1,'','','','','A','%s','%s','%s');"
            % (i + 1, uid, rno, esc("专送骑手"), days_ago(45, 10, 0), days_ago(2, 17, 0)))
    return sql, db


def mix_orders():
    """四库通用：把 80 笔「全已完成」改成有状态流转的分布，并给已退款补 mt_refund。"""
    stmts = []
    for db in ("bahar-db", "bahar-car", "bahar-catering", "bahar-health"):
        print("=== %s 订单状态多样化 + 退款样本" % db)
        ids = [r[0] for r in q(db, "SELECT ID FROM mt_order WHERE STATUS='I' ORDER BY ID")]
        if not ids:
            print("  [SKIP] 没有可改的订单")
            continue
        take = 0
        picked = []
        for n, st, ps, _ in ORDER_STATUS_PLAN:
            chunk = ids[take:take + n]
            picked.append((st, ps, chunk))
            take += n
        sql = []
        refund_rows = []
        rid = 1
        for st, ps, chunk in picked:
            if not chunk:
                continue
            idl = ",".join(chunk)
            if st == "A":
                sql.append("UPDATE mt_order SET STATUS='A',PAY_STATUS='A',PAY_TIME=NULL "
                           "WHERE ID IN (%s);" % idl)
            else:
                sql.append("UPDATE mt_order SET STATUS='%s',PAY_STATUS='%s' WHERE ID IN (%s);"
                           % (st, ps, idl))
            if st == "H":
                rows = q(db, "SELECT ID,USER_ID,STORE_ID,PAY_AMOUNT,ORDER_SN FROM mt_order "
                             "WHERE ID IN (%s)" % idl)
                for oid, uid, sid, amt, sn in rows:
                    refund_rows.append(
                        "INSERT INTO mt_refund (ID,ORDER_ID,MERCHANT_ID,STORE_ID,USER_ID,AMOUNT,"
                        "TYPE,REMARK,CREATE_TIME,UPDATE_TIME,STATUS,IMAGES,OPERATOR) VALUES "
                        "(%d,%s,1,%s,%s,'%s','return','客户申请退款，已原路退回','%s','%s','E','','system');"
                        % (rid, oid, sid or 1, uid, amt, days_ago(5 + rid % 10, 11, 20),
                           days_ago(4 + rid % 10, 15, 40)))
                    rid += 1
        sql += refund_rows
        if refund_rows:
            sql.insert(0, "DELETE FROM mt_refund WHERE ID BETWEEN 1 AND 99;")
        stmts.append((db, sql))
    return stmts


def roles():
    """账号角色区分：202（店员）从超管降到受限角色 202，只给会员/商品/订单/库存/门店。"""
    stmts = []
    LIMIT_ROOTS = {"会员管理": None, "商品管理": None, "订单管理": None, "库存管理": None, "门店管理": None}
    for db in ("bahar-db", "bahar-car", "bahar-catering", "bahar-health"):
        print("=== %s 账号角色区分" % db)
        roots = q(db, "SELECT source_id,source_name FROM t_source WHERE parent_id=0")
        want = [sid for sid, name in roots if name in LIMIT_ROOTS]
        if not want:
            print("  [SKIP] 找不到目标一级节点")
            continue
        sql = []
        sql.append("UPDATE t_account SET role_ids='202' WHERE acct_id=202;")
        sql.append("UPDATE t_account_duty SET duty_id=202 WHERE acct_id=202;")
        sql.append("DELETE FROM t_duty_source WHERE duty_id=202;")
        ids = q(db, "SELECT source_id FROM t_source WHERE parent_id IN (%s) OR source_id IN (%s)"
                % (",".join(want), ",".join(want)))
        sids = [r[0] for r in ids]
        base = 900001
        vals = []
        for i, sid in enumerate(sids):
            vals.append("(%d,202,%s)" % (base + i, sid))
        sql.append("INSERT INTO t_duty_source (duty_source_id,duty_id,source_id) VALUES %s;"
                   % ",".join(vals))
        print("  店员(202) 授权 %d 个权限节点（会员/商品/订单/库存/门店）" % len(sids))
        stmts.append((db, sql))
    return stmts


def run_sql(db, stmts):
    if not stmts:
        return False
    sql = "USE `%s`;\nSET NAMES utf8mb4;\n%s\n" % (db, "\n".join(stmts))
    cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p",
           "--default-character-set=utf8mb4"]
    p = subprocess.run(cmd, input=sql, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [执行失败] %s" % p.stderr.strip()[:400])
        return False
    return True


def main():
    ok = True
    for gen in (gen_car, gen_catering):
        r = gen()
        if not r:
            ok = False
            continue
        sql, db = r
        ok = run_sql(db, sql) and ok
        print("  [OK] 共 %d 条语句" % len(sql))
    for db, sql in mix_orders():
        ok = run_sql(db, sql) and ok
        print("  [OK] %s 共 %d 条语句" % (db, len(sql)))
    for db, sql in roles():
        ok = run_sql(db, sql) and ok
    print("=" * 60)
    print("总体:", "PASS" if ok else "有失败项，看上面日志")


if __name__ == "__main__":
    main()

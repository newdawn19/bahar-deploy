# -*- coding: utf-8 -*-
"""生成四行业演示数据（商品 / 会员 / 订单 / 明细 / 余额与积分流水）。

为什么必须动态取列：四库字段并不完全一致——
  - mt_goods：catering 缺 PLATFORM 与 book_id（car 的 GRADE_IDS 只是大小写不同，不算缺）
  - mt_user ：car / catering 缺 IP
  - mt_user_balance：只有零售库有这张表
  - mt_order：catering 独有餐台/人数/骑手等列，car 缺 PLATFORM
所以插入前先用 information_schema 取该库该表的真实列名，只写存在的列。

关键枚举（写错数据就显示不出来）：
  - 订单 STATUS：I=已完成 / B=已支付 / A=待支付 / C=已取消  → 用 I
  - 订单 PAY_STATUS：B=已支付 / A=待支付                    → 用 B
  - 订单 TYPE：goods=商品订单                                → 用 goods
  - PAY_TYPE：CASH / JSAPI / MICROPAY / BALANCE / ALISCAN / STORE
  - ORDER_MODE：express=配送 / oneself=自取
  - 通用状态：STATUS='A'（启用），YesOrNo='Y'/'N'

幂等：演示数据占用固定 ID 段（商品 1001+、会员 101+、订单 1001+），
      每次先按段 DELETE 再 INSERT，可重复执行。
"""
import io
import os
import random
import subprocess
from datetime import datetime, timedelta

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
OUT = r"D:\git-double\bahar\deploy\db\08-demo-data.sql"

random.seed(20260930)  # 固定种子，保证每次生成一致

MERCHANT_ID = 1
STORE_ID = 1
NOW = datetime(2026, 9, 30, 12, 0, 0)
PWD = "sZbejahexJx8f1vB9Z/YiQ=="  # base64(md5('123456'+'a1b2'))，会员端登录口令 123456
SALT = "a1b2"

# ---------------------------------------------------------------- 商品清单
# （分类序号 1-4，对应库里已有的 4 个分类）
GOODS = {
    "shop": {
        "db": "bahar-db",
        "price_lo": 3, "price_hi": 90,
        "cate": [
            ["乐事薯片 原味70g", "三只松鼠每日坚果", "好丽友派 12枚装", "奥利奥夹心饼干",
             "卫龙亲嘴烧", "洽洽山核桃瓜子", "良品铺子猪肉脯", "徐福记沙琪玛"],
            ["可口可乐 330ml", "农夫山泉 550ml", "康师傅冰红茶", "蒙牛纯牛奶 250ml",
             "星巴克拿铁 268ml", "青岛啤酒 500ml", "元气森林白桃味", "王老吉凉茶"],
            ["金号纯棉毛巾", "心相印抽纸 3层", "蓝月亮洗衣液 1kg", "高露洁全效牙膏",
             "舒肤佳沐浴露 720ml", "海飞丝洗发水 500ml", "苏泊尔保温杯 500ml", "天堂三折雨伞"],
            ["红富士苹果 500g", "海南香蕉 500g", "赣南脐橙 1kg", "山东大樱桃 250g",
             "阳光玫瑰葡萄 500g", "泰国金枕榴莲", "宁夏麒麟西瓜", "云南蓝莓 125g"],
        ],
    },
    "car": {
        "db": "bahar-car",
        "price_lo": 30, "price_hi": 880,
        "cate": [
            ["标准洗车", "精洗打蜡", "内饰深度清洗", "发动机舱清洗",
             "轮毂深度清洁", "漆面去污处理", "前挡玻璃镀膜", "全车臭氧消毒"],
            ["全车手工打蜡", "漆面镀晶", "内饰真皮护理", "座椅翻新修复",
             "顶棚绒面清洗", "空调系统清洗", "新车除甲醛", "局部划痕修复"],
            ["小保养 机油机滤", "大保养 三滤全换", "刹车片更换", "火花塞更换",
             "轮胎更换 单条", "四轮定位", "蓄电池更换", "空调滤芯更换"],
            ["米其林轮胎 205/55R16", "壳牌全合成机油 4L", "3M 隔热车膜", "70迈行车记录仪",
             "车载无线吸尘器", "固特异丝圈脚垫", "玻璃水 2L", "车载快充充电器"],
        ],
    },
    "catering": {
        "db": "bahar-catering",
        "price_lo": 6, "price_hi": 98,
        "cate": [
            ["宫保鸡丁", "麻婆豆腐", "秘制红烧肉", "水煮鱼片",
             "回锅肉", "清炒时蔬", "番茄牛腩煲", "蒜蓉粉丝扇贝"],
            ["口水鸡", "手拍黄瓜", "凉拌黑木耳", "皮蛋豆腐",
             "夫妻肺片", "东北大拉皮", "泡椒凤爪", "凉拌海带丝"],
            ["扬州炒饭", "阳春面", "葱油拌面", "虾仁小馄饨",
             "手工猪肉水饺", "腊味煲仔饭", "丝苗白米饭", "手工老面馒头"],
            ["鲜榨橙汁", "桂花酸梅汤", "柠檬蜂蜜水", "可口可乐",
             "雪碧", "王老吉", "现磨热豆浆", "冰镇啤酒"],
        ],
    },
    "health": {
        "db": "bahar-health",
        "price_lo": 68, "price_hi": 880,
        "cate": [
            ["深层清洁护理", "玻尿酸补水保湿", "美白淡斑护理", "抗衰紧致护理",
             "净颜祛痘护理", "眼部精细护理", "面部拨筋疏通", "小气泡深层清洁"],
            ["全身放松按摩", "肩颈疏通", "腰椎调理", "拔罐祛湿",
             "刮痧排毒", "艾灸养生", "中药足疗", "精油开背"],
            ["中药熏蒸", "体质辨识调理", "脾胃调理", "睡眠改善调理",
             "气血双补调理", "经络疏通", "肝胆调理", "亚健康调理"],
            ["胶原蛋白肽饮", "复合益生菌", "维生素C片", "深海鱼油软胶囊",
             "养生花草茶", "艾草足浴包", "乳胶护颈枕", "人体工学护腰垫"],
        ],
    },
}

# 中文姓名池（50 个）
NAMES = """张伟 王芳 李娜 刘洋 陈静 杨帆 赵敏 黄磊 周杰 吴桐
徐丽 孙浩 马超 朱婷 胡军 郭涛 何洁 高鹏 林薇 罗静
郑爽 梁宇 谢娜 宋佳 唐宁 许巍 韩雪 冯刚 曹颖 邓超
彭勇 曾毅 萧然 田甜 董洁 袁泉 潘玮 蒋雯 蔡明 余华
于洋 杜鹃 叶青 程磊 苏晴 魏晨 吕燕 丁俊 任达 沈冰""".split()

PAY_TYPES = ["JSAPI", "MICROPAY", "BALANCE", "CASH", "ALISCAN", "STORE"]
ORDER_MODES = ["oneself", "express"]


def sql_escape(s):
    return str(s).replace("\\", "\\\\").replace("'", "''")


def q(v):
    """生成 SQL 字面量"""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'%s'" % sql_escape(v)


def fetch_columns(db, table):
    sql = ("SELECT column_name FROM information_schema.columns "
           "WHERE table_schema='%s' AND table_name='%s';" % (db, table))
    p = subprocess.run([MYSQL, "-uroot", "-prootAdmin@0731", "-N", "-B", "-e", sql],
                       capture_output=True)
    return {c.strip().upper() for c in p.stdout.decode("utf-8", "replace").split("\n") if c.strip()}


def insert(db, table, rows, cols_of_db):
    """rows: list of dict（键用大写列名）；只保留该库真实存在的列"""
    if not rows:
        return []
    keys = [k for k in rows[0] if k.upper() in cols_of_db]
    if not keys:
        return []
    out = []
    for r in rows:
        vals = ", ".join(q(r.get(k)) for k in keys)
        out.append("INSERT INTO `%s` (%s) VALUES (%s);"
                   % (table, ", ".join("`%s`" % k for k in keys), vals))
    return out


def build(industry, cfg):
    db = cfg["db"]
    print("-- 生成 %s (%s) --" % (industry, db))
    cols = {t: fetch_columns(db, t) for t in
            ["mt_goods", "mt_user", "mt_order", "mt_order_goods",
             "mt_balance", "mt_point", "mt_user_balance", "mt_goods_cate"]}

    lines = ["USE `%s`;" % db, ""]
    lines.append("-- ===== %s 演示数据 =====" % industry)

    # ---------- 清理旧演示数据（固定 ID 段） ----------
    lines.append("DELETE FROM `mt_order_goods` WHERE ID >= 1001 AND ID < 9000;")
    lines.append("DELETE FROM `mt_balance`     WHERE ID >= 1001 AND ID < 9000;")
    lines.append("DELETE FROM `mt_point`       WHERE ID >= 1001 AND ID < 9000;")
    lines.append("DELETE FROM `mt_order`       WHERE ID >= 1001 AND ID < 9000;")
    lines.append("DELETE FROM `mt_goods`       WHERE ID >= 1001 AND ID < 9000;")
    lines.append("DELETE FROM `mt_user`        WHERE ID >= 101  AND ID < 900;")
    if cols["mt_user_balance"]:
        lines.append("DELETE FROM `mt_user_balance` WHERE ID >= 1001 AND ID < 9000;")
    lines.append("")

    # ---------- 商品 ----------
    goods_rows = []
    gid = 1001
    price_map = {}   # goods_id -> price
    for cate_idx, names in enumerate(cfg["cate"], start=1):
        for i, name in enumerate(names, start=1):
            price = round(random.uniform(cfg["price_lo"], cfg["price_hi"]), 2)
            line_price = round(price * random.uniform(1.15, 1.45), 2)
            goods_rows.append({
                "ID": gid, "TYPE": "goods", "MERCHANT_ID": MERCHANT_ID,
                "STORE_ID": STORE_ID, "NAME": name, "CATE_ID": cate_idx,
                "GOODS_NO": "D%04d" % gid,
                "PLATFORM": 0, "IS_SINGLE_SPEC": "Y",
                "PRICE": price, "LINE_PRICE": line_price,
                "COST_PRICE": round(price * 0.6, 2),
                "STOCK": random.randint(30, 500),
                "CAN_USE_POINT": "Y", "IS_MEMBER_DISCOUNT": "Y",
                "SORT": i, "INIT_SALE": random.randint(0, 300),
                "CREATE_TIME": NOW, "UPDATE_TIME": NOW,
                "OPERATOR": "system", "STATUS": "A",
            })
            price_map[gid] = price
            gid += 1
    lines.append("-- 商品 %d 个" % len(goods_rows))
    lines += insert(db, "mt_goods", goods_rows, cols["mt_goods"])
    lines.append("")

    # ---------- 会员 ----------
    user_rows = []
    for i in range(50):
        uid = 101 + i
        user_rows.append({
            "ID": uid, "MOBILE": "1380010%03d" % (i + 1),
            "NAME": NAMES[i], "USER_NO": "M%05d" % uid,
            "GRADE_ID": random.randint(1, 4),
            "BALANCE": round(random.uniform(0, 2000), 2),
            "POINT": random.randint(0, 5000),
            "SEX": 1 if i % 2 == 0 else 2,
            "PASSWORD": PWD, "SALT": SALT,
            "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            "IS_STAFF": "N", "STATUS": "A", "SOURCE": "system",
            "CREATE_TIME": NOW - timedelta(days=random.randint(30, 300)),
            "UPDATE_TIME": NOW, "OPERATOR": "system",
            "IP": "127.0.0.1",
        })
    lines.append("-- 会员 %d 个（口令 123456）" % len(user_rows))
    lines += insert(db, "mt_user", user_rows, cols["mt_user"])
    lines.append("")

    # ---------- 订单 + 明细 + 流水 ----------
    order_rows, og_rows, bal_rows, point_rows = [], [], [], []
    goods_ids = sorted(price_map)
    for k in range(80):
        oid = 1001 + k
        days_ago = random.randint(0, 29)
        created = NOW - timedelta(days=days_ago,
                                  hours=random.randint(0, 11),
                                  minutes=random.randint(0, 59))
        uid = random.randint(101, 150)
        items = random.sample(goods_ids, random.randint(1, 4))
        amount = 0.0
        for gi in items:
            num = random.choice([1, 1, 1, 2, 3])
            price = price_map[gi]
            amount += price * num
            og_rows.append({
                "ID": 1001 + len(og_rows), "ORDER_ID": oid, "GOODS_ID": gi,
                "SKU_ID": 0, "PRICE": price, "DISCOUNT": 0, "NUM": num,
                "CREATE_TIME": created, "UPDATE_TIME": created, "STATUS": "A",
            })
        amount = round(amount, 2)
        sn = "DEMO%s%04d" % (created.strftime("%Y%m%d"), k)
        order_rows.append({
            "ID": oid, "TYPE": "goods",
            "PAY_TYPE": random.choice(PAY_TYPES),
            "ORDER_MODE": random.choice(ORDER_MODES),
            "ORDER_SN": sn, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            "USER_ID": uid, "IS_VISITOR": "N",
            "AMOUNT": amount, "PAY_AMOUNT": amount, "DISCOUNT": 0,
            "DELIVERY_FEE": 0, "USE_POINT": 0, "POINT_AMOUNT": 0,
            "PLATFORM": 0, "STAFF_ID": random.randint(1, 3),
            "STATUS": "I", "PAY_STATUS": "B",
            "SETTLE_STATUS": "N", "CONFIRM_STATUS": "N", "COMMISSION_STATUS": "N",
            "CREATE_TIME": created, "PAY_TIME": created, "UPDATE_TIME": created,
            "OPERATOR": "system", "REMARK": "演示订单",
        })
        # 部分订单带充值与积分流水
        if k % 4 == 0:
            bal_rows.append({
                "ID": 1001 + len(bal_rows), "MERCHANT_ID": MERCHANT_ID,
                "STORE_ID": STORE_ID, "MOBILE": "1380010%03d" % (uid - 100),
                "USER_ID": uid, "ORDER_SN": sn,
                "AMOUNT": round(random.choice([100, 200, 300, 500, 800]), 2),
                "DESCRIPTION": "会员充值", "CREATE_TIME": created,
                "UPDATE_TIME": created, "OPERATOR": "system", "STATUS": "A",
            })
        if k % 3 == 0:
            point_rows.append({
                "ID": 1001 + len(point_rows), "MERCHANT_ID": MERCHANT_ID,
                "STORE_ID": STORE_ID, "USER_ID": uid, "ORDER_SN": sn,
                "AMOUNT": int(amount), "DESCRIPTION": "消费赠送积分",
                "CREATE_TIME": created, "UPDATE_TIME": created,
                "OPERATOR": "system", "STATUS": "A",
            })

    lines.append("-- 订单 %d 笔（近 30 天）" % len(order_rows))
    lines += insert(db, "mt_order", order_rows, cols["mt_order"])
    lines.append("-- 订单明细 %d 条" % len(og_rows))
    lines += insert(db, "mt_order_goods", og_rows, cols["mt_order_goods"])
    lines.append("-- 充值流水 %d 条" % len(bal_rows))
    lines += insert(db, "mt_balance", bal_rows, cols["mt_balance"])
    lines.append("-- 积分流水 %d 条" % len(point_rows))
    lines += insert(db, "mt_point", point_rows, cols["mt_point"])
    lines.append("")
    print("   商品 %d / 会员 %d / 订单 %d / 明细 %d / 充值 %d / 积分 %d"
          % (len(goods_rows), len(user_rows), len(order_rows),
             len(og_rows), len(bal_rows), len(point_rows)))
    return lines


if __name__ == "__main__":
    all_lines = ["-- 四行业演示数据（由 08-gen-demo-data.py 生成，可重复执行）",
                 "-- 会员端登录口令统一为 123456", ""]
    for name, cfg in GOODS.items():
        all_lines += build(name, cfg)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(all_lines))
    print("\n输出: %s (%d 行)" % (OUT, len(all_lines)))

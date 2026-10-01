# -*- coding: utf-8 -*-
"""补齐后台其余菜单的演示数据（文章 / 轮播 / 分组 / 标签 / 库存单据 /
会员领券 / 操作日志 / 打印机 / 员工 / 门店 / 卡券）。

背景：08 只生成了商品、会员、订单，后台不少菜单打开是空的，
演示时显得很假。这个脚本把剩余模块也填上，让每个菜单都像真在运营。

沿用 08 的做法：
  - 先用 information_schema 取该库该表的真实列名，只写存在的列（四库字段有差异）
  - 固定 ID 段（101+），先 DELETE 再 INSERT，幂等可重跑
  - 行业内容区分，四套各不相同
"""
import io
import random
import subprocess
from datetime import datetime, timedelta

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
OUT = r"D:\git-double\bahar\deploy\db\09-more-data.sql"

random.seed(20261001)

MERCHANT_ID = 1
STORE_ID = 1
NOW = datetime(2026, 10, 1, 12, 0, 0)

INDUSTRY = {
    "shop": {
        "db": "bahar-db",
        "article": [
            ("会员日狂欢 全场8折", "每月8号会员日，全场商品8折优惠，会员专享"),
            ("春季新品上市", "新一批休闲零食已上架，欢迎选购"),
            ("门店搬迁通知", "本店已迁至新址，营业时间不变"),
            ("积分兑换攻略", "教您如何用积分兑换心仪商品"),
            ("节假日营业时间", "节假日营业时间调整为 9:00-22:00"),
            ("夏日饮品节", "饮料专区满减活动进行中"),
            ("会员专享日", "每周三会员专享额外9折"),
            ("积分年底清零提醒", "年底积分将清零，请尽快兑换"),
        ],
        "banner": [("会员日全场8折", "/pages/index/index"),
                   ("春季新品上市", "/pages/goods/index"),
                   ("新人专享礼包", "/pages/coupon/index"),
                   ("门店环境展示", "/pages/article/index")],
        "stock": "零售商品",
    },
    "car": {
        "db": "bahar-car",
        "article": [
            ("春季爱车保养指南", "换季保养要点，让爱车保持最佳状态"),
            ("会员专享 洗车5折", "会员到店洗车享5折优惠"),
            ("内饰深度清洁的重要性", "定期清洁内饰，守护车内健康"),
            ("轮胎更换周期说明", "教您判断轮胎是否需要更换"),
            ("雨季行车安全提示", "雨天行车注意事项与安全检查"),
            ("会员积分兑换", "积分可兑换洗车、打蜡等服务"),
            ("新店开业钜惠", "新店开业期间办卡送好礼"),
            ("空调系统清洗常识", "空调异味从哪来，多久洗一次"),
        ],
        "banner": [("会员洗车5折", "/pages/index/index"),
                   ("精洗打蜡套餐", "/pages/goods/index"),
                   ("新客体验券", "/pages/coupon/index"),
                   ("施工车间展示", "/pages/article/index")],
        "stock": "汽车用品与耗材",
    },
    "catering": {
        "db": "bahar-catering",
        "article": [
            ("新品上市 夏季清爽菜系", "新增8道夏季清爽菜品，欢迎品尝"),
            ("会员日 全场9折", "每周二会员日，全场菜品9折"),
            ("本店招牌菜推荐", "主厨推荐：水煮鱼、红烧肉、宫保鸡丁"),
            ("外卖配送说明", "配送范围与费用说明"),
            ("包间预订须知", "包间预订流程与最低消费说明"),
            ("会员储值优惠", "充500送80，充1000送200"),
            ("食品安全公示", "本店食材来源与检测报告公示"),
            ("节日营业时间", "节日期间正常营业，欢迎光临"),
        ],
        "banner": [("会员日全场9折", "/pages/index/index"),
                   ("招牌菜推荐", "/pages/goods/index"),
                   ("储值送好礼", "/pages/coupon/index"),
                   ("餐厅环境展示", "/pages/article/index")],
        "stock": "食材与物料",
    },
    "health": {
        "db": "bahar-health",
        "article": [
            ("春季养生指南", "春季养肝护肝，饮食起居要点"),
            ("会员专享 护理套餐", "面部护理套餐会员专享价"),
            ("肩颈保养的重要性", "久坐族的肩颈保养建议"),
            ("艾灸养生的功效", "艾灸适合哪些人群，注意事项"),
            ("新会员体验活动", "首次到店体验价 98 元"),
            ("会员积分兑换", "积分可兑换护理项目与产品"),
            ("健康饮食建议", "配合调理的饮食搭配建议"),
            ("节假日预约提醒", "节假日客流较多，建议提前预约"),
        ],
        "banner": [("会员护理套餐", "/pages/index/index"),
                   ("新客体验98元", "/pages/goods/index"),
                   ("养生茶饮赠饮", "/pages/coupon/index"),
                   ("门店环境展示", "/pages/article/index")],
        "stock": "护理耗材与产品",
    },
}

GROUPS = ["普通会员组", "银卡会员组", "金卡会员组", "企业客户组"]
TAGS = [("高频消费", "#E8722D"), ("大额客户", "#0E9F6E"), ("价格敏感", "#409EFF"),
        ("沉睡会员", "#909399"), ("新客", "#7C5CE0"), ("待回访", "#F56C6C")]

MODULES = ["会员管理", "商品管理", "订单管理", "卡券管理", "营销管理", "门店设置"]


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'%s'" % str(v).replace("\\", "\\\\").replace("'", "''")


def fetch_columns(db, table):
    sql = ("SELECT column_name FROM information_schema.columns "
           "WHERE table_schema='%s' AND table_name='%s';" % (db, table))
    p = subprocess.run([MYSQL, "-uroot", "-prootAdmin@0731", "-N", "-B", "-e", sql],
                       capture_output=True)
    return {c.strip().upper() for c in p.stdout.decode("utf-8", "replace").split("\n") if c.strip()}


def insert(db, table, rows, cols):
    if not rows:
        return []
    keys = [k for k in rows[0] if k.upper() in cols]
    if not keys:
        return []
    out = []
    for r in rows:
        vals = ", ".join(q(r.get(k)) for k in keys)
        out.append("INSERT INTO `%s` (%s) VALUES (%s);"
                   % (table, ", ".join("`%s`" % k for k in keys), vals))
    return out


def build(key, cfg):
    db = cfg["db"]
    print("-- %s (%s) --" % (key, db))
    cols = {t: fetch_columns(db, t) for t in
            ["mt_article", "mt_banner", "mt_user_group", "mt_user_tag", "mt_stock",
             "mt_user_coupon", "t_action_log", "mt_printer", "mt_staff", "mt_store",
             "mt_coupon"]}

    L = ["USE `%s`;" % db, "", "-- ===== %s 补充数据 =====" % key]

    # 清理（只动 101+ 段，不动原有基础数据）
    for t in ["mt_article", "mt_banner", "mt_user_group", "mt_user_tag", "mt_stock",
              "mt_user_coupon", "t_action_log", "mt_printer", "mt_staff", "mt_store",
              "mt_coupon"]:
        if cols[t]:
            L.append("DELETE FROM `%s` WHERE ID >= 101 AND ID < 9000;" % t)
    L.append("")

    # ---------- 文章 ----------
    rows = []
    for i, (title, brief) in enumerate(cfg["article"], start=1):
        rows.append({
            "ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            "TITLE": title, "BRIEF": brief, "URL": "", "IMAGE": "",
            "DESCRIPTION": brief, "CLICK": random.randint(20, 800),
            "CREATE_TIME": NOW - timedelta(days=random.randint(1, 60)),
            "UPDATE_TIME": NOW, "OPERATOR": "system", "SORT": i, "STATUS": "A",
        })
    L.append("-- 文章 %d 条" % len(rows))
    L += insert(db, "mt_article", rows, cols["mt_article"])

    # ---------- 轮播 ----------
    rows = []
    for i, (title, url) in enumerate(cfg["banner"], start=1):
        rows.append({
            "ID": 100 + i, "TITLE": title, "MERCHANT_ID": MERCHANT_ID,
            "STORE_ID": STORE_ID, "URL": url, "IMAGE": "",
            "DESCRIPTION": title, "CREATE_TIME": NOW, "UPDATE_TIME": NOW,
            "OPERATOR": "system", "SORT": i, "STATUS": "A",
        })
    L.append("-- 轮播 %d 条" % len(rows))
    L += insert(db, "mt_banner", rows, cols["mt_banner"])

    # ---------- 会员分组 ----------
    rows = []
    for i, name in enumerate(GROUPS, start=1):
        rows.append({
            "ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            "NAME": name, "PARENT_ID": 0, "DESCRIPTION": name,
            "CREATE_TIME": NOW, "UPDATE_TIME": NOW, "OPERATOR": "system", "STATUS": "A",
        })
    L.append("-- 会员分组 %d 条" % len(rows))
    L += insert(db, "mt_user_group", rows, cols["mt_user_group"])

    # ---------- 会员标签 ----------
    rows = []
    for i, (name, color) in enumerate(TAGS, start=1):
        rows.append({
            "ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "NAME": name,
            "COLOR": color, "SORT": i, "DESCRIPTION": name,
            "CREATE_TIME": NOW, "UPDATE_TIME": NOW, "OPERATOR": "system", "STATUS": "A",
        })
    L.append("-- 会员标签 %d 条" % len(rows))
    L += insert(db, "mt_user_tag", rows, cols["mt_user_tag"])

    # ---------- 库存单据 ----------
    rows = []
    for i in range(1, 21):
        in_out = "入库" if i % 3 else "出库"
        t = NOW - timedelta(days=random.randint(0, 45))
        rows.append({
            "ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            "TYPE": in_out,
            "DESCRIPTION": "%s单 %s-%04d（%s）" % (in_out, cfg["stock"], i, t.strftime("%Y%m%d")),
            "CREATE_TIME": t, "UPDATE_TIME": t, "OPERATOR": "system", "STATUS": "A",
        })
    L.append("-- 库存单据 %d 条" % len(rows))
    L += insert(db, "mt_stock", rows, cols["mt_stock"])

    # ---------- 会员领券 ----------
    rows = []
    for i in range(1, 31):
        uid = 100 + random.randint(1, 60)
        used = i % 3 == 0
        t = NOW - timedelta(days=random.randint(1, 40))
        rows.append({
            "ID": 100 + i, "CODE": "CP%s%05d" % (key.upper()[:3], i),
            "TYPE": "C", "IMAGE": "", "GROUP_ID": 1,
            "COUPON_ID": random.randint(1, 3),
            "MOBILE": "13800100%03d" % (uid - 100) if uid > 100 else "13800000001",
            "USER_ID": uid, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            "AMOUNT": random.choice([5, 10, 20, 30, 50]),
            "BALANCE": 0 if used else random.choice([5, 10, 20, 30, 50]),
            "STATUS": "B" if used else "A",
            "USED_TIME": t + timedelta(days=random.randint(1, 10)) if used else None,
            "CREATE_TIME": t, "UPDATE_TIME": t,
            "EXPIRE_TIME": NOW + timedelta(days=random.randint(10, 90)),
            "OPERATOR": "system", "UUID": "", "ORDER_ID": 0,
        })
    L.append("-- 会员领券 %d 条" % len(rows))
    L += insert(db, "mt_user_coupon", rows, cols["mt_user_coupon"])

    # ---------- 操作日志 ----------
    rows = []
    for i in range(1, 61):
        m = random.choice(MODULES)
        t = NOW - timedelta(days=random.randint(0, 20),
                            hours=random.randint(0, 11),
                            minutes=random.randint(0, 59))
        rows.append({
            "ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            "ACTION_TIME": t, "TIME_CONSUMING": random.randint(20, 900),
            "CLIENT_IP": "127.0.0.1", "MODULE": m,
            "URL": "/backendApi/%s/list" % m, "ACCT_NAME": "bahar",
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "CLIENT_PORT": random.randint(40000, 60000),
            "PARAM": '{"page":1,"pageSize":10}',
        })
    L.append("-- 操作日志 %d 条" % len(rows))
    L += insert(db, "t_action_log", rows, cols["t_action_log"])

    # ---------- 打印机 ----------
    rows = [{"ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
             "SN": "SN%s%04d" % (key.upper()[:3], i),
             "NAME": "%s%s" % (["前台小票机", "后厨打印机"][i - 1], ""),
             "AUTO_PRINT": "Y", "CREATE_TIME": NOW, "UPDATE_TIME": NOW,
             "DESCRIPTION": "演示用打印机", "OPERATOR": "system", "STATUS": "A"}
            for i in (1, 2)]
    L.append("-- 打印机 %d 台" % len(rows))
    L += insert(db, "mt_printer", rows, cols["mt_printer"])

    # ---------- 员工 ----------
    names = ["陈明", "刘婷", "赵强"][:3]
    rows = []
    for i, nm in enumerate(names, start=1):
        rows.append({
            "ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            "USER_ID": 0, "CATEGORY": random.randint(1, 3),
            "MOBILE": "13900100%03d" % i, "REAL_NAME": nm, "WECHAT": "",
            "CREATE_TIME": NOW - timedelta(days=random.randint(30, 200)),
            "UPDATE_TIME": NOW, "AUDITED_STATUS": "A", "AUDITED_TIME": NOW,
            "DESCRIPTION": "演示员工",
        })
    L.append("-- 员工 %d 人" % len(rows))
    L += insert(db, "mt_staff", rows, cols["mt_staff"])

    # ---------- 门店（再补 2 家分店）----------
    rows = []
    for i, nm in enumerate(["城东分店", "新区旗舰店"], start=1):
        rows.append({
            "ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "NAME": nm,
            "QR_CODE": "", "LOGO": "", "IS_DEFAULT": "N",
            "CONTACT": "演示联系人", "PHONE": "1380013800%d" % i,
            "ADDRESS": "演示市演示区第 %d 号" % (100 + i),
            "LATITUDE": "31.23", "LONGITUDE": "121.47", "DISTANCE": 0,
            "HOURS": "09:00-21:00", "LICENSE": "", "CREDIT_CODE": "",
            "DESCRIPTION": "演示分店", "CREATE_TIME": NOW, "UPDATE_TIME": NOW,
            "STATUS": "A", "OPERATOR": "system",
        })
    L.append("-- 门店 %d 家" % len(rows))
    L += insert(db, "mt_store", rows, cols["mt_store"])

    # ---------- 卡券（再补 4 张）----------
    coupons = [("新客专享券", 10), ("满100减20", 20), ("会员日券", 15), ("节日礼包券", 30)]
    rows = []
    for i, (nm, amt) in enumerate(coupons, start=1):
        rows.append({
            "ID": 100 + i, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": STORE_ID,
            # IS_GIVE 是整数不是 char，写 'Y' 会报 Incorrect integer value
            "GROUP_ID": 1, "TYPE": "C", "NAME": nm, "IS_GIVE": 1,
            "GRADE_IDS": "", "POINT": 0, "APPLY_GOODS": "", "RECEIVE_CODE": "",
            # EXPIRE_TYPE 是字符串（现有数据用 'fix'），EXPIRE_TIME 是整数天数，
            # content 是 int —— 按错误类型写会报 Data truncated / Incorrect value
            "USE_FOR": "", "EXPIRE_TYPE": "fix",
            "EXPIRE_TIME": 90,
            "BEGIN_TIME": NOW, "END_TIME": NOW + timedelta(days=90),
            "AMOUNT": amt, "SEND_WAY": "1", "SEND_NUM": 0,
            "TOTAL": 500, "LIMIT_NUM": 1, "EXCEPT_TIME": "",
            "STORE_IDS": "", "DESCRIPTION": nm, "IMAGE": "", "REMARKS": "演示卡券",
            "IN_RULE": "", "OUT_RULE": "", "CREATE_TIME": NOW, "UPDATE_TIME": NOW,
            "OPERATOR": "system", "STATUS": "A", "content": 0,
        })
    L.append("-- 卡券 %d 张" % len(rows))
    L += insert(db, "mt_coupon", rows, cols["mt_coupon"])

    L.append("")
    return L


if __name__ == "__main__":
    all_lines = ["-- 后台其余菜单的演示数据（由 09-gen-more-data.py 生成，可重复执行）", ""]
    for key, cfg in INDUSTRY.items():
        all_lines += build(key, cfg)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(all_lines))
    print("\n输出: %s" % OUT)

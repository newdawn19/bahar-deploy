# -*- coding: utf-8 -*-
"""把后台「看着空」的角落补上：商户 / 后台账号 / 职务角色，以及
会员地址、会员标签关联、卡券分组、门店商品、库存明细。

起因：19 个菜单的列表本身都不为空，但仍有几处打开是空的或只有 1 条——
  商户信息 1 条（按账号所属商户过滤，看不到别人）
  后台账号 1 条、角色职务 1 条
  会员详情里的收货地址、所属标签 0 条
  库存单据的明细行、门店可售商品 0 条
演示时这些地方一打开就露馅，一并补齐。

沿用 09 的做法：先取真实列名只写存在的列；固定 ID 段（201+，避开 09 的 101+）；
先 DELETE 再 INSERT，幂等可重跑；四库内容按行业区分。

用法：
    python deploy/db/12-gen-extra-data.py            # 只生成 SQL
    python deploy/db/12-gen-extra-data.py --exec     # 生成并导入
"""
import io
import os
import subprocess
import sys
from datetime import datetime

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
OUT = r"D:\git-double\bahar\deploy\db\12-extra-data.sql"


def mysql_pwd():
    """口令不写进仓库：优先环境变量 DB_PASSWORD，其次读 deploy/.env.local"""
    p = os.environ.get("DB_PASSWORD")
    if p:
        return p
    env = os.path.join(os.path.dirname(OUT), "..", ".env.local")
    try:
        for line in io.open(env, encoding="utf-8"):
            if line.strip().startswith("DB_PASSWORD="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


PWD = mysql_pwd()

NOW = datetime(2026, 10, 2, 9, 0, 0)
MERCHANT_ID = 1

# 与库里现有账号一致（sha1 + 固定 salt），新账号沿用同密码，避免造完登不上
PWD_HASH = "b380f7a1afe140f323a3528a0fd709c65e65e2a1"
PWD_SALT = "1a2b3c4d5e6f7a8b"

# 四库内容：商户 / 职务 / 账号 / 收货地址 / 卡券分组
INDUSTRY = {
    "shop": {
        "db": "bahar-db",
        "merchant": [
            (201, "20001", "惠民连锁便利店", "张为民", "13800100201",
             "北京市朝阳区建国路 88 号", "社区连锁便利店，主营零食饮料与日用百货"),
            (202, "20002", "优鲜生活超市", "李优鲜", "13800100202",
             "北京市海淀区中关村大街 15 号", "生鲜与日用品综合超市，支持会员储值"),
        ],
        "duty": [(201, "门店店长", "负责单店日常经营与员工排班"),
                 (202, "财务专员", "负责账单核对与储值结算")],
        "account": [(201, "shop_manager", "门店店长", "王店长"),
                    (202, "shop_finance", "财务专员", "赵会计")],
        "address": ["北京市朝阳区建国路 88 号 3 单元 501",
                    "北京市朝阳区望京 SOHO T1 座 2201",
                    "北京市海淀区中关村大街 15 号院 2 号楼",
                    "北京市西城区金融街 7 号",
                    "北京市丰台区南三环东路 6 号",
                    "北京市通州区万达广场 B 座 1102"],
        "couponGroup": [(201, "新人专享礼包", 50.00, "注册即送的新人券包"),
                        (202, "节假日促销包", 100.00, "节假日通用券包")],
    },
    "car": {
        "db": "bahar-car",
        "merchant": [
            (201, "20001", "驰洁汽车服务连锁", "陈驰", "13800100201",
             "上海市闵行区莘庄工业区申北路 66 号", "汽车清洗美容连锁，含维修保养"),
            (202, "20002", "车美汇汽车养护", "周美汇", "13800100202",
             "上海市浦东新区张江镇科苑路 200 号", "中高端车辆养护与贴膜服务"),
        ],
        "duty": [(201, "服务顾问", "负责客户接待与项目推荐"),
                 (202, "技师主管", "负责施工安排与质量把关")],
        "account": [(201, "car_advisor", "服务顾问", "孙顾问"),
                    (202, "car_tech", "技师主管", "吴技师")],
        "address": ["上海市闵行区莘庄工业区申北路 66 号",
                    "上海市浦东新区张江镇科苑路 200 号",
                    "上海市徐汇区漕溪北路 331 号",
                    "上海市静安区南京西路 1266 号",
                    "上海市杨浦区五角场万达广场 C 座",
                    "上海市普陀区长寿路 285 号"],
        "couponGroup": [(201, "首单洗车礼包", 30.00, "首次到店洗车券包"),
                        (202, "养护套餐包", 200.00, "打蜡镀晶等养护券包")],
    },
    "food": {
        "db": "bahar-catering",
        "merchant": [
            (201, "20001", "味享餐饮连锁", "何味享", "13800100201",
             "广州市天河区体育西路 101 号", "中式快餐连锁，含外卖业务"),
            (202, "20002", "小满食集", "郑小满", "13800100202",
             "广州市越秀区北京路 295 号", "小吃集市与茶饮复合门店"),
        ],
        "duty": [(201, "前厅经理", "负责堂食接待与翻台"),
                 (202, "后厨主管", "负责出品与食材损耗")],
        "account": [(201, "food_hall", "前厅经理", "林经理"),
                    (202, "food_kitchen", "后厨主管", "黄主管")],
        "address": ["广州市天河区体育西路 101 号 A 座",
                    "广州市越秀区北京路 295 号",
                    "广州市海珠区新港东路 1000 号",
                    "广州市荔湾区上下九步行街 58 号",
                    "广州市白云区万达广场 3 层",
                    "广州市番禺区市桥街光明北路 12 号"],
        "couponGroup": [(201, "新客尝鲜包", 20.00, "首次点单立减券包"),
                        (202, "工作日午餐包", 40.00, "工作日午市专用券包")],
    },
    "health": {
        "db": "bahar-health",
        "merchant": [
            (201, "20001", "康怡美容养生", "钱康怡", "13800100201",
             "杭州市西湖区文三路 259 号", "美容美体与中医养生综合门店"),
            (202, "20002", "静和康养中心", "孙静和", "13800100202",
             "杭州市拱墅区莫干山路 851 号", "面向中老年群体的康养理疗中心"),
        ],
        "duty": [(201, "美容顾问", "负责客户咨询与方案定制"),
                 (202, "理疗师主管", "负责理疗排班与服务标准")],
        "account": [(201, "health_advisor", "美容顾问", "沈顾问"),
                    (202, "health_tech", "理疗师主管", "许理疗")],
        "address": ["杭州市西湖区文三路 259 号 2 幢",
                    "杭州市拱墅区莫干山路 851 号",
                    "杭州市上城区庆春路 118 号",
                    "杭州市滨江区江南大道 3688 号",
                    "杭州市余杭区五常大道 88 号",
                    "杭州市下城区中山北路 600 号"],
        "couponGroup": [(201, "体验礼券包", 99.00, "首次到店体验券包"),
                        (202, "疗程续费包", 500.00, "老客续费专享券包")],
    },
}

# 造关联数据时引用的真实 ID（各库一致，已核对）
USER_IDS = [1, 2, 3, 4, 5, 6]
GOODS_IDS = [1, 2, 3, 4, 5, 6, 7, 8]
STORE_IDS = [1, 101, 102]
TAG_IDS = [101, 102, 103, 104, 105, 106]
STOCK_IDS = [101, 102, 103, 104, 105]


def q(v):
    """按类型生成 SQL 字面量"""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace("\\", "\\\\").replace("'", "''")
    return "'%s'" % s


def fetch_columns(db, table):
    sql = ("SELECT column_name FROM information_schema.columns "
           "WHERE table_schema='%s' AND table_name='%s' ORDER BY ordinal_position;" % (db, table))
    p = subprocess.run([MYSQL, "-h127.0.0.1", "-uroot", "-p" + PWD, "-N", "-B", "-e", sql],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return [l.strip() for l in p.stdout.splitlines() if l.strip()]


def insert(db, table, rows, cols):
    """rows: list of dict。只写该表实际存在的列（四库字段有差异）"""
    valid = set(fetch_columns(db, table))
    use = [c for c in cols if c in valid]
    if not use:
        return []
    out = []
    for r in rows:
        vals = [q(r.get(c)) for c in use]
        out.append("INSERT INTO `%s`.`%s` (`%s`) VALUES (%s);"
                   % (db, table, "`,`".join(use), ",".join(vals)))
    return out


def delete(db, table, id_col, ids):
    return ["DELETE FROM `%s`.`%s` WHERE `%s` IN (%s);"
            % (db, table, id_col, ",".join(str(i) for i in ids))]


def build(key):
    cfg = INDUSTRY[key]
    db = cfg["db"]
    lines = ["-- ===== %s (%s) =====" % (db, key)]

    # 1. 商户：补到 3 条
    ids = [m[0] for m in cfg["merchant"]]
    lines += delete(db, "mt_merchant", "ID", ids)
    rows = []
    for mid, no, name, contact, phone, addr, desc in cfg["merchant"]:
        rows.append({"ID": mid, "TYPE": "MERCHANT", "NO": no, "NAME": name,
                     "CONTACT": contact, "PHONE": phone, "ADDRESS": addr,
                     "DESCRIPTION": desc, "STATUS": "A",
                     "CREATE_TIME": NOW, "UPDATE_TIME": NOW, "OPERATOR": "demo"})
    lines += insert(db, "mt_merchant", rows,
                    ["ID", "TYPE", "NO", "NAME", "CONTACT", "PHONE", "ADDRESS",
                     "DESCRIPTION", "STATUS", "CREATE_TIME", "UPDATE_TIME", "OPERATOR"])

    # 2. 职务角色：补到 3 条
    #    duty_type 必须存 AdminRoleEnum 的 key（'1'=超级管理员/'2'=普通管理员/'3'=用户角色），
    #    后端 BackendLoginController.getInfo() 以 duty_type == enum.key 反查角色 value，
    #    过去误写 'SYSTEM' 会导致 roles 恒为空、登录后菜单/路由全丢。这些为普通经营角色，按 '2' 存。
    ids = [d[0] for d in cfg["duty"]]
    lines += delete(db, "t_duty", "duty_id", ids)
    rows = [{"duty_id": did, "merchant_id": MERCHANT_ID, "duty_name": name,
             "status": "A", "description": desc, "duty_type": "2"}
            for did, name, desc in cfg["duty"]]
    lines += insert(db, "t_duty", rows,
                    ["duty_id", "merchant_id", "duty_name", "status", "description", "duty_type"])

    # 3. 后台账号：补到 3 条（密码沿用现有账号的 hash，同为 123456）
    ids = [a[0] for a in cfg["account"]]
    lines += delete(db, "t_account", "acct_id", ids)
    lines += delete(db, "t_account_duty", "acc_duty_id", ids)
    rows = []
    for aid, akey, aname, real in cfg["account"]:
        rows.append({"acct_id": aid, "account_key": "demo-key-%010d" % aid,
                     "account_name": aname, "password": PWD_HASH,
                     "account_status": 1, "is_active": 1,
                     "create_date": NOW, "modify_date": NOW, "salt": PWD_SALT,
                     "role_ids": "1", "locked": 0, "owner_id": 1,
                     "real_name": real, "merchant_id": MERCHANT_ID,
                     "store_id": 0, "staff_id": 0})
    lines += insert(db, "t_account", rows,
                    ["acct_id", "account_key", "account_name", "password", "account_status",
                     "is_active", "create_date", "modify_date", "salt", "role_ids", "locked",
                     "owner_id", "real_name", "merchant_id", "store_id", "staff_id"])

    # 关联到 duty_id=1（超级管理员），否则新账号登录后一个菜单都看不到；
    # 新增的 201/202 两条职务仅作为「角色职务」列表的数据展示
    rows = [{"acc_duty_id": aid, "acct_id": aid, "duty_id": 1}
            for aid, akey, aname, real in cfg["account"]]
    lines += insert(db, "t_account_duty", rows, ["acc_duty_id", "acct_id", "duty_id"])

    # 4. 会员收货地址：6 条
    ids = list(range(201, 207))
    lines += delete(db, "mt_address", "ID", ids)
    rows = []
    for i, uid in enumerate(USER_IDS):
        rows.append({"ID": 201 + i, "USER_ID": uid, "NAME": "会员%d" % uid,
                     "MOBILE": "13800100%03d" % uid, "PROVINCE_ID": 110000,
                     "CITY_ID": 110100, "REGION_ID": 110105,
                     "DETAIL": cfg["address"][i], "IS_DEFAULT": "Y" if i == 0 else "N",
                     "CREATE_TIME": NOW, "UPDATE_TIME": NOW, "STATUS": "A"})
    lines += insert(db, "mt_address", rows,
                    ["ID", "USER_ID", "NAME", "MOBILE", "PROVINCE_ID", "CITY_ID",
                     "REGION_ID", "DETAIL", "IS_DEFAULT", "CREATE_TIME", "UPDATE_TIME", "STATUS"])

    # 5. 会员标签关联：每人 2 个标签，共 12 条
    ids = list(range(201, 213))
    lines += delete(db, "mt_user_tag_relation", "ID", ids)
    rows = []
    n = 0
    for uid in USER_IDS:
        for tag in (TAG_IDS[n % len(TAG_IDS)], TAG_IDS[(n + 1) % len(TAG_IDS)]):
            rows.append({"ID": 201 + n, "USER_ID": uid, "TAG_ID": tag,
                         "CREATE_TIME": NOW, "OPERATOR": "demo"})
            n += 1
    lines += insert(db, "mt_user_tag_relation", rows,
                    ["ID", "USER_ID", "TAG_ID", "CREATE_TIME", "OPERATOR"])

    # 6. 卡券分组：补到 3 条
    ids = [g[0] for g in cfg["couponGroup"]]
    lines += delete(db, "mt_coupon_group", "ID", ids)
    rows = [{"ID": gid, "MERCHANT_ID": MERCHANT_ID, "STORE_ID": 1, "NAME": name,
             "MONEY": money, "NUM": 100, "TOTAL": 100, "DESCRIPTION": desc,
             "CREATE_TIME": NOW, "UPDATE_TIME": NOW, "OPERATOR": "demo", "STATUS": "A"}
            for gid, name, money, desc in cfg["couponGroup"]]
    lines += insert(db, "mt_coupon_group", rows,
                    ["ID", "MERCHANT_ID", "STORE_ID", "NAME", "MONEY", "NUM", "TOTAL",
                     "DESCRIPTION", "CREATE_TIME", "UPDATE_TIME", "OPERATOR", "STATUS"])

    # 7. 门店可售商品：8 条，分散到 3 家门店
    ids = list(range(201, 209))
    lines += delete(db, "mt_store_goods", "ID", ids)
    rows = []
    for i, gid in enumerate(GOODS_IDS):
        rows.append({"ID": 201 + i, "MERCHANT_ID": MERCHANT_ID,
                     "STORE_ID": STORE_IDS[i % len(STORE_IDS)], "GOODS_ID": gid,
                     "CREATE_TIME": NOW, "UPDATE_TIME": NOW, "STATUS": "A", "OPERATOR": "demo"})
    lines += insert(db, "mt_store_goods", rows,
                    ["ID", "MERCHANT_ID", "STORE_ID", "GOODS_ID",
                     "CREATE_TIME", "UPDATE_TIME", "STATUS", "OPERATOR"])

    # 8. 库存单据明细：10 条
    ids = list(range(201, 211))
    lines += delete(db, "mt_stock_item", "ID", ids)
    rows = []
    for i in range(10):
        rows.append({"ID": 201 + i, "STOCK_ID": STOCK_IDS[i % len(STOCK_IDS)],
                     "GOODS_ID": GOODS_IDS[i % len(GOODS_IDS)], "SKU_ID": 0,
                     "NUM": 10 + i * 5,
                     "DESCRIPTION": "盘点入库 %d 件" % (10 + i * 5),
                     "CREATE_TIME": NOW, "UPDATE_TIME": NOW, "OPERATOR": "demo", "STATUS": "A"})
    lines += insert(db, "mt_stock_item", rows,
                    ["ID", "STOCK_ID", "GOODS_ID", "SKU_ID", "NUM", "DESCRIPTION",
                     "CREATE_TIME", "UPDATE_TIME", "OPERATOR", "STATUS"])
    return lines


def main():
    all_lines = ["-- 由 deploy/db/12-gen-extra-data.py 生成，勿手改",
                 "-- 补齐：商户 / 后台账号 / 职务 / 会员地址 / 会员标签 / 卡券分组 / 门店商品 / 库存明细",
                 ""]
    for key in ("shop", "car", "food", "health"):
        all_lines += build(key)
        all_lines.append("")
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(all_lines))
    print("输出: %s (%d 行)" % (OUT, len(all_lines)))

    if "--exec" in sys.argv:
        # 语句里已带库名前缀，整份文件执行一次即可（重复跑是幂等的，只是没必要）
        # stdin 必须给二进制流：传文本流时 subprocess 会按 locale(cp936) 重新编码，
        # 中文被二次编码后长度变长，报 "Data too long for column 'NAME'"
        p = subprocess.run([MYSQL, "-h127.0.0.1", "-uroot", "-p" + PWD,
                            "--default-character-set=utf8mb4"],
                           stdin=open(OUT, "rb"),
                           capture_output=True, text=True, encoding="utf-8", errors="ignore")
        err = [l for l in (p.stderr or "").splitlines() if "Warning" not in l]
        print("导入:", "OK" if not err else "\n".join(err[:10]))


if __name__ == "__main__":
    main()

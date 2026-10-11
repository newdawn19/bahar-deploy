# -*- coding: utf-8 -*-
"""会员端首页「装修」种子数据生成器：四宫格导航 + 通栏广告图 + 前台可领券。

背景（为什么需要这个脚本）
  竞品首页从上到下是：门店条 → 搜索框 → 轮播 → 四宫格 → 通栏广告图 → 优惠券区 → 热门商品。
  我们四套会员端（零售 / 汽车 / 餐饮 / 康养）后三块之前是空的，根因都在数据层：

  1) 四宫格
     components/page/navBar 的数据来自 GET /clientApi/page/home 的 data.navigation，
     后端 SettingServiceImpl#getNavigation 读 mt_setting 里 NAME='navigation' AND TYPE='navigation'
     的 JSON 数组。四个库都没有这条记录 → 恒返回 []，整块不渲染。

  2) 通栏广告图
     组件 components/page/image（单图组）已存在，但首页没渲染、库里也没数据。
     本脚本往 mt_banner 写一条 STORE_ID=0 的广告记录，图片放在
     /static/uploadFiles/ads/ 目录下 —— 会员端首页据此把 banner 列表拆成
     「轮播」与「通栏广告图」两段（不新增后端接口，见 pages/index/index.vue 的注释）。
     餐饮端后端本来就按 position=m_home_ads 单独返回 ads，两种写法都兼容。

  3) 优惠券区
     POST /clientApi/coupon/list 默认只返回 SEND_WAY='front'（前台领取）的券，
     而演示库里的券 SEND_WAY 是 'auto' / '1' → 恒返回空。这里统一改成 'front'。

  4) 四宫格图标
     主题色不能硬编码在图片里，所以按四套主题色对 baharUniapp/static/nav/1..4.png
     做染色，输出到各库的 /static/uploadFiles/nav/ 目录。

幂等性：全部先 DELETE/覆盖再 INSERT/UPDATE，可反复执行。

用法：
    python deploy/db/19-gen-home-diy.py            # 只生成 SQL 与图标
    python deploy/db/19-gen-home-diy.py --exec     # 生成并导入四库
"""
import argparse
import io
import os
import shutil
import struct
import subprocess
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MYSQL = os.environ.get(
    "MYSQL_BIN", r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
)
OUT_SQL = os.path.join(ROOT, "deploy", "db", "19-home-diy-seed.sql")
ASSET_DIR = os.path.join(ROOT, "deploy", "db", "assets", "home-diy")

# 四套矩阵：库名 / 图片落盘根目录（= images.root）/ 品牌主色（= uni.scss 的 $bahar-theme）
# group_name 是各库前台可领券的分组名（下面第 5 步要补建 mt_coupon_group）
THEMES = [
    dict(name="retail", db="bahar-db", oss="D:/oss/bahar-shop", color="#00acac",
         group_name="新客与活动券"),
    dict(name="car", db="bahar-car", oss="D:/oss/bahar-car", color="#373f64",
         group_name="洗车优惠券"),
    dict(name="food", db="bahar-catering", oss="D:/oss/bahar-food", color="#113a28",
         group_name="到店优惠券"),
    dict(name="health", db="bahar-health", oss="D:/oss/bahar-health", color="#7c5cff",
         group_name="康养体验券"),
]

# 四宫格内容（对齐竞品线上文案）。url 必须取自 pages.json 里真实存在的页面：
#   pages/pay/index      买单支付
#   subPages/coupon/list 领券中心（分包页，navigationBarTitleText=领券中心）
#   pages/points/detail  积分（工程里没有独立的"积分兑换"页，取积分页兜底）
#   pages/share/index    邀请有礼
NAV_ITEMS = [
    dict(icon=1, name="买单支付", tips="支付攒积分", url="pages/pay/index", sort=4),
    dict(icon=2, name="领券中心", tips="领券更优惠", url="subPages/coupon/list", sort=3),
    dict(icon=3, name="积分兑换", tips="纯积分换好礼", url="pages/points/detail", sort=2),
    dict(icon=4, name="邀请有礼", tips="好礼相送", url="pages/share/index", sort=1),
]

NAV_ICON_SRC = os.path.join(ROOT, "baharUniapp", "static", "nav")

# 通栏广告图：复用各库已有的 article 活动图，拷进 ads 目录（避免与轮播图重复）
AD_IMAGE_SRC = "/static/uploadFiles/article/101.jpg"
AD_IMAGE_DST = "/static/uploadFiles/ads/home-ad-1.jpg"
AD_BANNER_ID = 201

NOW = "2026-10-11 10:00:00"


# ---------------------------------------------------------------- PNG 工具
def png_read(path):
    """读 8bit/RGBA/非隔行 PNG，返回 (w, h, bytearray RGBA)。"""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG: %s" % path)
    pos, idat = 8, b""
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            w, h, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            if (depth, color, interlace) != (8, 6, 0):
                raise ValueError("只支持 8bit RGBA 非隔行 PNG: %s" % path)
        elif ctype == b"IDAT":
            idat += chunk
    raw = zlib.decompress(idat)
    bpp, stride = 4, w * 4
    out = bytearray()
    prev = bytearray(stride)
    p = 0
    for _ in range(h):
        ftype = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ftype == 1:
                line[x] = (line[x] + a) & 0xFF
            elif ftype == 2:
                line[x] = (line[x] + b) & 0xFF
            elif ftype == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 0xFF
            elif ftype == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        out += line
        prev = line
    return w, h, out


def png_write(path, w, h, rgba):
    """写 8bit RGBA 非隔行 PNG（全部用 filter=0，简单可靠）。"""
    stride = w * 4
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(ctype, payload):
        body = ctype + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(
            ">I", zlib.crc32(body) & 0xFFFFFFFF
        )

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    blob = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "wb") as fp:
        fp.write(blob)


def recolor(src, dst, hex_color):
    """把单色图标整体染成主题色（保留 alpha 抗锯齿），避免硬编码色值。"""
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    w, h, px = png_read(src)
    for i in range(0, len(px), 4):
        if px[i + 3]:
            px[i], px[i + 1], px[i + 2] = rgb
    png_write(dst, w, h, px)


# ---------------------------------------------------------------- 资源落地
def build_assets():
    """生成四套主题色导航图标，并拷到各库的 /static/uploadFiles/ 下。"""
    report = []
    for theme in THEMES:
        nav_out = os.path.join(ASSET_DIR, "nav", theme["name"])
        oss_nav = os.path.join(theme["oss"], "static", "uploadFiles", "nav")
        for item in NAV_ITEMS:
            src = os.path.join(NAV_ICON_SRC, "%d.png" % item["icon"])
            name = "nav-%d.png" % item["icon"]
            recolor(src, os.path.join(nav_out, name), theme["color"])
            if not os.path.isdir(oss_nav):
                os.makedirs(oss_nav)
            shutil.copyfile(os.path.join(nav_out, name), os.path.join(oss_nav, name))

        # 通栏广告图：article 活动图 -> ads 目录
        src_img = os.path.join(theme["oss"], AD_IMAGE_SRC.lstrip("/").replace("/", os.sep))
        dst_dir = os.path.join(theme["oss"], "static", "uploadFiles", "ads")
        dst_img = os.path.join(dst_dir, os.path.basename(AD_IMAGE_DST))
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)
        shutil.copyfile(src_img, dst_img)
        report.append(
            "%s(%s) nav=4 ads=1 <- article/101.jpg" % (theme["name"], theme["color"])
        )
    return report


# ---------------------------------------------------------------- SQL 生成
def nav_json(theme):
    """mt_setting.VALUE：NavigationDto 数组。icon 为相对路径，iconUrl 由后端拼前缀。"""
    parts = []
    for item in NAV_ITEMS:
        parts.append(
            '{"name":"%s","tips":"%s","url":"%s","icon":"%s","sort":%d,"status":"A"}'
            % (
                item["name"],
                item["tips"],
                item["url"],
                "/static/uploadFiles/nav/nav-%d.png" % item["icon"],
                item["sort"],
            )
        )
    return "[%s]" % ",".join(parts)


def build_sql():
    lines = [
        "-- 由 deploy/db/19-gen-home-diy.py 生成，勿手改",
        "-- 会员端首页装修种子数据：四宫格导航 / 通栏广告图 / 前台可领券",
        "-- 幂等：可反复执行；四库（零售 bahar-db、汽车 bahar-car、餐饮 bahar-catering、康养 bahar-health）内容一致",
        "",
    ]
    for theme in THEMES:
        db = "`%s`" % theme["db"]
        lines += [
            "-- ===== %s（主色 %s）=====" % (theme["name"], theme["color"]),
            "",
            "-- 1) 四宫格导航：mt_setting NAME='navigation' AND TYPE='navigation'",
            "DELETE FROM %s.`mt_setting` WHERE `NAME`='navigation' AND `TYPE`='navigation' AND `MERCHANT_ID`=1;" % db,
            "INSERT INTO %s.`mt_setting`" % db,
            "  (`MERCHANT_ID`,`STORE_ID`,`TYPE`,`NAME`,`VALUE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)",
            "VALUES (1,1,'navigation','navigation','%s','会员端首页四宫格导航','%s','%s','demo','A');" % (
                nav_json(theme), NOW, NOW),
            "",
            "-- 2) 通栏广告图：mt_banner 一条 STORE_ID=0（对所有门店可见），图片在 uploadFiles/ads/ 下",
            "DELETE FROM %s.`mt_banner` WHERE `ID`=%d;" % (db, AD_BANNER_ID),
            "INSERT INTO %s.`mt_banner`" % db,
            "  (`ID`,`TITLE`,`position`,`MERCHANT_ID`,`STORE_ID`,`URL`,`IMAGE`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`SORT`,`STATUS`)",
            "VALUES (%d,'会员日狂欢','m_home_ads',1,0,'subPages/coupon/list','%s','首页通栏广告图','%s','%s','demo',1,'A');" % (
                AD_BANNER_ID, AD_IMAGE_DST, NOW, NOW),
            "",
            "-- 3) 优惠券：开放前台领取（coupon/list 默认只返回 SEND_WAY='front'）",
            "UPDATE %s.`mt_coupon` SET `SEND_WAY`='front', `UPDATE_TIME`='%s' WHERE `TYPE`='C' AND `MERCHANT_ID`=1;" % (
                db, NOW),
            "",
            "-- 4) 券面文案：门槛（sellingPoint 由 OUT_RULE 推算）+ 适用范围（会员端取 description）",
            "UPDATE %s.`mt_coupon` SET `OUT_RULE`='100', `UPDATE_TIME`='%s' WHERE `ID`=102 AND `TYPE`='C' AND `MERCHANT_ID`=1;" % (
                db, NOW),
            "UPDATE %s.`mt_coupon` SET `DESCRIPTION`='全场通用', `UPDATE_TIME`='%s' WHERE `ID` IN (1,101,104) AND `TYPE`='C' AND `MERCHANT_ID`=1;" % (
                db, NOW),
            "UPDATE %s.`mt_coupon` SET `DESCRIPTION`='指定商品可用', `UPDATE_TIME`='%s' WHERE `ID` IN (2,102,103) AND `TYPE`='C' AND `MERCHANT_ID`=1;" % (
                db, NOW),
            "",
            "-- 5) 补建卡券分组：mt_coupon.GROUP_ID 指向 1/2，但库里只有 3/201/202，",
            "--    UserCouponServiceImpl#receiveCoupon 会 new 出 null 分组 -> NullPointerException，",
            "--    领券接口直接 500。补上这两条分组，领券才真能入账。",
            "DELETE FROM %s.`mt_coupon_group` WHERE `ID` IN (1,2);" % db,
            "INSERT INTO %s.`mt_coupon_group`" % db,
            "  (`ID`,`MERCHANT_ID`,`STORE_ID`,`NAME`,`MONEY`,`NUM`,`TOTAL`,`DESCRIPTION`,`CREATE_TIME`,`UPDATE_TIME`,`OPERATOR`,`STATUS`)",
            "VALUES (1,1,1,'%s',0.00,0,1000,'会员端前台可领取的卡券分组','%s','%s','demo','A')," % (
                theme["group_name"], NOW, NOW),
            "       (2,1,1,'%s',0.00,0,1000,'会员端前台可领取的卡券分组','%s','%s','demo','A');" % (
                theme["group_name"], NOW, NOW),
            "",
        ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 执行
def mysql_pwd():
    """口令不写进仓库：优先环境变量 DB_PASSWORD，其次读 deploy/.env.local。"""
    pwd = os.environ.get("DB_PASSWORD")
    if pwd:
        return pwd
    env = os.path.join(ROOT, "deploy", ".env.local")
    try:
        for line in io.open(env, encoding="utf-8"):
            if line.strip().startswith("DB_PASSWORD="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def run_sql(path):
    if not os.path.isfile(MYSQL):
        raise SystemExit("找不到 mysql 客户端: %s" % MYSQL)
    pwd = mysql_pwd()
    cmd = [MYSQL, "-uroot", "--default-character-set=utf8mb4"]
    if pwd:
        cmd.append("-p" + pwd)
    with open(path, "rb") as fp:
        proc = subprocess.run(cmd, stdin=fp, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace").replace("\x00", "")
    sys.stdout.write(out)
    if proc.returncode != 0:
        raise SystemExit("导入失败 (exit=%s)" % proc.returncode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exec", action="store_true", help="生成后直接导入四库")
    ap.add_argument("--skip-assets", action="store_true", help="只生成 SQL，不生成图标")
    args = ap.parse_args()

    if not args.skip_assets:
        for line in build_assets():
            print("[assets] " + line)

    sql = build_sql()
    with io.open(OUT_SQL, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(sql)
    print("[sql] %s (%d bytes)" % (OUT_SQL, len(sql.encode("utf-8"))))

    if args.exec:
        run_sql(OUT_SQL)
        print("[exec] 已导入四库")


if __name__ == "__main__":
    main()

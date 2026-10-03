# -*- coding: utf-8 -*-
"""给四套演示库灌图片：生成真实图片文件 + 把相对路径写回数据库。

为什么要写这个脚本：四库所有图片字段 100% 为空（商品主图 0/44、会员头像 0/60、
文章 0/8、轮播 0/6 …），后台一打开就是满屏灰占位方块，客户第一眼就判定"没做完"。

存法（别写错，否则前端显示不出来）：
  - 数据库存**相对路径** `/static/uploadFiles/xxx.jpg`
  - 后端 GoodsServiceImpl 会拼 `images.upload.url`（http://127.0.0.1:8081）再返回
  - 磁盘落 ${images.root} + static/uploadFiles/...，即 D:/oss/<实例>/static/uploadFiles/
  - Spring 的 WebConfig 把 /static/** 映射到 file:D:/oss/<实例>/static/
  所以 /static/uploadFiles/goods/1001.jpg 会被 8081 直接吐出来。

幂等：同一批 ID 每次覆盖写，可重复执行。

用法：
    set DB_PASSWORD=...        （本机 deploy/.env.local 里已有）
    python deploy/db/13-gen-images.py            # 四库全灌
    python deploy/db/13-gen-images.py bahar-db   # 只灌一个库
"""
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
USER = os.environ.get("DB_USER", "root")
PWD = os.environ.get("DB_PASSWORD", "")

# 库 -> (图片落盘根目录, 行业配色, 端口)
INSTANCES = [
    ("bahar-db", "D:/oss/bahar-shop", "retail", 8081),
    ("bahar-car", "D:/oss/bahar-car", "car", 8082),
    ("bahar-catering", "D:/oss/bahar-food", "catering", 8083),
    ("bahar-health", "D:/oss/bahar-health", "health", 8084),
]

# 行业配色：(主色, 副色, 点缀色)
PALETTE = {
    "retail":   ((255, 138, 61), (255, 94, 98), (255, 213, 128)),
    "car":      ((54, 133, 232), (32, 84, 178), (150, 205, 255)),
    "catering": ((232, 74, 66), (176, 42, 46), (255, 190, 140)),
    "health":   ((46, 178, 152), (24, 122, 118), (186, 236, 214)),
}

SLOGAN = {
    "retail": "好物优选 · 会员专享",
    "car": "爱车养护 · 专业服务",
    "catering": "新鲜现做 · 到店即享",
    "health": "康养护理 · 预约到店",
}

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]


def font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def gradient(size, c1, c2, vertical=True):
    """先画一条 2px 的渐变再放大，比逐像素快得多。"""
    w, h = size
    strip_w, strip_h = (2, h) if not vertical else (w, 2)
    strip = Image.new("RGB", (strip_w, strip_h))
    d = ImageDraw.Draw(strip)
    n = strip_h if vertical else strip_w
    for i in range(n):
        t = i / max(1, n - 1)
        c = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        if vertical:
            d.line([(0, i), (w, i)], fill=c)
        else:
            d.line([(i, 0), (i, h)], fill=c)
    return strip.resize(size, Image.BICUBIC)


def center_text(d, box, text, f, fill, stroke=None):
    """在 box=(x0,y0,x1,y1) 中间画文字，超宽自动截断。"""
    x0, y0, x1, y1 = box
    max_w = x1 - x0
    while text and d.textlength(text, font=f) > max_w:
        text = text[:-1]
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = x0 + (max_w - tw) / 2 - bbox[0]
    y = y0 + ((y1 - y0) - th) / 2 - bbox[1]
    if stroke:
        d.text((x, y), text, font=f, fill=fill, stroke_width=3, stroke_fill=stroke)
    else:
        d.text((x, y), text, font=f, fill=fill)


def fit_text(d, text, f, max_w):
    while text and d.textlength(text, font=f) > max_w:
        text = text[:-1]
    return text


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert("RGB").save(path, "JPEG", quality=82, optimize=True)


# ------------------------------------------------------------------ 各类图
def goods_image(path, name, industry, variant=0, size=(600, 600)):
    c1, c2, c3 = PALETTE[industry]
    if variant:  # 相册图换个色调，别三张一模一样
        c1, c2 = c2, c3
    img = gradient(size, (250, 250, 252), (236, 240, 246))
    d = ImageDraw.Draw(img)
    w, h = size
    # 底部色块
    d.rectangle([w * 0.08, h * 0.12, w * 0.92, h * 0.88], fill=c3)
    # 中间圆
    r = w * 0.30
    d.ellipse([w / 2 - r, h * 0.34 - r, w / 2 + r, h * 0.34 + r], fill=c1, outline=c2, width=6)
    short = name[:2] if len(name) >= 2 else name
    f1 = font(int(w * 0.22))
    center_text(d, (w / 2 - r, h * 0.34 - r, w / 2 + r, h * 0.34 + r), short, f1, (255, 255, 255))
    f2 = font(int(w * 0.075))
    t = fit_text(d, name, f2, w * 0.80)
    center_text(d, (w * 0.10, h * 0.70, w * 0.90, h * 0.84), t, f2, (60, 66, 78))
    save(img, path)


def avatar(path, name, industry, size=(200, 200)):
    c1, c2, _ = PALETTE[industry]
    img = gradient(size, c1, c2)
    d = ImageDraw.Draw(img)
    w, h = size
    d.ellipse([w * 0.06, h * 0.06, w * 0.94, h * 0.94], fill=(255, 255, 255))
    d.ellipse([w * 0.10, h * 0.10, w * 0.90, h * 0.90], fill=c1)
    ch = (name or "会")[0]
    f = font(int(w * 0.44))
    center_text(d, (w * 0.10, h * 0.10, w * 0.90, h * 0.90), ch, f, (255, 255, 255))
    save(img, path)


def banner(path, idx, industry, size=(1200, 450)):
    c1, c2, c3 = PALETTE[industry]
    img = gradient(size, c1, c2, vertical=False)
    d = ImageDraw.Draw(img)
    w, h = size
    for i in range(3):  # 几个装饰圆
        r = w * (0.18 + 0.06 * i)
        d.ellipse([w * 0.72 - r, h * 0.5 - r, w * 0.72 + r, h * 0.5 + r], outline=c3, width=8)
    f1 = font(int(h * 0.20))
    d.text((w * 0.07, h * 0.34), SLOGAN[industry], font=f1, fill=(255, 255, 255),
           stroke_width=4, stroke_fill=(0, 0, 0, 0))
    f2 = font(int(h * 0.10))
    d.text((w * 0.07, h * 0.62), "第 %d 张轮播图" % (idx + 1), font=f2, fill=(255, 255, 255))
    save(img, path)


def article_img(path, title, industry, size=(800, 420)):
    c1, c2, c3 = PALETTE[industry]
    img = gradient(size, c2, c1)
    d = ImageDraw.Draw(img)
    w, h = size
    d.rectangle([w * 0.06, h * 0.16, w * 0.94, h * 0.84], outline=c3, width=6)
    f = font(int(h * 0.18))
    t = fit_text(d, title or "公告", f, w * 0.78)
    center_text(d, (w * 0.10, h * 0.30, w * 0.90, h * 0.62), t, f, (255, 255, 255),
                stroke=(0, 0, 0, 0))
    f2 = font(int(h * 0.09))
    center_text(d, (w * 0.10, h * 0.66, w * 0.90, h * 0.80), SLOGAN[industry], f2, c3)
    save(img, path)


def store_img(path, name, industry, size=(800, 600)):
    c1, c2, c3 = PALETTE[industry]
    img = gradient(size, (245, 247, 250), (222, 230, 240))
    d = ImageDraw.Draw(img)
    w, h = size
    d.rectangle([w * 0.08, h * 0.18, w * 0.92, h * 0.82], fill=c3)
    d.rectangle([w * 0.08, h * 0.62, w * 0.92, h * 0.82], fill=c1)
    f = font(int(h * 0.16))
    t = fit_text(d, name or "门店", f, w * 0.74)
    center_text(d, (w * 0.10, h * 0.66, w * 0.90, h * 0.80), t, f, (255, 255, 255))
    f2 = font(int(h * 0.13))
    center_text(d, (w * 0.10, h * 0.28, w * 0.90, h * 0.52), "门店形象", f2, c2)
    save(img, path)


def coupon_img(path, name, industry, size=(600, 300)):
    c1, c2, c3 = PALETTE[industry]
    img = gradient(size, c1, c2, vertical=False)
    d = ImageDraw.Draw(img)
    w, h = size
    d.line([(w * 0.62, 0), (w * 0.62, h)], fill=(255, 255, 255), width=6)
    f = font(int(h * 0.26))
    center_text(d, (w * 0.04, h * 0.20, w * 0.58, h * 0.62), "券", f, (255, 255, 255))
    f2 = font(int(h * 0.13))
    t = fit_text(d, name or "优惠券", f2, w * 0.32)
    center_text(d, (w * 0.66, h * 0.30, w * 0.96, h * 0.70), t, f2, (255, 255, 255))
    save(img, path)


def cate_img(path, name, industry, size=(240, 240)):
    c1, c2, c3 = PALETTE[industry]
    img = Image.new("RGB", size, c3)
    d = ImageDraw.Draw(img)
    w, h = size
    d.ellipse([w * 0.12, h * 0.12, w * 0.88, h * 0.88], fill=c1)
    f = font(int(w * 0.30))
    t = fit_text(d, (name or "分类")[:2], f, w * 0.62)
    center_text(d, (w * 0.12, h * 0.12, w * 0.88, h * 0.88), t, f, (255, 255, 255))
    save(img, path)


def book_img(path, name, industry, size=(600, 400)):
    """预约项目封面。mt_book 只有汽车/餐饮/康养三库有数据。"""
    c1, c2, c3 = PALETTE[industry]
    img = gradient(size, c2, c1, vertical=False)
    d = ImageDraw.Draw(img)
    w, h = size
    d.rectangle([w * 0.06, h * 0.14, w * 0.94, h * 0.86], outline=c3, width=5)
    # 左上角一个"时钟"符号，暗示预约
    r = h * 0.16
    cx, cy = w * 0.20, h * 0.30
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c3, width=5)
    d.line([(cx, cy), (cx, cy - r * 0.55)], fill=c3, width=4)
    d.line([(cx, cy), (cx + r * 0.45, cy + r * 0.25)], fill=c3, width=4)
    f = font(int(h * 0.20))
    t = fit_text(d, name or "预约项目", f, w * 0.78)
    center_text(d, (w * 0.10, h * 0.52, w * 0.90, h * 0.76), t, f, (255, 255, 255),
                stroke=(0, 0, 0, 0))
    save(img, path)


def merchant_img(path, name, industry, size=(400, 400)):
    c1, c2, _ = PALETTE[industry]
    img = gradient(size, c2, c1)
    d = ImageDraw.Draw(img)
    w, h = size
    f = font(int(w * 0.22))
    t = fit_text(d, (name or "商户")[:4], f, w * 0.78)
    center_text(d, (w * 0.10, h * 0.35, w * 0.90, h * 0.65), t, f, (255, 255, 255),
                stroke=(0, 0, 0, 0))
    save(img, path)


# ------------------------------------------------------------------ 数据库
def q(db, sql):
    cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p", "-N", "-B",
           "--default-character-set=utf8mb4", "-D", db, "-e", sql]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [SQL 失败] %s" % p.stderr.strip()[:200])
        return []
    return [l.split("\t") for l in p.stdout.splitlines() if l.strip()]


def run_sql_file(db, path):
    with open(path, encoding="utf-8") as f:
        sql = f.read()
    cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p",
           "--default-character-set=utf8mb4", "-D", db]
    p = subprocess.run(cmd, input=sql, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [执行失败] %s" % p.stderr.strip()[:300])
        return False
    return True


def has_table(db, name):
    rows = q(db, "SELECT COUNT(*) FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='%s'" % (db, name))
    return bool(rows) and rows[0][0] == "1"


def esc(s):
    return (s or "").replace("\\", "\\\\").replace("'", "''")


def main():
    random.seed(20261003)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    total = 0
    for db, root, industry, port in INSTANCES:
        if only and db != only:
            continue
        print("=" * 60)
        print("%s  (%s)  ->  %s" % (db, industry, root))
        print("=" * 60)
        stmts = []

        goods = q(db, "SELECT ID,NAME FROM mt_goods WHERE STATUS='A'")
        for gid, name in goods:
            rel = "/static/uploadFiles/goods/%s.jpg" % gid
            goods_image(root + "/static/uploadFiles/goods/%s.jpg" % gid, name, industry)
            total += 1
            albums = []
            for v in (1, 2):
                r2 = "/static/uploadFiles/goods/%s_%d.jpg" % (gid, v)
                goods_image(root + "/static/uploadFiles/goods/%s_%d.jpg" % (gid, v),
                            name, industry, variant=v)
                albums.append(r2)
                total += 1
            stmts.append("UPDATE mt_goods SET LOGO='%s', IMAGES='%s' WHERE ID=%s;"
                         % (rel, ",".join([rel] + albums), gid))
        print("  商品 %d 张（含相册）" % len(goods))

        users = q(db, "SELECT ID,NAME FROM mt_user WHERE STATUS='A'")
        for uid, name in users:
            rel = "/static/uploadFiles/avatar/%s.jpg" % uid
            avatar(root + "/static/uploadFiles/avatar/%s.jpg" % uid, name, industry)
            stmts.append("UPDATE mt_user SET AVATAR='%s' WHERE ID=%s;" % (rel, uid))
            total += 1
        print("  会员头像 %d 张" % len(users))

        arts = q(db, "SELECT ID,TITLE FROM mt_article")
        for aid, title in arts:
            rel = "/static/uploadFiles/article/%s.jpg" % aid
            article_img(root + "/static/uploadFiles/article/%s.jpg" % aid, title, industry)
            stmts.append("UPDATE mt_article SET IMAGE='%s' WHERE ID=%s;" % (rel, aid))
            total += 1
        print("  文章封面 %d 张" % len(arts))

        bns = q(db, "SELECT ID FROM mt_banner")
        for i, (bid,) in enumerate(bns):
            rel = "/static/uploadFiles/banner/%s.jpg" % bid
            banner(root + "/static/uploadFiles/banner/%s.jpg" % bid, i, industry)
            stmts.append("UPDATE mt_banner SET IMAGE='%s' WHERE ID=%s;" % (rel, bid))
            total += 1
        print("  轮播图 %d 张" % len(bns))

        stores = q(db, "SELECT ID,NAME FROM mt_store")
        for sid, sname in stores:
            rel = "/static/uploadFiles/store/%s.jpg" % sid
            store_img(root + "/static/uploadFiles/store/%s.jpg" % sid, sname, industry)
            stmts.append("UPDATE mt_store SET LOGO='%s' WHERE ID=%s;" % (rel, sid))
            total += 1
        print("  门店图 %d 张" % len(stores))

        cps = q(db, "SELECT ID,NAME FROM mt_coupon")
        for cid, cname in cps:
            rel = "/static/uploadFiles/coupon/%s.jpg" % cid
            coupon_img(root + "/static/uploadFiles/coupon/%s.jpg" % cid, cname, industry)
            stmts.append("UPDATE mt_coupon SET IMAGE='%s' WHERE ID=%s;" % (rel, cid))
            total += 1
        print("  卡券图 %d 张" % len(cps))

        cates = q(db, "SELECT ID,NAME FROM mt_goods_cate")
        for cid, cname in cates:
            rel = "/static/uploadFiles/cate/%s.jpg" % cid
            cate_img(root + "/static/uploadFiles/cate/%s.jpg" % cid, cname, industry)
            stmts.append("UPDATE mt_goods_cate SET LOGO='%s' WHERE ID=%s;" % (rel, cid))
            total += 1
        print("  分类图 %d 张" % len(cates))

        mers = q(db, "SELECT ID,NAME FROM mt_merchant")
        for mid, mname in mers:
            rel = "/static/uploadFiles/merchant/%s.jpg" % mid
            merchant_img(root + "/static/uploadFiles/merchant/%s.jpg" % mid, mname, industry)
            stmts.append("UPDATE mt_merchant SET LOGO='%s' WHERE ID=%s;" % (rel, mid))
            total += 1
        print("  商户图 %d 张" % len(mers))

        if has_table(db, "mt_book"):
            books = q(db, "SELECT ID,name FROM mt_book")
            for bid, bname in books:
                rel = "/static/uploadFiles/book/%s.jpg" % bid
                book_img(root + "/static/uploadFiles/book/%s.jpg" % bid, bname, industry)
                stmts.append("UPDATE mt_book SET logo='%s' WHERE ID=%s;" % (rel, bid))
                total += 1
            print("  预约项目封面 %d 张" % len(books))

        out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "tmp", "13-images-%s.sql" % db)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write("USE `%s`;\n" % db)
            f.write("\n".join(stmts) + "\n")
        print("  写库语句 %d 条 -> %s" % (len(stmts), os.path.basename(out)))
        if run_sql_file(db, out):
            print("  [OK] 已写回数据库")
    print("=" * 60)
    print("生成图片文件共 %d 个" % total)


if __name__ == "__main__":
    main()

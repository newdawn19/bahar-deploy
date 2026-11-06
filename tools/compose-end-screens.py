# -*- coding: utf-8 -*-
"""把交付截图按「端」合成四张长图。

素材来自 deliverables/：
  - 客户交付/01-界面截图/{后台Admin,会员端,收银端}  49 张正式运行截图
  - 根目录下 h5-*.png                              22 张 H5 / 小程序适配截图

用法：
  python deploy/tools/compose-end-screens.py
输出：
  deliverables/四端界面合成图/*.png  （每端一张）
"""
import re
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "deliverables" / "客户交付" / "01-界面截图"
DELIV = ROOT / "deliverables"
OUT = DELIV / "四端界面合成图"

FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_BD = "C:/Windows/Fonts/msyhbd.ttc"

BG = "#F4F6F8"
CARD = "#FFFFFF"
BORDER = "#E1E7EB"
SHADOW = "#DCE2E7"
TEXT = "#1B2A33"
MUTED = "#61727D"

CANVAS_W = 2000
MARGIN = 50
HEADER_H = 196
FOOTER_H = 86
PAD = 12
LABEL_H = 58


def pngs(d):
    return sorted(d.glob("*.png"), key=lambda p: p.name)


def h5pngs():
    return sorted(DELIV.glob("h5-*.png"), key=lambda p: p.name)


# 端配置：输出名 / 标题 / 副标题 / 主色 / 每行张数 / 素材
ENDS = [
    dict(file="01-收银端-Electron-POS.png",
         title="收银端 · Electron POS",
         sub="8 张真实运行截图｜登录 / 收银台 / 订单 / 会员 / 充值 / 核销 / 总览 / 设置",
         color="#2E6BE6", cols=2, files=pngs(SHOTS / "收银端"),
         source="客户交付/01-界面截图/收银端"),
    dict(file="02-用户App端-会员端.png",
         title="用户 App 端 · 会员中心",
         sub="20 张真实运行截图｜首页 / 微店 / 商品 / 会员 / 卡券 / 余额 / 积分 / 订单 / 分销 / 商家管理 / 数据统计",
         color="#176C68", cols=5, files=pngs(SHOTS / "会员端"),
         source="客户交付/01-界面截图/会员端"),
    dict(file="03-小程序端-H5适配.png",
         title="小程序端 · H5 适配",
         sub="22 张 750rpx 基准截图｜四行业首页改版 / 会员中心 / 商户端工作台（含 goods 与断点对照）",
         color="#1A9E5C", cols=5, files=h5pngs(),
         source="deliverables/h5-*.png"),
    dict(file="04-后台管理端-Admin.png",
         title="后台管理端 · Admin",
         sub="21 张真实运行截图｜登录 / 看板 / 会员 / 商品 / 库存 / 卡券 / 订单 / 门店 / 账号 / 日志",
         color="#D97706", cols=2, files=pngs(SHOTS / "后台Admin"),
         source="客户交付/01-界面截图/后台Admin"),
]


def font(size, bold=False):
    return ImageFont.truetype(FONT_BD if bold else FONT, size)


def label_of(path, idx):
    stem = path.stem
    m = re.match(r"^(\d{2})[-_](.+)$", stem)
    if m:
        return m.group(1), m.group(2)
    return "%02d" % (idx + 1), stem.replace("h5-", "", 1) if stem.startswith("h5-") else stem


def fit_image(path, box_w):
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    if w > box_w:
        nh = max(1, round(h * box_w / w))
        im = im.resize((box_w, nh), Image.LANCZOS)
    return im


def text_w(draw, s, f):
    return draw.textbbox((0, 0), s, font=f)[2]


def compose(cfg):
    files = cfg["files"]
    cols = cfg["cols"]
    gap = 24 if cols >= 4 else 30
    card_w = (CANVAS_W - 2 * MARGIN - (cols - 1) * gap) // cols
    img_w = card_w - 2 * PAD

    # 预排版：算出每张图的缩放高度、卡片高度、行高
    items = []
    for i, p in enumerate(files):
        num, name = label_of(p, i)
        im = fit_image(p, img_w)
        card_h = PAD + im.height + LABEL_H + PAD
        items.append(dict(path=p, num=num, name=name, im=im, h=card_h))
    rows = [items[i:i + cols] for i in range(0, len(items), cols)]
    row_heights = [max(it["h"] for it in row) for row in rows]

    total_h = HEADER_H + sum(row_heights) + gap * (len(rows) - 1) + FOOTER_H + MARGIN
    canvas = Image.new("RGB", (CANVAS_W, total_h), BG)
    d = ImageDraw.Draw(canvas)

    # 顶部：色条 + 标题 + 副标题 + 右上角计数
    d.rectangle((0, 0, CANVAS_W, 9), fill=cfg["color"])
    d.rounded_rectangle((MARGIN, 52, MARGIN + 9, 122), radius=4, fill=cfg["color"])
    d.text((MARGIN + 30, 48), cfg["title"], font=font(62, True), fill=TEXT)
    d.text((MARGIN + 32, 132), cfg["sub"], font=font(24), fill=MUTED)
    badge = "共 %d 张" % len(files)
    bf = font(28, True)
    bw = text_w(d, badge, bf)
    d.rounded_rectangle((CANVAS_W - MARGIN - bw - 44, 56, CANVAS_W - MARGIN, 112),
                        radius=12, fill=cfg["color"])
    d.text((CANVAS_W - MARGIN - bw - 22, 68), badge, font=bf, fill="#FFFFFF")
    d.line((MARGIN, HEADER_H - 18, CANVAS_W - MARGIN, HEADER_H - 18), fill="#DFE5EA", width=2)

    y = HEADER_H
    for row, rh in zip(rows, row_heights):
        # 最后一行不足 cols 张时整体居中，避免右侧留一大块空白
        row_w = len(row) * card_w + (len(row) - 1) * gap
        x0 = MARGIN if len(row) == cols else (CANVAS_W - row_w) // 2
        for c, it in enumerate(row):
            x = x0 + c * (card_w + gap)
            # 阴影 + 卡片
            d.rounded_rectangle((x + 3, y + 5, x + card_w + 3, y + it["h"] + 5),
                                radius=14, fill=SHADOW)
            d.rounded_rectangle((x, y, x + card_w, y + it["h"]),
                                radius=14, fill=CARD, outline=BORDER, width=2)
            canvas.paste(it["im"], (x + PAD, y + PAD))
            d.line((x + PAD, y + PAD + it["im"].height + 6,
                    x + card_w - PAD, y + PAD + it["im"].height + 6),
                   fill="#EEF1F3", width=2)
            ly = y + PAD + it["im"].height + 18
            nf = font(21, True)
            d.text((x + PAD + 4, ly), it["num"], font=nf, fill=cfg["color"])
            nw = text_w(d, it["num"], nf)
            name = it["name"]
            tf = font(16 if len(name) > 18 else (18 if len(name) > 13 else 22))
            # 名称过长则截断，避免溢出卡片
            max_w = card_w - 2 * PAD - nw - 20
            while name and text_w(d, name, tf) > max_w:
                name = name[:-1]
            if name != it["name"]:
                name = name.rstrip("- ") + "…"
            d.text((x + PAD + nw + 16, ly - 1), name, font=tf, fill=TEXT)
        y += rh + gap

    # 页脚
    fy = total_h - FOOTER_H + 16
    d.line((MARGIN, fy - 14, CANVAS_W - MARGIN, fy - 14), fill="#DFE5EA", width=2)
    left = "素材：deliverables/" + cfg["source"]
    right = "bahar 四行业矩阵演示站 · 基于开源产品改造，仅作技术能力证明 · %s" % date.today().isoformat()
    d.text((MARGIN, fy), left, font=font(21), fill=MUTED)
    rw = text_w(d, right, font(21))
    d.text((CANVAS_W - MARGIN - rw, fy), right, font=font(21), fill=MUTED)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / cfg["file"]
    canvas.save(out, "PNG", optimize=True)
    print("  [OK] %-34s %d 张  %d×%d  %.1f MB" %
          (cfg["file"], len(files), CANVAS_W, total_h, out.stat().st_size / 1024 / 1024))
    canvas.close()
    for it in items:
        it["im"].close()
    return out


def main():
    print("输出目录：%s" % OUT)
    for cfg in ENDS:
        if not cfg["files"]:
            print("  [FAIL] %s 没找到素材" % cfg["title"])
            return 1
        compose(cfg)
    print("完成：4 张合成图")
    return 0


if __name__ == "__main__":
    sys.exit(main())

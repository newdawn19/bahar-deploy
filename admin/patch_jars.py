# -*- coding: utf-8 -*-
"""
把 deploy/admin 的后台 SPA 直接注入已打好的 fat jar，跳过完整重新打包。

用途：只改了前端静态资源时，不必再跑一遍 mvn package（每套约 2 分钟）。
做法：重写 zip —— 原样拷贝除 BOOT-INF/classes/static/admin/** 之外的全部条目，
      再把最新 admin 资源（含按实例生成的 config.js）写回去。

用法: python patch_jars.py
"""
import json
import os
import shutil
import zipfile

SRC = r"D:\git-double\bahar\deploy\admin"
RUNTIME = r"D:\git-double\bahar\deploy\runtime"

# jar 名 -> (实例标题, 主题色)。四套共用一份 Admin 源码，靠这里注入的配置区分。
INSTANCES = [
    ("bahar-shop.jar", "bahar 会员营销管理系统 · 通用零售", {
        "primary": "#409EFF", "sidebar": "#001529",
        "g1": "#1d3a5c", "g2": "#2b5876", "g3": "#409EFF",
    }),
    ("bahar-car.jar", "bahar 会员营销管理系统 · 汽车美容", {
        "primary": "#0E9F6E", "sidebar": "#0B3B2E",
        "g1": "#0B3B2E", "g2": "#10624A", "g3": "#0E9F6E",
    }),
    ("bahar-food.jar", "bahar 会员营销管理系统 · 餐饮", {
        "primary": "#E8722D", "sidebar": "#4A2C17",
        "g1": "#4A2C17", "g2": "#7A3F1D", "g3": "#E8722D",
    }),
    ("bahar-health.jar", "bahar 会员营销管理系统 · 康养美业", {
        "primary": "#7C5CE0", "sidebar": "#261B45",
        "g1": "#261B45", "g2": "#4B3A78", "g3": "#7C5CE0",
    }),
]

PREFIX = "BOOT-INF/classes/static/admin/"
IGNORE = {"sync.py", "patch_jars.py"}

CONFIG_TPL = """/* 实例配置 —— 由 deploy/admin/patch_jars.py 生成，请勿手工修改 */
window.__BAHAR_ADMIN_TITLE__ = '%s';
window.__BAHAR_ADMIN_BASE__ = '';
window.__BAHAR_ADMIN_THEME__ = %s;
"""


def collect_admin_files():
    """[(相对路径, 绝对路径)]"""
    out = []
    for root, dirs, files in os.walk(SRC):
        for f in files:
            if f in IGNORE:
                continue
            rel = os.path.relpath(os.path.join(root, f), SRC).replace("\\", "/")
            out.append((rel, os.path.join(root, f)))
    return out


def patch(jar_path, title, theme):
    tmp = jar_path + ".tmp"
    files = collect_admin_files()
    cfg = CONFIG_TPL % (title, json.dumps(theme, ensure_ascii=False))

    with zipfile.ZipFile(jar_path, "r") as zin, \
            zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zout:

        # 1) 拷贝原有条目（跳过旧的 admin 目录，含目录条目）
        skipped = 0
        for item in zin.infolist():
            if item.filename.startswith(PREFIX):
                skipped += 1
                continue
            zout.writestr(item, zin.read(item.filename))

        # 2) 写入最新 admin 资源
        for rel, abs_path in files:
            if rel == "config.js":
                continue  # 由实例标题另行生成
            with open(abs_path, "rb") as fp:
                zout.writestr(PREFIX + rel, fp.read())

        # 3) 实例配置
        zout.writestr(PREFIX + "config.js", cfg.encode("utf-8"))

        added = len([r for r, _ in files if r != "config.js"]) + 1

    shutil.move(tmp, jar_path)
    print("OK  %-18s  替换 %d 个旧条目, 写入 %d 个文件" % (
        os.path.basename(jar_path), skipped, added))


def main():
    for jar, title, theme in INSTANCES:
        p = os.path.join(RUNTIME, jar)
        if not os.path.isfile(p):
            print("!! 不存在，跳过:", p)
            continue
        patch(p, title, theme)


if __name__ == "__main__":
    main()

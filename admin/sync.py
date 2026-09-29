# -*- coding: utf-8 -*-
"""把 deploy/admin 的后台 SPA 同步到 4 个工程的 static/admin 下"""
import os, shutil, sys

SRC = r"D:\git-double\bahar\deploy\admin"
INSTANCES = [
    # (目标 static 根, 实例标题)
    (r"D:\git-double\bahar\bahar\bahar-application\src\main\resources\static", "bahar 会员营销管理系统 · 通用零售"),
    (r"D:\git-double\bahar\baharCar\backend\bahar-application\src\main\resources\static", "bahar 会员营销管理系统 · 汽车美容"),
    (r"D:\git-double\bahar\baharCatering\baharBackend\bahar-application\src\main\resources\static", "bahar 会员营销管理系统 · 餐饮"),
    (r"D:\git-double\bahar\baharHealth\backend-api\bahar-application\src\main\resources\static", "bahar 会员营销管理系统 · 康养美业"),
]

CONFIG_TPL = """/* 实例配置 —— 由 deploy/admin/sync.py 生成，请勿手工修改 */
window.__BAHAR_ADMIN_TITLE__ = '%s';
window.__BAHAR_ADMIN_BASE__ = '';
"""

IGNORE = {"sync.py"}

def main():
    for static_root, title in INSTANCES:
        dst = os.path.join(static_root, "admin")
        if not os.path.isdir(static_root):
            print("!! 跳过(目录不存在):", static_root); continue
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        os.makedirs(dst)
        # 拷贝资源
        for root, dirs, files in os.walk(SRC):
            rel = os.path.relpath(root, SRC)
            if rel == ".":
                target = dst
            else:
                target = os.path.join(dst, rel)
            os.makedirs(target, exist_ok=True)
            for f in files:
                if f in IGNORE: continue
                shutil.copy2(os.path.join(root, f), os.path.join(target, f))
        # 写入实例配置
        with open(os.path.join(dst, "config.js"), "w", encoding="utf-8") as fp:
            fp.write(CONFIG_TPL % title)
        n = sum(len(fs) for _, _, fs in os.walk(dst))
        print("OK  %-70s  %s  (%d files)" % (title, dst, n))

if __name__ == "__main__":
    main()

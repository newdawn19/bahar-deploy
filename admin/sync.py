# -*- coding: utf-8 -*-
"""把 deploy/admin 的后台 SPA 同步到 4 个工程的 src/main/resources/static/admin 下。

为什么必须有这一步：
  patch_jars.py 只把 Admin 注入打好的 jar（给 start-all.sh 用）；
  但用 IDEA 直接跑工程时，classpath 走的是 target/classes，而它由
  src/main/resources 复制而来。不同步的话 IDEA 里加载的是旧版 Admin，
  表现为图标不显示、主题色不生效 —— 与 jar 里跑出来的效果不一致。

  所以：改完 deploy/admin 之后跑一次本脚本，再让 IDEA 重新运行即可。
  用法： python deploy/admin/sync.py
"""
import json
import os
import shutil

SRC = r"D:\git-double\bahar\deploy\admin"

# 实例主题色（与 patch_jars.py 保持一致）
THEMES = {
    "零售": {"primary": "#409EFF", "sidebar": "#001529",
            "g1": "#1d3a5c", "g2": "#2b5876", "g3": "#409EFF"},
    "汽车": {"primary": "#0E9F6E", "sidebar": "#0B3B2E",
            "g1": "#0B3B2E", "g2": "#10624A", "g3": "#0E9F6E"},
    "餐饮": {"primary": "#E8722D", "sidebar": "#4A2C17",
            "g1": "#4A2C17", "g2": "#7A3F1D", "g3": "#E8722D"},
    "康养": {"primary": "#7C5CE0", "sidebar": "#261B45",
            "g1": "#261B45", "g2": "#4B3A78", "g3": "#7C5CE0"},
}

# (bahar-application 模块根, 行业)
# 每套同步两处：
#   1) src/main/resources/static —— 源码，供打包与后续 build 复制
#   2) target/classes/static     —— IDEA 直接运行时 classpath 实际加载的就是它，
#      只同步 src 的话 IDEA 里还是旧版 Admin（图标不显示 / 主题色不生效），
#      必须等一次 rebuild 才会更新。这里直接写进去，IDEA 重启即可见。
INSTANCES = [
    (r"D:\git-double\bahar\bahar\bahar-application", "零售"),
    (r"D:\git-double\bahar\baharCar\backend\bahar-application", "汽车"),
    (r"D:\git-double\bahar\baharCatering\baharBackend\bahar-application", "餐饮"),
    (r"D:\git-double\bahar\baharHealth\backend-api\bahar-application", "康养"),
]

CONFIG_TPL = """/* 实例配置 —— 由 deploy/admin/sync.py 生成，请勿手工修改 */
window.__BAHAR_ADMIN_TITLE__ = '%s';
window.__BAHAR_ADMIN_BASE__ = '';
window.__BAHAR_ADMIN_THEME__ = %s;
"""

# 只同步前端资源，工具脚本不进各工程源码
IGNORE = {"sync.py", "patch_jars.py", "make_inline_font.py"}


def copy_admin(dst, industry):
    # 注意：这里原来用 shutil.rmtree(dst) 先清空再拷，但一次性删掉整个 admin 目录
    # （60+ 个文件）会触发批量删除保护而中断，导致同步根本跑不完。
    # 改成「覆盖式复制」——内容一致就跳过，不一致才写；陈旧文件只报告不删除，
    # 效果等价但不会触发批量删除。
    os.makedirs(dst, exist_ok=True)
    stale = []

    for root, dirs, files in os.walk(SRC):
        rel = os.path.relpath(root, SRC)
        target = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(target, exist_ok=True)
        for f in files:
            if f in IGNORE:
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(target, f))

    src_names = set()
    for root, dirs, files in os.walk(SRC):
        for f in files:
            if f not in IGNORE:
                src_names.add(os.path.relpath(os.path.join(root, f), SRC))
    src_names.add("config.js")
    for root, dirs, files in os.walk(dst):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), dst)
            if rel not in src_names:
                stale.append(rel)
    if stale:
        print("    陈旧文件(未删除，请手工确认):", stale)

    title = "bahar 会员营销管理系统 · %s" % (
        {"零售": "通用零售", "汽车": "汽车美容", "餐饮": "餐饮", "康养": "康养美业"}[industry])
    with open(os.path.join(dst, "config.js"), "w", encoding="utf-8") as fp:
        fp.write(CONFIG_TPL % (title, json.dumps(THEMES[industry], ensure_ascii=False)))
    return sum(len(fs) for _, _, fs in os.walk(dst))


def main():
    for app_root, industry in INSTANCES:
        if not os.path.isdir(app_root):
            print("!! 跳过(目录不存在):", app_root)
            continue
        targets = [os.path.join(app_root, "src", "main", "resources", "static", "admin")]
        # target/classes 只在工程 build 过之后才有，没有就跳过（下次 rebuild 会带上）
        tc = os.path.join(app_root, "target", "classes", "static", "admin")
        if os.path.isdir(os.path.dirname(tc)):
            targets.append(tc)

        for dst in targets:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            n = copy_admin(dst, industry)
            kind = "src" if "src" in dst.replace("\\", "/") else "target"
            print("OK  %-6s %-8s -> %s (%d files)" % (industry, kind, dst, n))


if __name__ == "__main__":
    main()

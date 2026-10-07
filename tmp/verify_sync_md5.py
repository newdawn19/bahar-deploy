# -*- coding: utf-8 -*-
"""校验 4 套工程的 admin 静态资源与 deploy/admin 源是否字节一致，并检查关联字段关键字。"""
import hashlib
import os
import sys

SRC = r"D:\git-double\bahar\deploy\admin"

ROOTS = [
    ("零售", r"D:\git-double\bahar\bahar\bahar-application"),
    ("汽车", r"D:\git-double\bahar\baharCar\backend\bahar-application"),
    ("餐饮", r"D:\git-double\bahar\baharCatering\baharBackend\bahar-application"),
    ("康养", r"D:\git-double\bahar\baharHealth\backend-api\bahar-application"),
]

FILES = [
    "index.html",
    "js/api.js",
    "js/app.js",
    "js/crud.js",
    "js/modules.js",
    "js/views.js",
]

# (文件, 必须包含的关键字)
KEYWORDS = {
    "js/modules.js": ["所属商户", "所属门店", "门店数", "员工数", "关联会员",
                      "storeCount", "staffCount", "merchantName", "userNo"],
    "js/crud.js": ["=== 'expr'", "c.expr", "s.row.", "c.align"],
}

BAD = 0


def md5(path):
    """返回文件 md5；不存在返回 None。"""
    try:
        with open(path, "rb") as fp:
            return hashlib.md5(fp.read()).hexdigest()
    except OSError:
        return None


def main():
    global BAD
    base = {}
    for rel in FILES:
        base[rel] = md5(os.path.join(SRC, rel))

    print("=== md5 一致性（源 deploy/admin） ===")
    for rel in FILES:
        print("%-16s %s" % (rel, base[rel]))
    print()

    for rel in FILES:
        print("--- %s ---" % rel)
        for ind, root in ROOTS:
            for kind, mid in (("src", "src/main/resources"),
                              ("target", "target/classes")):
                p = os.path.join(root, *mid.split("/"), "static", "admin", *rel.split("/"))
                v = md5(p)
                ok = (v == base[rel])
                if not ok:
                    BAD += 1
                print("  %-4s %-6s %s %s" % (ind, kind, v, "OK" if ok else "*** DIFF/MISSING ***"))
        print()

    print("=== 关键字检查 ===")
    for rel, kws in KEYWORDS.items():
        for ind, root in ROOTS:
            for kind, mid in (("src", "src/main/resources"),
                              ("target", "target/classes")):
                p = os.path.join(root, *mid.split("/"), "static", "admin", *rel.split("/"))
                try:
                    with open(p, "r", encoding="utf-8") as fp:
                        txt = fp.read()
                except OSError:
                    print("  %-4s %-6s %-16s MISSING" % (ind, kind, rel))
                    BAD += 1
                    continue
                miss = [k for k in kws if k not in txt]
                if miss:
                    BAD += 1
                print("  %-4s %-6s %-16s %s" % (
                    ind, kind, rel,
                    "全部命中" if not miss else "缺失: %s" % ",".join(miss)))

    print()
    print("RESULT:", "PASS" if BAD == 0 else "FAIL(%d)" % BAD)
    return 0 if BAD == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""修会员重名：四库里 ID 1-5 与 101-105 是同一批姓名，导致姓名登录必失败。

为什么必须修：MemberServiceImpl.queryMemberByName() 只在查到**恰好 1 条**时才返回会员，
           查到 2 条直接返回 null，于是 ClientSignController 的"账号密码登录"永远报
           "账号或密码有误"。实测手机号能登录、姓名不能登录，根因就在这。
           演示现场销售多半会输姓名，一输就报错，等于会员端登录是坏的。

修法：保留 ID 较小那个的原名，其余从备用姓名池里取一个未占用的名字改掉。
      幂等：跑完再查无重复，重复执行不会再改。

用法: set DB_PASSWORD=... && python deploy/db/16-fix-dup-member-names.py
"""
import os
import subprocess
import sys

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
USER = os.environ.get("DB_USER", "root")
PWD = os.environ.get("DB_PASSWORD", "")

DBS = ["bahar-db", "bahar-car", "bahar-catering", "bahar-health"]

# 备用姓名池：足够多，取用前会先检查库里是否已占用
POOL = ["赵磊", "钱明", "孙丽", "周涛", "吴静", "徐强", "马丽", "朱峰", "胡斌", "郭敏",
        "何超", "高倩", "林峰", "罗雪", "郑凯", "梁爽", "谢军", "宋佳", "唐宇", "许诺",
        "韩梅", "冯刚", "邓超", "曹颖", "彭勇", "曾丽", "肖华", "田甜", "董明", "潘婷"]


def q(db, sql):
    cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p", "-N", "-B",
           "--default-character-set=utf8mb4", "-D", db, "-e", sql]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [SQL 失败] %s" % p.stderr.strip()[:200])
        return []
    return [l.split("\t") for l in p.stdout.splitlines() if l.strip()]


def exec_sql(db, sql):
    cmd = [MYSQL, "-u" + USER, ("-p" + PWD) if PWD else "-p",
           "--default-character-set=utf8mb4", "-D", db]
    p = subprocess.run(cmd, input=sql, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [执行失败] %s" % p.stderr.strip()[:300])
        return False
    return True


def main():
    ok = True
    for db in DBS:
        print("=" * 60)
        print(db)
        print("=" * 60)
        dups = q(db, "SELECT NAME, COUNT(*) FROM mt_user WHERE STATUS='A' "
                     "GROUP BY NAME HAVING COUNT(*)>1")
        if not dups:
            print("  无重名，跳过")
            continue
        used = set(r[0] for r in q(db, "SELECT DISTINCT NAME FROM mt_user"))
        pool = [n for n in POOL if n not in used]
        stmts = []
        pi = 0
        for name, cnt in dups:
            # 保留 ID 最小的那个，其余改名
            ids = [r[0] for r in q(db, "SELECT ID FROM mt_user WHERE NAME='%s' "
                                       "AND STATUS='A' ORDER BY ID" % name)]
            for uid in ids[1:]:
                if pi >= len(pool):
                    print("  [WARN] 备用姓名池不够了，%s 未处理" % name)
                    ok = False
                    break
                new = pool[pi]
                pi += 1
                stmts.append("UPDATE mt_user SET NAME='%s' WHERE ID=%s;" % (new, uid))
                print("  ID=%s  %s -> %s" % (uid, name, new))
        if stmts:
            if exec_sql(db, "\n".join(stmts)):
                print("  [OK] 改了 %d 个重名会员" % len(stmts))
        left = q(db, "SELECT NAME, COUNT(*) FROM mt_user WHERE STATUS='A' "
                     "GROUP BY NAME HAVING COUNT(*)>1")
        print("  剩余重名组: %d" % len(left))
        if left:
            ok = False
    print("=" * 60)
    print("总体: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

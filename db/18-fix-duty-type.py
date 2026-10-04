# -*- coding: utf-8 -*-
"""修 t_duty.duty_type：把误写的 'SYSTEM' 纠正为 AdminRoleEnum 的 key。

为什么必须修：后端 BackendLoginController.getInfo() 用
    role.getDutyType().equals(item.getKey())
反查角色（key: '1'=超级管理员 / '2'=普通管理员 / '3'=用户角色，见
common/enums/AdminRoleEnum.java）。库内 duty_type 却是 'SYSTEM'，
' SYSTEM'.equals('1') 恒为 false → roles 恒为空数组 → 收银端登录后
getInfo 被守卫反复调用（死循环）、菜单/路由全丢。

映射规则（按 duty_name 语义，幂等）：
    duty_id=1      超级管理员      -> '1'
    其余（店长/财务/顾问/主管等）  -> '2'（普通管理员）
    仅当当前值不是合法 key('1'/'2'/'3') 时才更新，避免覆盖正确数据。

用法: python deploy/db/18-fix-duty-type.py
口令来源优先级：环境变量 DB_PASSWORD > deploy/.env.local 的 DB_PASSWORD。
（仓库内不存明文口令；.env.local 已被 .gitignore 排除）
"""
import os
import subprocess
import sys

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
USER = os.environ.get("DB_USER", "root")


def load_env_password():
    """读 deploy/.env.local 里的 DB_PASSWORD（与环境变量同优先级来源）。"""
    here = os.path.dirname(os.path.abspath(__file__))
    env_local = os.path.join(here, "..", ".env.local")
    try:
        with open(env_local, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DB_PASSWORD="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


PWD = os.environ.get("DB_PASSWORD") or load_env_password()
if not PWD:
    print("!!! 未提供数据库口令：请设置环境变量 DB_PASSWORD，"
          "或在 deploy/.env.local 写入 DB_PASSWORD=...")
    sys.exit(2)

DBS = ["bahar-db", "bahar-car", "bahar-catering", "bahar-health"]
# 合法枚举 key，非此集合的值都视为脏数据
VALID_KEYS = ("1", "2", "3")


def q(db, sql):
    """执行查询，返回按 tab 切分的行列表（-N -B 无表头/批量）。"""
    cmd = [MYSQL, "-u" + USER, "-p" + PWD, "-N", "-B",
           "--default-character-set=utf8mb4", "-D", db, "-e", sql]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [SQL 失败] %s" % p.stderr.strip()[:200])
        return []
    return [l.split("\t") for l in p.stdout.splitlines() if l.strip()]


def exec_sql(db, sql):
    """执行写入语句。"""
    cmd = [MYSQL, "-u" + USER, "-p" + PWD,
           "--default-character-set=utf8mb4", "-D", db]
    p = subprocess.run(cmd, input=sql, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  [执行失败] %s" % p.stderr.strip()[:300])
        return False
    return True


def target_key(duty_id, duty_type):
    """返回该行应写入的 key；若已是合法 key 则返回 None（表示无需改）。"""
    if duty_type in VALID_KEYS:
        return None
    # 超级管理员固定 '1'，其余经营角色按普通管理员 '2'
    return "1" if duty_id == "1" else "2"


def main():
    ok = True
    total_affected = 0
    for db in DBS:
        print("=" * 60)
        print(db)
        print("=" * 60)
        rows = q(db, "SELECT DUTY_ID, DUTY_NAME, DUTY_TYPE FROM t_duty ORDER BY DUTY_ID;")
        if not rows:
            print("  [WARN] t_duty 无数据或库不可用，跳过")
            ok = False
            continue
        stmts = []
        for r in rows:
            duty_id = r[0]
            duty_name = r[1] if len(r) > 1 else ""
            duty_type = r[2] if len(r) > 2 else ""
            new_key = target_key(duty_id, duty_type)
            if new_key is None:
                print("  duty_id=%s  %s  duty_type=%s  （已合法，跳过）"
                      % (duty_id, duty_name, duty_type))
                continue
            stmts.append("UPDATE t_duty SET duty_type='%s' WHERE duty_id=%s;"
                         % (new_key, duty_id))
            print("  duty_id=%s  %s  duty_type=%s -> %s"
                  % (duty_id, duty_name, duty_type, new_key))
        if stmts:
            if exec_sql(db, "\n".join(stmts)):
                total_affected += len(stmts)
                print("  [OK] 更新 %d 行" % len(stmts))
            else:
                ok = False
        else:
            print("  [OK] 无需更新（幂等）")
        # 复核
        after = q(db, "SELECT DUTY_ID, DUTY_TYPE FROM t_duty ORDER BY DUTY_ID;")
        bad = [r for r in after if len(r) > 1 and r[1] not in VALID_KEYS]
        print("  复核: %s" % ("全部合法" if not bad else "仍非法 -> %s" % bad))
        if bad:
            ok = False
    print("=" * 60)
    print("总更新行数: %d" % total_affected)
    print("总体: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

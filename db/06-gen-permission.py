# -*- coding: utf-8 -*-
"""
从后端控制器的 @PreAuthorize("@pms.hasPermission('xxx:yyy:zzz')") 反推全量权限点，
生成 t_source / t_duty_source 初始化数据，并把全部权限授予 demo 超级管理员职务。

权限校验链路（PermissionService.hasPermission）：
    t_account -> t_account_duty -> t_duty_source -> t_source.path
    t_source.path 中 '/' 会被替换成 ':' 后与 @PreAuthorize 的权限串比对
    另含通配："*:*:*" 放行一切 -> 对应 path = '*/*/*'

产出：deploy/db/06-init-permission.sql （四个库，幂等可重跑）
"""
import os
import re
import subprocess

ROOT = r"D:\git-double\bahar"
MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
# 口令不再写死在仓库里：从环境变量读取（本地见 deploy/.env.local）
USER = os.environ.get("DB_USER", "root")
PWD = os.environ.get("DB_PASSWORD", "changeme")

PROJECTS = [
    ("bahar",         "bahar-db",       r"bahar"),
    ("baharCar",      "bahar-car",      r"baharCar"),
    ("baharCatering", "bahar-catering", r"baharCatering"),
    ("baharHealth",   "bahar-health",   r"baharHealth"),
]

PERM_RE = re.compile(r"@pms\.hasPermission\('([^']+)'\)")

# 一级模块中文名
L1 = {
    "system": "系统管理", "content": "内容管理", "order": "订单管理",
    "member": "会员管理", "goods": "商品管理", "coupon": "卡券管理",
    "balance": "余额管理", "userBalance": "会员余额", "settlement": "结算管理",
    "point": "积分管理", "invoice": "发票管理", "userGrade": "会员等级",
    "subMessage": "订阅消息", "store": "门店管理", "smsTemplate": "短信模板",
    "printer": "打印管理", "openGift": "开屏有礼", "stockCheck": "库存盘点",
    "stock": "库存管理", "staff": "员工管理", "merchant": "商户管理",
    "book": "预约管理", "commission": "分销佣金", "refund": "退款管理",
    "cashier": "收银台", "tableArea": "桌台区域", "table": "桌台管理",
}

# 二级/三级动作或子模块中文名
L2 = {
    "index": "列表", "list": "列表", "add": "新增", "edit": "编辑",
    "delete": "删除", "detail": "详情", "setting": "设置",
    "delivery": "发货", "doSubmit": "提交结算", "doConfirm": "确认结算",
    "confirm": "核销", "confirmLog": "核销记录", "distribute": "充值",
    "modify": "调整", "cash": "提现", "log": "日志", "relation": "关系",
    "rule": "规则", "article": "文章", "banner": "轮播图", "service": "服务协议",
    "cate": "分类", "goods": "商品", "group": "分组", "userTag": "标签",
    "userCoupon": "会员券", "coupon": "卡券", "deliverFee": "配送费",
    "takeOut": "外卖", "print": "打印", "reject": "驳回", "export": "导出",
    "import": "导入", "sync": "同步", "audit": "审核", "recharge": "充值",
    "change": "变更", "reset": "重置", "pwd": "密码", "role": "角色",
    "account": "账号", "duty": "职务", "log1": "日志",
}

PAGE_SEGS = ("index", "list")


def cap(s):
    return s[:1].upper() + s[1:] if s else s


def collect_perms(project_dir):
    """扫描工程全部 Java，抽取去重后的权限串"""
    perms = set()
    for dirpath, _, files in os.walk(os.path.join(ROOT, project_dir)):
        if "target" in dirpath.replace("\\", "/").split(os.sep):
            continue
        for fn in files:
            if not fn.endswith(".java"):
                continue
            try:
                txt = open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for m in PERM_RE.finditer(txt):
                p = m.group(1).strip()
                if p and p != "*":
                    perms.add(p)
    return perms


def build_nodes(perms):
    """按 ':' 切分建树；返回有序的 [(source_id, name, path, level, parent_id, ename, is_menu)]"""
    nodes = {}
    roots = []
    counter = [1000]  # 起始 source_id，避开业务数据

    def ensure(segs):
        key = tuple(segs)
        if key in nodes:
            return nodes[key]
        sid = counter[0]
        counter[0] += 1
        level = len(segs)
        last = segs[-1]
        if level == 1:
            name = L1.get(last, cap(last))
            parent = 0
            ename = cap(last)
            is_menu = 1
        else:
            sub = L2.get(last, cap(last))
            name = sub
            parent = ensure(segs[:-1])
            ename = cap(last)
            # 二级里的 index/list 视为页面；其余为按钮级权限
            is_menu = 1 if (level == 2 and last in PAGE_SEGS) else 0
        nodes[key] = sid
        roots.append((sid, name, "/".join(segs), level, parent, ename, is_menu))
        return sid

    for p in sorted(perms):
        ensure(p.split(":"))
    return sorted(roots, key=lambda x: x[0])


def q(s):
    return "'" + str(s).replace("\\", "\\\\").replace("'", "''") + "'"


def gen_sql(db, nodes):
    out = []
    out.append("-- ========== %s : 权限/菜单初始化（幂等，可重复执行）==========" % db)
    out.append("-- 来源：后端控制器 @PreAuthorize 注解，共 %d 个权限节点" % len(nodes))
    out.append("DELETE FROM `%s`.`t_duty_source` WHERE source_id BETWEEN 999 AND 1999;" % db)
    out.append("DELETE FROM `%s`.`t_source`      WHERE source_id BETWEEN 999 AND 1999;" % db)
    out.append("")
    out.append("-- 通配权限：*:*:*  ->  demo 账号放行一切，避免菜单权限遗漏")
    out.append("INSERT INTO `%s`.`t_source` "
               "(source_id, merchant_id, source_name, source_code, path, ename, new_icon, "
               "status, source_level, source_style, is_menu, description, parent_id, is_log, icon) VALUES "
               "(999, 0, %s, %s, %s, %s, %s, 'A', 1, 0, 0, %s, 0, 0, %s);"
               % (db, q("通配权限"), q("all"), q("*/*/*"), q("All"), q(""), q("系统内置通配权限"), q("")))
    out.append("")
    out.append("-- 以下为按 @PreAuthorize 反推的菜单/权限树")
    for sid, name, path, level, parent, ename, is_menu in nodes:
        out.append(
            "INSERT INTO `%s`.`t_source` "
            "(source_id, merchant_id, source_name, source_code, path, ename, new_icon, "
            "status, source_level, source_style, is_menu, description, parent_id, is_log, icon) VALUES "
            "(%d, 1, %s, %s, %s, %s, %s, 'A', %d, %d, %d, %s, %d, 0, %s);"
            % (db, sid, q(name), q(path.replace("/", "_")), q(path), q(ename),
               q("el-icon-menu" if is_menu else ""), level, sid, is_menu,
               q(name), parent, q("")))
    out.append("")
    out.append("-- 全部权限授予 1 号职务（超级管理员）")
    out.append("INSERT INTO `%s`.`t_duty_source` (duty_id, source_id) "
               "SELECT 1, source_id FROM `%s`.`t_source` WHERE source_id BETWEEN 999 AND 1999;" % (db, db))
    out.append("")
    out.append("-- 确保 demo 账号已绑定该职务")
    out.append("INSERT INTO `%s`.`t_account_duty` (acct_id, duty_id) "
               "SELECT a.acct_id, 1 FROM `%s`.`t_account` a "
               "WHERE NOT EXISTS (SELECT 1 FROM `%s`.`t_account_duty` d "
               "WHERE d.acct_id = a.acct_id AND d.duty_id = 1);" % (db, db, db))
    out.append("")
    return "\n".join(out)


def main():
    all_sql = []
    summary = []
    for proj, db, pdir in PROJECTS:
        perms = collect_perms(proj)
        nodes = build_nodes(perms)
        sql = gen_sql(db, nodes)
        all_sql.append(sql)
        summary.append((proj, db, len(perms), len(nodes)))
        # 单库明细留存
        open(os.path.join(ROOT, "deploy", "db", "tmp", "perm_%s.sql" % db),
             "w", encoding="utf-8").write(sql)

    head = ("-- ============================================================\n"
            "-- bahar 四库「菜单 / 权限」初始化脚本\n"
            "-- 由 deploy/db/06-gen-permission.py 自动生成，幂等可重复执行\n"
            "-- 运行: mysql -uroot -p < deploy/db/06-init-permission.sql\n"
            "-- ============================================================\n\n")
    out_path = os.path.join(ROOT, "deploy", "db", "06-init-permission.sql")
    open(out_path, "w", encoding="utf-8").write(head + "\n".join(all_sql))

    print("%-14s %-16s %8s %8s" % ("工程", "库", "权限点", "菜单节点"))
    for r in summary:
        print("%-14s %-16s %8d %8d" % r)
    print("\n生成:", out_path)


if __name__ == "__main__":
    main()

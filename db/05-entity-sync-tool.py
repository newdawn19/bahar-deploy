# -*- coding: utf-8 -*-
"""
按「后端工程 <-> 数据库」配对，做实体类 -> 真实库表结构的全量差异比对。

背景：作者的 db/*.sql 建库脚本比实体类旧，导致若干实体字段在库里不存在，
      MyBatis-Plus 查询时报 Unknown column，后台直接 500。

策略：
  1) 解析每个后端工程的 @TableName 实体类（含父类继承字段）
  2) 与 information_schema 比对
  3) 缺失表 -> CREATE TABLE IF NOT EXISTS
     缺失列 -> ALTER TABLE ADD COLUMN（information_schema 守卫，幂等）
  4) 生成带存储过程的 SQL，可重复执行
"""
import os
import re
import subprocess
import collections

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
# 口令不再写死在仓库里：从环境变量读取（本地见 deploy/.env.local）
USER = os.environ.get("DB_USER", "root")
PWD = os.environ.get("DB_PASSWORD", "changeme")
ROOT = r"D:\git-double\bahar"

# 工程 -> (库名, 实体根目录)
PAIRS = [
    ("bahar",        "bahar-db",       r"bahar\bahar-repository\src\main\java\com\bahar\repository\model"),
    ("baharCar",     "bahar-car",      r"baharCar\backend\bahar-repository\src\main\java\com\bahar\repository\model"),
    ("baharCatering","bahar-catering", r"baharCatering\baharBackend\bahar-repository\src\main\java\com\bahar\repository\model"),
    ("baharHealth",  "bahar-health",   r"baharHealth\backend-api\bahar-repository\src\main\java\com\bahar\repository\model"),
]


def sh(sql, db=None):
    cmd = [MYSQL, "-u" + USER, "-p" + PWD, "-N", "-B"]
    if db:
        cmd += ["-D", db]
    cmd += ["-e", sql]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0 and "Warning" not in (p.stderr or ""):
        raise RuntimeError(p.stderr[:2000])
    return p.stdout


# ---------------- Java 实体解析 ----------------
CLASS_RE = re.compile(r"(?:^|\n)\s*(?:public\s+|final\s+)*class\s+(\w+)(?:\s+extends\s+([\w\.]+))?")
TABLENAME_RE = re.compile(r"@TableName\s*\(\s*value\s*=\s*\"(\w+)\"|@TableName\s*\(\s*\"(\w+)\"")
FIELD_RE = re.compile(r"^\s{2,}private\s+(?!static|final)([\w\.<>\[\],\s]+?)\s+(\w+)\s*(?:=|;)", re.M)
TABLEFIELD_RE = re.compile(r"@TableField\s*\(([^)]*)\)")
TABLEID_RE = re.compile(r"@TableId\s*\(([^)]*)\)")


def camel_to_snake(name):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def strip_annotations_of(line, text, pos):
    """取该字段声明之前的注解块，判断是否 exist=false / transient，并取显式列名"""
    head = text[:pos]
    # 向前找：连续行由 @... 或 // 或 /* */ 组成
    lines = head.split("\n")
    block = []
    for ln in reversed(lines):
        st = ln.strip()
        if st.startswith("@") or st.startswith("//") or st.startswith("*") or st.startswith("/*"):
            block.append(st)
        elif st == "":
            continue
        else:
            break
    block = "\n".join(reversed(block))
    explicit = None
    m = TABLEID_RE.search(block)
    if m:
        v = re.search(r"value\s*=\s*\"(\w+)\"", m.group(1))
        if v:
            explicit = v.group(1)
    if explicit is None:
        m = TABLEFIELD_RE.search(block)
        if m:
            args = m.group(1)
            v = re.search(r"value\s*=\s*\"(\w+)\"", args)
            if v:
                explicit = v.group(1)
            elif args.strip().startswith("\""):
                explicit = args.strip().strip("\"")
    if re.search(r"exist\s*=\s*false", block):
        return None, False
    if re.search(r"^\s*transient\s", line) or " transient " in line:
        return None, False
    return explicit, True


TYPE_MAP = [
    (re.compile(r"^(BigDecimal)$"), "DECIMAL(12,2)"),
    (re.compile(r"^(LocalDateTime|Date|LocalDate|Timestamp|Instant|LocalTime)$"), "DATETIME"),
    (re.compile(r"^(Long|long)$"), "BIGINT"),
    (re.compile(r"^(Integer|int|Short|short|Byte|byte)$"), "INT"),
    (re.compile(r"^(Double|double|Float|float)$"), "DOUBLE"),
    (re.compile(r"^(Boolean|boolean)$"), "TINYINT(1)"),
    (re.compile(r"^(byte\[\]|Byte\[\])$"), "BLOB"),
    (re.compile(r"^(String|char|Character)$"), "VARCHAR"),
]


def java_to_col(jtype):
    jtype = jtype.strip().split("<")[0].strip()
    for rx, sql in TYPE_MAP:
        if rx.match(jtype):
            return sql
    return "VARCHAR"


def parse_models(model_dir):
    """返回 {ClassName: {'table':..,'extends':..,'fields':[(colName, sqlType)]}}"""
    models = {}
    for dirpath, _, files in os.walk(model_dir):
        for fn in files:
            if not fn.endswith(".java"):
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8", errors="replace").read()
            m = CLASS_RE.search(text)
            if not m:
                continue
            cls = m.group(1)
            parent = (m.group(2) or "").split(".")[-1]
            tn = TABLENAME_RE.search(text)
            table = (tn.group(1) or tn.group(2)) if tn else None
            fields = []
            for f in FIELD_RE.finditer(text):
                jtype, name = f.group(1), f.group(2)
                if name in ("serialVersionUID",):
                    continue
                explicit, keep = strip_annotations_of(f.group(0), text, f.start())
                if not keep:
                    continue
                col = explicit.lower() if explicit else camel_to_snake(name)
                fields.append((col, java_to_col(jtype)))
            models[cls] = {"table": table, "extends": parent, "fields": fields}
    # 解析继承
    def resolve(cls, seen=None):
        seen = seen or set()
        if cls in seen or cls not in models:
            return []
        seen.add(cls)
        info = models[cls]
        out = list(info["fields"])
        if info["extends"]:
            out += resolve(info["extends"], seen)
        return out
    resolved = {}
    for cls, info in models.items():
        flds = collections.OrderedDict()
        # 父类字段在前
        parent_first = []
        if info["extends"]:
            parent_first = resolve(info["extends"])
        for c, t in parent_first + info["fields"]:
            flds.setdefault(c, t)
        resolved[cls] = {"table": info["table"], "fields": list(flds.items())}
    return resolved


def existing_schema(db):
    """返回 {table: {col: (dtype, charLen)}}"""
    rows = sh("SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, "
              "IFNULL(CHARACTER_MAXIMUM_LENGTH,0) FROM information_schema.COLUMNS "
              "WHERE TABLE_SCHEMA='%s'" % db)
    sch = collections.defaultdict(dict)
    for line in rows.strip().split("\n"):
        if not line.strip():
            continue
        t, c, dt, cl = line.split("\t")
        sch[t.lower()][c.lower()] = (dt, int(cl))
    return sch


def make_proc(db, missing_tables, missing_cols, existing_row_bytes):
    """生成幂等存储过程"""
    proc = "bahar_sync_%s" % db.replace("-", "_")
    out = []
    out.append("-- 自动生成：%s 实体->库结构补齐（幂等）" % db)
    out.append("DELIMITER $$")
    out.append("DROP PROCEDURE IF EXISTS %s $$" % proc)
    out.append("CREATE PROCEDURE %s()\nBEGIN" % proc)
    for t, cols in missing_tables.items():
        out.append("  -- [建表] %s" % t)
        body = []
        for c, ty in cols:
            if c == "id":
                body.append("  `%s` INT NOT NULL AUTO_INCREMENT" % c)
            else:
                body.append("  `%s` %s NULL" % (c, ty))
        if not any(c == "id" for c, _ in cols):
            if cols:
                body.append("  `id` INT NOT NULL AUTO_INCREMENT")
        pk = ",\n  PRIMARY KEY (`id`)" if any(c == "id" for c, _ in cols) or True else ""
        out.append("  CREATE TABLE IF NOT EXISTS `%s`.`%s` (\n%s%s\n  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
                   % (db, t, ",\n".join(body), pk))
    for t, cols in missing_cols.items():
        out.append("  -- [补列] %s : %s" % (t, ", ".join(c for c, _ in cols)))
        for c, ty in cols:
            out.append("  IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS "
                       "WHERE TABLE_SCHEMA='%s' AND UPPER(TABLE_NAME)=UPPER('%s') "
                       "AND UPPER(COLUMN_NAME)=UPPER('%s')) THEN" % (db, t, c))
            out.append("    ALTER TABLE `%s`.`%s` ADD COLUMN `%s` %s NULL;" % (db, t, c, ty))
            out.append("  END IF;")
    out.append("END $$")
    out.append("DELIMITER ;")
    out.append("CALL %s();" % proc)
    out.append("DROP PROCEDURE IF EXISTS %s;" % proc)
    return "\n".join(out)


def main():
    report = []
    for proj, db, mdir in PAIRS:
        full = os.path.join(ROOT, mdir)
        models = parse_models(full)
        sch = existing_schema(db)
        missing_tables = collections.OrderedDict()
        missing_cols = collections.OrderedDict()
        for cls, info in sorted(models.items()):
            t = info["table"]
            if not t:
                continue
            tl = t.lower()
            if tl not in sch:
                missing_tables[tl] = info["fields"]
                continue
            have = sch[tl]
            need = [(c, ty) for c, ty in info["fields"] if c.lower() not in have]
            # VARCHAR 长度自适应，避免 Row size too large (utf8mb4 每字符 4 字节)
            cur_bytes = sum((cl * 4 if dt in ("varchar", "char") else 0)
                            for dt, cl in have.values())
            budget = max(0, 60000 - cur_bytes)
            n_str = sum(1 for _, ty in need if ty == "VARCHAR")
            per = int(budget / 4 / n_str) if n_str else 0
            fixed = []
            for c, ty in need:
                if ty == "VARCHAR":
                    fixed.append((c, "VARCHAR(%d)" % max(32, min(255, per))) if per >= 32
                                 else (c, "TEXT"))
                else:
                    fixed.append((c, ty))
            if fixed:
                missing_cols[tl] = fixed
        n_alter = sum(len(v) for v in missing_cols.values())
        report.append((proj, db, len(models), len(missing_tables),
                       len(missing_cols), n_alter))
        sql = make_proc(db, missing_tables, missing_cols, 0)
        path = os.path.join(ROOT, "deploy", "db", "tmp", "sync_%s.sql" % db)
        open(path, "w", encoding="utf-8").write(sql)
        print("  -> %s" % path)
        # 明细
        with open(os.path.join(ROOT, "deploy", "db", "tmp", "sync_%s.txt" % db),
                  "w", encoding="utf-8") as f:
            for t, v in missing_tables.items():
                f.write("MISSING TABLE  %s  (%d cols)\n" % (t, len(v)))
            for t, v in missing_cols.items():
                f.write("MISSING COLS   %-28s : %s\n" % (t, ", ".join("%s %s" % x for x in v)))

    print("\n%-14s %-16s %6s %8s %8s %8s" % ("工程", "库", "实体数", "缺表", "缺列表", "缺列数"))
    for r in report:
        print("%-14s %-16s %6d %8d %8d %8d" % r)


if __name__ == "__main__":
    main()

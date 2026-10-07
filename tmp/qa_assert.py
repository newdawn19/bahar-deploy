# -*- coding: utf-8 -*-
"""对 qa_render_result.json 做断言，避免"看着像对"就算过。

断言点：
  A. 三个列表必须出现本次新增的表头
  B. expr 列（所属门店/所属商户）不能为空、不能把模板原样输出（出现 { } 或 undefined）
  C. 边界：商户 201/202（无门店无员工）显示 0；门店 101/102（无员工）显示 0
  D. 员工列表每一行都要有「关联会员」
  E. 控制台不能有 error/warning/未捕获异常
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "qa_render_result.json")

EXPECT_HEADERS = {
    "merchant": ["门店数", "员工数"],
    "store": ["所属商户", "员工数"],
    "staff": ["所属门店", "所属商户", "关联会员"],
}

BAD_PAT = re.compile(r"\{|\}|undefined|null|\[object|function\s*\(")

failures = []
notes = []


def fail(port, route, msg):
    failures.append("[%s %s] %s" % (port, route, msg))


def cell(row, headers, name):
    for i, h in enumerate(headers):
        if h == name:
            return row[i] if i < len(row) else None
    return None


def main():
    with open(RESULT, encoding="utf-8") as fp:
        data = json.load(fp)

    for port, info in data.items():
        for route, spec in info.get("routes", {}).items():
            if "error" in spec:
                fail(port, route, "没抓到表格: %s" % spec["error"])
                continue
            headers = spec.get("headers", [])
            rows = spec.get("rows", [])

            # A. 表头
            for h in EXPECT_HEADERS[route]:
                if h not in headers:
                    fail(port, route, "表头缺少「%s」，实际表头=%s" % (h, headers))

            # E. 控制台
            for lg in spec.get("logs", []):
                fail(port, route, "控制台输出: %s" % lg[:200])
            for er in spec.get("errors", []):
                fail(port, route, "未捕获异常: %s" % er[:300])

            if not rows:
                fail(port, route, "列表 0 行")
                continue

            # B. 关键列不能为空 / 不能是模板原文
            check_cols = EXPECT_HEADERS[route]
            for idx, row in enumerate(rows):
                for col in check_cols:
                    v = cell(row, headers, col)
                    if v is None:
                        fail(port, route, "第%d行找不到列「%s」" % (idx + 1, col))
                        continue
                    if v == "":
                        fail(port, route, "第%d行「%s」为空（行=%s）" % (idx + 1, col, row))
                    elif BAD_PAT.search(v):
                        fail(port, route,
                             "第%d行「%s」疑似模板原文/未渲染: %r" % (idx + 1, col, v))

            # C. 边界
            if route == "merchant":
                for row in rows:
                    if cell(row, headers, "ID") in ("201", "202"):
                        sc = cell(row, headers, "门店数")
                        fc = cell(row, headers, "员工数")
                        if sc != "0" or fc != "0":
                            fail(port, route,
                                 "无门店商户 #%s 应显示 0/0，实际 门店数=%r 员工数=%r"
                                 % (cell(row, headers, "ID"), sc, fc))
                        else:
                            notes.append("%s 商户 #%s 无门店无员工 -> 门店数=%s 员工数=%s (OK)"
                                         % (port, cell(row, headers, "ID"), sc, fc))
            if route == "store":
                for row in rows:
                    name = cell(row, headers, "门店名称")
                    if name in ("城东分店", "新区旗舰店"):
                        fc = cell(row, headers, "员工数")
                        if fc != "0":
                            fail(port, route, "无员工门店「%s」员工数应为 0，实际 %r" % (name, fc))
                        else:
                            notes.append("%s 门店「%s」无员工 -> 员工数=%s (OK)" % (port, name, fc))
            # D. 员工关联会员
            if route == "staff":
                empty = [r for r in rows
                         if not (cell(r, headers, "关联会员") or "").strip()]
                if empty:
                    fail(port, route, "有 %d 名员工「关联会员」为空: %s"
                         % (len(empty), empty[:3]))
                else:
                    notes.append("%s 员工 %d 行全部有「关联会员」(OK)" % (port, len(rows)))
                # expr 列抽样：至少有一行的所属门店/所属商户非空且不是 '-'
                for col in ("所属门店", "所属商户"):
                    vals = [cell(r, headers, col) for r in rows]
                    bad = [v for v in vals if (not v) or v == "-" or BAD_PAT.search(v or "")]
                    if bad:
                        fail(port, route, "expr 列「%s」异常值: %s" % (col, bad[:3]))
                    else:
                        notes.append("%s expr 列「%s」样例=%s (OK)" % (port, col, vals[:3]))

    print("======== 断言明细 ========")
    for n in notes:
        print("  · " + n)
    print("\n======== 结论 ========")
    if failures:
        print("FAIL —— %d 项未通过:" % len(failures))
        for f in failures:
            print("  !! " + f)
        return 1
    print("PASS —— 四套实例三个列表的关联列全部真实渲染，无控制台报错")
    return 0


if __name__ == "__main__":
    sys.exit(main())

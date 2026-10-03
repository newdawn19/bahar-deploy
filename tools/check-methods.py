# -*- coding: utf-8 -*-
"""比对「前端 modules.js 声明的请求方法」与「四个后端工程实际的 @RequestMapping method」。

背景：Admin 是四个实例共用的一份静态资源，但四套后端的同名接口
有 GET/POST 不一致（典型：商品列表零售/汽车/康养是 POST，餐饮是 GET）。
前端写死一种方法，必然在某一个工程上报
    "请求地址'...',不支持'POST'请求"。
这个脚本把不一致一次性列出来，避免靠用户逐个页面点才发现。

用法: python deploy/tools/check-methods.py
"""
import io
import os
import re

# 从脚本位置反推仓库根，别写死绝对路径 —— 换台机器/换个盘符就得改
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

PROJECTS = [
    ("零售 8081", "bahar/bahar-application/src/main/java"),
    ("汽车 8082", "baharCar/backend/bahar-application/src/main/java"),
    ("餐饮 8083", "baharCatering/baharBackend/bahar-application/src/main/java"),
    ("康养 8084", "baharHealth/backend-api/bahar-application/src/main/java"),
]

# 前端未显式写 method 时的默认值（与 crud.js / api.js 的调用方式一致）
DEFAULT_METHOD = {"list": "get", "save": "post", "status": "post",
                  "info": "get", "del": "get"}


def _first_path(body):
    """从 @RequestMapping(...) 的括号内容里取出第一个路径字面量，
    兼容 value=/path=/{"a"} 与 @RequestMapping("/x") 简写。"""
    m = re.search(r'(?:value|path)\s*=\s*\{\s*"([^"]+)"', body)
    if m:
        return m.group(1)
    m = re.search(r'(?:value|path)\s*=\s*"([^"]+)"', body)
    if m:
        return m.group(1)
    m = re.search(r'^\s*"([^"]+)"', body)
    return m.group(1) if m else None


def parse_backend(src_dir):
    """扫出 { 归一化路径: set(method) }"""
    out = {}
    # 类级与方法级注解结构相同，靠是否含 RequestMethod/GetMapping/PostMapping 区分
    ann_re = re.compile(r'@(RequestMapping|GetMapping|PostMapping)\(([^)]*)\)')
    for dirpath, _, files in os.walk(src_dir):
        if "controller" not in dirpath.lower():
            continue
        for fn in files:
            if not fn.endswith("Controller.java"):
                continue
            text = io.open(os.path.join(dirpath, fn), encoding="utf-8",
                           errors="ignore").read()
            # 类声明之前的注解是类级的，之后的是方法级的。
            # 不能靠"有没有 method"区分：@RequestMapping(value="/list") 不写 method
            # 时 Spring 放行所有方法，那正是方法级注解。
            cm = re.search(r'\bpublic\s+class\b', text)
            split = cm.start() if cm else 0
            base = ""
            for mm in ann_re.finditer(text):
                kind, body, pos = mm.group(1), mm.group(2), mm.start()
                path = _first_path(body)
                if path is None:
                    continue
                if pos < split:
                    base = path
                    continue
                if "RequestMethod" in body:
                    methods = set(x.lower() for x in
                                  re.findall(r'RequestMethod\.(\w+)', body))
                elif kind == "GetMapping":
                    methods = {"get"}
                elif kind == "PostMapping":
                    methods = {"post"}
                else:
                    methods = {"get", "post"}   # 未限定：任意方法都放行
                out.setdefault(norm(base + path), set()).update(methods)
    return out


def parse_frontend(path):
    """扫出 [ (动作, url, method) ]"""
    text = io.open(path, encoding="utf-8").read()
    pat = re.compile(
        r'\b(list|save|info|status|del):\s*\{\s*(?:method:\s*\'(\w+)\',\s*)?'
        r'url:\s*\'([^\']+)\'')
    out = []
    for m in pat.finditer(text):
        act, method, url = m.group(1), m.group(2), m.group(3)
        out.append((act, url, (method or DEFAULT_METHOD[act]).lower()))
    return out


def norm(url):
    """把 {id} 换成占位，便于与后端路径匹配"""
    return re.sub(r'\{[^}]+\}', '{x}', url)


def main():
    fe = parse_frontend(os.path.join(ROOT, "deploy", "admin", "js", "modules.js"))
    bes = [(name, parse_backend(os.path.join(ROOT, p))) for name, p in PROJECTS]

    print("前端 modules.js 共声明 %d 个接口\n" % len(fe))
    rows = []
    for act, url, method in fe:
        key = norm(url)
        supported = {}
        for name, be in bes:
            ms = be.get(key)
            supported[name] = ("?/" .join(sorted(ms)) if ms else "——")
            if ms:
                supported[name] = "/".join(sorted(ms))
        # 后端未登记的不参与判断（可能是路径拼不出来）
        known = {k: v for k, v in supported.items() if v != "——"}
        if not known:
            rows.append((url, method, supported, "未匹配到后端映射"))
            continue
        bad = [k for k, v in known.items() if method not in v.split("/")]
        if len(set(known.values())) > 1:
            rows.append((url, method, supported, "四套后端本身不一致"))
        elif bad:
            rows.append((url, method, supported, "前端 %s 与全部后端冲突" % method))
        else:
            continue

    if not rows:
        print("全部一致，没有 GET/POST 冲突。")
        return

    print("=" * 96)
    print("%-46s %-6s %s" % ("URL", "前端", "问题"))
    print("=" * 96)
    for url, method, supported, issue in rows:
        print("%-46s %-6s %s" % (url, method, issue))
        print("     后端: " + "  ".join(
            "%s=%s" % (k, v) for k, v in supported.items()))
    print("=" * 96)
    print("共 %d 处" % len(rows))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""用真实 HTTP 拉取运行中的 Admin 静态资源，确认浏览器实际拿到的是新版还是旧版。

本机全局代理 http_proxy=127.0.0.1:50078 会把 127.0.0.1 也代理掉并 502，
所以必须显式构造一个不带代理的 opener。
"""
import hashlib
import sys
import urllib.request

SRC_MD5 = {
    "modules.js": None,
    "crud.js": None,
    "api.js": None,
    "app.js": None,
    "views.js": None,
}

PORTS = [8081, 8082, 8083, 8084]

KEYS = ["所属商户", "所属门店", "门店数", "员工数", "关联会员"]


def md5_file(path):
    """返回文件 md5。"""
    with open(path, "rb") as fp:
        return hashlib.md5(fp.read()).hexdigest()


def load_src_md5():
    """读取 deploy/admin 源文件的 md5。"""
    base = r"D:\git-double\bahar\deploy\admin\js"
    for name in SRC_MD5:
        SRC_MD5[name] = md5_file(base + "\\" + name)


def fetch(url):
    """绕过代理 GET，返回 (status, bytes)；失败返回 (None, None)。"""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url, timeout=8) as resp:
            return resp.status, resp.read()
    except Exception as exc:  # noqa: BLE001 - 诊断脚本，需要吞掉所有网络异常
        return None, ("ERR: %s" % exc).encode("utf-8")


def main():
    load_src_md5()
    print("源文件 md5:")
    for k, v in SRC_MD5.items():
        print("   %-12s %s" % (k, v))
    print()

    for port in PORTS:
        url = "http://127.0.0.1:%d/admin/js/modules.js" % port
        status, body = fetch(url)
        print("== %s ==" % url)
        if status != 200:
            print("   状态: %s  %s" % (status, body[:160].decode("utf-8", "replace")))
            continue
        got = hashlib.md5(body).hexdigest()
        same = (got == SRC_MD5["modules.js"])
        print("   HTTP 200, %d bytes, md5=%s -> %s" % (
            len(body), got, "新版(与源一致)" if same else "*** 旧版 ***"))
        txt = body.decode("utf-8", "replace")
        hit = [k for k in KEYS if k in txt]
        miss = [k for k in KEYS if k not in txt]
        print("   命中关键字: %s" % (",".join(hit) or "(无)"))
        if miss:
            print("   缺失关键字: %s" % ",".join(miss))

        for name in ("crud.js", "api.js", "app.js", "views.js"):
            st2, b2 = fetch("http://127.0.0.1:%d/admin/js/%s" % (port, name))
            if st2 != 200:
                print("   %-10s 状态 %s" % (name, st2))
                continue
            g2 = hashlib.md5(b2).hexdigest()
            print("   %-10s md5=%s -> %s" % (
                name, g2, "一致" if g2 == SRC_MD5[name] else "*** 不一致 ***"))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

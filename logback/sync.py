# -*- coding: utf-8 -*-
"""把 deploy/logback/logback-spring.xml 模板铺到四套工程。

每套写两处：
  1) src/main/resources/logback-spring.xml —— 源码，供打包
  2) target/classes/logback-spring.xml     —— IDEA 直接运行时 classpath 实际加载的就是它。
     只写 src 的话，IDEA 里跑的仍是旧日志配置（和 jar 行为不一致）。

模板里的 APP_NAME 默认值按实例替换成各自的名字；
运行时还能用 -DAPP_NAME= / -DLOG_HOME= 覆盖（start-all.sh 就是这么传的）。

用法： python deploy/logback/sync.py
"""
import io
import os
import re

BASE = r"D:\git-double\bahar\deploy\logback"
TPL = os.path.join(BASE, "logback-spring.xml")

# (bahar-application 模块根, 实例名, 行业)
INSTANCES = [
    (r"D:\git-double\bahar\bahar\bahar-application", "bahar-shop", "零售"),
    (r"D:\git-double\bahar\baharCar\backend\bahar-application", "bahar-car", "汽车"),
    # 实例名刻意与 runtime jar 名保持一致（bahar-food.jar）：
    # start-all.sh 是用 -DAPP_NAME="${jar%.jar}" 推导的，两边不一致会导致
    # 同一套服务在两种启动方式下落进不同目录
    (r"D:\git-double\bahar\baharCatering\baharBackend\bahar-application", "bahar-food", "餐饮"),
    (r"D:\git-double\bahar\baharHealth\backend-api\bahar-application", "bahar-health", "康养"),
]


def render(tpl, app_name):
    return re.sub(r'value="\$\{APP_NAME:-[a-z0-9-]+\}"',
                  'value="${APP_NAME:-%s}"' % app_name, tpl)


def main():
    tpl = io.open(TPL, encoding="utf-8").read()
    for module, app, industry in INSTANCES:
        content = render(tpl, app)
        targets = [os.path.join(module, "src", "main", "resources", "logback-spring.xml")]
        tc = os.path.join(module, "target", "classes", "logback-spring.xml")
        if os.path.isdir(os.path.dirname(tc)):
            targets.append(tc)
        for t in targets:
            if not os.path.isdir(os.path.dirname(t)):
                print("!! 跳过（目录不存在）: " + t)
                continue
            with io.open(t, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            print("OK  %-6s %-16s -> %s" % (industry, app, t))


if __name__ == "__main__":
    main()

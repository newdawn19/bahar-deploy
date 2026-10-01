# -*- coding: utf-8 -*-
"""把 Element UI 图标字体内联进 CSS（data URI），绕开后端鉴权。

为什么需要：SecurityConfig 的匿名访问白名单只放行
  /**/*.html、/**/*.css、/**/*.js
字体文件（.woff / .ttf）不在其中，会被 anyRequest().authenticated() 拦成 403，
图标字体加载不到，页面上所有 el-icon-* 都显示不出来。

改 Java 侧白名单是根治办法，但要重新打包（约 14 分钟）。这里先把 woff 内联成
data URI，随 CSS 一起走 /**/*.css 放行规则，改完 patch_jars 立即生效。

用法： python make_inline_font.py   （在 deploy/admin 目录下执行）
"""
import base64
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WOFF = os.path.join(HERE, "vendor", "fonts", "element-icons.woff")
OUT = os.path.join(HERE, "vendor", "element-icons-inline.css")

with open(WOFF, "rb") as fp:
    b64 = base64.b64encode(fp.read()).decode()

css = (
    "/* 由 make_inline_font.py 生成：把图标字体内联为 data URI。\n"
    "   原因：后端 SecurityConfig 未放行 .woff/.ttf，字体请求会被 403。 */\n"
    '@font-face{font-family:element-icons;'
    'src:url(data:application/font-woff;charset=utf-8;base64,%s) format("woff");'
    'font-weight:400;font-display:"auto";font-style:normal}\n' % b64
)

io.open(OUT, "w", encoding="utf-8", newline="\n").write(css)
print("已生成 %s (%.1f KB)" % (OUT, len(css) / 1024.0))

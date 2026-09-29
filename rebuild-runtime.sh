#!/usr/bin/env bash
# 一条命令完成：四套后端重新打包 → 复制到 deploy/runtime → 重新注入 Admin 静态资源
#
# 什么时候需要跑：改了 application.yaml / sentry.yaml 之后，
# deploy/runtime 里的 jar 就是旧的，必须重打，否则改动不生效。
#
# 用法： ./deploy/rebuild-runtime.sh
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

PYTHON="${PYTHON:-python}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON="C:/Users/Lenovo/.workbuddy/binaries/python/versions/3.13.12/python.exe"

echo "===== 1/3 打包四套后端 ====="
./deploy/build-all.sh package || { echo "!!! 打包失败"; exit 1; }

echo ""
echo "===== 2/3 复制 fat jar 到 deploy/runtime ====="
pick() { # $1=模块 target 目录  $2=目标 jar 名
  local src
  src="$(find "$1" -maxdepth 1 -name '*.jar' ! -name '*sources*' ! -name '*javadoc*' 2>/dev/null | head -1)"
  if [ -z "$src" ]; then
    echo "!!! 没找到 jar: $1"
    return 1
  fi
  cp -f "$src" "deploy/runtime/$2"
  echo "  $2  <-  $src"
}

pick "bahar/bahar-application/target"            "bahar-shop.jar"   || exit 1
pick "baharCar/backend/bahar-application/target" "bahar-car.jar"    || exit 1
pick "baharCatering/baharBackend/bahar-application/target" "bahar-food.jar" || exit 1
pick "baharHealth/backend-api/bahar-application/target"    "bahar-health.jar" || exit 1

echo ""
echo "===== 3/3 重新注入 Admin 静态资源 ====="
# 直接打包会覆盖掉之前注入的 static/admin，必须重新注入
"$PYTHON" deploy/admin/patch_jars.py || { echo "!!! 注入 Admin 失败"; exit 1; }

echo ""
echo "完成。下一步： ./deploy/start-all.sh"

#!/usr/bin/env bash
# 一键编译/打包 bahar 四套后端（绕开 IDEA，直接用本机 Maven + JDK）
# 用法:
#   ./build-all.sh            # 只编译（compile）
#   ./build-all.sh package    # 打 fat jar（package, 跳过测试）
#
# 注意：四个仓库的 Maven 根目录不在仓库顶层，而在各自的子目录里。

set -u

GOAL="${1:-compile}"
MVN="${MVN:-/d/maven-qg-3.9.11/bin/mvn}"
JAVA_HOME="${JAVA_HOME:-C:/Program Files/Java/jdk-11}"
export JAVA_HOME

PROJECTS=(
  "bahar|bahar"
  "baharCar|baharCar/backend"
  "baharCatering|baharCatering/baharBackend"
  "baharHealth|baharHealth/backend-api"
)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

fail=0
for item in "${PROJECTS[@]}"; do
  name="${item%%|*}"
  dir="${item##*|}"
  echo ""
  echo "==================================================="
  echo ">>> [$name]  $dir   goal=$GOAL"
  echo "==================================================="
  cd "$ROOT/$dir" || { echo "目录不存在: $ROOT/$dir"; fail=1; continue; }

  if [ "$GOAL" = "package" ]; then
    "$MVN" -B -DskipTests clean package
  else
    "$MVN" -B -DskipTests clean compile
  fi

  if [ $? -ne 0 ]; then
    echo "!!! [$name] 构建失败"
    fail=1
  else
    echo "### [$name] OK"
  fi
done

echo ""
if [ $fail -eq 0 ]; then
  echo "全部构建成功 ✅"
else
  echo "存在失败工程 ❌"
fi
exit $fail

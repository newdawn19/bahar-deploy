#!/usr/bin/env bash
# 一键启动 bahar 四套演示实例（零售 8081 / 汽车 8082 / 餐饮 8083 / 康养 8084）
# 后台 Admin 入口： http://127.0.0.1:<port>/admin/index.html
# 演示账号： bahar / 123456
#
# 前置：Redis 已启动、MySQL 已初始化（deploy/db/*.sql）
# 用法： ./start-all.sh

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# java 可执行文件：优先环境变量 JAVA_BIN，其次 JAVA_HOME，最后 PATH 探测。
# 不再写死 Windows 路径，Linux 部署可直接用。
if [ -z "${JAVA_BIN:-}" ]; then
  if [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then
    JAVA_BIN="$JAVA_HOME/bin/java"
  else
    JAVA_BIN="$(command -v java 2>/dev/null || true)"
  fi
fi
if [ -z "${JAVA_BIN:-}" ]; then
  echo "!!! 找不到 java，请设置 JAVA_BIN 或 JAVA_HOME"
  exit 1
fi
echo "java: $JAVA_BIN"

RUN_DIR="$ROOT/deploy/runtime"
LOG_DIR="$ROOT/deploy/logs"

# 四套 application.yaml 里数据库密码都是 ${DB_PASSWORD:changeme} 占位，
# 不传就用默认值 changeme，连接池初始化直接失败
# （报 "Public Key Retrieval is not allowed"，实际是密码不对）。
# 本地默认口令放在 deploy/.env.local（该文件不入库，避免密码进仓库）：
#   echo 'DB_PASSWORD=你的口令' > deploy/.env.local
# 也可临时指定：DB_PASSWORD=xxx ./start-all.sh
ENV_LOCAL="$ROOT/deploy/.env.local"
[ -f "$ENV_LOCAL" ] && . "$ENV_LOCAL"
export DB_PASSWORD="${DB_PASSWORD:-changeme}"

mkdir -p "$LOG_DIR"

# 名称 | 运行 jar | 端口   （用 | 分隔，各字段不要带多余空格）
INSTANCES=(
  "零售 bahar-shop|bahar-shop.jar|8081"
  "汽车 bahar-car|bahar-car.jar|8082"
  "餐饮 bahar-food|bahar-food.jar|8083"
  "康养 bahar-health|bahar-health.jar|8084"
)

# 去掉首尾空白，避免 jar 名匹配不到
trim() { printf '%s' "$1" | tr -d '[:space:]'; }

echo "运行目录: $RUN_DIR"
if [ ! -d "$RUN_DIR" ] || [ -z "$(ls -A "$RUN_DIR" 2>/dev/null)" ]; then
  echo "!!! $RUN_DIR 里没有 jar，请先执行 ./build-all.sh package 并把产物复制到 deploy/runtime"
  exit 1
fi

for item in "${INSTANCES[@]}"; do
  label="$(trim "${item%%|*}")"
  rest="${item#*|}"
  jar="$(trim "${rest%%|*}")"
  port="$(trim "${rest##*|}")"

  if [ ! -f "$RUN_DIR/$jar" ]; then
    echo "!!! 缺少 $jar，跳过 $label"
    continue
  fi

  # 端口已占用则跳过
  if netstat -ano 2>/dev/null | grep -q "127.0.0.1:$port .*LISTENING"; then
    echo "--- [$label] 端口 $port 已在监听，跳过"
    continue
  fi

  echo ">>> [$label] $jar  ->  http://127.0.0.1:$port/admin/index.html"
  # 必须显式传 --server.port：IDE 会往环境里注入 SERVER__PORT(如 16713)，
  # Spring Boot 的宽松绑定会把它当成 server.port，覆盖掉 yaml 里的 8081~8084。
  # 命令行参数优先级最高，可确保端口确定。
  SERVER__PORT= SERVER_PORT= "$JAVA_BIN" -jar "$RUN_DIR/$jar" --server.port="$port" > "$LOG_DIR/$jar.log" 2>&1 &
  echo $! > "$LOG_DIR/$jar.pid"
done

echo ""
echo "启动指令已下发，等待就绪约 15 秒后可用。日志在 $LOG_DIR"
echo "停止： ./stop-all.sh"

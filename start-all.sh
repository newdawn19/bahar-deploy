#!/usr/bin/env bash
# 一键启动 bahar 四套演示实例（零售 8081 / 汽车 8082 / 餐饮 8083 / 康养 8084）
# 后台 Admin 入口： http://127.0.0.1:<port>/admin/index.html
# 演示账号： bahar / 123456
#
# 前置：Redis 已启动、MySQL 已初始化（deploy/db/*.sql）
# 用法： ./start-all.sh
#
# 行为：先把四套全部拉起，再逐个轮询等待就绪。
#       成功的打印"就绪"；失败的**打印该实例的报错摘要与日志路径**，不会静默跳过。
#       超时（默认 90 秒）同样视为失败并打印日志尾部，方便直接定位。
#       最后汇总；有失败时以退出码 1 结束（交互运行下会等你按键再关，避免一闪而过）。

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
# 优先级：命令行显式指定 > .env.local > 兜底 changeme
# （先存下命令行传进来的值，否则会被 .env.local 里的赋值盖掉）
CLI_DB_PASSWORD="${DB_PASSWORD:-}"
ENV_LOCAL="$ROOT/deploy/.env.local"
[ -f "$ENV_LOCAL" ] && . "$ENV_LOCAL"
[ -n "$CLI_DB_PASSWORD" ] && DB_PASSWORD="$CLI_DB_PASSWORD"
export DB_PASSWORD="${DB_PASSWORD:-changeme}"

# 单实例就绪等待上限（秒），机器慢可加大： READY_TIMEOUT=180 ./start-all.sh
READY_TIMEOUT="${READY_TIMEOUT:-90}"

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

# 启动即致命的错误特征（出现任意一个就不用再等了）
FATAL_RE="APPLICATION FAILED TO START|UnableToConnectException|Failed to configure a DataSource|Port .* was already in use|Address already in use"

# 就绪标志。注意四套的启动类名不同，不能只匹配 BaharApplication：
#   零售 Started BaharApplication / 汽车 Started BaharCarApplication /
#   餐饮 Started BaharFoodApplication / 康养 Started BaharHealthApplication
# 所以再兜一个所有套都会打的 "Jetty started on port(s) ..."。
READY_RE="Started .*Application|Jetty started on port"

# 端口是否被占用。Java 监听的是 0.0.0.0:<port> 与 [::]:<port>，
# 只匹配 127.0.0.1 会漏掉上一轮残留的实例，导致新实例一启动就端口冲突。
port_in_use() {
  netstat -ano 2>/dev/null | grep -qE "[:.]$1[[:space:]].*LISTENING"
}

# 轮询等待就绪：0=就绪 1=启动失败 2=超时
wait_ready() {
  local log="$1" waited=0
  while [ "$waited" -lt "$READY_TIMEOUT" ]; do
    if grep -qaE "$READY_RE" "$log" 2>/dev/null; then
      return 0
    fi
    if grep -qaE "$FATAL_RE" "$log" 2>/dev/null; then
      return 1
    fi
    sleep 2
    waited=$((waited + 2))
  done
  return 2
}

# 打印报错摘要：优先 APPLICATION FAILED 那段，否则取 ERROR/异常尾部
show_error() {
  local log="$1" label="$2"
  echo ""
  echo "  ---- [$label] 报错摘要 ----"
  if grep -qa "APPLICATION FAILED TO START" "$log" 2>/dev/null; then
    grep -aA 30 "APPLICATION FAILED TO START" "$log" 2>/dev/null | sed 's/^/  /' | head -35
  else
    grep -aE "ERROR|Exception|Caused by" "$log" 2>/dev/null | tail -15 | sed 's/^/  /'
  fi
  echo "  ---- 日志尾部 ----"
  tail -12 "$log" 2>/dev/null | sed 's/^/  /'
  echo "  ---- 完整日志: $log ----"
  echo ""
}

echo "运行目录: $RUN_DIR"
if [ ! -d "$RUN_DIR" ] || [ -z "$(ls -A "$RUN_DIR" 2>/dev/null)" ]; then
  echo "!!! $RUN_DIR 里没有 jar，请先执行 ./deploy/rebuild-runtime.sh"
  exit 1
fi

echo ""
echo "===== 启动中 ====="
LAUNCHED=()
declare -a LABELS=() JARS=() PORTS=()

for item in "${INSTANCES[@]}"; do
  label="$(trim "${item%%|*}")"
  rest="${item#*|}"
  jar="$(trim "${rest%%|*}")"
  port="$(trim "${rest##*|}")"

  if [ ! -f "$RUN_DIR/$jar" ]; then
    echo "!!! 缺少 $jar，跳过 $label"
    continue
  fi

  # 端口已被占用（多半是上一轮还在跑）则跳过，不覆盖人家的日志
  if port_in_use "$port"; then
    echo "--- [$label] 端口 $port 已在监听，跳过"
    continue
  fi

  # 必须显式传 --server.port：IDE 会往环境里注入 SERVER__PORT(如 16713)，
  # Spring Boot 的宽松绑定会把它当成 server.port，覆盖掉 yaml 里的 8081~8084。
  # 命令行参数优先级最高，可确保端口确定。
  SERVER__PORT= SERVER_PORT= "$JAVA_BIN" -jar "$RUN_DIR/$jar" --server.port="$port" > "$LOG_DIR/$jar.log" 2>&1 &
  echo $! > "$LOG_DIR/$jar.pid"

  echo ">>> [$label] 已下发启动指令 -> http://127.0.0.1:$port/admin/index.html"
  LABELS+=("$label"); JARS+=("$jar"); PORTS+=("$port")
done

echo ""
echo "===== 等待就绪（每套最多 ${READY_TIMEOUT}s）====="
FAILED=()
for i in "${!JARS[@]}"; do
  label="${LABELS[$i]}"; jar="${JARS[$i]}"; port="${PORTS[$i]}"
  log="$LOG_DIR/$jar.log"
  wait_ready "$log" "$port"
  case $? in
    0) echo "  [就绪] $label  http://127.0.0.1:$port/admin/index.html" ;;
    1) echo "  [失败] $label  启动报错"
       FAILED+=("$label")
       show_error "$log" "$label" ;;
    2) echo "  [超时] $label  等待 ${READY_TIMEOUT}s 仍未就绪"
       FAILED+=("$label")
       show_error "$log" "$label" ;;
  esac
done

echo "===== 汇总 ====="
echo "日志目录: $LOG_DIR"

if [ "${#FAILED[@]}" -gt 0 ]; then
  echo ""
  echo "!!! 以下实例未就绪: ${FAILED[*]}"
  echo "常见原因："
  echo "  - MySQL 还没起来，或 DB_PASSWORD 不对（报 Public Key Retrieval is not allowed）"
  echo "  - Redis 没启动（RedisConfig 启动即 ping，不通直接失败）"
  echo "  - 端口被占用、jar 与当前配置不一致（改过 yaml 需跑 rebuild-runtime.sh）"
  # 交互运行时停一下，避免双击运行时窗口一闪而过看不到报错
  if [ -t 0 ]; then
    echo ""
    read -r -p "按回车键关闭..." _ || true
  fi
  exit 1
fi

echo "四套全部就绪。停止： ./deploy/stop-all.sh"

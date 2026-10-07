#!/usr/bin/env bash
# QA 专用：把 8082(汽车) / 8084(康养) 两个演示实例拉起来并常驻。
# 用 run_in_background 跑本脚本，java 进程作为它的子进程存活，供后续无头浏览器访问。
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

[ -f deploy/.env.local ] && . deploy/.env.local
export DB_PASSWORD="${DB_PASSWORD:-changeme}"
export LOG_HOME="${LOG_HOME:-/logs}"

mkdir -p deploy/logs

start_one() {
  local jar="$1" port="$2" log="$3"
  echo ">>> 启动 $jar --server.port=$port  (日志: $log)"
  SERVER__PORT= SERVER_PORT= java -DAPP_NAME="${jar%.jar}" -DLOG_HOME="$LOG_HOME" \
    -jar "deploy/runtime/$jar" --server.port="$port" > "$log" 2>&1 &
  echo $! > "${log%.log}.pid"
}

start_one bahar-car.jar    8082 deploy/logs/bahar-car.qa.log
start_one bahar-health.jar 8084 deploy/logs/bahar-health.qa.log

# 等就绪
for i in $(seq 1 90); do
  r2=$(netstat -ano 2>/dev/null | grep -cE "[:.]8082[[:space:]].*LISTENING")
  r4=$(netstat -ano 2>/dev/null | grep -cE "[:.]8084[[:space:]].*LISTENING")
  if [ "$r2" -gt 0 ] && [ "$r4" -gt 0 ]; then
    # 端口监听只是 Tomcat 起来了，再等 Spring 真正 Ready
    sleep 6
    echo ">>> 8082/8084 均已监听 (第 ${i}0 秒内)"
    break
  fi
  sleep 2
done

echo "=== 就绪状态 ==="
netstat -ano | grep -E ":808[24] " | grep LISTENING
echo "=== 保持常驻（Ctrl-C 结束）==="
# 常驻：等两个子进程，避免脚本退出导致 java 被回收
wait

#!/usr/bin/env bash
# 停止 deploy/start-all.sh 启动的四个实例

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/deploy/logs"

if [ ! -d "$LOG_DIR" ]; then
  echo "没有 $LOG_DIR，未发现运行中的实例"
  exit 0
fi

count=0
for pidfile in "$LOG_DIR"/*.pid; do
  [ -f "$pidfile" ] || continue
  pid="$(cat "$pidfile")"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "停止 PID $pid  ($(basename "$pidfile" .pid))"
    kill "$pid" 2>/dev/null
    count=$((count + 1))
  fi
  rm -f "$pidfile"
done

# 兜底：pid 文件里的号未必对得上实际 java 进程（Git Bash 的 $! 有时拿到的
# 是中间 shell 的 PID），所以再按端口扫一遍把漏网的杀掉。
# Java 监听在 0.0.0.0:<port> 与 [::]:<port>，不要只匹配 127.0.0.1。
stop_port() {
  local port="$1" pids pid
  pids=$(netstat -ano 2>/dev/null | grep -E "[:.]$port[[:space:]].*LISTENING" \
         | awk '{print $NF}' | sort -u)
  for pid in $pids; do
    [ -n "$pid" ] || continue
    echo "停止端口 $port 上的 PID $pid"
    kill "$pid" 2>/dev/null || taskkill //PID "$pid" //F > /dev/null 2>&1 || true
  done
}

for port in 8081 8082 8083 8084; do
  stop_port "$port"
done

if [ "$count" -eq 0 ]; then
  echo "没有运行中的实例（已按端口再确认一遍）"
else
  echo "已停止 $count 个实例（并已按端口清理残留）"
fi

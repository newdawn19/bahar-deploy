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

if [ "$count" -eq 0 ]; then
  echo "没有运行中的实例"
else
  echo "已停止 $count 个实例"
fi

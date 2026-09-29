#!/usr/bin/env bash
# 生成 MySQL 容器初始化脚本：从本机已调好的四个库直接导出（结构 + 演示数据）。
#
# 为什么不从各仓库的 db/*.sql 拼：
#   餐饮的 bahar-food.sql 只有 62 表（缺 8 张），康养更是完全没有 SQL，
#   且两个迁移脚本写死了库名 bahar-db。本机四库已经是补齐后的最终状态
#   （bahar-db 70 / bahar-car 68 / bahar-catering 70 / bahar-health 64 表），
#   直接导出最稳，避免把补表补列的活儿搬到服务器上重做一遍。
#
# 用法： ./prepare-mysql-init.sh           # 口令取自 deploy/.env.local 或 DB_PASSWORD
#        DB_PASSWORD=xxx ./prepare-mysql-init.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/mysql-init"

# 与 start-all.sh 一致：本地默认口令从 deploy/.env.local 读取（该文件不入库，
# 避免把真实口令写进仓库）。也可临时指定：DB_PASSWORD=xxx ./prepare-mysql-init.sh
ENV_LOCAL="$(cd "$HERE/.." && pwd)/.env.local"
[ -f "$ENV_LOCAL" ] && . "$ENV_LOCAL"
DB_PASSWORD="${DB_PASSWORD:-changeme}"

# 探测 mysqldump
DUMP="${DUMP_BIN:-}"
if [ -z "$DUMP" ]; then
  for c in mysqldump "/c/Program Files/MySQL/MySQL Server 8.0/bin/mysqldump.exe" \
           "/usr/bin/mysqldump" "/usr/local/mysql/bin/mysqldump"; do
    if command -v "$c" >/dev/null 2>&1; then DUMP="$c"; break; fi
  done
fi
if [ -z "$DUMP" ]; then
  echo "!!! 找不到 mysqldump，可用 DUMP_BIN=/path/to/mysqldump 指定"
  exit 1
fi

mkdir -p "$OUT"
rm -f "$OUT"/*.sql

echo "mysqldump: $DUMP"
echo "导出四库到 $OUT ..."

"$DUMP" -h"${DB_HOST:-127.0.0.1}" -P"${DB_PORT:-3306}" -uroot -p"$DB_PASSWORD" \
  --databases bahar-db bahar-car bahar-catering bahar-health \
  --default-character-set=utf8mb4 --single-transaction --skip-lock-tables \
  > "$OUT/00-all-databases.sql"

if [ ! -s "$OUT/00-all-databases.sql" ]; then
  echo "!!! 导出为空，请检查 MySQL 是否启动、密码是否正确、四个库是否存在"
  exit 1
fi

echo ""
echo "完成： $OUT/00-all-databases.sql  ($(wc -c < "$OUT/00-all-databases.sql") 字节)"
echo "容器首次启动会自动导入（挂载到 /docker-entrypoint-initdb.d）。"
echo "注意：仅在 mysql-data 卷为空（首次启动）时导入一次；已有数据不会重复执行。"

# 公网部署（Docker Compose + Nginx）

把四行业演示站从本机 `127.0.0.1` 搬到一台公网服务器。

## 架构

```
                    ┌─ shop.<DOMAIN>   → bahar-shop   :8080 → MySQL bahar-db       + Redis db0
客户端 ── Nginx ────┼─ car.<DOMAIN>    → bahar-car    :8080 → MySQL bahar-car       + Redis db1
                    ├─ food.<DOMAIN>   → bahar-food   :8080 → MySQL bahar-catering  + Redis db2
                    └─ health.<DOMAIN> → bahar-health :8080 → MySQL bahar-health    + Redis db3
```

**为什么用子域名而不是路径前缀**：四套后端没有 `context-path`，接口都是
`/backendApi/**`、页面是 `/admin/index.html`。若用 `域名/shop/` 这种前缀，
前端 `api.js` 里的请求地址会全部错位。子域名方案零代码改动。

## 一、服务器上准备

- Docker 20.10+ 与 Docker Compose v2
- 域名 DNS：给四个子域名各加一条 A 记录指向服务器（或 `*.域名` 通配解析）
- 放通 80 端口（HTTPS 启用后放通 443）
- 建议 4C8G 及以上：四个 JVM 各 `-Xmx512m`，加 MySQL 与 Redis

## 二、本机准备

```bash
# 1) 重新打包四套后端（改过 yaml / sentry 后必须重打）
cd D:/git-double/bahar && ./deploy/build-all.sh package

# 2) 把产物放到 deploy/runtime（四个 jar 已在此，跳过即可）
#    bahar-shop.jar / bahar-car.jar / bahar-food.jar / bahar-health.jar

# 3) 导出本机已调好的四个库作为容器初始化脚本
cd deploy/docker && ./prepare-mysql-init.sh
```

## 三、上传到服务器

```bash
# 只需 deploy 目录（含 runtime 四个 jar 与 db 脚本）
scp -r D:/git-double/bahar/deploy user@server:/opt/bahar/
```

## 四、配置并启动

```bash
cd /opt/bahar/deploy/docker
cp .env.example .env
vi .env                     # 填 DOMAIN 与 DB_PASSWORD（务必改强密码）

docker compose up -d
docker compose ps           # 五个应用容器 + mysql + redis + nginx 全部 healthy
```

## 五、验证

| 入口 | 地址 |
|---|---|
| 零售后台 | `http://shop.<域名>/admin/index.html` |
| 汽车后台 | `http://car.<域名>/admin/index.html` |
| 餐饮后台 | `http://food.<域名>/admin/index.html` |
| 康养后台 | `http://health.<域名>/admin/index.html` |

演示账号 `bahar / 123456`（**上线前必须改**，见 GAP-LIST 的 G11）。

## 六、启用 HTTPS

```bash
# 通配符证书需 DNS 验证（按提示添加 TXT 记录）
certbot certonly --manual --preferred-challenges dns -d "*.<域名>" -d "<域名>"

cp /etc/letsencrypt/live/<域名>/fullchain.pem /opt/bahar/deploy/docker/certs/
cp /etc/letsencrypt/live/<域名>/privkey.pem   /opt/bahar/deploy/docker/certs/
```

然后打开 `docker-compose.yml` 里 nginx 的 `443:443` 映射，并把
`nginx/templates/bahar.conf.template` 末尾的 443 四段反注释，最后
`docker compose up -d nginx` 重启即可。

## 七、日常运维

```bash
docker compose logs -f shop          # 看某一套的日志
docker compose restart food          # 改了 jar 后重启对应实例
docker compose down                  # 停止（数据卷保留）
```

更新 jar：把新 jar 覆盖 `deploy/runtime/*.jar`，再 `docker compose restart <服务名>`
（jar 是挂载进去的，不需要重新构建镜像）。

## 与本地脚本的关系

| 场景 | 用哪个 |
|---|---|
| 本机开发 / 演示 | `deploy/start-all.sh` + `deploy/stop-all.sh`（直接 `java -jar`，8081-8084） |
| 公网部署 | 本目录 `docker compose up -d`（容器内统一 8080，Nginx 按子域名分发） |

两套共用同一批 jar 与同一份配置；`application.yaml` 里所有本机相关值都已改成
环境变量占位（`DB_HOST`、`DB_NAME`、`REDIS_HOST`、`REDIS_DB`、`IMAGE_ROOT`、
`IMAGE_BASE_URL`），本地不传变量时行为与改动前完全一致。

## 已知注意点

- **MySQL 只在数据卷为空时导入一次** `mysql-init/*.sql`。若四个库已存在但有改动，
  需要 `docker compose down -v` 清卷后重新启动（会丢数据，慎用在演示库）。
- **Sentry 已禁用**（原配置指向作者自建的第三方服务器，对外演示会外泄堆栈）。
- 四套后端都依赖 Redis 才能启动（`RedisConfig` 启动即 `ping`），compose 里已配
  `depends_on` 健康检查。

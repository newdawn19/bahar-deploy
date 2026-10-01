# 本地部署方案（四行业演示站）

适用：在本机或一台内网机器上，从零把四套演示实例跑起来，用于开发、演示或给客户现场看。
如果要放到公网对外，看 `docker/README.md`（Docker Compose + Nginx + 域名）。

---

## 一、环境要求

| 组件 | 版本 | 说明 |
|---|---|---|
| JDK | 11 | 四套后端编译目标 1.8，运行用 11 验证过；17 也能编 |
| Maven | 3.6+ | 打包用，本地仓库 `D:\maven-qg-3.9.11\repository` |
| MySQL | 8.0 | 四库：bahar-db / bahar-car / bahar-catering / bahar-health |
| Redis | 5+ | **强依赖**：`RedisConfig` 启动即 ping，不通则启动失败 |
| Node | 16+ | 仅运行 Electron 收银端时需要 |
| 内存 | 8G 建议 | 四个 JVM 各约 300-500M |

**MySQL 必须能容纳四个库，且 Redis 必须在启动应用之前就已经就绪。**
这两条是启动失败最常见的原因，见「六、常见问题」。

---

## 二、最快路径（已有 jar 和数据库时）

```bash
cd D:/git-double/bahar
./deploy/start-all.sh          # 起四套：8081 零售 / 8082 汽车 / 8083 餐饮 / 8084 康养
```

然后打开：

| 行业 | 后台入口 |
|---|---|
| 零售 | http://127.0.0.1:8081/admin/index.html |
| 汽车美容 | http://127.0.0.1:8082/admin/index.html |
| 餐饮 | http://127.0.0.1:8083/admin/index.html |
| 康养美业 | http://127.0.0.1:8084/admin/index.html |

演示账号 `bahar / 123456`。

---

## 三、从零开始

### 1. 准备数据库

```bash
# 依次导入（顺序不能变：先建业务库，再补表结构，再灌数据）
mysql -uroot -p < deploy/db/01-init-data.sql          # 平台/商户/门店/职务/账号
mysql -uroot -p < deploy/db/02-patch-tables.sql       # 补缺失表
mysql -uroot -p < deploy/db/03-create-health-db.sql   # 康养库（从主库复制表结构）
mysql -uroot -p < deploy/db/04-init-basic-data.sql    # 基础业务数据
mysql -uroot -p < deploy/db/06-init-permission.sql    # 权限点（否则接口全 AccessDenied）
mysql -uroot -p < deploy/db/07-backfill-null-columns.sql  # 新增列的存量回填
mysql -uroot -p < deploy/db/08-demo-data.sql          # 演示数据（商品/会员/订单/流水）
```

> 若表结构与实体类不一致（报 `Unknown column`），用
> `python deploy/db/05-entity-sync-tool.py` 重新比对并生成补列 SQL。
> 若菜单权限不对，用 `python deploy/db/06-gen-permission.py` 重新生成。

### 2. 配置数据库口令（本地唯一需要配的东西）

```bash
echo 'DB_PASSWORD=你的口令' > deploy/.env.local
```

**就这一个。** 其余连接参数（主机、端口、库名、Redis 库号）四套各有固定值，
已写在各自的 `application.yaml` 里，默认值就是本地环境，不需要你配任何环境变量。

`.env.local` 已被 `.gitignore` 排除，不会进仓库。
临时覆盖用：`DB_PASSWORD=xxx ./deploy/start-all.sh`（命令行优先于 `.env.local`）。

> 只有放到公网容器里时才需要额外的 `DB_HOST` / `REDIS_HOST` / `IMAGE_ROOT` /
> `IMAGE_BASE_URL`，而且这些在 `docker/docker-compose.yml` 里已经用锚点统一配好了，
> 服务级别只留行业差异的两项，见 `docker/.env.example`。

### 3. 打包后端

```bash
./deploy/rebuild-runtime.sh
```

一条命令完成：四套 `mvn package` → 复制 fat jar 到 `deploy/runtime` → 重新注入 Admin 静态资源。约 4 分钟。

> **改过 `application.yaml` 或 `sentry.yaml` 之后必须重跑这条命令。**
> `deploy/runtime` 里的 jar 是副本，不重打的话改动不生效，而且 Admin 页面会丢失。

### 4. 启动

```bash
./deploy/start-all.sh
# 停止： ./deploy/stop-all.sh
```

日志在 `deploy/logs/<jar>.log`。

---

## 四、验证

```bash
# 后台是否看得到数据（登录 → 拉会员/商品/订单三个列表）
python deploy/smoke-data.py

# 收银端链路（验证码 → 登录 → 收银台接口）
python deploy/smoke-cashier.py
```

`smoke-data.py` 的正常输出应为四套全部 OK，各列表条数：会员 60、商品 43-44、订单 80。

---

## 五、可选组件

### Electron 收银端

```bash
cd baharCashier
npm install --ignore-scripts     # 首次；加 --ignore-scripts 避开 esbuild 的 EBUSY 回滚
npm run dev:shop                 # 零售；另有 dev:car / dev:food / dev:health / dev:origin
```

默认 `dev` 指向本地零售（8081），`dev:origin` 是作者线上地址，不要误连。

### 会员端（uniapp）

四份源码都已按行业指向本地端口，用 HBuilderX 打开对应工程运行即可：

| 行业 | 源码位置 | 指向 |
|---|---|---|
| 零售 | `baharUniapp/` | 8081 |
| 汽车 | `baharCar/client/` | 8082 |
| 餐饮 | `baharCatering/baharUniapp/` | 8083 |
| 康养 | `baharHealth/uniapp-ui/` | 8084 |

**建议发行成 H5** 挂到站点下给客户看，不必走小程序（省掉 AppID 与审核）。

---

## 六、常见问题

**1. 启动报 `Public Key Retrieval is not allowed`**
不是 allowPublicKeyRetrieval 的问题，**是密码不对**。检查是否传了 `DB_PASSWORD`、
`.env.local` 是否在 `deploy/` 下。
另一种情况：**MySQL 还没就绪**（刚开机时服务仍在启动）就拉起了应用，
等 MySQL 能连上后重启即可。

**2. 端口不是 8081-8084**
IDE 会往环境注入 `SERVER__PORT`（如 16713），Spring Boot 的宽松绑定会把它当成
`server.port`。启动脚本已显式传 `--server.port` 并清空该变量来规避。

**3. 接口全部 `AccessDeniedException`**
`t_source` 权限表为空。执行 `06-init-permission.sql`。

**4. 列表能打开但一条数据都没有**
多半是新增列的存量行为 NULL，被 `is_staff='N'` 这类等值过滤挡掉了。
执行 `07-backfill-null-columns.sql`。

**5. Admin 页面 404**
jar 被重新打包过但没重新注入 Admin 资源。跑 `python deploy/admin/patch_jars.py`。

**6. `deploy/runtime` 里的 jar 突然不见了**
IDEA 持有后端工程，reimport 会触发 clean 删掉 `target/*.jar`。
所以运行用的 jar 统一放 `deploy/runtime`，不要把 `target/` 当运行目录。

---

## 七、目录说明

```
deploy/
├── runtime/            四个运行 jar（bahar-shop / car / food / health）
├── logs/               启动日志与 pid
├── db/                 建库、补表、权限、演示数据脚本（01-08）
├── admin/              后台 SPA 源码 + patch_jars.py（注入 jar）
├── docker/             公网部署（compose + nginx + 部署文档）
├── start-all.sh        启动四实例
├── stop-all.sh         停止四实例
├── build-all.sh        四后端编译/打包
├── rebuild-runtime.sh  打包 + 复制 + 注入 Admin（改配置后必跑）
├── smoke-data.py       后台数据冒烟
└── smoke-cashier.py    收银端链路冒烟
```

> `deploy/` 自身是一个独立 git 仓库（私有：newdawn19/bahar-deploy），
> 顶层 `D:/git-double/bahar` 不是 git 仓库。

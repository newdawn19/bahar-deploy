# 访问清单（启动命令 · 地址 · 账号）

四套演示实例 + 三端入口的完整清单。**仅供本地演示使用，勿外传。**

---

## 一、先起服务（四套后端）

```bash
cd D:/git-double/bahar
./deploy/start-all.sh      # 起四套；停止用 ./deploy/stop-all.sh
```

启动后会逐个报告"就绪 / 失败"，失败直接打印报错。四套都起来约 1 分钟。

前置：MySQL（3306）与 Redis（6379）必须在运行——**Redis 不通会直接启动失败**。

---

## 二、后台管理端（浏览器打开）

| 行业 | 地址 | 账号 | 密码 |
|---|---|---|---|
| 零售 | http://127.0.0.1:8081/admin/index.html | `bahar` | `123456` |
| 汽车美容 | http://127.0.0.1:8082/admin/index.html | `bahar` | `123456` |
| 餐饮 | http://127.0.0.1:8083/admin/index.html | `bahar` | `123456` |
| 康养美业 | http://127.0.0.1:8084/admin/index.html | `bahar` | `123456` |

登录需要图形验证码（验证码走 Redis，所以 Redis 必须通）。

四套各有一个主题色，用来确认自己进的是哪套：零售蓝 / 汽车绿 / 餐饮橙 / 康养紫。

---

## 三、会员端（uni-app，四份源码）

用 HBuilderX 打开对应工程运行即可，配置已指向本地对应端口：

| 行业 | 源码目录 | 指向后端 |
|---|---|---|
| 零售 | `baharUniapp/` | 8081 |
| 汽车美容 | `baharCar/client/` | 8082 |
| 餐饮 | `baharCatering/baharUniapp/` | 8083 |
| 康养美业 | `baharHealth/uniapp-ui/` | 8084 |

**登录方式**：手机号 + 密码（不是后台那个账号）。

| 项 | 值 |
|---|---|
| 手机号 | `13800100001` ~ `13800100050`（新生成，50 个）<br>`13800000001` ~ `13800000010`（原有，10 个） |
| 密码 | `123456` |

常用几个：`13800100001`（张伟）、`13800100002`（王芳）、`13800100003`（李娜）、`13800100004`（刘洋）。

> 想让客户直接看，建议**发行成 H5** 挂到站点下，省掉小程序 AppID 与审核。

---

## 四、收银端（Electron 桌面端）

```bash
cd baharCashier
npm run dev:shop      # 零售，连 8081
npm run dev:car       # 汽车美容，连 8082
npm run dev:food      # 餐饮，连 8083
npm run dev:health    # 康养美业，连 8084
```

`npm run dev` 默认等于 `dev:shop`。**不要跑 `dev:origin`**，那是作者线上地址。

| 项 | 值 |
|---|---|
| 账号 | `bahar` |
| 密码 | `123456` |

（与后台同一套账号，走 `backendApi/login/doLogin`。）

首次运行需 `npm install --ignore-scripts`（已装过则跳过）。

---

## 五、中间件

| 组件 | 地址 | 账号 | 密码 |
|---|---|---|---|
| MySQL | 127.0.0.1:3306 | `root` | `rootAdmin@0731` |
| Redis | 127.0.0.1:6379 | — | 无密码 |

四个库：`bahar-db`、`bahar-car`、`bahar-catering`、`bahar-health`。
Redis 四套分别用 db 0 / 1 / 2 / 3。

> MySQL 的口令写在 `deploy/.env.local`（未入库）。改了口令记得同步改那里。

---

## 六、数据规模（各库）

| 类型 | 数量 |
|---|---|
| 会员 | 60 |
| 商品 | 43-44 |
| 订单 | 80 |
| 订单明细 | 约 190 |
| 充值流水 | 20 |
| 积分流水 | 27 |

---

## 七、快速自检

```bash
# 后台是否看得到数据（登录 → 拉会员/商品/订单三个列表）
python deploy/smoke-data.py

# 收银端链路（验证码 → 登录 → 收银台接口）
python deploy/smoke-cashier.py
```

---

## 八、常见问题的入口

- 起不来 / 报 `Public Key Retrieval is not allowed` → MySQL 没就绪或口令不对
- 端口不是 8081-8084（IDEA 启动时）→ IDEA 注入了 `SERVER__PORT`，在 Run Configuration 里显式指定 `SERVER_PORT`
- 接口全 `AccessDeniedException` → 权限表为空，执行 `db/06-init-permission.sql`
- 列表打开但没数据 → 新增列是 NULL，执行 `db/07-backfill-null-columns.sql`
- 更多见 `LOCAL-DEPLOY.md`

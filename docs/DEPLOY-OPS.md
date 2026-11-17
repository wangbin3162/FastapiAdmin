# 部署与运维

> 生产部署、备份、凭据与巡检。凭据与不可逆操作的红线见 [`AGENTS.md`](../AGENTS.md)。Docker 细节见 [`docker/README.md`](../docker/README.md)。
> 本文由原 `README.md` 的「部署说明 / 运维手册」与 `SKILL.md` §10、§13 迁移而来。

## 0. 部署边界

- **聊天边界**：内部聊天定位为**轻量内部沟通**，仅支持纯文字消息，**不含文件传输、撤回、已读回执、多端同步等 IM 能力**；如有强 IM 需求，请对接企业微信 / 钉钉 / 飞书等成熟产品。随时可在 `ENABLED_MODULES` 中移除 `chat` 停用。
- **单实例部署**：实时功能（内部聊天 WebSocket、定时任务调度器）基于单实例内存连接与本地调度实现，请以**单实例方式**部署。如需水平扩展，请自行引入 Redis Pub/Sub 或消息队列。
- **密钥安全**：所有第三方密钥（AI、云存储等）请配置在 `backend/env/.env.*` 环境变量中，**切勿提交到仓库或写入数据库**。
- **数据库迁移**：正式环境请使用 Alembic 迁移（`uv run alembic upgrade head`）管理表结构变更，`create_all` 仅用于首次初始化的兜底。

## 环境事实

- 当前可用的对象存储测试服务只有 **MinIO S3**；FTP/FTPS、SFTP、OBS、OSS、COS 没有测试环境，不作为本轮集成验收项。
- 生产：`https://service.fastapiadmin.com`，健康检查 `/api/v1/monitor/health/check`，Web `/web/`。
- 生产当前 `DEMO_ENABLE=true` 时会统一拦截写操作并返回“演示环境，禁止操作”；测试写接口前先确认环境，不要把该返回误判为代码故障。


## 生产部署与备份

- 部署前必须确认并备份：后端源码、`docker/nginx/web`、数据库 dump；
- 生产备份目录：`/home/FastapiAdmin/backups/release-<时间戳>/`；
- 部署后验证：health、web、登录、关键列表、调度器日志；
- 生产是演示模式时，写操作/导出被拦截是配置行为；
- 不把生产凭据、dump、密钥写入仓库。


## 1. 架构与目录

| 组件 | 说明 | 对外端口 |
| --- | --- | --- |
| nginx | TLS 终止、静态站点、反向代理 `/api/v1` | 80 / 443 |
| backend | FastAPI（uvicorn，1 worker，非 root 运行 uid=1000） | 仅 127.0.0.1:8001 |
| postgres | PostgreSQL 16，数据卷 `postgres_data` | 仅 127.0.0.1:5432 |
| redis | Redis 7（会话/缓存/限流） | 仅 127.0.0.1:6379 |

服务器布局（`/home/FastapiAdmin`）：

```
docker/                     # 唯一部署目录，不含业务源码
├── docker-compose.yaml     # 服务编排（端口仅 127.0.0.1，密钥由 .env 注入）
├── docker-compose.override.yaml  # nginx 版本固定 + 缓存配置挂载 + ACME 目录
├── .env                    # 真实凭据（600，不入库）
├── .env.example            # 占位模板（入库）
├── backend/Dockerfile      # 源码构建路径（正式部署不用它）
├── nginx/
│   ├── nginx.conf          # 站点配置（含文档封堵、隐藏文件拒绝、ACME 放行）
│   ├── cache-headers.inc   # 静态资源长缓存片段
│   ├── acme/               # ACME http-01 校验目录
│   ├── ssl/                # 证书与私钥（600，不入库）
│   └── {web,app,docs}/dist # 三端静态成品（由本地构建后上传）
└── postgres/ redis/        # 初始化 SQL 与 redis.conf
backups/                    # 部署前自动备份（每类保留 5 份）
```

仓库侧：`deploy.sh`（本机执行的成品部署脚本）、`backend/requirements/`（依赖分组）、`.github/workflows/`（CI）。

---

## 2. 日常部署

在本机仓库根目录执行（需要本机可免密 SSH 到服务器、且本机 Docker 可用——`colima start`）：

```bash
./deploy.sh web        # 构建并部署 Web 管理后台
./deploy.sh app        # 构建并部署移动端 H5
./deploy.sh backend    # 本地构建 PostgreSQL 版镜像 → 传输 → 只重建 backend
./deploy.sh all        # 三样全发
./deploy.sh verify     # 公网四端验证
./deploy.sh backups    # 列出服务器备份
./deploy.sh prune      # 轮转清理旧备份与旧镜像
./deploy.sh rollback web|app|backend
```

要点：

- **服务器不接收源码、不执行构建**：后端以 `docker save → ssh → docker load` 交付镜像，前端以 tar 管道交付成品。
- 每次部署前自动备份到 `backups/<标签>-<时间戳>`，备份失败即中止，不会带着假备份上线。
- 只重建变化的容器；PostgreSQL/Redis/Nginx 不受影响。
- MySQL 版本镜像：`./deploy.sh backend-mysql`（**只构建与自检，不切换**），仅在需要 MySQL 时使用，需同步改 compose 的数据库服务与连接配置。

---

## 3. 密钥与口令

| 项 | 位置 | 说明 |
| --- | --- | --- |
| `SECRET_KEY` | 服务器 `docker/.env` | JWT 签名密钥，64 位 hex，随机生成 |
| `DATA_ENCRYPTION_KEY` | 服务器 `docker/.env` | 落库敏感数据加密主密钥 |
| `DATA_ENCRYPTION_OLD_KEYS` | 服务器 `docker/.env` | 轮换前的旧密钥，仅用于解密历史密文 |
| 种子账号口令 | 服务器 `/root/.fa-seed-passwords`（600） | `super`/`admin`/`user`，登录后请自行修改并删除该文件 |

**轮换密钥的正确步骤**（不可跳步，否则历史密文无法解密）：

1. 把当前 `DATA_ENCRYPTION_KEY`（未设置时取当前 `SECRET_KEY`）追加到 `DATA_ENCRYPTION_OLD_KEYS`；
2. 生成新值：`openssl rand -hex 32`，写入 `SECRET_KEY` / `DATA_ENCRYPTION_KEY`；
3. `docker compose up -d --force-recreate backend`；
4. 验证历史密文仍可解密（例如存储源口令），再删除 `OLD_KEYS` 中不再需要的旧值。

> 注意：更换 `SECRET_KEY` 会使已签发的令牌全部失效，用户需重新登录。

---

## 4. 运行状态与巡检

- **每日巡检**：`systemctl list-timers fa-health-check.timer`（每天 08:30，带 5 分钟随机延迟）
- 巡检内容：4 个容器健康、`/api/v1/monitor/health/check` 与 `/web/`、`/app/` 可用性、证书剩余天数、磁盘、swap、备份与镜像堆积
- 结果：`/var/log/fa-health.log`；有告警时写入 syslog（`journalctl -t fa-health`）且服务退出码非 0
- 手动执行：`systemctl start fa-health-check.service && tail -n 30 /var/log/fa-health.log`

常用排查命令：

```bash
cd /home/FastapiAdmin/docker
docker compose ps
docker logs --tail 100 backend
docker inspect backend --format '{{.State.Health.Status}}'
ss -tlnp | grep docker-proxy      # 确认对外只有 80/443
```

---

## 5. 证书

- 当前证书：`docker/nginx/ssl/server.pem`（`CN=service.fastapiadmin.com`），由巡检脚本监控到期天数
- 续期（重新签发后）：替换 `server.pem` 与 `server.key` → `docker exec nginx nginx -s reload`
- 已放行 ACME http-01 校验路径（`/.well-known/acme-challenge/` → `docker/nginx/acme`），如需切换到 acme.sh 自动续期，把校验文件写入该目录即可，无需再改 nginx 配置

---

## 6. 配置取值格式（踩过的坑）

`.env` / compose 里的取值格式取决于应用侧字段类型：

| 类型 | 写法 | 例子 |
| --- | --- | --- |
| `str`（应用内部再按逗号拆） | 逗号分隔字符串 | `PROD_CORS_ORIGINS=https://a.com,https://b.com` |
| `list[str]`（pydantic-settings 直接解析） | **必须 JSON 数组字面量** | `OAUTH_ALLOWED_HOSTS=["service.fastapiadmin.com","*.fastapiadmin.com"]` |

把 `list[str]` 字段写成逗号分隔字符串会让应用**启动期抛 `SettingsError`**，容器不断重启、网关返回 502。2026-10-04 的部署事故就是这个原因（已修复并在 compose 默认值里固化 JSON 形态）。

排查方式：`docker logs --tail 40 backend`，若看到
`pydantic_settings.exceptions.SettingsError: error parsing value for field "XXX" from source "EnvSettingsSource"`，
就是该字段的取值格式与类型不匹配。

## 7. 凭据轮换（生产）

轮换对象：PostgreSQL 用户 / Redis。三者都通过 `docker/.env` 注入，且
**镜像内不得包含任何口令**（`deploy.sh` 在构建上下文里剔除
`DATABASE_PASSWORD / REDIS_PASSWORD / SECRET_KEY / DATA_ENCRYPTION_KEY` 等键，
仅保留主机名、端口等非敏感项——审计 B3 的根治）。

标准步骤（约 1 分钟中断窗口，顺序不可颠倒）：

```bash
cd /home/FastapiAdmin/docker
cp -a .env ".env.bak-rotate-$(date +%Y%m%d-%H%M%S)"   # 先备份，便于回滚

# 1) 改数据库口令（用 stdin 传 SQL，避免口令出现在命令行历史/ps）
NEW=$(openssl rand -base64 36 | tr -d '/+=' | cut -c1-30)
docker exec -i postgres psql -U postgres <<SQL
ALTER USER postgres WITH PASSWORD '$NEW';
SQL

# 2) 同步写入 .env（键名：POSTGRES_PASSWORD）
# 3) 重建引用该值的容器：postgres → redis → backend
#    注意：postgres/redis 的健康检查命令内插了 .env 值，必须一并重建，否则健康检查会一直失败
docker compose up -d --force-recreate postgres && sleep 20
docker compose up -d --force-recreate redis
docker compose up -d --force-recreate backend

# 4) 验证：旧口令必须被拒（PostgreSQL 报认证失败 / Redis 报 WRONGPASS），新口令可用，健康检查 db_status/redis_status = 1
```

排查提示：`docker exec -i` 会让容器内进程读走脚本自身的 stdin（若脚本经 `bash -s` 传入，
后续步骤会被吞掉）——务必加 `</dev/null` 或改用 `-e` 直传。

## 8. 已知遗留问题

当前覆盖基线与剩余缺口见 [`docs/COVERAGE-PLAN.md`](./COVERAGE-PLAN.md)。仍需关注：

1. 会话失效机制：停用/删除/改密后旧会话仍有效（最长 7 天），需应用侧继续改造；
2. 数据权限注入完整性：删除/清空/改状态等路径需继续核验；
3. 前端 i18n、通知状态枚举与后端语义一致性；
4. 后端覆盖仍为约 63%，`gencode` 生成写入/同步、OAuth/微信登录、AI 主流程、调度器对账和前端全源码仍未完成；
5. 外部存储仅验证 MinIO/S3；FTP/SFTP/OBS/OSS/COS 当前无测试服务，未纳入本轮验收。

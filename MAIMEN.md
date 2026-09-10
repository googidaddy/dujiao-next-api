# 麦门全栈维护线

此分支从官方 v1.4.7 的 `47cc6207c6796ccfda0526a3708be39e1b59eba3` 建立，源码来源及工具链记录在 [upstream.json](ops/maimen/upstream.json)。后端业务保持官方基线。2026-09-11 按商城部署需求定制前端：沿用麦门商店名称，移除项目推广链接、广告位和默认品牌图标，保留源码许可证及必要的法律说明。后台移除上游二进制覆盖更新入口，后续升级统一通过本分支 CI 和固定 digest 镜像发布。

当前 GitHub 仓库是公开 fork。仅提交源码、构建流程和无密钥模板；实际配置、数据库、卡密、用户数据、日志和备份保存在部署目录及受限存储中。

## 分支与日常开发

- `origin`：`git@github.com:googidaddy/dujiao-next-api.git`，新维护分支 `maimen-fullstack`。
- `upstream`：官方 `https://github.com/dujiao-next/dujiao-next.git`，仅用于获取上游更新；本地 push URL 设为 `DISABLED`。
- 原 `main` 和旧 `maimen` 分支继续保留；新商城使用 `maimen-fullstack` 独立发布。
- 前台在 `frontend/user/`，后台在 `frontend/admin/`，后端业务在 `internal/modules/`。一次界面定制单独提交，后续升级时核对保留情况。

开发前准备 `.nvmrc` 指定的 Node 24.11.1、pnpm 10.34.3 和 `go.mod` 指定的 Go 1.26.5；也可以使用官方 Dockerfile 的完整构建环境。macOS 的 arm64 开发环境与当前生产 linux/amd64 区分记录。

```bash
nvm install
nvm use
(cd frontend/admin && pnpm install --frozen-lockfile && pnpm test && pnpm build:fullstack)
(cd frontend/user && pnpm install --frozen-lockfile && pnpm test && pnpm build)
go vet ./...
go test ./...
python3 ops/maimen/scripts/check_templates.py
```

前后端本地联调使用独立测试配置和数据库。不要把生产数据库连接放到本地开发配置；新版启动和 `--help` 都可能先执行数据库迁移。

## 镜像发布

[maimen-fullstack workflow](.github/workflows/maimen-fullstack.yml) 在该维护分支 push 时验证 Go、两个前端和有效 Compose 隔离配置。通过后，按同一个 commit 构建 linux/amd64 镜像，在无网络、临时 SQLite 环境检查 API、前台、动态后台路径及嵌入资源，再发布到 GHCR。

- 镜像仓库：`ghcr.io/googidaddy/dujiao-next-fullstack`。
- 构建标签：`fullstack-<完整源码 SHA>`；不覆盖旧 API 镜像仓库或移动的 latest 标签。
- 部署使用 workflow 输出的 `仓库@sha256:...`，同时记录源码 SHA、目标平台、验证结果。
- workflow 的成功状态及发布 digest 需要实际核对；配置文件存在不等于已经构建成功。
- 保留上游 Release workflow，但限制其发布任务只在官方仓库执行；本维护线由自己的 workflow 发布容器。

仅推送新维护分支，不推送上游版本 tag：

```bash
git push -u origin maimen-fullstack
```

GitHub Actions 仅发布应用镜像，不持有服务器 SSH、支付或数据库凭据，也不自动部署生产。

## 独立部署与演练

部署模板在 [ops/maimen](ops/maimen/)。将 `compose.yml`、`compose.rehearsal.yml` 和 `.env.example` 复制到明确的新目录；应用源码目录与运行数据目录分开。准备 `config/`、`data/postgres/`、`data/redis/`、`data/uploads/` 和 `data/logs/`，按实际服务设置权限。

- PostgreSQL 16.14、Redis 7.4.9 使用已核实的原版本 digest；新 PG / Redis 实例使用独立密码。
- 目标配置由原配置合并生成，保留原应用密钥和 JWT 密钥，替换数据库、Redis 连接及目标代理地址。恢复既有管理员时将 bootstrap 用户名 / 密码留空。
- 配置文件只读挂载；数据目录必须事先存在，Docker 不自动创建猜测的挂载目录。
- API / User / Admin 合并为 `app` 服务，端口仅绑定 `127.0.0.1`；PG、Redis 不发布宿主机端口。
- `app` 使用显式 profile，默认启动数据服务不会连带触发应用迁移。
- 本编排只有商城的 app / postgres / redis，不包含延期的 EPUSDT / BEpusdt。

隔离演练必须同时使用 `compose.rehearsal.yml`、独立目录和独立 project。该覆盖文件采用 internal 网络、API 模式、无自动重启及资源上限；首次启动前仍需在副本禁用 / 替换支付、SMTP、Telegram 和其他真实外联设置，并实测网络无法对外连接。

在新的演练目录中，先启动数据服务，完成逻辑恢复和基线核对后，再显式启动 app：

```bash
docker compose -p maimen-v147-rehearsal -f compose.yml -f compose.rehearsal.yml up -d postgres redis
# 在此完成空库恢复、独立配置、uploads 和基线检查。
docker compose -p maimen-v147-rehearsal -f compose.yml -f compose.rehearsal.yml --profile app up -d app
```

停止和重启均点名当前 project 的相关服务。旧部署含延期网关，正式切换时不能整组 down 或重启 Docker。Nginx 示例仅供合并审阅，不能直接覆盖现有 TLS、真实 IP、后台访问控制或回调规则。

镜像 smoke test 只验证新镜像能运行，并不能代替 PostgreSQL 真实备份恢复、历史游客凭据、支付、库存、队列和完整回滚演练。旧站在准备和演练期间继续在线；正式切换须停写、取得最终 T0 恢复集并重新恢复，不能把过期的演练数据库上线。

## 后续升级

每次升级在独立分支获取明确的官方版本，核对发行说明、schema、迁移和工具链后合并上游；不要把 fork 的移动 main 直接当作生产版本。解决定制冲突并通过检查后再合入 `maimen-fullstack`，由同一条发布链生成新镜像。

升级时同步更新 `ops/maimen/upstream.json`、`.nvmrc`、workflow 中的版本标识和必要的部署说明，记录源码 SHA 与镜像 digest。纯前端展示修改沿用运行数据，但仍需完成前端测试、全栈构建和镜像验证。

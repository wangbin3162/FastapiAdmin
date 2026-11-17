# Lessons — 错题本

本文件记录**近期真正踩过的坑**，以及能拦住它的规则。**修改代码前阅读相关条目。**

每条错题被独立踩到 **3 次**，就把它移进 [`docs/CODE-STANDARDS.md`](docs/CODE-STANDARDS.md) 变成硬规矩，从这里删掉。本文件故意易腐，只装还没站住的东西。

**健康体量：≤ 5 条错题。** 数「## 错题」下的二级标题条数（证据较长，限条数不限行数）：

```bash
awk '/^## 错题/{f=1;next} /^## 毕业记录/{f=0} f&&/^### /{n++} END{print n+0}' LESSONS.md
```

初始条目来自原 `SKILL.md` 的历史记录，复发次数从 1 起算；日期以提交为准。

---

## 错题

### 源码已修 ≠ 部署已修

**前端源码修复后，必须重建并同步三份 dist，并在产物里核对特征字符串，才能说「已修」。**
- 症状：AI chat 重复出现「连接成功」，源码已修仍复现。
- 根因：`frontend/web/dist`、`docker/nginx/web/dist`、`backend/dist` 三份预构建副本不入库却被打进部署，停在修复前。
- 证据：源码提交 `e39a369b` 已修，三份 dist 仍是旧包（见 `docs/DEV-GUIDE.md`「前端产物验证」）。
- 复发 1 次
- ✅ 做对了：`grep` 产物里的 `readyState` 守卫，确认含 `!== WebSocket.CLOSED`。

### 连接类资源与缓存页的生命周期

**带 WebSocket/定时器/全局监听的页面，必须在 `onActivated`/`onDeactivated` 释放与恢复，不能只靠 `onUnmounted`；守卫要覆盖 CONNECTING。**
- 症状：登出→登录后出现多条 ws、多条「连接成功」。
- 根因：只挡 `OPEN`，CONNECTING 期间重入会覆盖旧引用；KeepAlive 下 `onUnmounted` 不会触发。
- 证据：`docs/DEV-GUIDE.md`「KeepAlive 缓存与连接类资源」。
- 复发 1 次

### 路由出口 KeepAlive 只能一层

**不要给目录路由挂壳组件，不要给 KeepAlive 加 `:max`。**
- 症状：切换菜单时接口重复请求，同一页面被重复挂载。
- 根因：壳组件（`NestedRouterParent`）随缓存存活多份；`:max` 的 LRU 在标签仍打开时挤掉页面。
- 证据：`docs/DEV-GUIDE.md` 同节；`layouts/fa-page-content/index.vue`。
- 复发 1 次

### 静默失败的启动期配置

**挂载与检查必须使用同一路径常量；改完生成代码/模块必须重启后端；env 的 `list[str]` 字段必须写 JSON 数组。**
- 症状：`register_frontend` 首次请求才 500；新生成模块不生效且无报错；`SettingsError` 导致容器重启、网关 502。
- 根因：检查用 `path_conf.FRONTEND_DIST_DIR`、挂载却硬编码；动态路由只在启动时发现；list 字段写成逗号串。
- 证据：`docs/DEV-GUIDE.md`「已知注意点」；`docs/DEPLOY-OPS.md`「配置取值格式」（2026-10-04 部署事故）。
- 复发 1 次

---

## 毕业记录

已毕业进 [`docs/CODE-STANDARDS.md`](docs/CODE-STANDARDS.md) 的条目（这里只留指针）：

- （暂无）

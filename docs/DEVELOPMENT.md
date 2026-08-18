# VibeEmber 开发文档

> 返回 [社区介绍](../README.md)

面向 Vibe Coder、独立开发者和小型创业团队的产品首发与冷启动互助社区。

VibeEmber 希望解决一个很具体的问题：很多产品并不是没有价值，只是在发布时没有第一批真实用户、体验反馈和初始曝光。在这里，开发者可以展示作品、帮助其他产品完成真实体验，再为自己的项目获得冷启动支持。

> 先一起跨过冷启动，然后各凭本事起飞。

## 在线体验

[https://wenxinxu.com/VibeEmber/](https://wenxinxu.com/VibeEmber/)

## 已实现功能

- 产品展示、分类筛选与搜索
- 开发者注册、登录和安全退出
- 真实项目投稿与持久化存储
- 投稿状态查询：审核中、已上线、已驳回
- 管理员审核工作台
- 通过审核后自动公开展示
- 驳回原因和审核操作记录
- 互助任务、火苗积分和贡献榜的界面原型
- 桌面端和移动端响应式布局
- 针对低配置服务器的静态构建与轻量 API

## 技术架构

```text
浏览器
  ├─ React 静态前端
  └─ /VibeEmber/api/*
          ↓
        Nginx
          ↓
  Python WSGI 轻量 API
          ↓
        SQLite
```

| 部分 | 技术 |
| --- | --- |
| 前端 | React 19、TypeScript、Vite / Vinext |
| 图标 | Lucide React |
| 后端 | Python 3 标准库 WSGI，无第三方运行时依赖 |
| 数据库 | SQLite（WAL 模式） |
| Web 服务 | Nginx |
| 进程管理 | systemd |

前端使用纯静态构建产物，服务器无需安装 Node.js 依赖或参与编译。API 只使用 Python 标准库，适合内存较小的服务器。

## 项目结构

```text
app/
  page.tsx                 # 主页与交互逻辑
  globals.css              # 全局样式和响应式布局
static/
  index.html               # 静态版入口
  src/main.tsx             # 静态版 React 挂载入口
server/
  app.py                   # 账号、投稿和审核 API
  vibe-ember-api.service   # systemd 服务配置
  *.conf                   # Nginx 参考配置
vite.static.config.ts      # /VibeEmber/ 子路径静态构建配置
```

## 本地开发

### 环境要求

- Node.js `>= 22.13.0`
- Python `>= 3.10`

### 启动前端

```bash
npm install
npm run dev
```

### 启动 API

API 不需要安装 Python 依赖。开发环境可参考以下变量启动：

```bash
PORT=8790 \
BASE_PATH=/ \
COOKIE_SECURE=0 \
ALLOWED_ORIGINS=http://localhost:3000 \
BOOTSTRAP_ADMIN_EMAIL=admin@example.com \
python3 server/app.py
```

API 健康检查：

```bash
curl http://127.0.0.1:8790/api/health
```

> 注：生产环境中前端与 API 通过 Nginx 的 `/VibeEmber/api/` 路径整合。

## 构建

### Vinext / Sites 构建

```bash
npm run build
```

### 普通服务器静态构建

```bash
npm run build:static
```

构建结果会生成在 `static-dist/` 中。只需把该目录下的产物交给 Nginx 托管，不要在低配置服务器上执行 `npm install` 或构建。

## 生产环境配置

`server/vibe-ember-api.env.example` 提供了环境变量示例：

| 变量 | 说明 |
| --- | --- |
| `HOST` | API 监听地址，生产环境建议使用 `127.0.0.1` |
| `PORT` | API 监听端口，默认 `8790` |
| `BASE_PATH` | Cookie 所属站点路径，默认 `/VibeEmber` |
| `DATA_DIR` | SQLite 数据目录 |
| `DB_PATH` | SQLite 数据库文件路径 |
| `BOOTSTRAP_ADMIN_EMAIL` | 指定可注册为管理员的邮箱 |
| `ALLOWED_ORIGINS` | 允许发起写操作的站点来源，多个值用逗号分隔 |
| `COOKIE_SECURE` | 生产环境必须设为 `1` |
| `ACCESS_LOG` | 是否输出 API 访问日志 |

第一次部署时，使用 `BOOTSTRAP_ADMIN_EMAIL` 指定的邮箱注册，该账号会自动获得管理员权限。其他邮箱默认为普通开发者。

## 安全设计

- 密码使用 PBKDF2-SHA256 加盐哈希，不保存明文
- 会话令牌仅以 SHA-256 哈希形式存入数据库
- Cookie 使用 `HttpOnly`、`SameSite=Lax` 和生产环境 `Secure`
- 写操作需要 CSRF Token 校验
- 注册和登录包含基础频率限制
- 管理员权限由服务端校验，不依赖前端隐藏
- 项目默认为待审核，只有审核通过后才会公开

请勿将生产环境配置、邮箱授权码、SSH 密钥、服务器密码或 SQLite 数据库提交到 Git。

## 数据表

- `users`：用户账号、密码哈希与角色
- `sessions`：登录会话、CSRF Token 与过期时间
- `projects`：项目投稿、所属用户与审核状态
- `review_audit`：审核人、审核动作、原因和时间

## 当前边界

以下功能还未完成，欢迎继续建设：

- 邮箱验证与忘记密码
- 项目 Logo 和截图上传
- 互助任务的真实数据化
- 火苗积分明细与防作弊规则
- 评论、收藏和站内通知
- 邮件通知与审核结果提醒

## 社区原则

VibeEmber 用于真实产品体验、有效反馈和联合推广，不鼓励机器刷量、虚假注册、刷广告收益或规避第三方平台规则。

互助解决的是产品从 0 到 1 的启动问题。能不能长期获得用户和收入，最终仍然取决于产品价值与运营能力。

## 贡献

欢迎通过 Issue 提交建议或问题。在提交 Pull Request 前，请确保：

```bash
npm run build
npm run build:static
python3 -m py_compile server/app.py
```

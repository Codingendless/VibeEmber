# VibeEmber 受限部署账号

服务器账号：`vibeember-deploy`

该账号只用于上传和部署 VibeEmber，不具有通用 sudo 权限，也不能修改服务器上的其他项目。

## 第一次使用

请在自己的电脑生成独立 SSH 密钥：

```bash
ssh-keygen -t ed25519 -f ~/.ssh/vibeember_deploy -C "vibeember-deploy"
```

把 `~/.ssh/vibeember_deploy.pub` 的一整行内容交给服务器管理员。私钥 `~/.ssh/vibeember_deploy` 只能保存在自己的电脑上，不能通过微信、邮件或 GitHub 发送。

## 部署静态前端

在本地项目目录执行：

```bash
npm ci
npm run build:static
tar -C static-dist -czf static.tar.gz .
scp -i ~/.ssh/vibeember_deploy static.tar.gz vibeember-deploy@SERVER:/home/vibeember-deploy/staging/static.tar.gz
ssh -i ~/.ssh/vibeember_deploy vibeember-deploy@SERVER sudo /usr/local/sbin/vibeember-deploy
```

## 部署 API

```bash
scp -i ~/.ssh/vibeember_deploy server/app.py vibeember-deploy@SERVER:/home/vibeember-deploy/staging/app.py
ssh -i ~/.ssh/vibeember_deploy vibeember-deploy@SERVER sudo /usr/local/sbin/vibeember-deploy
```

也可以先同时上传 `static.tar.gz` 和 `app.py`，再执行一次部署命令。

## 查看状态和日志

```bash
ssh -i ~/.ssh/vibeember_deploy vibeember-deploy@SERVER sudo /usr/local/sbin/vibeember-status
```

## 权限边界

该账号可以：

- 上传 `static.tar.gz` 和 `app.py` 到自己的暂存目录
- 发布 VibeEmber 新版本
- 重启 VibeEmber API
- 查看 VibeEmber API 状态和日志

该账号不能：

- 获得 root Shell
- 执行任意 sudo 命令
- 编辑 Nginx、SSH、systemd 或系统配置
- 修改其他网站和服务
- 读取 VibeEmber 的 SQLite 数据库或生产环境变量
- 使用 SSH 端口转发、代理转发、X11 或隧道

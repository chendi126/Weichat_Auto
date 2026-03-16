# 银河快报——公众号文章自动生成发布系统

这是一个基于 AI 的科技新闻和 GitHub 热门项目自动生成并发布到微信公众号的系统。它可以：

- 自动搜索科技新闻并生成文章
- 自动获取 GitHub 热门项目并生成推荐文章
- 自动发布到微信公众号
- 通过飞书机器人智能响应用户请求

---

## 目录

- [配置说明](#配置说明)
- [运行命令](#运行命令)
- [微信公众号配置](#微信公众号配置)
- [飞书机器人配置](#飞书机器人配置)

---

## 配置说明

所有配置都在 `config.yaml` 文件中，修改后保存立即生效。

### 1. 微信公众号配置

位置：`config.yaml` 中的 `wechat` 部分

```yaml
wechat:
  app_id: "你的AppID"        # 微信公众号AppID
  app_secret: "你的AppSecret" # 微信公众号AppSecret
  cover_image: "封面图片.png" # 文章封面图片
```

### 2. AI 大模型配置

位置：`config.yaml` 中

```yaml
# MiniMax（备用）
minimax:
  api_key: "你的API Key"
  model: "abab6.5s-chat"
  base_url: "https://api.minimaxi.com/v1"

# DeepSeek（用于生成新闻文章、GitHub 文章和7字总结）
deepseek:
  api_key: "你的API Key"
  model: "deepseek-chat"
```

### 3. 定时任务配置

位置：`config.yaml` 中的 `scheduler` 部分

```yaml
scheduler:
  enabled: true   # 是否启用定时发布
  hour: 8         # 定时发布小时 (0-23)
  minute: 0       # 定时发布分钟 (0-59)
```

### 4. 飞书机器人配置

位置：`config.yaml` 中的 `feishu` 部分

```yaml
feishu:
  app_id: "你的AppID"
  app_secret: "你的AppSecret"
  port: 5000       # 服务端口
```

### 5. AI 搜索配置（Tavily）

位置：`config.yaml` 中的 `tavily` 部分

```yaml
tavily:
  api_key: "你的Tavily API Key"
```

#### 获取 Tavily API Key

1. 访问 [Tavily 官网](https://www.tavily.com/)
2. 注册/登录账号
3. 进入「Dashboard」→「API Keys」
4. 点击「Create API Key」创建密钥
5. 复制密钥并填入配置

> **注意**：Tavily 提供免费额度，个人使用基本够用。

---

## 运行命令

### Windows

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 手动执行 AI 新闻生成
python src/main.py --now

# 手动执行 GitHub 热门生成
python src/github_main.py --now

# 以定时任务模式运行（每天自动发布）
python src/main.py --daemon

# 以定时任务模式运行 GitHub 热门
python src/github_main.py --daemon

# 启动飞书机器人服务
python src/feishu_server.py
```

或者使用脚本：

```bash
# 手动执行 AI 新闻
bash run.sh -n

# 手动执行 GitHub 热门
bash run.sh -g

# 定时任务模式运行 AI 新闻
bash run.sh -d

# 定时任务模式运行 GitHub 热门
bash run.sh -G

# 启动飞书机器人服务
bash run.sh -f
```

### Linux / 服务器

```bash
# 激活虚拟环境
source .venv/bin/activate

# 手动执行 AI 新闻
python src/main.py --now

# 手动执行 GitHub 热门
python src/github_main.py --now

# 以定时任务模式运行
python src/main.py --daemon

# 启动飞书机器人服务（后台运行）
nohup python src/feishu_server.py > feishu.log 2>&1 &
```

---

## 微信公众号配置

> **注意**：
> - 自动发布文章到**草稿箱**功能，需要在公众平台配置**IP白名单**
> - 自动**群发**功能需要**企业微信/企业公众号**（本项目暂未实现）

### 步骤 1：获取 AppID 和 AppSecret

1. 登录 [微信开发者平台](https://open.weixin.qq.com/)
2. 进入「设置与开发」→「基本配置」
3. 记录「公众号appID」和「公众号appsecret」

### 步骤 2：配置 IP 白名单（重要！）

1. 在「基本配置」页面找到「公众号设置」→「功能设置」
2. 点击「IP白名单」
3. 添加你的服务器公网 IP 地址
4. **必须配置白名单，否则无法自动发布到草稿箱**

### 步骤 3：在配置文件中填写

打开 `config.yaml`，找到 `wechat` 部分：

```yaml
wechat:
  app_id: "这里填入你的AppID"
  app_secret: "这里填入你的AppSecret"
  cover_image: "封面.png"  # 封面图片文件名
```

### 步骤 4：准备封面图片

将封面图片文件（如 `封面.png`）放在项目根目录下。

### 功能说明

| 功能 | 支持情况 |
|------|----------|
| 发布到草稿箱 | ✅ 需要配置IP白名单 |
| 自动群发 | ❌ 需要企业公众号 |

---

## 飞书机器人配置

### 步骤 1：创建飞书应用

1. 打开 [飞书开放平台](https://open.feishu.cn/)
2. 进入「应用开发」→「创建应用」
3. 填写应用名称，创建应用

### 步骤 2：获取 AppID 和 AppSecret

1. 进入应用设置页面
2. 点击「凭证与权限」→「获取凭证」
3. 记录 `App ID` 和 `App Secret`

### 步骤 3：配置权限

1. 进入「权限管理」
2. 添加以下权限：
   - 接收消息 → 接收消息
   - 发送消息 → 发送消息
   - 消息与群组 → 读取群组信息
   - 通讯录 → 读取组织架构

### 步骤 4：配置回调地址

1. 进入「事件订阅」
2. 点击「创建订阅」
3. 填写回调地址：`https://你的域名/feishu/callback`
4. 添加事件：
   - `im.message.receive_v1`（接收消息）

### 步骤 5：填写配置

打开 `config.yaml`，找到 `feishu` 部分：

```yaml
feishu:
  app_id: "这里填入你的AppID"
  app_secret: "这里填入你的AppSecret"
  port: 5000  # 你服务器暴露的端口
```

### 步骤 6：启动服务

```bash
# Linux 后台运行
nohup python src/feishu_server.py > feishu.log 2>&1 &

# Windows
python src/feishu_server.py
```

### 飞书机器人功能

- 发送「最新」或「新闻」：获取最新科技新闻
- 发送「GitHub」或「开源」：获取 GitHub 热门项目
- 发送任意关键词：搜索相关资讯

---

## 项目结构

```
projects/
├── config.yaml          # 配置文件（所有配置在这里）
├── run.sh               # 运行脚本
├── src/
│   ├── main.py          # 主程序（新闻生成）
│   ├── github_main.py   # GitHub 热门生成
│   ├── article_writer.py    # 新闻文章生成模块（含提示词）
│   ├── github_writer.py     # GitHub 文章生成模块（含提示词）
│   ├── feishu_bot.py        # 飞书机器人
│   ├── feishu_server.py     # 飞书服务
│   ├── wechat_publisher.py  # 微信发布
│   ├── scheduler.py         # 定时任务
│   └── config.py            # 配置加载
```

---

## 常见问题

### Q: 修改配置后需要重启吗？

不需要。程序每次运行都会读取 `config.yaml`，保存后立即生效。

### Q: 如何查看运行日志？

- 飞书机器人日志：`feishu.log`
- 新闻生成日志：查看程序输出

### Q: 定时任务不生效怎么办？

检查 `config.yaml` 中 `scheduler.enabled` 是否为 `true`。

### Q: 公众号发布失败怎么办？

1. 检查 AppID 和 AppSecret 是否正确
2. 检查是否已配置 IP 白名单
3. 查看日志中的具体错误信息

### Q: 如何获取服务器的公网 IP？

访问以下网站查看你的公网 IP：
- https://ip-api.com/
- https://whatismyipaddress.com/

### Q: 飞书机器人收不到消息怎么办？

1. 检查飞书应用是否已发布
2. 检查回调地址是否配置正确
3. 检查服务器防火墙是否开放对应端口
4. 查看 `feishu.log` 日志排查

### Q: 如何测试微信公众号配置是否正确？

```bash
python scripts/test_wechat_config.py
```

### Q: 文章生成失败怎么办？

1. 检查 AI（DeepSeek/MiniMax）API Key 是否正确
2. 检查 API 余额是否充足
3. 查看日志中的具体错误信息

### Q: 如何手动运行一次测试？

```bash
# 测试 AI 新闻生成
python src/main.py --now

# 测试 GitHub 热门
python src/github_main.py --now

# 测试飞书机器人（前台运行）
python src/feishu_server.py
```

### Q: 飞书机器人需要一直运行吗？

是的，飞书机器人需要保持运行才能接收消息。建议使用 `nohup` 或 `screen` 在后台运行。

### Q: 如何停止飞书机器人？

```bash
# 查看进程
ps aux | grep feishu_server

# 杀掉进程
kill <进程ID>
```

## 项目概述
- **名称**: AI科技新闻自动化发布工作流
- **功能**: 每日自动获取AI和科技行业的最新新闻，去重后编写成高质量文章，生成配图，并发布到「Spaceman的Ai圈子」微信公众号

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| search_news | `nodes/search_news_node.py` | task | 搜索AI和科技新闻 | - | - |
| filter_news | `nodes/filter_news_node.py` | task | 去重过滤新闻，排除已发布内容 | - | - |
| write_article | `nodes/write_article_node.py` | agent | 编写科技新闻文章 | - | `config/write_article_llm_cfg.json` |
| generate_image | `nodes/generate_image_node.py` | task | 生成文章配图 | - | - |
| publish_to_wechat | `nodes/publish_to_wechat_node.py` | task | 发布到微信公众号 | - | - |
| save_published | `nodes/save_published_node.py` | task | 保存已发布新闻到数据库 | - | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
无

## 技能使用
- 节点 `search_news` 使用技能 `web-search` - 搜索AI和科技新闻
- 节点 `write_article` 使用技能 `llm` - 编写高质量文章
- 节点 `generate_image` 使用技能 `image-generation` - 生成科技风格配图
- 节点 `publish_to_wechat` 使用技能 `wechat-official-account` - 发布到微信公众号
- 节点 `filter_news` 和 `save_published` 使用技能 `supabase` - 数据库存储和去重

## 微信公众号集成配置

### 配置步骤
1. **启用集成**：
   - 登录 Coze 平台项目管理页面
   - 进入「集成」→「微信公众号」
   - 点击「启用」按钮

2. **配置凭证**：
   - 填写微信公众号的 **AppID** 和 **AppSecret**
   - 保存配置

3. **获取凭证方法**：
   - 登录微信公众平台：https://mp.weixin.qq.com
   - 进入「设置与开发」→「基本配置」
   - 在「开发者ID」中可以看到 AppID
   - 点击「AppSecret」后的「重置」或「获取」按钮
   - 扫码验证后即可获得 AppSecret

4. **配置IP白名单**（重要）：
   - 在微信公众平台进入「设置与开发」→「基本配置」→「IP白名单」
   - 添加以下IP段：
     - `115.190.0.0/16`
     - `115.191.0.0/16`
     - `101.126.0.0/16`
   - 保存配置

### 诊断脚本
运行以下命令检查集成配置状态：
```bash
python scripts/diagnose_wechat_integration.py
```

### 常见错误及解决方法
| 错误码 | 错误信息 | 解决方法 |
|--------|---------|---------|
| 500 | Integration credential request failed | 检查是否在项目管理中启用了微信公众号集成 |
| 40164 | IP地址不在白名单中 | 在微信公众平台添加服务器IP段到白名单 |
| 48001 | api 功能未授权 | 检查公众号是否已获得草稿箱和发布接口权限 |
| 41001 | 凭证缺失 | 确认 AppID 和 AppSecret 配置正确 |

## 工作流说明

### 执行流程
1. **搜索新闻** (`search_news`): 使用网络搜索获取当天最新的AI和科技新闻（15条）
2. **去重过滤** (`filter_news`): 查询数据库中已发布的新闻URL，排除重复内容
3. **编写文章** (`write_article`): 使用大语言模型将过滤后的新闻整合成一篇高质量的综合文章，并应用**星际风格排版**
4. **生成配图** (`generate_image`): 根据文章内容生成科技风格的配图
5. **发布到公众号** (`publish_to_wechat`): 将文章和配图发布到微信公众号（需要配置集成凭证）
6. **保存记录** (`save_published`): 将发布的新闻URL和文章信息保存到数据库，用于后续去重

### 文章样式：科技新闻风格

**设计理念**：专业、现代、易读，让读者快速了解最新的AI和科技动态

**视觉特点**：
- 🌌 **深色背景**：深蓝渐变背景 (#0a0a1a → #1a1a2e → #16213e)
- 📐 **几何线条**：顶部和底部的渐变线条装饰
- ⭐ **星际点缀**：20颗发光的星星点缀在页面各处
- 🌅 **温暖光色**：金色(#ffd700)、橙色(#ff8c00)、红色(#ff6b6b)渐变
- 🎨 **大字号标题**：渐变色标题，吸引眼球

**页面元素**：
- **顶部标识**：`◆ Spaceman的Ai圈子 ◆`
- **标题区域**：渐变色标题 + 日期标识
- **内容区域**：大字号、高行距、两端对齐
- **底部标识**：`◆ 感谢阅读 ◆`

**内容风格**：
- 聚焦GitHub热门项目、AI大模型动态、科技圈新闻、鸿蒙发展等
- 专业而不晦涩，生动而不浮夸
- 使用场景代入、数据震撼等方式开头
- 深度解析技术趋势和影响

**适用场景**：微信公众号文章、网页展示、电子出版物

### 输入输出
- **输入**: 无（自动获取当天新闻）
- **输出**:
  - `article_title`: 文章标题
  - `article_content`: 文章内容（HTML格式）
  - `image_url`: 配图URL
  - `publish_result`: 发布结果
  - `save_result`: 保存结果

### 配置说明
- 大模型配置文件: `config/write_article_llm_cfg.json`
  - 模型: doubao-seed-2-0-pro-260215
  - 温度: 0.6（保证准确性和可读性）
  - 最大token: 32768
  - 系统提示词: 定义了科技新闻编辑的角色和文章编写规范
  - 内容方向: GitHub项目、AI大模型、科技圈动态、鸿蒙发展等

### 数据库表结构
```sql
CREATE TABLE published_news (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,              -- 新闻URL（用于去重）
    title TEXT,                     -- 新闻原标题
    article_title TEXT,             -- 生成的文章标题
    article_content TEXT,           -- 生成的文章内容
    image_url TEXT,                 -- 配图URL
    publish_result JSONB,           -- 发布结果
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 注意事项
1. **微信公众号集成**: 需要在项目设置中配置微信公众号集成凭证（AppID 和 AppSecret），否则发布会失败
2. **去重机制**: 通过新闻URL进行去重，确保每天发布的新闻不重复
3. **文章质量**: 使用专业的大模型编写，确保文章结构清晰、内容丰富、有深度见解
4. **配图风格**: 自动生成科技风格的配图，适合微信公众号封面

### 测试结果
工作流已成功测试，能够：
- ✅ 搜索最新的AI和科技新闻
- ✅ 有效去重，避免重复内容
- ✅ 生成高质量的综合文章
- ✅ 生成专业的科技风格配图
- ⚠️ 发布功能需要配置微信公众号集成凭证
- ✅ 保存记录到数据库，支持长期去重

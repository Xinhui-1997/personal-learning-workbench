# 个人学习工作台｜维护手册

这份文件的目的：即使完全找不到最初的 ChatGPT 对话，也能继续维护这个项目。

## 1. 项目在哪里

- GitHub 仓库：`Xinhui-1997/personal-learning-workbench`
- 在线网站：`https://xinhui-1997.github.io/personal-learning-workbench/`
- 前端托管：GitHub Pages
- 云端数据：Supabase
- 当前 Supabase 项目：`kemjqowxmyzauvbyebwg`
- 每日内容：ChatGPT 定时任务每天 05:30（Asia/Tokyo）生成并写入 `daily_cards`

## 2. 现在有 6 个模块

数据库里的 module 值：

- `task` → 今日小事
- `english` → Daily English
- `physics` → 每日物理
- `psych` → 每日心理
- `science` → 每日科普
- `poetry` → 每日诗词

每日诗词内容池在：`data/poetry_catalog.json`

## 3. 文件各自负责什么

### `index.html`
页面骨架。

适合修改：
- 顶部导航
- 日期区域
- 登录/账号弹窗
- 阅读规则放在哪里
- 新增静态区域

### `styles.css`
主要界面样式。

适合修改：
- 卡片大小
- 字体
- 间距
- 手机端布局
- 按钮和统计页

### `poetry.css`
每日诗词的独立颜色和样式。

### `app.js`
网站核心逻辑。

这里控制：
- 模块列表 `BASE`
- 日期切换
- 从 Supabase 读每天的卡片
- 完成/取消完成
- 进度条
- 统计页
- 来源页
- Realtime 同步

如果要新增模块，通常至少要同时修改：
1. `app.js` 的模块列表
2. Supabase 两张表的 module CHECK constraint
3. 每日生成任务的模块规则
4. 对应 CSS

### `auth-password.js`
邮箱 + 密码登录、设置密码、退出登录。

### `config.js`
前端连接 Supabase 的公开配置。

注意：这里只能放浏览器端可公开的 publishable/anon key，绝不能放 service role secret。

### `sw.js`
PWA 离线缓存。

只要增加了一个新的前端文件，例如 `new-module.css`，通常要把它加进 `APP_SHELL`，并把 CACHE 版本从 `v2` 改成 `v3`，否则手机可能长期看到旧页面。

### `manifest.webmanifest`
控制“添加到主屏幕”后的 App 名称、图标等。

### `.github/workflows/deploy-pages.yml`
GitHub Pages 自动部署。

每次 main 分支有新提交，GitHub Actions 会把列出的前端文件复制到 `_site` 并发布。

重要：新建前端文件后，除了在 HTML 中引用，还必须确认这里的 `cp ... _site/` 也包含它，否则仓库里有文件但线上网站没有。

### `data/poetry_catalog.json`
每日诗词候选库与选材规则。

可以直接继续添加：
```json
{"author":"作者","title":"作品名","type":"古词","priority":9}
```

现代诗要注意版权；仍受版权保护的作品不应把全文直接放进网站。

## 4. Supabase 数据结构

### `daily_cards`
每天的学习内容。

主要字段：
- `study_date`
- `module`
- `title`
- `body_html`
- `meta`
- `source_name`
- `source_url`
- `score`

唯一键：`(study_date, module)`

所以一天同一个模块只保留一张卡。

### `completion`
用户完成状态。

主要字段：
- `user_id`
- `study_date`
- `module`
- `completed`
- `updated_at`

唯一键：`(user_id, study_date, module)`

手机和电脑同步就是靠这张表 + Supabase Auth + Realtime。

## 5. 每日内容生成规则

当前定时任务每天日本时间 05:30 运行。

总体原则：
- 每天生成 6 个模块
- English 中英双语
- 物理 / 心理 / 科普中文优先
- 外部来源必须是真实可追溯的标题与 URL
- Score = 0.30 Quality + 0.20 Interesting + 0.20 Learnability + 0.15 Language fit + 0.10 Novelty + 0.05 Diversity
- 来源质量低于 80 淘汰
- 最近内容避免重复
- 每日诗词不要求网站更新，优先从经典文学库选择

如果日后要改“内容偏好”，优先改定时任务的 prompt，而不是改网页。

例如：
- 想让物理更专业 → 改每日任务的 physics 规则
- 想让诗词更偏宋词 → 改 poetry 规则 / `poetry_catalog.json`
- 想完全删除今日小事 → 同时改前端模块、数据库约束、生成任务

## 6. 最常见修改怎么做

### 只改颜色/布局
改 `styles.css` / `poetry.css`。

### 改阅读规则文字
改 `index.html` 里的 `languageNotice`。

### 改栏目名字
改 `app.js` 的 `BASE`。

### 新增一个栏目
不要只改页面。需要：
1. `app.js` 增加模块
2. CSS 增加颜色
3. Supabase `daily_cards` 和 `completion` 的 CHECK constraint 增加 module
4. 每日自动任务增加该模块的内容规则
5. 如新增独立 CSS/JS，更新 `deploy-pages.yml` 和 `sw.js`

### 修改每日诗词候选
直接改 `data/poetry_catalog.json`。

### 改登录方式
主要看 `auth-password.js` 和 `index.html` 登录框。

### 页面改了但手机还是旧的
检查：
1. GitHub Actions 是否部署成功
2. `deploy-pages.yml` 是否把新文件复制到 `_site`
3. `sw.js` 的 CACHE 版本是否升级
4. 手机彻底关闭 PWA 后重开，必要时清站点缓存

## 7. 如何确认某次修改是否上线

在 GitHub 仓库：

`Actions` → `Deploy PWA to GitHub Pages`

最新一条必须是绿色 Success。

然后打开：

`https://xinhui-1997.github.io/personal-learning-workbench/`

电脑可用 Ctrl+F5 强制刷新。

## 8. 不要把什么提交到 GitHub

不要提交：
- Supabase service role key
- 私人 API secret
- 邮箱密码
- 任何真实账户密码

`config.js` 里的 Supabase publishable/anon key 本来就是浏览器端使用，可以公开；真正敏感的服务端密钥不能放进去。

## 9. 如果未来让另一个 ChatGPT 接手

不要重新从头描述整个项目。

直接告诉它：

> 请接手我的 GitHub 项目 `Xinhui-1997/personal-learning-workbench`。先阅读 `README.md`、`MAINTENANCE.md`、`FUTURE_CHAT_PROMPT.md`，再检查当前 main 分支代码和 Supabase schema，然后根据我的新要求继续修改。不要凭以前聊天猜测，以仓库和数据库当前状态为准。

这样即使原对话完全丢失，也可以继续。

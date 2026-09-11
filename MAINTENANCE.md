# 个人学习工作台｜维护手册

这份文件的目的：即使完全找不到最初的 ChatGPT 对话，也能继续维护这个项目。

## 1. 项目在哪里

- GitHub 仓库：`Xinhui-1997/personal-learning-workbench`
- 在线网站：`https://xinhui-1997.github.io/personal-learning-workbench/`
- 前端托管：GitHub Pages
- 云端数据：Supabase
- 当前 Supabase 项目：`kemjqowxmyzauvbyebwg`
- 每日内容：ChatGPT 定时任务每天 05:30（Asia/Tokyo）生成并写入 `public.daily_cards`
- 周六提醒：每周六 08:00 读取当天 `weekend_read` 并发送；原则上不重新选文

## 2. 当前模块

常规每天 6 个模块：

- `task` → 今日小事
- `english` → Daily English
- `physics` → 每日物理
- `psych` → 每日心理
- `science` → 每日科普
- `poetry` → 每日诗词

星期六额外出现第 7 个模块：

- `weekend_read` → 周六短读

`weekend_read` 只在星期六计入当天进度和统计，其他日期不应显示，也不应进入完成率分母。

每日诗词内容池在：`data/poetry_catalog.json`。

## 3. 正式数据流

这个项目不是“每天重新生成 HTML”。正式流程是：

1. GitHub Pages 部署固定前端：`index.html` + CSS + JS。
2. 每天 05:30 的 ChatGPT 定时任务生成当天内容并写入 Supabase `daily_cards`。
3. 前端打开某个日期时，从 Supabase 查询该日期的卡片。
4. 常规日期显示 6 个模块；星期六前端额外允许并显示 `weekend_read`。
5. 用户完成状态写入 `completion`，电脑和手机通过 Supabase Auth + Realtime 同步。
6. 每周六 08:00 的提醒任务读取当天已经生成的 `weekend_read`，因此聊天和网页看到的是同一篇文章。

不要再建立另一套独立 JSON/HTML 周六选文流程，否则容易出现两个来源不一致。

## 4. 文件各自负责什么

### `index.html`
页面骨架、阅读规则、CSS/JS 引用。

### `styles.css`
主要界面样式：布局、普通模块卡片、统计页、按钮、回到顶部等。

### `poetry.css`
每日诗词专用样式，包括 `.translation-block` / `.translation-line` 等逐句译文结构。

### `weekend-read.css`
周六短读专用样式。当前使用独立柔和主题色，并让周六短读在桌面端横跨整行。

### `app.js`
网站核心逻辑：

- 模块列表 `BASE`
- `modulesForDate(date)`：决定某天应该有哪些模块
- 日期切换
- 从 Supabase 读取 `daily_cards`
- 完成状态
- 进度条
- 统计页
- 来源页
- Realtime 同步

周六限定逻辑的关键点：`weekend_read` 存在于模块全集，但只有 `parse(date).getDay()===6` 时才进入当天模块列表。

统计页也必须按“实际应有模块数”计算：普通日 6 项，周六 7 项（若以后关闭 `task`，还要继续按配置动态计算）。

### `ui-enhancements.js`
界面增强：顶部进度条/文字点击跳转、键盘跳转、右下角回到顶部。模块列表中也要包含 `weekend_read`。

### `auth-password.js`
邮箱 + 密码登录、设置密码、退出登录。

### `config.js`
浏览器端 Supabase 公开配置。绝不能写 service role secret。

### `sw.js`
PWA 离线缓存。新增前端文件后必须：

1. 加入 `APP_SHELL`
2. 升级 `CACHE` 版本

当前周六短读上线时已把 `weekend-read.css` 加入缓存。

### `.github/workflows/deploy-pages.yml`
GitHub Pages 自动部署。每次 `main` 有提交会把前端文件复制到 `_site` 后发布。

新增前端文件时，不仅要在 HTML 引用，还要把文件加入这里的 `cp ... _site/`。

### `data/poetry_catalog.json`
每日诗词候选库。

## 5. Supabase 数据结构

### `daily_cards`
主要字段：

- `study_date`
- `module`
- `title`
- `body_html`
- `meta`
- `source_name`
- `source_url`
- `score`

唯一键：`(study_date, module)`。

`module` CHECK 当前允许：`task, english, physics, psych, science, poetry, weekend_read`。

### `completion`
主要字段：

- `user_id`
- `study_date`
- `module`
- `completed`
- `updated_at`

唯一键：`(user_id, study_date, module)`。

`module` CHECK 同样允许 `weekend_read`。

## 6. 每日内容生成规则

每天 05:30 运行。

常规日期生成 6 个模块；如果当天是星期六，再额外生成 `weekend_read`。

通用原则：

- English 中英双语
- 物理 / 心理 / 科普中文优先
- 外部来源必须是真实可追溯的标题与 URL
- Score = 0.30 Quality + 0.20 Interesting + 0.20 Learnability + 0.15 Language fit + 0.10 Novelty + 0.05 Diversity
- 来源质量低于 80 淘汰
- 最近内容避免重复
- 卡片尽量使用 `.callout` / `.vocab` 等信息块，避免整页只有普通段落

### 每日诗词

古典作品要求：

1. `.poetry-text` 展示全文或完整经典选段
2. 必要注释
3. **逐句译文**，不能只给一段大意
4. `.poetry-note` 做简短欣赏

逐句译文结构：

```html
<div class="translation-block">
  <div class="translation-title">逐句译文</div>
  <div class="translation-line">
    <strong>原句</strong>
    <span>对应的现代汉语翻译</span>
  </div>
</div>
```

诗词可自然延长到约 3–5 分钟。现代作品要注意版权，不要复制仍受保护作品的全文。

### 周六短读 `weekend_read`

硬性标准：

- 只在星期六生成
- 文章必须在生成日前 14 天内发表
- 免费可读，原文链接可直接打开
- 类型：人物 / 思想 / 文化文章或随笔
- 原文优先约 5–10 分钟
- 查询最近至少 8 周的 `weekend_read`，避免重复作者、刊物、URL 和过于相似的主题
- 不做阅读理解题，不要求用户记忆或总结

建议 `body_html`：一句中文导读 + `<div class="callout"><strong>为什么值得读：</strong>...</div>` + 2–4 个主题标签。

字段约定：

- `title`：原文准确标题
- `source_name`：`作者 · 媒体/刊物`
- `source_url`：原文链接
- `meta`：发布日期 + 约 5–10 分钟 + 免费可读

## 7. 常见修改

### 只改颜色/布局
改 `styles.css`；诗词改 `poetry.css`；周六短读改 `weekend-read.css`。

### 改进度条跳转或回到顶部
改 `ui-enhancements.js`。

### 改阅读规则文字
改 `index.html` 的 `languageNotice`。

### 新增一个栏目
不要只改页面。至少检查：

1. `app.js` 模块列表和日期条件
2. `ui-enhancements.js` 导航模块
3. CSS
4. Supabase `daily_cards` / `completion` 的 module CHECK
5. 每日自动任务 prompt
6. `deploy-pages.yml`
7. `sw.js`
8. README / MAINTENANCE

### 页面改了但手机还是旧的
检查：

1. GitHub Actions 是否部署成功
2. `deploy-pages.yml` 是否包含新文件
3. `sw.js` CACHE 是否升级
4. 手机彻底关闭 PWA 后重开，必要时清站点缓存

## 8. 如何确认上线

GitHub：`Actions` → `Deploy PWA to GitHub Pages`，最新一条应为绿色 Success。

线上：`https://xinhui-1997.github.io/personal-learning-workbench/`

电脑可用 Ctrl+F5 强制刷新。

## 9. 安全规则

不要提交：

- Supabase service role key
- 私人 API secret
- 邮箱密码
- 任何真实账户密码

`config.js` 的 publishable/anon key 可以用于浏览器；真正敏感的服务端密钥不能放进去。

## 10. 以后让另一个 ChatGPT 接手

直接告诉它：

> 请接手我的 GitHub 项目 `Xinhui-1997/personal-learning-workbench`。先阅读 `README.md`、`MAINTENANCE.md`、`FUTURE_CHAT_PROMPT.md`，再检查当前 main 分支代码、Supabase schema 和两个内容定时任务，然后根据我的新要求继续修改。不要凭以前聊天猜测，以仓库、数据库和当前任务配置为准。

# 个人学习工作台｜维护手册

这份文件的目的：即使完全找不到最初的 ChatGPT 对话，也能继续维护这个项目。

## 1. 项目在哪里

- GitHub 仓库：`Xinhui-1997/personal-learning-workbench`
- 在线网站：`https://xinhui-1997.github.io/personal-learning-workbench/`
- 前端托管：GitHub Pages
- 云端数据：Supabase
- 当前 Supabase 项目：`kemjqowxmyzauvbyebwg`
- 每日内容：ChatGPT 定时任务每天 05:30（Asia/Tokyo）生成并写入 `public.daily_cards`
- 周六短读：由同一个每日 05:30 任务在星期六额外生成；只在学习卡网页呈现，不在聊天里复述

## 2. 当前模块

常规学习模块：

- `task` → 今日小事
- `english` → Daily English
- `physics` → 每日物理
- `psych` → 每日心理
- `science` → 每日科普
- `poetry` → 每日诗词

奖励模块：

- `fun` → 每日开心一刻；完成任意 3 个学习模块后解锁，不计入完成进度

星期六额外出现：

- `weekend_read` → 周六短读

`weekend_read` 只在星期六计入当天进度和统计，其他日期不应显示，也不应进入完成率分母。

每日诗词内容池在：`data/poetry_catalog.json`。

## 3. 正式数据流

这个项目不是“每天重新生成 HTML”。正式流程是：

1. GitHub Pages 部署固定前端：`index.html` + CSS + JS。
2. 每天 05:30 的 ChatGPT 定时任务生成当天内容并写入 Supabase `daily_cards`。
3. 前端打开某个日期时，从 Supabase 查询该日期的卡片。
4. 常规日期显示基础学习模块；星期六额外允许并显示 `weekend_read`。
5. `fun` 在完成任意 3 个学习模块后解锁。
6. 用户完成状态写入 `completion`，电脑和手机通过 Supabase Auth + Realtime 同步。
7. 周六短读以数据库当天 `weekend_read` 为唯一正式来源，不建立第二套独立选文流程。

## 4. 文件各自负责什么

### `index.html`
页面骨架、阅读规则、CSS/JS 引用。

### `styles.css`
主要界面样式：布局、普通模块卡片、统计页、按钮、回到顶部等。

### `poetry.css`
每日诗词专用样式，包括 `.translation-block` / `.translation-line` 等逐句译文结构。

### `weekend-read.css`
周六短读专用样式。当前使用独立柔和主题色，并让周六短读在桌面端横跨整行。

### `fun-module.js` / `fun.css`
每日开心一刻的解锁与展示。

### `notes-module.js` / `notes.css`
今日小事上方的记事框，支持文字、图片和语音等记录。

### `app.js`
网站核心逻辑：模块列表、日期切换、从 Supabase 读取 `daily_cards`、完成状态、进度条、统计页、来源页、Realtime 同步等。

周六限定逻辑的关键点：`weekend_read` 只在星期六进入当天模块列表。统计页也必须按“实际应有模块数”动态计算。

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

### `completion`
主要字段：

- `user_id`
- `study_date`
- `module`
- `completed`
- `updated_at`

唯一键：`(user_id, study_date, module)`。

如果新增模块，必须同步检查两个表的 module CHECK、RLS 和前端模块列表。

## 6. 每日内容生成规则

每天 05:30 运行。

常规日期生成学习模块和 `fun`；如果当天是星期六，再额外生成 `weekend_read`。

通用原则：

- English 中英双语
- 物理 / 心理 / 科普中文优先
- 外部来源必须是真实可追溯的标题与 URL
- Score = 0.30 Quality + 0.20 Interesting + 0.20 Learnability + 0.15 Language fit + 0.10 Novelty + 0.05 Diversity
- 来源质量低于 80 淘汰
- 最近内容避免重复
- 卡片尽量使用 `.callout` / `.vocab` 等信息块，避免整页只有普通段落
- `meta` 必须是人类可读纯文本，不得显示 JSON、`score_breakdown`、`label`、`type` 等内部字段

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

### 每日开心一刻 `fun`

- 每天只生成 1 条
- 完成任意 3 个学习模块后解锁
- 不计入学习进度
- 优先无需专业背景就能理解的生活幽默、冷笑话、热笑话、谐音梗、机智小故事、语言反转
- 不使用程序员、数学、医学、金融、法律等专业梗；如果使用专业领域，只接受物理领域，而且必须让非专业读者也容易看懂
- 干净、不低俗，不以弱势群体、外貌、疾病、灾难或身份特征为笑点
- 约 10–30 秒读完

### 周六短读 `weekend_read`

这是当前最重要的选文规则，**不要恢复成旧版“过去 14 天新发表文章”规则**。

硬性标准：

1. **只在星期六生成。**
2. **只选中文可读内容。** 不推荐英文原文；外文作品必须有高质量中文译文。
3. **发表时间不限。** 经典旧作与新文章一视同仁，以质量为先。
4. **优先白话文。** 不选文言文作为周六短读主文。
5. **阅读时长必须控制在 10 分钟以内，优先 5–10 分钟。**
6. 可选内容包括：
   - 中文经典文学完整短篇
   - 经典文学中的自然章节或完整节选
   - 散文、随笔
   - 人物 / 思想 / 文化文章
   - 外文经典或优秀文章的中文译文
7. 允许并鼓励“成年后重读经典”，例如鲁迅《从百草园到三味书屋》这一类语言清楚、画面感强、无需学术背景即可进入的作品。
8. 原作太长时，只推荐一个完整、自然的章节或节选，并明确标注“节选”，不要让用户误以为是全文。
9. 优先免费、无需登录即可直接阅读的中文链接。公版作品可优先使用维基文库、国家机构、出版社或其他可靠公开文本来源。
10. 若作品仍受版权保护，不要把大段正文复制进 `body_html`；只写导读、“为什么值得读”、主题标签和原文链接。
11. 查询最近至少 8 周 `weekend_read`，避免重复作品、作者和 URL，并尽量避免连续几周同一种题材；但不要为了“新鲜”牺牲经典质量。
12. 不做阅读理解题，不要求记忆、摘抄或总结。

建议 `body_html`：一句中文导读 + `<div class="callout"><strong>为什么值得读：</strong>...</div>` + 2–4 个主题标签。

字段约定：

- `title`：准确中文标题；节选需明确标注
- `source_name`：作者 + 作品集 / 译者 / 可靠文本来源
- `source_url`：可直接阅读的中文页面
- `meta`：纯文本，例如“约 8–10 分钟 · 中文原文 · 免费可读”或“约 6 分钟 · 中文译文 · 免费可读”
- `score`：按质量公式给分

## 7. 常见修改

### 只改颜色/布局
改 `styles.css`；诗词改 `poetry.css`；周六短读改 `weekend-read.css`。

### 改进度条跳转或回到顶部
改 `ui-enhancements.js`。

### 改阅读规则文字
改 `index.html` 的对应说明。

### 新增一个栏目
不要只改页面。至少检查：

1. `app.js` 模块列表和日期条件
2. `ui-enhancements.js` 导航模块
3. CSS
4. Supabase `daily_cards` / `completion` 的 module CHECK
5. 每日自动任务 prompt
6. `deploy-pages.yml`
7. `sw.js`
8. README / MAINTENANCE / FUTURE_CHAT_PROMPT

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

> 请接手我的 GitHub 项目 `Xinhui-1997/personal-learning-workbench`。先阅读 `README.md`、`MAINTENANCE.md`、`FUTURE_CHAT_PROMPT.md`，再检查当前 main 分支代码、Supabase schema 和每日内容定时任务，然后根据我的新要求继续修改。不要凭以前聊天猜测，以仓库、数据库和当前任务配置为准。

# 个人学习工作台

在线地址：

https://xinhui-1997.github.io/personal-learning-workbench/

个人学习 PWA。当前架构：GitHub Pages + Supabase + PWA + ChatGPT 每日内容 Agent。

## 当前模块

常规每天 6 个模块：

- 今日小事
- Daily English
- 每日物理
- 每日心理
- 每日科普
- 每日诗词

每周六额外出现：

- 周六短读（`weekend_read`）——过去两周内发表、免费可读的人物 / 思想 / 文化文章或随笔，优先 5–10 分钟读完

## 当前状态

- GitHub Pages 已上线
- Supabase `daily_cards` / `completion` 已建立并启用 RLS
- 完成状态支持云端同步与 Realtime
- 支持邮箱 + 密码登录
- 已建立每天 05:30（Asia/Tokyo）的自动内容生成任务；周六该任务会额外生成 `weekend_read`
- 已建立周六 08:00 的短读提醒；提醒直接读取当天 `daily_cards.weekend_read`，与网页保持同一篇
- `data/poetry_catalog.json` 保存每日诗词候选库

## 内容原则

- Daily English：中英双语
- Physics / Psychology / Science：中文优先；优质英文来源入选后转中文
- 每日诗词：古诗、古词、古文名篇、现代诗；优先经典但非小学启蒙级篇目，并附注释、逐句译文、赏析
- 周六短读：过去 14 天内发表、免费可读、人物 / 思想 / 文化类，优先原文 5–10 分钟；避免近期重复作者、刊物、URL 和主题
- 常规卡片通常约 1–2 分钟；诗词约 3–5 分钟；周六短读原文约 5–10 分钟
- Score = 0.30 Quality + 0.20 Interesting + 0.20 Learnability + 0.15 Language fit + 0.10 Novelty + 0.05 Diversity
- 来源质量低于 80 直接淘汰
- 外部来源标题和链接必须可追溯，不编造来源

## 以后如何继续维护

即使原来的 ChatGPT 对话丢失，也不影响项目继续开发。

请优先阅读：

- [`MAINTENANCE.md`](./MAINTENANCE.md) —— 完整维护手册，说明每个文件、数据库、部署和常见修改方法
- [`FUTURE_CHAT_PROMPT.md`](./FUTURE_CHAT_PROMPT.md) —— 以后开启新 ChatGPT 对话时可直接复制的接手提示词

未来新的 ChatGPT 只要能访问这个 GitHub 仓库，并按维护手册检查当前 Supabase 和定时任务，就可以继续修改，而不需要找回旧聊天。

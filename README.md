# 个人学习工作台

在线地址：

https://xinhui-1997.github.io/personal-learning-workbench/

每天 5–8 分钟的个人学习 PWA。内容经来源质量、可读性、语言适配、新颖性与多样性评分后生成；Daily English 保持中英双语，其他模块以中文为主。

当前架构：GitHub Pages + Supabase + PWA + ChatGPT 每日内容 Agent。

## 当前状态

- GitHub Pages 已上线
- Supabase `daily_cards` / `completion` 已建立并启用 RLS
- 完成状态支持云端同步与 Realtime
- 已建立每天 05:30（Asia/Tokyo）的自动内容生成任务
- 2026-09-06 ～ 2026-09-08 有示例内容

## 内容原则

- Daily English：中英双语
- Physics / Psychology / Science：中文优先；优质英文来源入选后转中文
- 每张卡约 1–2 分钟
- Score = 0.30 Quality + 0.20 Interesting + 0.20 Learnability + 0.15 Language fit + 0.10 Novelty + 0.05 Diversity
- 来源质量低于 80 直接淘汰
- 原文标题和链接必须可追溯，不编造来源

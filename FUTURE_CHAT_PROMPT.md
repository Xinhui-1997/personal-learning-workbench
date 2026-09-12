# 未来新对话接手提示词

如果以后找不到原来的 ChatGPT 对话，把下面这段直接发给新的 ChatGPT：

---

请接手我的个人学习工作台项目。

GitHub 仓库：`Xinhui-1997/personal-learning-workbench`
在线网站：`https://xinhui-1997.github.io/personal-learning-workbench/`

先做以下事情，不要直接猜：
1. 阅读仓库里的 `README.md`
2. 阅读 `MAINTENANCE.md`
3. 检查当前 main 分支代码
4. 如果需要改数据/同步，检查当前 Supabase 项目和 schema
5. 如果需要改每天自动生成的内容，先检查当前定时任务配置

这个项目当前是：GitHub Pages + PWA + Supabase + ChatGPT 每日内容 Agent。

常规每天模块：
- 今日小事
- Daily English
- 每日物理
- 每日心理
- 每日科普
- 每日诗词

每周六额外模块：
- 周六短读（数据库 module=`weekend_read`）：只选中文可读内容，发表时间不限；优先中文白话经典文学、散文、随笔、人物 / 思想 / 文化文章，也可选高质量外文作品的中文译文。允许完整短篇或自然的章节/节选；阅读时长必须控制在 10 分钟以内，优先 5–10 分钟。经典质量优先，例如鲁迅《从百草园到三味书屋》这一类成年后仍值得重读的文章。该卡由每日 05:30 任务在周六生成并写入 Supabase，只在学习卡网页呈现，不要在聊天中复述内容。

我的要求以仓库、数据库和我这次新说的需求为准，不要依赖已经丢失的旧聊天。

修改时请同时检查：
- 前端代码
- Supabase module 约束 / RLS / 数据结构
- GitHub Pages 部署文件
- Service Worker 缓存
- 每日自动生成任务
- 周六短读相关任务

完成修改后告诉我改了哪些文件、数据库是否改了、是否已部署成功，以及我是否需要手动操作。

---

## 更简单的一句话版本

> 接手 `Xinhui-1997/personal-learning-workbench`，先读 README 和 MAINTENANCE，再按当前仓库/Supabase/定时任务状态继续开发。

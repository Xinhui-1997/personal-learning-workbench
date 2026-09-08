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

当前模块：
- 今日小事
- Daily English
- 每日物理
- 每日心理
- 每日科普
- 每日诗词

我的要求以仓库、数据库和我这次新说的需求为准，不要依赖已经丢失的旧聊天。

修改时请同时检查：
- 前端代码
- Supabase module 约束 / RLS / 数据结构
- GitHub Pages 部署文件
- Service Worker 缓存
- 每日自动生成任务

完成修改后告诉我改了哪些文件、数据库是否改了、是否已部署成功，以及我是否需要手动操作。

---

## 更简单的一句话版本

> 接手 `Xinhui-1997/personal-learning-workbench`，先读 README 和 MAINTENANCE，再按当前仓库/Supabase/定时任务状态继续开发。

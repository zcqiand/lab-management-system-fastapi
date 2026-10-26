# 更新日志

格式照 `v<MAJOR>.<MINOR>.<PATCH>-<YYYYMMDD>`（tag 即放行：全量回归绿后打 tag）。

历史版本（tag 底账，明细见 git log）：

- `v0.1.4-20261011`（2026-10-11）— chore(retire): LAB_AUTH_DEV_PASSWORD 退役——原生登录代理 saas IdP (REQ-2026-023)
- `v0.1.3-20261006`（2026-10-06）— chore(env): 补 .env.example/.env.test 两件套——5.104 L0.5 三件套对齐
- `v0.1.2-20261002`（2026-10-02）— fix(deploy): httpx 升进主依赖——v0.1.1 首航第二例传递缺口
- `v0.1.1-20261002`（2026-10-02）— fix(deploy): sqlalchemy/psycopg2 升进主依赖——镜像 saas 仓首航事故预防性修复
- `v0.1.0-20261002`（2026-10-02）— docs(req): REQ-2026-008 根路径跳转 Swagger 对齐文档——功能影响 0（基础设施端点不进树，待评审）

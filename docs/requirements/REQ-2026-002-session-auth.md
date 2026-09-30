# REQ-2026-002 批1 会话与认证：当前会话 + 选租户换发 + 权限（菜单/权限集）+ 认证（密码/SSO/刷新/登出）

| 项 | 值 |
|---|---|
| 提出人 | zcqiand |
| 提出日期 | 2026-09-30 |
| 优先级 | P0 |
| 状态 | 已评审 |
| 关联 ADR | REQ-2026-001（总纲 T-1）；ADR-0041（三层全生成） |

## 1. 需求描述

### 用户原话

> 继续

（承接 lab 仓 REQ-2026-001 总纲 T-1「批1 会话与认证——对接身份平台 SSO，其余一切的前置」，用户以「继续」批准按总纲进入第一批实现。范围/口径拍板见总纲 §1 三项。）

### 我的理解

在生成区骨架上，把总纲 T-1 圈定的认证簇 10 端点从「未实现 500 兜底」落成真实现，
语义逐条对齐家族参照实现（lab-management-system-springboot，contract-test live 全绿的 oracle 侧）：

| 端点 | 功能 ID | 家族语义要点（lab-springboot 参照） |
|---|---|---|
| POST /api/auth/login | M01.F05.I01 | 用户名+密码校验，签发 HS256 access/refresh token 对 + 租户列表（MyTenant：tenantId/code/name/roleIds，roleIds 真 join）；错误凭证 4xx；service.account-service 链路 |
| POST /api/auth/native-login | M01.F05.I01 | 与 login 同源非浏览器通道（springboot AuthController:64 直通 service.login，service-account 链路）；树不另立行（镜像 springboot 树无 I06 行） |
| POST /api/auth/logout | M01.F05.I05 | 无状态 JWT：服务端无 session，204 |
| GET /api/auth/me | M00.F01.I01 | CurrentUserSession：user + 关联租户列表 + currentTenantId（token tenant_id claim 优先，缺省 TENANT-001） |
| POST /api/auth/switch-tenant | M00.F02.I01 | 校验租户归属后换发携带 tenant_id claim 的 token |
| GET /api/auth/menus | M01.F04.I01 | 按角色下发导航树（5 根节点，镜像家族形状） |
| GET /api/auth/permissions | M01.F04.I02 | RBAC 权限串列表（admin 全量 11 项） |
| POST /api/auth/refresh | M01.F05.I04 | lab refresh token 是 HS256 JWT（typ=refresh）内嵌 saas refresh token；调 saas 换发后签新 lab JWT 对 |
| GET /api/auth/sso/authorize | M01.F05.I02 | RFC 6749 §10.12 标准 state（前端生成原样透传）；forward saas 签发一次性 code |
| POST /api/auth/sso/callback | M01.F05.I03 | saas code 换 token → /me/whoami + /me/tenants 取 user/membership 信 saas；首次 SSO 按 email upsert 到 lab directory；state 校验在前端回跳比对 |

硬约束：API/DTO/实体仍是生成物零手改；实现只写 impl/ 缝 + app.py 组合根；
env（DATABASE_URL / JWT 三键 / 身份平台地址与 OAuth 凭据）fail-fast 无兜底（硬规则 §1）。

### 澄清记录

| 疑问 | 澄清结论 | 澄清人 | 日期 |
|---|---|---|---|
| 无（范围/口径已在总纲拍板；native-login 树行口径镜像 springboot——同源直通不另立行） | — | — | — |

## 2. 验收标准

| 编号 | 场景（给定） | 操作（当） | 预期（则） |
|---|---|---|---|
| AC-1 | 种子用户（家族 dev 约定） | 正确凭据 POST /auth/login | 200：token/refreshToken/user/tenants（MyTenant 四字段）/currentTenantId |
| AC-2 | 登录后有效 Bearer | GET /auth/me | 200 CurrentUserSession；无 Bearer/坏 token → 401 |
| AC-3 | 归属租户的 Bearer | POST /auth/switch-tenant | 200 换发 token；非归属租户 → 4xx |
| AC-4 | 有效 Bearer | GET /auth/menus + /auth/permissions | 200 导航树（5 根节点）+ 权限串列表（admin 11 项） |
| AC-5 | 有效 refreshToken | POST /auth/refresh | 200 新 token 对（内嵌 saas refresh 续期链路） |
| AC-6 | SSO 链路 | /auth/sso/authorize → saas → /auth/sso/callback | 换发 lab token 对 + 首次按 email upsert |
| AC-7 | 全部实现完成 | suite 门禁 L1-L5 | 全绿（red-first：测试先红后绿，trace 挂功能 ID） |

## 3. 任务拆解

| 任务 ID | 任务描述 | 类型 | 负责人 | 预估 | 状态 |
|---|---|---|---|---|---|
| T-1 | red-first：批1 全部断言测试（httpx ASGI 直连 + PG 真库 scratch 种子，挂 M00.F01.I01/M00.F02.I01/M01.F04.I01/I02/M01.F05.I01/I04/I05） | 测试 | claude | 中 | 待开始 |
| T-2 | impl/ 基座：config（env fail-fast）/ context / errors（家族 ErrorResponse）/ security（HS256 签发校验 + 租户 claim） | 开发 | claude | 中 | 待开始 |
| T-3 | AuthApiImpl 落 10 端点语义（SSO 簇对齐 saas 跳板语义，身份平台地址 env） | 开发 | claude | 大 | 待开始 |
| T-4 | app.py 组合根：create_app 工厂 + 异常 handler（家族 4xx 收口）+ 静态装配冒烟 | 开发 | claude | 小 | 待开始 |
| T-5 | 功能树同 commit：4 个 F 翻「已上线」+ 11 个 I 级子项翻「已上线」（I03/I04 前端锚定行维持开发中）；门禁 L1-L5 全绿 | 收口 | claude | 小 | 待开始 |

## 4. 功能影响

| 功能 ID | 功能名称 | 影响类型 | 说明 | 关联任务 |
|---|---|---|---|---|
| M00.F01 | 当前用户会话 | 变更 | 状态 规划→已上线；I 级子项 I01 | T-1/T-3/T-5 |
| M00.F02 | 登录选租户 | 变更 | 状态 规划→已上线；I 级子项 I01 | T-1/T-3/T-5 |
| M01.F04 | 权限管理 | 变更 | 状态 规划→已上线；I 级子项 I01/I02（实现）+ I03/I04（前端锚定行，镜像 springboot 维持开发中） | T-1/T-3/T-5 |
| M01.F05 | 认证管理 | 变更 | 状态 规划→已上线；I 级子项 I01/I02/I03/I04/I05 | T-1/T-3/T-5 |

新增：0（I 级子项随 F 行登记，编号镜像 lab-springboot）；变更：4；删除：0。

## 5. 流程影响

无（SSO/登录流程形状以家族参照实现与 shared 契约为准；本仓无流程图）。

## 6. 风险与回滚

| 风险 | 影响面 | 缓解 | 回滚方式 |
|---|---|---|---|
| 语义与家族分叉（错误码/claim 口径/租户过滤） | contract-test 批6 接入 | 逐条对照 lab-springboot 源码实现，注释标注参照行 | git revert 本批 commit |
| SSO 簇依赖 saas 身份平台可达 | T-3 测试 | 单测内以契约形状断言为主（authorize/callback 形状锁），saas 联调归批6 live；本机 saas dev 栈在跑可真连 | 端点独立可关 |
| 测试直连远程 PG | L4 变慢/轮换假红 | scratch 库建在同服务器（镜像 saas fastapi 配方）；假红先 ping 看丢包隔离复跑 | 断言失败即红，无静默 |
| mypy strict 与生成区 Any 缝隙 | L3 | 生成区 follow_imports=skip 既有接线；impl 不显式 Any/type: ignore | 既有 pyproject 配置 |

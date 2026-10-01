# REQ-2026-007 批6 数据统计 + contract-test live 接入（M05.F01；总纲 T-5 尾 + T-6）

| 项 | 值 |
|---|---|
| 提出人 | zcqiand |
| 提出日期 | 2026-10-01 |
| 优先级 | P0 |
| 状态 | 已验收（2026-10-01：lab fastapi 全门 L1-L5 绿 + 93 tests；CT live cap-2 springboot+fastapi 389/389 绿 AC-7 达成；首轮 9 红六组根因全修，见澄清记录） |
| 关联 | REQ-2026-001（总纲 T-5 尾 + T-6）；REQ-2026-006（批5 先例：act 流转数据供仪表盘聚合消费） |

## 1. 需求描述

### 用户原话

> 继续

（承接 lab 仓 REQ-2026-001 总纲：批5 之后进入批6「数据统计（M05）+ contract-test
live 接入（T-6）」。用户以「继续」批准按总纲进入第六批，批2-批5 同款授权形态。）

### 我的理解

两件事：

| 域 | 端点数 | 功能 ID | 语义 |
|---|---|---|---|
| /api/summary | 2（GET /api/summary + GET /api/summary/stats） | M05.F01.I01 / I06 / I03 / I04 | 报告汇总表 + 仪表盘统计 |
| lab-management-system-contract-test | 0（无新端点） | 无（基建） | fastapi 以 live 目标接入 CT（:5207），总纲 T-6 |

语义逐条对照 lab-springboot `SummaryService` + `SummaryController` +
`SampleReceiptRepository.summary` native SQL：

1. **鉴权/tenant**：2 端点 `require_login` + `current_tenant_or_default`（批2 先例；
   springboot controller 同款 currentTenantIdOrDefaultStatic）。
2. **GET /api/summary**（镜像 getReportSummary）：
   - categoryCode null/空串 → "ALL"；dateFrom/dateTo null → ""（空串等同无界，
     契约 query 入参可缺省）。
   - 行集 = summary native SQL 镜像：tenant 等值 + (ALL = 不过滤 | categoryCode
     等值) + commission_date 前后缀（字符串字典序即日期序，`>=`/`<=`），
     **ORDER BY commission_date DESC, commission_code**（summary 专用排序，与
     list 的 updated_at DESC 不同——注意区分）。
   - SummaryData 三键：summaryName=`报告汇总（{cat}）`（cat=ALL 时字面 ALL）；
     columns=6 列固定（commissionCode/categoryCode/projectName/flowStatus/
     result/reportCode + 中文 label）；rows=逐行 renderRow。
   - renderRow：六键全 string，**null → ""**（flowStatus/result 取 wire 枚举值，
     reportCode/projectName 等取列值或 ""）。
3. **GET /api/summary/stats**（镜像 getDashboardStats 全量，含 I03/I04 扩展段）：
   - 基础（I06）：contractCount（tenant 全量）/ receiptCount（= summary ALL 行数）/
     sampleCount（tenant 全量）；reportCountByStatus 三桶：draft=receiving+
     task_assignment+data_entry、reviewing=review+approval、issued=issuance+
     archived；pendingTaskCount=task_assignment+data_entry+review。
   - 核心指标（I03）：todayTestCount=created_at 或 test_start_date 以**服务器本地
     今日**前缀开头的单数（springboot LocalDate.now()+String.valueOf 前缀匹配，
     created_at 存 UTC ISO——同机同行为，机械镜像不修正时区）；
     qualifiedRateByMaterial{concrete,rebar,sand}：码表全量预载（summaryName 映射，
     null→""），categoryCode → summaryName 关键词匹配（concrete=混凝土|水泥、
     rebar=钢筋|钢材|焊接|机械连接|连接、sand=砂|碎（卵）石|轻集料|颗粒级配，
     首命中），result=="pass" 计 pass；rate=round(pass/total*1000)/1000.0（total=0
     → 0.0）；三键恒在（未命中材料 total=0/pass=0/rate=0.0）。reportOutputByStatus：
     generated=reportCode 非空数、pending=reviewing、issued=issued。
   - 任务漏斗（I04）：funnelByStage 六段 snake_case 键（生成模型 __properties 为
     SSOT）：pendingCollect=receiving、received=task_assignment、testing=
     data_entry 且 reportCode 空、reporting=data_entry 且 reportCode 非空、
     reviewing=reviewing、issued=issued。
   - 全字段恒非 null（NON_NULL 镜像无剔除面）。
4. **contract-test live 接入**（总纲 T-6，无新端点）：
   - `src/targets.ts` 加 `fastapi → http://localhost:5207`（端口表 conventions §6
     X07 槽位，2026-09-29 已启用；uvicorn 显式 --port）。
   - `.harness/stack.json` trace_env.CONTRACT_TARGETS 加 `fastapi`（4→5 目标；
     prewarm /health 落 DEFAULT_HEALTH 无需加名）。
   - live 验证打 **lab_dev**（三库分层约定：CT 走 _dev）；fastapi server 配方
     `.venv` uvicorn `lab_management_system_fastapi.app:app --port 5207`。
   - 开发会话 live 上限 2（springboot=oracle + fastapi 被测；live-ct-e2e 上限
     人裁惯例），REQ-2026-006 §4.5 遗留的三态 filter live 对照随 CT live 兑现
     （receipts-act/lastsubmit 套件已覆盖）。

硬约束：API/DTO/实体生成物零手改；实现只写 impl/ 缝（新 summary_impl.py）；
测试零种子依赖全走 API create；CT 仓改动只限 targets.ts + stack.json trace_env
+ 必要的文档（不碰测试断言面——CT 测试已存在且四方绿）。

### 澄清记录

| 疑问 | 澄清结论 | 案件澄清人 | 日期 |
|---|---|---|---|
| springboot 树 M05.F01.I03/I04 状态是「规划」但 springboot SummaryService 代码已实现，fastapi 侧登记什么状态？ | fastapi 树按本仓实现登记「已上线」；两树状态各自独立（树是仓内余额账，非家族同步账）。springboot 树的规划/代码不一致是那仓的账，本批不代改 | claude（实证 springboot SummaryService 全文含 I03/I04 段 + springboot 树行） | 2026-10-01 |
| trace_env 加名是 memory 在册的「升档人裁」线，本批做不做？ | 做：总纲 T-6 即本批授权范围，「继续」已批；且 lab CT trace_env 现值本就是全家后端（4 目标），fastapi 是第 5 后端，加入=延续现状非新增语义。REQ 记录在案 | claude（实证 CT stack.json trace_env 4 目标 + 总纲 T-6 原文） | 2026-10-01 |
| todayTestCount 的 today 用 UTC 还是本地日期？ | 服务器本地日期（date.today()），镜像 springboot LocalDate.now()；created_at 存 UTC ISO 字符串做前缀匹配——两侧同构（同机部署），跨时区漂移是双侧一致的既有行为，不单侧修正 | claude（实证 springboot SummaryService today 段） | 2026-10-01 |
| summary 行排序是什么？ | commission_date DESC, commission_code（summary native SQL 专用；与 receipts list 的 updated_at DESC, commission_code 不同源不同列） | claude（实证 SampleReceiptRepository.summary ORDER BY） | 2026-10-01 |
| funnelByStage 键名形状？ | snake_case wire 键（pending_collect 等 5 键，received/reviewing/issued 单词键）——以 fastapi 生成模型 __properties 为 SSOT，与 springboot @JsonProperty 同源契约 | claude（实证 dashboard_stats_funnel_by_stage.py） | 2026-10-01 |
| CT live 首轮 9 红（6 文件）：report-names GET 500 ×3 + receipts 两测试连锁，根因？ | lab-nextjs 种子直灌行 RN-102-x 的 ext_fields 元素缺契约必填 type → fastapi pydantic 500、springboot Jackson 容忍输出 "type": null（违约 wire）。修法=种子 JSON + lab_dev 三行 UPDATE 双处（type 按语义补 text/select/date + options:[]）；springboot 的容忍是违约流出不是镜像基准，不复刻 | claude（lab_dev 行级探针复现 + springboot wire 实测） | 2026-10-01 |
| contracts POST normalize 分叉：fastapi tenantId 回显 zero-uuid-1 vs springboot TENANT-001，根因？ | current_tenant_or_default 的 fallback 源错镜像：springboot 走 directory.defaultTenant().getTenantId()（业务码），fastapi 曾走 LAB_SAAS_DEFAULT_TENANT_ID env（SSO 请求体 body.tenantId 的值源，UUID 形）。修=fallback 改 ctx.request.app.state.directory.default_tenant().tenant_id；saas_client 的 SSO body 消费点保持 env（那是正确镜像） | claude（双侧登录链 + token claim 解码 + springboot Controller 实证） | 2026-10-01 |
| technical-requirements POST 400（comparison is required）vs springboot 200，谁对？ | springboot 对：Mapper 缺失落 RequirementComparison.u，wire 值是 "≥"（u 是 Java 枚举转义名非 wire 值——原判「'u' 契约不可表达」误读）。修=fastapi impl 缺失照镜像落 "≥"，去 400；三后端共库 + 三键全局主键，tenant 归一后跨目标 DELETE 404 同步治愈 | claude（springboot Mapper/dto 枚举源码 + 双侧 wire 逐字段对照） | 2026-10-01 |
| CT compare.test 端口数组断言红（期望 4 目标实得 5）？ | 本批 targets.ts 加 fastapi 的 CT 仓自身断言同步义务：compare.test 数组加 fastapi + 标题四个→五个 + 5207 断言；conventions §6 X07 槽位 2026-09-29 已登记，无需改文档 | claude（conventions §6 132-133 行实证） | 2026-10-01 |
| TE PUT 带契约外字段（requirement）fastapi 400 vs springboot 200？ | springboot 对：Jackson 未知字段忽略 → applyUpdate 全 null 跳过 → 空更新 200；fastapi impl 自加的「空载荷 400」是分叉点（springboot 无此校验）。修=去 400，空载荷 no-op 200 镜像（连带正常 PUT/空载荷 PUT 行为回归一致） | claude（springboot Mapper.applyUpdate + 双侧实测三态 PUT） | 2026-10-01 |
| 后记（总纲收口批修订）：本 REQ §4.5「M05 模块行不翻（M02 先例）；M03 同此惯例在册」的声明作废——T-3 树翻转实操已翻 M05 模块行（754441d），总纲收口批（REQ-2026-001，2026-10-01）据此把惯例收敛为「模块行随 F 行翻」并补齐 M02/M03/M04/M06 | 惯例收敛，树账面一致 | claude | 2026-10-01 |

## 2. 验收标准

| 编号 | 场景（给定） | 操作（当） | 面预期（则） |
|---|---|---|---|
| AC-1 | 租户内若干接样单（多类别/多日期） | GET /api/summary（缺省/ALL/指定类别/日期界） | summaryName 按 cat 回显；columns 恒 6 列；行按 commission_date DESC, commission_code 排序；过滤语义与 native SQL 一致 |
| AC-2 | 含 null 可选字段的接样单 | GET /api/summary | 行六键恒 string、null→""；flowStatus/result 为 wire 枚举值 |
| AC-3 | 空租户（无单） | GET /api/summary + /stats | rows=[]；stats 全计数 0、rate 0.0、三材料键恒在 |
| AC-4 | 批5 流转数据 | GET /api/summary/stats | 三桶聚合与 funnel 六段计数精确（testing/reporting 按 reportCode 有无分桶）；pendingTaskCount=task+entry+review |
| AC-5 | 当日新建单 | GET /api/summary/stats | todayTestCount 计入（created_at 今日前缀）；合格率按材料关键词分桶 |
| AC-6 | tenant 隔离 | TENANT-002 token 查 summary | 只见本租户数据 |
| AC-7 | fastapi :5207 live | CONTRACT_TARGETS=springboot,fastapi 跑 CT 套件 | 全绿（fastapi 与 springboot oracle 逐端点比对一致；含批5 act/test-records/三态 filter 面） |
| AC-8 | 全部实现完成 | suite 门禁 L1-L5 | 全绿（red-first；trace 挂 4 个 I ID；CT 仓 gate 绿） |

## 3. 任务拆解

| 任务 ID | 任务描述 | 类型 | 负责人 | 预估 | 状态 |
|---|---|---|---|---|---|
| T-0 | 需求文档门：本文件 + 功能树 M05.F01 翻开发中 + 4 个 I 子项登记 + README 台账行 | 文档 | claude | 小 | 已完成 |
| T-1 | red-first：tests/test_summary.py 全断言（挂 4 个 I ID；汇总列结构/过滤/排序 + stats 全段聚合 + tenant 隔离 + 空租户形状） | 测试 | claude | 中 | 已完成 |
| T-2 | impl：summary_impl.py 两端点（renderRow/码表预载/材料关键词/漏斗 6 段，逐条镜像 SummaryService） | 开发 | claude | 中 | 已完成 |
| T-3 | 收口：CT 仓 targets.ts + trace_env 加名 + live 验证（springboot+fastapi 双目标）；树 5 行翻已上线；trace 实测修正；门禁全绿；双仓（lab fastapi + contract-test）commit + suite gitlink | 收口 | claude | 中 | 已完成 |

## 4. 功能影响

| 功能 ID | 功能名称 | 影响类型 | 说明 | 关联任务 |
|---|---|---|---|---|
| M05.F01 | 报告汇总 | 变更 | 规划→开发中；新增子项 I01/I03/I04/I06 | T-1～T-3 |

新增：4（全部为 I 级子项）；变更：1（F 行翻级）；删除：0。
另：contract-test 仓基建改动不入功能树（targets/trace_env 是 harness 面，先例：
rails 接入批同样未登记树）。

## 4.5 遗留与开放问题

- 见证取样跟踪未实现：springboot 侧同样未实现（SummaryService 无 witness 段），
  两侧一致规划态，**不编号登记**（登记空 ID 即悬空引用）；若未来实现再拆子项。
- saas-identity-platform-fastapi NON_NULL 收口回补：与本批无关，在册待人裁。
- M05 模块行不翻（M02 先例：F 行上线不动模块行）；M03 模块行同此惯例在册。

## 5. 流程影响

本批是总纲 T-5 的收尾批（M05 落地后 lab fastapi 生成面 13 模块全部有真实现），
同时打通 T-6：contract-test 从「springboot 单 oracle live」扩展到「springboot+
fastapi 双目标」，此后任何 lab 契约语义回归在 CT live 即被双后端互证拦截。

## 6. 风险与回滚

| 风险 | 影响面 | 缓解 | 回滚方式 |
|---|---|---|---|
| stats 聚合（三桶/漏斗/合格率）与 springboot 分母口径偏差 | /api/summary/stats | 逐段镜像 SummaryService 源码；测试用受控数据集逐数断言 | git revert 本批 commit |
| summary 排序/日期前缀语义偏差 | /api/summary | ORDER BY 与 native SQL 逐字对照；日期字典序测试覆盖 | git revert 本批 commit |
| CT live 接入暴露既有实现面偏差（批1-4 端点与 oracle 不一致） | CT live 套件 | live 红即真问题：逐条修实现（属本批范围）；修不动回滚 CT 仓 targets/trace_env 两处 | git revert 两仓 commit |
| trace_env 5 目标后 CT gate 需 5207 存活 | CT gate | 环境探针化降档已在册（5.101）；live 门槛与 rails 接入时同构 | trace_env 移除 fastapi 名 |

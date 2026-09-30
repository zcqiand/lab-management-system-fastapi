# REQ-2026-006 批5 试验过程流：任务分配 + 检测记录 + 流程状态机 act 面（M03.F02/F03/F05-F08）

| 项 | 值 |
|---|---|
| 提出人 | zcqiand |
| 提出日期 | 2026-09-30 |
| 优先级 | P0 |
| 状态 | 已验收（2026-10-01，全门 L1-L5 绿，89 passed；T-0～T-3 完成） |
| 关联 | REQ-2026-001（总纲 T-5）；REQ-2026-005（批4 先例：envelope/业务键/tenant 收口口径沿用） |

## 1. 需求描述

### 用户原话

> 继续

（承接 lab 仓 REQ-2026-001 总纲 T-5「批5 试验过程流：任务分配（M03.F02）→
数据录入（M03.F03）→ 审核/批准/发放/归档（M03.F05-F08）——流程状态机，
依赖 T-4」。用户以「继续」批准按总纲进入第五批，批2/3/4 同款授权形态。）

### 我的理解

批4 落了合同/接样/样品 25 端点；本批把试验过程域 **15 端点** 落成真实现：

| 生成路由段 | 端点数 | 功能 ID | 语义 |
|---|---|---|---|
| /api/receipts | 9（7 act + history + task） | M03.F01.I03 / F02.I01+I02 / F03.I02 / F05.I01 / F06.I01 / F07.I01 / F08.I01 / F09.I02 | 流程状态机 act 面 |
| /api/test-records | 6（list/create/get/update/delete/verdict） | M03.F03.I01 | 检测记录 |

语义逐条对照 lab-springboot `ReportFlowService`/`SampleReceiptService`/
`TestRecordService` + 两 Mapper + 两 Repository + 两 Controller：

1. **鉴权**：15 端点全部 `require_bearer`（批1-4 先例：无全局兜底，逐端点显式挂）。
2. **tenant 收口**：per-id 与 list 均 tenant-scoped；他人租户行 miss → 404/err。
   tenant 来源复用批2 `current_tenant_or_default`。
3. **act 七端点共享语义**（镜像 `ReportFlowService.actForStage`）：
   - **operator 双层 400**：契约必填缺失 → 校验层 400（批3 收口）；空串穿透契约 →
     impl 镜像 IAE → 400 `"operator is required"`。operator 校验**先于 per-id 循环**
     ——整批拒，一条不处理。
   - **body 缺省**：契约 body `Body(None)` 可缺省；impl 对 None 同 400 口径
     （镜像 springboot @Valid 拒空载）。
   - **逐条批量**：ids 逐条处理，单条失败不中断批，**HTTP 恒 200**；
     miss → `err("Receipt not found: {id}")`；stage 不符 →
     `err("Stage mismatch: requires {stage} but is {current}")`；非法转移 →
     `err("Invalid transition from {current} with {action}")`；
     成功 → `ok(id, target)`（`{id, ok: true, flowStatus: to}`，无 message 键）；
     err 项 `{id, ok: false, message}` 无 flowStatus 键（NON_NULL 镜像）。
   - **状态机转移表**（`ReportFlowService` 枚举映射，wire 值小写枚举名）：
     SUBMIT_NEXT 链 `receiving→task_assignment→data_entry→review→approval→
     issuance→archived`；RETURN_PREV 严格反向；WITHDRAW 仅 receiving（自转移
     写 history）；其余组合 → invalid transition。
   - **history 追加 wire 真值**：条目 `{action, from, to, operator, at, reason}`
     六键，action=submit/return/withdraw、from/to 用流转前后 wire 枚举值，
     operator=请求者；**reason null 强转 `""`**（镜像 springboot `js(null)→""`
     ——history 存储条目六键恒在，序列化侧 reason 键不缺席）。
   - **last_submitted_by 三态**：SUBMIT 写 operator；WITHDRAW 清空；RETURN 保留。
     updated_at=now 恒刷。三态 filter 的 submitted 分支依赖此字段（批4 只实锚 not_yet）。
4. **archived act 特例**（镜像 `actArchived`）：stage 必须 ARCHIVED（不符 →
   `err("Stage mismatch: requires archived but is {current}")`）；仅接受 SUBMIT
   （否则 `err("Action not allowed: archived accepts only submit but got {action}")`）；
   SUBMIT = ARCHIVED→ARCHIVED 自转移写 history（audit 语义），reason 缺省
   `"archived: post-archive audit"`。
5. **assignTask**（PUT /api/receipts/{id}/task，镜像 `SampleReceiptService.assignTask`）：
   - 三字段（assigneeId/assigneeName/plannedTestDate）None 跳过（部分更新）；
   - updatedAt 恒刷（无论是否推进）；
   - **仅 flow_status==RECEIVING 时**推进 task_assignment 并写 history
     （action=submit、**operator=assigneeName 非请求者**、from=receiving、
     to=task_assignment、reason="M03.F02 任务分配"）；
   - **任何 stage 都可 assign**（非 RECEIVING 只刷字段不推进）；
   - **不走 transitionTo：last_submitted_by 不写**（springboot assignTask 直写
     flowStatus+history，实证推翻 transitionTo 推断）；
   - assigneeName 为 None 时 RECEIVING 上仍推进，history operator 强转空串
     （appendHistory js(null)→"" 镜像）。
6. **history 端点**（GET /api/receipts/{id}/history）：miss → 404；flow_history
   空/`[]`/坏 JSON → `[]`（parseHistory 镜像）；命中 → 条目列表（六键恒在）。
7. **test-records 六端点**（镜像 `TestRecordService`/`TestRecordMapper`/
   `TestRecordRepository`）：
   - **list envelope**：items/page(??1)/pageSize(??20)/total=size；**仅 sampleId
     过滤**，ORDER BY `updated_at DESC, id`；**parameterCode 契约入参存在但
     springboot controller 接受后不传 service（不过滤）——镜像同款忽略，注释标注**。
   - **create**：契约必填（sampleId/parameterCode/requirement/result）缺失 →
     校验层 400；id = `TR-`+UUID；无业务前置校验（sample/parameter FK 不复验，
     撞 FK → 500 双侧一致不测）；createdAt/updatedAt=now。
   - **update**：miss → 404；六字段（parameterCode/standardCode/requirementCode/
     requirement/result/verdict）None 跳过 + updatedAt=now；**sample_id 不在
     applyUpdate 列（业务键建后恒定，镜像「有意遗漏」）**。
   - **verdict**（PATCH /{id}/verdict，双侧生成 API 一致）：只改 verdict+updatedAt；miss → 404。
   - **delete**：miss → 404；命中 → 204（组合根 204 收口追加 `/api/test-records/`
     前缀）；samples.sample_id → test_records FK 为 CASCADE（删样品级联删记录，
     双侧一致不特判）。
8. **无 flow 语义的部分**：本批 receipt create 仍恒 receiving/[]/''；COMPLETED
   枚举值两侧 service 均不可达，不实现不测。contract-test 仓无同步义务（15 端点
   全部已在 shared 契约且 springboot 已实现，本批是补实现非契约变化，§2 不触发）。

硬约束：API/DTO/实体生成物零手改；实现只写 impl/ 缝（receipts act/history/task
并入批4 `receipts_impl.py` 或新缝文件，test-records 新 `test_records_impl.py`）；
测试零种子依赖全走 API create（测试样品/记录全经 API 建）。

### 澄清记录

| 疑问 | 澄清结论 | 案件澄清人 | 日期 |
|---|---|---|---|
| 样品 CRUD 归属：springboot 树挂 M03.F03.I01-I05，本仓要不要登记？ | 不登记：本仓批4 已裁 samples 归 M03.F01.I02（澄清记录第 1 条），双 ID 双账禁止；本批 F03 节只登记真锚点（test-records + data-entry act） | claude（实证 springboot SampleService 纯 CRUD 零流转；本仓批4 澄清记录在先） | 2026-09-30 |
| flowQueue 端点要不要实现？ | 不实现：springboot `SampleReceiptService.flowQueue` 存在但 controller 无挂载（树 M03.F05.I01/F07.I01/F08.I01 均「已废弃：共享端点删除，队列走前端列表筛选」）；API 面只认生成物，fastapi 生成物无此路由 | claude（实证 springboot controller 无 queue 路由 + fastapi receipts_api.py 路径表） | 2026-09-30 |
| URL 段名与状态枚举值不一致怎么办？ | 以生成路由 wire 字面量为准：`assigning`（≠task_assignment）、`data-entry`（≠data_entry）、`approve`（≠approval）；impl 按路由绑定的 FlowStatus 常量比对 stage，URL 段名只是路径 | claude（实证 fastapi receipts_api.py 七个 act 路径字面量） | 2026-09-30 |
| list 的 parameterCode 参数过滤吗？ | 不过滤：springboot controller 签名收 parameterCode 但只传 sampleId 给 service——镜像同款接受不过滤（差异如实保留，impl 注释标注）；fastapi 生成 stub 签名收参，impl 不使用 | claude（实证 springboot TestRecordController.testRecordsListTestRecords 全文） | 2026-09-30 |
| FlowStatus.COMPLETED 枚举值怎么处理？ | 不实现不测：两侧 service 均无引用（springboot ReportFlowService/SampleReceiptService 零命中；fastapi enums 镜像生成物）；转移链终点是 archived 不是 completed | claude（grep 实证两侧 service 零命中） | 2026-09-30 |
| history 条目 reason=null 时形状？ | 存储侧强转空串：springboot appendHistory `js(null)→""`，条目六键恒在；fastapi 存储侧同款强转，序列化 reason 键不缺席（NON_NULL 只剔 None，空串保留） | claude（实证 SampleReceiptMapper.js() + appendHistory 格式串） | 2026-09-30 |
| assignTask 推进时 lastSubmittedBy 写不写？ | **不写**：springboot assignTask 直写 flowStatus+history（entity.setFlowStatus + appendHistory），不走 transitionTo → last_submitted_by 不动；快测断言相应修正。assigneeName=None 时 RECEIVING 上仍推进，operator 强转空串（js() 镜像） | claude（实证 SampleReceiptService.assignTask 全文） | 2026-09-30 |
| 详情行（springboot F05.I02/F06.I02/F07.I02/F08.I02）要不要登记？ | 不登记：GET receipt 详情面批4 已上线（本仓 F09.I01），act 行是本批新增的独立端点语义，详情行语义已被 F09.I01 覆盖，登记即双账 | claude（本仓批4 F09.I01 已验收在先） | 2026-09-30 |

## 2. 验收标准

| 编号 | 场景（给定） | 操作（当） | 面预期（则） |
|---|---|---|---|
| AC-1 | 新建 receipt（receiving） | 七 stage act 端点全转移矩阵（SUBMIT 链到底 / RETURN 反向 / WITHDRAW 仅 receiving / archived 仅 SUBMIT） | ok 项 `{id, ok, flowStatus}` / err 项 `{id, ok:false, message}`、HTTP 恒 200、单条失败不中断批；状态机按转移表精确走 |
| AC-2 | 批量 ids 混合命中/miss/stage 不符 | 一次 act 多 id | ok/err 逐条独立；miss/stage 不符/非法转移三种 err 文案逐字镜像；批次整体 HTTP 200 |
| AC-3 | operator 缺失/空串 | act 无 operator 或 operator="" | 契约必填缺失 → 400 校验层；空串 → 400 `"operator is required"`；均先于 per-id 循环（整批拒） |
| AC-4 | RECEIVING receipt | PUT /{id}/task 带三字段 / 部分 None / 非 RECEIVING | 字段 None 跳过；仅 RECEIVING 推进 + history operator=assigneeName；非 RECEIVING 只刷字段；updatedAt 恒刷 |
| AC-5 | 流转过的 receipt | GET /{id}/history | 条目六键恒在（reason 空串场景验证）；空 history → []；miss → 404；with last_submitted_by 三态（SUBMIT 写/WITHDRAW 清/RETURN 保留） |
| AC-6 | sample 存在 | test-records CRUD 全链路 | envelope 1/20 回显、sampleId 过滤、TR- 前缀、部分更新六字段、sample_id 不可改、verdict 改判、delete 204 |
| AC-7 | 批5 流转数据 | receipts list filter=submitted | 命中 last_submitted_by 非空 + 从指定 stage submit 过的单；not_yet 分支批4 已锚不变 |
| AC-8 | tenant 隔离 | TENANT-002 token 操作 TENANT-001 的 receipt/记录 | list 不可见；act/assignment/history/记录 CRUD 均 404/err |
| AC-9 | 全部实现完成 | suite 门禁 L1-L5 | 全绿（red-first：测试先红后绿；trace 挂 10 个 I ID；L4 打 scratch 库） |

## 3. 任务拆解

| 任务 ID | 任务描述 | 类型 | 负责人 | 预估 | 状态 |
|---|---|---|---|---|---|
| T-0 | 需求文档门：本文件 + 功能树 6 F 行翻开发中 + 10 个 I 子项登记 + README 台账行 | 文档 | claude | 小 | 已完成（2026-09-30） |
| T-1 | red-first：tests/test_flow_test_records.py 全断言（挂 10 个 I ID；7 act 全转移矩阵 + 批量 ok/err + operator 双层 + assignTask 两态 + history + test-records 全链 + 三态 filter submitted 深测） | 测试 | claude | 中 | 已完成（12/12 转绿 2026-09-30） |
| T-2 | impl：receipts act 7 + history + task（并入批4 receipts_impl.py）+ test_records_impl.py 六端点 + app.py 204 收口追加 /api/test-records/ 前缀 | 开发 | claude | 中 | 已完成（2026-09-30） |
| T-3 | 收口：树 6F+10I 翻已上线；trace 实测修正本文档预写；门禁 L1-L5 全绿；双仓收账 commit | 收口 | claude | 小 | 已完成（2026-10-01；14 测试/10 I ID 全挂 trace，89 passed） |

## 4. 功能影响

| 功能 ID | 功能名称 | 影响类型 | 说明 | 关联任务 |
|---|---|---|---|---|
| M03.F01 | 接样管理 | 变更 | 已上线功能追加子项 I03（receiving act） | T-1～T-3 |
| M03.F02 | 任务分配 | 变更 | 规划→开发中；新增子项 I01/I02 | T-1～T-3 |
| M03.F03 | 数据录入 | 变更 | 规划→开发中；新增子项 I01/I02（样品 CRUD 已归 F01.I02，不重复登记） | T-1～T-3 |
| M03.F05 | 报告审核 | 变更 | 规划→开发中；新增子项 I01 | T-1～T-3 |
| M03.F06 | 报告批准 | 变更 | 规划→开发中；新增子项 I01 | T-1～T-3 |
| M03.F07 | 报告发放 | 变更 | 规划→开发中；新增子项 I01 | T-1～T-3 |
| M03.F08 | 报告归档 | 变更 | 规划→开发中；新增子项 I01 | T-1～T-3 |
| M03.F09 | 接样单详情 | 变更 | 已上线功能追加子项 I02（history） | T-1～T-3 |

新增：10（全部为 I 级子项）；变更：8（6 F 翻级 + F01/F09 追加子项）；删除：0。

## 4.5 遗留与开放问题

- 三态 filter submitted 分支的 live 对照（fastapi Python 判定 vs springboot native jsonb
  谓词）：unit 档 Python 侧等值判定已覆盖，live 对照归批6 contract-test live 接入（总纲 T-6）。
- saas-identity-platform-fastapi NON_NULL 收口回补（批4 遗留 open question）：与本批无关，
  保持 session.json open_questions 在册待人裁。

## 5. 流程影响

本批是家族 flow-function-map（springboot 仓在册）「接样→任务分配→数据录入→审核→批准→
发放→归档」链的首次端点级实锚：七 act 端点即该链的端点面，批4 锚定的初始态 receiving
之上补全整条 SUBMIT 链、RETURN 反向链、WITHDRAW 撤回（仅接样态自转移）与
archived audit 自转移。

## 6. 风险与回滚

| 风险 | 影响面 | 缓解 | 回滚方式 |
|---|---|---|---|
| Python 侧 act 批量/转移判定与 springboot 枚举映射偏差 | 7 act 端点 | 逐条镜像 ReportFlowService 枚举映射；err 文案逐字断言（not found/stage mismatch/invalid transition） | git revert 本批 commit |
| 三态 filter submitted Python 判定与 native jsonb 谓词语义偏差 | receipts list | 谓词逐条镜像（last_submitted_by 非空 + history 从指定 stage submit）；批6 live 对照兜底 | git revert 本批 commit |
| test_records envelope/FK 行为与 springboot 偏差 | 6 端点 | envelope 1/20 家族约定镜像；FK 撞库 500/CASCADE 双侧一致不特判（裁定入档） | git revert 本批 commit |

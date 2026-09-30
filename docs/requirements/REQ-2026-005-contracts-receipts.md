# REQ-2026-005 批4 合同与接样入口：合同管理 + 接样单 CRUD/详情（M02.F01 + M03.F01/F09）

| 项 | 值 |
|---|---|
| 提出人 | zcqiand |
| 提出日期 | 2026-09-30 |
| 优先级 | P0 |
| 状态 | 已验收（2026-09-30，T-0～T-3 全批完成） |
| 关联 ADR | REQ-2026-001（总纲 T-4）；REQ-2026-003/004（批2/批3 先例） |

## 1. 需求描述

### 用户原话

> 继续

（承接 lab 仓 REQ-2026-001 总纲 T-4「批4 合同与接样入口：合同管理（M02.F01）+
接样单 CRUD/详情（M03.F01、M03.F09）」，用户以「继续」批准按总纲进入第四批，
批2/批3 同款授权形态。）

### 我的理解

批3 落了码表四面 16 端点；本批把合同/接样/样品三个生成 API 面 **25 端点** 落成真实现：

| 生成路由段 | 端点数 | 功能 ID | 语义 |
|---|---|---|---|
| /api/contracts | 5（list/create/get/update/delete） | M02.F01 | 合同管理 |
| /api/receipts | 14（CRUD 5 + flow 7 + assign_task + history） | M03.F01（CRUD 5） | 接样单 |
| /api/samples | 6（list/create/get/update/delete/updateExt） | M03.F01.I02 + M03.F09 | 样品 |

**flow 7 端点 + assign_task + history 留批5**（总纲 T-5 试验过程流），本批不实现不测
（500 Not implemented 如实保留）。

语义逐条对照 lab-springboot `ContractService`/`SampleReceiptService`/`SampleService`
+ 三 Mapper + 三 Repository + 三 Controller：

1. **鉴权**：25 端点全部 `require_bearer`（批1-3 先例：无全局兜底，逐端点显式挂）。
2. **tenant 收口**：三面均 tenant-scoped；get/update/delete 按 `findByTenantIdAndId`
   定位，他人租户行 miss → 404（隔离）。tenant 来源复用批2 `current_tenant_or_default`。
3. **list 过滤**（镜像 Repository filter JPQL + `n()`）：
   - contracts：keyword 非空 → lower contains contract_code OR project_name；
     status 非空 → 等值（JPQL `:status IS NULL OR`——None 不过滤）；
     ORDER BY `updated_at DESC, contract_code`。
   - receipts：contractId 非空 → 等值（n()）；flowStatus 非空 → 等值（IS NULL 判空，
     Repository 注释「null='' 是 UNKNOWN 折叠 WHERE」）；keyword 非空 → contains
     commission_code OR project_name；ORDER BY `updated_at DESC, commission_code`。
     **filter 三态**（5.57 入契约）：仅认 "not_yet"/"submitted"，其它值（含 null）等同
     不传走原路径。not_yet=停在指定环节（无环节时=history 空）；submitted=已从指定环节
     submit（无环节时=history 非空且 last_submitted_by 非空）。springboot 走 native SQL
     jsonb 谓词；fastapi 镜像为 Python 侧等值判定（结果集有限，语义恒等，注释标注）。
   - samples：receiptId 非空 → 等值；keyword 非空 → contains sample_code OR sample_name；
     ORDER BY `created_at DESC, sample_code`。
   - **envelope：items 恒全量 + page??1 + pageSize??20 + total=size**。⚠️ 与批3 catalog 的
     `pageSize??size` 有意不同——springboot 三控制器注释「2026-09-16 T11 live 实证：
     list envelope 缺省值对齐家族约定 page=1 / pageSize=20（nextjs oracle pageOf 默认）」，
     各自对照各自参照。
4. **create**（镜像 fromCreate*）：
   - contract：契约必填缺失 → 校验层 400；**无 requireNonBlank**（ContractMapper 无 IAE）；
     status null → ACTIVE；id = `C-`+UUID；createdAt/updatedAt=now。
     unique(tenant_id, contract_code) 撞 → 500 双侧一致不测（批2 裁定）。
   - receipt：**contractId 必须存在**（tenant-scoped miss → 404 "Contract not found"，
     Service create 前置校验）；flowStatus=receiving、flowHistory=[]、result=''（
     ReceiptResult.EMPTY）；id = `R-`+UUID。unique(tenant_id, commission_code) 撞 → 500 不测。
   - sample：**receiptId 必须存在**（miss → 404 "Receipt not found"）；ext null → {}；
     id = `S-`+UUID。
   - 列表字段：judgment_basis/testing_basis/test_parameters null/空 → `[]`
     （serializeStringList 镜像；toDto 侧恒回 list 恒不回 null）。
5. **update**（镜像 applyUpdate*）：miss → 404；部分更新 None 跳过 + updatedAt=now；
   **无空载荷 400 特判**。⚠️ **业务码不可改**：UpdateContractRequest虽有 contractCode 字段、
   UpdateSampleRequest 虽有 receiptId/sampleCode 字段，但 applyUpdate 均不触及（有意遗漏，
   镜像 mapper 原样）；receipt update 亦不改 contractId、category FK 不复验。
6. **updateExt（samples）**：5.89 契约 ext 必填（缺省 → 校验层 400）；**整体替换**
   （合并是前端职责，react ReportPreviewModal 提交前已合并——springboot 注释锚定）。
7. **delete**：miss → 404；命中 → 204（组合根收口追加 `/api/contracts/`、`/api/receipts/`、
   `/api/samples/` DELETE 前缀）。FK：receipts.contract_id → contracts RESTRICT、
   samples.receipt_id → receipts CASCADE——删除撞 FK 500 / 级联删样品均双侧一致，不特判不测
   （批2 裁定）。
8. **无 flow 语义**：本批创建的 receipt 恒 receiving/[]/''，三态 filter 的 submitted
   分支需批5 流转数据方可实锚。

硬约束：API/DTO/实体生成物零手改；实现只写 impl/ 缝；测试零种子依赖全走 API create
（receipt 的 categoryCode FK → inspection_report_names，用批2 report-names create 先建）。

### 澄清记录

| 疑问 | 澄清结论 | 澄清人 | 日期 |
|---|---|---|---|
| samples_api 6 端点归属哪批哪个 F？springboot SampleService javadoc 标「M03.F02/F03」 | 归批4 落地、锚定 M03.F01.I02（接样录入面：接样单与样品同录）：样品 CRUD 无流程语义，F02/F03 的真锚点（assignTask=任务分配、test-records=数据录入）留批5。springboot javadoc 是过程域宽泛标注（样品服务于任务/数据录入环节），非 CRUD 端点归属证明 | claude（实证 SampleService 方法面：纯 CRUD + ext 补录，零流转逻辑） | 2026-09-30 |
| list envelope 缺省 pageSize=20 与批3 catalog pageSize??size 冲突？ | 不冲突：springboot 两处实现原样不同（catalog 控制器 pageSize??size；合同/接样/样品控制器 page=1/pageSize=20 且注释锚定 T11 live 实证对齐 nextjs oracle）。各自对照各自参照，镜像差异如实保留 | claude（实证三控制器 + InspectionCatalogController 对照） | 2026-09-30 |
| receipts list 的 filter 三态参数归批4 还是批5？ | 归批4：它是 list 端点的过滤语义（5.57 已入契约），非流程转移动作。批4 只能实锚 not_yet 分支（无流转数据），submitted 分支批5 补深测 | claude | 2026-09-30 |
| update 载荷带 contractCode/receiptId/sampleCode 会改吗？ | 不会：applyUpdate 三 mapper 均不触及业务码（contract_code 建后恒定；换 receipt 用 delete+重建）。fastapi 同样跳过这些字段——是镜像「有意遗漏」不是 None-skip 惯例的推论 | claude（实证 ContractMapper.applyUpdate/SampleMapper.applyUpdate 全文） | 2026-09-30 |
| null 可选字段在 JSON 响应里是键存在值 null 还是键不存在？ | 键不存在：springboot 全家族 DTO 逐类 @JsonInclude(NON_NULL)（T11 live 实证 GET receipt 无 issuedAt 键）。fastapi 组合根 include 前对全部 APIRoute 挂 response_model_exclude_none=True（include 复制路由时固化进 handler 闭包，生成区零改动）。批1-3 的 12 处「键值 is None」断言系当时镜像偏差，本批统一翻转为「键不存在」并全量回归（75 passed） | claude（实证 springboot SampleReceipt.java 等 DTO 注解 + Jackson NON_NULL 递归语义） | 2026-09-30 |

## 2. 验收标准

| 编号 | 场景（给定） | 操作（当） | 预期（则） |
|---|---|---|---|
| AC-1 | 有效 Bearer + 租户内合同 | 合同 CRUD 全链路（list 过滤 keyword/status、get、部分更新、delete） | 200/204/404 语义符合镜像；contract_code 建后不可改；status 缺省 active |
| AC-2 | 有效载荷 | 接样单 create/get/update/delete | 默认 flowStatus=receiving、flowHistory=[]、result=""；contractId 不存在 → 404；contractId 不可改 |
| AC-3 | receipts list 带 filter | filter=not_yet / submitted / 其它值 | not_yet 命中新单（history 空）；submitted 空（无流转数据）；其它值等同不传 |
| AC-4 | 既有 receipt | 样品 CRUD + updateExt | ext 缺省 {}；updateExt 整体替换；缺 ext → 400；receiptId 不存在 → 404；receiptId/sampleCode 不可改 |
| AC-5 | 接样单 + 样品 | GET receipt + GET samples?receiptId= | 详情面两路数据齐备（接样信息全字段 + 样品清单按 createdAt DESC, sample_code） |
| AC-6 | tenant 隔离 | TENANT-002 token 操作 TENANT-001 的合同/接样单/样品 | list 不可见；get/update/delete 404；跨租户 FK 引用 create → 404 |
| AC-7 | 全部实现完成 | suite 门禁 L1-L5 | 全绿（red-first：测试先红后绿，trace 挂 4 个 I ID；L4 打 scratch 库） |

## 3. 任务拆解

| 任务 ID | 任务描述 | 类型 | 负责人 | 预估 | 状态 |
|---|---|---|---|---|---|
| T-0 | 需求文档门：本文件 + 功能树 M02.F01/M03.F01/M03.F09 翻开发中 + 4 个 I 子项登记 + README 台账行 | 文档 | claude | 小 | 已完成（2026-09-30） |
| T-1 | red-first：tests/test_contracts_receipts.py 全断言（挂 4 个 I ID，零种子依赖全走 API create） | 测试 | claude | 中 | 已完成（2026-09-30，7 断言 red→green） |
| T-2 | impl：contracts/receipts/samples 三 impl 缝 25 端点（flow 7 + assign + history 留批5）+ app.py 204 收口追加三前缀 | 开发 | claude | 中 | 已完成（2026-09-30） |
| T-3 | 收口：功能树 3F+4I 翻「已上线」；门禁 L1-L5 全绿；trace 收账；双仓收账 commit | 收口 | claude | 小 | 已完成（2026-09-30，门禁 exit=0，trace 75 条含 7 处批4 映射；T-2 收口发现并落地家族级 NON_NULL 序列化镜像——见澄清记录） |

## 4. 功能影响

| 功能 ID | 功能名称 | 影响类型 | 说明 | 关联任务 |
|---|---|---|---|---|
| M02.F01 | 合同管理 | 变更 | 状态 规划→已上线；新增子项 I01 | T-1～T-3 |
| M03.F01 | 接样管理 | 变更 | 状态 规划→已上线；新增子项 I01/I02（CRUD 面；流程状态机归批5） | T-1～T-3 |
| M03.F09 | 接样单详情 | 变更 | 状态 规划→已上线；新增子项 I01（receipt GET + samples 清单；检测数据归批5） | T-1～T-3 |

新增：4（全部为 I 级子项）；变更：3；删除：0。

## 5. 流程影响

无端点级流程落地（flow 7 端点留批5）；flow-function-map.md 的 接样→…→归档 映射
自批5 起逐步实锚，本批仅锚定接样单初始态 receiving。

## 6. 风险与回滚

| 风险 | 影响面 | 缓解 | 回滚方式 |
|---|---|---|---|
| 三面 CRUD 与批3 字典面口径漂移（envelope 20 vs size 等） | 家族一致性 | 逐面对照各自 springboot 控制器/Repository 实证；差异点全部注释标注来源 | git revert 本批 commit |
| 三态 filter Python 侧判定与 native jsonb SQL 语义偏差 | receipts list | 谓词逐条镜像（history 空判、last_submitted_by 非空判、stage 等值/非等值）；批5 落流转后加 live 对照 | git revert 本批 commit |
| samples 锚定 M03.F01 与 springboot javadoc F02/F03 不一致 | 功能树账实 | 澄清记录第 1 条已实证裁定；批5 F02/F03 落地时以真锚点（assignTask/test-records）登记，不冲突 | 功能树行随批5 复核 |

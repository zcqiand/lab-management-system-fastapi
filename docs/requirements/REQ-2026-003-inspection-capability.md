# REQ-2026-003 批2 检测能力八件：专项/项目/参数/标准/计算方法/技术要求/报告名称/参数界面

| 项 | 值 |
|---|---|
| 提出人 | zcqiand |
| 提出日期 | 2026-09-30 |
| 优先级 | P0 |
| 状态 | 已验收（2026-09-30，T-0～T-4 全批完成） |
| 关联 ADR | REQ-2026-001（总纲 T-2）；REQ-2026-002（批1 基座与组合根） |

## 1. 需求描述

### 用户原话

> 继续

（承接 lab 仓 REQ-2026-001 总纲 T-2「批2 检测能力八件：专项/项目/参数/标准/计算方法/技术要求/报告名称/参数界面（M06.F01-F08）——lab 业务字典根」，用户以「继续」批准按总纲进入第二批。范围/口径拍板见总纲 §1 三项。）

### 我的理解

批1 落了认证域（内存目录，不连库）；本批起接入 PG 真库（`DATABASE_URL` 引擎已装配、
`entities.py` 26 实体已生成），把 M06 检测能力字典 5 个生成 API 面 **60 端点**从「未实现
500 兜底」落成真实现，语义逐条对齐 lab-springboot（InspectionDictionaryService /
InspectionJunctionService / CalculationMethodService / TechnicalRequirementService /
InspectionReportNameService / ParamInterfaceService + 各 Controller/Mapper/Repository）：

| 生成 API 面 | 功能 ID | 端点数 | 家族语义要点（springboot 参照） |
|---|---|---|---|
| inspection_dictionary | M06.F01-F04 | 28 | 4 实体（specialty/object/parameter/standard）CRUD + 4 junction 家族 link/unlink/list；全部**平台级**（无 tenant_id，per V012） |
| calculation_methods | M06.F05 | 5 | 复合主键 (object, parameter)；平台级 |
| technical_requirements | M06.F06 | 5 | 业务三键 (object, parameter, judgmentStandard)；**tenant-scoped**（claim tenant_id，缺省回退 directory 默认租户 TENANT-001——镜像 `currentTenantIdOrDefault()`，目录配置非字面量兜底） |
| report_names | M06.F07 | 14 | CRUD + ext_fields jsonb 模板 + 3 junction 家族（object/parameter/standard，standard 带 role）；平台级 |
| param_interfaces | M06.F08 | 8 | CRUD + config jsonb + 参数↔界面 link（link 行 config jsonb）；平台级 |

关键镜像语义（全批统一）：

1. **鉴权**：60 端点全部 `require_bearer`（批1 先例：无全局兜底，逐端点显式挂）。
2. **list 分页形**：Page 包裹端点接受 page/pageSize 但**不用作过滤**（数据量小，镜像
   springboot controller 注释），返回 items=过滤后全量、page=`page??1`、
   pageSize=`pageSize??list.size()`、total=list.size()；junction list 固定 page=1、
   pageSize=size。tech_req 与 calculation_methods 契约返裸 `List[T]`（无包裹）。
3. **过滤**：keyword 大小写不敏感 contains 于 code OR name（None→不过滤）；sort_order,
   code 排序（tech_req 按 sortOrder + 三键，calculation 按 sortOrder + 双键）。
4. **create**：必填缺失 → 400（镜像 IAE message）；默认值逐一镜像（isOfficial/enabled=
   true、isOptionalForQualification=false、sortOrder=0；parameter rawName/canonicalName
   默认=name、aliases=[]、sourceType=official；standard status=active；calc
   algorithmType=manual、specimenCount=1；techreq valueType=numeric、comparison=u、
   judgmentMode=manual、verificationStatus=draft）；created_at/updated_at=UTC ISO 字符串
   （PG 侧 Text 列）。
5. **update**：部分更新（None 跳过字段）、updated_at=now；miss → 404 NOT_FOUND。
6. **delete**：miss → 404；命中 → 204。FK RESTRICT 冲突（如删被项目引用的专项）双侧
   均为 500（springboot 无 DataIntegrityViolation handler，fastapi 同样不特判——镜像
   一致性优先）。
7. **junction link**：字段 null/blank → 400；save() = upsert（同 PK 覆盖既有行，含
   config/qualificationLevel 等载荷字段回写）；**unlink 幂等 204**（未命中静默 no-op，
   REQ-2026-001 Task 2.6 四方一致口径）。
8. **jsonb**：parameter.aliases / report_name.ext_fields / param_interface.config /
   param_interface_link.config 四列 JSONB ↔ pydantic 模型直转（SQLAlchemy JSONB 列
   天然 dict/list，无需 springboot 的 String 序列化层）。

硬约束：API/DTO/实体生成物零手改；实现只写 impl/ 缝（app.py 组合根批1 已就位，
`_ROUTERS` 已挂全部 13 个生成 router，缝发现 `subclasses[0]` 自动生效）；DB 读写走
`RequestContext.session`（批1 中间件已建）。

### 澄清记录

| 疑问 | 澄清结论 | 澄清人 | 日期 |
|---|---|---|---|
| 生成 `inspection_catalog_api` 命名像检测能力，实为何物 | 实为型号/规格/等级/牌号（brands/grades/models/specs，M04.F06-F09 批3 范围）；批2 用的是 inspection_dictionary_api（specialty/object/parameter/standard）——按生成 models 实证，不按命名直觉 | claude | 2026-09-30 |
| 项目↔标准（object_standard_links）归属：树 F02 说明「专项/参数关联」、F03「标准/参数关联」、F04 只写 CRUD | 裁定：F02.I02=专项↔项目+项目↔参数；F03.I02=标准↔参数；F04.I02=项目↔标准（role 维度）。契约面不变，仅树归属 | claude | 2026-09-30 |
| 批2 L4 打 PG 真库，gate 需注入 DATABASE_URL | 需人裁将 lab-management-system-fastapi 加入 `scripts/gate.py L4_DB_INJECT_REPOS`（先例 2026-09-29 saas-identity-platform-fastapi 同语义入表）；测试在同服务器建 scratch 库 `lab_fastapi_scratch` 用后必 DROP，不直改 lab_test 种子 | 已人裁（2026-09-30 批准入表+开工） | 2026-09-30 |
| tech_req 三键同键跨租户可否并存（种子设计） | 不可。PG PK=三键（tenant_id 是普通索引列），同三键第二行 UniqueViolation——schema 事实，springboot TechnicalRequirementKey 四部件在 PG 侧不可表达。测试改用异三键双租户行（TENANT-001@PAR-A / TENANT-002@PAR-B）验 tenant 收口 | claude（实证 generated entities PK） | 2026-09-30 |

## 2. 验收标准

| 编号 | 场景（给定） | 操作（当） | 预期（则） |
|---|---|---|---|
| AC-1 | 有效 Bearer + 种子字典数据 | GET 四实体 list（带/不带 keyword、status、sourceType 过滤） | 200 Page 包裹：items 全量、page/pageSize/total 语义符合镜像；keyword 大小写不敏感命中 code/name |
| AC-2 | 有效载荷 | POST 创建四实体 + 计算方法 + 技术要求 + 报告名称 + 参数界面 | 200 返回建后实体，默认值逐一符合镜像；缺必填 → 400 |
| AC-3 | 既有 code | PATCH（update） | 200 部分更新生效；不存在 code → 404 NOT_FOUND |
| AC-4 | 既有/不存在 code | DELETE | 既有 → 204；不存在 → 404 |
| AC-5 | junction 载荷 | link 两次同键（第二次带不同载荷）+ unlink 一次 + unlink 再一次 | link 均 204（第二次覆盖载荷）；unlink 均 204（幂等）；list 反映状态 |
| AC-6 | 技术要求 tenant 收口 | 带 tenant_id claim / 不带 claim 的 token 分别调用 | claim 租户隔离可见性；无 claim 落 directory 默认租户（TENANT-001） |
| AC-7 | 全部实现完成 | suite 门禁 L1-L5 | 全绿（red-first：测试先红后绿，trace 挂 13 个功能 ID；L4 打 scratch 库） |

## 3. 任务拆解

| 任务 ID | 任务描述 | 类型 | 负责人 | 预估 | 状态 |
|---|---|---|---|---|---|
| T-0 | 【待人裁】`L4_DB_INJECT_REPOS` 入表 lab-management-system-fastapi（门禁语义改动，ADR-0038 表纪律） | 门禁 | zcqiand | 小 | 已完成（2026-09-30，人裁批准入表，注释链同 saas fastapi 先例） |
| T-1 | red-first：conftest 增补 scratch 库 fixture（镜像 saas 配方：DROP/CREATE `lab_fastapi_scratch` + create_all + 收工 DROP，fail-fast 在 fixture）+ 字典种子 + 5 个测试文件全断言（挂 13 个 I ID） | 测试 | claude | 大 | 已完成（2026-09-30，40 断言 red→green；conftest 补回 trace 适配器双钩子——批2 重写时遗失，L5 实证） |
| T-2 | impl 字典面：InspectionDictionaryApiImpl 28 端点（4 实体 CRUD + 4 junction 家族） | 开发 | claude | 大 | 已完成（2026-09-30，204 走组合根收口镜像 saas 先例，零 type: ignore） |
| T-3 | impl 其余四面：CalculationMethodsApiImpl(5) + TechnicalRequirementsApiImpl(5，tenant 收口) + ReportNamesApiImpl(14) + ParamInterfacesApiImpl(8) | 开发 | claude | 大 | 已完成（2026-09-30，techreq tenant 收口 + comparison 缺失 400 裁定 + ext_fields jsonb 归一化） |
| T-4 | 收口：功能树 8F+13I 翻「已上线」；门禁 L1-L5 全绿；trace 收账；双仓收账 commit | 收口 | claude | 中 | 已完成（2026-09-30，门禁 exit=0，trace 63 条含 40 处 M06 映射） |

## 4. 功能影响

| 功能 ID | 功能名称 | 影响类型 | 说明 | 关联任务 |
|---|---|---|---|---|
| M06.F01 | 检测专项 | 变更 | 状态 规划→已上线；新增子项 I01 | T-1～T-4 |
| M06.F02 | 检测项目 | 变更 | 状态 规划→已上线；新增子项 I01（CRUD）/I02（专项↔项目+项目↔参数） | T-1～T-4 |
| M06.F03 | 检测参数 | 变更 | 状态 规划→已上线；新增子项 I01（CRUD+aliases）/I02（标准↔参数） | T-1～T-4 |
| M06.F04 | 检测标准 | 变更 | 状态 规划→已上线；新增子项 I01（CRUD+status）/I02（项目↔标准，role） | T-1～T-4 |
| M06.F05 | 计算方法 | 变更 | 状态 规划→已上线；新增子项 I01（复合主键 CRUD+双过滤） | T-1～T-4 |
| M06.F06 | 技术要求 | 变更 | 状态 规划→已上线；新增子项 I01（三键 CRUD+四维过滤+tenant 收口） | T-1～T-4 |
| M06.F07 | 报告名称 | 变更 | 状态 规划→已上线；新增子项 I01（CRUD+extFields）/I02（三关联家族） | T-1～T-4 |
| M06.F08 | 参数界面 | 变更 | 状态 规划→已上线；新增子项 I01（CRUD+config）/I02（参数↔界面 link） | T-1～T-4 |

新增：13（全部为 I 级子项，随 F 行登记，编号为本仓首拆）；变更：8；删除：0。

## 5. 流程影响

无（M06 是字典维护域，无流程图；flow-function-map.md 的过程流映射不涉及本批）。

## 6. 风险与回滚

| 风险 | 影响面 | 缓解 | 回滚方式 |
|---|---|---|---|
| 语义与家族分叉（过滤/默认值/幂等口径） | contract-test 批6 接入 | 逐条对照 springboot Service/Mapper/Repository 实现，注释标注参照方法 | git revert 本批 commit |
| 60 端点体量大 | 单批回归面 | 按 5 个 API 面分文件实现与测试（T-2/T-3 分任务）；junction 家族形状统一抽 helper | 各 API 面独立可回退 |
| L4 打远程 PG 轮换假红 | 门禁稳定性 | scratch 库同服务器镜像 saas 配方；假红先 ping 看丢包隔离复跑（家族在册配方） | 断言失败即红，无静默 |
| FK RESTRICT 删除 500（双侧一致） | 边缘路径 | 镜像 springboot 无特判；契约测试不覆盖 500 路径（msw 无法表达），批6 live 同口径 | 无需回滚（一致性即正确） |
| gate L4_DB_INJECT_REPOS 入表未裁 | 门禁语义 | T-0 显式人裁，不偷跑（表纪律：入表必须人裁+账本登记） | 出表即回退 |

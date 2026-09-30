# REQ-2026-004 批3 基础数据四件：型号/规格/等级/牌号码表（M04.F06-F09）

| 项 | 值 |
|---|---|
| 提出人 | zcqiand |
| 提出日期 | 2026-09-30 |
| 优先级 | P0 |
| 状态 | 已验收（2026-09-30，T-0～T-3 全批完成） |
| 关联 ADR | REQ-2026-001（总纲 T-3）；REQ-2026-003（批2 检测能力与共享基建） |

## 1. 需求描述

### 用户原话

> 继续

（承接 lab 仓 REQ-2026-001 总纲 T-3「批3 基础数据：型号/规格/等级/牌号维护（M04.F06-F09），
列表按检测专项过滤，依赖 T-2」，用户以「继续」批准按总纲进入第三批。）

### 我的理解

批2 落了检测能力字典 5 面 60 端点（PG 真库 + tenant 收口 + 204 组合根收口）；本批把
`inspection_catalog` 生成 API 面 **16 端点**（4 实体 × list/create/update/delete）落成真实现，
语义逐条对齐 lab-springboot `CatalogService` / `InspectionCatalogMapper` / 各 Repository
（4 表同构同语义，springboot 合并在一个 service——fastapi 同样合并在一个 impl 缝）。

功能 ID ↔ 实体对应（按 springboot service 注释锚定，不按字母序直觉）：

| 生成路由段 | 实体 | 功能 ID | 语义 |
|---|---|---|---|
| /api/catalog/models | InspectionModels | M04.F06 | 型号码表 |
| /api/catalog/specs | InspectionSpecs | M04.F07 | 规格码表 |
| /api/catalog/grades | InspectionGrades | M04.F08 | 等级码表 |
| /api/catalog/brands | InspectionBrands | M04.F09 | 牌号码表 |

关键镜像语义（springboot 参照方法逐条标注）：

1. **鉴权**：16 端点全部 `require_bearer`（批1/批2 先例：无全局兜底，逐端点显式挂）。
2. **tenant 收口**：4 表均带 `tenant_id NOT NULL`；list 按 tenant 等值过滤，update/delete
   按 `findByTenantIdAndCode` 定位——他人租户同 code 行 miss → 404（隔离语义）。
   tenant 来源 = claim tenant_id 非空用之否则 directory 默认租户（复用批2
   `current_tenant_or_default` helper，镜像 `CatalogService` javadoc「controller 注入 +
   ConfigUserDirectory 默认租户」）。
3. **list 过滤**（镜像 Repository `filter` JPQL + Service `n()`）：
   `inspectionObjectCode` null→"" 恒不过滤（`'' OR 等值`），非空→等值；`keyword` null→""
   不过滤，非空→lower(code) contains OR lower(name) contains。排序 `ORDER BY sort_order, code`。
   Page 包裹（与 shared `Page<T>` 一致）：items=过滤后全量、page=`page??1`、
   pageSize=`pageSize??list.size()`、total=size（批2 同款，分页参数不作过滤）。
4. **create**（镜像 `fromCreate*`）：code/name 必填（契约 DTO required，校验层 400 收口）；
   `sortOrder` null→0；tenantId=当前租户；createdAt/updatedAt=now（UTC ISO）。
   **撞 (tenant, code)**：springboot `save()` 对手工 ID 实体 = JPA merge → 覆盖既有行
   （fastapi 镜像：get 命中→全字段覆盖**含 createdAt=now**，批2 字典面实体 create 同款先例；
   注意与 junction 的 `upsert_junction` 不同——junction 载荷不含 created_at）。
5. **update**（镜像 `applyUpdate*`）：miss（含他人租户行）→ 404；部分更新
   （inspectionObjectCode/name/remark/sortOrder 逐字段 None 跳过）+ updatedAt=now。
   **无「空载荷 400」特判**——springboot applyUpdate 原样没有该检查（全 None 载荷仅刷
   updatedAt；与批2 report_names/techreq 的 empty-400 是有意的镜像差异，各自对照各自参照）。
6. **delete**（镜像 Service delete*）：miss → 404；命中 → 204（组合根收口，本批追加
   `/api/catalog/` DELETE 前缀条件）。FK RESTRICT（grade 等被 technical_requirements 引用）
   → 500 双侧一致（批2 同款裁定，无特判）。
7. **无 get-by-code 端点**：catalog 契约只有 list/create/update/delete 四类（批2 字典面有
   GET 单体，本面没有）。

硬约束：API/DTO/实体生成物零手改；实现只写 impl/ 缝；`InspectionModel`（DTO）与
`InspectionModels`（实体）同名异指，import 时注意。测试数据全部走 API create 建立零种子
依赖（conftest 既有 grades 种子行 tenant_id=""，PK=code 单键会占 C25/C30——测试用例避开
这两个 code）。

### 澄清记录

| 疑问 | 澄清结论 | 澄清人 | 日期 |
|---|---|---|---|
| 树说明「官方数据码表」与实体 `tenant_id NOT NULL` 矛盾？ | 不矛盾：springboot CatalogService 是 tenant-scoped（list/create/update/delete 全带 tenantId），「官方」指数据内容来源（国标码表），不代表平台级共享。fastapi 按tenant-scoped 镜像（实体列 NOT NULL 是 schema 事实佐证） | claude（实证 CatalogService javadoc + 实体列） | 2026-09-30 |
| create 撞 (tenant, code) 是 500 还是 upsert？ | upsert：JPA `save()` 对手工赋 ID 实体走 merge（isNew=false）→ 覆盖既有行。批2 字典面实体 create 已按此镜像（含 createdAt=now），批3 同款 | claude（实证 SimpleJpaRepository.save 语义 + 批2 先例） | 2026-09-30 |
| 批3 是否需要新的门禁人裁项？ | 不需要：L4_DB_INJECT_REPOS 批2 已入表 lab-management-system-fastapi，scratch 库配方复用 | claude | 2026-09-30 |

## 2. 验收标准

| 编号 | 场景（给定） | 操作（当） | 预期（则） |
|---|---|---|---|
| AC-1 | 有效 Bearer + tenant 内既有码表行 | GET 四面 list（带/不带 inspectionObjectCode、keyword） | 200 Page 包裹：items 全量、page/pageSize/total 语义符合镜像；专项等值过滤、keyword 大小写不敏感命中 code/name；sort_order,code 排序 |
| AC-2 | 有效载荷 | POST 创建四实体（带/不带 sortOrder） | 200 返回建后实体（tenantId=当前租户、sortOrder 缺省 0）；缺 code/name → 400 |
| AC-3 | 既有 code | PUT 部分字段 | 200 部分更新生效（None 字段不动）；不存在 code → 404 |
| AC-4 | 既有/不存在 code | DELETE | 既有 → 204；不存在 → 404 |
| AC-5 | 同 (tenant, code) 二次 create（不同载荷） | POST | 200 merge 覆盖（全字段含 createdAt 刷新） |
| AC-6 | tenant 隔离 | TENANT-002 token 操作 TENANT-001 的行 | list 不可见；update/delete 404 |
| AC-7 | 全部实现完成 | suite 门禁 L1-L5 | 全绿（red-first：测试先红后绿，trace 挂 4 个 I ID；L4 打 scratch 库） |

## 3. 任务拆解

| 任务 ID | 任务描述 | 类型 | 负责人 | 预估 | 状态 |
|---|---|---|---|---|---|
| T-0 | 需求文档门：本文件 + 功能树 M04 4F 翻开发中 + 4 个 I 子项登记 + README 台账行 | 文档 | claude | 小 | 已完成（2026-09-30） |
| T-1 | red-first：tests/test_inspection_catalog.py 全断言（挂 M04.F06-F09 4 个 I ID，零种子依赖全走 API create） | 测试 | claude | 中 | 已完成（2026-09-30，5 断言 red→green） |
| T-2 | impl：InspectionCatalogApiImpl 16 端点（4 实体同构 CRUD）+ app.py 204 收口追加 /api/catalog/ DELETE | 开发 | claude | 中 | 已完成（2026-09-30，表驱动 _Family 合并镜像 springboot 单 service 形态） |
| T-3 | 收口：功能树 4F+4I 翻「已上线」；门禁 L1-L5 全绿；trace 收账；双仓收账 commit | 收口 | claude | 小 | 已完成（2026-09-30，门禁 exit=0，trace 68 条含 4 处 M04 映射） |

## 4. 功能影响

| 功能 ID | 功能名称 | 影响类型 | 说明 | 关联任务 |
|---|---|---|---|---|
| M04.F06 | 型号维护 | 变更 | 状态 规划→已上线；新增子项 I01 | T-1～T-3 |
| M04.F07 | 规格维护 | 变更 | 状态 规划→已上线；新增子项 I01 | T-1～T-3 |
| M04.F08 | 等级维护 | 变更 | 状态 规划→已上线；新增子项 I01 | T-1～T-3 |
| M04.F09 | 牌号维护 | 变更 | 状态 规划→已上线；新增子项 I01 | T-1～T-3 |

新增：4（全部为 I 级子项，随 F 行登记，编号为本仓首拆）；变更：4；删除：0。

## 5. 流程影响

无（M04 是基础数据码表维护域，无流程图；flow-function-map.md 不涉及本批）。

## 6. 风险与回滚

| 风险 | 影响面 | 缓解 | 回滚方式 |
|---|---|---|---|
| 语义与批2 字典面漂移（同构 CRUD 两套口径） | 家族一致性 | 复用批2 helper（current_tenant_or_default/require_login/require_non_blank/now_iso/keyword_hit）；实体 create merge 语义对齐批2 字典面（非 junction） | git revert 本批 commit |
| 种子行 PK 占用（conftest grades C25/C30，PK=code 无租户维度） | 测试数据 | 测试用例避开 C25/C30 作 grade code；零种子依赖全走 API create | 无需回滚（测试域隔离） |
| FK RESTRICT 删除 500（双侧一致） | 边缘路径 | 镜像 springboot 无特判；批2 同款裁定 | 无需回滚（一致性即正确） |

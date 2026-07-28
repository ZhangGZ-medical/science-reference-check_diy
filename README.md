# science-reference-check_diy

> 科学引文批量验证技能 — 多源交叉验证、结构化报告输出

---

## ⚡ 给 AI Agent 的一键安装指令

> **复制下面整个代码块，粘贴给你的 WorkBuddy AI Agent，即可完成全自动安装。**

````text
请从 GitHub 安装 science-reference-check_diy 技能，并自动处理所有依赖。

操作步骤：
1. 从 GitHub 克隆技能到本地：
   git clone https://github.com/ZhangGZ-medical/science-reference-check_diy.git /tmp/science-reference-check_diy
   cp -r /tmp/science-reference-check_diy ~/.workbuddy/skills/

2. 安装依赖技能（每次执行一条）：
   @marketplace-skill-installer 安装 pubmed-search
   @marketplace-skill-installer 安装 literature-search
   @marketplace-skill-installer 安装 patents-search
   @marketplace-skill-installer 安装 docx

3. 安装 Python 依赖：
   pip install python-docx requests

4. 配置 Valyu API Key（用于 PubMed 搜索，免费额度 $10）：
   获取 Key → https://platform.valyu.ai
   bash ~/.workbuddy/skills/lc-pubmed-search/scripts/search setup <你的Key>
   bash ~/.workbuddy/skills/lc-literature-search/scripts/search setup <你的Key>

5. 验证安装：
   bash ~/.workbuddy/skills/lc-pubmed-search/scripts/search "test" 1
   python3 -c "import docx; print('OK')"

全部完成后回复"安装完成"，并列出已安装的技能列表。
````

> **GitHub 仓库**：https://github.com/ZhangGZ-medical/science-reference-check_diy

---

## 目录

1. [给 AI Agent 的一键安装指令](#-给-ai-agent-的一键安装指令)
2. [功能概述](#功能概述)
3. [安装与配置](#安装与配置)
4. [使用方法](#使用方法)
5. [输入输出说明](#输入输出说明)
6. [验证能力矩阵](#验证能力矩阵)
7. [适用场景](#适用场景)
8. [架构设计](#架构设计)
9. [扩展指南](#扩展指南)
10. [FAQ](#faq)

---

## 功能概述

`science-reference-check_diy` 是一个面向学术写作场景的参考文献批量验证工具。它通过多源数据库交叉验证，逐条确认参考文献的作者、标题、期刊、年份、卷期页码是否准确，并以结构化报告呈现结果。

### 核心功能

| 功能 | 说明 |
|------|------|
| **多源交叉验证** | PubMed、WebSearch、专利数据库、临床试验注册中心四通道并行 |
| **并行批量处理** | 4-5个独立Agent同时验证不同分组的引文 |
| **三态判定** | ✅ 完全通过 / ⚠️ 存在问题 / ❌ 未找到 |
| **格式检查** | 作者大小写、标题完整性、期刊缩写、卷期页码格式 |
| **可信度评估** | PMID/DOI 确认、同行评审期刊标注、预印本标识 |
| **双格式输出** | DOCX（带专业排版表格）+ MD（源文件） |
| **修正建议** | 对每条问题文献提供具体的修改建议 |

### 为什么需要这个技能

在学术论文投稿前，参考文献的准确性直接影响论文的可信度。手动逐条核对25+条参考文献需要数小时，且容易遗漏拼写错误、标题偏差等问题。本技能将这一流程自动化，将验证时间从数小时压缩到数分钟，同时保证覆盖面和准确性。

---

## 安装与配置

### 环境要求

| 组件 | 最低版本 | 用途 |
|------|---------|------|
| WorkBuddy | 任意版本 | 技能运行平台 |
| Node.js | 18+ | PubMed/文献/专利搜索脚本运行 |
| Python | 3.9+ | DOCX 报告生成（python-docx） |
| Bash (Git Bash) | — | 搜索脚本执行环境（Windows 自带） |
| 网络 | 可访问 api.valyu.ai | PubMed / 文献 API 调用 |

### 一键安装

> 以下命令集将完成技能本体安装 + 全部依赖技能安装 + API Key 配置。
> 在 WorkBuddy 中向 AI 助手发送以下任意一条指令即可自动执行：

**方式一：从 GitHub 一键安装（推荐，适用于裸机 Agent）**

> 这是给尚未安装任何技能的 AI Agent 的完整安装指令

```
# 步骤 1：克隆技能本体
git clone https://github.com/ZhangGZ-medical/science-reference-check_diy.git /tmp/science-reference-check_diy
cp -r /tmp/science-reference-check_diy ~/.workbuddy/skills/

# 步骤 2：安装依赖技能（在 WorkBuddy 对话中逐条执行）
@marketplace-skill-installer 安装 pubmed-search
@marketplace-skill-installer 安装 literature-search
@marketplace-skill-installer 安装 patents-search
@marketplace-skill-installer 安装 docx

# 步骤 3：安装 Python 依赖
pip install python-docx requests

# 步骤 4：配置 Valyu API Key
# 获取免费 Key（$10 额度）：https://platform.valyu.ai
bash ~/.workbuddy/skills/lc-pubmed-search/scripts/search setup <YOUR_VALYU_API_KEY>
bash ~/.workbuddy/skills/lc-literature-search/scripts/search setup <YOUR_VALYU_API_KEY>
```

**方式二：通过 marketplace-skill-installer（已安装本技能后更新依赖）**

```
@marketplace-skill-installer 安装 science-reference-check_diy 及其全部依赖
```

**方式二：手动逐条安装**

```
# 如果本技能尚未安装，复制技能目录到 ~/.workbuddy/skills/
# （通常由 marketplace-skill-installer 自动完成，以下为手动备选方案）

# 步骤 1：安装本技能
cp -r /path/to/science-reference-check_diy ~/.workbuddy/skills/

# 步骤 2：安装依赖技能
# --- pubmed-search ---
# 搜索并安装（WorkBuddy 中执行）：
@marketplace-skill-installer 安装 pubmed-search

# --- literature-search ---
@marketplace-skill-installer 安装 literature-search

# --- patents-search ---
@marketplace-skill-installer 安装 patents-search

# --- docx ---
@marketplace-skill-installer 安装 docx

# 步骤 3：配置 Valyu API Key
# 获取免费 Key（$10 额度）：https://platform.valyu.ai
# 然后在 WorkBuddy 中执行：
bash ~/.workbuddy/skills/lc-pubmed-search/scripts/search setup YOUR_VALYU_API_KEY
bash ~/.workbuddy/skills/lc-literature-search/scripts/search setup YOUR_VALYU_API_KEY
```

### 依赖技能明细

| 技能名 | 安装路径 | 用途 | 强制 |
|--------|---------|------|------|
| `pubmed-search` | `~/.workbuddy/skills/lc-pubmed-search/` | PubMed 文献检索验证 | ✅ 是 |
| `literature-search` | `~/.workbuddy/skills/lc-literature-search/` | 跨库文献检索（arXiv/bioRxiv/medRxiv） | ✅ 是 |
| `patents-search` | `~/.workbuddy/skills/lc-patents-search/` | 专利数据库检索 | ⚠️ 按需（含专利引文时） |
| `docx` | `~/.workbuddy/plugins/.../docx/` | DOCX 格式报告输出（python-docx） | ✅ 是 |

### 配置验证

安装完成后，运行以下命令验证环境是否就绪：

```bash
# 1. 检查技能目录完整性
echo "=== 技能文件检查 ==="
for f in \
  ~/.workbuddy/skills/science-reference-check_diy/SKILL.md \
  ~/.workbuddy/skills/science-reference-check_diy/README.md \
  ~/.workbuddy/skills/lc-pubmed-search/scripts/search \
  ~/.workbuddy/skills/lc-literature-search/scripts/search \
  ~/.workbuddy/skills/lc-patents-search/SKILL.md; do
  [ -f "$f" ] && echo "  ✅ $(basename $(dirname $f))/$(basename $f)" || echo "  ❌ 缺失: $f"
done

# 2. 验证 PubMed API 连通性
bash ~/.workbuddy/skills/lc-pubmed-search/scripts/search "test query" 1 && \
  echo "  ✅ Valyu API 连通" || \
  echo "  ❌ API 不通，请检查 Key 配置"

# 3. 验证 Python docx 模块
python3 -c "import docx; print('  ✅ python-docx 可用')" 2>/dev/null || \
  echo "  ❌ python-docx 未安装，请执行: pip install python-docx"

echo "=== 验证完成 ==="
```

期望输出：
```
=== 技能文件检查 ===
  ✅ science-reference-check_diy/SKILL.md
  ✅ science-reference-check_diy/README.md
  ✅ lc-pubmed-search/search
  ✅ lc-literature-search/search
  ✅ lc-patents-search/SKILL.md
  ✅ Valyu API 连通
  ✅ python-docx 可用
=== 验证完成 ===
```

### API Key 管理

| Key | 获取地址 | 免费额度 | 配置命令 |
|-----|---------|---------|---------|
| Valyu API Key | https://platform.valyu.ai | $10（约500-1000次搜索） | `bash ~/.workbuddy/skills/lc-pubmed-search/scripts/search setup <KEY>` |

> **注意**：pubmed-search 和 literature-search 共享同一个 Valyu API Key，只需执行一次 setup。Key 保存在 `~/.valyu/config.json`。

### 升级方法

```bash
# 拉取最新版本（如果通过 git 管理）
cd ~/.workbuddy/skills/science-reference-check_diy && git pull

# 或重新复制最新文件
cp -r /path/to/latest/science-reference-check_diy/* ~/.workbuddy/skills/science-reference-check_diy/
```

### 卸载

```bash
rm -rf ~/.workbuddy/skills/science-reference-check_diy
# 依赖技能可独立保留或单独卸载
```

---

## 使用方法

### 调用技能

在 WorkBuddy 对话中直接使用：

```
# 直接调用（最短路径）
@science-reference-check_diy 验证以下参考文献：
[1] Greenberg SM, ...

# 或通过 fable5 工作流路由
@fable5-workflow_diy 验证参考文献
```

接受以下引文格式（自动识别）：

**格式 1：标准 GB/T 7714 / NSFC 引文**
```
[1] Greenberg SM, Ziai WC, Cordonnier C, et al. 2022 guideline for the management of
patients with spontaneous intracerebral hemorrhage. Stroke, 2022, 53(7): e282-e361.
```

**格式 2：Vancouver 格式**
```
[1] Greenberg SM, Ziai WC, Cordonnier C, et al. 2022 guideline for the management of
patients with spontaneous intracerebral hemorrhage: a guideline from the American Heart
Association/American Stroke Association. Stroke. 2022;53(7):e282-e361.
```

**格式 3：混合类型列表**
```
[1] 期刊论文 - 标准格式
[2] 中国专利 - CN121472147A
[3] 临床试验 - MR-42-25-002783
```

### 交互模式

```
用户：@science-reference-check_diy 验证以下25条参考文献 [粘贴引文列表]

技能响应：
  Phase 0: 分类 → A线（深度调研）
  Phase 1: 澄清 → 边界清晰，跳过
  Phase 2: 技能分析 → 4项依赖，全部就绪
  Phase 3: 生成执行提示词
  Phase 4: 等待用户确认
  
用户：确认执行

技能响应：
  Phase 5: 启动4个并行Agent → 各组验证中...
  Phase 6: 编译报告 → MD + DOCX 交付
```

### 批量大小建议

| 引文数量 | Agent 数量 | 建议分组 |
|---------|-----------|---------|
| 1-10条 | 2个 | 各5条 |
| 11-25条 | 4个 | 各5-7条 |
| 26-50条 | 5个 | 各8-10条 |
| 50条以上 | 分批处理 | 每批25条 |

---

## 输入输出说明

### 输入规范

| 字段 | 要求 | 示例 |
|------|------|------|
| 编号 | `[N]` 格式 | `[1]`, `[2]` |
| 作者 | 姓氏在前，名缩写在后 | `Zhang G, Li Y` |
| 标题 | 完整标题，不要缩写 | `Stable intracerebral transplantation...` |
| 期刊 | 全称（非缩写） | `Nature Communications` |
| 年份 | 四位数 | `2025` |
| 卷(期) | 卷(期)格式 | `53(7)`, `16` |
| 页码 | 起止页码 | `e282-e361`, `999-1007` |

### 输出报告结构

```
参考文献验证报告
├── 元数据（任务、方法、日期、状态）
├── 执行摘要（总览表格）
├── 逐条验证结果
│   ├── [1] ✅ 引文标题
│   │   └── 验证属性表（作者/标题/期刊/年份/卷期页码/来源）
│   ├── [2] ✅ ...
│   ├── ...
│   ├── [9] ⚠️ 引文标题 — 问题摘要
│   └── ...
├── 需修正文献详情
│   ├── 问题说明
│   ├── 引用 vs 正确对比
│   └── 修正建议
├── 统计总览（通过率表格）
├── 验证来源分布
└── 结论
```

### 输出文件

| 文件 | 格式 | 路径 |
|------|------|------|
| 验证报告 | DOCX | `results/参考文献验证报告.docx` |
| 验证报告 | MD | `results/参考文献验证报告.md` |

---

## 验证能力矩阵

### 按文献类型

| 文献类型 | 验证源 | 验证深度 | 可信度 |
|---------|--------|---------|--------|
| PubMed 收录期刊 | PubMed API | 作者/标题/期刊/年/卷期/页码 + PMID/DOI | ⭐⭐⭐⭐⭐ |
| 非 PubMed 期刊 | WebSearch + 官网 | 标题/期刊/年 + DOI | ⭐⭐⭐⭐ |
| 预印本 | bioRxiv/medRxiv/arXiv | 标题/作者/日期 | ⭐⭐⭐ |
| 中国专利 | 万方/知网/Google Patents | 专利号/发明人/申请日/公开日 | ⭐⭐⭐⭐ |
| 国际专利 | Google Patents / WIPO | 专利号/发明人/日期 | ⭐⭐⭐⭐ |
| 临床试验备案 | ClinicalTrials.gov / 中国注册中心 | 备案号/负责人/机构 | ⭐⭐⭐⭐ |
| 网页/报告 | WebSearch | 标题/URL/日期 | ⭐⭐ |

### 常见问题检测

| 问题类型 | 检测方式 | 示例 |
|---------|---------|------|
| 作者拼写错误 | 大小写比对 | `Mcourt R` → `McCourt R` |
| 标题偏差 | 相似度比对 | 描述性概括 ≠ 官方标题 |
| 期刊名错误 | 全称/缩写标准化 | `Lancet Neurol` vs `Lancet Neurology` |
| 卷期页码错误 | 精确匹配 | `22(2):159` vs `22(2):159-171` |
| PMID 错误 | 交叉校验 | 给出的 PMID 返回不相关文章 |
| DOI 缺失 | 补全检查 | 提供可用的 DOI |

---

## 适用场景

### 场景 1：学术论文投稿前检查

> 最常用的场景。在论文最终定稿前，对所有参考文献做一次全面验证。

**适用**：SCI 期刊、中文核心期刊投稿
**产出**：可直接附在审稿回复中的验证报告

### 场景 2：基金申请书审核

> 国自然/省基金标书中的参考文献验证。

**适用**：NSFC、省基金申请书
**产出**：含修正建议的逐条报告

### 场景 3：学位论文盲审准备

> 硕博论文盲审前，确保引用无瑕疵。

**适用**：硕士/博士论文
**产出**：双格式交付（DOCX 可直接插入论文附录）

### 场景 4：系统综述/Meta 分析

> PRISMA 流程中的引用验证环节。

**适用**：Cochrane 系统综述、Meta 分析
**产出**：按纳入/排除标准分组的验证报告

### 场景 5：同行评审辅助

> 作为审稿人，快速核查作者引用的准确性。

**适用**：期刊审稿
**产出**：可直接粘贴到审稿意见中的问题列表

---

## 架构设计

### 目录结构

```
science-reference-check_diy/
├── SKILL.md                          # 技能定义（WorkBuddy 加载此文件）
├── README.md                         # 本文档（面向用户）
├── scripts/
│   └── verify_refs.py                # 单条引文的格式解析与预校验（可选）
└── references/
    ├── agent_prompt_template.md      # Agent 提示词模板
    └── output_template.md            # 输出报告模板
```

### 执行架构

```
用户输入（引文列表）
    │
    ▼
┌──────────────┐
│  输入解析     │ → 按编号、类型分组
└──────────────┘
    │
    ├──────────┬──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│Agent1│  │Agent2│  │Agent3│  │Agent4│  │Agent5│
│Refs  │  │Refs  │  │Refs  │  │Refs  │  │Refs  │
│1-6   │  │7-12  │  │13-18 │  │19-25 │  │...   │
│PubMed│  │PubMed│  │PubMed│  │PubMed│  │      │
│+Web  │  │+Web  │  │+Patent│ │+Web  │  │      │
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
    │         │         │         │         │
    └─────────┴────┬────┴─────────┴─────────┘
                   ▼
          ┌──────────────┐
          │  结果汇总     │ ← 交叉验证不确定项
          └──────────────┘
                   │
                   ▼
          ┌──────────────┐
          │  报告生成     │ → MD + DOCX
          └──────────────┘
```

### 数据流

```
引文输入 → 解析器（提取字段） → 分类器（按类型） → 分配器（分给Agent）
    → 验证器（Agent 查询） → 比对器（匹配判断） → 补验器（不确定项）
    → 编译器（统一格式） → 输出器（MD+DOCX）
```

---

## 扩展指南

### 添加新的验证源

1. 在 `SKILL.md` 的"验证能力矩阵"中添加新行
2. 在 Phase 2（分类）中添加新类型识别规则
3. 在 Agent 提示词中添加对应的验证逻辑

示例：添加 Google Scholar 验证通道
```markdown
## 验证源扩展：Google Scholar
- 搜索格式：`"完整标题" author:"姓氏 名"`
- 比对方：标题、作者、年份、引用次数
- 标记：`[GS]` 前缀
```

### 添加新的引文格式

1. 在 `scripts/verify_refs.py` 的 `parse_citation()` 函数中添加新格式的正则表达式
2. 在 SKILL.md 输入格式部分添加示例

### 自定义验证规则

编辑 `SKILL.md` 中的"判定标准"表格：
```markdown
| ✅ 完全通过 | 自定义条件 |
| ⚠️ 存在问题 | 自定义条件 |
```

### 与其他工作流集成

本技能设计为 fable5-workflow_diy 的插件，也可独立使用：

```markdown
# 在自定义工作流中调用
@science-reference-check_diy [引文列表]
```

---

## FAQ

### Q: 需要什么 API Key？
**A:** 需要 Valyu API Key（用于 PubMed 搜索）。该 Key 已预配置在全局记忆中，首次使用无需额外设置。

### Q: 验证25条引文需要多久？
**A:** 通常 2-4 分钟（4个并行Agent同时工作）。主要耗时在 PubMed 搜索 API 的响应时间。

### Q: 如何处理 PubMed 未收录的中文期刊？
**A:** 自动降级到 WebSearch（知网/万方/百度学术），并在报告中标注验证来源和可信度。

### Q: 可以只验证部分字段吗？
**A:** 可以。在对话中说明只关注特定字段（如"只验证期刊和年份"），技能会调整验证策略。

### Q: 如何处理 "et al." 的作者列表？
**A:** 验证第一作者和最后作者（通讯作者），中间作者用 "et al." 标注。如果原文作者少于规定数量（通常3人），会在报告中提示。

### Q: 预印本可以验证吗？
**A:** 可以。支持 arXiv、bioRxiv、medRxiv。预印本标注 ⭐⭐⭐ 可信度（未经同行评审）。

### Q: DOCX 可以自定义格式吗？
**A:** 可以。修改 `references/output_template.md` 中的表格样式定义，或自定义 `scripts/verify_refs.py` 中的 python-docx 样式。

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-07-28 | 初始发布。4-Agent 并行验证、PubMed+WebSearch+专利+临床试验多源交叉、MD+DOCX 双输出 |

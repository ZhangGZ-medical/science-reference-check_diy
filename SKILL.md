---
name: science-reference-check_diy
description: 科学引文批量验证技能。支持多源交叉验证（PubMed/WebSearch/专利数据库/临床试验注册中心），逐条核对参考文献的作者、标题、期刊、年份、卷期页码准确性，输出结构化验证报告。触发词：验证参考文献、检查引文、引用格式验证、参考文献核对、reference check。
agent_created: true
version: 1.0.0
created: 2026-07-28
install:
  dependencies:
    - name: pubmed-search
      path: ~/.workbuddy/skills/pubmed-search/
      download: "curl -L -o /tmp/pubmed.zip 'https://lightmake.site/api/v1/download?slug=pubmed-search' && mkdir -p ~/.workbuddy/skills/pubmed-search && unzip -o /tmp/pubmed.zip -d ~/.workbuddy/skills/pubmed-search"
      required: true
    - name: literature-search
      path: ~/.workbuddy/skills/literature-search/
      download: "curl -L -o /tmp/lit.zip 'https://lightmake.site/api/v1/download?slug=literature-search' && mkdir -p ~/.workbuddy/skills/literature-search && unzip -o /tmp/lit.zip -d ~/.workbuddy/skills/literature-search"
      required: true
    - name: patents-search
      path: ~/.workbuddy/skills/patents-search/
      download: null
      required: false
      fallback: "WebSearch 自动替代专利验证"
    - name: docx
      path: builtin
      download: null
      required: true
  api_keys:
    - name: Valyu API Key
      url: https://platform.valyu.ai
      setup_cmd: "bash ~/.workbuddy/skills/pubmed-search/scripts/search setup <KEY>"
  verify_cmds:
    - "ls ~/.workbuddy/skills/pubmed-search/scripts/search || ls ~/.workbuddy/skills/lc-pubmed-search/scripts/search"
    - "ls ~/.workbuddy/skills/literature-search/scripts/search || ls ~/.workbuddy/skills/lc-literature-search/scripts/search"
    - "python3 -c 'import docx; print(\"OK\")'"
    - "bash ~/.workbuddy/skills/pubmed-search/scripts/search \"test\" 1 || bash ~/.workbuddy/skills/lc-pubmed-search/scripts/search \"test\" 1"
---

# science-reference-check_diy v1.0 — 科学引文批量验证

## 概述

对学术论文参考文献列表进行逐条多源交叉验证。检查每条的作者拼写、标题准确性、期刊名称、年份、卷期页码是否与数据库一致，输出逐条状态（✅/⚠️/❌）和修正建议。

## 核心能力

| 能力 | 说明 |
|------|------|
| 多源验证 | PubMed（Valyu API）、WebSearch、专利数据库、临床试验注册中心 |
| 并行处理 | 4-5个Agent并行验证，每组5-7条引文 |
| 格式检查 | 作者拼写（大小写）、标题完整性、期刊标准缩写、卷期页码格式 |
| 可信度评估 | PMID/DOI存在性、同行评审期刊、预印本标注 |
| 结构化输出 | MD + DOCX 双格式，逐条标注 ✅/⚠️/❌ |

## 前置依赖

### 技能自检（首次调用时执行）

技能被调用后，第一件事是检查依赖是否就绪：

```bash
# 快速自检脚本（兼容 lc- 和标准命名）
echo "=== science-reference-check_diy 依赖检查 ==="
DEPS_OK=true

# 检查 PubMed 搜索脚本（优先标准路径，兼容 lc- 前缀）
if [ -f ~/.workbuddy/skills/pubmed-search/scripts/search ]; then
  PUBMED_PATH=~/.workbuddy/skills/pubmed-search
elif [ -f ~/.workbuddy/skills/lc-pubmed-search/scripts/search ]; then
  PUBMED_PATH=~/.workbuddy/skills/lc-pubmed-search
else
  echo "❌ pubmed-search 缺失"
  echo "   安装：curl -L -o /tmp/pubmed.zip 'https://lightmake.site/api/v1/download?slug=pubmed-search'"
  echo "        mkdir -p ~/.workbuddy/skills/pubmed-search && unzip -o /tmp/pubmed.zip -d ~/.workbuddy/skills/pubmed-search"
  DEPS_OK=false
fi
[ -n "$PUBMED_PATH" ] && echo "✅ pubmed-search 已安装 ($PUBMED_PATH)"

# 检查文献搜索脚本
if [ -f ~/.workbuddy/skills/literature-search/scripts/search ]; then
  LIT_PATH=~/.workbuddy/skills/literature-search
elif [ -f ~/.workbuddy/skills/lc-literature-search/scripts/search ]; then
  LIT_PATH=~/.workbuddy/skills/lc-literature-search
else
  echo "❌ literature-search 缺失"
  echo "   安装：curl -L -o /tmp/lit.zip 'https://lightmake.site/api/v1/download?slug=literature-search'"
  echo "        mkdir -p ~/.workbuddy/skills/literature-search && unzip -o /tmp/lit.zip -d ~/.workbuddy/skills/literature-search"
  DEPS_OK=false
fi
[ -n "$LIT_PATH" ] && echo "✅ literature-search 已安装 ($LIT_PATH)"

# 检查 python-docx
if python3 -c "import docx" 2>/dev/null; then
  echo "✅ python-docx 可用"
else
  echo "❌ python-docx 缺失 → 执行: pip install python-docx"
  DEPS_OK=false
fi

# 检查 Valyu API Key
if bash "$PUBMED_PATH/scripts/search" "test" 1 >/dev/null 2>&1; then
  echo "✅ Valyu API 连通"
else
  echo "⚠️ Valyu API 未配置 → 获取 Key: https://platform.valyu.ai"
  echo "   配置: bash $PUBMED_PATH/scripts/search setup <KEY>"
fi

if [ "$DEPS_OK" = false ]; then
  echo "⚠️ 部分依赖缺失，将自动安装..."
  # 自动触发 marketplace-skill-installer
fi
echo "=== 检查完成 ==="
```

自检失败时的自动修复流程：
1. 缺失技能 → 调用 `@marketplace-skill-installer` 安装
2. 缺失 python-docx → `pip install python-docx`
3. API Key 未配置 → 提示用户获取并运行 setup 命令
4. 全部就绪 → 进入执行流程

### 依赖技能列表

| 技能 | 用途 | 安装路径 | 公开下载 |
|------|------|---------|---------|
| `pubmed-search` | PubMed 文献检索 | `~/.workbuddy/skills/pubmed-search/` | [SkillHub](https://lightmake.site/api/v1/download?slug=pubmed-search) |
| `literature-search` | 跨库文献检索（PubMed+arXiv+bioRxiv+medRxiv） | `~/.workbuddy/skills/literature-search/` | [SkillHub](https://lightmake.site/api/v1/download?slug=literature-search) |
| `patents-search` | 专利数据库检索（可选，缺失时自动用 WebSearch 替代） | `~/.workbuddy/skills/patents-search/` | ⚠️ 不可公开下载 |
| `docx` | DOCX 格式输出 | 内置 marketplace | WorkBuddy 自带 |

**API Key**：Valyu API Key（已记录在全局 `~/.workbuddy/MEMORY.md`）。

## 执行流程

### Phase 1：输入解析

从用户输入中提取参考文献列表。支持格式：
- 标准 GB/T 7714 / Vancouver / NSFC 引文格式
- 自由文本列表（按编号分隔）

解析每条引文的：编号、作者、标题、期刊、年份、卷(期)、页码。

### Phase 2：分类与分组

按文献类型分组：

| 类型 | 特征 | 验证源 |
|------|------|--------|
| 期刊论文 | 含期刊名、卷期页码 | PubMed 优先 |
| 预印本 | arXiv/bioRxiv/medRxiv 标记 | 对应预印本服务器 |
| 专利 | 专利号（CN/US/WO...） | 专利数据库 / WebSearch |
| 临床试验 | 备案号（NCT/MR-...） | ClinicalTrials.gov / 中国临床试验注册中心 |
| 其他 | 网页/报告/会议 | WebSearch |

每组 5-7 条，分配给并行 Agent。

### Phase 3：并行验证

对每组启动一个 Agent（`subagent_type: general-purpose`，`run_in_background: true`）。

每个 Agent 的任务：
1. 对期刊论文：运行 `bash ~/.workbuddy/skills/pubmed-search/scripts/search "标题关键词" 5`（如含 lc- 前缀则使用 lc-pubmed-search 路径）
2. 对专利/临床试验/预印本：使用 `WebSearch`
3. 比对返回结果与引用内容
4. 输出每条的状态和差异说明

**Agent 提示词模板**（见 `references/agent_prompt_template.md`）。

### Phase 4：汇总与交叉验证

收集所有 Agent 结果后：
1. 对不确定条目（卷期页码未直接显示）进行 WebSearch 补充验证
2. 对 PMID/DOI 进行二次确认
3. 编译统一状态标记

### Phase 5：输出报告

输出结构：
```
## 执行摘要（总览表格）
## 逐条验证结果（每条一级标题 + 属性表格）
## 需修正文献详情（问题说明 + 修正建议）
## 统计总览
## 验证来源分布
## 结论
```

MD + DOCX 双格式交付，DOCX 在前。

## 判定标准

| 状态 | 条件 |
|------|------|
| ✅ 完全通过 | 作者、标题、期刊、年份、卷期页码全部匹配 |
| ⚠️ 存在问题 | 部分字段不匹配但可修正（拼写、格式差异） |
| ❌ 未找到 | 在所有验证源中均无法定位 |

**常见问题分类**：

| 严重程度 | 问题类型 | 示例 |
|---------|---------|------|
| 🔴 严重 | 标题完全不对 | 引用的是描述性概括而非官方标题 |
| 🔴 严重 | 期刊/年份错误 | 引用到错误的期刊 |
| 🟡 中等 | 作者拼写错误 | "Mcourt R" → "McCourt R" |
| 🟡 中等 | 卷/期/页码偏差 | 数字或页码范围不符 |
| 🟢 轻微 | 字母大小写 | 标题中某词首字母大小写 |
| 🟢 轻微 | "et al." 使用 | 作者数超过3人时用 et al. |

## 最佳实践

### 搜索词构造
- 取标题前 4-6 个关键词（去掉 "a/the/and" 等停用词）
- 加上第一作者姓氏：`"Author Keyword1 Keyword2 Journal关键词"`
- 对中文文献：加 `PMID` 或 `DOI` 直接定位

### 卷期页码验证
- PubMed 摘要页可能不直接显示 → 使用 WebSearch 搜索 DOI 补验证
- 优先搜索格式：`"完整标题" DOI`

### 中国专利验证
- 搜索 `"CN专利号 发明人"` 在万方/知网/Google Patents
- 关键检查点：专利号、申请日、公开日、发明人、专利权人

### 临床试验备案验证
- 中国项目：搜索 `"备案号 负责人 医院"` + 中国临床试验注册中心
- 国际项目：ClinicalTrials.gov 直查 NCT 编号

## 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 验证报告 DOCX | `results/参考文献验证报告.docx` | 主要交付物 |
| 验证报告 MD | `results/参考文献验证报告.md` | 源文件 |

## 与 fable5-workflow 集成

本技能是 fable5-workflow_diy 的 A线插件。当 fable5 检测到"验证参考文献"类任务时，自动路由到本技能。

在 fable5 中的调用链：
```
Phase 2（技能分析）→ 检测依赖 → 安装缺失 → 就绪报告
Phase 3（提示词生成）→ 引入本技能验证策略
Phase 5（A线执行）→ 技能调用链中插入本技能
Phase 6（审查交付）→ 标准 MD+DOCX
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-07-28 | 初始版本。4-Agent 并行验证，PubMed+WebSearch+专利+临床试验多源交叉验证，MD+DOCX 双输出。基于25条脑出血文献验证实战经验固化。 |

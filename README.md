# 小红书内容生成器（V2）

## 概览

V2 从“固定分类随机生成”升级为“动态主题治理 + 索引驱动生成”。

核心变化：
- 主题不锁死：可按用户需求创建新主题
- 先索引后生成：必须先确认主题索引 JSON
- 按状态推进：pending -> generated -> verified -> published -> archived
- 科学门禁：事实类内容未通过证据门禁不得发布
- 模板解耦：模板独立存储于 templates 目录

## 目录结构

```text
xiaohongshu-generator/
├── SKILL.md
├── SKILL.zh-CN.md
├── data/
│   ├── topics_index.json
│   ├── generation_templates.json
│   └── governance_defaults.json
├── scripts/
│   └── generator.py
├── templates/
│   ├── _meta/template_registry.json
│   ├── life_tips/short_mobile_v2.md
│   ├── symbol_packs/
│   └── validation_rules/
└── examples/
```

运行期治理目录（位于 `<content_root>`）：

```text
<content_root>/
└── _governance/
    ├── theme_registry.json
    ├── topic_index.<theme>.json
    ├── content_index.jsonl
    └── verification/
        ├── verified_claims.json
        ├── conditional_claims.json
        └── banned_claims.json
```

输出目录规则：
- 默认（当前技能根目录）：`C:\Users\song\IdeaProjects\qingshuihe\codex_skills\xiaohongshu-generator`
- 可覆盖：`--content-root "<自定义目录>"` 或环境变量 `XHS_CONTENT_ROOT`
- 优先级：参数 > 环境变量 > 默认目录

## 常用命令

### 1. 创建主题索引

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py create-topic-index \
  --theme "租房生活指南" \
  --subthemes "厨房:收纳,去油污;卧室:防潮,除味"
```

自定义输出目录示例：

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py \
  --content-root "D:\\xhs_content" \
  create-topic-index \
  --theme "租房生活指南" \
  --subthemes "厨房:收纳,去油污;卧室:防潮,除味"
```

### 2. 规划待生成话题（生成 N 条前）

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py plan-topics \
  --index "codex_skills/xiaohongshu-generator/_governance/topic_index.theme_xxx.json" \
  --count 3
```

### 3. 更新话题状态

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py mark-status \
  --index "codex_skills/xiaohongshu-generator/_governance/topic_index.theme_xxx.json" \
  --status generated \
  --topic-ids topic_a topic_b
```

### 4. 写入内容台账

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py add-record \
  --theme-id theme_xxx \
  --subtheme-id subtheme_xxx \
  --topic-id topic_xxx \
  --title "示例标题" \
  --file-path "生活小妙招/厨房/2026-03-05-001-示例.md"
```

### 5. 查看生活小妙招模板

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py show-life-tips-template --pick-style
```

## 输出目录规范

### 目录结构

```text
<content_root>/
├── encyclopedia/                    # 百科知识
│   ├── 宇宙探索/
│   │   ├── 001-黑洞的形成与特性.md
│   │   ├── 002-系外行星探索.md
│   │   └── 003-恒星的生命周期.md
│   ├── 地球科学/
│   │   ├── 001-板块构造理论.md
│   │   └── 002-火山类型与喷发机制.md
│   └── 海洋奥秘/
│
├── life_tips/                       # 生活小妙招
│   ├── 厨房/
│   │   ├── 001-冰箱去异味.md
│   │   └── 002-调料瓶清洁.md
│   ├── 浴室/
│   │   └── 001-浴室除霉.md
│   └── 衣物护理/
│
└── _governance/                     # 治理文件
    ├── encyclopedia_topics_index.json
    ├── life_tips_topics_index.json
    └── content_index.jsonl
```

### 文件命名规范

**格式**：`{序号}-{标题}.md`

**规则**：
- 序号：3位数字，每个次级主题从001开始递增
- 标题：中文，与内容标题一致
- 连接符：使用 `-`（短横线）

**示例**：
- `001-黑洞的形成与特性.md`
- `002-系外行星探索.md`
- `023-冰箱去异味.md`

### content_index.jsonl 字段示例

```json
{
  "content_id": "encyclopedia_001",
  "topic_id": "topic_enc_001",
  "theme": "百科知识",
  "subtheme": "宇宙探索",
  "title": "黑洞的形成与特性",
  "file_path": "encyclopedia/宇宙探索/001-黑洞的形成与特性.md",
  "status": "generated",
  "generated_at": "2026-03-06T00:00:00",
  "word_count": 593,
  "evidence_level": "verified",
  "sources": ["来源1", "来源2", "来源3"]
}
```

**注意**：不再使用独立的.metadata.json文件，所有元数据统一存储在content_index.jsonl中。

## 生活小妙招模板约束（已落地）

- 正文 180-320 字，最大 380 字
- 仅 3-4 个解决方案
- 适配手机端 1-2 次划屏
- 使用多风格符号包轮换，降低 AI 同质化

## 百科知识模板约束（V2.0）

- 正文 400-700 字，深度讲解
- 2-3 个核心知识段落，每段 80-150 字
- 必须包含数据来源说明（3个以上来源，至少1个权威来源）
- 证据级别必须为 verified

## 验证要求

提交前至少执行：

```bash
python -m py_compile codex_skills/xiaohongshu-generator/scripts/generator.py
```

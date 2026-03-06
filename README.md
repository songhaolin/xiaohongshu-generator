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

## 生活小妙招模板约束（已落地）

- 正文 180-320 字，最大 380 字
- 仅 3-4 个解决方案
- 适配手机端 1-2 次划屏
- 使用多风格符号包轮换，降低 AI 同质化

## 验证要求

提交前至少执行：

```bash
python -m py_compile codex_skills/xiaohongshu-generator/scripts/generator.py
```

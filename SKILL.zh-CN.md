# 技能说明：xiaohongshu-generator（V2）

> 说明：本技能已升级为“动态主题治理 + 模板化生成”模式，不再局限固定主题。

## 核心定位

本技能的核心不再是“直接随机生成”，而是：

1. 先建索引：一级主题 -> 二级主题 -> 三级话题
2. 用户确认索引
3. 按索引状态批量生成（用户可指定 N 条）
4. 每条生成后必须回写状态与台账

## 内容根目录

- 默认内容目录（当前技能根目录）：`C:\Users\song\IdeaProjects\qingshuihe\codex_skills\xiaohongshu-generator`
- 治理目录：`<content_root>/_governance/`

支持用户指定输出目录：
- 命令参数：`--content-root "<自定义目录>"`
- 环境变量：`XHS_CONTENT_ROOT`

优先级：
1. `--content-root`
2. `XHS_CONTENT_ROOT`
3. 默认目录

当用户明确指定输出目录时，正文与治理文件都必须写入该目录。

## 强制规则（必须执行）

### 1）先索引，后生成
- 用户提出新主题时，必须先输出该主题的索引 JSON。
- 用户确认索引前，禁止输出可发布正文。

### 2）主题动态化
- 主题不锁死在 5/6 类。
- 用户要求的任意主题都可创建为一级主题。

### 3）按状态推进
- 状态流转：`pending -> generated -> verified -> published -> archived`
- 当用户要求“生成 N 条”时，优先从 `pending` 选题。

### 4）必须回写
每生成一条，必须更新：
- 对应 `topic_index.<theme>.json` 的话题状态
- `content_index.jsonl` 内容台账
- metadata 统计与更新时间

### 5）科学验证门禁
事实类主题（妙招/科普/美景/送礼等）必须满足：
- 至少 3 个来源
- 至少 1 个权威来源
- 证据级别为 `verified` 或 `conditional`
- 若为 `insufficient`，禁止输出可发布内容

### 6）去重规则
- 标题精确去重
- 主题冷却期去重
- 语义相似度去重
- 命中重复时自动切换候选话题

## 索引 JSON 标准

```json
{
  "schema_version": "2.0",
  "theme": {
    "id": "theme_xxx",
    "name": "主题名",
    "description": "可选"
  },
  "subthemes": [
    {
      "id": "subtheme_xxx",
      "name": "次级主题",
      "topics": [
        {
          "id": "topic_xxx",
          "name": "三级话题",
          "status": "pending",
          "created_at": "2026-03-05T00:00:00",
          "updated_at": "2026-03-05T00:00:00"
        }
      ]
    }
  ],
  "metadata": {
    "total_topics": 20,
    "status_count": {
      "pending": 20,
      "generated": 0,
      "verified": 0,
      "published": 0,
      "archived": 0
    },
    "created_at": "2026-03-05T00:00:00",
    "last_updated": "2026-03-05T00:00:00"
  }
}
```

## 模板管理（与 SKILL 解耦）

不要把详细模板硬编码在本文件。
模板统一放在：

- 注册表：`templates/_meta/template_registry.json`
- 各主题模板：`templates/<theme>/...`
- 多风格符号包：`templates/symbol_packs/...`
- 规则校验：`templates/validation_rules/...`

## 当前落地模板（生活小妙招）

- 模板：`templates/life_tips/short_mobile.md`
- 符号包：`templates/symbol_packs/life_tips.json`
- 校验规则：`templates/validation_rules/life_tips.json`

约束：
- 正文 180-320 字（上限 380）
- 仅 3-4 个方案
- 手机端 1-2 次划屏可读完
- 符号风格轮换，避免 AI 同质化

## 科学验证知识库

优先使用本地规则文件：
- `<content_root>/_governance/verification/verified_claims.json`
- `<content_root>/_governance/verification/conditional_claims.json`
- `<content_root>/_governance/verification/banned_claims.json`

再结合实时搜索进行交叉验证。

## 本地脚本能力（scripts/generator.py）

支持以下命令：
- `create-topic-index`：创建主题索引
- `plan-topics`：按索引规划待生成话题
- `mark-status`：批量更新状态
- `add-record`：写入内容台账
- `show-life-tips-template`：查看生活小妙招模板配置

所有命令都支持可选输出目录覆盖：

`python scripts/generator.py --content-root "C:\\path\\to\\output" <command> ...`

## 发布前质量检查

- [ ] 选题来自已确认索引
- [ ] 状态流转合法
- [ ] 去重规则通过
- [ ] 科学验证门禁通过（事实类）
- [ ] 模板字段完整
- [ ] 已写入台账与状态回写

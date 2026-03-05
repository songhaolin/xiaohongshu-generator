---
name: xiaohongshu-generator
description: Dynamic Xiaohongshu content system with topic-index governance, scientific validation gates, anti-duplication controls, and template-based generation.
---

# Skill Specification: xiaohongshu-generator (V2)

## Purpose

This skill is no longer a fixed 5/6-category generator.
It is a **dynamic topic governance + generation system**:

1. Build topic index first (Level 1 theme -> Level 2 subtheme -> Level 3 topic list)
2. Ask user to confirm the index
3. Generate N items strictly from index status and order
4. Write back status and ledger after each item

## Runtime Content Root

Default output root (current skill root):

`C:\Users\song\IdeaProjects\qingshuihe\codex_skills\xiaohongshu-generator`

Governance files are stored under:

`<content_root>/_governance/`

Output root can be user-specified:

- CLI parameter: `--content-root "<custom_path>"`
- Environment variable: `XHS_CONTENT_ROOT`

Priority order:

1. `--content-root`
2. `XHS_CONTENT_ROOT`
3. default path above

When user explicitly provides an output directory, the skill must use that directory
for both generated content and governance files.

## Mandatory Workflow (Hard Rules)

### Rule 1: Index-first
- If user asks for a new theme, output a dedicated topic index JSON first.
- Do not generate publishable content until user confirms the index.

### Rule 2: Dynamic themes
- Themes are not locked to preset categories.
- Any user-requested theme can become a new Level 1 theme.

### Rule 3: Status-driven generation
- Generate topics by status priority:
  - `pending` -> `generated` -> `verified` -> `published` -> `archived`
- For "generate N items", always pick from `pending` first.

### Rule 4: Write-back required
After each generated item, update:
- topic status in topic index
- `content_index.jsonl` ledger entry
- updated timestamp and metadata counters

### Rule 5: Scientific validation gate
For factual themes (life tips, encyclopedia, scenery, gift guides, etc.):
- at least 3 sources
- at least 1 authority source
- evidence level must be `verified` or `conditional`
- `insufficient` must be blocked (not publishable)

### Rule 6: Anti-duplication
- title exact-match dedup
- topic cooldown dedup
- semantic similarity dedup
- if duplicate is detected, switch to next candidate topic

## Topic Index Schema (Required)

```json
{
  "schema_version": "2.0",
  "theme": {
    "id": "theme_xxx",
    "name": "主题名",
    "description": "可选描述"
  },
  "subthemes": [
    {
      "id": "subtheme_xxx",
      "name": "次级主题",
      "topics": [
        {
          "id": "topic_xxx",
          "name": "三级主题",
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

## Template System (Decoupled)

Do not hardcode detailed format blocks in this SKILL file.
Use external template files:

- template registry: `templates/_meta/template_registry.json`
- per-theme templates: `templates/<theme>/...`
- symbol packs: `templates/symbol_packs/...`
- validation rules: `templates/validation_rules/...`

## Life Tips Current Production Template

Use:
- `templates/life_tips/short_mobile.md`
- `templates/symbol_packs/life_tips.json`
- `templates/validation_rules/life_tips.json`

Key constraints:
- body 180-320 chars (max 380)
- 3-4 solutions only
- mobile readable in 1-2 scrolls
- style symbols must rotate to reduce AI homogenization

## Scientific Validation Knowledge Sources

Use governance verification files first:
- `<content_root>/_governance/verification/verified_claims.json`
- `<content_root>/_governance/verification/conditional_claims.json`
- `<content_root>/_governance/verification/banned_claims.json`

Then perform real-time web search for current evidence.

## CLI Helper Script

Use `scripts/generator.py` for local governance operations:

- `create-topic-index`
- `plan-topics`
- `mark-status`
- `add-record`
- `show-life-tips-template`

All commands accept optional output-root override:

`python scripts/generator.py --content-root "C:\\path\\to\\output" <command> ...`

## Quality Checklist

Before outputting publishable content:
- [ ] topic selected from confirmed index
- [ ] status transition is valid
- [ ] anti-duplication checks passed
- [ ] scientific gate passed (if factual)
- [ ] template structure is complete
- [ ] ledger write-back completed

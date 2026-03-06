# QuickStart（V2）

## 输出目录（先确认）

- 默认输出目录（当前技能根目录）：`C:\Users\song\IdeaProjects\qingshuihe\codex_skills\xiaohongshu-generator`
- 如需自定义，给所有命令增加：`--content-root "<自定义目录>"`
- 也可设置环境变量：`XHS_CONTENT_ROOT`

## 1) 先建主题索引（必须）

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py create-topic-index \
  --theme "你要做的一级主题" \
  --subthemes "二级A:三级1,三级2;二级B:三级3,三级4"
```

输出后先让用户确认索引，再进入生成。

## 2) 按索引取 N 条待生成话题

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py plan-topics \
  --index "codex_skills/xiaohongshu-generator/_governance/topic_index.theme_xxx.json" \
  --count 5
```

## 3) 生成内容并回写状态

生成完成一条后：

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py mark-status \
  --index "codex_skills/xiaohongshu-generator/_governance/topic_index.theme_xxx.json" \
  --status generated \
  --topic-ids topic_xxx
```

并写入台账：

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py add-record \
  --theme-id theme_xxx \
  --subtheme-id subtheme_xxx \
  --topic-id topic_xxx \
  --title "内容标题" \
  --file-path "encyclopedia/宇宙探索/001-黑洞的形成与特性.md"
```

**注意**：file-path使用二级目录结构，文件命名格式为 `001-标题.md`

## 4) 事实类内容做科学门禁

- 至少 3 个来源
- 至少 1 个权威来源
- 证据级别若为 `insufficient`，禁止发布

## 5) 生活小妙招模板

查看当前模板与符号风格：

```bash
python codex_skills/xiaohongshu-generator/scripts/generator.py show-life-tips-template --pick-style
```

模板约束：180-320 字、3-4 条方案、1-2 屏读完。

## 输出目录规范

### 文件存储结构

```text
<content_root>/
├── encyclopedia/                    # 百科知识
│   ├── 宇宙探索/
│   │   ├── 001-黑洞的形成与特性.md
│   │   └── 002-系外行星探索.md
│   └── 地球科学/
│       └── 001-板块构造理论.md
│
├── life_tips/                       # 生活小妙招
│   ├── 厨房/
│   │   ├── 001-冰箱去异味.md
│   │   └── 002-调料瓶清洁.md
│   └── 浴室/
│       └── 001-浴室除霉.md
```

### 文件命名规则

**格式**：`{序号}-{标题}.md`

- 序号：3位数字（001, 002, ...）
- 每个次级主题独立编号
- 标题：中文，与内容一致

### 元数据管理

- ✅ 使用：`_governance/content_index.jsonl` 统一管理
- ❌ 不再使用：独立的 `.metadata.json` 文件

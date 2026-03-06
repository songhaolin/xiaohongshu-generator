# Claude Code 权限配置

## 技能说明

这是小红书内容生成器技能，用于生成小红书平台的百科知识、生活小妙招等内容。

## 自动放行权限

以下操作不需要用户确认，可以直接执行：

### 文件读取操作
- 读取 `templates/` 目录下的所有模板文件
- 读取 `_governance/` 目录下的治理文件
- 读取输出目录下的已有内容文件

### 文件写入操作
- 创建和修改 `<content_root>/encyclopedia/` 目录下的内容文件
- 创建和修改 `<content_root>/life_tips/` 目录下的内容文件
- 更新 `_governance/content_index.jsonl` 文件
- 更新 `_governance/*_topics_index.json` 文件

### 脚本执行
- 执行 `scripts/generator.py` 及其参数命令
- Python脚本相关的文件操作

### 目录操作
- 创建次级主题目录（如 `encyclopedia/宇宙探索/`）
- 创建必要的治理目录结构

## 安全说明

此技能仅执行内容生成相关的文件操作，不会：
- 修改系统文件
- 删除非输出目录的文件
- 执行网络请求（除必要的数据验证外）
- 修改用户的其他项目文件

## 输出目录

默认输出目录：
```
C:\Users\song\IdeaProjects\qingshuihe\codex_skills\xiaohongshu-generator
```

可通过 `--content-root` 参数或 `XHS_CONTENT_ROOT` 环境变量自定义。

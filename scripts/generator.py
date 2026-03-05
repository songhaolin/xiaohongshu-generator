#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书内容治理与生成辅助脚本。

V2 目标：
1. 主题动态化：不锁死固定主题，先索引后生成。
2. 治理可追溯：状态流转 + 台账回写 + 可恢复。
3. 模板解耦：模板文件独立于 SKILL 文本。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


DEFAULT_STATUS_FLOW = ["pending", "generated", "verified", "published", "archived"]
DEFAULT_EVIDENCE_LEVELS = ["verified", "conditional", "insufficient"]


class GovernanceError(RuntimeError):
    """治理流程异常。"""


class XiaohongshuGenerator:
    """小红书主题治理与内容生成辅助器。"""

    def __init__(self, data_dir: Optional[Path] = None, content_root: Optional[Path] = None):
        self.skill_root = Path(__file__).resolve().parent.parent
        self.data_dir = Path(data_dir) if data_dir else self.skill_root / "data"
        self.templates_dir = self.skill_root / "templates"
        env_content_root = os.getenv("XHS_CONTENT_ROOT", "").strip()
        if content_root:
            resolved_content_root = Path(content_root)
        elif env_content_root:
            resolved_content_root = Path(env_content_root)
        else:
            # 默认输出目录使用当前技能根目录。
            resolved_content_root = self.skill_root
        self.content_root = resolved_content_root.expanduser().resolve()
        self.governance_root = self.content_root / "_governance"
        self.verification_root = self.governance_root / "verification"

        self.topics_index = self._load_json(self.data_dir / "topics_index.json", fallback={"categories": []})
        self.templates = self._load_json(self.data_dir / "generation_templates.json", fallback={})
        self.governance_defaults = self._load_json(
            self.data_dir / "governance_defaults.json",
            fallback={
                "status_flow": DEFAULT_STATUS_FLOW,
                "science_validation": {
                    "required_sources": 3,
                    "required_authority_sources": 1,
                    "evidence_levels": DEFAULT_EVIDENCE_LEVELS,
                },
            },
        )
        self.template_registry = self._load_json(
            self.templates_dir / "_meta" / "template_registry.json",
            fallback={"version": "1.0.0", "templates": []},
        )
        self.ensure_governance_files()

    @staticmethod
    def _load_json(path: Path, fallback: Optional[dict] = None) -> dict:
        """加载 JSON，不存在时返回 fallback。"""
        if not path.exists():
            return copy.deepcopy(fallback) if fallback is not None else {}
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")

    @staticmethod
    def _slugify(text: str, prefix: str) -> str:
        """生成稳定 id；中文无法直接转写时退化为哈希。"""
        ascii_slug = re.sub(r"[^0-9a-zA-Z]+", "_", text).strip("_").lower()
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        if ascii_slug and len(ascii_slug) >= 3 and not ascii_slug[0].isdigit():
            return f"{ascii_slug}_{digest}"
        if ascii_slug:
            return f"{prefix}_{ascii_slug}_{digest}"
        return f"{prefix}_{digest}"

    def ensure_governance_files(self) -> None:
        """初始化治理目录与默认文件。"""
        self.verification_root.mkdir(parents=True, exist_ok=True)

        registry_path = self.governance_root / "theme_registry.json"
        if not registry_path.exists():
            self._write_json(
                registry_path,
                {
                    "schema_version": "2.0",
                    "status_flow": self.governance_defaults.get("status_flow", DEFAULT_STATUS_FLOW),
                    "themes": [],
                    "last_updated": datetime.now().isoformat(timespec="seconds"),
                },
            )

        for filename in ["verified_claims.json", "conditional_claims.json", "banned_claims.json"]:
            filepath = self.verification_root / filename
            if not filepath.exists():
                self._write_json(filepath, {"schema_version": "1.0", "items": []})

        content_index = self.governance_root / "content_index.jsonl"
        if not content_index.exists():
            content_index.parent.mkdir(parents=True, exist_ok=True)
            content_index.write_text("", encoding="utf-8")

    def create_topic_index(self, theme_name: str, subthemes: Dict[str, List[str]], description: str = "") -> dict:
        """按一级/二级/三级结构创建主题索引 JSON。"""
        if not subthemes:
            raise GovernanceError("至少需要一个二级主题及其三级话题。")

        theme_id = self._slugify(theme_name, "theme")
        now = datetime.now().isoformat(timespec="seconds")
        subtheme_nodes = []
        total_topics = 0

        for subtheme_name, topics in subthemes.items():
            if not topics:
                continue
            subtheme_id = self._slugify(subtheme_name, "subtheme")
            topic_nodes = []
            for topic_name in topics:
                topic_id = self._slugify(topic_name, "topic")
                topic_nodes.append(
                    {
                        "id": topic_id,
                        "name": topic_name,
                        "status": "pending",
                        "created_at": now,
                        "updated_at": now,
                    }
                )
            total_topics += len(topic_nodes)
            subtheme_nodes.append(
                {
                    "id": subtheme_id,
                    "name": subtheme_name,
                    "topics": topic_nodes,
                }
            )

        if not subtheme_nodes:
            raise GovernanceError("未生成有效二级主题，请检查输入。")

        return {
            "schema_version": "2.0",
            "theme": {
                "id": theme_id,
                "name": theme_name,
                "description": description,
            },
            "subthemes": subtheme_nodes,
            "metadata": {
                "total_topics": total_topics,
                "status_count": {status: 0 for status in self.governance_defaults.get("status_flow", DEFAULT_STATUS_FLOW)},
                "created_at": now,
                "last_updated": now,
            },
        }

    def save_topic_index(self, index_data: dict, output_path: Optional[Path] = None) -> Path:
        """保存主题索引，并注册到 theme_registry。"""
        theme = index_data.get("theme", {})
        theme_id = theme.get("id")
        if not theme_id:
            raise GovernanceError("索引缺少 theme.id。")

        target = output_path or (self.governance_root / f"topic_index.{theme_id}.json")
        self._write_json(target, index_data)
        self._register_theme(theme_id=theme_id, theme_name=theme.get("name", theme_id), index_path=target)
        return target

    def _register_theme(self, theme_id: str, theme_name: str, index_path: Path) -> None:
        registry_path = self.governance_root / "theme_registry.json"
        registry = self._load_json(registry_path, fallback={"schema_version": "2.0", "themes": []})
        themes = registry.setdefault("themes", [])

        try:
            stored_index_path = str(index_path.relative_to(self.content_root)).replace("\\", "/")
        except ValueError:
            stored_index_path = str(index_path.resolve())

        found = next((theme for theme in themes if theme.get("id") == theme_id), None)
        now = datetime.now().isoformat(timespec="seconds")
        payload = {
            "id": theme_id,
            "name": theme_name,
            "index_file": stored_index_path,
            "updated_at": now,
        }
        if found:
            found.update(payload)
        else:
            payload["created_at"] = now
            themes.append(payload)

        registry["last_updated"] = now
        self._write_json(registry_path, registry)

    def load_topic_index(self, index_file: Path) -> dict:
        """加载主题索引。"""
        if not index_file.exists():
            raise GovernanceError(f"索引文件不存在: {index_file}")
        return self._load_json(index_file, fallback={})

    def plan_topics(self, index_file: Path, count: int, subtheme: Optional[str] = None) -> List[dict]:
        """按 pending 优先规则规划待生成话题。"""
        if count <= 0:
            return []
        index = self.load_topic_index(index_file)
        candidates: List[dict] = []

        for sub in index.get("subthemes", []):
            if subtheme and sub.get("id") != subtheme and sub.get("name") != subtheme:
                continue
            for topic in sub.get("topics", []):
                if topic.get("status") == "pending":
                    candidates.append(
                        {
                            "theme_id": index.get("theme", {}).get("id"),
                            "theme_name": index.get("theme", {}).get("name"),
                            "subtheme_id": sub.get("id"),
                            "subtheme_name": sub.get("name"),
                            "topic_id": topic.get("id"),
                            "topic_name": topic.get("name"),
                            "status": topic.get("status"),
                        }
                    )

        return candidates[:count]

    def mark_topic_status(
        self,
        index_file: Path,
        topic_ids: Iterable[str],
        status: str,
        note: str = "",
    ) -> dict:
        """批量更新三级话题状态。"""
        status_flow = self.governance_defaults.get("status_flow", DEFAULT_STATUS_FLOW)
        if status not in status_flow:
            raise GovernanceError(f"非法状态: {status}, 允许值: {status_flow}")

        index = self.load_topic_index(index_file)
        target_ids = set(topic_ids)
        now = datetime.now().isoformat(timespec="seconds")
        updated = []

        for sub in index.get("subthemes", []):
            for topic in sub.get("topics", []):
                if topic.get("id") in target_ids:
                    topic["status"] = status
                    topic["updated_at"] = now
                    if note:
                        topic["note"] = note
                    updated.append(topic["id"])

        index["metadata"]["last_updated"] = now
        index["metadata"]["status_count"] = self._recount_status(index)
        self._write_json(index_file, index)
        return {"updated_topic_ids": updated, "status": status}

    def _recount_status(self, index: dict) -> dict:
        status_counter = {status: 0 for status in self.governance_defaults.get("status_flow", DEFAULT_STATUS_FLOW)}
        for sub in index.get("subthemes", []):
            for topic in sub.get("topics", []):
                status = topic.get("status", "pending")
                status_counter[status] = status_counter.get(status, 0) + 1
        return status_counter

    def append_content_record(
        self,
        theme_id: str,
        subtheme_id: str,
        topic_id: str,
        title: str,
        file_path: str,
        status: str = "generated",
        evidence_level: str = "conditional",
    ) -> dict:
        """向内容台账写入记录。"""
        evidence_levels = self.governance_defaults.get("science_validation", {}).get(
            "evidence_levels", DEFAULT_EVIDENCE_LEVELS
        )
        if evidence_level not in evidence_levels:
            raise GovernanceError(f"非法 evidence_level: {evidence_level}")

        now = datetime.now().isoformat(timespec="seconds")
        content_hash = hashlib.md5(f"{title}|{file_path}|{now}".encode("utf-8")).hexdigest()
        record = {
            "id": content_hash[:12],
            "theme_id": theme_id,
            "subtheme_id": subtheme_id,
            "topic_id": topic_id,
            "title": title,
            "file_path": file_path,
            "status": status,
            "evidence_level": evidence_level,
            "content_hash": content_hash,
            "created_at": now,
        }
        ledger_path = self.governance_root / "content_index.jsonl"
        with ledger_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def get_life_tips_template(self) -> dict:
        """读取生活小妙招短屏模板配置。"""
        registry = self.template_registry.get("templates", [])
        tpl = next((item for item in registry if item.get("id") == "life_tips.short_mobile.v2"), None)
        if not tpl:
            raise GovernanceError("模板注册缺少 life_tips.short_mobile.v2")
        template_path = self.skill_root / tpl["path"]
        symbol_pack_path = self.skill_root / tpl["symbol_pack"]
        validation_path = self.skill_root / tpl["validation"]

        return {
            "template_markdown": template_path.read_text(encoding="utf-8"),
            "symbol_pack": self._load_json(symbol_pack_path, fallback={"styles": []}),
            "validation_rules": self._load_json(validation_path, fallback={}),
        }

    @staticmethod
    def parse_subtheme_spec(raw_spec: str) -> Dict[str, List[str]]:
        """解析二级/三级主题表达式。

        示例：
        厨房:冰箱去异味,菜板杀菌;浴室:镜子清洁,防霉
        """
        mapping: Dict[str, List[str]] = {}
        if not raw_spec.strip():
            return mapping
        for segment in raw_spec.split(";"):
            if not segment.strip():
                continue
            if ":" not in segment:
                raise GovernanceError(f"二级主题格式错误: {segment}")
            name, topics_raw = segment.split(":", 1)
            topics = [item.strip() for item in topics_raw.split(",") if item.strip()]
            if not topics:
                raise GovernanceError(f"二级主题 {name} 未提供三级话题")
            mapping[name.strip()] = topics
        return mapping


def emit_json(payload: dict) -> None:
    """Windows 控制台编码兼容输出。"""
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="小红书主题治理与模板辅助脚本")
    parser.add_argument(
        "--content-root",
        default="",
        help="可选：指定小红书内容输出根目录；不传则使用技能根目录或环境变量 XHS_CONTENT_ROOT",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_index = subparsers.add_parser("create-topic-index", help="创建主题索引 JSON")
    create_index.add_argument("--theme", required=True, help="一级主题名称")
    create_index.add_argument(
        "--subthemes",
        required=True,
        help="二级/三级主题，格式：二级A:三级1,三级2;二级B:三级3,三级4",
    )
    create_index.add_argument("--description", default="", help="主题描述")
    create_index.add_argument("--output", default="", help="输出路径，默认写入 _governance")

    plan_topics = subparsers.add_parser("plan-topics", help="按索引规划待生成话题")
    plan_topics.add_argument("--index", required=True, help="主题索引文件路径")
    plan_topics.add_argument("--count", type=int, required=True, help="计划生成条数")
    plan_topics.add_argument("--subtheme", default="", help="指定二级主题 id 或 name")

    mark_status = subparsers.add_parser("mark-status", help="更新话题状态")
    mark_status.add_argument("--index", required=True, help="主题索引文件路径")
    mark_status.add_argument("--status", required=True, help="目标状态")
    mark_status.add_argument("--topic-ids", nargs="+", required=True, help="三级话题 id 列表")
    mark_status.add_argument("--note", default="", help="补充说明")

    add_record = subparsers.add_parser("add-record", help="写入内容台账")
    add_record.add_argument("--theme-id", required=True)
    add_record.add_argument("--subtheme-id", required=True)
    add_record.add_argument("--topic-id", required=True)
    add_record.add_argument("--title", required=True)
    add_record.add_argument("--file-path", required=True)
    add_record.add_argument("--status", default="generated")
    add_record.add_argument("--evidence-level", default="conditional")

    show_life_tips = subparsers.add_parser("show-life-tips-template", help="预览生活小妙招模板配置")
    show_life_tips.add_argument("--pick-style", action="store_true", help="随机展示一个符号风格包")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    content_root = Path(args.content_root).expanduser().resolve() if args.content_root else None
    generator = XiaohongshuGenerator(content_root=content_root)

    if args.command == "create-topic-index":
        subthemes = generator.parse_subtheme_spec(args.subthemes)
        index_data = generator.create_topic_index(theme_name=args.theme, subthemes=subthemes, description=args.description)
        output_path = Path(args.output) if args.output else None
        saved = generator.save_topic_index(index_data=index_data, output_path=output_path)
        emit_json({"saved": str(saved), "theme_id": index_data["theme"]["id"]})
        return

    if args.command == "plan-topics":
        plan = generator.plan_topics(
            index_file=Path(args.index),
            count=args.count,
            subtheme=args.subtheme or None,
        )
        emit_json({"count": len(plan), "topics": plan})
        return

    if args.command == "mark-status":
        result = generator.mark_topic_status(
            index_file=Path(args.index),
            topic_ids=args.topic_ids,
            status=args.status,
            note=args.note,
        )
        emit_json(result)
        return

    if args.command == "add-record":
        record = generator.append_content_record(
            theme_id=args.theme_id,
            subtheme_id=args.subtheme_id,
            topic_id=args.topic_id,
            title=args.title,
            file_path=args.file_path,
            status=args.status,
            evidence_level=args.evidence_level,
        )
        emit_json(record)
        return

    if args.command == "show-life-tips-template":
        payload = generator.get_life_tips_template()
        response = {
            "template_preview": payload["template_markdown"],
            "validation_rules": payload["validation_rules"],
        }
        if args.pick_style:
            styles = payload["symbol_pack"].get("styles", [])
            response["symbol_style"] = random.choice(styles) if styles else {}
        else:
            response["symbol_style_count"] = len(payload["symbol_pack"].get("styles", []))
        emit_json(response)
        return

    raise GovernanceError(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()

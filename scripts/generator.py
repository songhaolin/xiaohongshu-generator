#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书内容生成器
核心逻辑：实时搜索 + 模板生成
"""

import json
import random
from pathlib import Path

class XiaohongshuGenerator:
    """小红书内容生成器"""

    def __init__(self, data_dir=None):
        """初始化生成器"""
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)

        # 加载索引和模板
        self.topics_index = self._load_json("topics_index.json")
        self.templates = self._load_json("generation_templates.json")

    def _load_json(self, filename):
        """加载JSON文件"""
        filepath = self.data_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_categories(self):
        """获取所有内容分类"""
        return self.topics_index["categories"]

    def get_category_by_id(self, category_id):
        """根据ID获取分类"""
        for cat in self.topics_index["categories"]:
            if cat["id"] == category_id:
                return cat
        return None

    def get_random_topic(self, category_id=None, subcategory_id=None):
        """
        获取随机选题

        Args:
            category_id: 分类ID，如 None 则随机选择
            subcategory_id: 子分类ID，如 None 则随机选择

        Returns:
            dict: {category, subcategory, topic}
        """
        if category_id is None:
            # 随机选择分类（按权重）
            categories = self.get_categories()
            weights = [cat["weight"] for cat in categories]
            category = random.choices(categories, weights=weights, k=1)[0]
        else:
            category = self.get_category_by_id(category_id)

        if subcategory_id is None:
            # 随机选择子分类
            subcategory = random.choice(category["subcategories"])
        else:
            subcategory = next(
                (sub for sub in category["subcategories"] if sub["id"] == subcategory_id),
                None
            )

        # 随机选择主题
        if "topics" in subcategory:
            topic = random.choice(subcategory["topics"])
        else:
            # 对于故事类，从示例主题中选择
            topic = random.choice(subcategory.get("sample_topics", ["温馨故事"]))

        return {
            "category": category,
            "subcategory": subcategory,
            "topic": topic
        }

    def generate_search_keywords(self, selection):
        """
        生成搜索关键词

        Args:
            selection: 选题信息

        Returns:
            list: 搜索关键词列表
        """
        category_id = selection["category"]["id"]
        topic = selection["topic"]
        template = self.templates.get(f"{category_id}_template", {})

        search_keywords = template.get("search_keywords", [topic])

        # 替换占位符
        keywords = []
        for kw in search_keywords:
            kw = kw.replace("{topic}", topic)
            kw = kw.replace("{scenery_name}", topic)
            kw = kw.replace("{story_title}", topic)
            keywords.append(kw)

        return keywords

    def generate_title(self, selection):
        """
        生成标题

        Args:
            selection: 选题信息

        Returns:
            str: 标题
        """
        category_id = selection["category"]["id"]
        topic = selection["topic"]
        template = self.templates.get(f"{category_id}_template", {})

        title_patterns = template.get("title_pattern", [topic])
        title_pattern = random.choice(title_patterns)

        # 替换占位符
        title = title_pattern.replace("{topic}", topic)
        title = title.replace("{scenery_name}", topic)
        title = title.replace("{story_title}", topic)
        title = title.replace("{number}", str(random.randint(3, 5)))

        return title

    def generate_hashtags(self, selection):
        """
        生成话题标签

        Args:
            selection: 选题信息

        Returns:
            list: 话题标签列表
        """
        category_id = selection["category"]["id"]
        template = self.templates.get(f"{category_id}_template", {})
        hashtags = template.get("hashtags", [])

        # 添加子分类相关标签
        subcategory = selection["subcategory"]
        if "name" in subcategory:
            hashtags.append(subcategory["name"])

        return hashtags

    def get_image_style(self, category_id):
        """
        获取图片风格描述

        Args:
            category_id: 分类ID

        Returns:
            str: 图片风格描述
        """
        template = self.templates.get(f"{category_id}_template", {})
        return template.get("image_style", "温馨风格")

    def get_structure_template(self, category_id):
        """
        获取内容结构模板

        Args:
            category_id: 分类ID

        Returns:
            dict: 结构模板
        """
        template = self.templates.get(f"{category_id}_template", {})
        return template.get("structure", {})

    def print_selection(self, selection):
        """打印选题信息（调试用）"""
        print(f"\n{'='*60}")
        print(f"分类: {selection['category']['name']}")
        print(f"子分类: {selection['subcategory']['name']}")
        print(f"主题: {selection['topic']}")
        print(f"发布时间: {selection['category'].get('publish_time', 'anytime')}")
        print(f"{'='*60}\n")


def main():
    """测试函数"""
    generator = XiaohongshuGenerator()

    # 测试随机选题
    print("测试随机选题：")
    for i in range(5):
        selection = generator.get_random_topic()
        generator.print_selection(selection)

        # 生成标题
        title = generator.generate_title(selection)
        print(f"标题: {title}")

        # 生成搜索关键词
        keywords = generator.generate_search_keywords(selection)
        print(f"搜索关键词: {', '.join(keywords)}")

        # 生成话题标签
        hashtags = generator.generate_hashtags(selection)
        print(f"话题标签: {' '.join(['#' + tag for tag in hashtags])}")

        print()


if __name__ == "__main__":
    main()

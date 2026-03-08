"""AI 服务 - 使用 OpenRouter API (兼容 OpenAI SDK)"""
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from ..config import settings


class AIService:
    """AI 服务 - 热点分析、真实性验证"""
    
    _client: Optional[AsyncOpenAI] = None
    
    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        """获取 OpenAI 客户端（配置为 OpenRouter）"""
        if cls._client is None:
            cls._client = AsyncOpenAI(
                base_url=settings.OPENROUTER_BASE_URL,
                api_key=settings.OPENROUTER_API_KEY,
                default_headers={
                    "HTTP-Referer": "https://hot-monitor.local",
                    "X-Title": "Hot Monitor",
                }
            )
        return cls._client
    
    @classmethod
    async def analyze_hotspot(
        cls,
        title: str,
        content: str,
        source: str,
    ) -> Dict[str, Any]:
        """
        分析热点内容
        
        返回:
        - score: 重要性评分 0-100
        - is_verified: 是否经过验证
        - is_fake: 是否可能是假消息
        - summary: 内容摘要
        - analysis: 详细分析
        - tags: 标签列表
        """
        if not settings.OPENROUTER_API_KEY:
            # 没有配置 API Key，返回默认值
            return {
                "score": 50,
                "is_verified": False,
                "is_fake": False,
                "summary": content[:200] if content else title,
                "analysis": "AI服务未配置",
                "tags": [],
            }
        
        prompt = f"""请分析以下热点内容，并以 JSON 格式返回分析结果：

标题: {title}
来源: {source}
内容: {content[:2000] if content else '无详细内容'}

请返回以下格式的 JSON（不要包含 markdown 代码块）:
{{
    "score": <重要性评分0-100，基于内容的新闻价值、影响力、相关性>,
    "is_verified": <布尔值，内容是否看起来真实可信>,
    "is_fake": <布尔值，是否可能是假消息/谣言/标题党>,
    "summary": "<50字以内的中文摘要>",
    "analysis": "<100字以内的详细分析，说明为什么给出这个评分>",
    "tags": ["<相关标签1>", "<相关标签2>", "<相关标签3>"]
}}

注意：
1. 如果内容涉及AI、大模型、科技突破等话题，给予较高评分
2. 如果标题明显夸张、不实或是营销内容，标记为可能是假消息
3. 标签应该包含技术领域、相关公司/产品名称等"""

        try:
            client = cls.get_client()
            response = await client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的科技新闻分析师，擅长识别假新闻和评估新闻价值。请直接返回JSON，不要使用markdown代码块。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 尝试解析 JSON
            # 清理可能的 markdown 代码块
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            return {
                "score": min(100, max(0, result.get("score", 50))),
                "is_verified": bool(result.get("is_verified", False)),
                "is_fake": bool(result.get("is_fake", False)),
                "summary": str(result.get("summary", ""))[:200],
                "analysis": str(result.get("analysis", ""))[:500],
                "tags": result.get("tags", [])[:10],
            }
            
        except json.JSONDecodeError as e:
            print(f"AI 返回的 JSON 解析失败: {e}")
            return cls._default_result(title, content)
        except Exception as e:
            print(f"AI 分析失败: {e}")
            return cls._default_result(title, content)
    
    @classmethod
    def _default_result(cls, title: str, content: str) -> Dict[str, Any]:
        """返回默认分析结果"""
        return {
            "score": 50,
            "is_verified": False,
            "is_fake": False,
            "summary": content[:200] if content else title[:200],
            "analysis": "自动分析",
            "tags": [],
        }
    
    @classmethod
    async def check_keyword_match(
        cls,
        keyword: str,
        title: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        检查内容是否真正匹配关键词（防止假冒/不相关内容）
        
        返回:
        - is_match: 是否真正相关
        - confidence: 置信度 0-100
        - reason: 原因说明
        """
        if not settings.OPENROUTER_API_KEY:
            # 简单的关键词匹配
            text = (title + " " + content).lower()
            is_match = keyword.lower() in text
            return {
                "is_match": is_match,
                "confidence": 80 if is_match else 20,
                "reason": "基于关键词匹配",
            }
        
        prompt = f"""判断以下内容是否真正与关键词"{keyword}"相关：

标题: {title}
内容: {content[:1000] if content else '无详细内容'}

请判断：
1. 内容是否真正讨论/涉及"{keyword}"这个主题
2. 不要被标题党或不相关的提及所迷惑
3. 内容需要有实质性的相关信息

返回 JSON 格式（不要代码块）:
{{
    "is_match": <布尔值>,
    "confidence": <置信度0-100>,
    "reason": "<简短说明原因>"
}}"""

        try:
            client = cls.get_client()
            response = await client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个内容相关性分析专家。直接返回JSON。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            return {
                "is_match": bool(result.get("is_match", True)),
                "confidence": min(100, max(0, result.get("confidence", 50))),
                "reason": str(result.get("reason", "")),
            }
            
        except Exception as e:
            print(f"关键词匹配检查失败: {e}")
            # 降级为简单匹配
            text = (title + " " + content).lower()
            is_match = keyword.lower() in text
            return {
                "is_match": is_match,
                "confidence": 60 if is_match else 40,
                "reason": "降级为关键词匹配",
            }
    
    @classmethod
    async def generate_summary(cls, hotspots: list) -> str:
        """
        为多个热点生成综合摘要
        """
        if not settings.OPENROUTER_API_KEY or not hotspots:
            return ""
        
        hotspot_text = "\n".join([
            f"- {h.get('title', '')}: {h.get('summary', '')}"
            for h in hotspots[:10]
        ])
        
        prompt = f"""请为以下热点内容生成一段100字以内的综合摘要：

{hotspot_text}

要求：
1. 突出最重要的内容
2. 使用简洁的中文
3. 适合快速浏览"""

        try:
            client = cls.get_client()
            response = await client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个新闻摘要专家。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"生成摘要失败: {e}")
            return ""

"""
RAG 检索增强生成模块
"""

import streamlit as st
import re
from typing import List, Dict, Any, Optional


class RAGRetriever:
    """RAG 检索器 - 从知识库检索相关内容"""

    def __init__(self, kb_manager):
        self.kb_manager = kb_manager

    def retrieve(self, query: str, top_k: int = 5, category: str = None, min_similarity: float = 0.3) -> List[Dict]:
        """检索相关内容"""
        if not self.kb_manager:
            return []

        try:
            results = self.kb_manager.search(query, top_k=top_k, category=category)

            # 过滤低相关度结果
            filtered = [r for r in results if r.get('similarity', 0) >= min_similarity]

            return filtered
        except Exception as e:
            print(f"检索失败: {e}")
            return []

    def format_context(self, results: List[Dict], max_chars: int = 2000) -> str:
        """格式化检索结果为上下文"""
        if not results:
            return ""

        context = "【知识库参考资料】\n\n"
        total_chars = 0

        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            title = result.get('title', '')
            similarity = result.get('similarity', 0)

            # 截取内容
            if len(content) > 500:
                content = content[:500] + "..."

            context += f"**参考资料 {i}**（相关度: {similarity:.1%}）\n"
            if title:
                context += f"来源：{title}\n"
            context += f"内容：{content}\n\n"

            total_chars += len(content)
            if total_chars >= max_chars:
                break

        return context


class RAGGenerator:
    """RAG 生成器 - 基于检索结果生成回答"""

    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.retriever = None

    def set_retriever(self, retriever):
        self.retriever = retriever

    def generate(self, query: str, history: List = None, category: str = None,
                 top_k: int = 3, min_similarity: float = 0.3):
        """RAG 生成回答"""

        # 1. 检索相关内容
        if self.retriever:
            results = self.retriever.retrieve(query, top_k=top_k, category=category, min_similarity=min_similarity)
        else:
            results = []

        # 2. 构建 prompt
        if results:
            context = self._format_context_for_prompt(results)
            prompt = self._build_rag_prompt(query, context)
            has_context = True
        else:
            prompt = self._build_normal_prompt(query)
            has_context = False

        # 3. 调用大模型
        try:
            response, used_provider, status = self.model_manager.smart_chat(prompt, history)

            if status == "success":
                # 添加来源标注
                if has_context:
                    sources = self._format_sources(results)
                    response = f"{response}\n\n---\n *参考了 {len(results)} 条知识库内容*"
                    if sources:
                        response += f"\n{sources}"
                return response, used_provider
            else:
                return f"❌ 生成失败: {response}", "error"
        except Exception as e:
            return f"❌ 生成失败: {str(e)}", "error"

    def _format_context_for_prompt(self, results: List[Dict]) -> str:
        """格式化检索结果为 prompt 上下文"""
        context = "以下是相关知识库内容，请基于这些信息回答用户问题：\n\n"

        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            title = result.get('title', '')

            # 截取合适长度
            if len(content) > 800:
                content = content[:800] + "..."

            context += f"【参考{i}】"
            if title:
                context += f"（来源：{title}）"
            context += f"\n{content}\n\n"

        context += "请根据以上参考资料回答用户问题。如果参考资料中没有相关信息，请如实告知用户。"

        return context

    def _build_rag_prompt(self, query: str, context: str) -> str:
        """构建 RAG prompt"""
        system_instruction = """你是一个专业的校园智能助手。请基于提供的参考资料回答用户问题。

要求：
1. 优先使用参考资料中的信息
2. 如果参考资料中有具体信息（如时间、地点、条件等），要准确引用
3. 如果参考资料不足，如实告知用户
4. 回答要清晰、有条理
5. 使用中文回复"""

        prompt = f"{system_instruction}\n\n{context}\n\n用户问题：{query}\n\n回答："

        return prompt

    def _build_normal_prompt(self, query: str) -> str:
        """构建普通 prompt（无检索结果）"""
        prompt = f"""你是一个专业的校园智能助手。

用户问题：{query}

请根据你的知识回答。如果问题涉及校园具体信息（如课程、教室、活动、奖学金等），建议用户通过知识库管理上传相关信息。"""

        return prompt

    def _format_sources(self, results: List[Dict]) -> str:
        """格式化来源信息"""
        sources = "\n\n📖 **信息来源**："
        for result in results[:3]:
            title = result.get('title', '')
            similarity = result.get('similarity', 0)
            if title:
                sources += f"\n• {title}（相关度 {similarity:.1%}）"
        return sources


class RAGQueryProcessor:
    """RAG 查询处理器 - 智能路由和查询"""

    def __init__(self, model_manager, kb_manager):
        self.model_manager = model_manager
        self.retriever = RAGRetriever(kb_manager)
        self.generator = RAGGenerator(model_manager)
        self.generator.set_retriever(self.retriever)

    def process_query(self, query: str, history: List = None) -> str:
        """处理用户查询"""

        # 1. 意图识别
        intent = self._detect_intent(query)

        # 2. 根据意图路由
        if intent == "course":
            return self._handle_course_query(query)
        elif intent == "classroom":
            return self._handle_classroom_query(query)
        elif intent == "canteen":
            return self._handle_canteen_query(query)
        elif intent == "activity":
            return self._handle_activity_query(query)
        elif intent == "scholarship":
            return self._handle_scholarship_query(query)
        else:
            # 通用 RAG 查询
            response, provider = self.generator.generate(query, history, top_k=5)
            return response

    def _detect_intent(self, query: str) -> str:
        """检测查询意图"""
        query_lower = query.lower()

        if any(kw in query_lower for kw in ["课", "课程", "课表", "上课"]):
            return "course"
        elif any(kw in query_lower for kw in ["教室", "空教室", "自习室"]):
            return "classroom"
        elif any(kw in query_lower for kw in ["食堂", "吃饭", "餐厅", "美食"]):
            return "canteen"
        elif any(kw in query_lower for kw in ["活动", "讲座", "比赛", "晚会"]):
            return "activity"
        elif any(kw in query_lower for kw in ["奖学金", "助学金", "资助"]):
            return "scholarship"
        else:
            return "general"

    def _handle_course_query(self, query: str) -> str:
        """处理课程查询"""
        try:
            from modules.services.course_service import query_today_course
            return query_today_course()
        except Exception as e:
            return f"课程查询失败: {e}"

    def _handle_classroom_query(self, query: str) -> str:
        """处理教室查询"""
        try:
            from modules.services.classroom_service import query_current_room
            return query_current_room()
        except Exception as e:
            return f"教室查询失败: {e}"

    def _handle_canteen_query(self, query: str) -> str:
        """处理食堂查询"""
        try:
            from modules.services.canteen_service import query_current_canteen
            return query_current_canteen()
        except Exception as e:
            return f"食堂查询失败: {e}"

    def _handle_activity_query(self, query: str) -> str:
        """处理活动查询"""
        try:
            from modules.services.activity_service import query_current_month_activity
            return query_current_month_activity()
        except Exception as e:
            return f"活动查询失败: {e}"

    def _handle_scholarship_query(self, query: str) -> str:
        """处理奖学金查询（使用 RAG）"""
        response, provider = self.generator.generate(query, top_k=5, category="规章制度")
        return response


# ==================== 辅助函数 ====================

def init_rag_system(model_manager, kb_manager):
    """初始化 RAG 系统"""
    if model_manager and kb_manager:
        return RAGQueryProcessor(model_manager, kb_manager)
    return None


def rag_chat(rag_processor, user_input: str, history: List = None) -> str:
    """RAG 智能对话入口"""
    if rag_processor:
        return rag_processor.process_query(user_input, history)
    else:
        return "RAG系统未初始化，请检查知识库连接。"
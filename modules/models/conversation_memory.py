"""
对话记忆管理器 - 管理多轮对话上下文
"""
from datetime import datetime
from modules.config import MAX_HISTORY_LENGTH, MAX_CONTEXT_TOKENS


class ConversationMemory:
    def __init__(self, max_history=MAX_HISTORY_LENGTH):
        self.max_history = max_history
        self.system_prompt = """你是朔方智域校园智能助手，一个友好、专业的校园生活学习助手。
你可以帮助学生：
- 查询课程表、空教室、食堂推荐、校园活动
- 解答学习问题、提供生活帮助
- 分析图片内容
- 进行智能检索

请用中文回复，保持热情友好的语气。"""

    def format_history_for_deepseek(self, history):
        messages = []
        messages.append({"role": "system", "content": self.system_prompt})
        for msg in history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant" and msg["content"]:
                content = msg["content"]
                if len(content) > 2000:
                    content = content[:2000] + "...(内容已截断)"
                messages.append({"role": "assistant", "content": content})
        return messages

    def format_history_for_ollama(self, history):
        if not history:
            return ""
        formatted = ""
        for msg in history:
            if msg["role"] == "user":
                formatted += f"用户: {msg['content']}\n"
            elif msg["role"] == "assistant" and msg["content"]:
                content = msg["content"]
                if len(content) > 1500:
                    content = content[:1500] + "..."
                formatted += f"助手: {content}\n"
        return formatted

    def compress_history(self, history, max_tokens=MAX_CONTEXT_TOKENS):
        if not history:
            return history

        def estimate_tokens(text):
            if not text:
                return 0
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            english_words = len([w for w in text.split() if w.isalpha()])
            return chinese_chars * 2 + english_words * 1.3

        compressed = []
        total_tokens = 0
        for msg in reversed(history):
            content_tokens = estimate_tokens(msg.get("content", ""))
            if total_tokens + content_tokens > max_tokens:
                break
            compressed.insert(0, msg)
            total_tokens += content_tokens
        if not compressed and len(history) >= 2:
            compressed = history[-2:]
        return compressed

    def add_to_history(self, history, role, content, max_history=None):
        max_len = max_history or self.max_history
        history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        if len(history) > max_len:
            history.pop(0)
        return history

    def clear_history(self):
        return []
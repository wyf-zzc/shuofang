"""
智能模型管理器 - 实现双模式切换（DeepSeek/Ollama）
"""
import time
import requests
from datetime import datetime
from modules.config import *
from modules.models.conversation_memory import ConversationMemory
from modules.models.network_detector import network_detector


class SmartModelManager:
    def __init__(self):
        self.mode = "auto"
        self.deepseek_available = False
        self.ollama_available = False
        self.current_provider = None
        self.conversation_memory = ConversationMemory()
        self.stats = {"deepseek": {"calls": 0, "last_used": None}, "ollama": {"calls": 0, "last_used": None}}

    def set_mode(self, mode):
        if mode in ["auto", "deepseek", "ollama"]:
            self.mode = mode
            return True
        return False

    def check_services(self):
        self.deepseek_available, _ = self._check_deepseek_service()
        self.ollama_available, _ = self._check_ollama_service()
        return {"deepseek": self.deepseek_available, "ollama": self.ollama_available}

    def _check_deepseek_service(self):
        if not DEEPSEEK_API_KEY:
            return False, "❌ 未配置DeepSeek API密钥"
        try:
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            response = requests.get(f"{DEEPSEEK_API_BASE}/models", headers=headers, timeout=5)
            if response.status_code == 200:
                return True, "✅ DeepSeek服务正常"
            return False, f"❌ DeepSeek服务异常: HTTP {response.status_code}"
        except Exception as e:
            return False, f"❌ 无法连接DeepSeek: {e}"

    def _check_ollama_service(self):
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                return True, "✅ Ollama服务正常"
            return False, f"❌ Ollama服务异常: HTTP {response.status_code}"
        except Exception as e:
            return False, f"❌ 无法连接Ollama: {e}"

    def get_best_provider(self, is_vision=False):
        if self.mode == "deepseek":
            return "deepseek" if self.deepseek_available else None
        elif self.mode == "ollama":
            return "ollama" if self.ollama_available else None
        network_online = network_detector.is_online()
        if network_online and self.deepseek_available:
            return "deepseek"
        elif self.ollama_available:
            return "ollama"
        return None

    def chat_with_deepseek(self, prompt, history=None, is_vision=False, image_base64=None):
        self.stats["deepseek"]["calls"] += 1
        self.stats["deepseek"]["last_used"] = datetime.now().isoformat()
        try:
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            if is_vision and image_base64:
                messages = [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}]
                model = DEEPSEEK_VISION_MODEL
            else:
                if history:
                    messages = self.conversation_memory.format_history_for_deepseek(history)
                    messages.append({"role": "user", "content": prompt})
                else:
                    messages = [
                        {"role": "system", "content": self.conversation_memory.system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                model = DEEPSEEK_TEXT_MODEL
            payload = {"model": model, "messages": messages, "max_tokens": 1000, "temperature": 0.7, "stream": False}
            response = requests.post(f"{DEEPSEEK_API_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"], None
            return None, f"DeepSeek API错误: {response.status_code}"
        except Exception as e:
            return None, f"DeepSeek连接失败: {str(e)}"

    def chat_with_ollama(self, prompt, history=None, is_vision=False, image_base64=None, model=OLLAMA_TEXT_MODEL):
        self.stats["ollama"]["calls"] += 1
        self.stats["ollama"]["last_used"] = datetime.now().isoformat()
        try:
            # 构建 prompt
            full_prompt = prompt

            # 添加历史（如果启用）
            if history and not is_vision:
                history_text = self.conversation_memory.format_history_for_ollama(history)
                if history_text:
                    full_prompt = history_text + f"用户: {prompt}\n助手: "

            # 限制 prompt 长度
            if len(full_prompt) > 3000:
                full_prompt = full_prompt[-3000:]

            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500
                }
            }

            if is_vision and image_base64:
                payload["images"] = [image_base64]
                payload["model"] = LOCAL_VISION_MODEL

            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=90
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get("response", "")
                if not result:
                    result = "抱歉，我没有理解您的问题。"
                return result, None
            else:
                return None, f"Ollama错误: {response.status_code}"

        except Exception as e:
            return None, f"Ollama连接失败: {str(e)}"

    def smart_chat(self, prompt, history=None, is_vision=False, image_base64=None, fallback=True):
        # ✅ 先检查服务状态，更新可用性
        services = self.check_services()

        best_provider = self.get_best_provider(is_vision)
        if not best_provider:
            return "⚠️ 无可用AI服务，请检查网络连接和本地Ollama服务", None, "error"

        result = None
        error = None
        used_provider = best_provider

        if best_provider == "deepseek":
            result, error = self.chat_with_deepseek(prompt, history, is_vision, image_base64)
            # ✅ 使用更新后的 self.ollama_available
            if error and fallback and self.ollama_available:
                used_provider = "ollama"
                result, error = self.chat_with_ollama(prompt, history, is_vision, image_base64)
                if not error:
                    result = f"⚠️ DeepSeek服务异常，已切换到本地Ollama:\n\n{result}"

        elif best_provider == "ollama":
            result, error = self.chat_with_ollama(prompt, history, is_vision, image_base64)
            # ✅ 使用更新后的 self.deepseek_available
            if error and fallback and self.deepseek_available and network_detector.is_online():
                used_provider = "deepseek"
                result, error = self.chat_with_deepseek(prompt, history, is_vision, image_base64)
                if not error:
                    result = f"⚠️ Ollama服务异常，已切换到DeepSeek云端:\n\n{result}"

        if error:
            return f"❌ 服务调用失败: {error}", None, "error"

        return result, used_provider, "success"

    def get_stats_summary(self):
        return {
            "deepseek_calls": self.stats["deepseek"]["calls"],
            "ollama_calls": self.stats["ollama"]["calls"],
            "total_calls": self.stats["deepseek"]["calls"] + self.stats["ollama"]["calls"],
            "current_mode": self.mode,
            "current_provider": self.current_provider
        }
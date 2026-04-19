"""
硅基流动图片分析器 - 云端视觉模型
"""
import streamlit as st
import requests
from modules.config import st as config_st
from modules.models.network_detector import network_detector
from modules.vision.ollama_vision import PureOllamaVisionAnalyzer


class SmartVisionAnalyzer:
    def __init__(self):
        self.ollama_analyzer = PureOllamaVisionAnalyzer()
        self.siliconflow_api_key = config_st.secrets.get("SILICONFLOW_API_KEY", "")
        self.siliconflow_base_url = "https://api.siliconflow.cn/v1"

    def analyze_image_smart(self, image_file, question):
        if network_detector.is_online() and self.siliconflow_api_key:
            try:
                image_base64 = self.ollama_analyzer.encode_image_to_base64(image_file)
                if not image_base64:
                    st.warning("图片编码失败，将使用本地模型")
                else:
                    with st.spinner("🌐 正在使用 Qwen3-VL (硅基流动) 分析图片..."):
                        headers = {
                            "Authorization": f"Bearer {self.siliconflow_api_key}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": "Qwen/Qwen3-VL-30B-A3B-Instruct",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": question},
                                        {"type": "image_url",
                                         "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                                    ]
                                }
                            ],
                            "max_tokens": 1000,
                            "temperature": 0.7
                        }
                        response = requests.post(
                            f"{self.siliconflow_base_url}/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=60
                        )
                        if response.status_code == 200:
                            data = response.json()
                            result = data["choices"][0]["message"]["content"]
                            st.toast("✅ 使用 Qwen3-VL 分析完成", icon="🌐")
                            return f"🌐 {result}", "qwen"
                        else:
                            st.warning(f"API 返回错误 {response.status_code}，将使用本地模型")
            except Exception as e:
                st.warning(f"API 调用失败: {e}，将使用本地模型")

        with st.spinner("💻 使用本地 Ollama 分析图片中..."):
            result, error = self.ollama_analyzer.analyze_image_simple(image_file, question)
        if error:
            return f"❌ 图片分析失败: {error}", None
        st.toast("✅ 使用本地 Ollama 分析完成", icon="💻")
        return f"💻 {result}", "ollama"

    def analyze_image(self, image_file, question):
        return self.analyze_image_smart(image_file, question)
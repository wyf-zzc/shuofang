"""
本地Ollama图片分析器
"""
import base64
import requests
from PIL import Image
from io import BytesIO
from modules.config import OLLAMA_BASE_URL


class PureOllamaVisionAnalyzer:
    def __init__(self, base_url=None, model=None):
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or "moondream:latest"

    def encode_image_to_base64(self, image_file, max_size=384, quality=60):
        try:
            if hasattr(image_file, 'read'):
                img_bytes = image_file.read()
                img = Image.open(BytesIO(img_bytes))
            elif isinstance(image_file, bytes):
                img = Image.open(BytesIO(image_file))
            else:
                raise ValueError("不支持的图片格式")
            if img.mode != 'RGB':
                img = img.convert('RGB')
            if img.size[0] > max_size or img.size[1] > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True, subsampling=2)
            compressed_bytes = buffer.getvalue()
            return base64.b64encode(compressed_bytes).decode('utf-8')
        except Exception:
            if hasattr(image_file, 'read'):
                image_file.seek(0)
                img_bytes = image_file.read()
            elif isinstance(image_file, bytes):
                img_bytes = image_file
            else:
                return None
            return base64.b64encode(img_bytes).decode('utf-8')

    def analyze_image_simple(self, image_file, question):
        try:
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code != 200:
                    return None, "未检测到Ollama服务"
                available_models = [model.get("name") for model in response.json().get("models", [])]
            except:
                return None, "无法连接Ollama服务"

            # 使用 moondream 作为视觉模型
            target_model = "moondream:latest"
            if target_model not in available_models:
                for model in available_models:
                    if "moondream" in model.lower() or "llava" in model.lower():
                        target_model = model
                        break
                else:
                    return None, f"未找到视觉模型。请安装: ollama pull moondream:latest"

            image_base64 = self.encode_image_to_base64(image_file, max_size=256, quality=45)
            if not image_base64:
                return None, "图片编码失败"

            # 使用英文提示（moondream 对英文响应更好）
            if question and question != "分析图片":
                simple_prompt = f"Describe this image: {question}"
            else:
                simple_prompt = "Describe this image in detail."

            api_url = f"{self.base_url}/api/generate"
            payload = {
                "model": target_model,
                "prompt": simple_prompt,
                "images": [image_base64],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 300}
            }

            response = requests.post(api_url, json=payload, timeout=90)

            if response.status_code == 200:
                result = response.json().get("response", "分析完成")
                if not result or len(result) < 5:
                    result = "图片分析完成。"

                # ========== 强制翻译成中文（不判断直接翻译） ==========
                try:
                    translate_payload = {
                        "model": "qwen2.5:0.5b",
                        "prompt": f"将以下英文翻译成中文，只输出中文：\n{result}",
                        "stream": False,
                        "options": {"temperature": 0.1, "num_predict": 500}
                    }
                    trans_response = requests.post(
                        f"{self.base_url}/api/generate",
                        json=translate_payload,
                        timeout=60
                    )
                    if trans_response.status_code == 200:
                        translated = trans_response.json().get("response", "")
                        if translated and len(translated) > 5:
                            result = translated
                except Exception as e:
                    print(f"翻译失败: {e}")
                # ========== 翻译结束 ==========

                return result, None
            return None, f"请求失败: {response.status_code}"

        except requests.Timeout:
            return None, "分析超时，请尝试上传更小的图片"
        except Exception as e:
            return None, f"分析失败: {str(e)}"
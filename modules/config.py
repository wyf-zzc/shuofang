"""
配置文件
"""
import streamlit as st

# ==================== DeepSeek配置 ====================
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_TEXT_MODEL = "deepseek-chat"
DEEPSEEK_VISION_MODEL = "deepseek-vl2"

# ==================== Ollama配置 ====================
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TEXT_MODEL = "qwen:7b"
LOCAL_VISION_MODEL = "moondream"

# ==================== 对话记忆配置 ====================
MAX_HISTORY_LENGTH = 20
MAX_CONTEXT_TOKENS = 4000

# ==================== 每日一句数据库 ====================
DAILY_QUOTES = [
    {"text": "学如逆水行舟，不进则退。", "author": "《增广贤文》", "category": "学习"},
    {"text": "不积跬步，无以至千里；不积小流，无以成江海。", "author": "荀子", "category": "坚持"},
    {"text": "知之者不如好之者，好之者不如乐之者。", "author": "孔子", "category": "学习态度"},
    {"text": "三人行，必有我师焉。", "author": "孔子", "category": "谦虚"},
    {"text": "业精于勤，荒于嬉；行成于思，毁于随。", "author": "韩愈", "category": "勤奋"},
    {"text": "书山有路勤为径，学海无涯苦作舟。", "author": "韩愈", "category": "勤奋"},
    {"text": "天行健，君子以自强不息。", "author": "《周易》", "category": "自强"},
    {"text": "千里之行，始于足下。", "author": "老子", "category": "行动"},
    {"text": "少壮不努力，老大徒伤悲。", "author": "《长歌行》", "category": "珍惜时光"},
    {"text": "非学无以广才，非志无以成学。", "author": "诸葛亮", "category": "志向"},
    {"text": "博学之，审问之，慎思之，明辨之，笃行之。", "author": "《中庸》", "category": "学习方法"},
    {"text": "学而不思则罔，思而不学则殆。", "author": "孔子", "category": "思考"},
    {"text": "温故而知新，可以为师矣。", "author": "孔子", "category": "复习"},
    {"text": "读书破万卷，下笔如有神。", "author": "杜甫", "category": "阅读"},
    {"text": "黑发不知勤学早，白首方悔读书迟。", "author": "颜真卿", "category": "珍惜时光"}
]
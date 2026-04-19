# -*- coding: utf-8 -*-
"""
朔方智域·多模态认知计算与全域知识检索校园智能引擎系统
主程序入口
"""
import os

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import streamlit as st
from PIL import Image
from datetime import datetime

# 导入模型模块
from modules.models.smart_model import SmartModelManager
from modules.models.network_detector import network_detector

# 导入服务模块
from modules.services.course_service import (
    query_course_by_weekday, query_today_course,
    query_course_by_time_slot
)
from modules.services.classroom_service import (
    query_classroom_by_time, query_current_room
)
from modules.services.canteen_service import (
    query_canteen_by_meal
)
from modules.services.activity_service import (
    query_activity_by_month, query_current_month_activity,
    query_upcoming_activities, smart_activity_query
)
from modules.services.exam_service import show_exam_dashboard

# 导入数据库模块
from modules.database.knowledge_base import show_knowledge_base_upload, KnowledgeBaseManager

# 导入视觉模块
from modules.vision.siliconflow_vision import SmartVisionAnalyzer

# 导入工具模块
from modules.utils.helpers import (
    show_daily_quote, get_weekday_cn, get_time_slot_by_hour,
    get_time_slot_cn, get_meal_by_hour
)
from modules.utils.intent import detect_intent

# 页面的配置
st.set_page_config(
    page_title="朔方智域·大模型认知计算与全域知识检索校园智能引擎系统",
    layout="wide"
)


# ==================== 初始化 ====================

@st.cache_resource
def init_model_manager():
    """初始化模型管理器"""
    return SmartModelManager()


model_manager = init_model_manager()


def init_session_state():
    """初始化 session state"""
    if "kb_manager" not in st.session_state:
        st.session_state.kb_manager = None
        st.session_state.kb_manager_available = False  # 云端环境禁用本地向量检索

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [{
            "role": "assistant",
            "content": "你好！我是朔方智域校园智能助手👋\n\n**✨ 智能双模式运行**\n• 有网时使用DeepSeek云端模型\n• 没网时使用Ollama本地模型\n• 自动切换，服务不中断\n• **支持对话记忆** - 我能记住我们聊过的内容！\n\n我可以帮你：\n• 查今日课程表\n• 找空教室\n• 推荐食堂美食\n• 查询校园活动\n• 智能语义检索\n• 分析图片内容\n• 解答学习问题"
        }]

    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None

    if "max_history" not in st.session_state:
        st.session_state.max_history = 10
    if "enable_memory" not in st.session_state:
        st.session_state.enable_memory = True
    if "current_provider" not in st.session_state:
        st.session_state.current_provider = None


init_session_state()


# ==================== 智能检索函数 ====================
def smart_search(query, category=None, top_k=5):
    """智能语义检索"""
    if not st.session_state.get("kb_manager_available", False):
        return "❌ 检索功能暂不可用，请检查知识库连接。"

    if not query or not query.strip():
        return "⚠️ 请输入检索内容。"

    kb_manager = st.session_state.kb_manager

    try:
        results = kb_manager.search(query, top_k=top_k, category=category)

        if not results:
            category_hint = f"（分类：{category}）" if category else ""
            return f"📭 未找到与「{query}」相关的内容{category_hint}。\n\n💡 建议：\n• 尝试使用更简短的关键词\n• 检查关键词拼写\n• 更换其他分类试试"

        filtered_results = [r for r in results if r.get('similarity', 0) >= 0.15]

        if not filtered_results:
            return f"📭 未找到高相关度的内容。\n\n💡 建议：\n• 使用更精确的关键词\n• 尝试其他分类"

        response = f"**🔍 检索结果（共{len(filtered_results)}条）**\n\n"

        for i, result in enumerate(filtered_results, 1):
            similarity = result.get('similarity', 0)
            score = similarity * 100
            title = result.get('title', '无标题')

            if score >= 70:
                icon = "🎯"
            elif score >= 50:
                icon = "📌"
            elif score >= 30:
                icon = "📄"
            else:
                icon = "🔖"

            response += f"{icon} **{i}. {title}** (相关度: {score:.1f}%)\n"

            content = result.get('content', '')
            if len(content) > 300:
                query_lower = query.lower()
                content_lower = content.lower()
                pos = content_lower.find(query_lower)
                if pos != -1:
                    start = max(0, pos - 80)
                    end = min(len(content), pos + 150)
                    content = "..." + content[start:end] + "..."
                    content = content.replace(query, f"**{query}**")
                    content = content.replace(query.lower(), f"**{query.lower()}**")
                else:
                    content = content[:300] + "..."

            response += f"{content}\n\n"

        response += "---\n"
        response += "💡 **检索小贴士**\n"
        response += "• 使用更具体的关键词可获得更精确的结果\n"
        response += "• 尝试切换分类筛选\n"
        response += "• 通过「知识库管理」可上传更多文档"

        return response

    except Exception as e:
        return f"❌ 检索失败: {str(e)}"


# ==================== 智能对话增强 ====================

def enhanced_smart_chat(prompt, history=None, is_vision=False, image_base64=None):
    """增强版智能对话"""
    if model_manager is None:
        return "❌ 模型服务未初始化，请检查配置。", "error"

    if not prompt or not prompt.strip():
        return "⚠️ 请输入问题内容。", "error"

    try:
        result, used_provider, status = model_manager.smart_chat(
            prompt, history, is_vision, image_base64
        )

        if status == "success" and result:
            return result, used_provider
        elif result:
            return result, "error"
        else:
            return "❌ 抱歉，我暂时无法回答这个问题。请稍后再试。", "error"
    except Exception as e:
        return f"❌ 对话服务异常: {str(e)}", "error"


# ==================== 主应用界面 ====================

st.title("🎓 朔方智域·大模型认知计算与全域知识检索校园智能引擎系统")
st.caption("你的校园生活学习智能助手 | 智能双模式（有网用DeepSeek🌐，没网用Ollama💻）| 支持对话记忆🧠 | 向量语义检索📚")

# ==================== 侧边栏 ====================

with st.sidebar:
    st.markdown("### 🔧 服务状态")
    services = model_manager.check_services()
    col1, col2 = st.columns(2)
    with col1:
        if services["deepseek"]:
            st.success("🌐 DeepSeek")
        else:
            st.error("🌐 DeepSeek")
    with col2:
        if services["ollama"]:
            st.success("💻 Ollama")
        else:
            st.error("💻 Ollama")

    network_status = network_detector.get_status_message()
    if "正常" in network_status:
        st.success(network_status)
    elif "受限" in network_status:
        st.warning(network_status)
    else:
        st.error(network_status)

    st.markdown("---")
    st.markdown("### ⚙️ 运行模式")
    mode_option = st.selectbox("选择运行模式", ["自动切换 (推荐)", "DeepSeek云端", "Ollama本地"], index=0)
    mode_map = {"自动切换 (推荐)": "auto", "DeepSeek云端": "deepseek", "Ollama本地": "ollama"}
    model_manager.set_mode(mode_map[mode_option])

    st.markdown("---")
    st.markdown("### 🧠 记忆设置")
    enable_memory = st.checkbox("启用对话记忆", value=st.session_state.enable_memory,
                                help="开启后AI会记住之前的对话内容")
    st.session_state.enable_memory = enable_memory

    if enable_memory:
        max_history = st.slider("记忆轮数", min_value=2, max_value=20, value=st.session_state.max_history,
                                help="记住最近多少轮对话")
        st.session_state.max_history = max_history

        if st.button("🗑️ 清空记忆", use_container_width=True, type="secondary"):
            st.session_state.chat_messages = [st.session_state.chat_messages[0]]
            st.success("✅ 对话记忆已清空")
            st.rerun()

        history_count = len([m for m in st.session_state.chat_messages
                             if
                             m["role"] != "assistant" or m["content"] != st.session_state.chat_messages[0]["content"]])
        st.caption(f"📊 当前记忆: {history_count} 条对话")

    st.markdown("---")
    st.markdown("### 📱 功能菜单")
    menu_options = [
        "💬 智能对话",
        "📅 考试倒计时",
        "📖 每日一句",
        "📚 知识库管理",
        "🔍 智能检索",
        "📚 课程查询",
        "🏫 教室查询",
        "🍜 食堂推荐",
        "🎉 活动查询"
    ]
    selected_menu = st.radio("选择功能", menu_options, index=0, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### 📊 使用统计")
    stats = model_manager.get_stats_summary()
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("🌐 DeepSeek", stats["deepseek_calls"])
    with col_stat2:
        st.metric("💻 Ollama", stats["ollama_calls"])

    # ========== 图片上传（只在智能对话时显示）==========
    if selected_menu == "💬 智能对话":
        st.markdown("---")
        st.markdown("##### 📷 上传图片分析")

        uploaded_file = st.file_uploader(
            label="选择图片文件",
            type=["jpg", "jpeg", "png", "gif", "bmp"],
            help="支持上传学习资料、题目、校园场景等图片进行分析",
            key="image_upload"
        )

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="已上传图片", use_column_width=True)
            st.session_state.uploaded_image = uploaded_file
            st.success("✅ 图片已上传")

# ==================== 主功能区路由 ====================

if selected_menu == "📅 考试倒计时":
    show_exam_dashboard(model_manager)

elif selected_menu == "📖 每日一句":
    st.title("📖 每日一句")
    st.caption("每日更新，激励你的学习之旅")
    show_daily_quote()

elif selected_menu == "📚 知识库管理":
    show_knowledge_base_upload()

elif selected_menu == "🔍 智能检索":
    st.title("🔍 智能检索")
    st.markdown("---")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input(
            "输入检索内容",
            placeholder="例如：奖学金申请、周一课程、食堂推荐...",
            key="search_input"
        )
    with col2:
        search_category = st.selectbox(
            "分类筛选",
            ["全部", "学习资源", "校园服务", "规章制度", "活动通知"],
            key="search_category"
        )
    with col3:
        top_k = st.selectbox("结果数量", [3, 5, 10, 15], index=1, key="search_topk")

    if st.button("🚀 开始检索", type="primary", use_container_width=True):
        if search_query:
            with st.spinner("正在语义检索中..."):
                result = smart_search(
                    search_query,
                    None if search_category == "全部" else search_category,
                    top_k=top_k
                )
                st.markdown(result)
        else:
            st.warning("请输入检索内容")

    st.markdown("---")
    st.info("💡 提示：支持语义检索，输入关键词即可找到相关知识库内容")

elif selected_menu == "📚 课程查询":
    st.title("📚 课程查询")
    st.markdown("---")

    query_type = st.radio("查询方式", ["按星期查询", "按时间段查询"], horizontal=True)

    if query_type == "按星期查询":
        col1, col2 = st.columns([1, 2])
        with col1:
            weekday = st.selectbox("选择星期", ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
                                   index=["周一", "周二", "周三", "周四", "周五", "周六", "周日"].index(
                                       get_weekday_cn()))
        if st.button("🔍 查询课程", type="primary"):
            with st.spinner("正在查询..."):
                result = query_course_by_weekday(weekday)
                st.markdown(result)
    else:
        col1, col2 = st.columns(2)
        with col1:
            weekday = st.selectbox("选择星期", ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
                                   index=["周一", "周二", "周三", "周四", "周五", "周六", "周日"].index(
                                       get_weekday_cn()))
        with col2:
            time_slot = st.selectbox("选择时间段", ["早上", "上午", "下午", "晚上"],
                                     index=["早上", "上午", "下午", "晚上"].index(get_time_slot_cn()))
        if st.button("🔍 查询课程", type="primary"):
            with st.spinner("正在查询..."):
                result = query_course_by_time_slot(time_slot, weekday)
                st.markdown(result)

    st.markdown("---")
    st.info(f"💡 当前时间：{get_weekday_cn()} {get_time_slot_cn()}，可查询今日课程")

elif selected_menu == "🏫 教室查询":
    st.title("🏫 教室查询")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        weekday = st.selectbox("选择星期", ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
                               index=["周一", "周二", "周三", "周四", "周五", "周六", "周日"].index(get_weekday_cn()))
    with col2:
        time_slot = st.selectbox("选择时间段", ["早上", "上午", "中午", "下午", "晚上"],
                                 index=["早上", "上午", "中午", "下午", "晚上"].index(get_time_slot_cn()))

    if st.button("🔍 查询空教室", type="primary"):
        with st.spinner("正在查询..."):
            result = query_classroom_by_time(weekday, time_slot)
            st.markdown(result)

    st.markdown("---")
    st.info(f"💡 当前时间：{get_weekday_cn()} {get_time_slot_cn()}，可查询该时段空教室")

elif selected_menu == "🍜 食堂推荐":
    st.title("🍜 食堂推荐")
    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        meal = st.selectbox("选择餐段", ["早餐", "午餐", "下午茶", "晚餐"],
                            index=["早餐", "午餐", "下午茶", "晚餐"].index(get_meal_by_hour()))
    with col2:
        limit = st.slider("推荐数量", 3, 10, 5)

    if st.button("🔍 查询推荐", type="primary"):
        with st.spinner("正在查询..."):
            result = query_canteen_by_meal(meal, limit=limit)
            st.markdown(result)

    st.markdown("---")
    st.info(f"💡 当前餐段：{get_meal_by_hour()}，系统已自动推荐")

elif selected_menu == "🎉 活动查询":
    st.title("🎉 活动查询")
    st.markdown("---")

    now = datetime.now()
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.selectbox("年份", [now.year, now.year + 1], index=0)
    with col2:
        month = st.selectbox("月份", list(range(1, 13)), index=now.month - 1)
    with col3:
        days = st.selectbox("近期范围", [7, 14, 30, 60], index=2)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 查询活动", type="primary", use_container_width=True):
            with st.spinner("正在查询..."):
                result = query_activity_by_month(year, month)
                st.markdown(result)
    with col2:
        if st.button(f"📅 未来{days}天活动", type="secondary", use_container_width=True):
            with st.spinner("正在查询..."):
                result = query_upcoming_activities(days)
                st.markdown(result)

    st.markdown("---")
    st.info("💡 提示：活动时间和地点可能调整，请以官方通知为准")

else:  # 💬 智能对话
    st.title("💬 智能对话")

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.get("current_provider"):
        provider_icon = "🌐" if st.session_state.current_provider == "deepseek" else "💻"
        provider_name = "DeepSeek云端" if st.session_state.current_provider == "deepseek" else "Ollama本地"
        st.caption(f"{provider_icon} 当前使用：{provider_name}")

    if st.session_state.uploaded_image:
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🗑️ 清除图片", type="secondary"):
                st.session_state.uploaded_image = None
                st.rerun()

    st.markdown("---")

    with st.expander("💡 建议问题"):
        st.markdown("""
        - 今天有什么课？
        - 现在哪个教室空着？
        - 食堂有什么好吃的？
        - 最近有什么活动？
        - 帮我规划复习计划
        """)

    user_input = st.chat_input("输入你的问题...")

    if user_input:
        current_input = user_input

        with st.chat_message("user"):
            st.markdown(current_input)
            if st.session_state.uploaded_image:
                st.image(Image.open(st.session_state.uploaded_image), width=150)

        st.session_state.chat_messages.append({"role": "user", "content": current_input})

        if st.session_state.enable_memory and len(
                st.session_state.chat_messages) > st.session_state.max_history * 2 + 1:
            welcome_msg = st.session_state.chat_messages[0]
            recent_msgs = st.session_state.chat_messages[-(st.session_state.max_history * 2):]
            st.session_state.chat_messages = [welcome_msg] + recent_msgs

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                intent_result = detect_intent(current_input)
                intent = intent_result.get("intent", "unknown")
                time_slot = intent_result.get("time", "")
                question = intent_result.get("question", current_input)

                if intent == "image_help":
                    if st.session_state.uploaded_image:
                        analyzer = SmartVisionAnalyzer()
                        response, used_model = analyzer.analyze_image_smart(st.session_state.uploaded_image, question)
                        if used_model == "qwen":
                            st.info("🌐 使用硅基流动 Qwen3-VL 云端视觉模型")
                        elif used_model == "ollama":
                            st.info("💻 使用Ollama本地视觉模型")
                        else:
                            st.info("💻 使用本地视觉模型")
                    else:
                        response = "请先上传图片。点击侧边栏的📷按钮可以上传图片。"

                elif intent == "query_room":
                    response = query_classroom_by_time(get_weekday_cn(), time_slot if time_slot else get_time_slot_cn())

                elif intent == "query_course":
                    if time_slot:
                        response = query_course_by_time_slot(time_slot, get_weekday_cn())
                    else:
                        response = query_today_course()

                elif intent == "query_canteen":
                    response = query_canteen_by_meal(get_meal_by_hour())

                elif intent == "query_activity":
                    response = query_current_month_activity()

                elif intent == "smart_search":
                    response = smart_search(question, top_k=5)

                else:
                    kb_context = ""
                    if st.session_state.get("kb_manager_available", False):
                        try:
                            results = st.session_state.kb_manager.search(question, top_k=3)
                            if results:
                                kb_context = "【参考资料】\n"
                                for r in results:
                                    if r.get('similarity', 0) >= 0.3:
                                        content = r.get('content', '')
                                        if len(content) > 500:
                                            content = content[:500] + "..."
                                        kb_context += f"- {content}\n\n"
                        except Exception as e:
                            st.warning(f"知识库检索失败: {e}")

                    if kb_context and kb_context != "【参考资料】\n":
                        question = f"{kb_context}\n\n【用户问题】\n{question}\n\n请基于以上参考资料回答用户问题。如果参考资料中没有相关信息，请如实告知用户。"

                    history = None
                    if st.session_state.enable_memory:
                        history = [m for m in st.session_state.chat_messages[:-1]
                                   if m["role"] != "assistant" or m["content"] != st.session_state.chat_messages[0][
                                       "content"]]

                    response, used_provider = enhanced_smart_chat(question, history)

                    if used_provider == "deepseek":
                        st.caption("🌐 使用DeepSeek云端模型")
                        st.session_state.current_provider = "deepseek"
                    elif used_provider == "ollama":
                        st.caption("💻 使用Ollama本地模型")
                        st.session_state.current_provider = "ollama"
                    else:
                        st.caption("⚠️ 使用本地模板")

                st.markdown(response)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})

        st.rerun()

# ==================== 底部信息 ====================

st.markdown("---")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
stats = model_manager.get_stats_summary()
mode_text = {"auto": "自动切换", "deepseek": "DeepSeek云端模式", "ollama": "Ollama本地模式"}.get(model_manager.mode,
                                                                                                 "自动切换")

kb_stats = st.session_state.kb_manager.get_stats() if st.session_state.kb_manager_available else {"total": 0}

st.markdown(f"""
<div style='text-align: center; color: #666; font-size: 0.8em; padding: 10px; background: #f8f9fa; border-radius: 5px;'>
🎓 <b>朔方智域·多模态认知计算与全域知识检索校园智能引擎系统</b> v10.0 | 
🤖 <b>智能双模式 · 有网用DeepSeek🌐 · 没网用Ollama💻</b> | 
🧠 <b>对话记忆</b> | 
📚 <b>向量语义检索</b> ({kb_stats['total']}个向量) |
📊 调用统计: 云端:{stats['deepseek_calls']}次 | 本地:{stats['ollama_calls']}次 | 
⏰ 运行时间：{current_time} | 
🎯 当前模式：{mode_text}
</div>
""", unsafe_allow_html=True)

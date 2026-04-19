"""
教室查询服务 - 按星期和时间段查询空教室
"""
import streamlit as st
import re
from datetime import datetime
from modules.utils.helpers import get_weekday_cn, get_time_slot_cn


def get_time_range_by_slot(time_slot):
    """根据时间段获取具体时间范围"""
    time_map = {
        "早上": "8:00-9:40",
        "上午": "10:00-11:40",
        "中午": "12:00-13:30",
        "下午": "14:00-15:40",
        "晚上": "16:00-17:40"
    }
    return time_map.get(time_slot, "时间待定")


def get_time_slot_cn_from_hour():
    """根据当前小时获取时间段（中）"""
    hour = datetime.now().hour
    if 5 <= hour < 10:
        return "早上"
    elif 10 <= hour < 14:
        return "上午"
    elif 14 <= hour < 17:
        return "下午"
    else:
        return "晚上"


def extract_rooms_from_line(line):
    """从一行文本中提取教室编号"""
    rooms = []

    # 教室模式：A-101, 明学楼101, 实验楼301 等
    room_patterns = [
        r'(明学楼\d{3})',
        r'(实验楼\d{3})',
        r'(物理楼\d{3})',
        r'(图书馆自习室)',
        r'(体育馆)',
        r'([A-Z]-\d{3})',
        r'([A-Z]\d{3})'
    ]

    # 直接匹配所有教室
    for pattern in room_patterns:
        matches = re.findall(pattern, line)
        for room in matches:
            if room not in rooms:
                rooms.append(room)

    # 要是没有匹配到，尝试按分隔符拆分
    if not rooms:
        # 支持中文逗号、英文逗号、空格、顿号
        separators = r'[，,、\s]+'
        parts = re.split(separators, line)
        for part in parts:
            part = part.strip()
            for pattern in room_patterns:
                room_match = re.match(pattern, part)
                if room_match:
                    room = room_match.group(1)
                    if room not in rooms:
                        rooms.append(room)
                    break

    return rooms


def parse_rooms_from_content(content, target_weekday, target_time_slot=None):
    """从知识库内容中精确解析空教室列表"""
    rooms = []
    lines = content.split('\n')

    # 时间段关键词
    time_keywords = {
        "早上": ["早上", "8:00", "8点"],
        "上午": ["上午", "10:00", "10点"],
        "中午": ["中午", "12:00", "12点"],
        "下午": ["下午", "14:00", "2点"],
        "晚上": ["晚上", "16:00", "4点"]
    }

    target_time_range = get_time_range_by_slot(target_time_slot) if target_time_slot else None
    in_target_section = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查是否是目标星期和时间段的标题行
        if target_weekday in line:
            time_matched = False

            if target_time_slot:
                # 检查行中是否包含目标时间段关键词
                for kw in time_keywords.get(target_time_slot, []):
                    if kw in line:
                        time_matched = True
                        break

                # 也检查括号内的时间范围
                time_range_match = re.search(r'（(\d+:\d+-\d+:\d+)）', line)
                if time_range_match and target_time_range:
                    if time_range_match.group(1) == target_time_range:
                        time_matched = True
            else:
                time_matched = True

            if time_matched:
                in_target_section = True
                # 提取当前行的教室
                rooms_in_line = extract_rooms_from_line(line)
                for room in rooms_in_line:
                    if room not in rooms:
                        rooms.append(room)
            continue

        # 如果在目标区域内，继续提取教室
        if in_target_section:
            # 检查是否遇到新的星期
            if re.match(r'^[周一二三四五六日]', line):
                break

            # 提取教室
            rooms_in_line = extract_rooms_from_line(line)
            for room in rooms_in_line:
                if room not in rooms:
                    rooms.append(room)

    return rooms


def query_classroom_by_time(weekday=None, time_slot=None):
    """查询指定星期和时间段的空教室"""
    if not st.session_state.get("kb_manager_available", False):
        return "教室查询功能暂不可用，请检查知识库。"

    kb_manager = st.session_state.kb_manager

    if weekday is None:
        weekday = get_weekday_cn()

    if time_slot is None:
        time_slot = get_time_slot_cn()

    # 标准化输入
    weekday_map = {
        "周一": "周一", "星期一": "周一",
        "周二": "周二", "星期二": "周二",
        "周三": "周三", "星期三": "周三",
        "周四": "周四", "星期四": "周四",
        "周五": "周五", "星期五": "周五",
        "周六": "周六", "星期六": "周六",
        "周日": "周日", "星期日": "周日", "星期天": "周日"
    }
    weekday = weekday_map.get(weekday, weekday)

    time_slot_map = {
        "早上": "早上", "上午": "上午", "中午": "中午", "下午": "下午", "晚上": "晚上"
    }
    time_slot = time_slot_map.get(time_slot, time_slot)

    # 搜索知识库
    search_queries = [
        f"{weekday}{time_slot}空教室",
        f"{weekday}空教室",
        f"{time_slot}空教室",
        "空教室"
    ]

    all_results = []
    for query in search_queries:
        results = kb_manager.search(query, top_k=5)
        if results:
            all_results.extend(results)

    if not all_results:
        time_range = get_time_range_by_slot(time_slot)
        return f"🏫 {weekday}{time_slot}（{time_range}）的空教室：\n\n暂无该时段空教室信息。\n\n💡 请通过「知识库管理」上传教室安排信息。"

    # 解析空教室
    all_rooms = []
    for result in all_results:
        if result.get('similarity', 0) > 0.25:
            content = result.get('content', '')
            rooms = parse_rooms_from_content(content, weekday, time_slot)
            all_rooms.extend(rooms)

    # 去重
    unique_rooms = []
    for room in all_rooms:
        if room not in unique_rooms:
            unique_rooms.append(room)
    unique_rooms.sort()

    time_range = get_time_range_by_slot(time_slot)

    # 构建返回内容
    if unique_rooms:
        response = f"🏫 {weekday}{time_slot}（{time_range}）的空教室：\n\n"
        response += f"📌 共找到 {len(unique_rooms)} 间空教室：\n\n"

        # 分组显示
        mingxue_rooms = [r for r in unique_rooms if "明学楼" in r]
        shiyan_rooms = [r for r in unique_rooms if "实验楼" in r]
        other_rooms = [r for r in unique_rooms if "明学楼" not in r and "实验楼" not in r]

        if mingxue_rooms:
            response += "🏛️ 明学楼：\n"
            for i in range(0, len(mingxue_rooms), 5):
                response += "   " + "、".join(mingxue_rooms[i:i + 5]) + "\n"
            response += "\n"

        if shiyan_rooms:
            response += "🔬 实验楼：\n"
            for i in range(0, len(shiyan_rooms), 5):
                response += "   " + "、".join(shiyan_rooms[i:i + 5]) + "\n"
            response += "\n"

        if other_rooms:
            response += "📚 其他：\n"
            response += "   " + "、".join(other_rooms) + "\n\n"

        response += "💡 温馨提示：\n"
        response += "• 空教室可能会有临时调课，以实际为准\n"
        response += "• 使用空教室请保持安静和整洁\n"

        return response
    else:
        # 尝试返回原始内容
        for result in all_results[:2]:
            content = result.get('content', '')
            if weekday in content or time_slot in content:
                if len(content) > 400:
                    content = content[:400] + "..."
                return f"🏫 {weekday}{time_slot}（{time_range}）的空教室：\n\n{content}\n\n💡 以上信息仅供参考。"

        return f"🏫 {weekday}{time_slot}（{time_range}）的空教室：\n\n暂无该时段空教室信息。"


def query_current_room():
    """查询当前时段的空教室"""
    weekday = get_weekday_cn()
    time_slot = get_time_slot_cn_from_hour()
    return query_classroom_by_time(weekday, time_slot)


def query_classroom_by_weekday(weekday=None):
    """查询指定星期全天的空教室"""
    if not st.session_state.get("kb_manager_available", False):
        return "教室查询功能暂不可用，请检查知识库。"

    kb_manager = st.session_state.kb_manager

    if weekday is None:
        weekday = get_weekday_cn()

    weekday_map = {
        "周一": "周一", "星期二": "周二", "周三": "周三",
        "周四": "周四", "周五": "周五", "周六": "周六", "周日": "周日"
    }
    weekday = weekday_map.get(weekday, weekday)

    results = kb_manager.search(f"{weekday}空教室", top_k=5)

    if not results:
        return f"🏫 {weekday}全天空教室：\n\n暂无信息。"

    response = f"🏫 {weekday}全天空教室：\n\n"

    time_slots = ["早上", "上午", "中午", "下午", "晚上"]
    time_range_map = {
        "早上": "8:00-9:40",
        "上午": "10:00-11:40",
        "中午": "12:00-13:30",
        "下午": "14:00-15:40",
        "晚上": "16:00-17:40"
    }

    for result in results:
        if result.get('similarity', 0) > 0.25:
            content = result.get('content', '')
            for slot in time_slots:
                rooms = parse_rooms_from_content(content, weekday, slot)
                if rooms:
                    unique_rooms = []
                    for r in rooms:
                        if r not in unique_rooms:
                            unique_rooms.append(r)
                    response += f"📌 {slot}（{time_range_map.get(slot, '')}）：\n"
                    response += f"   {', '.join(unique_rooms[:8])}\n"
                    if len(unique_rooms) > 8:
                        response += f"   等{len(unique_rooms)}间教室\n"
                    response += "\n"
            break

    if "全天空教室" in response and len(response) < 50:
        response += "暂无详细空教室信息。\n\n💡 周末教室基本空闲，建议使用图书馆自习室。"

    return response


def query_classroom_by_building(building=None, weekday=None, time_slot=None):
    """按教学楼查询空教室"""
    if not st.session_state.get("kb_manager_available", False):
        return "教室查询功能暂不可用，请检查知识库。"

    kb_manager = st.session_state.kb_manager

    if weekday is None:
        weekday = get_weekday_cn()

    if time_slot is None:
        time_slot = get_time_slot_cn_from_hour()

    if building is None:
        building = "明学楼"

    results = kb_manager.search(f"{weekday}{time_slot}空教室", top_k=3)

    if not results:
        return f"🏫 {weekday}{time_slot} {building}的空教室：\n\n暂无信息。"

    all_rooms = []
    for result in results:
        if result.get('similarity', 0) > 0.25:
            content = result.get('content', '')
            rooms = parse_rooms_from_content(content, weekday, time_slot)
            building_rooms = [r for r in rooms if building in r]
            all_rooms.extend(building_rooms)

    unique_rooms = []
    for r in all_rooms:
        if r not in unique_rooms:
            unique_rooms.append(r)
    unique_rooms.sort()

    time_range = get_time_range_by_slot(time_slot)

    if unique_rooms:
        return f"🏫 {weekday}{time_slot}（{time_range}）{building}的空教室：\n\n📌 {', '.join(unique_rooms)}\n\n💡 共{len(unique_rooms)}间教室可用。"
    else:
        return f"🏫 {weekday}{time_slot}（{time_range}）{building}的空教室：\n\n暂无该教学楼空教室信息。"


def smart_classroom_query(user_input):
    """智能教室查询"""
    user_input_lower = user_input.lower()

    # 判断教学楼
    building = None
    if "明学楼" in user_input_lower:
        building = "明学楼"
    elif "实验楼" in user_input_lower:
        building = "实验楼"
    elif "图书馆" in user_input_lower:
        building = "图书馆自习室"

    # 判断星期
    weekday = None
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    for wd in weekdays:
        if wd in user_input_lower:
            weekday = wd
            break

    # 判断时间段
    time_slot = None
    if "早上" in user_input_lower:
        time_slot = "早上"
    elif "上午" in user_input_lower:
        time_slot = "上午"
    elif "中午" in user_input_lower:
        time_slot = "中午"
    elif "下午" in user_input_lower:
        time_slot = "下午"
    elif "晚上" in user_input_lower:
        time_slot = "晚上"

    # 根据条件查询
    if building and weekday and time_slot:
        return query_classroom_by_building(building, weekday, time_slot)
    elif building and weekday:
        return query_classroom_by_building(building, weekday)
    elif building:
        return query_classroom_by_building(building)
    elif weekday and time_slot:
        return query_classroom_by_time(weekday, time_slot)
    elif weekday:
        return query_classroom_by_weekday(weekday)
    else:
        return query_current_room()


# ==================== 快捷查询函数 ====================

def query_morning_room(weekday=None):
    """查询早上空教室"""
    if weekday is None:
        weekday = get_weekday_cn()
    return query_classroom_by_time(weekday, "早上")


def query_am_room(weekday=None):
    """查询上午空教室"""
    if weekday is None:
        weekday = get_weekday_cn()
    return query_classroom_by_time(weekday, "上午")


def query_pm_room(weekday=None):
    """查询下午空教室"""
    if weekday is None:
        weekday = get_weekday_cn()
    return query_classroom_by_time(weekday, "下午")


def query_evening_room(weekday=None):
    """查询晚上空教室"""
    if weekday is None:
        weekday = get_weekday_cn()
    return query_classroom_by_time(weekday, "晚上")


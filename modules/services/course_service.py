"""
课程查询服务 - 按星期和时间段查询课程，
"""
import streamlit as st
import re
from datetime import datetime

# ==================== 备用的课程数据 ====================
FALLBACK_COURSES = {
    "周一": [
        {"time_slot": "早上", "time_range": "8:00-9:40", "name": "高等数学", "room": "明学楼101", "teacher": "张明老师",
         "credit": "4"},
        {"time_slot": "上午", "time_range": "10:00-11:40", "name": "大学英语", "room": "明学楼205",
         "teacher": "李华老师", "credit": "3"},
        {"time_slot": "下午", "time_range": "14:00-15:40", "name": "C语言程序设计", "room": "实验楼301",
         "teacher": "王磊老师", "credit": "3"},
    ],
    "周二": [
        {"time_slot": "早上", "time_range": "8:00-9:40", "name": "线性代数", "room": "明学楼102", "teacher": "陈静老师",
         "credit": "3"},
        {"time_slot": "上午", "time_range": "10:00-11:40", "name": "大学物理", "room": "明学楼301",
         "teacher": "杨光老师", "credit": "3"},
        {"time_slot": "下午", "time_range": "14:00-15:40", "name": "数据结构", "room": "实验楼302",
         "teacher": "王磊老师", "credit": "4"},
    ],
    "周三": [
        {"time_slot": "早上", "time_range": "8:00-9:40", "name": "概率论与数理统计", "room": "明学楼104",
         "teacher": "张明老师", "credit": "3"},
        {"time_slot": "上午", "time_range": "10:00-11:40", "name": "工程制图", "room": "明学楼202",
         "teacher": "李建国老师", "credit": "3"},
    ],
    "周四": [
        {"time_slot": "早上", "time_range": "8:00-9:40", "name": "离散数学", "room": "明学楼105", "teacher": "陈静老师",
         "credit": "3"},
        {"time_slot": "上午", "time_range": "10:00-11:40", "name": "计算机组成原理", "room": "明学楼203",
         "teacher": "王磊老师", "credit": "4"},
    ],
    "周五": [
        {"time_slot": "早上", "time_range": "8:00-9:40", "name": "操作系统", "room": "明学楼106", "teacher": "王磊老师",
         "credit": "4"},
        {"time_slot": "上午", "time_range": "10:00-11:40", "name": "计算机网络", "room": "明学楼204",
         "teacher": "张伟老师", "credit": "3"},
    ],
    "周六": [],
    "周日": [],
}

TIME_SLOT_DISPLAY = {
    "早上": "早上（8:00-9:40）",
    "上午": "上午（10:00-11:40）",
    "下午": "下午（14:00-15:40）",
    "晚上": "晚上（16:00-17:40）"
}

TIME_RANGE_MAP = {
    "早上": "8:00-9:40",
    "上午": "10:00-11:40",
    "下午": "14:00-15:40",
    "晚上": "16:00-17:40"
}

# 时间段关键词映射
SLOT_KEYWORDS = {
    "早上": ["早上", "8:00", "8点"],
    "上午": ["上午", "10:00", "10点"],
    "下午": ["下午", "14:00", "2点"],
    "晚上": ["晚上", "16:00", "4点"]
}


# ==================== 辅助函数 ====================

def get_weekday_cn():
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[datetime.now().weekday()]


def get_time_slot_cn():
    hour = datetime.now().hour
    if 5 <= hour < 10:
        return "早上"
    elif 10 <= hour < 14:
        return "上午"
    elif 14 <= hour < 17:
        return "下午"
    else:
        return "晚上"


def parse_course_from_content(content, target_weekday, target_time_slot=None):

    courses = []
    lines = content.split('\n')

    current_weekday = None
    current_time_slot = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过标题行（如【课程表信息】）
        if line.startswith('【') and line.endswith('】'):
            continue

        # 检测星期标题（如"周一课程："、"周一："、"【周一课程】"）
        weekday_match = re.match(r'^[\s【]*([周一|周二|周三|周四|周五|周六|周日]+)(?:课程)?[：:】\s]*', line)
        if weekday_match:
            current_weekday = weekday_match.group(1)
            current_time_slot = None
            continue

        # 如果还没有进入目标星期，跳过
        if current_weekday != target_weekday:
            continue

        # 检测时间段标题（如"上午："、"早上："）
        slot_match = re.match(r'^[\s]*([上午|早上|下午|晚上]+)[：:]\s*', line)
        if slot_match:
            slot_name = slot_match.group(1)
            for slot, keywords in SLOT_KEYWORDS.items():
                if slot_name in keywords or slot_name == slot:
                    current_time_slot = slot
                    break
            continue

        # 匹配课程行：数字. 时间 课程名 @ 地点 老师 学分
        # 格式：1. 8:00-9:40 高等数学 @ 明学楼101 张明老师 4学分
        course_match = re.match(
            r'^(\d+)\.\s*(\d+:\d+-\d+:\d+)\s+([^@]+?)(?:\s+@\s+([^\s]+))?\s*(.*?)$',
            line
        )
        if course_match:
            num, time_range, name, room, rest = course_match.groups()
            name = name.strip()

            # 提取老师和学分
            teacher = ""
            credit = ""
            if rest:
                # 提取老师（以"老师"结尾）
                teacher_match = re.search(r'([^0-9]+?老师)', rest)
                if teacher_match:
                    teacher = teacher_match.group(1).strip()
                # 提取学分
                credit_match = re.search(r'(\d+)学分', rest)
                if credit_match:
                    credit = credit_match.group(1)

            # 如果没有提取到老师，尝试从整行提取
            if not teacher:
                teacher_match2 = re.search(r'([^0-9]{2,8}?老师)', line)
                if teacher_match2:
                    teacher = teacher_match2.group(1).strip()

            # 确定时间段
            time_slot = current_time_slot
            if not time_slot:
                for slot, keywords in SLOT_KEYWORDS.items():
                    for kw in keywords:
                        if kw in time_range or kw in line:
                            time_slot = slot
                            break
                    if time_slot:
                        break

            # 如果指定了目标时间段，只添加匹配的
            if target_time_slot and time_slot != target_time_slot:
                continue

            courses.append({
                "name": name,
                "time_slot": time_slot or "未知",
                "time_range": time_range,
                "room": room if room else "待定",
                "teacher": teacher if teacher else "待定",
                "credit": credit
            })
            continue

        # 匹配简化格式：- 课程名 时间 地点 老师
        simple_match = re.match(r'^[-•*]\s*(.+?)\s+(\d+:\d+-\d+:\d+)(?:\s+@\s+(.+?))?\s*(.*?)$', line)
        if simple_match:
            name, time_range, room, rest = simple_match.groups()
            name = name.strip()

            teacher = ""
            credit = ""
            if rest:
                teacher_match = re.search(r'([^0-9]+?老师)', rest)
                if teacher_match:
                    teacher = teacher_match.group(1).strip()
                credit_match = re.search(r'(\d+)学分', rest)
                if credit_match:
                    credit = credit_match.group(1)

            time_slot = current_time_slot
            if not time_slot:
                for slot, keywords in SLOT_KEYWORDS.items():
                    for kw in keywords:
                        if kw in time_range:
                            time_slot = slot
                            break
                    if time_slot:
                        break

            if target_time_slot and time_slot != target_time_slot:
                continue

            courses.append({
                "name": name,
                "time_slot": time_slot or "未知",
                "time_range": time_range,
                "room": room if room else "待定",
                "teacher": teacher if teacher else "待定",
                "credit": credit
            })

    return courses


def get_fallback_courses(weekday, time_slot=None):
    """获取备用死数据课程"""
    courses = FALLBACK_COURSES.get(weekday, [])
    if time_slot:
        courses = [c for c in courses if c.get("time_slot") == time_slot]
    return courses


def format_course_response(courses, weekday, time_slot=None, is_fallback=False):
    """格式化课程查询结果"""
    if not courses:
        if time_slot:
            time_range = TIME_RANGE_MAP.get(time_slot, "")
            return f"📚 {weekday}{time_slot}（{time_range}）的课程：\n\n暂无该时段课程安排。"
        else:
            return f"📚 {weekday}的课程：\n\n暂无课程信息。\n\n💡 请通过「知识库管理」上传课程表信息。"

    source_tag = "（参考数据）" if is_fallback else ""

    if time_slot:
        time_range = TIME_RANGE_MAP.get(time_slot, "")
        response = f"📚 {weekday}{time_slot}（{time_range}）的课程{source_tag}：\n\n"
        for course in courses:
            response += format_single_course(course)
    else:
        response = f"📚 {weekday}全天课程{source_tag}：\n\n"
        response += f"📅 日期：{datetime.now().strftime('%Y年%m月%d日')}\n\n"

        courses_by_slot = {"早上": [], "上午": [], "下午": [], "晚上": []}
        for course in courses:
            slot = course.get("time_slot", "未知")
            if slot in courses_by_slot:
                courses_by_slot[slot].append(course)

        for slot, slot_courses in courses_by_slot.items():
            if slot_courses:
                response += f"{TIME_SLOT_DISPLAY.get(slot, slot)}\n"
                for course in slot_courses:
                    response += format_single_course(course)
                response += "\n"

    if is_fallback:
        response += "\n💡 提示：知识库未连接，以上为参考数据。可通过「知识库管理」上传更准确的课程信息。"

    return response


def format_single_course(course):
    """格式化单门课程信息"""
    result = f"   📖 {course['name']}\n"
    if course.get('time_range'):
        result += f"       时间：{course['time_range']}\n"
    if course.get('room') and course['room'] != "待定":
        result += f"       地点：{course['room']}\n"
    if course.get('teacher') and course['teacher'] != "待定":
        result += f"       教师：{course['teacher']}\n"
    if course.get('credit'):
        result += f"       学分：{course['credit']}学分\n"
    result += "\n"
    return result


# ==================== 主查询函数 ====================

def query_course_by_weekday(weekday=None):
    """查询指定星期几的全部课程"""
    if weekday is None:
        weekday = get_weekday_cn()

    kb_available = st.session_state.get("kb_manager_available", False)

    if kb_available:
        kb_manager = st.session_state.kb_manager
        results = kb_manager.search(f"{weekday} 课程", top_k=5)

        if results:
            all_courses = []
            for result in results:
                if result.get('similarity', 0) > 0.25:
                    content = result.get('content', '')
                    courses = parse_course_from_content(content, weekday)
                    all_courses.extend(courses)

            if all_courses:
                # 按时间段排序
                slot_order = {"早上": 0, "上午": 1, "下午": 2, "晚上": 3}
                all_courses.sort(key=lambda x: slot_order.get(x.get('time_slot', ''), 4))
                return format_course_response(all_courses, weekday, is_fallback=False)

    fallback_courses = get_fallback_courses(weekday)
    return format_course_response(fallback_courses, weekday, is_fallback=True)


def query_course_by_time_slot(time_slot=None, weekday=None):
    """按时间段查询课程"""
    if time_slot is None:
        time_slot = get_time_slot_cn()
    if weekday is None:
        weekday = get_weekday_cn()

    kb_available = st.session_state.get("kb_manager_available", False)

    if kb_available:
        kb_manager = st.session_state.kb_manager
        results = kb_manager.search(f"{weekday} {time_slot} 课程", top_k=5)

        if results:
            all_courses = []
            for result in results:
                if result.get('similarity', 0) > 0.25:
                    content = result.get('content', '')
                    courses = parse_course_from_content(content, weekday, time_slot)
                    all_courses.extend(courses)

            if all_courses:
                return format_course_response(all_courses, weekday, time_slot, is_fallback=False)

    fallback_courses = get_fallback_courses(weekday, time_slot)
    return format_course_response(fallback_courses, weekday, time_slot, is_fallback=True)


def query_today_course():
    return query_course_by_weekday(get_weekday_cn())


def query_current_course():
    return query_course_by_time_slot(get_time_slot_cn(), get_weekday_cn())


def query_monday():
    return query_course_by_weekday("周一")


def query_tuesday():
    return query_course_by_weekday("周二")


def query_wednesday():
    return query_course_by_weekday("周三")


def query_thursday():
    return query_course_by_weekday("周四")


def query_friday():
    return query_course_by_weekday("周五")


def smart_course_query(user_input):
    """智能课程查询"""
    user_input_lower = user_input.lower()

    if any(word in user_input_lower for word in ["今天", "今日"]):
        if "上午" in user_input_lower:
            return query_course_by_time_slot("上午")
        elif "下午" in user_input_lower:
            return query_course_by_time_slot("下午")
        elif "晚上" in user_input_lower:
            return query_course_by_time_slot("晚上")
        else:
            return query_today_course()

    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    for wd in weekdays:
        if wd in user_input:
            if "上午" in user_input_lower:
                return query_course_by_time_slot("上午", wd)
            elif "下午" in user_input_lower:
                return query_course_by_time_slot("下午", wd)
            else:
                return query_course_by_weekday(wd)

    return query_today_course()


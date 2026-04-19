# -*- coding: utf-8 -*-
"""
活动查询服务 - 查询校园活动，自动过滤非活动内容，带死数据备用
"""
import streamlit as st
import re
from datetime import datetime, timedelta

# ==================== 关键词配置 ====================

ACTIVITY_KEYWORDS = [
    "讲座", "活动", "比赛", "大赛", "分享会", "双选会", "招聘",
    "志愿者", "观影", "影院", "摄影", "十佳歌手", "篮球联赛",
    "考研经验", "四六级", "备考", "工作坊", "双创", "数学建模",
    "奖学金", "诗会", "读书日", "劳动节", "校庆", "晚会", "初赛",
    "决赛", "展览", "沙龙", "论坛", "宣讲会", "交流会", "运动会"
]

EXCLUDE_KEYWORDS = [
    "空教室", "课程表", "明学楼", "实验楼", "教室", "自习室",
    "学分", "老师", "讲授", "上课", "考试", "复习", "教材"
]

# ==================== 死数据（备用活动数据） ====================

FALLBACK_ACTIVITIES = {
    2026: {
        4: [
            {"name": "人工智能与大模型技术前沿讲座", "date": "4月15日", "time": "14:00-16:00",
             "location": "图书馆报告厅", "desc": "中科院计算所王建国研究员主讲"},
            {"name": "校园十佳歌手大赛初赛", "date": "4月12日", "time": "18:30-21:00",
             "location": "学生活动中心多功能厅", "desc": "报名截止4月10日"},
            {"name": "春季篮球联赛", "date": "4月8日-4月30日", "time": "16:00-18:00",
             "location": "学校篮球场", "desc": "12支院系代表队参赛"},
            {"name": "考研经验分享会", "date": "4月18日", "time": "19:00-21:00",
             "location": "明学楼201", "desc": "优秀考研学生代表分享经验"},
            {"name": "英语四六级备考讲座", "date": "4月22日", "time": "15:00-17:00",
             "location": "实验楼301", "desc": "新东方名师讲解听力与阅读技巧"},
            {"name": "春季校园双选会", "date": "4月20日", "time": "9:00-15:00",
             "location": "体育馆", "desc": "60余家企业到场，提供岗位800余个"},
        ]
    }
}

FALLBACK_UPCOMING_ACTIVITIES = [
    {"name": "人工智能与大模型技术前沿讲座", "date": "4月15日", "time": "14:00-16:00", "location": "图书馆报告厅"},
    {"name": "校园十佳歌手大赛初赛", "date": "4月12日", "time": "18:30-21:00", "location": "学生活动中心"},
    {"name": "春季篮球联赛", "date": "4月8日-4月30日", "time": "16:00-18:00", "location": "学校篮球场"},
    {"name": "考研经验分享会", "date": "4月18日", "time": "19:00-21:00", "location": "明学楼201"},
    {"name": "英语四六级备考讲座", "date": "4月22日", "time": "15:00-17:00", "location": "实验楼301"},
]


# ==================== 辅助函数 ====================

def is_activity_content(content):
    """判断内容是否为活动"""
    for kw in EXCLUDE_KEYWORDS:
        if kw in content:
            return False
    for kw in ACTIVITY_KEYWORDS:
        if kw in content:
            return True
    date_patterns = [r'\d{1,2}月\d{1,2}日', r'\d{4}年\d{1,2}月\d{1,2}日']
    for pattern in date_patterns:
        if re.search(pattern, content):
            return True
    return False


def extract_activity_info(content):
    """从内容中提取活动信息"""
    activities = []
    lines = content.split('\n')

    for line in lines:
        if len(line.strip()) < 10:
            continue
        if not is_activity_content(line):
            continue

        name = ""
        name_match = re.search(r'[0-9]*[\.、]?\s*([^。，,]{4,30}?)[：:]', line)
        if name_match:
            name = name_match.group(1).strip()
        else:
            patterns = [r'([^，,。]{4,25}?)(?:讲座|活动|比赛)', r'([^，,。]{4,25}?)(?:[举举]行)']
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1).strip()
                    break
        if not name:
            name = line[:25].strip()

        date_str = ""
        date_match = re.search(r'(\d{1,2})月(\d{1,2})日', line)
        if date_match:
            date_str = f"{date_match.group(1)}月{date_match.group(2)}日"

        time_str = ""
        time_match = re.search(r'(\d{1,2})点(\d{0,2})分?', line)
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2) if time_match.group(2) else "00"
            time_str = f"{hour}:{minute}"

        location = ""
        location_match = re.search(r'(图书馆|报告厅|活动中心|明学楼\d{3}|实验楼\d{3}|体育馆)', line)
        if location_match:
            location = location_match.group(1)

        activities.append({
            "name": name, "date": date_str, "time": time_str,
            "location": location, "raw": line.strip()
        })

    return activities


# ==================== 主查询函数 ====================
def query_activities(year=None, month=None, limit=10):
    """查询校园活动"""
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    kb_available = st.session_state.get("kb_manager_available", False)

    if kb_available:
        kb_manager = st.session_state.kb_manager

        # 改进搜索词，更精准地定位活动
        search_queries = [
            f"{year}年{month}月 校园活动",
            "讲座 时间 地点",
            "比赛 报名 截止",
            "宣讲会 举办 地点",
            "社团活动 通知"
        ]

        all_results = []
        for query in search_queries:
            results = kb_manager.search(query, top_k=10)
            if results:
                all_results.extend(results)

        # 添加相似度阈值过滤
        all_activities = []
        for result in all_results:
            similarity = result.get('similarity', 0)
            if similarity < 0.4:  # 提高阈值，过滤低相关度结果
                continue

            content = result.get('content', '')

            # 强制排除奖学金相关内容
            if any(word in content for word in ["奖学金", "申请表", "评选"]):
                continue

            activities = extract_activity_info(content)
            all_activities.extend(activities)

        # 去重并返回
        seen = set()
        unique_activities = []
        for act in all_activities:
            key = f"{act['name']}_{act['date']}"
            if key not in seen and act['name']:  # 确保活动名称不为空
                seen.add(key)
                unique_activities.append(act)

        if unique_activities:
            return format_activity_response(unique_activities[:limit], year, month)
        else:
            return " 暂无找到近期校园活动，请稍后再试。"

    return "⚠️ 知识库未连接，无法查询活动信息。"
    # 使用死数据
    year_data = FALLBACK_ACTIVITIES.get(year, {})
    month_data = year_data.get(month, [])

    if month_data:
        return format_activity_response(month_data[:limit], year, month, is_fallback=True)
    else:
        return f"🎉 {year}年{month}月活动：\n\n暂无该月活动信息。\n\n💡 请关注学校官网获取最新活动通知。"


def query_upcoming_activities(days=30):
    """查询未来N天内的活动"""
    kb_available = st.session_state.get("kb_manager_available", False)

    if kb_available:
        kb_manager = st.session_state.kb_manager
        results = kb_manager.search("活动", top_k=15)

        if results:
            all_activities = []
            today = datetime.now()
            for result in results:
                if result.get('similarity', 0) > 0.3:
                    content = result.get('content', '')
                    if not is_activity_content(content):
                        continue
                    activities = extract_activity_info(content)
                    all_activities.extend(activities)

            if all_activities:
                return format_upcoming_response(all_activities[:10], days)

    # 使用死数据
    return format_upcoming_response(FALLBACK_UPCOMING_ACTIVITIES[:10], days, is_fallback=True)


def format_activity_response(activities, year, month, is_fallback=False):
    """格式化活动查询结果"""
    source_tag = "（参考数据）" if is_fallback else ""
    response = f" {year}年{month}月活动{source_tag}：\n\n"
    response += f" 共找到 {len(activities)} 个活动\n\n"

    for i, act in enumerate(activities, 1):
        response += f"{i}. **{act['name']}**\n"
        if act.get('date'):
            response += f"    日期：{act['date']}\n"
        if act.get('time'):
            response += f"    时间：{act['time']}\n"
        if act.get('location'):
            response += f"    地点：{act['location']}\n"
        if act.get('desc'):
            response += f"    简介：{act['desc']}\n"
        response += "\n"

    response += "💡 提示：具体时间地点以官方通知为准。"
    return response


def format_upcoming_response(activities, days, is_fallback=False):
    """格式化近期活动查询结果"""
    source_tag = "（参考数据）" if is_fallback else ""
    today = datetime.now()
    response = f" 近期活动（{days}天内）{source_tag}：\n\n"
    response += f"📅 今天是 {today.strftime('%Y年%m月%d日')}\n\n"

    for i, act in enumerate(activities, 1):
        response += f"{i}. **{act['name']}**\n"
        if act.get('date'):
            response += f"   📅 {act['date']}\n"
        if act.get('time'):
            response += f"   ⏰ {act['time']}\n"
        if act.get('location'):
            response += f"   📍 {act['location']}\n"
        response += "\n"

    return response


#  兼容旧接口的函数

def query_activity_by_month(year=None, month=None):
    """按月份查询活动"""
    return query_activities(year, month)


def query_current_month_activity():
    """查询当前月份活动"""
    return query_activities()


def query_activity_by_name(activity_name):
    """按名称查询活动"""
    # 从死数据中搜索
    for year, year_data in FALLBACK_ACTIVITIES.items():
        for month, activities in year_data.items():
            for act in activities:
                if activity_name in act['name']:
                    response = f"📌 {act['name']} 活动详情：\n\n"
                    response += f" 日期：{act['date']}\n"
                    response += f" 时间：{act['time']}\n"
                    response += f" 地点：{act['location']}\n"
                    response += f" 简介：{act['desc']}\n"
                    return response
    return f"未找到「{activity_name}」相关活动信息。"


def query_this_month_activities():
    """查询本月活动"""
    return query_activities()


def smart_activity_query(user_input):
    """智能活动查询"""
    user_input_lower = user_input.lower()

    if "近期" in user_input_lower or "最近" in user_input_lower:
        return query_upcoming_activities(30)

    month_match = re.search(r'(\d{1,2})月', user_input)
    if month_match:
        month = int(month_match.group(1))
        return query_activities(month=month)

    return query_activities()


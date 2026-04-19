"""
工具函数库 - 日期、时间、每日一句
"""
import random
from datetime import datetime, date
import streamlit as st
from modules.config import DAILY_QUOTES


def get_weekday_cn():
    """获取当前星期几的中文"""
    weekdays_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    return weekdays_cn[datetime.now().weekday()]


def get_time_slot_by_hour():
    """获取当前时段（用于食堂推荐）"""
    current_hour = datetime.now().hour
    if 6 <= current_hour < 10:
        return "早餐"
    elif 10 <= current_hour < 14:
        return "午餐"
    elif 14 <= current_hour < 17:
        return "下午茶"
    else:
        return "晚餐"


def get_time_slot_cn():
    """获取当前时间段（用于教室查询）"""
    current_hour = datetime.now().hour
    if 8 <= current_hour < 12:
        return "上午"
    elif 12 <= current_hour < 14:
        return "中午"
    elif 14 <= current_hour < 18:
        return "下午"
    else:
        return "晚上"


def get_meal_by_hour():
    """获取当前餐段（用于食堂推荐）"""
    return get_time_slot_by_hour()


def get_current_date():
    """获取当前日期字符串"""
    now = datetime.now()
    return f"{now.year}年{now.month}月{now.day}日"


def get_time_range_by_slot(time_slot):
    """根据时间段获取具体时间范围"""
    time_map = {
        "早上": "8:00-9:40",
        "上午": "10:00-11:40",
        "中午": "12:00-13:30",
        "下午": "14:00-15:40",
        "晚上": "16:00-17:40"
    }
    return time_map.get(time_slot, time_slot)


def get_daily_quote():
    """获取每日一句"""
    today = date.today()
    seed = int(today.strftime("%Y%m%d"))
    random.seed(seed)
    quote = random.choice(DAILY_QUOTES)
    random.seed()
    return quote


def show_daily_quote():
    """显示每日一句"""
    quote = get_daily_quote()
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; color: white; margin: 20px 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <div style="font-size: 1.2em; font-style: italic; line-height: 1.6; margin-bottom: 10px;">
            "{quote['text']}"
        </div>
        <div style="text-align: right; font-weight: bold; font-size: 1em;">
            —— {quote['author']}
        </div>
        <div style="display: inline-block; background: rgba(255, 255, 255, 0.2); padding: 3px 10px; border-radius: 20px; font-size: 0.8em; margin-top: 5px;">
            #{quote['category']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    today_cn = get_weekday_cn()
    st.caption(f"📅 {date.today().strftime('%Y年%m月%d日')} {today_cn}")
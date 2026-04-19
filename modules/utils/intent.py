"""
意图识别 - 识别用户输入意图并路由
"""


def detect_intent(user_input):
    user_input_lower = user_input.lower()

    if any(word in user_input_lower for word in ["教室", "空教室", "自习室"]):
        time_slot = ""
        if "上午" in user_input_lower or "早上" in user_input_lower:
            time_slot = "上午"
        elif "下午" in user_input_lower:
            time_slot = "下午"
        elif "晚上" in user_input_lower or "傍晚" in user_input_lower:
            time_slot = "晚上"
        return {"intent": "query_room", "time": time_slot, "question": user_input}

    elif any(word in user_input_lower for word in ["课", "课程", "课表"]):
        return {"intent": "query_course", "time": "", "question": user_input}

    elif any(word in user_input_lower for word in ["食堂", "吃饭", "餐厅", "推荐"]):
        return {"intent": "query_canteen", "time": "", "question": user_input}

    elif any(word in user_input_lower for word in ["活动", "比赛", "讲座", "通知"]):
        return {"intent": "query_activity", "time": "", "question": user_input}

    elif any(word in user_input_lower for word in ["图片", "照片", "分析图片"]):
        return {"intent": "image_help", "time": "", "question": user_input}

    elif any(word in user_input_lower for word in ["搜索", "查找", "检索"]):
        return {"intent": "smart_search", "time": "", "question": user_input}

    else:
        return {"intent": "chat", "time": "", "question": user_input}
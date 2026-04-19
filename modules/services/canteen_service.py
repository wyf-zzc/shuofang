"""
食堂推荐服务 - 按时间段推荐食堂和菜品
"""
import streamlit as st
import re
from datetime import datetime

# ==================== 备用数据 ====================
# 当知识库检索失败时，返回这些预设的餐厅推荐信息

FALLBACK_CANTEEN_DATA = {
    "早餐": {
        "time_range": "7:00-9:00",
        "peak_hours": "7:30-8:10",
        "tips": "建议7:30前到，人少菜全",
        "recommendations": [
            {"name": "鲜肉包子", "price": "2元", "window": "面食窗口", "canteen": "西区餐厅"},
            {"name": "豆浆油条", "price": "3元", "window": "早餐窗口", "canteen": "西区餐厅"},
            {"name": "鸡蛋灌饼", "price": "3.5元", "window": "煎饼窗口", "canteen": "西区餐厅"},
            {"name": "上海鲜肉小笼包", "price": "6-8元/笼", "window": "点心窗口", "canteen": "东区餐厅"},
            {"name": "豆腐脑+油饼", "price": "3.5元", "window": "北方窗口", "canteen": "东区餐厅"},
        ]
    },
    "午餐": {
        "time_range": "11:00-13:00",
        "peak_hours": "11:50-12:30",
        "tips": "西区智慧餐厅排队较快，建议错峰",
        "recommendations": [
            {"name": "小份菜（自助）", "price": "1-10元", "window": "智慧餐盘", "canteen": "西区餐厅"},
            {"name": "麻辣香锅", "price": "12-18元", "window": "香锅窗口", "canteen": "东区餐厅"},
            {"name": "黄焖鸡米饭", "price": "13元", "window": "焖锅窗口", "canteen": "东区餐厅"},
            {"name": "牛肉拉面", "price": "8-10元", "window": "面食窗口", "canteen": "东区餐厅"},
            {"name": "烤肉拌饭", "price": "10-12元", "window": "风味窗口", "canteen": "西区餐厅"},
        ]
    },
    "下午茶": {
        "time_range": "14:00-16:00",
        "peak_hours": "15:00-15:30",
        "tips": "适合学习间隙补充能量",
        "recommendations": [
            {"name": "奶茶+鸡蛋仔", "price": "10元", "window": "饮品窗口", "canteen": "风味餐厅"},
            {"name": "咖啡+蛋糕", "price": "12-15元", "window": "西式餐厅", "canteen": "东区餐厅"},
            {"name": "水果拼盘", "price": "5-8元", "window": "水果窗口", "canteen": "西区餐厅"},
        ]
    },
    "晚餐": {
        "time_range": "17:00-19:00",
        "peak_hours": "17:30-18:30",
        "tips": "18:30后部分窗口关闭，建议早点去",
        "recommendations": [
            {"name": "烤肉拌饭", "price": "10-12元", "window": "风味窗口", "canteen": "西区餐厅"},
            {"name": "麻辣小火锅", "price": "12-18元", "window": "火锅窗口", "canteen": "西区餐厅"},
            {"name": "酸菜鱼", "price": "14元", "window": "风味窗口", "canteen": "第一食堂"},
            {"name": "铁锅焖面", "price": "9-11元", "window": "面食窗口", "canteen": "东区餐厅"},
            {"name": "螺蛳粉", "price": "9-11元", "window": "特色窗口", "canteen": "西区餐厅"},
            {"name": "牛排套餐", "price": "18-25元", "window": "西式餐厅", "canteen": "东区餐厅"},
        ]
    }
}

# 完整食堂信息（备用）
FALLBACK_FULL_CANTEEN = """
【山西工学院食堂信息】

西区餐厅（新天地学府餐厅）：
- 位置：西区
- 特色：智慧餐厅、小份菜、25个窗口
- 营业时间：早餐7:00-9:00 午餐11:00-13:00 晚餐17:00-19:00
- 最大亮点：智慧餐盘系统+小份菜窗口，1-10元价格不等
- 推荐菜品：烤肉拌饭(10-12元)、油泼面(8-10元)、螺蛳粉(9-11元)、麻辣小火锅(12-18元)

东区餐厅（好未来学子餐厅）：
- 位置：东区
- 特色：风味多样、西餐专区
- 营业时间：早餐7:00-9:00 午餐11:00-13:00 晚餐17:00-19:00
- 推荐菜品：麻辣香锅(12-18元)、兰州牛肉面(8-10元)、牛排套餐(18-25元)、滑蛋饭(9-12元)

就餐建议：
- 早餐推荐：一食堂的豆浆油条
- 午餐建议：12:30后就餐人较少
- 晚餐推荐：三食堂特色菜
- 支付方式：校园卡刷卡或扫码支付
"""


# ==================== 辅助函数 ====================

def get_meal_by_hour():
    """根据当前小时获取餐别"""
    hour = datetime.now().hour
    if 5 <= hour < 10:
        return "早餐"
    elif 10 <= hour < 14:
        return "午餐"
    elif 14 <= hour < 17:
        return "下午茶"
    else:
        return "晚餐"


def get_time_slot_by_hour():
    """根据当前小时获取时间段"""
    return get_meal_by_hour()


def parse_canteen_content(content, meal):
    """从知识库内容中解析食堂推荐（"""
    recommendations = []

    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue

        # 跳过标题行和分隔线
        if line.startswith('===') or line.startswith('【') or line.startswith('*'):
            continue

        # 匹配格式：- 菜品名 价格 或 • 菜品名 价格
        # 支持格式：- 红烧肉套餐 15元、- 红烧肉套餐：15元、• 红烧肉套餐 15元
        match = re.match(r'^[-•*]\s*(.+?)(?:[：:]\s*)?(\d+\.?\d*-\d+\.?\d*元|\d+\.?\d*元)?', line)

        if match:
            name = match.group(1).strip()
            price = match.group(2) if match.group(2) else ""

            # 过滤掉太短或无效的名称
            if len(name) >= 2 and len(name) <= 30:
                # 提取窗口信息
                window = ""
                if "窗口" in line:
                    win_match = re.search(r'([^，,。]{2,10}?窗口)', line)
                    if win_match:
                        window = win_match.group(1)

                # 提取餐厅信息
                canteen = ""
                if "西区" in line:
                    canteen = "西区餐厅"
                elif "东区" in line:
                    canteen = "东区餐厅"
                elif "南区" in line:
                    canteen = "南区餐厅"
                elif "北区" in line:
                    canteen = "北区餐厅"

                recommendations.append({
                    "name": name,
                    "price": price,
                    "window": window,
                    "canteen": canteen,
                    "raw": line
                })
            continue


        match2 = re.match(r'^([^0-9]{2,25}?)\s+(\d+\.?\d*-\d+\.?\d*元|\d+\.?\d*元)', line)
        if match2:
            name = match2.group(1).strip()
            price = match2.group(2)

            if len(name) >= 2 and len(name) <= 25:
                recommendations.append({
                    "name": name,
                    "price": price,
                    "window": "",
                    "canteen": "",
                    "raw": line
                })

    return recommendations


def get_fallback_canteen_data(meal, limit=5):
    """获取备用死数据"""
    meal_data = FALLBACK_CANTEEN_DATA.get(meal, FALLBACK_CANTEEN_DATA["晚餐"])

    recommendations = meal_data.get("recommendations", [])[:limit]

    return {
        "time_range": meal_data.get("time_range", "时间待定"),
        "peak_hours": meal_data.get("peak_hours", "未知"),
        "tips": meal_data.get("tips", "请按时就餐"),
        "recommendations": recommendations
    }


# ==================== 主查询函数 ====================

def query_canteen_by_meal(meal=None, limit=10):
    """查询指定餐段的食堂推荐"""

    if meal is None:
        meal = get_meal_by_hour()

    # 尝试从知识库检索
    kb_available = st.session_state.get("kb_manager_available", False)

    if kb_available:
        kb_manager = st.session_state.kb_manager

        search_queries = [f"{meal} 推荐", f"{meal} 食堂", "食堂推荐", "晚餐推荐", "午餐推荐"]
        all_results = []

        for query in search_queries:
            results = kb_manager.search(query, top_k=8)
            if results:
                all_results.extend(results)

        if all_results:
            # 解析推荐菜品
            all_recommendations = []
            for result in all_results:
                if result.get('similarity', 0) > 0.25:
                    content = result.get('content', '')
                    recs = parse_canteen_content(content, meal)
                    all_recommendations.extend(recs)

            # 去重（按名称）
            seen = set()
            unique_recs = []
            for rec in all_recommendations:
                key = rec['name']
                if key not in seen:
                    seen.add(key)
                    unique_recs.append(rec)

            if unique_recs:
                # 构建返回内容（基于知识库）
                response = f"🍜 {meal}推荐（知识库）\n\n"
                response += f"📋 推荐菜品（共{min(len(unique_recs), limit)}种）：\n\n"
                for i, rec in enumerate(unique_recs[:limit], 1):
                    response += f"{i}. {rec['name']}"
                    if rec.get('price'):
                        response += f" ｜ {rec['price']}"
                    if rec.get('canteen'):
                        response += f" ｜ 📍 {rec['canteen']}"
                    if rec.get('window'):
                        response += f" ｜ {rec['window']}"
                    response += "\n"

                response += f"\n⏰ 营业时间：根据各餐厅安排\n"
                response += f"💡 提示：西区餐厅支持小份菜自助取餐\n"
                response += "\n⚠️ 注意事项：\n"
                response += "• 校园卡刷卡或扫码支付\n"
                response += "• 清真窗口设在东区餐厅二楼\n"

                return response

    # ========== 知识库无数据时 ==========
    fallback_data = get_fallback_canteen_data(meal, limit)

    response = f"🍜 {meal}推荐（参考数据）\n\n"
    response += f"⏰ 营业时间：{fallback_data['time_range']}\n"
    response += f"🔥 高峰期：{fallback_data['peak_hours']}\n"
    response += f"💡 建议：{fallback_data['tips']}\n\n"

    response += f"📋 推荐菜品（共{len(fallback_data['recommendations'])}种）：\n\n"
    for i, rec in enumerate(fallback_data['recommendations'], 1):
        response += f"{i}. {rec['name']}"
        if rec.get('price'):
            response += f" ｜ {rec['price']}"
        if rec.get('window'):
            response += f" ｜ {rec['window']}"
        if rec.get('canteen'):
            response += f" ｜ 📍 {rec['canteen']}"
        response += "\n"

    response += "\n⚠️ 注意事项：\n"
    response += "• 校园卡刷卡或扫码支付\n"
    response += "• 清真窗口设在东区餐厅二楼\n"
    response += "• 西区餐厅支持小份菜自助取餐\n"
    response += "• 以上信息仅供参考，以实际为准\n"

    if not kb_available:
        response += "\n💡 提示：知识库未连接，以上为参考数据。可通过「知识库管理」上传更准确的食堂信息。"

    return response


def query_current_canteen():
    """查询当前时段的食堂推荐"""
    return query_canteen_by_meal(get_meal_by_hour())


def query_canteen_full():
    """查询完整食堂信息（带死数据备用）"""

    kb_available = st.session_state.get("kb_manager_available", False)

    if kb_available:
        kb_manager = st.session_state.kb_manager
        results = kb_manager.search("食堂 推荐 菜单", top_k=5)

        if results:
            response = "🍜 食堂完整信息：\n\n"
            for result in results:
                if result.get('similarity', 0) > 0.3:
                    content = result.get('content', '')
                    if len(content) > 800:
                        content = content[:800] + "..."
                    response += f"{content}\n\n"
            return response

    # 使用备用
    return FALLBACK_FULL_CANTEEN


# ==================== 快捷查询函数 ====================

def query_breakfast():
    """查询早餐推荐"""
    return query_canteen_by_meal("早餐", limit=5)


def query_lunch():
    """查询午餐推荐"""
    return query_canteen_by_meal("午餐", limit=6)


def query_dinner():
    """查询晚餐推荐"""
    return query_canteen_by_meal("晚餐", limit=8)


def query_afternoon_tea():
    """查询下午茶推荐"""
    return query_canteen_by_meal("下午茶", limit=3)


def smart_canteen_query(user_input):
    """智能食堂查询"""
    user_input_lower = user_input.lower()

    if "全部" in user_input_lower or "完整" in user_input_lower or "所有" in user_input_lower:
        return query_canteen_full()

    if "早餐" in user_input_lower:
        return query_breakfast()
    elif "午餐" in user_input_lower:
        return query_lunch()
    elif "晚餐" in user_input_lower:
        return query_dinner()
    elif "下午茶" in user_input_lower:
        return query_afternoon_tea()

    return query_current_canteen()



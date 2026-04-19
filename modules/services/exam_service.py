"""
考试服务 - 考试倒计时、复习计划生成
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime, date, timedelta

class ExamManager:
    def __init__(self):
        if "exams" not in st.session_state:
            st.session_state.exams = []
        self.init_exam_database()

    def init_exam_database(self):
        os.makedirs("data", exist_ok=True)
        self.db_path = "data/exams.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS exams (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, date TEXT NOT NULL, subject TEXT NOT NULL, location TEXT, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''
        )
        conn.commit()
        conn.close()
        self.load_exams_from_db()

    def load_exams_from_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exams ORDER BY date")
            rows = cursor.fetchall()
            exams = []
            for row in rows:
                exam = {"id": row[0], "name": row[1], "date": row[2], "subject": row[3],
                        "location": row[4] if row[4] else "", "notes": row[5] if row[5] else "",
                        "created_at": row[6] if len(row) > 6 else ""}
                exams.append(exam)
            st.session_state.exams = exams
            conn.close()
        except Exception as e:
            st.warning(f"加载考试失败: {e}")
            st.session_state.exams = []

    def add_exam(self, name, date_str, subject, location="", notes=""):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO exams (name, date, subject, location, notes) VALUES (?, ?, ?, ?, ?)',
                           (name, date_str, subject, location, notes))
            exam_id = cursor.lastrowid
            conn.commit()
            conn.close()
            exam = {"id": exam_id, "name": name, "date": date_str, "subject": subject,
                    "location": location, "notes": notes, "created_at": datetime.now().isoformat()}
            st.session_state.exams.append(exam)
            return True
        except Exception as e:
            st.warning(f"添加考试失败: {e}")
            return False

    def delete_exam(self, exam_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
            conn.commit()
            conn.close()
            st.session_state.exams = [e for e in st.session_state.exams if e["id"] != exam_id]
            return True
        except Exception as e:
            st.warning(f"删除考试失败: {e}")
            return False

    def get_upcoming_exams(self, days=30):
        upcoming = []
        today = datetime.now().date()
        for exam in st.session_state.exams:
            try:
                exam_date = datetime.strptime(exam['date'], "%Y-%m-%d").date()
                days_left = (exam_date - today).days
                if 0 <= days_left <= days:
                    exam['days_left'] = days_left
                    exam['status'] = self._get_status(days_left)
                    exam['date_display'] = exam_date.strftime("%Y年%m月%d日")
                    upcoming.append(exam)
            except:
                continue
        return sorted(upcoming, key=lambda x: x['days_left'])

    def _get_status(self, days_left):
        if days_left < 0:
            return "已完成"
        elif days_left == 0:
            return "今天考试"
        elif days_left <= 3:
            return "紧急"
        elif days_left <= 7:
            return "近期"
        elif days_left <= 14:
            return "准备中"
        else:
            return "规划中"

    def get_stats(self):
        upcoming = self.get_upcoming_exams(days=365)
        total = len(upcoming)
        urgent = len([e for e in upcoming if e['days_left'] <= 3])
        recent = len([e for e in upcoming if 4 <= e['days_left'] <= 7])
        avg_days = sum(e['days_left'] for e in upcoming) / total if total > 0 else 0
        return {"total": total, "urgent": urgent, "recent": recent, "avg_days": avg_days}


# ==================== 大模型复习规划生成器 ====================

def generate_review_plan_with_llm(exam, model_manager):
    """使用大模型生成复习计划"""

    exam_name = exam.get('name', '考试')
    subject = exam.get('subject', '科目')
    days_left = exam.get('days_left', 0)
    notes = exam.get('notes', '')
    location = exam.get('location', '')

    # 构建提示词
    prompt_lines = []
    prompt_lines.append("你是一位经验丰富的校园学习规划专家。请为以下考试制定一份详细、个性化、可执行的复习计划。")
    prompt_lines.append("")
    prompt_lines.append("## 考试信息")
    prompt_lines.append(f"- 考试名称：{exam_name}")
    prompt_lines.append(f"- 科目：{subject}")
    prompt_lines.append(f"- 剩余天数：{days_left}天")
    prompt_lines.append(f"- 考试地点：{location if location else '待定'}")
    prompt_lines.append(f"- 备注/重点：{notes if notes else '无特殊要求'}")
    prompt_lines.append("")
    prompt_lines.append("## 输出要求")
    prompt_lines.append("请按以下格式输出，使用 Markdown 格式：")
    prompt_lines.append("")
    prompt_lines.append("# 📚 {exam_name} 复习计划")
    prompt_lines.append("")
    prompt_lines.append("## 📊 基本信息")
    prompt_lines.append("- 剩余天数：**{days_left}天**")
    prompt_lines.append("- 建议每日学习时间：**X小时**")
    prompt_lines.append("- 难度评估：**X/10**")
    prompt_lines.append("")
    prompt_lines.append("## 🎯 总体策略")
    prompt_lines.append("（根据剩余天数给出整体复习策略）")
    prompt_lines.append("")
    prompt_lines.append("## 📅 每日详细安排")
    prompt_lines.append("（按天列出，从今天开始到考试前一天）")
    prompt_lines.append("")
    prompt_lines.append("## ⭐ 重点复习内容")
    prompt_lines.append("（根据科目特点列出重点）")
    prompt_lines.append("")
    prompt_lines.append("## 💡 备考小贴士")
    prompt_lines.append("（实用的学习方法和技巧）")
    prompt_lines.append("")
    prompt_lines.append("## 🎯 考前最后提醒")
    prompt_lines.append("（考试前一天和当天的注意事项）")

    prompt = "\n".join(prompt_lines)

    try:
        with st.spinner(" 大模型正在为你生成个性化复习计划..."):
            result, used_provider, status = model_manager.smart_chat(prompt)

            if status == "success" and result:
                provider_name = "DeepSeek云端" if used_provider == "deepseek" else "Ollama本地"
                result = f"✨ *由 {provider_name} 大模型生成* ✨\n\n---\n\n{result}"
                return result
            else:
                return None
    except Exception as e:
        st.warning(f"大模型生成失败: {e}")
        return None


def generate_review_plan(exam, model_manager=None):
    """生成复习计划（优先使用大模型）"""

    exam_name = exam.get('name', '考试')
    subject = exam.get('subject', '科目')
    days_left = exam.get('days_left', 0)
    notes = exam.get('notes', '')

    # 优先使用大模型（如果可用）
    if model_manager is not None:
        services_available = model_manager.check_services()
        has_llm = services_available.get("deepseek", False) or services_available.get("ollama", False)

        if has_llm:
            llm_plan = generate_review_plan_with_llm(exam, model_manager)
            if llm_plan:
                return llm_plan

    # 降级：使用模板生成
    return generate_template_review_plan(exam_name, subject, days_left, notes)


def generate_template_review_plan(exam_name, subject, days_left, notes=""):
    """模板生成复习计划（降级方案）"""

    if days_left <= 0:
        lines = []
        lines.append(f"# 📚 {exam_name} 今日考试！")
        lines.append("")
        lines.append("## 💪 考前提醒")
        lines.append("- **放松心态**，不要紧张")
        lines.append("- **检查物品**：准考证、学生证、身份证、文具")
        lines.append("- **提前到场**：建议提前30分钟到达考场")
        lines.append("- **保持睡眠**：前一晚保证7-8小时睡眠")
        lines.append("")
        lines.append("祝你考试顺利，取得好成绩！🎉")
        return "\n".join(lines)

    if days_left <= 3:
        return generate_urgent_plan_template(exam_name, subject, days_left, notes)
    elif days_left <= 7:
        return generate_weekly_plan_template(exam_name, subject, days_left, notes)
    elif days_left <= 14:
        return generate_two_week_plan_template(exam_name, subject, days_left, notes)
    else:
        return generate_long_term_plan_template(exam_name, subject, days_left, notes)


def generate_urgent_plan_template(exam_name, subject, days_left, notes):
    """紧急复习计划模板（3天内）"""
    lines = []
    lines.append(f"# 📚 {exam_name} 紧急复习计划")
    lines.append("")
    lines.append("## 📊 基本信息")
    lines.append(f"- 剩余天数：**{days_left}天**")
    lines.append("- 模式：**紧急冲刺模式**")
    lines.append("- 建议每日学习：**6-8小时**")
    lines.append("")
    lines.append("## 🎯 总体策略")
    lines.append("- 集中突破重点、难点")
    lines.append("- 以真题和错题为主")
    lines.append("- 放弃偏难怪题，保基础分")
    lines.append("")
    lines.append("## 📅 每日安排")
    lines.append("")
    lines.append(f"### 第1天（距考试{days_left}天）")
    lines.append("- **上午**：梳理知识框架，标记薄弱点")
    lines.append("- **下午**：做1-2套真题，分析错题")
    lines.append("- **晚上**：背诵核心公式/概念")
    lines.append("")

    if days_left >= 2:
        lines.append(f"### 第2天（距考试{days_left - 1}天）")
        lines.append("- **上午**：复习错题本，巩固薄弱环节")
        lines.append("- **下午**：模拟考试（限时完成）")
        lines.append("- **晚上**：回顾重点，整理笔记")
        lines.append("")

    lines.append("### 考前最后一天")
    lines.append("- **上午**：快速浏览知识点")
    lines.append("- **下午**：放松休息，不再做新题")
    lines.append("- **晚上**：准备考试用品，早睡（23:00前）")
    lines.append("")
    lines.append("## ⭐ 重点复习内容")
    if notes:
        lines.append(notes)
    else:
        lines.append("- 历年真题中的高频考点")
        lines.append("- 老师划的重点范围")
        lines.append("- 自己的错题本")
    lines.append("")
    lines.append("## 💡 备考小贴士")
    lines.append("- 每学习50分钟休息10分钟")
    lines.append("- 保持充足睡眠，不要熬夜")
    lines.append("- 适当运动缓解压力")
    lines.append("")
    lines.append("## 🎯 考前提醒")
    lines.append("✅ 带齐证件（学生证、身份证、准考证）")
    lines.append("✅ 准备好文具（2B铅笔、黑色签字笔、橡皮）")
    lines.append("✅ 提前30分钟到达考场")
    lines.append("✅ 保持良好心态")
    lines.append("")
    lines.append("**加油！相信自己！💪**")

    return "\n".join(lines)


def generate_weekly_plan_template(exam_name, subject, days_left, notes):
    """一周复习计划模板"""
    lines = []
    lines.append(f"# 📚 {exam_name} 复习计划")
    lines.append("")
    lines.append("## 📊 基本信息")
    lines.append(f"- 剩余天数：**{days_left}天**")
    lines.append("- 模式：**强化冲刺模式**")
    lines.append("- 建议每日学习：**5-6小时**")
    lines.append("")
    lines.append("## 🎯 总体策略")
    lines.append(f"- **前{days_left - 2}天**：系统复习，查漏补缺")
    lines.append("- **最后2天**：模拟冲刺，调整状态")
    lines.append("")
    lines.append("## 📅 每日安排")
    lines.append("")
    lines.append(f"### 第1-{days_left - 2}天（基础巩固）")
    lines.append("**每天任务：**")
    lines.append("- **上午 9:00-12:00**：学习1-2章重点内容")
    lines.append("- **下午 14:00-17:00**：做配套习题，分析错题")
    lines.append("- **晚上 19:00-21:00**：复习当天内容，整理笔记")
    lines.append("")
    lines.append("### 冲刺阶段（最后2天）")
    lines.append("")
    lines.append("#### 倒数第2天")
    lines.append("- **上午**：全真模拟测试（限时完成）")
    lines.append("- **下午**：分析错题，查漏补缺")
    lines.append("- **晚上**：回顾核心知识点")
    lines.append("")
    lines.append("#### 考前最后一天")
    lines.append("- **上午**：快速浏览重点")
    lines.append("- **下午**：放松休息")
    lines.append("- **晚上**：准备物品，早睡")
    lines.append("")
    lines.append("## ⭐ 重点复习内容")
    if notes:
        lines.append(notes)
    else:
        lines.append("- 根据老师划的重点复习")
        lines.append("- 关注历年真题重复考点")
        lines.append("- 整理自己的薄弱环节")
    lines.append("")
    lines.append("## 📝 每日时间表")
    lines.append("```")
    lines.append("上午 9:00-12:00  → 学习新内容/复习重点")
    lines.append("中午 12:00-14:00 → 午餐 + 午休")
    lines.append("下午 14:00-17:00 → 做题练习 + 错题分析")
    lines.append("傍晚 17:00-19:00 → 晚餐 + 放松")
    lines.append("晚上 19:00-21:00 → 巩固复习 + 整理笔记")
    lines.append("晚上 21:00-22:30 → 休闲娱乐 + 准备休息")
    lines.append("```")
    lines.append("")
    lines.append("**按计划执行，稳扎稳打！🎯**")

    return "\n".join(lines)


def generate_two_week_plan_template(exam_name, subject, days_left, notes):
    """两周复习计划模板"""
    lines = []
    lines.append(f"# 📚 {exam_name} 复习计划")
    lines.append("")
    lines.append("## 📊 基本信息")
    lines.append(f"- 剩余天数：**{days_left}天**")
    lines.append("- 模式：**系统复习模式**")
    lines.append("- 建议每日学习：**4-5小时**")
    lines.append("")
    lines.append("## 🎯 总体策略")
    lines.append("- **第一周**：全面复习，打好基础")
    lines.append("- **第二周**：强化训练，查漏补缺")
    lines.append("")
    lines.append("## 📅 第一周安排（基础阶段）")
    lines.append("- 目标：完成所有章节的第一轮复习")
    lines.append("- 每天：学习2-3章内容 + 做配套习题")
    lines.append("- 重点：理解概念，建立知识框架")
    lines.append("")
    lines.append("## 📅 第二周安排（强化阶段）")
    lines.append("- 目标：真题训练 + 错题回顾")
    lines.append("- 每天：1套真题 + 分析错题")
    lines.append("- 重点：掌握解题技巧，提高速度")
    lines.append("")
    lines.append("## ⭐ 重点复习内容")
    if notes:
        lines.append(notes)
    else:
        lines.append("- 按照章节顺序系统复习")
        lines.append("- 完成历年真题（至少3套）")
        lines.append("- 整理错题本，反复查看")
    lines.append("")
    lines.append("## 🎯 考前3天冲刺")
    lines.append("- 第3天：模拟考试（严格按照考试时间）")
    lines.append("- 第2天：复习错题，背诵重点")
    lines.append("- 第1天：放松心态，准备考试用品")
    lines.append("")
    lines.append("**合理规划时间，劳逸结合！📖**")

    return "\n".join(lines)


def generate_long_term_plan_template(exam_name, subject, days_left, notes):
    """长期复习计划模板（14天以上）"""
    weeks = days_left // 7

    lines = []
    lines.append(f"# 📚 {exam_name} 复习计划")
    lines.append("")
    lines.append("## 📊 基本信息")
    lines.append(f"- 剩余天数：**{days_left}天**（约{weeks}周）")
    lines.append("- 模式：**长期规划模式**")
    lines.append("- 建议每日学习：**3-4小时**")
    lines.append("")
    lines.append("## 🎯 总体策略（分阶段）")
    lines.append(f"- **第1-{weeks - 2 if weeks > 2 else 1}周**：基础夯实阶段")
    lines.append(f"- **第{weeks - 1 if weeks > 2 else 2}周**：强化提升阶段")
    lines.append("- **最后1周**：冲刺模拟阶段")
    lines.append("")
    lines.append("## 📅 各阶段任务")
    lines.append("")
    lines.append("### 基础阶段")
    lines.append("- 目标：完成所有章节的系统学习")
    lines.append("- 方法：教材+课件+课后习题")
    lines.append(f"- 进度：每周完成3-4章")
    lines.append("")
    lines.append("### 强化阶段")
    lines.append("- 目标：真题训练 + 专题突破")
    lines.append("- 方法：按题型分类练习")
    lines.append("- 进度：每周完成2-3套真题")
    lines.append("")
    lines.append("### 冲刺阶段")
    lines.append("- 目标：模拟考试 + 查漏补缺")
    lines.append("- 方法：全真模拟，限时完成")
    lines.append("- 重点：调整心态，保持状态")
    lines.append("")
    lines.append("## 📝 每周时间安排")
    lines.append("```")
    lines.append("周一至周五：")
    lines.append("  上午 8:30-11:30 → 学习新内容")
    lines.append("  下午 14:00-17:00 → 做题练习")
    lines.append("  晚上 19:00-21:00 → 复习巩固")
    lines.append("")
    lines.append("周六：")
    lines.append("  上午 → 模拟测试")
    lines.append("  下午 → 分析错题")
    lines.append("")
    lines.append("周日：")
    lines.append("  休息 / 补漏 / 整理笔记")
    lines.append("```")
    lines.append("")
    lines.append("## ⭐ 重点复习内容")
    if notes:
        lines.append(notes)
    else:
        lines.append("- 按教材章节顺序复习")
        lines.append("- 完成近5年真题")
        lines.append("- 建立错题本，定期回顾")
    lines.append("")
    lines.append("## 💡 备考建议")
    lines.append("✅ 制定周计划并严格执行")
    lines.append("✅ 每周复盘学习进度")
    lines.append("✅ 保持规律作息，不要熬夜")
    lines.append("✅ 适当运动，保持健康")
    lines.append("")
    lines.append("**坚持就是胜利！🎓**")

    return "\n".join(lines)


def show_review_plan(exam, model_manager=None):
    """显示复习计划"""
    with st.spinner("正在生成复习计划..."):
        plan = generate_review_plan(exam, model_manager)
        st.markdown(plan)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 复制计划", key=f"copy_plan_{exam['id']}"):
                st.code(plan[:1000])
                st.success("已复制到剪贴板（前1000字符）")
        with col2:
            if st.button("🔄 重新生成", key=f"regen_plan_{exam['id']}"):
                st.rerun()


def show_exam_dashboard(model_manager=None):
    """显示考试倒计时面板"""
    st.title("📅 考试倒计时")
    exam_manager = ExamManager()

    # 侧边栏添加考试
    with st.sidebar:
        st.markdown("---")
        st.subheader("📝 添加新考试")
        with st.form("add_exam_form"):
            exam_name = st.text_input("考试名称*", placeholder="如：期末考试")
            exam_date = st.date_input("考试日期*", min_value=date.today())
            exam_subject = st.text_input("科目*", placeholder="如：高等数学")
            exam_location = st.text_input("考试地点", placeholder="如：明学楼101")
            exam_notes = st.text_area("备注", placeholder="复习重点、注意事项等", height=100)

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("✅ 添加考试", use_container_width=True)
            with col2:
                clear_btn = st.form_submit_button("🗑️ 清空", use_container_width=True, type="secondary")

            if submitted and exam_name and exam_subject:
                success = exam_manager.add_exam(
                    name=exam_name,
                    date_str=exam_date.strftime("%Y-%m-%d"),
                    subject=exam_subject,
                    location=exam_location,
                    notes=exam_notes
                )
                if success:
                    st.success(f"✅ 已添加考试：{exam_name}")
                else:
                    st.error("❌ 添加考试失败")
                st.rerun()
            if clear_btn:
                st.rerun()

    # 统计卡片
    col1, col2, col3 = st.columns(3)
    stats = exam_manager.get_stats()
    with col1:
        st.metric("📊 总考试数", stats["total"])
    with col2:
        st.metric("🚨 紧急考试", stats["urgent"], delta="3天内")
    with col3:
        st.metric("📈 平均剩余", f"{stats['avg_days']:.1f}天")

    st.markdown("---")

    # 考试列表
    upcoming_exams = exam_manager.get_upcoming_exams(days=365)

    if not upcoming_exams:
        st.info("🎉 暂无考试安排，请在侧边栏添加考试")
        return

    # 筛选
    status_filter = st.selectbox(
        "筛选状态",
        ["全部", "今天考试", "紧急（3天内）", "近期（7天内）", "准备中（14天内）", "规划中"]
    )

    for exam in upcoming_exams:
        filter_map = {
            "全部": True,
            "今天考试": exam['status'] == "今天考试",
            "紧急（3天内）": exam['status'] == "紧急",
            "近期（7天内）": exam['status'] == "近期",
            "准备中（14天内）": exam['status'] == "准备中",
            "规划中": exam['status'] == "规划中"
        }
        if not filter_map.get(status_filter, True):
            continue

        with st.expander(f"**{exam['name']}** - {exam['subject']} ({exam['status']})",
                         expanded=exam['status'] in ["今天考试", "紧急"]):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**日期**: {exam['date_display']}")
                st.write(f"**剩余天数**: {exam['days_left']}天")
                if exam.get('location'):
                    st.write(f"**地点**: {exam['location']}")
            with col2:
                if exam['days_left'] <= 30:
                    progress = 1 - (exam['days_left'] / 30)
                    st.progress(min(progress, 1.0))
                    st.caption("倒计时进度")
            with col3:
                if st.button("🗑️ 删除", key=f"delete_{exam['id']}", type="secondary"):
                    if exam_manager.delete_exam(exam['id']):
                        st.success("✅ 考试已删除")
                        st.rerun()
                    else:
                        st.error("❌ 删除失败")

            if exam.get('notes'):
                st.info(f"💡 **备注**: {exam['notes']}")

            # 生成复习计划按钮
            st.markdown("---")
            st.subheader("📖 复习计划")

            if st.button("🎯 生成复习计划", key=f"plan_btn_{exam['id']}"):
                show_review_plan(exam, model_manager)


if __name__ == "__main__":
    show_exam_dashboard()
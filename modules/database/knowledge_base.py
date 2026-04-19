"""
知识库管理器 - 集成向量存储和文档切片
"""
import streamlit as st
from typing import List, Dict, Optional
from modules.database.vector_store import VectorStore
from modules.database.document_chunker import DocumentChunker


class KnowledgeBaseManager:
    def __init__(self, db_path: str = "data/vector_store.db"):
        self.vector_store = VectorStore(db_path)
        self.chunker = DocumentChunker(chunk_size=500, overlap=50)

    def add_document(self, title: str, content: str, category: str = "general",
                     source: str = "用户上传", file_name: str = None, file_type: str = None) -> tuple:
        try:
            doc = {
                'title': title,
                'content': content,
                'category': category,
                'metadata': {
                    'source': source,
                    'file_name': file_name,
                    'file_type': file_type,
                    'original_title': title
                }
            }
            chunks = self.chunker.chunk_text(content, title)
            for i, chunk in enumerate(chunks):
                chunk['category'] = category
                chunk['metadata'] = {
                    **doc['metadata'],
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }

            success_count = 0
            for chunk in chunks:
                doc_id = self.vector_store.add_text(
                    content=chunk['content'],
                    title=chunk['title'],
                    category=category,
                    metadata=chunk['metadata']
                )
                if doc_id:
                    success_count += 1
            if success_count > 0:
                return True, f"文档已切分为 {success_count} 个片段并向量化存储", success_count
            else:
                return False, "文档存储失败", 0
        except Exception as e:
            return False, f"添加文档失败: {str(e)}", 0

    def search(self, query: str, top_k: int = 5, category: str = None) -> List[Dict]:
        return self.vector_store.search(query, top_k=top_k, category=category)

    def get_relevant_context(self, query: str, top_k: int = 3, max_chars: int = 1500) -> str:
        results = self.search(query, top_k=top_k)
        if not results:
            return ""
        context = "📚 相关参考资料：\n\n"
        total_chars = 0
        for i, result in enumerate(results, 1):
            context += f"---\n"
            context += f"**{i}. {result['title']}** (相关度: {result['similarity']:.1%})\n"
            content = result['content']
            context += f"{content}\n\n"
            total_chars += len(content)
            if total_chars >= max_chars:
                context += "... (内容已截断)\n"
                break
        return context

    def delete_document(self, doc_id: int) -> bool:
        return self.vector_store.delete_document(doc_id)

    def get_all_documents(self, limit: int = 100) -> List[Dict]:
        return self.vector_store.get_all_documents(limit=limit)

    def get_stats(self) -> Dict:
        return self.vector_store.get_stats()

    def get_categories(self) -> List[str]:
        stats = self.get_stats()
        return list(stats.get('by_category', {}).keys())


def show_knowledge_base_upload():
    """显示知识库管理界面"""
    st.title("📚 知识库管理")

    if "kb_manager" not in st.session_state:
        st.session_state.kb_manager = KnowledgeBaseManager()
        st.session_state.kb_manager_available = True

    kb = st.session_state.kb_manager

    tab1, tab2, tab3 = st.tabs(["📤 上传文档", "📋 文档列表", "📊 统计信息"])

    with tab1:
        st.subheader("上传知识文档")
        with st.form("upload_knowledge_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("文档标题 *", placeholder="例如：校园卡使用指南")
                category = st.selectbox("文档分类 *", ["学习资源", "校园服务", "规章制度", "活动通知", "其他"])
            with col2:
                source = st.text_input("信息来源", placeholder="例如：学校官网、教务处")
                file_type = st.selectbox("文档类型", ["文本", "规章制度", "学习资料", "活动通知", "其他"])
            content = st.text_area("文档内容 *", height=300, placeholder="请输入文档的详细内容...")
            uploaded_file = st.file_uploader("或上传文件（可选）", type=['txt', 'md', 'json'],
                                             help="支持上传txt、md、json格式的文件")
            file_name = None
            if uploaded_file:
                file_name = uploaded_file.name
                try:
                    file_content = uploaded_file.read().decode('utf-8')
                    if not content:
                        content = file_content
                        st.info(f"✅ 已从文件读取内容，共 {len(content)} 字符")
                except Exception as e:
                    st.error(f"文件读取失败: {e}")
            submitted = st.form_submit_button("✅ 上传到知识库", use_container_width=True, type="primary")
            if submitted:
                if not title or not content:
                    st.error("请填写文档标题和内容")
                else:
                    with st.spinner("正在处理文档（切片、向量化、存储）..."):
                        success, message, doc_count = kb.add_document(
                            title=title, content=content, category=category,
                            source=source or "用户上传", file_name=file_name, file_type=file_type
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                        else:
                            st.error(f"❌ {message}")

    with tab2:
        st.subheader("知识库文档列表")
        col1, col2 = st.columns([2, 1])
        with col1:
            categories = ["全部"] + kb.get_categories()
            filter_category = st.selectbox("按分类筛选", categories)
        with col2:
            search_term = st.text_input("🔍 搜索文档", placeholder="输入标题关键词")
        documents = kb.get_all_documents(limit=100)
        if filter_category != "全部":
            documents = [d for d in documents if d.get('category') == filter_category]
        if search_term:
            documents = [d for d in documents if search_term.lower() in d['title'].lower()]
        if not documents:
            st.info(" 暂无文档，请先上传")
        else:
            st.caption(f"共找到 {len(documents)} 篇文档")
            for doc in documents:
                with st.expander(f"📄 {doc['title']} ({doc.get('category', '未分类')})"):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**分类**: {doc.get('category', '未知')}")
                        st.markdown(f"**来源**: {doc.get('metadata', {}).get('source', '未知')}")
                        st.markdown(f"**上传时间**: {doc.get('created_at', '未知')[:19] if doc.get('created_at') else '未知'}")
                        if doc.get('metadata', {}).get('file_name'):
                            st.markdown(f"**源文件**: {doc['metadata']['file_name']}")
                    with col2:
                        if st.button("📖 查看详情", key=f"view_{doc['id']}"):
                            with st.expander("完整内容", expanded=True):
                                st.markdown(doc.get('full_content', doc['content']))
                    with col3:
                        if st.button("🗑️ 删除", key=f"del_{doc['id']}", type="secondary"):
                            if kb.delete_document(doc['id']):
                                st.success(f"已删除文档「{doc['title']}」")
                                st.rerun()
                            else:
                                st.error("删除失败")
                    st.markdown("**内容预览**:")
                    st.caption(doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content'])

    with tab3:
        st.subheader("知识库统计")
        stats = kb.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📚 总文档数", stats["total"])
        with col2:
            st.metric("📂 分类数量", len(stats.get("by_category", {})))
        if stats.get("by_category"):
            st.subheader("按分类统计")
            import pandas as pd
            df = pd.DataFrame([{"分类": cat, "数量": count} for cat, count in stats["by_category"].items()])
            st.dataframe(df, use_container_width=True)
            st.bar_chart(df.set_index("分类"))
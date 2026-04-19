"""
向量数据库 - 实现文本向量化和语义检索
"""
import os
import json
import pickle
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import streamlit as st


class VectorStore:
    def __init__(self, db_path: str = "data/vector_store.db",
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.db_path = db_path
        self.model_name = model_name
        self.model = None
        self.vector_dim = 384
        self._load_model()
        self.init_database()

    def _load_model(self):
        try:
            with st.spinner("正在加载向量化模型，首次加载需要下载模型文件（约400MB）..."):
                self.model = SentenceTransformer(self.model_name)
                st.success(" 向量化模型加载成功")
        except Exception as e:
            st.error(f"模型加载失败: {e}")
            raise

    def init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vector_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                title TEXT,
                category TEXT,
                vector BLOB NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON vector_store(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON vector_store(created_at)')
        conn.commit()
        conn.close()

    def _text_to_vector(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(self.vector_dim)
        if len(text) > 2000:
            text = text[:2000]
        if self.model is None:
            self._load_model()
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector

    def _vector_to_blob(self, vector: np.ndarray) -> bytes:
        return pickle.dumps(vector)

    def _blob_to_vector(self, blob: bytes) -> np.ndarray:
        return pickle.loads(blob)

    def add_text(self, content: str, title: str = "", category: str = "general", metadata: Dict = None) -> Optional[int]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            vector = self._text_to_vector(content)
            vector_blob = self._vector_to_blob(vector)
            meta_str = json.dumps(metadata or {}, ensure_ascii=False)
            cursor.execute('''
                INSERT INTO vector_store (content, title, category, vector, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (content, title, category, vector_blob, meta_str))
            doc_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return doc_id
        except Exception as e:
            st.error(f"添加文本失败: {e}")
            return None

    def search(self, query: str, top_k: int = 5, category: str = None, min_similarity: float = 0.3) -> List[Dict]:
        try:
            query_vector = self._text_to_vector(query)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if category:
                cursor.execute('''
                    SELECT id, content, title, category, vector, metadata, created_at
                    FROM vector_store WHERE category = ?
                ''', (category,))
            else:
                cursor.execute('SELECT id, content, title, category, vector, metadata, created_at FROM vector_store')
            rows = cursor.fetchall()
            conn.close()
            if not rows:
                return []
            results = []
            for row in rows:
                doc_id, content, title, cat, vector_blob, meta_str, created_at = row
                doc_vector = self._blob_to_vector(vector_blob)
                similarity = float(np.dot(query_vector, doc_vector))
                if similarity >= min_similarity:
                    try:
                        metadata = json.loads(meta_str) if meta_str else {}
                    except:
                        metadata = {}
                    results.append({
                        'id': doc_id,
                        'content': content[:500] + '...' if len(content) > 500 else content,
                        'full_content': content,
                        'title': title,
                        'category': cat,
                        'similarity': similarity,
                        'metadata': metadata,
                        'created_at': created_at
                    })
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
        except Exception as e:
            st.error(f"搜索失败: {e}")
            return []

    def delete_document(self, doc_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vector_store WHERE id = ?", (doc_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"删除失败: {e}")
            return False

    def get_document(self, doc_id: int) -> Optional[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, title, category, metadata, created_at
                FROM vector_store WHERE id = ?
            ''', (doc_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'id': row[0],
                    'content': row[1],
                    'title': row[2],
                    'category': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5]
                }
            return None
        except Exception as e:
            st.error(f"获取文档失败: {e}")
            return None

    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, title, category, metadata, created_at
                FROM vector_store ORDER BY created_at DESC LIMIT ? OFFSET ?
            ''', (limit, offset))
            rows = cursor.fetchall()
            conn.close()
            documents = []
            for row in rows:
                documents.append({
                    'id': row[0],
                    'content': row[1][:300] + '...' if len(row[1]) > 300 else row[1],
                    'full_content': row[1],
                    'title': row[2],
                    'category': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5]
                })
            return documents
        except Exception as e:
            st.error(f"获取文档列表失败: {e}")
            return []

    def get_stats(self) -> Dict:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vector_store")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT category, COUNT(*) FROM vector_store GROUP BY category")
            by_category = dict(cursor.fetchall())
            conn.close()
            return {'total': total, 'by_category': by_category}
        except Exception as e:
            st.error(f"获取统计失败: {e}")
            return {'total': 0, 'by_category': {}}
"""
文档切片器 - 将长文档切分成适合向量化的片段
"""
from typing import List, Dict


class DocumentChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, title: str = "") -> List[Dict]:
        """将文本切分成多个片段"""
        if not text or not text.strip():
            return []

        chunks = []
        paragraphs = text.split('\n')
        current_chunk = ""
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para_size = len(para)

            if para_size > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'title': f"{title} (第{len(chunks) + 1}部分)" if title else f"片段{len(chunks) + 1}"
                    })
                    current_chunk = ""
                    current_size = 0

                for i in range(0, para_size, self.chunk_size - self.overlap):
                    chunk_para = para[i:i + self.chunk_size]
                    if chunk_para.strip():
                        chunks.append({
                            'content': chunk_para.strip(),
                            'title': f"{title} (第{len(chunks) + 1}部分)" if title else f"片段{len(chunks) + 1}"
                        })

            elif current_size + para_size > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'title': f"{title} (第{len(chunks) + 1}部分)" if title else f"片段{len(chunks) + 1}"
                    })
                if self.overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                    current_chunk = overlap_text + "\n" + para
                    current_size = len(current_chunk)
                else:
                    current_chunk = para
                    current_size = para_size
            else:
                if current_chunk:
                    current_chunk += "\n" + para
                else:
                    current_chunk = para
                current_size += para_size

        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'title': f"{title} (第{len(chunks) + 1}部分)" if title else f"片段{len(chunks) + 1}"
            })

        return chunks

    def chunk_document(self, document: Dict) -> List[Dict]:
        """
        切分文档（接收文档字典，返回切片列表）

        Args:
            document: 文档字典，包含 content, title, category, metadata 等字段

        Returns:
            切分后的片段列表
        """
        content = document.get('content', '')
        title = document.get('title', '')
        category = document.get('category', 'general')
        metadata = document.get('metadata', {})

        # 使用 chunk_text 进行切分
        chunks = self.chunk_text(content, title)

        # 为每个片段添加元数据
        for i, chunk in enumerate(chunks):
            chunk['category'] = category
            chunk['metadata'] = {
                **metadata,
                'original_title': title,
                'chunk_index': i,
                'total_chunks': len(chunks)
            }

        return chunks
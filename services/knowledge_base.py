import os
import re
import math
from collections import Counter
from config import KNOWLEDGE_DIR


class KnowledgeBase:
    """基于TF-IDF的轻量级知识库检索服务。"""

    def __init__(self):
        self.chunks: list[dict] = []  # {"title": str, "content": str, "source": str}
        self._idf: dict[str, float] = {}
        self._chunk_vectors: list[Counter] = []
        self._loaded = False

    def load(self):
        """加载所有知识库MD文件并分块。"""
        if self._loaded:
            return

        for fname in os.listdir(KNOWLEDGE_DIR):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(KNOWLEDGE_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            self._split_into_chunks(content, fname)

        self._build_index()
        self._loaded = True

    def _split_into_chunks(self, content: str, source: str):
        """按二级标题(##)分块，每块约300-800字。"""
        sections = re.split(r'\n(?=## )', content)
        for section in sections:
            section = section.strip()
            if not section:
                continue
            # 提取标题
            lines = section.split("\n", 1)
            title = lines[0].lstrip("#").strip()
            body = lines[1].strip() if len(lines) > 1 else ""

            # 如果内容太长，按三级标题再切
            if len(body) > 800:
                subsections = re.split(r'\n(?=### )', body)
                for sub in subsections:
                    sub = sub.strip()
                    if not sub:
                        continue
                    sub_lines = sub.split("\n", 1)
                    sub_title = sub_lines[0].lstrip("#").strip()
                    sub_body = sub_lines[1].strip() if len(sub_lines) > 1 else sub
                    self.chunks.append({
                        "title": f"{title} > {sub_title}" if sub_title != title else title,
                        "content": sub_body[:800],
                        "source": source,
                    })
            else:
                self.chunks.append({
                    "title": title,
                    "content": body,
                    "source": source,
                })

    def _tokenize(self, text: str) -> list[str]:
        """简单中文分词：按标点/空格切分 + 2-gram。"""
        # 移除markdown标记
        text = re.sub(r'[#*`\[\]()|\-_>]', ' ', text)
        # 按非中文/字母/数字字符切分
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}|[0-9]+(?:\.[0-9]+)?', text.lower())
        # 加入2-gram
        bigrams = []
        for w in words:
            if len(w) >= 4 and re.match(r'[\u4e00-\u9fff]+', w):
                for i in range(len(w) - 1):
                    bigrams.append(w[i:i + 2])
        return words + bigrams

    def _build_index(self):
        """构建TF-IDF索引。"""
        n = len(self.chunks)
        if n == 0:
            return

        # 文档频率
        df: Counter = Counter()
        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk["title"] + " " + chunk["content"]))
            for t in tokens:
                df[t] += 1
            self._chunk_vectors.append(Counter(self._tokenize(chunk["title"] + " " + chunk["content"])))

        # IDF
        self._idf = {t: math.log(n / (1 + freq)) for t, freq in df.items()}

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """检索最相关的知识块。"""
        self.load()
        if not self.chunks:
            return []

        query_tokens = Counter(self._tokenize(query))
        scores = []

        for i, chunk_tf in enumerate(self._chunk_vectors):
            score = 0.0
            for token, q_count in query_tokens.items():
                if token in chunk_tf:
                    tf = chunk_tf[token]
                    idf = self._idf.get(token, 0)
                    score += tf * idf * q_count
            scores.append((score, i))

        scores.sort(reverse=True)
        results = []
        for score, idx in scores[:top_k]:
            if score > 0:
                results.append(self.chunks[idx])
        return results

    def get_context_for_query(self, query: str, max_chars: int = 3000) -> str:
        """为对话查询生成知识库上下文字符串。"""
        results = self.search(query, top_k=5)
        if not results:
            return ""

        context_parts = []
        total = 0
        for r in results:
            snippet = f"【{r['title']}】\n{r['content']}"
            if total + len(snippet) > max_chars:
                break
            context_parts.append(snippet)
            total += len(snippet)

        return "\n\n---\n\n".join(context_parts)

    def get_all_topics(self) -> list[dict]:
        """获取所有知识主题（用于前端导航）。返回扁平列表。"""
        self.load()
        topics = []
        seen = set()
        for chunk in self.chunks:
            key = chunk["title"]
            if key not in seen:
                seen.add(key)
                topics.append({
                    "title": chunk["title"],
                    "source": chunk["source"].replace(".md", ""),
                })
        return topics


# 单例
knowledge_base = KnowledgeBase()

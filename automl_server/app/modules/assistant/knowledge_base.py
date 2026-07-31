"""Small local product knowledge base for assistant workflow guidance."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


KNOWLEDGE_DIRECTORY = Path(__file__).with_name("knowledge")
MAX_DOCUMENT_CHARS = 6000
MAX_SEARCH_LIMIT = 5


@dataclass(frozen=True)
class KnowledgeDocument:
    source: str
    title: str
    keywords: tuple[str, ...]
    content: str


class AssistantKnowledgeBase:
    """Loads markdown guidance at query time so operations docs can be updated with the app."""

    def __init__(self, directory: Path = KNOWLEDGE_DIRECTORY):
        self.directory = directory

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []
        bounded_limit = max(1, min(limit, MAX_SEARCH_LIMIT))
        query_terms = self._query_terms(normalized_query)
        ranked: list[tuple[int, KnowledgeDocument, list[str]]] = []
        for document in self._load_documents():
            searchable = f"{document.title} {' '.join(document.keywords)} {document.content}".lower()
            matched_terms = [term for term in query_terms if term in searchable]
            score = len(matched_terms)
            if normalized_query in searchable:
                score += 5
            score += sum(2 for keyword in document.keywords if keyword.lower() in normalized_query)
            if score > 0:
                ranked.append((score, document, matched_terms))
        ranked.sort(key=lambda item: (-item[0], item[1].source))
        return [
            {
                "source": document.source,
                "title": document.title,
                "matched_terms": matched_terms[:12],
                "content": document.content[:MAX_DOCUMENT_CHARS],
            }
            for _, document, matched_terms in ranked[:bounded_limit]
        ]

    def _load_documents(self) -> list[KnowledgeDocument]:
        if not self.directory.exists():
            return []
        documents: list[KnowledgeDocument] = []
        for path in sorted(self.directory.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            lines = text.splitlines()
            title = path.stem
            keywords: tuple[str, ...] = ()
            content_start = 0
            for index, line in enumerate(lines):
                if line.startswith("# ") and title == path.stem:
                    title = line[2:].strip()
                if line.lower().startswith("keywords:"):
                    keywords = tuple(item.strip().lower() for item in line.split(":", 1)[1].split(",") if item.strip())
                    content_start = index + 1
            content = "\n".join(lines[content_start:]).strip()
            documents.append(KnowledgeDocument(path.name, title, keywords, content))
        return documents

    @staticmethod
    def _query_terms(query: str) -> list[str]:
        terms = set(re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]{2,}", query))
        for alias, expansions in {
            "dpo": ("偏好", "二选一", "多选一", "chosen", "rejected"),
            "偏好": ("dpo", "chosen", "rejected"),
            "标注": ("annotation", "项目", "工作台"),
            "训练": ("task", "模型", "部署"),
            "部署": ("模型", "推理", "health"),
        }.items():
            if alias in query:
                terms.update(expansions)
        return sorted(terms, key=lambda term: (-len(term), term))

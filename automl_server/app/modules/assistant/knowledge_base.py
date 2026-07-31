"""Local product knowledge documents selected explicitly by the assistant model."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


KNOWLEDGE_DIRECTORY = Path(__file__).with_name("knowledge")
MAX_DOCUMENT_CHARS = 6000
MAX_DOCUMENTS_PER_READ = 5


@dataclass(frozen=True)
class KnowledgeDocumentDescriptor:
    source: str
    description: str


PRODUCT_KNOWLEDGE_DOCUMENTS = (
    KnowledgeDocumentDescriptor(
        source="dpo-annotation.md",
        description="DPO 偏好标注：适用场景、从零开始流程、JSONL 格式、校验失败和导出结果。",
    ),
    KnowledgeDocumentDescriptor(
        source="workspace-flows.md",
        description="工作台通用流程：数据集、标注项目、训练任务、模型部署和推理。",
    ),
)
PRODUCT_KNOWLEDGE_SOURCES = tuple(document.source for document in PRODUCT_KNOWLEDGE_DOCUMENTS)


@dataclass(frozen=True)
class KnowledgeDocument:
    source: str
    title: str
    content: str


class AssistantKnowledgeBase:
    """Loads markdown guidance at query time so operations docs can be updated with the app."""

    def __init__(self, directory: Path = KNOWLEDGE_DIRECTORY):
        self.directory = directory

    def read(self, sources: Iterable[str]) -> list[dict[str, Any]]:
        requested_sources = list(sources)
        if not requested_sources:
            return []
        if len(requested_sources) > MAX_DOCUMENTS_PER_READ:
            raise ValueError(f"一次最多读取 {MAX_DOCUMENTS_PER_READ} 份知识库文档")
        if len(set(requested_sources)) != len(requested_sources):
            raise ValueError("documents 不能包含重复文件")

        documents_by_source = {document.source: document for document in self._load_documents()}
        missing_sources = [source for source in requested_sources if source not in documents_by_source]
        if missing_sources:
            raise ValueError(f"知识库文档不存在：{', '.join(missing_sources)}")

        return [
            {
                "source": source,
                "title": documents_by_source[source].title,
                "content": documents_by_source[source].content[:MAX_DOCUMENT_CHARS],
            }
            for source in requested_sources
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
            if lines and lines[0].startswith("# "):
                title = lines[0][2:].strip()
            documents.append(KnowledgeDocument(path.name, title, text.strip()))
        return documents

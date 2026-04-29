"""
Local document collection for question-only project creation.

MVP scope:
- Read project-local seed documents from Data/
- Reuse extracted text from previous projects
- Rank candidates with a lightweight lexical score
"""

import hashlib
import json
import logging
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence
from urllib.parse import quote
from urllib.request import Request, urlopen

from ..config import Config
from ..utils.file_parser import FileParser
from .text_processor import TextProcessor


MAX_SOURCE_CHARS = 30_000
MIN_TOKEN_LENGTH = 2
MAX_WEB_CANDIDATES = 8
HTTP_TIMEOUT_SECONDS = 8
WIKIPEDIA_SEARCH_APIS = {
    "en": "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit={limit}",
    "ko": "https://ko.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit={limit}",
}
WIKIPEDIA_SUMMARY_APIS = {
    "en": "https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
    "ko": "https://ko.wikipedia.org/api/rest_v1/page/summary/{title}",
}

logger = logging.getLogger(__name__)
HTTP_HEADERS = {
    "User-Agent": "UngdrooFish/1.0 (+https://example.local)",
    "Accept": "application/json",
}


@dataclass
class CollectedDocument:
    title: str
    path: str
    source_type: str
    text: str
    score: float
    size: int

    def to_project_file(self) -> Dict[str, object]:
        return {
            "filename": self.title,
            "source": self.source_type,
            "path": self.path,
            "size": self.size,
            "score": round(self.score, 4),
            "auto_collected": True,
        }

    def to_seed_text(self) -> str:
        score = round(self.score, 4)
        return (
            f"=== Auto-collected source: {self.title} ===\n"
            f"Source type: {self.source_type}\n"
            f"Path: {self.path}\n"
            f"Relevance score: {score}\n\n"
            f"{self.text}"
        )


def collect_related_documents(
    query: str,
    max_documents: int = 8,
) -> List[CollectedDocument]:
    candidates = _load_candidates(query)
    if not candidates:
        return []

    query_tokens = _tokenize(query)
    scored = []
    for candidate in candidates:
        score = _score_document(query_tokens, query, candidate)
        scored.append(
            CollectedDocument(
                title=candidate["title"],
                path=candidate["path"],
                source_type=candidate["source_type"],
                text=candidate["text"],
                score=score,
                size=candidate["size"],
            )
        )

    positive = [doc for doc in scored if doc.score > 0]
    pool = positive if positive else scored

    pool.sort(
        key=lambda doc: (
            doc.score,
            1 if doc.source_type == "Data" else 0,
            min(doc.size, MAX_SOURCE_CHARS),
        ),
        reverse=True,
    )
    return pool[:max_documents]


def format_collected_documents(question: str, documents: Sequence[CollectedDocument]) -> str:
    lines = [
        "=== Prediction question ===",
        question.strip(),
        "",
        "=== Selected local sources ===",
    ]

    for idx, doc in enumerate(documents, 1):
        lines.append(
            f"{idx}. {doc.title} "
            f"(source={doc.source_type}, score={round(doc.score, 4)}, path={doc.path})"
        )

    lines.append("")
    lines.extend(doc.to_seed_text() for doc in documents)
    return "\n\n".join(lines)


def _load_candidates(query: str) -> List[Dict[str, object]]:
    raw_candidates = []
    raw_candidates.extend(_load_data_documents())
    raw_candidates.extend(_load_previous_project_documents())
    if not raw_candidates and query.strip():
        raw_candidates.extend(_load_web_documents(query))

    seen = set()
    deduped = []
    for candidate in raw_candidates:
        text = candidate["text"].strip()
        if not text:
            continue

        digest = hashlib.sha1(_normalize_for_hash(text).encode("utf-8", errors="ignore")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)

        candidate["text"] = text[:MAX_SOURCE_CHARS]
        deduped.append(candidate)

    return deduped


def _load_web_documents(query: str) -> List[Dict[str, object]]:
    docs: List[Dict[str, object]] = []
    seen_keys = set()

    for lang in ("ko", "en"):
        payload = _search_wikipedia(query, lang)
        for item in payload.get("query", {}).get("search", []):
            title = item.get("title", "").strip()
            key = f"{lang}:{title}"
            if not title or key in seen_keys:
                continue
            seen_keys.add(key)
            summary = _fetch_wikipedia_summary(title, lang)
            if not summary:
                continue
            docs.append(
                {
                    "title": title,
                    "path": f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "source_type": "Web",
                    "text": TextProcessor.preprocess_text(summary),
                    "size": len(summary),
                }
            )
    return docs


def _search_wikipedia(query: str, lang: str) -> Dict[str, object]:
    try:
        search_api = WIKIPEDIA_SEARCH_APIS.get(lang, WIKIPEDIA_SEARCH_APIS["en"])
        search_url = search_api.format(query=quote(query), limit=MAX_WEB_CANDIDATES)
        req = Request(search_url, headers=HTTP_HEADERS)
        with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("Web search fallback failed (%s): %s", lang, exc)
        return {}


def _fetch_wikipedia_summary(title: str, lang: str) -> str:
    try:
        summary_api = WIKIPEDIA_SUMMARY_APIS.get(lang, WIKIPEDIA_SUMMARY_APIS["en"])
        url = summary_api.format(title=quote(title))
        req = Request(url, headers=HTTP_HEADERS)
        with urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        extract = payload.get("extract", "") or ""
        description = payload.get("description", "") or ""
        combined = f"{title}\n{description}\n\n{extract}".strip()
        return combined[:MAX_SOURCE_CHARS]
    except Exception:
        return ""


def _load_data_documents() -> List[Dict[str, object]]:
    project_root = Path(__file__).resolve().parents[3]
    data_dir = project_root / "Data"
    if not data_dir.exists():
        return []

    docs = []
    for path in _iter_supported_files(data_dir):
        try:
            text = TextProcessor.preprocess_text(FileParser.extract_text(str(path)))
        except Exception:
            continue
        docs.append(
            {
                "title": path.name,
                "path": _relative_path(path, project_root),
                "source_type": "Data",
                "text": text,
                "size": path.stat().st_size,
            }
        )
    return docs


def _load_previous_project_documents() -> List[Dict[str, object]]:
    projects_dir = Path(Config.UPLOAD_FOLDER) / "projects"
    if not projects_dir.exists():
        return []

    docs = []
    project_root = Path(__file__).resolve().parents[3]
    for text_path in projects_dir.glob("proj_*/extracted_text.txt"):
        try:
            text = TextProcessor.preprocess_text(text_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not text or len(text) < 100:
            continue
        docs.append(
            {
                "title": f"{text_path.parent.name}/extracted_text.txt",
                "path": _relative_path(text_path, project_root),
                "source_type": "PreviousProject",
                "text": text,
                "size": text_path.stat().st_size,
            }
        )
    return docs


def _iter_supported_files(root: Path):
    allowed = {f".{ext}" for ext in Config.ALLOWED_EXTENSIONS}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in allowed:
            yield path


def _score_document(query_tokens: List[str], query: str, doc: Dict[str, object]) -> float:
    if not query_tokens:
        return 0.0

    title = str(doc["title"]).lower()
    text = str(doc["text"]).lower()
    searchable = f"{title}\n{text[:MAX_SOURCE_CHARS]}"
    doc_tokens = _tokenize(searchable)
    if not doc_tokens:
        return 0.0

    token_counts: Dict[str, int] = {}
    for token in doc_tokens:
        token_counts[token] = token_counts.get(token, 0) + 1

    unique_doc_tokens = set(doc_tokens)
    overlap = set(query_tokens) & unique_doc_tokens
    if not overlap:
        return _substring_score(query, searchable)

    weighted_overlap = 0.0
    for token in overlap:
        tf = token_counts.get(token, 0)
        title_boost = 2.5 if token in title else 1.0
        weighted_overlap += (1.0 + math.log1p(tf)) * title_boost

    coverage = len(overlap) / max(len(set(query_tokens)), 1)
    density = weighted_overlap / math.sqrt(max(len(doc_tokens), 1))
    return round(weighted_overlap + (coverage * 5.0) + density, 6)


def _substring_score(query: str, searchable: str) -> float:
    compact_query = re.sub(r"\s+", "", query.lower())
    compact_doc = re.sub(r"\s+", "", searchable.lower())
    if len(compact_query) < 4:
        return 0.0

    hits = 0
    for size in (6, 5, 4):
        grams = {compact_query[i : i + size] for i in range(0, max(len(compact_query) - size + 1, 0))}
        hits += sum(1 for gram in grams if gram and gram in compact_doc) * size
    return float(hits) / 10.0


def _tokenize(text: str) -> List[str]:
    tokens = []
    for token in re.findall(r"[\w가-힣]+", text.lower()):
        if len(token) >= MIN_TOKEN_LENGTH and not token.isdigit():
            tokens.append(token)
    return tokens


def _normalize_for_hash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:MAX_SOURCE_CHARS]


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)

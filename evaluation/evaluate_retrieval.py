"""Evaluate vector and hybrid retrieval against the local policy question set.

The evaluator uses a deterministic local hash embedding model, so it does not
download models or call external services. It reports independent measurements
for each configuration and intentionally does not select a winner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.chunking.fixed_chunker import Chunk, ChunkerConfig, chunk_policy_document
from rag.embeddings.embedding_service import EmbeddingService
from rag.ingestion.document_loader import load_policy_documents
from rag.preprocessing.cleaner import clean_policy_document
from rag.retrieval.hybrid_retriever import HybridRetriever
from rag.retrieval.keyword_retriever import KeywordRetriever
from rag.retrieval.reranker import Reranker
from rag.retrieval.retriever import VectorRetriever
from rag.retrieval.vector_store import VectorStore


DEFAULT_TOP_K = 5
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "evaluation" / "retrieval_results.json"
TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)?", re.IGNORECASE)
EVALUATION_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from",
    "how", "i", "in", "is", "it", "of", "on", "or", "that", "the", "this",
    "to", "what", "when", "where", "which", "why", "with", "you", "your",
}


class DeterministicEmbeddingModel:
    """Small deterministic embedding model used only by this evaluator."""

    def __init__(self, dimension: int = 128) -> None:
        self._dimension = dimension

    def get_sentence_embedding_dimension(self) -> int:
        return self._dimension

    def encode(
        self,
        texts: Sequence[str],
        *,
        normalize_embeddings: bool,
        batch_size: int,
    ) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self._dimension
            for token in TOKEN_PATTERN.findall(text.casefold()):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % self._dimension
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[index] += sign

            if normalize_embeddings:
                norm = math.sqrt(sum(value * value for value in vector))
                if norm:
                    vector = [value / norm for value in vector]
            vectors.append(vector)
        return vectors


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError(f"Evaluation dataset contains no records: {path}")
    return records


def _build_chunks(policy_root: Path) -> list[Chunk]:
    documents = load_policy_documents(policy_root)
    chunks: list[Chunk] = []
    config = ChunkerConfig(chunk_size=500, overlap=50)
    for document in documents:
        cleaned = clean_policy_document(document.text)
        metadata = document.metadata.to_dict()
        chunks.extend(
            chunk_policy_document(
                cleaned.text,
                policy_id=document.metadata.policy_id,
                source=document.metadata.source,
                metadata=metadata,
                config=config,
            )
        )
    if not chunks:
        raise ValueError(f"No chunks generated from policy directory: {policy_root}")
    return chunks


def _build_retrievers(
    chunks: Sequence[Chunk],
    top_k: int,
) -> tuple[VectorRetriever, HybridRetriever]:
    embedding_service = EmbeddingService(model=DeterministicEmbeddingModel())
    vector_retriever = VectorRetriever(
        embedding_service=embedding_service,
        vector_store=VectorStore(default_top_k=top_k),
        top_k=top_k,
    )
    vector_retriever.index_chunks(chunks)

    keyword_retriever = KeywordRetriever(chunks=chunks, top_k=top_k)
    hybrid_retriever = HybridRetriever(
        keyword_retriever,
        vector_retriever,
        top_k=top_k,
    )
    return vector_retriever, hybrid_retriever


def _text(candidate: Any) -> str:
    return str(getattr(candidate, "text", ""))


def _policy_id(candidate: Any) -> str | None:
    metadata = getattr(candidate, "metadata", {}) or {}
    value = metadata.get("policy_id")
    return str(value) if value is not None else None


def _evidence_metrics(
    candidates: Sequence[Any],
    expected_policy_id: str | None,
    expected_evidence: Sequence[str],
) -> dict[str, Any]:
    combined_text = "\n".join(_text(candidate).casefold() for candidate in candidates)
    matched_evidence = [
        evidence
        for evidence in expected_evidence
        if evidence.casefold() in combined_text
    ]

    if expected_evidence:
        evidence_hit_rate = len(matched_evidence) / len(expected_evidence)
    else:
        evidence_hit_rate = 1.0 if not candidates else 0.0

    if expected_policy_id:
        relevant = [candidate for candidate in candidates if _policy_id(candidate) == expected_policy_id]
        expected_policy_retrieved = any(_policy_id(candidate) == expected_policy_id for candidate in candidates)
    else:
        relevant = []
        expected_policy_retrieved = not candidates

    if candidates:
        retrieval_relevance = len(relevant) / len(candidates)
    else:
        retrieval_relevance = 1.0 if expected_policy_id is None else 0.0

    return {
        "evidence_hit_rate": round(evidence_hit_rate, 4),
        "evidence_matches": matched_evidence,
        "retrieval_relevance": round(retrieval_relevance, 4),
        "expected_policy_retrieved": expected_policy_retrieved,
        "expected_policy_retrieval_rate": 1.0 if expected_policy_retrieved else 0.0,
    }


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(text.casefold())
        if token not in EVALUATION_STOPWORDS and len(token) > 1
    }


def _relevant_candidates(query: str, candidates: Sequence[Any]) -> list[Any]:
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    return [candidate for candidate in candidates if _tokens(_text(candidate)) & query_tokens]


def _build_answer(query: str, candidates: Sequence[Any]) -> tuple[str, bool, list[str]]:
    """Create a deterministic answer/refusal for answer-level evaluation."""
    relevant = _relevant_candidates(query, candidates)
    if not relevant:
        return "Insufficient policy evidence to answer this question.", False, []

    evidence_parts: list[str] = []
    citations: list[str] = []
    for candidate in relevant:
        text = _text(candidate).strip()
        if text:
            evidence_parts.append(text)
        policy_id = _policy_id(candidate)
        if policy_id and policy_id not in citations:
            citations.append(policy_id)
    answer = " ".join(evidence_parts)
    if citations:
        answer = f"{answer} Sources: {', '.join(citations)}."
    return answer, True, citations


def _answer_metrics(
    query: str,
    answer: str,
    supported: bool,
    expected_supported: bool,
    expected_evidence: Sequence[str],
    expected_policy_id: str | None,
    candidates: Sequence[Any],
    citations: Sequence[str],
) -> dict[str, Any]:
    answer_tokens = _tokens(answer) if supported else set()
    query_tokens = _tokens(query)
    retrieved_text = "\n".join(_text(candidate) for candidate in candidates)
    retrieved_tokens = _tokens(retrieved_text)

    answer_relevance = (
        len(answer_tokens & query_tokens) / len(query_tokens)
        if supported and query_tokens
        else 0.0
    )
    groundedness = (
        len(answer_tokens & retrieved_tokens) / len(answer_tokens)
        if supported and answer_tokens
        else (1.0 if not supported and not candidates else 0.0)
    )
    if expected_policy_id:
        citation_source_coverage = 1.0 if expected_policy_id in citations else 0.0
    else:
        citation_source_coverage = 1.0 if not citations else 0.0

    return {
        "answer_relevance": round(answer_relevance, 4),
        "groundedness": round(groundedness, 4),
        "citation_source_coverage": round(citation_source_coverage, 4),
        "refusal_correctness": 1.0 if supported == expected_supported else 0.0,
        "expected_supported": expected_supported,
        "actual_supported": supported,
        "expected_evidence_count": len(expected_evidence),
    }


def _evaluate_configuration(
    name: str,
    retriever: Any,
    records: Sequence[Mapping[str, Any]],
    top_k: int,
    *,
    reranker: Reranker | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for record in records:
        query = str(record["question"])
        filters = record.get("filters") or None
        started = perf_counter()
        candidates = retriever.retrieve(query, top_k=top_k, filters=filters)
        if reranker is not None:
            candidates = reranker.rerank(query, candidates, top_k=top_k)
        latency_ms = (perf_counter() - started) * 1000

        answer, supported, citations = _build_answer(query, candidates)

        metrics = _evidence_metrics(
            candidates,
            record.get("expected_policy_id"),
            record.get("expected_evidence", []),
        )
        metrics.update(
            _answer_metrics(
                query,
                answer,
                supported,
                bool(record.get("expected_supported")),
                record.get("expected_evidence", []),
                record.get("expected_policy_id"),
                candidates,
                citations,
            )
        )
        results.append(
            {
                "question_id": record["question_id"],
                "query": query,
                "configuration": name,
                "answer": answer,
                "supported": supported,
                "refused": not supported,
                "retrieved_chunk_ids": [candidate.chunk_id for candidate in candidates],
                "retrieved_policy_ids": [_policy_id(candidate) for candidate in candidates],
                "retrieved_evidence": [
                    {
                        "chunk_id": candidate.chunk_id,
                        "policy_id": _policy_id(candidate),
                        "text": _text(candidate),
                        "score": round(float(candidate.score), 6),
                    }
                    for candidate in candidates
                ],
                "citations": list(citations),
                "expected_evidence": record.get("expected_evidence", []),
                "expected_policy_id": record.get("expected_policy_id"),
                "expected_supported": record.get("expected_supported"),
                "category": record.get("category"),
                "filters": record.get("filters", {}),
                "latency_ms": round(latency_ms, 4),
                "metrics": metrics,
            }
        )

    return {
        "name": name,
        "top_k": top_k,
        "reranking_enabled": reranker is not None,
        "results": results,
        "summary": _summarize(results),
    }


def _summarize(results: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not results:
        return {
            "evidence_hit_rate": 0.0,
            "retrieval_relevance": 0.0,
            "expected_policy_retrieval_rate": 0.0,
            "answer_relevance": 0.0,
            "groundedness": 0.0,
            "citation_source_coverage": 0.0,
            "refusal_correctness": 0.0,
            "average_latency_ms": 0.0,
        }
    metric_names = (
        "evidence_hit_rate",
        "retrieval_relevance",
        "expected_policy_retrieval_rate",
        "answer_relevance",
        "groundedness",
        "citation_source_coverage",
        "refusal_correctness",
    )
    summary = {
        metric: round(
            sum(float(result["metrics"][metric]) for result in results) / len(results),
            4,
        )
        for metric in metric_names
    }
    summary["average_latency_ms"] = round(
        sum(float(result["latency_ms"]) for result in results) / len(results),
        4,
    )
    return summary


def evaluate(
    *,
    dataset_path: Path,
    policy_root: Path,
    output_path: Path,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """Evaluate both retrieval configurations and write JSON results."""
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")

    records = _load_dataset(dataset_path)
    chunks = _build_chunks(policy_root)
    vector_retriever, hybrid_retriever = _build_retrievers(chunks, top_k)

    report = {
        "dataset_id": json.loads(dataset_path.read_text(encoding="utf-8")).get("dataset_id"),
        "dataset_path": str(dataset_path),
        "policy_root": str(policy_root),
        "chunk_count": len(chunks),
        "configurations": [
            _evaluate_configuration("vector", vector_retriever, records, top_k),
            _evaluate_configuration(
                "hybrid_reranked",
                hybrid_retriever,
                records,
                top_k,
                reranker=Reranker(),
            ),
        ],
        "qualitative_observations": [
            "Metrics are measured independently for each configuration and are not used to declare a winner.",
            "Answer-level scores use the deterministic evaluator answer built from retrieved evidence; they are not measurements from an external LLM.",
            "Latency includes retrieval and optional reranking, but excludes corpus loading and index construction.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "data" / "evaluation" / "rag_evaluation_dataset.json",
    )
    parser.add_argument(
        "--policy-root",
        type=Path,
        default=PROJECT_ROOT / "data" / "policies",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    report = evaluate(
        dataset_path=args.dataset,
        policy_root=args.policy_root,
        output_path=args.output,
        top_k=args.top_k,
    )
    print(f"Evaluated {len(report['configurations'])} configurations across {len(report['configurations'][0]['results'])} questions.")
    print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()
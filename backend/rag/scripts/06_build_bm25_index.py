import json
import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from core.artifacts import sha256_file, write_manifest
from core.config import settings
from retrieval.index_text import doc_full_text

BM25_INDEX_FILE = settings.indexes_dir / "bm25_index.pkl"


def load_jsonl(path: Path) -> list[dict]:
    docs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def main() -> None:
    if not settings.rag_documents_file.exists():
        raise FileNotFoundError(
            f"RAG documents file not found: {settings.rag_documents_file}. "
            "Run scripts\\05_build_rag_documents.py or export_rag_knowledge_base_to_corpus.py first."
        )

    settings.indexes_dir.mkdir(parents=True, exist_ok=True)

    docs = load_jsonl(settings.rag_documents_file)
    print(f"Loaded documents: {len(docs)}")

    tokenized_corpus: list[list[str]] = []
    full_texts: list[str] = []

    for doc in docs:
        tokens, full_text = doc_full_text(doc)
        tokenized_corpus.append(tokens)
        full_texts.append(full_text)

    bm25 = BM25Okapi(tokenized_corpus)

    min_df = 1 if len(docs) < 40 else 2
    tfidf_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=40000,
        min_df=min_df,
        sublinear_tf=True,
    )
    X = tfidf_vectorizer.fit_transform(full_texts)
    X_norm = normalize(X)

    payload: dict = {
        "docs": docs,
        "tokenized_corpus": tokenized_corpus,
        "bm25": bm25,
        "tfidf_vectorizer": tfidf_vectorizer,
        "tfidf_X_norm": X_norm,
    }

    with BM25_INDEX_FILE.open("wb") as f:
        pickle.dump(payload, f)

    corpus_sha = sha256_file(settings.rag_documents_file)
    bm25_sha = sha256_file(BM25_INDEX_FILE)

    write_manifest(
        corpus_path=settings.rag_documents_file,
        corpus_sha256=corpus_sha,
        bm25_index_path=BM25_INDEX_FILE,
        bm25_sha256=bm25_sha,
        document_count=len(docs),
        extra={"tfidf_enabled": True, "tfidf_min_df": min_df},
    )

    report = {
        "index_file": str(BM25_INDEX_FILE),
        "document_count": len(docs),
        "avg_tokens": round(
            sum(len(tokens) for tokens in tokenized_corpus) / max(len(tokenized_corpus), 1),
            2,
        ),
        "tfidf_features": int(X.shape[1]),
        "corpus_sha256": corpus_sha,
        "bm25_sha256": bm25_sha,
    }

    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.reports_dir / "build_bm25_index_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved BM25 + TF-IDF index: {BM25_INDEX_FILE}")
    print(f"Saved manifest: {settings.indexes_dir / 'rag_artifacts_manifest.json'}")
    print(f"Saved report: {report_path}")
    print(f"Average tokens/doc: {report['avg_tokens']}")


if __name__ == "__main__":
    main()

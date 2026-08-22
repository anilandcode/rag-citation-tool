"""CLI entry point for RAG Citation Tool."""

import argparse
import json
import sys

from src.ingestion.pipeline import run_ingestion
from src.retrieval.pipeline import build_full_retrieval_pipeline
from src.generation.pipeline import (
    build_query_engine,
    verify_citations,
)
from src.evaluation.ragas_harness import run_ragas_evaluation


def _postprocessors(reranker):
    return [reranker] if reranker is not None else []


def cmd_ingest(args):
    nodes = run_ingestion(input_dir=args.input_dir)
    print(
        f"Ingested {len(nodes)} chunks from "
        f"{len({n.metadata.get('source') for n in nodes})} documents"
    )


def cmd_query(args):
    nodes = run_ingestion(input_dir=args.input_dir)
    _, hybrid_retriever, reranker = build_full_retrieval_pipeline(nodes)
    qe = build_query_engine(
        retriever=hybrid_retriever,
        node_postprocessors=_postprocessors(reranker),
    )
    response = qe.query(args.question)
    print(str(response))


def cmd_eval(args):
    """Run RAGAS on a pre-filled dataset OR pipeline+RAGAS via run_full_eval helper."""
    with open(args.dataset, "r") as f:
        data = json.load(f)

    # If rows already have answers+contexts, score only.
    if data and "answer" in data[0] and "contexts" in data[0]:
        results = run_ragas_evaluation(data)
        print(json.dumps(results, indent=2))
        return

    # Golden Q/A only → full pipeline then RAGAS
    from src.generation.pipeline import extract_citations

    nodes = run_ingestion(input_dir=args.input_dir)
    _, hybrid_retriever, reranker = build_full_retrieval_pipeline(nodes)
    qe = build_query_engine(
        retriever=hybrid_retriever,
        node_postprocessors=_postprocessors(reranker),
    )
    eval_data = []
    for item in data:
        if item.get("expect_refusal"):
            continue
        question = item["question"]
        ground_truth = item.get("ground_truth", "")
        response = qe.query(question)
        answer = str(response)
        contexts = [n.text for n in response.source_nodes]
        eval_data.append(
            {
                "question": question,
                "ground_truth": ground_truth,
                "answer": answer,
                "contexts": contexts,
                "citations": [
                    {"source": c.source, "page": c.page}
                    for c in extract_citations(answer)
                ],
            }
        )
    results = run_ragas_evaluation(eval_data)
    print(json.dumps({"metrics": results, "n": len(eval_data)}, indent=2))


def cmd_verify(args):
    nodes = run_ingestion(input_dir=args.input_dir)
    _, hybrid_retriever, reranker = build_full_retrieval_pipeline(nodes)
    qe = build_query_engine(
        retriever=hybrid_retriever,
        node_postprocessors=_postprocessors(reranker),
    )
    response = qe.query(args.question)
    report = verify_citations(str(response), response.source_nodes)
    print(
        f"Citations: {report.total_citations}, Verified: {report.verified}, "
        f"Accuracy: {report.accuracy:.2%}, Refusal: {report.is_refusal}"
    )


def main():
    parser = argparse.ArgumentParser(prog="rag-cite", description="RAG Citation Tool")
    subparsers = parser.add_subparsers(dest="command")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument("--input-dir", default="./data")
    ingest_parser.set_defaults(func=cmd_ingest)

    query_parser = subparsers.add_parser("query", help="Query the RAG pipeline")
    query_parser.add_argument("question")
    query_parser.add_argument("--input-dir", default="./data")
    query_parser.set_defaults(func=cmd_query)

    eval_parser = subparsers.add_parser(
        "eval",
        help="Run evaluation (pre-filled RAGAS rows, or golden Qs + pipeline)",
    )
    eval_parser.add_argument("dataset")
    eval_parser.add_argument(
        "--input-dir",
        default="./data/demo",
        help="Corpus when dataset has questions only",
    )
    eval_parser.set_defaults(func=cmd_eval)

    verify_parser = subparsers.add_parser("verify", help="Query and verify citations")
    verify_parser.add_argument("question")
    verify_parser.add_argument("--input-dir", default="./data")
    verify_parser.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()

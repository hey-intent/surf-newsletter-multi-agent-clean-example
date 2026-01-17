"""Surf Newsletter - AI-powered newsletter generation with multi-agent orchestration.

Structure:
- core/      : Foundational components (models, config, personas, llm)
- agents/    : AI agents (SelectorAgent, GraderAgent)
- compute/   : Non-LLM operations (fetcher, aggregator, renderer)
- pipelines/ : LangGraph orchestration (state, nodes, graph, orchestrator)
"""

from src.pipelines.newsletter_orchestrator import NewsletterPipeline, run_pipeline

__all__ = [
    "NewsletterPipeline",
    "run_pipeline",
]

__version__ = "0.2.0"

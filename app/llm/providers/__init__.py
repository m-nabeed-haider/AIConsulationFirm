"""Concrete LLM provider implementations.

Each module in this package adapts one specific backend (e.g. Ollama)
to the :class:`app.llm.base.BaseLLM` contract. Application code should
not import from this package directly — providers are constructed via
:class:`app.llm.factory.LLMFactory`.
"""

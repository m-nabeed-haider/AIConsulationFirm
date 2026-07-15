# AI Consulting Firm

A fully local, multi-agent AI system that simulates an AI consulting company —
built on Python, designed to eventually run on Ollama and LangGraph.

> **Status:** Module 0 — Project Foundation. This repository currently
> contains only the project scaffold (structure, configuration, logging,
> and tests). No agents, workflows, or AI functionality have been
> implemented yet.

---

## Project Overview

AI Consulting Firm is a locally-run platform that will simulate a team of
specialized AI "employees" collaborating to analyze a business or software
idea submitted by a user. The long-term goal is a system where multiple
agents — each with a distinct role — work together to produce a coherent,
multi-perspective consulting deliverable, entirely on local infrastructure.

## Vision

To build a private, self-hosted alternative to a traditional consulting
engagement: a small AI "firm" that can take a raw idea and return a
structured, well-reasoned set of analyses, without relying on external
cloud AI services.

## Goals

- Establish a clean, modular, and testable project foundation.
- Incrementally introduce multi-agent orchestration in future modules.
- Keep every module independently reviewable and independently useful.
- Favor clarity and maintainability over premature complexity.
- Run entirely on local infrastructure (local LLMs via Ollama).

## Future Architecture (High Level)

> The following describes **planned, not implemented** architecture. It is
> included to orient contributors; none of it exists in the current
> codebase.

The system is expected to evolve into a multi-agent architecture where a
supervising agent coordinates specialized agents, each responsible for a
distinct area of analysis:

- **CEO / Supervisor** — coordinates the overall workflow and delegates work.
- **Project Manager** — tracks scope, tasks, and deliverables.
- **Research Analyst** — gathers and synthesizes market information.
- **Business Analyst** — evaluates business viability.
- **Technical Architect** — proposes system/technical designs.
- **Financial Analyst** — produces financial projections and analysis.
- **Software Engineer** — drafts implementation-level proposals.
- **Documentation Writer** — compiles findings into readable reports.
- **Reviewer** — critiques and validates outputs from other agents.
- **Evaluator** — scores and benchmarks overall output quality.

Orchestration between agents is planned to be built with **LangGraph**, with
**Ollama** providing local model inference. Persistent and semantic memory
(likely a vector database) will allow agents to retain and retrieve context
across a session. None of this exists yet — see [Development Roadmap](#development-roadmap).

## Folder Structure

```
ai-consulting-firm/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   │
│   ├── core/                   # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── config.py           # Typed environment configuration
│   │   ├── constants.py        # Static application constants
│   │   └── logger.py           # Centralized Loguru configuration
│   │
│   ├── agents/                 # (reserved) AI agent implementations
│   ├── llm/                    # (reserved) LLM client integrations
│   ├── orchestration/          # (reserved) Multi-agent workflow orchestration
│   ├── memory/                 # (reserved) Agent memory systems
│   ├── tools/                  # (reserved) Agent tools
│   ├── api/                    # (reserved) FastAPI routers/endpoints
│   ├── services/               # (reserved) Application service layer
│   ├── schemas/                # (reserved) Pydantic data models
│   └── utils/                  # (reserved) Shared helper utilities
│
├── docs/                       # Project documentation
├── tests/                      # Automated tests
├── logs/                       # Runtime log output (git-ignored)
├── reports/                    # Generated reports (git-ignored)
├── docker/                     # Containerization assets
├── scripts/                    # Developer/utility scripts
│
├── .env.example                # Environment variable template
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Tech Stack

**Currently in use (Module 0):**

- Python 3.12
- Pydantic / Pydantic Settings — configuration management
- Loguru — logging
- Pytest — testing
- Black, isort, mypy — code quality tooling

**Planned for future modules:**

- FastAPI — HTTP API layer
- LangGraph — multi-agent orchestration
- Ollama — local LLM inference
- A vector database — semantic memory (specific choice TBD)

## Installation

**Prerequisites:** Python 3.12+

```bash
# Clone the repository
git clone <repository-url>
cd ai-consulting-firm

# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your local environment file
cp .env.example .env
```

## Running the Project

```bash
python -m app.main
```

Expected output:

```
AI Consulting Firm initialized successfully.
```

Running the tests:

```bash
pytest
```

## Development Roadmap

| Module | Name | Scope |
|--------|------|-------|
| 0 | Project Foundation | Project scaffold, configuration, logging, tests *(this module)* |
| 1 | Future | Core domain schemas and data contracts |
| 2 | Future | LLM client integration (Ollama) |
| 3 | Future | Single-agent execution pipeline |
| 4 | Future | Multi-agent orchestration (LangGraph) |
| 5 | Future | Memory systems |
| 6 | Future | API layer (FastAPI) |
| 7 | Future | Reporting and output generation |

Exact module boundaries and ordering are subject to change as the project
evolves.

## Future Modules

Planned areas of future work include agent implementations, orchestration
workflows, memory and retrieval systems, tool integrations, and an API
layer. See [`docs/10_Future_Work.md`](docs/10_Future_Work.md) for details as
they are documented.

## Contribution Guidelines

- Follow the existing project structure; place new code in the appropriate
  package rather than introducing ad hoc modules.
- Adhere to PEP 8, use type hints, and write Google-style docstrings.
- Keep functions small and single-purpose (SOLID, DRY, KISS).
- Run `black`, `isort`, and `mypy` before submitting changes.
- Add or update tests for any new behavior.
- Keep each module scoped to its stated objective — avoid introducing
  functionality from future modules ahead of schedule.

## License

This project is licensed under the terms of the [MIT License](LICENSE).

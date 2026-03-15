# KeplAI Implementation Plan

**Date:** 2026-03-15
**Approach:** Full-Stack Incremental (Vertical Slices)
**Strategy:** Each phase delivers a working end-to-end slice (SDK + API + UI)

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | SDK-first, FastAPI wraps SDK, React frontend | SDK is independently usable; API is an optional HTTP layer |
| LLM Provider | OpenAI SDK initially, LiteLLM later | Simplicity first; structured outputs work well with OpenAI |
| Vector Store | Qdrant with abstract interface | User preference; ABC allows swapping to any vector DB |
| Graph Viz | Cytoscape.js or react-force-graph | Whichever fits best during Phase 4 |
| Graph Engine | Apache Jena Fuseki via Docker | Per PRD; zero-config for end users |
| Frontend | React + Vite + TypeScript | Per user spec |
| Backend | FastAPI | Per user spec |

---

## Project Structure

```
keplai/
├── pyproject.toml
├── src/
│   └── keplai/                   # Python SDK (core library)
│       ├── __init__.py           # exports KeplAI class
│       ├── engine.py             # JenaEngine (Docker lifecycle)
│       ├── graph.py              # KeplAI main class
│       ├── ontology.py           # OntologyManager
│       ├── extractor.py          # AI triple extraction
│       ├── disambiguator.py      # Entity resolution
│       ├── nlq.py                # NL2SPARQL
│       ├── vectorstore/          # Abstract vector store interface
│       │   ├── base.py           # ABC
│       │   └── qdrant.py         # Qdrant implementation
│       └── config.py             # Settings, LLM config
├── api/                          # FastAPI layer
│   ├── main.py
│   ├── routers/
│   │   ├── graph.py
│   │   ├── ontology.py
│   │   ├── extraction.py
│   │   └── query.py
│   ├── schemas.py                # Pydantic request/response models
│   └── dependencies.py          # KeplAI instance injection
├── frontend/                     # React + Vite + TS
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/                  # API client layer
│   │   ├── hooks/
│   │   └── types/
│   └── (standard Vite scaffold)
├── docker/                       # Fuseki config templates
│   └── fuseki-config.ttl
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
    └── plans/
```

---

## Phase 1: Engine Management + CRUD Foundation

**Goal:** Spin up Fuseki via Docker, add/find/delete triples, expose via API, display in a basic UI shell.

### SDK (`src/keplai/`)

- **`engine.py` — `JenaEngine` class**
  - Use Docker Python SDK to pull `stain/jena-fuseki` image
  - Generate `fuseki-config.ttl` with OWL reasoning enabled
  - Start/stop containers programmatically
  - Health check polling (wait for Fuseki to be ready)
  - Volume mounting for TDB2 data persistence
  - Configurable port, dataset name, container name

- **`graph.py` — `KeplAI` main class**
  - `KeplAI.start(engine="docker", reasoner="OWL")` — class method, provisions engine, returns instance
  - `.stop()` — graceful shutdown, data persists via Docker volumes
  - `.add(subject, predicate, object)` — insert a triple via SPARQL UPDATE
  - `.find(subject=None, predicate=None, object=None)` — query triples with optional filters via SPARQL SELECT
  - `.delete(subject, predicate, object)` — remove a triple via SPARQL UPDATE
  - `.get_all_triples()` — dump all triples

- **`config.py` — Settings**
  - Fuseki image name, port, dataset name
  - Base namespace URI (`http://keplaai.io/entity/`, `http://keplaai.io/ontology/`)
  - Configurable via environment variables or constructor args

- **Namespace management (within `graph.py`)**
  - Auto-map plain strings to URIs: `"Mehdi"` → `<http://keplaai.io/entity/Mehdi>`
  - Auto-detect if object is a literal (string, int, float, date) or entity (URI)
  - Use `rdflib` for URI construction and validation

### API (`api/`)

- **`main.py`** — FastAPI app with lifespan handler (start/stop KeplAI engine)
- **`dependencies.py`** — Dependency injection for the KeplAI instance
- **`routers/graph.py`**
  - `POST /api/graph/triples` — add a triple
  - `GET /api/graph/triples` — query triples (optional query params: subject, predicate, object)
  - `DELETE /api/graph/triples` — remove a triple
  - `GET /api/graph/status` — engine health check
  - `GET /api/graph/triples/all` — get all triples
- **`schemas.py`** — Pydantic models for Triple (subject, predicate, object), StatusResponse, etc.

### Frontend (`frontend/`)

- Vite + React + TS project scaffold
- **Layout shell** — sidebar navigation, header with app title, main content area
- **Status indicator** — engine health badge in header (green/red dot)
- **Triples page**
  - Table view of all triples (subject, predicate, object columns)
  - Add triple form (3 input fields + submit)
  - Delete button per row
  - Search/filter inputs
- **API client layer** — axios or fetch wrapper with base URL config, typed responses

### Tests

- Unit tests for namespace mapping (string → URI, literal detection)
- Unit tests for SPARQL query generation
- Integration test: start engine → add triple → find it → delete it → verify gone → stop engine

### Deliverable

You can run `KeplAI.start()` in Python, add triples, see them in the browser table, delete them, and shut down cleanly. The Fuseki container persists data across restarts.

---

## Phase 2: Ontology Management

**Goal:** Define OWL classes and properties, store them in Fuseki, manage via API, visualize in UI.

### SDK (`src/keplai/`)

- **`ontology.py` — `OntologyManager` class**
  - `define_class(name)` — create an OWL Class (e.g., `Person`, `Company`)
  - `define_property(name, domain, range)` — create an OWL ObjectProperty or DatatypeProperty
  - `get_classes()` — list all defined classes
  - `get_properties()` — list all defined properties with domain/range
  - `get_schema()` — return full ontology as structured dict (used later by AI extractor)
  - `remove_class(name)` / `remove_property(name)` — delete from ontology
  - Store ontology triples in Fuseki using `rdfs:Class`, `owl:ObjectProperty`, `rdfs:domain`, `rdfs:range`

- **Update `graph.py`**
  - Expose `graph.ontology` property returning the `OntologyManager`
  - Validate triples against ontology when in strict mode (optional, warn if predicate not defined)

### API (`api/`)

- **`routers/ontology.py`**
  - `POST /api/ontology/classes` — define a class
  - `GET /api/ontology/classes` — list all classes
  - `DELETE /api/ontology/classes/{name}` — remove a class
  - `POST /api/ontology/properties` — define a property (name, domain, range)
  - `GET /api/ontology/properties` — list all properties
  - `DELETE /api/ontology/properties/{name}` — remove a property
  - `GET /api/ontology/schema` — full schema dump

### Frontend (`frontend/`)

- **Ontology page**
  - Classes panel — list of defined classes, add/delete
  - Properties panel — list of properties with domain→range, add/delete
  - Visual schema diagram — simple node-edge view showing classes connected by properties (lightweight, no full graph viz yet)
- Update sidebar nav with Ontology link

### Tests

- Unit tests for OWL triple generation (class definition → correct RDF)
- Unit tests for property domain/range validation
- Integration test: define ontology → verify in Fuseki via SPARQL → retrieve via API

### Deliverable

Developer can define `Person`, `Company`, `founded(Person→Company)` via Python or the UI, and see the schema visualized. Ontology persists in Fuseki.

---

## Phase 3: AI Extraction + Entity Resolution

**Goal:** Extract triples from text using LLM, resolve duplicate entities, expose via API, manage in UI.

### SDK (`src/keplai/`)

- **`extractor.py` — `AIExtractor` class**
  - `extract(text, mode="strict"|"open")` — returns list of extracted triples
  - **Strict mode:**
    - Fetch current ontology via `OntologyManager.get_schema()`
    - Convert OWL schema to JSON Schema / Pydantic model dynamically
    - Send to OpenAI with structured outputs (response_format) forcing compliance
    - LLM can only use defined classes and properties
  - **Open mode:**
    - LLM freely extracts entities and relationships
    - New classes/predicates are created on the fly
  - Prompt engineering: system prompt with clear triple extraction instructions, few-shot examples

- **`disambiguator.py` — `EntityDisambiguator` class**
  - Uses the abstract vector store interface
  - On each extracted entity:
    1. Embed the entity name
    2. Search vector store for similar existing entities
    3. If similarity > configurable threshold (default 0.90), map to existing URI
    4. If no match, create new entity and store embedding
  - `resolve(entity_name)` → returns canonical URI
  - `get_all_entities()` → list all known entities with embeddings

- **`vectorstore/base.py` — `VectorStore` ABC**
  - `add(id, text, metadata)` — store an embedding
  - `search(text, top_k, threshold)` — similarity search
  - `delete(id)` — remove an embedding
  - `list_all()` — return all stored items

- **`vectorstore/qdrant.py` — `QdrantVectorStore`**
  - Implements ABC using `qdrant-client`
  - Uses Qdrant's local mode (in-memory or local file) for zero-config
  - Embedding via OpenAI `text-embedding-3-small` (or configurable model)

- **Update `graph.py`**
  - `graph.extract_and_store(text, mode="strict")` — orchestrates: extract → disambiguate → store triples
  - Wires `AIExtractor` + `EntityDisambiguator` together

- **`config.py` updates**
  - OpenAI API key configuration
  - Embedding model name
  - Disambiguation threshold
  - Qdrant connection settings (default: local mode)

### API (`api/`)

- **`routers/extraction.py`**
  - `POST /api/extract` — body: `{text, mode}`, returns extracted + disambiguated triples
  - `POST /api/extract/preview` — extract without storing (dry run), shows what would be added and disambiguation decisions
  - `GET /api/entities` — list all known entities with their canonical URIs
  - `GET /api/entities/{name}/similar` — find similar entities (disambiguation debug)

### Frontend (`frontend/`)

- **Extraction page**
  - Text input area (paste or type unstructured text)
  - Mode selector (strict / open toggle)
  - "Preview" button — shows extracted triples before committing
  - Disambiguation panel — shows entity matches and confidence scores, allow user to override
  - "Confirm & Store" button — commits triples to graph
  - History of recent extractions
- **Update Triples page** — show source metadata (manually added vs. AI-extracted)

### Tests

- Unit tests for prompt construction (strict mode JSON schema generation)
- Unit tests for disambiguator logic (above/below threshold, exact match)
- Unit tests for vector store ABC compliance
- Integration test: extract from text → verify disambiguation → verify triples in Fuseki
- Mock OpenAI responses for deterministic testing

### Deliverable

User pastes text like "Mehdi established BrandPulse Analytics in 2023", the system extracts triples, recognizes "BrandPulse Analytics" as existing "BrandPulse", and stores correctly. Visible in the UI with disambiguation explanations.

---

## Phase 4: Natural Language Query + Graph Explorer

**Goal:** Query the graph in English, visualize the knowledge graph interactively, explain inferred knowledge.

### SDK (`src/keplai/`)

- **`nlq.py` — `NLQueryEngine` class**
  - `ask(question)` — natural language → SPARQL → results
  - Process:
    1. Fetch graph schema (classes, properties, sample entities) via `OntologyManager`
    2. Build LLM prompt with schema context + question
    3. LLM generates a read-only `SELECT` SPARQL query
    4. Validate generated SPARQL (no INSERT/DELETE/DROP — read-only enforcement)
    5. Execute against Fuseki
    6. Format results as structured JSON
  - `ask_with_explanation(question)` — returns results + the generated SPARQL + explanation of inferred facts
  - Support for follow-up questions (conversation context)

- **Inference/explanation support in `graph.py`**
  - `graph.explain(subject, predicate, object)` — query Jena's reasoner to show why a fact is true
  - Distinguish between asserted (explicitly added) and inferred (derived by OWL reasoning) triples
  - Format inference chains for agent consumption

- **Update `graph.py`**
  - `graph.ask(question)` — delegates to `NLQueryEngine`
  - `graph.analyze_and_propose_ontology(text)` — AI Schema Proposer (Feature 7 from PRD)
    - Send text to LLM with instructions to propose classes and properties
    - Return structured proposal: `{classes: [...], properties: [{name, domain, range}, ...]}`
    - Developer reviews and optionally applies with `graph.ontology.apply_proposal(proposal)`

### API (`api/`)

- **`routers/query.py`**
  - `POST /api/query/ask` — body: `{question}`, returns results + generated SPARQL
  - `POST /api/query/sparql` — raw SPARQL execution (read-only enforcement)
  - `POST /api/query/explain` — explain a specific triple (asserted vs. inferred)
  - `POST /api/ontology/propose` — body: `{text}`, returns proposed schema
  - `POST /api/ontology/apply-proposal` — apply a proposed schema

### Frontend (`frontend/`)

- **Query page**
  - Natural language input bar (prominent, chat-like UX)
  - Results table with formatted output
  - "Show SPARQL" toggle — reveals the generated query
  - Query history sidebar
  - Raw SPARQL editor (advanced mode) with syntax highlighting

- **Graph Explorer page**
  - Interactive graph visualization (Cytoscape.js or react-force-graph)
  - Nodes = entities (colored by class), edges = predicates
  - Click node → show all triples for that entity
  - Click edge → show relationship details
  - Filter by class, predicate, or search
  - Zoom, pan, layout controls
  - Visual distinction for inferred vs. asserted triples (dashed vs. solid edges)

- **Schema Proposer UI (on Ontology page)**
  - Text input → "Analyze & Propose" button
  - Shows proposed classes and properties as a review table
  - Accept/reject individual items
  - "Apply Selected" button

### Tests

- Unit tests for SPARQL generation from NL (mock LLM responses)
- Unit tests for read-only SPARQL validation (reject INSERT/DELETE)
- Unit tests for schema proposal parsing
- Integration test: define ontology → add triples → ask NL question → verify correct answer
- Integration test: propose schema → apply → verify in Fuseki

### Deliverable

User types "What companies did Mehdi found?" in the UI, sees results, can view the generated SPARQL, and explore the full knowledge graph visually. Inferred facts are highlighted. Schema proposer suggests ontologies from raw text.

---

## Phase 5: Polish, Testing, Packaging & Documentation

**Goal:** Production-readiness, comprehensive tests, developer experience, packaging.

### SDK Polish

- **Error handling & resilience**
  - Graceful handling: Docker not installed, Fuseki unreachable, LLM API errors, invalid SPARQL
  - Custom exception hierarchy: `KeplAIError`, `EngineError`, `ExtractionError`, `QueryError`, `DisambiguationError`
  - Retry logic for transient failures (Fuseki startup, LLM rate limits)
  - Timeout configuration for all external calls

- **Reconnection support**
  - `KeplAI.connect(endpoint="http://localhost:3030")` — connect to existing Fuseki instance
  - Detect existing containers and reattach instead of creating new ones

- **Configuration improvements**
  - Support `.env` files, environment variables, and constructor args (priority order)
  - Sensible defaults for everything
  - Configuration validation on startup

- **Logging**
  - Structured logging throughout (Python `logging` module)
  - Configurable log levels
  - Log SPARQL queries, LLM prompts/responses (debug level), disambiguation decisions

### API Polish

- **Error responses** — consistent error schema across all endpoints
- **CORS configuration** — configurable origins for frontend
- **OpenAPI documentation** — enhanced descriptions, examples for all endpoints
- **WebSocket endpoint** — for long-running extraction tasks (progress updates)
- **Rate limiting** — optional, for LLM-calling endpoints

### Frontend Polish

- **Loading states** — spinners, skeleton screens for all async operations
- **Error handling** — toast notifications, inline error messages
- **Responsive layout** — works on different screen sizes
- **Dark/light theme** — toggle in header
- **Keyboard shortcuts** — Ctrl+Enter to submit queries

### Testing

- **Unit test coverage** — target 80%+ for SDK core
- **Integration test suite** — full end-to-end flows with real Docker/Fuseki
- **API tests** — pytest with httpx/TestClient for all endpoints
- **Frontend tests** — Vitest + React Testing Library for key components
- **CI configuration** — GitHub Actions workflow for test + lint + build

### Packaging & Distribution

- **`pyproject.toml`** — proper metadata, dependencies, optional extras (`[api]`, `[qdrant]`)
- **`pip install keplai`** — installs SDK only
- **`pip install keplai[api]`** — installs SDK + FastAPI layer
- **`pip install keplai[all]`** — everything
- **Docker Compose** — single `docker-compose.yml` to spin up Fuseki + API + Frontend
- **CLI entry point** — `keplai serve` to start the API server

### Documentation

- README with quickstart guide
- API reference (auto-generated from OpenAPI)
- SDK usage examples
- Architecture overview

### Deliverable

A polished, installable Python package with optional API and frontend. Docker Compose for one-command deployment. Comprehensive test suite. Ready for public release or demo.

---

## Phase Summary

| Phase | Focus | SDK | API | Frontend |
|-------|-------|-----|-----|----------|
| 1 | Engine + CRUD | JenaEngine, KeplAI core, namespace mgmt | Triple CRUD endpoints | Layout shell, triples table |
| 2 | Ontology | OntologyManager, class/property definitions | Ontology CRUD endpoints | Ontology page, schema diagram |
| 3 | AI Extraction | AIExtractor, EntityDisambiguator, VectorStore | Extraction endpoints | Extraction page, disambiguation UI |
| 4 | NL Query + Viz | NLQueryEngine, schema proposer, inference | Query + proposal endpoints | Query page, graph explorer, proposer UI |
| 5 | Polish | Error handling, logging, reconnection | Error schema, WebSocket, CORS | Loading states, theme, responsiveness |

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Core Language | Python 3.10+ |
| Graph Engine | Apache Jena Fuseki (Docker) |
| RDF/SPARQL | rdflib, SPARQLWrapper |
| Container Mgmt | docker (Python SDK) |
| LLM (Phase 1) | OpenAI SDK |
| LLM (Future) | LiteLLM |
| Vector Store | Qdrant (abstract interface for swappability) |
| Backend API | FastAPI |
| Frontend | React + Vite + TypeScript |
| Graph Viz | Cytoscape.js or react-force-graph |
| Testing | pytest, Vitest, React Testing Library |

---

## Dependencies Per Phase

- **Phase 1:** docker, rdflib, SPARQLWrapper, fastapi, uvicorn, react, vite, typescript
- **Phase 2:** No new dependencies (builds on Phase 1)
- **Phase 3:** openai, qdrant-client, pydantic (already in fastapi)
- **Phase 4:** No new dependencies (graph viz library added to frontend)
- **Phase 5:** pytest, httpx, vitest, @testing-library/react

---

## API Contract (Updated from PRD)

```python
from keplai import KeplAI

# 1. Zero-config startup (Spins up Fuseki Docker)
graph = KeplAI.start(engine="docker", reasoner="OWL")

# 2. Schema definition (Pythonic)
graph.ontology.define_class("Company")
graph.ontology.define_class("Person")
graph.ontology.define_property("founded", domain="Person", range="Company")

# 3. Manual Graph addition
graph.add("Mehdi", "founded", "BrandPulse")

# 4. AI-Powered Extraction with Auto-Disambiguation
text = "Mehdi established a new SaaS startup called BrandPulse Analytics in 2023."
graph.extract_and_store(text)

# 5. Natural Language Query
results = graph.ask("What companies did Mehdi found?")
print(results)  # [{'entity': 'BrandPulse', 'type': 'Company'}]

# 6. Shut down and persist
graph.stop()

# --- Advanced Usage ---

# Open Extraction (AI invents the schema)
graph.extract_and_store("The James Webb Telescope discovered K2-18b.", mode="open")

# Hybrid Drafting (AI proposes a schema for review)
proposed = graph.analyze_and_propose_ontology(
    "Mehdi started BrandPulse in 2023. Sarah put $50k into the business."
)
print(proposed)
# { classes: ['Person', 'Company'], properties: ['founded', 'invested_in'] }

# Strict Extraction (forced to use exact schema)
graph.extract_and_store("Mehdi started a SaaS startup called BrandPulse.", mode="strict")
```

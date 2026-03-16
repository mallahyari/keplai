# KeplAI — Next Features

## 1. LiteLLM Integration

Swap the hard-coded OpenAI SDK for LiteLLM, enabling any LLM provider (Anthropic, Google, Azure, Ollama, local models) with a single config change.

**Scope:**
- Replace `openai` dependency with `litellm` in extractor, NLQ engine, and disambiguator
- Add `KEPLAI_LLM_PROVIDER` and `KEPLAI_LLM_MODEL` config options (e.g. `anthropic/claude-sonnet-4-20250514`, `ollama/llama3`)
- Keep OpenAI-compatible structured outputs where available; fall back to JSON-mode + parsing for providers that don't support it
- Embedding provider config: allow using local sentence-transformers or any LiteLLM-supported embedding model
- Update all prompts to be provider-agnostic

**Impact:** Users are no longer locked to OpenAI. Local/self-hosted LLMs become possible for air-gapped or cost-sensitive environments.

---

## 2. Schema Proposer

AI analyzes raw text and proposes an ontology schema (classes + properties) for the user to review and apply.

**Scope:**
- `graph.analyze_and_propose_ontology(text)` → returns `{"classes": [...], "properties": [{name, domain, range}, ...]}`
- LLM prompt: analyze the text, identify entity types and relationships, propose a clean ontology
- `graph.ontology.apply_proposal(proposal)` — bulk-create classes and properties from a proposal dict
- API endpoint: `POST /api/ontology/propose` (body: `{text}`) → returns proposal
- API endpoint: `POST /api/ontology/apply-proposal` (body: proposal) → applies it
- Frontend: text input → "Analyze & Propose" button → review table with accept/reject per item → "Apply Selected"

**Impact:** Users can bootstrap an ontology from raw text instead of manually defining every class and property.

---

## 3. Ontology Upload & Import

Allow users to upload an existing OWL/RDF/TTL ontology file, load it into Fuseki, and immediately query against it.

**Scope:**
- `graph.ontology.load_file(path_or_url, format="auto")` — parse and import an ontology file (OWL/XML, Turtle, N-Triples, JSON-LD)
  - Use `rdflib` to parse locally, then bulk-insert triples into Fuseki via SPARQL UPDATE or Fuseki's Graph Store Protocol
  - Auto-detect format from file extension or content
- `graph.ontology.load_url(url)` — fetch and import a remote ontology (e.g. schema.org, FOAF, Dublin Core)
- After import, auto-detect classes (`owl:Class`, `rdfs:Class`) and properties (`owl:ObjectProperty`, `owl:DatatypeProperty`, `rdf:Property`) to populate `get_schema()`
- API endpoint: `POST /api/ontology/upload` — multipart file upload
- API endpoint: `POST /api/ontology/import-url` — body: `{url}`
- Frontend: upload dropzone + URL input on the Ontology page, with import progress and summary of what was loaded
- Support large ontologies: chunked SPARQL inserts (batch 1000 triples per request)
- After loading, user can immediately ask natural-language questions — the NLQ engine picks up the imported schema automatically

**Impact:** Users can leverage existing domain ontologies (medical, financial, legal, etc.) instead of building from scratch, and query them in natural language.

---

## 4. Inference Explanations

Show users *why* a fact exists in the graph — whether it was directly asserted or inferred by the OWL reasoner.

**Scope:**
- `graph.explain(subject, predicate, object)` → returns explanation dict:
  - `asserted: bool` — was this triple explicitly added?
  - `inferred: bool` — was it derived by the reasoner?
  - `reasoning_chain: list` — the inference steps (e.g. "Person subClassOf Agent → Mehdi rdf:type Agent")
- Query Fuseki's inference graph vs. base graph to distinguish asserted from inferred triples
- API endpoint: `POST /api/query/explain` — body: `{subject, predicate, object}`
- Frontend: click any triple or edge in the explorer to see explanation panel (asserted badge vs. inferred badge with reasoning chain)
- Graph Explorer: dashed edges for inferred triples, solid for asserted

**Impact:** Makes the knowledge graph transparent and trustworthy — users understand where facts come from.

---

## 5. WebSocket for Long Extractions

Provide real-time progress updates for large text extraction jobs instead of blocking HTTP requests.

**Scope:**
- `WS /api/extract/stream` — WebSocket endpoint that accepts `{text, mode}` and streams progress events:
  - `{"event": "extracting", "progress": 0.3}` — LLM extraction in progress
  - `{"event": "disambiguating", "entity": "BrandPulse", "match": "BrandPulseAnalytics", "score": 0.95}`
  - `{"event": "storing", "triple": {...}}`
  - `{"event": "complete", "total": 12}`
- SDK: `graph.extract_and_store_streaming(text, mode, callback)` — accepts a callback for progress events
- Frontend: progress bar + live event log during extraction
- Support chunked extraction for very long text: split into paragraphs, extract each, stream results incrementally

**Impact:** Long extractions (multi-page documents) become usable with real-time feedback instead of timeouts.

---

## Priority Order

| # | Feature | Complexity | Value |
|---|---------|-----------|-------|
| 1 | Ontology Upload & Import | Medium | High — unlocks existing ontologies |
| 2 | Schema Proposer | Medium | High — bootstraps new ontologies |
| 3 | LiteLLM Integration | Low-Medium | High — provider flexibility |
| 4 | Inference Explanations | Medium | Medium — transparency |
| 5 | WebSocket Extractions | Medium | Medium — UX for large jobs |

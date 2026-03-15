````markdown
# Product Requirements Document (PRD)

**Project Name:** GraphAI (Working Title)
**Document Purpose:** To provide technical specifications, architecture, and implementation phases for an AI coding assistant to build the GraphAI Python framework.

---

## 1. Project Overview

**GraphAI** is a Python framework for building AI-native knowledge graph applications. It provides a developer-friendly interface to **Apache Jena Fuseki**, combining the mathematical strictness of Semantic Web standards (RDF, OWL, SPARQL) with the fuzzy, natural-language capabilities of Large Language Models (LLMs).

**The core problem:** Standard vector databases lack multi-hop reasoning and logical strictness. Semantic web tools (Jena) are too complex for average Python developers and struggle with messy, unstructured LLM outputs.
**The solution:** GraphAI bridges this gap, acting as the "Agentic Memory" layer that translates Pythonic and natural language operations into strict SPARQL/RDF running on a dynamically managed Apache Jena engine.

---

## 2. System Architecture & Tech Stack

### 2.1 Tech Stack

- **Core Language:** Python 3.10+
- **Graph Engine:** Apache Jena Fuseki (run via Docker)
- **RDF/SPARQL Interface:** `rdflib`, `SPARQLWrapper`
- **Container Management:** `docker` (Python SDK for zero-config provisioning)
- **AI/LLM Integration:** `LiteLLM` (for multi-provider LLM support) or standard `openai` SDK.
- **Vector/Embeddings (for Entity Resolution):** `chromadb` (local, lightweight) or `FAISS`.

### 2.2 High-Level Architecture

```text
[ User / AI Agent ]
       │
       ▼[ GraphAI Python SDK ]
       │── 1. Engine Manager (Docker/Fuseki lifecycle)
       │── 2. Graph Operations API (add, find, delete)
       │── 3. AI Extractor (Text -> RDF Triples)
       │── 4. Entity Disambiguator (Fuzzy-to-Strict mapper)
       │── 5. NL2SPARQL Translator
       │
       ▼[ SPARQL API (HTTP) ]
       │
       ▼
[ Apache Jena Fuseki (Docker) ]
  ├── TDB2 (Storage)
  ├── OWL/RDFS Reasoner (Inference Engine)
  └── Lucene (Text Index)
```
````

---

## 3. Core Features & Functional Requirements

### Feature 1: "Zero-Config" Dynamic Fuseki Provisioning

- **Requirement:** The user should not need to install Java or write Jena Assembler (`.ttl`) files.
- **Behavior:** The `JenaEngine` class uses the Python Docker SDK to pull the `secoresearch/fuseki` (or official `stain/jena-fuseki`) image, generate the necessary config file with OWL reasoning enabled, and spin up the container automatically.

### Feature 2: Pythonic Graph API & Namespace Management

- **Requirement:** Abstract SPARQL CRUD operations into Python methods.
- **Behavior:** Methods like `add(subject, predicate, object)` should automatically map strings to standard URIs (e.g., "Mehdi" -> `http://graphai.io/entity/Mehdi`).
- **Types:** Automatically detect if the `object` is a literal (string/int) or a URI (another entity).

### Feature 3: Neuro-Symbolic "Fuzzy-to-Strict" Entity Resolution

- **Requirement:** Prevent duplicate entities when LLMs extract variations of the same name (e.g., "BrandPulse", "Brand Pulse Analytics").
- **Behavior:** Intercept incoming triples from the AI Extractor. Embed the entity name. Search the local vector store for similar existing entities. If a match is > 90% similar, map the new extraction to the _existing_ URI in Jena.

### Feature 4: Natural Language to SPARQL (NLQ)

- **Requirement:** Allow users to query the graph using English.
- **Behavior:** Fetch the graph schema (existing predicates and classes). Inject the schema into an LLM prompt. Ask the LLM to generate a strict, read-only `SELECT` SPARQL query. Execute it and return formatted JSON.

### Feature 5: Explainable Neuro-Symbolic Agent Tools

- **Requirement:** Expose methods that AI frameworks (LangChain/Autogen) can use as tools, and explain _inferred_ knowledge.
- **Behavior:** When reasoning is enabled in Jena, querying relationships returns inferred facts. The API should be able to format these facts cleanly so an agent can state _why_ it knows something based on the ontology.

### Feature 6: Schema-Driven vs. Open Extraction (Strict vs. Fuzzy)

- **Requirement:** The AI Extractor must support two modes of operation to prevent "predicate explosion" (hallucinated relationships).
- **Behavior (Strict Mode):** When `mode="strict"` is passed, the framework dynamically translates the currently defined OWL ontology (Classes and Properties) into a strict JSON Schema / Pydantic model. The LLM is forced via "Structured Outputs" to only extract entities and relationships that match this exact schema.
- **Behavior (Open Mode):** When `mode="open"`, the LLM is allowed to infer and invent new classes and predicates on the fly, which are then stored in the graph.

### Feature 7: AI Schema Proposer (Hybrid Drafting)

- **Requirement:** Allow the framework to suggest an ontology based on a corpus of text before committing it to the graph.
- **Behavior:** A method `analyze_and_propose_ontology(text)` reads unstructured text and returns a proposed set of standard Classes and Properties (e.g., "I suggest creating `Person` and `Company` with the predicate `founded`"). The developer can then approve and apply this schema.

---

## 4. API Contract (Desired Developer Experience)

The AI should design the code to fulfill this exact UX:

```python
from graphai import GraphAI, Entity

# 1. Zero-config startup (Spins up Fuseki Docker)
graph = GraphAI.start(engine="docker", reasoner="OWL")

# 2. Schema definition (Pythonic)
graph.ontology.define_class("Company")
graph.ontology.define_class("Person")
graph.ontology.define_property("founded", domain="Person", range="Company")

# 3. Manual Graph addition
graph.add("Mehdi", "founded", "BrandPulse")

# 4. AI-Powered Extraction with Auto-Disambiguation
text = "Mehdi established a new SaaS startup called BrandPulse Analytics in 2023."
# (Under the hood: Disambiguator realizes "BrandPulse Analytics" is "BrandPulse")
graph.extract_and_store(text)

# 5. Natural Language Query
results = graph.ask("What companies did Mehdi found?")
print(results) #[{'entity': 'BrandPulse', 'type': 'Company'}]

# 6. Shut down and persist
graph.stop()


# 1. Open Extraction (AI invents the schema)
graph.extract_and_store("The James Webb Telescope discovered K2-18b.", mode="open")

# 2. Hybrid Drafting (AI proposes a schema for you to review)
proposed_schema = graph.analyze_and_propose_ontology("Mehdi started BrandPulse in 2023. Sarah put $50k into the business.")
print(proposed_schema)
# Output: { classes: ['Person', 'Company'], properties:['founded', 'invested_in'] }

# 3. Strict Extraction (AI is forced to use your exact schema)
graph.ontology.define_class("Person")
graph.ontology.define_class("Company")
graph.ontology.define_property("founded", domain="Person", range="Company")

text = "Mehdi started a SaaS startup called BrandPulse."
# The LLM is forced to map "started" to "founded" because of the strict JSON schema.
graph.extract_and_store(text, mode="strict")
```

---

## 5. Use Cases (For Context)

1.  **Agentic Memory:** An AI agent uses `graph.extract_and_store()` after every user conversation to build a long-term memory map of the user's life, preferences, and connections.
2.  **Enterprise RAG:** Connecting unstructured PDFs to structured corporate hierarchies, allowing users to ask complex multi-hop questions like "Which developers work on projects funded by the marketing department?"
3.  **Explainable Recommendations:** Using Jena's OWL reasoner to recommend products, where the AI can query the graph to explain the logical derivation of the recommendation.

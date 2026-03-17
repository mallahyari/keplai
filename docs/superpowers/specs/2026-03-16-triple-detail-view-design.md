# Triple Detail View — Design Spec

**Goal:** Add a slide-out detail panel to the Triples page that shows provenance (how a triple was created) and entity context (related triples, entity type, similar entities) with clickable entity navigation.

**Audience:** Both technical users and non-technical domain experts who need to understand where triples came from and how entities relate.

**Tech Stack:** React 19, TypeScript, Tailwind CSS 4, shadcn/ui, sonner (toasts), lucide-react. Backend: FastAPI, Python, JSON file storage for provenance.

---

## 1. Provenance Store (Backend)

### New SDK Class: `ProvenanceStore`

**File:** `src/keplai/provenance.py`

Records metadata about how each triple was created. Keyed by a deterministic hash of `(subject, predicate, object)` using SHA-256 of the concatenated values with a separator.

**Critical: Hash key identity.** The hash must use **full URI strings** — the same values returned by `graph.find()` and `get_all_triples()`. For example, `"http://keplai.io/entity/Mehdi"` not `"Mehdi"`. This ensures the frontend can look up provenance using the triple values it already has from the triples table. When recording provenance inside `add()`, use `str(self._to_entity_uri(subject))`, `str(self._to_predicate_uri(predicate))`, `str(self._to_object(obj))` to get the resolved URIs. When recording inside `load_rdf()`, use `str(s)`, `str(p)`, `str(o)` from the rdflib triples (which are already URIRef/Literal objects).

**Provenance record schema:**

```json
{
  "method": "manual" | "extraction" | "import",
  "created_at": "2026-03-16T14:30:00Z",
  "source_text": "Mehdi founded BrandPulse...",
  "extraction_mode": "strict" | "open",
  "ontology_source": "foaf.ttl",
  "disambiguation": {
    "subject_original": "Mehdi",
    "subject_matched": "MehdiAllahyari",
    "subject_score": 0.92,
    "object_original": "BrandPulse",
    "object_matched": "BrandPulseAnalytics",
    "object_score": 0.88
  }
}
```

Fields are present only when relevant to the method:
- `source_text`, `extraction_mode`, `disambiguation` — only for `method: "extraction"`
- `ontology_source` — only for `method: "import"`
- `created_at` — always present
- `method` — always present

### Storage

A single `provenance.json` file alongside the existing data files. The path is configured via a new `provenance_path` field added to `KeplAISettings` in `src/keplai/config.py` (defaults to `"./provenance.json"`). Loaded into a Python dict on init, flushed to disk on each write.

**Note:** This is a new storage pattern — the existing SDK stores all graph data in Apache Fuseki via SPARQL. Provenance uses a JSON sidecar file instead of Fuseki because it's auxiliary metadata (not graph data), has a simple key-value access pattern, and avoids coupling provenance schema to the RDF model. The store assumes single-process access. No file locking is needed for the current single-server deployment.

### Hash Function

```python
import hashlib

def triple_hash(subject: str, predicate: str, obj: str) -> str:
    key = f"{subject}\x00{predicate}\x00{obj}"
    return hashlib.sha256(key.encode()).hexdigest()
```

The null byte separator prevents collisions from values that contain the separator character.

### ProvenanceStore API

```python
class ProvenanceStore:
    def __init__(self, path: str = "./provenance.json"):
        """Load provenance.json from path, creating if absent."""

    def record(self, subject: str, predicate: str, obj: str, **metadata) -> None:
        """Record provenance for a triple. Overwrites if exists."""

    def get(self, subject: str, predicate: str, obj: str) -> dict | None:
        """Return provenance record for a triple, or None."""

    def delete(self, subject: str, predicate: str, obj: str) -> None:
        """Remove provenance for a triple (called when triple is deleted)."""
```

### Integration Points

The `ProvenanceStore` is exposed as a lazy `@property` on `KeplAI` (matching the existing pattern used by `ontology`, `extractor`, `disambiguator`, and `nlq`). Configured via `KeplAISettings.provenance_path`. It is called **after** a triple is successfully stored in the graph — provenance is only recorded for triples that actually exist.

- **`graph.add()`** — after the triple is stored, records `method: "manual"` with timestamp
- **`graph.extract_and_store()`** — after each extracted triple is stored, records `method: "extraction"` with source text, extraction mode, and disambiguation info. The disambiguation data comes from the `EntityDisambiguator` results already available in `extract_and_store`.
- **`ontology.load_rdf()`** — after `_batch_insert()` completes, iterates the parsed `rdf_graph` triples and records `method: "import"` with `ontology_source` (filename or URL) for each. Access the provenance store via `self._graph.provenance` (OntologyManager already holds a `self._graph` reference to the `KeplAI` instance). Use `str(s)`, `str(p)`, `str(o)` from the rdflib triples to get string URIs matching the hash key format.
- **`graph.delete()`** — removes provenance for the deleted triple (after the triple is removed from the graph)

### New API Endpoint

**`GET /api/graph/triples/provenance`**

Query parameters: `subject`, `predicate`, `obj` (all required).

Response schema:

```python
class ProvenanceResponse(BaseModel):
    method: str  # "manual", "extraction", "import"
    created_at: str
    source_text: str | None = None
    extraction_mode: str | None = None
    ontology_source: str | None = None
    disambiguation: DisambiguationInfo | None = None  # reuse existing model from api/schemas.py
```

The `DisambiguationInfo` Pydantic model already exists in `api/schemas.py` (line 65) — reuse it to ensure type consistency between the stored JSON and the API response.

Returns `null` (HTTP 200 with `null` body) if no provenance exists for the triple. This is intentional — provenance absence is expected for legacy triples, not an error condition. HTTP 200 with null simplifies frontend handling (no need to catch 404).

---

## 2. Entity Context API (Backend)

### New API Endpoint

**`GET /api/entities/{name}/context`**

This endpoint lives in `api/routers/extraction.py` alongside the existing entity endpoints (`GET /api/entities` and `GET /api/entities/{name}/similar`). The route decorator is `@router.get("/entities/{name}/context")` — the `/api` prefix is already applied by the router.

Returns comprehensive context about an entity in a single request.

Response schema:

```python
class EntityContextResponse(BaseModel):
    entity: str
    triples_as_subject: list[TripleOut]       # existing schema in api/schemas.py
    triples_as_object: list[TripleOut]         # existing schema in api/schemas.py
    entity_type: str | None                     # Ontology class name, or None
    similar_entities: list[SimilarEntityOut]    # existing schema in api/schemas.py
```

Uses existing response models `TripleOut` and `SimilarEntityOut` from `api/schemas.py` — no new response models needed for the list items.

### Implementation

Uses existing SDK methods:
- `graph.find(subject=name)` for `triples_as_subject`
- `graph.find(obj=name)` for `triples_as_object`
- Entity type detection (see below)
- `graph.disambiguator.get_similar(name)` for `similar_entities` (same method used by the existing `GET /api/entities/{name}/similar` endpoint)

**Entity type detection:** Query `graph.find(subject=name)` and look for triples where the predicate is exactly `rdf:type`, or ends with `#type` or `/type`. If found, extract the object value — check against class names in `ontology.get_schema()["classes"]` (each entry is a dict with `"uri"` and `"name"` keys; match against the `"name"` value). If the object is a URI (e.g., `http://xmlns.com/foaf/0.1/Person`), extract the fragment/local name (e.g., `Person`) and match that. Return `None` if no type triple exists.

**Related triples cap:** Both `triples_as_subject` and `triples_as_object` are returned in full (no pagination). These are typically small lists. If performance becomes an issue, pagination can be added later.

### Frontend Types

Added to `frontend/src/types/graph.ts`. Reuses the existing `DisambiguationInfo` interface (already defined in `graph.ts` — note: its fields use `string | null` for matched/score, not plain `string`/`number`).

```typescript
// DisambiguationInfo already exists in this file — reuse it, do not redefine

export interface ProvenanceRecord {
  method: "manual" | "extraction" | "import";
  created_at: string;
  source_text?: string;
  extraction_mode?: string;
  ontology_source?: string;
  disambiguation?: DisambiguationInfo;
}

export interface EntityContext {
  entity: string;
  triples_as_subject: Triple[];    // reuses existing Triple interface
  triples_as_object: Triple[];     // reuses existing Triple interface
  entity_type: string | null;
  similar_entities: SimilarEntity[]; // reuses existing SimilarEntity interface
}
```

### Frontend API Client Additions

Added to `frontend/src/api/client.ts`. Note: `BASE` is `/api/graph` (for provenance endpoint) and entity endpoints use `/api/entities` (matching existing entity API pattern). `encodeURIComponent` is used for URL encoding.

```typescript
getTripleProvenance: (subject: string, predicate: string, obj: string) =>
  request<ProvenanceRecord | null>(
    `${BASE}/triples/provenance?subject=${encodeURIComponent(subject)}&predicate=${encodeURIComponent(predicate)}&obj=${encodeURIComponent(obj)}`
  ),

getEntityContext: (name: string) =>
  request<EntityContext>(`/api/entities/${encodeURIComponent(name)}/context`),
```

---

## 3. Triple Detail Panel (Frontend)

### Trigger & Behavior

- Clicking any triple row in the triples table (except the delete button) opens the detail panel for that triple
- Clicking the same row again or the X button closes the panel
- The selected row gets a subtle accent background highlight
- Cursor shows as pointer on table rows

### Layout

The panel slides in from the right, `w-96` (384px) — slightly wider than the Explorer page panel (`w-80` / 320px) to accommodate provenance details. The triples table and panel sit side-by-side using `flex` layout (same pattern as the Explorer page detail panel).

### Panel Content (top to bottom)

**Header:**
- Subject → Predicate → Object displayed prominently in a styled block
- X close button (top-right)

**Provenance Card:**
- Method badge: color-coded pill — blue for "Manual", purple for "Extraction", amber for "Import"
- Timestamp: "Created Mar 16, 2026" (formatted with `toLocaleDateString`)
- Source text (extraction only): collapsible block with the original text, collapsed by default
- Disambiguation info (extraction only): badges showing "Original → Matched (score%)"
- Ontology source (import only): e.g., "Imported from foaf.ttl"
- No provenance state: muted text "No provenance recorded" (for legacy triples)

**Subject Context — "About {shortName(subject)}":** (The `shortName` utility already exists in `explorer.tsx` — extract it to a shared `lib/utils.ts` or `lib/graph-utils.ts` for reuse.)
- Entity type badge if known (e.g., `Person` with a tag icon)
- Mini-table of related triples (where this entity appears as subject or object, excluding the currently viewed triple)
- Each entity name in the mini-table is **clickable** — clicking reloads the panel to show that entity's context as if a new triple was selected
- Similar entities: small list with match score badges
- Empty state if no related triples: "No other connections found"

**Object Context — "About {shortName(object)}":**
- Same layout as subject context

### Loading States

Each section loads independently:
- Provenance: skeleton card while loading
- Subject context: skeleton rows while loading
- Object context: skeleton rows while loading

Errors show inline muted text (e.g., "Failed to load provenance") rather than blocking the whole panel.

### Click-to-Navigate (Entity Hopping)

When a user clicks an entity name in the related triples mini-table:
1. The panel header updates to show "Entity: {clickedName}" instead of the triple header
2. A breadcrumb or back button appears to return to the original triple view
3. The panel shows a single entity context section (all triples for that entity, type, similar entities)
4. Clicking another entity in *that* view navigates deeper (replaces the current entity view)
5. The back button always returns to the original triple detail view

This is implemented as a simple state stack: `[tripleView, entityView?]`. Max depth of 1 entity hop from the triple view to keep it simple — the back button returns to the triple, not to a previous entity.

---

## 4. Triples Page Integration

### Changes to TriplesPage

- Add `selectedTriple` state (`Triple | null`)
- Row click handler: `onClick={() => setSelectedTriple(t)}` (skip if click target is the delete button)
- Selected row uses **value-based comparison** (not reference equality, since triples array is rebuilt on refresh): `className={cn(selectedTriple && selectedTriple.subject === t.subject && selectedTriple.predicate === t.predicate && selectedTriple.object === t.object && "bg-accent/30")}`. Extract this into a `isSelectedTriple(a, b)` helper for readability.
- Layout wrapper: when panel is open, wrap table + panel in a flex container
- Panel closes when triple is deleted (check by value match against the deleted triple)

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `TripleDetailPanel` | `components/triples/triple-detail-panel.tsx` | Main slide-out panel container |
| `ProvenanceCard` | `components/triples/provenance-card.tsx` | Provenance display with method badge, timestamp, source text |
| `EntityContext` | `components/triples/entity-context.tsx` | Reusable entity section (related triples, type, similar entities) |

### No New Routes

The detail panel is state within TriplesPage, not a separate route. No changes to the hash router.

---

## 5. New Dependencies

None. All functionality uses existing libraries (React, Tailwind, shadcn/ui, sonner, lucide-react).

---

## 6. Backend Changes Summary

| Change | File |
|--------|------|
| New `provenance_path` setting | `src/keplai/config.py` (KeplAISettings) |
| New `ProvenanceStore` class | `src/keplai/provenance.py` |
| Add lazy `provenance` property | `src/keplai/graph.py` (KeplAI) |
| Record provenance on add | `src/keplai/graph.py` (add) |
| Record provenance on extraction | `src/keplai/graph.py` (extract_and_store) |
| Record provenance on import | `src/keplai/ontology.py` (load_rdf) |
| Delete provenance on triple delete | `src/keplai/graph.py` (delete) |
| New `ProvenanceResponse` schema | `api/schemas.py` |
| New `EntityContextResponse` schema | `api/schemas.py` |
| New `GET /triples/provenance` endpoint | `api/routers/graph.py` |
| New `GET /entities/{name}/context` endpoint | `api/routers/extraction.py` |

---

## 7. Out of Scope

- SPARQL-queryable provenance (RDF reification)
- Triple versioning or edit history
- Bulk provenance export
- Provenance for triples that existed before this feature ships (they'll show "No provenance recorded")

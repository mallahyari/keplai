from pydantic import BaseModel


class TripleIn(BaseModel):
    subject: str
    predicate: str
    object: str | int | float


class TripleOut(BaseModel):
    subject: str
    predicate: str
    object: str


class TripleQuery(BaseModel):
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None


class StatusResponse(BaseModel):
    engine: str
    healthy: bool
    endpoint: str
    dataset: str


# -- Ontology schemas --

class ClassIn(BaseModel):
    name: str


class ClassOut(BaseModel):
    uri: str
    name: str


class PropertyIn(BaseModel):
    name: str
    domain: str
    range: str


class PropertyOut(BaseModel):
    uri: str
    name: str
    domain: str
    range: str


class SchemaOut(BaseModel):
    classes: list[ClassOut]
    properties: list[PropertyOut]


# -- Extraction schemas --

class ExtractionRequest(BaseModel):
    text: str
    mode: str = "strict"


class DisambiguationInfo(BaseModel):
    subject_original: str
    subject_matched: str | None = None
    subject_score: float | None = None
    object_original: str
    object_matched: str | None = None
    object_score: float | None = None


class ExtractedTripleOut(BaseModel):
    subject: str
    predicate: str
    object: str
    disambiguation: DisambiguationInfo


class CandidateMatch(BaseModel):
    name: str
    score: float


class PreviewTripleOut(BaseModel):
    subject: str
    predicate: str
    object: str
    subject_candidates: list[CandidateMatch] = []
    object_candidates: list[CandidateMatch] = []


class EntityOut(BaseModel):
    name: str


class SimilarEntityOut(BaseModel):
    name: str
    score: float


# -- Query schemas --

class AskRequest(BaseModel):
    question: str


class SparqlRequest(BaseModel):
    sparql: str


class QueryResult(BaseModel):
    results: list[dict[str, str]]
    sparql: str


class QueryResultWithExplanation(BaseModel):
    results: list[dict[str, str]]
    sparql: str
    explanation: str


# -- Import schemas --

class ImportUrlRequest(BaseModel):
    url: str
    name: str | None = None


class ImportResponse(BaseModel):
    ontology_id: str | None = None
    graph_uri: str | None = None
    triples_loaded: int
    format: str
    classes: list[ClassOut]
    properties: list[PropertyOut]


class OntologyMetadataOut(BaseModel):
    id: str
    name: str
    source: str
    graph_uri: str
    import_date: str
    classes_count: int
    properties_count: int


class StatsResponse(BaseModel):
    triple_count: int
    entity_count: int
    ontology_count: int
    class_count: int
    property_count: int


# -- Provenance schemas --

class ProvenanceResponse(BaseModel):
    method: str
    created_at: str
    source_text: str | None = None
    extraction_mode: str | None = None
    ontology_source: str | None = None
    disambiguation: DisambiguationInfo | None = None


# -- Entity context schemas --

class EntityContextResponse(BaseModel):
    entity: str
    triples_as_subject: list[TripleOut]
    triples_as_object: list[TripleOut]
    entity_type: str | None = None
    similar_entities: list[SimilarEntityOut]

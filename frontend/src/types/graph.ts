export interface Triple {
  subject: string;
  predicate: string;
  object: string;
}

export interface TripleInput {
  subject: string;
  predicate: string;
  object: string | number;
}

export interface EngineStatus {
  engine: string;
  healthy: boolean;
  endpoint: string;
  dataset: string;
}

// Ontology types

export interface OntologyClass {
  uri: string;
  name: string;
}

export interface OntologyProperty {
  uri: string;
  name: string;
  domain: string;
  range: string;
}

export interface OntologySchema {
  classes: OntologyClass[];
  properties: OntologyProperty[];
}

// Extraction types

export interface ExtractionRequest {
  text: string;
  mode: "strict" | "open";
}

export interface DisambiguationInfo {
  subject_original: string;
  subject_matched: string | null;
  subject_score: number | null;
  object_original: string;
  object_matched: string | null;
  object_score: number | null;
}

export interface ExtractedTriple {
  subject: string;
  predicate: string;
  object: string;
  disambiguation: DisambiguationInfo;
}

export interface CandidateMatch {
  name: string;
  score: number;
}

export interface PreviewTriple {
  subject: string;
  predicate: string;
  object: string;
  subject_candidates: CandidateMatch[];
  object_candidates: CandidateMatch[];
}

export interface Entity {
  name: string;
}

export interface SimilarEntity {
  name: string;
  score: number;
}

// Query types

export interface QueryResult {
  results: Record<string, string>[];
  sparql: string;
}

export interface QueryResultWithExplanation extends QueryResult {
  explanation: string;
}

// Import types

export interface OntologyImportResponse {
  triples_loaded: number;
  format: string;
  classes: OntologyClass[];
  properties: OntologyProperty[];
}

// Graph explorer types

export interface GraphNode {
  id: string;
  label: string;
}

export interface GraphLink {
  source: string;
  target: string;
  label: string;
}

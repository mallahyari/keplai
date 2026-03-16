import type {
  Triple,
  TripleInput,
  EngineStatus,
  OntologyClass,
  OntologyProperty,
  OntologySchema,
  OntologyImportResponse,
  OntologyMetadata,
  ExtractionRequest,
  ExtractedTriple,
  PreviewTriple,
  Entity,
  SimilarEntity,
  QueryResult,
  QueryResultWithExplanation,
} from "@/types/graph";

const BASE = "/api/graph";
const ONT_BASE = "/api/ontology";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getStatus: () => request<EngineStatus>(`${BASE}/status`),

  getAllTriples: () => request<Triple[]>(`${BASE}/triples/all`),

  queryTriples: (params: {
    subject?: string;
    predicate?: string;
    object?: string;
  }) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v) as [string, string][]
    ).toString();
    return request<Triple[]>(`${BASE}/triples${qs ? `?${qs}` : ""}`);
  },

  addTriple: (triple: TripleInput) =>
    request<{ status: string }>(`${BASE}/triples`, {
      method: "POST",
      body: JSON.stringify(triple),
    }),

  deleteTriple: (triple: TripleInput) =>
    request<{ status: string }>(`${BASE}/triples`, {
      method: "DELETE",
      body: JSON.stringify(triple),
    }),

  // Ontology
  getClasses: () => request<OntologyClass[]>(`${ONT_BASE}/classes`),

  defineClass: (name: string) =>
    request<{ status: string }>(`${ONT_BASE}/classes`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  removeClass: (name: string) =>
    request<{ status: string }>(`${ONT_BASE}/classes/${name}`, {
      method: "DELETE",
    }),

  getProperties: () => request<OntologyProperty[]>(`${ONT_BASE}/properties`),

  defineProperty: (name: string, domain: string, range: string) =>
    request<{ status: string }>(`${ONT_BASE}/properties`, {
      method: "POST",
      body: JSON.stringify({ name, domain, range }),
    }),

  removeProperty: (name: string) =>
    request<{ status: string }>(`${ONT_BASE}/properties/${name}`, {
      method: "DELETE",
    }),

  getSchema: () => request<OntologySchema>(`${ONT_BASE}/schema`),

  uploadOntologyFile: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${ONT_BASE}/upload`, { method: "POST", body: form }).then(
      async (res) => {
        if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
        return res.json() as Promise<OntologyImportResponse>;
      },
    );
  },

  importOntologyUrl: (url: string, name?: string) =>
    request<OntologyImportResponse>(`${ONT_BASE}/import-url`, {
      method: "POST",
      body: JSON.stringify({ url, name }),
    }),

  // Multi-ontology management
  getOntologies: () => request<OntologyMetadata[]>(`${ONT_BASE}/ontologies`),

  deleteOntology: (ontologyId: string, graphUri: string) =>
    request<{ status: string }>(
      `${ONT_BASE}/ontologies/${ontologyId}?graph_uri=${encodeURIComponent(graphUri)}`,
      { method: "DELETE" },
    ),

  getOntologySchema: (ontologyId: string, graphUri: string) =>
    request<OntologySchema>(
      `${ONT_BASE}/ontologies/${ontologyId}/schema?graph_uri=${encodeURIComponent(graphUri)}`,
    ),

  // Extraction
  extractAndStore: (req: ExtractionRequest) =>
    request<ExtractedTriple[]>("/api/extract", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  extractPreview: (req: ExtractionRequest) =>
    request<PreviewTriple[]>("/api/extract/preview", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  getEntities: () => request<Entity[]>("/api/entities"),

  getSimilarEntities: (name: string) =>
    request<SimilarEntity[]>(`/api/entities/${encodeURIComponent(name)}/similar`),

  // Query
  ask: (question: string) =>
    request<QueryResult>("/api/query/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  askWithExplanation: (question: string) =>
    request<QueryResultWithExplanation>("/api/query/ask/explain", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  executeSparql: (sparql: string) =>
    request<QueryResult>("/api/query/sparql", {
      method: "POST",
      body: JSON.stringify({ sparql }),
    }),
};

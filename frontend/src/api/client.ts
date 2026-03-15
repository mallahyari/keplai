import type {
  Triple,
  TripleInput,
  EngineStatus,
  OntologyClass,
  OntologyProperty,
  OntologySchema,
  ExtractionRequest,
  ExtractedTriple,
  PreviewTriple,
  Entity,
  SimilarEntity,
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
};

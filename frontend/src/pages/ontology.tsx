import { useCallback, useEffect, useState } from "react";
import { api } from "@/api/client";
import type { OntologyClass, OntologyProperty, OntologyImportResponse, OntologyMetadata, OntologySchema } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Trash2, Eye } from "lucide-react";

export function OntologyPage() {
  const [classes, setClasses] = useState<OntologyClass[]>([]);
  const [properties, setProperties] = useState<OntologyProperty[]>([]);
  const [loading, setLoading] = useState(true);

  // Add class form
  const [className, setClassName] = useState("");

  // Add property form
  const [propName, setPropName] = useState("");
  const [propDomain, setPropDomain] = useState("");
  const [propRange, setPropRange] = useState("");

  // Import section
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importUrl, setImportUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<OntologyImportResponse | null>(null);
  const [importError, setImportError] = useState("");

  // Multi-ontology management
  const [ontologies, setOntologies] = useState<OntologyMetadata[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<{ id: string; schema: OntologySchema } | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [cls, props, onts] = await Promise.all([
        api.getClasses(),
        api.getProperties(),
        api.getOntologies(),
      ]);
      setClasses(cls);
      setProperties(props);
      setOntologies(onts);
    } catch (err) {
      console.error("Failed to load ontology", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleAddClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!className) return;
    await api.defineClass(className);
    setClassName("");
    refresh();
  };

  const handleDeleteClass = async (name: string) => {
    await api.removeClass(name);
    refresh();
  };

  const handleAddProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!propName || !propDomain || !propRange) return;
    await api.defineProperty(propName, propDomain, propRange);
    setPropName("");
    setPropDomain("");
    setPropRange("");
    refresh();
  };

  const handleDeleteProperty = async (name: string) => {
    await api.removeProperty(name);
    refresh();
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;
    setImporting(true);
    setImportError("");
    setImportResult(null);
    try {
      const result = await api.uploadOntologyFile(importFile);
      setImportResult(result);
      setImportFile(null);
      const input = document.getElementById("ontology-file") as HTMLInputElement;
      if (input) input.value = "";
      refresh();
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setImporting(false);
    }
  };

  const handleUrlImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importUrl) return;
    setImporting(true);
    setImportError("");
    setImportResult(null);
    try {
      const result = await api.importOntologyUrl(importUrl);
      setImportResult(result);
      setImportUrl("");
      refresh();
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setImporting(false);
    }
  };

  const handleDeleteOntology = async (id: string, graphUri: string) => {
    try {
      await api.deleteOntology(id, graphUri);
      setSelectedSchema(null);
      refresh();
    } catch (err) {
      console.error("Failed to delete ontology", err);
    }
  };

  const handleViewSchema = async (id: string, graphUri: string) => {
    if (selectedSchema?.id === id) {
      setSelectedSchema(null);
      return;
    }
    try {
      const schema = await api.getOntologySchema(id, graphUri);
      setSelectedSchema({ id, schema });
    } catch (err) {
      console.error("Failed to load schema", err);
    }
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold tracking-tight">Ontology</h2>

      {/* Import section */}
      <section className="space-y-4">
        <h3 className="text-lg font-medium">Import Ontology</h3>

        <div className="grid gap-4 md:grid-cols-2">
          {/* File upload */}
          <form onSubmit={handleFileUpload} className="space-y-3 rounded-lg border p-4">
            <p className="text-sm font-medium">Upload File</p>
            <p className="text-xs text-muted-foreground">
              Supports OWL/XML (.owl, .rdf), Turtle (.ttl), N-Triples (.nt), JSON-LD (.jsonld)
            </p>
            <Input
              id="ontology-file"
              type="file"
              accept=".owl,.rdf,.xml,.ttl,.nt,.jsonld,.json"
              onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
            />
            <Button type="submit" disabled={!importFile || importing}>
              {importing ? "Uploading\u2026" : "Upload & Import"}
            </Button>
          </form>

          {/* URL import */}
          <form onSubmit={handleUrlImport} className="space-y-3 rounded-lg border p-4">
            <p className="text-sm font-medium">Import from URL</p>
            <p className="text-xs text-muted-foreground">
              Fetch a remote ontology (e.g. schema.org, FOAF, Dublin Core)
            </p>
            <Input
              value={importUrl}
              onChange={(e) => setImportUrl(e.target.value)}
              placeholder="https://example.org/ontology.owl"
            />
            <Button type="submit" disabled={!importUrl || importing}>
              {importing ? "Importing\u2026" : "Import from URL"}
            </Button>
          </form>
        </div>

        {importError && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {importError}
          </div>
        )}

        {importResult && (
          <div className="rounded-md border border-green-200 bg-green-50 p-4 space-y-2">
            <p className="text-sm font-medium text-green-800">
              Import successful — {importResult.triples_loaded} triples loaded (format: {importResult.format})
            </p>
            <p className="text-xs text-green-700">
              Detected {importResult.classes.length} classes and {importResult.properties.length} properties
            </p>
          </div>
        )}
      </section>

      <Separator />

      {/* Imported Ontologies section */}
      <section className="space-y-4">
        <h3 className="text-lg font-medium">Imported Ontologies</h3>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Classes</TableHead>
                <TableHead>Properties</TableHead>
                <TableHead>Imported</TableHead>
                <TableHead className="w-[100px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : ontologies.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    No ontologies imported
                  </TableCell>
                </TableRow>
              ) : (
                ontologies.map((ont) => (
                  <TableRow key={ont.id}>
                    <TableCell className="font-medium">{ont.name}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground truncate max-w-[200px]">
                      {ont.source}
                    </TableCell>
                    <TableCell>{ont.classes_count}</TableCell>
                    <TableCell>{ont.properties_count}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(ont.import_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleViewSchema(ont.id, ont.graph_uri)}
                        title="View schema"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteOntology(ont.id, ont.graph_uri)}
                        title="Delete ontology"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {selectedSchema && (
          <div className="rounded-md border p-4 space-y-3">
            <p className="text-sm font-medium">Schema Details</p>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Classes ({selectedSchema.schema.classes.length})</p>
                <ul className="text-sm space-y-0.5">
                  {selectedSchema.schema.classes.map((c) => (
                    <li key={c.uri} className="font-mono text-xs">{c.name} &mdash; <span className="text-muted-foreground">{c.uri}</span></li>
                  ))}
                  {selectedSchema.schema.classes.length === 0 && (
                    <li className="text-muted-foreground text-xs">None</li>
                  )}
                </ul>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Properties ({selectedSchema.schema.properties.length})</p>
                <ul className="text-sm space-y-0.5">
                  {selectedSchema.schema.properties.map((p) => (
                    <li key={p.uri} className="font-mono text-xs">{p.name} ({p.domain} &rarr; {p.range})</li>
                  ))}
                  {selectedSchema.schema.properties.length === 0 && (
                    <li className="text-muted-foreground text-xs">None</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}
      </section>

      <Separator />

      {/* Classes section */}
      <section className="space-y-4">
        <h3 className="text-lg font-medium">Classes</h3>

        <form onSubmit={handleAddClass} className="flex gap-3 items-end">
          <div className="space-y-1">
            <Label htmlFor="class-name">Class Name</Label>
            <Input
              id="class-name"
              value={className}
              onChange={(e) => setClassName(e.target.value)}
              placeholder="e.g. Person"
            />
          </div>
          <Button type="submit">Add Class</Button>
        </form>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>URI</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    Loading…
                  </TableCell>
                </TableRow>
              ) : classes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    No classes defined
                  </TableCell>
                </TableRow>
              ) : (
                classes.map((c) => (
                  <TableRow key={c.uri}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">
                      {c.uri}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteClass(c.name)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </section>

      {/* Properties section */}
      <section className="space-y-4">
        <h3 className="text-lg font-medium">Properties</h3>

        <form onSubmit={handleAddProperty} className="flex gap-3 items-end">
          <div className="space-y-1">
            <Label htmlFor="prop-name">Property Name</Label>
            <Input
              id="prop-name"
              value={propName}
              onChange={(e) => setPropName(e.target.value)}
              placeholder="e.g. founded"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="prop-domain">Domain</Label>
            <Input
              id="prop-domain"
              value={propDomain}
              onChange={(e) => setPropDomain(e.target.value)}
              placeholder="e.g. Person"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="prop-range">Range</Label>
            <Input
              id="prop-range"
              value={propRange}
              onChange={(e) => setPropRange(e.target.value)}
              placeholder="e.g. Company"
            />
          </div>
          <Button type="submit">Add Property</Button>
        </form>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Domain</TableHead>
                <TableHead>Range</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    Loading…
                  </TableCell>
                </TableRow>
              ) : properties.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    No properties defined
                  </TableCell>
                </TableRow>
              ) : (
                properties.map((p) => (
                  <TableRow key={p.uri}>
                    <TableCell className="font-medium">{p.name}</TableCell>
                    <TableCell>{p.domain}</TableCell>
                    <TableCell>{p.range}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteProperty(p.name)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  );
}

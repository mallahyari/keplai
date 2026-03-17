import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Trash2, Eye, BookOpen, Upload } from "lucide-react";
import { api } from "@/api/client";
import type { OntologyClass, OntologyProperty, OntologyImportResponse, OntologyMetadata, OntologySchema } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { PageTabs } from "@/components/ui/page-tabs";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const TABS = [
  { id: "ontologies", label: "Imported Ontologies" },
  { id: "classes", label: "Classes" },
  { id: "properties", label: "Properties" },
  { id: "import", label: "Import" },
];

export function OntologyPage() {
  const [activeTab, setActiveTab] = useState("ontologies");
  const [classes, setClasses] = useState<OntologyClass[]>([]);
  const [properties, setProperties] = useState<OntologyProperty[]>([]);
  const [ontologies, setOntologies] = useState<OntologyMetadata[]>([]);
  const [loading, setLoading] = useState(true);

  // Class form
  const [className, setClassName] = useState("");
  // Property form
  const [propName, setPropName] = useState("");
  const [propDomain, setPropDomain] = useState("");
  const [propRange, setPropRange] = useState("");
  // Import
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importUrl, setImportUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<OntologyImportResponse | null>(null);
  // Schema viewer
  const [selectedSchema, setSelectedSchema] = useState<{ id: string; schema: OntologySchema } | null>(null);
  // Delete confirmations
  const [deleteOntTarget, setDeleteOntTarget] = useState<OntologyMetadata | null>(null);
  const [deleteClassTarget, setDeleteClassTarget] = useState<string | null>(null);
  const [deletePropTarget, setDeletePropTarget] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [cls, props, onts] = await Promise.all([
        api.getClasses(), api.getProperties(), api.getOntologies(),
      ]);
      setClasses(cls);
      setProperties(props);
      setOntologies(onts);
    } catch {
      toast.error("Failed to load ontology data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleAddClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!className.trim()) return;
    try {
      await api.defineClass(className.trim());
      toast.success(`Class "${className.trim()}" created`);
      setClassName("");
      refresh();
    } catch (err) {
      toast.error("Failed to create class: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const handleDeleteClass = async (name: string) => {
    try {
      await api.removeClass(name);
      toast.success(`Class "${name}" deleted`);
      refresh();
    } catch (err) {
      toast.error("Failed to delete class: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const handleAddProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!propName.trim() || !propDomain.trim() || !propRange.trim()) return;
    try {
      await api.defineProperty(propName.trim(), propDomain.trim(), propRange.trim());
      toast.success(`Property "${propName.trim()}" created`);
      setPropName("");
      setPropDomain("");
      setPropRange("");
      refresh();
    } catch (err) {
      toast.error("Failed to create property: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const handleDeleteProperty = async (name: string) => {
    try {
      await api.removeProperty(name);
      toast.success(`Property "${name}" deleted`);
      refresh();
    } catch (err) {
      toast.error("Failed to delete property: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const handleDeleteOntology = async (ont: OntologyMetadata) => {
    try {
      await api.deleteOntology(ont.id, ont.graph_uri);
      toast.success(`Ontology "${ont.name}" deleted`);
      setSelectedSchema(null);
      refresh();
    } catch (err) {
      toast.error("Failed to delete ontology: " + (err instanceof Error ? err.message : "Unknown error"));
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
      toast.error("Failed to load schema: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;
    setImporting(true);
    setImportResult(null);
    try {
      const result = await api.uploadOntologyFile(importFile);
      setImportResult(result);
      setImportFile(null);
      const input = document.getElementById("ontology-file") as HTMLInputElement;
      if (input) input.value = "";
      toast.success(`Ontology imported — ${result.triples_loaded} triples loaded`);
      refresh();
    } catch (err) {
      toast.error("Upload failed: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setImporting(false);
    }
  };

  const handleUrlImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importUrl.trim()) return;
    setImporting(true);
    setImportResult(null);
    try {
      const result = await api.importOntologyUrl(importUrl.trim());
      setImportResult(result);
      setImportUrl("");
      toast.success(`Ontology imported — ${result.triples_loaded} triples loaded`);
      refresh();
    } catch (err) {
      toast.error("Import failed: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageTabs tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Imported Ontologies tab */}
      {activeTab === "ontologies" && (
        <div className="space-y-4">
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Classes</TableHead>
                  <TableHead>Properties</TableHead>
                  <TableHead>Imported</TableHead>
                  <TableHead className="w-25" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell />
                    </TableRow>
                  ))
                ) : ontologies.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6}>
                      <EmptyState
                        icon={BookOpen}
                        title="No ontologies imported"
                        description="Import an ontology to get started."
                        actions={[{ label: "Import Ontology", onClick: () => setActiveTab("import") }]}
                      />
                    </TableCell>
                  </TableRow>
                ) : (
                  ontologies.map((ont) => (
                    <TableRow key={ont.id}>
                      <TableCell className="font-medium">{ont.name}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground truncate max-w-50">{ont.source}</TableCell>
                      <TableCell>{ont.classes_count}</TableCell>
                      <TableCell>{ont.properties_count}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{new Date(ont.import_date).toLocaleDateString()}</TableCell>
                      <TableCell className="flex gap-1">
                        <Button variant="ghost" size="icon" onClick={() => handleViewSchema(ont.id, ont.graph_uri)} title="View schema">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => setDeleteOntTarget(ont)} title="Delete ontology">
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
                      <li key={c.uri} className="font-mono text-xs">{c.name} — <span className="text-muted-foreground">{c.uri}</span></li>
                    ))}
                    {selectedSchema.schema.classes.length === 0 && <li className="text-muted-foreground text-xs">None</li>}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Properties ({selectedSchema.schema.properties.length})</p>
                  <ul className="text-sm space-y-0.5">
                    {selectedSchema.schema.properties.map((p) => (
                      <li key={p.uri} className="font-mono text-xs">{p.name} ({p.domain} → {p.range})</li>
                    ))}
                    {selectedSchema.schema.properties.length === 0 && <li className="text-muted-foreground text-xs">None</li>}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Classes tab */}
      {activeTab === "classes" && (
        <div className="space-y-4">
          <form onSubmit={handleAddClass} className="flex gap-3 items-end">
            <div className="space-y-1">
              <Label htmlFor="class-name">Class Name *</Label>
              <Input id="class-name" value={className} onChange={(e) => setClassName(e.target.value)} placeholder="e.g. Person" required />
            </div>
            <Button type="submit" disabled={!className.trim()}>Add Class</Button>
          </form>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>URI</TableHead>
                  <TableHead className="w-15" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                      <TableCell />
                    </TableRow>
                  ))
                ) : classes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3}>
                      <EmptyState icon={BookOpen} title="No classes defined" description="Define your first class above." />
                    </TableCell>
                  </TableRow>
                ) : (
                  classes.map((c) => (
                    <TableRow key={c.uri}>
                      <TableCell className="font-medium">{c.name}</TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">{c.uri}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="icon" onClick={() => setDeleteClassTarget(c.name)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {/* Properties tab */}
      {activeTab === "properties" && (
        <div className="space-y-4">
          <form onSubmit={handleAddProperty} className="flex gap-3 items-end">
            <div className="space-y-1">
              <Label htmlFor="prop-name">Name *</Label>
              <Input id="prop-name" value={propName} onChange={(e) => setPropName(e.target.value)} placeholder="e.g. founded" required />
            </div>
            <div className="space-y-1">
              <Label htmlFor="prop-domain">Domain *</Label>
              <Input id="prop-domain" value={propDomain} onChange={(e) => setPropDomain(e.target.value)} placeholder="e.g. Person" required />
            </div>
            <div className="space-y-1">
              <Label htmlFor="prop-range">Range *</Label>
              <Input id="prop-range" value={propRange} onChange={(e) => setPropRange(e.target.value)} placeholder="e.g. Company" required />
            </div>
            <Button type="submit" disabled={!propName.trim() || !propDomain.trim() || !propRange.trim()}>Add Property</Button>
          </form>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Domain</TableHead>
                  <TableHead>Range</TableHead>
                  <TableHead className="w-15" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell />
                    </TableRow>
                  ))
                ) : properties.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4}>
                      <EmptyState icon={BookOpen} title="No properties defined" description="Define your first property above." />
                    </TableCell>
                  </TableRow>
                ) : (
                  properties.map((p) => (
                    <TableRow key={p.uri}>
                      <TableCell className="font-medium">{p.name}</TableCell>
                      <TableCell>{p.domain}</TableCell>
                      <TableCell>{p.range}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="icon" onClick={() => setDeletePropTarget(p.name)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {/* Import tab */}
      {activeTab === "import" && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <form onSubmit={handleFileUpload} className="space-y-3 rounded-lg border p-4">
              <p className="text-sm font-medium">Upload File</p>
              <p className="text-xs text-muted-foreground">Supports OWL/XML, Turtle, N-Triples, JSON-LD</p>
              <Input id="ontology-file" type="file" accept=".owl,.rdf,.xml,.ttl,.nt,.jsonld,.json" onChange={(e) => setImportFile(e.target.files?.[0] ?? null)} />
              <Button type="submit" disabled={!importFile || importing}>
                <Upload className="h-4 w-4 mr-1" /> {importing ? "Uploading…" : "Upload & Import"}
              </Button>
            </form>

            <form onSubmit={handleUrlImport} className="space-y-3 rounded-lg border p-4">
              <p className="text-sm font-medium">Import from URL</p>
              <p className="text-xs text-muted-foreground">Fetch a remote ontology (e.g. FOAF, Dublin Core)</p>
              <Input value={importUrl} onChange={(e) => setImportUrl(e.target.value)} placeholder="https://example.org/ontology.owl" />
              <Button type="submit" disabled={!importUrl.trim() || importing}>
                <Upload className="h-4 w-4 mr-1" /> {importing ? "Importing…" : "Import from URL"}
              </Button>
            </form>
          </div>

          {importResult && (
            <div className="rounded-md border border-green-200 bg-green-50 dark:bg-green-950/30 p-4 space-y-2">
              <p className="text-sm font-medium text-green-800 dark:text-green-200">
                Import successful — {importResult.triples_loaded} triples loaded (format: {importResult.format})
              </p>
              <p className="text-xs text-green-700 dark:text-green-300">
                Detected {importResult.classes.length} classes and {importResult.properties.length} properties
              </p>
            </div>
          )}
        </div>
      )}

      {/* Delete confirmation dialogs */}
      <ConfirmDialog
        open={deleteOntTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteOntTarget(null); }}
        title="Delete ontology?"
        description={deleteOntTarget ? `Delete "${deleteOntTarget.name}"? This removes all its triples and cannot be undone.` : ""}
        onConfirm={() => { if (deleteOntTarget) handleDeleteOntology(deleteOntTarget); }}
      />
      <ConfirmDialog
        open={deleteClassTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteClassTarget(null); }}
        title="Delete class?"
        description={`Remove class "${deleteClassTarget}"?`}
        onConfirm={() => { if (deleteClassTarget) handleDeleteClass(deleteClassTarget); }}
      />
      <ConfirmDialog
        open={deletePropTarget !== null}
        onOpenChange={(open) => { if (!open) setDeletePropTarget(null); }}
        title="Delete property?"
        description={`Remove property "${deletePropTarget}"?`}
        onConfirm={() => { if (deletePropTarget) handleDeleteProperty(deletePropTarget); }}
      />
    </div>
  );
}

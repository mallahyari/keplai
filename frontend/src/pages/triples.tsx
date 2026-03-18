import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, Filter, Trash2, Database } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/api/client";
import type { Triple } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { shortName } from "@/lib/graph-utils";
import { TripleDetailPanel } from "@/components/triples/triple-detail-panel";

const PAGE_SIZE = 50;

interface TriplesPageProps {
  onNavigate?: (href: string) => void;
}

export function TriplesPage({ onNavigate }: TriplesPageProps) {
  const [triples, setTriples] = useState<Triple[]>([]);
  const [loading, setLoading] = useState(true);

  // Add dialog
  const [addOpen, setAddOpen] = useState(false);
  const [subject, setSubject] = useState("");
  const [predicate, setPredicate] = useState("");
  const [object, setObject] = useState("");
  const [adding, setAdding] = useState(false);

  // Filters
  const [showFilters, setShowFilters] = useState(false);
  const [filterSubject, setFilterSubject] = useState("");
  const [filterPredicate, setFilterPredicate] = useState("");
  const [filterObject, setFilterObject] = useState("");

  // Sort
  const [sortCol, setSortCol] = useState<"subject" | "predicate" | "object" | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  // Pagination
  const [page, setPage] = useState(1);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<Triple | null>(null);

  // Batch selection
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [batchDeleting, setBatchDeleting] = useState(false);
  const [batchDeleteConfirm, setBatchDeleteConfirm] = useState(false);

  // Detail panel
  const [selectedTriple, setSelectedTriple] = useState<Triple | null>(null);

  const isSelectedTriple = (a: Triple | null, b: Triple) =>
    a !== null && a.subject === b.subject && a.predicate === b.predicate && a.object === b.object;

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAllTriples();
      setTriples(data);
    } catch {
      toast.error("Failed to load triples");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Filter + sort + paginate
  const filtered = useMemo(() => {
    let result = triples.filter((t) => {
      if (filterSubject && !t.subject.toLowerCase().includes(filterSubject.toLowerCase())) return false;
      if (filterPredicate && !t.predicate.toLowerCase().includes(filterPredicate.toLowerCase())) return false;
      if (filterObject && !t.object.toLowerCase().includes(filterObject.toLowerCase())) return false;
      return true;
    });
    if (sortCol) {
      result = [...result].sort((a, b) => {
        const av = a[sortCol].toLowerCase();
        const bv = b[sortCol].toLowerCase();
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      });
    }
    return result;
  }, [triples, filterSubject, filterPredicate, filterObject, sortCol, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Reset page and selection when filters change
  useEffect(() => { setPage(1); setSelected(new Set()); }, [filterSubject, filterPredicate, filterObject]);

  const toggleSort = (col: "subject" | "predicate" | "object") => {
    if (sortCol === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortCol(col);
      setSortDir("asc");
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject || !predicate || !object) return;
    setAdding(true);
    try {
      await api.addTriple({ subject, predicate, object });
      toast.success("Triple added");
      setSubject(""); setPredicate(""); setObject("");
      setAddOpen(false);
      refresh();
    } catch (err) {
      toast.error("Failed to add triple: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (t: Triple) => {
    try {
      await api.deleteTriple(t);
      toast.success("Triple deleted");
      refresh();
      if (selectedTriple && isSelectedTriple(selectedTriple, t)) {
        setSelectedTriple(null);
      }
    } catch {
      toast.error("Failed to delete triple");
    }
  };

  const toggleSelect = (idx: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const allOnPageSelected = paginated.length > 0 && paginated.every((_, i) => selected.has((page - 1) * PAGE_SIZE + i));

  const toggleSelectAll = () => {
    if (allOnPageSelected) {
      setSelected((prev) => {
        const next = new Set(prev);
        paginated.forEach((_, i) => next.delete((page - 1) * PAGE_SIZE + i));
        return next;
      });
    } else {
      setSelected((prev) => {
        const next = new Set(prev);
        paginated.forEach((_, i) => next.add((page - 1) * PAGE_SIZE + i));
        return next;
      });
    }
  };

  const handleBatchDelete = async () => {
    setBatchDeleting(true);
    const toDelete = [...selected].map((idx) => filtered[idx]).filter(Boolean);
    let ok = 0;
    let fail = 0;
    for (const t of toDelete) {
      try {
        await api.deleteTriple(t);
        ok++;
      } catch {
        fail++;
      }
    }
    if (ok > 0) toast.success(`Deleted ${ok} triple${ok > 1 ? "s" : ""}`);
    if (fail > 0) toast.error(`Failed to delete ${fail} triple${fail > 1 ? "s" : ""}`);
    setSelected(new Set());
    setSelectedTriple(null);
    setBatchDeleting(false);
    refresh();
  };

  const sortIndicator = (col: string) => {
    if (sortCol !== col) return "";
    return sortDir === "asc" ? " ↑" : " ↓";
  };

  return (
    <div className="space-y-4">
      {/* Actions row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowFilters((s) => !s)}>
            <Filter className="h-4 w-4 mr-1" /> Filters
          </Button>
          {filtered.length !== triples.length && (
            <span className="text-xs text-muted-foreground">
              Showing {filtered.length} of {triples.length}
            </span>
          )}
          {filtered.length === triples.length && !loading && (
            <span className="text-xs text-muted-foreground">{triples.length} triples</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {selected.size > 0 && (
            <Button size="sm" variant="destructive" disabled={batchDeleting} onClick={() => setBatchDeleteConfirm(true)}>
              <Trash2 className="h-4 w-4 mr-1" /> Delete {selected.size}
            </Button>
          )}
          <Button size="sm" onClick={() => setAddOpen(true)}>
            <Plus className="h-4 w-4 mr-1" /> Add Triple
          </Button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex gap-3 rounded-md border p-3">
          <Input placeholder="Filter subject..." value={filterSubject} onChange={(e) => setFilterSubject(e.target.value)} className="text-sm" />
          <Input placeholder="Filter predicate..." value={filterPredicate} onChange={(e) => setFilterPredicate(e.target.value)} className="text-sm" />
          <Input placeholder="Filter object..." value={filterObject} onChange={(e) => setFilterObject(e.target.value)} className="text-sm" />
        </div>
      )}

      {/* Table + Detail Panel */}
      <div className="flex gap-4">
        {/* Table */}
        <div className="rounded-md border overflow-x-auto flex-1 min-w-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-border accent-primary"
                    checked={allOnPageSelected && paginated.length > 0}
                    onChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead className="cursor-pointer select-none" onClick={() => toggleSort("subject")}>
                  Subject{sortIndicator("subject")}
                </TableHead>
                <TableHead className="cursor-pointer select-none" onClick={() => toggleSort("predicate")}>
                  Predicate{sortIndicator("predicate")}
                </TableHead>
                <TableHead className="cursor-pointer select-none" onClick={() => toggleSort("object")}>
                  Object{sortIndicator("object")}
                </TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell />
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell />
                  </TableRow>
                ))
              ) : paginated.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5}>
                    <EmptyState
                      icon={Database}
                      title="No triples yet"
                      description="Add your first triple or extract from text."
                      actions={[
                        { label: "Add Triple", onClick: () => setAddOpen(true) },
                        ...(onNavigate ? [{ label: "Extract from Text", onClick: () => onNavigate("/extraction"), variant: "outline" as const }] : []),
                      ]}
                    />
                  </TableCell>
                </TableRow>
              ) : (
                paginated.map((t, i) => {
                  const globalIdx = (page - 1) * PAGE_SIZE + i;
                  return (
                    <TableRow
                      key={i}
                      className={cn(
                        "cursor-pointer",
                        selected.has(globalIdx) && "bg-accent/20",
                        isSelectedTriple(selectedTriple, t) && "bg-accent/30"
                      )}
                      onClick={(e) => {
                        if ((e.target as HTMLElement).closest("button") || (e.target as HTMLElement).closest("input")) return;
                        setSelectedTriple(isSelectedTriple(selectedTriple, t) ? null : t);
                      }}
                    >
                      <TableCell>
                        <input
                          type="checkbox"
                          className="h-4 w-4 rounded border-border accent-primary"
                          checked={selected.has(globalIdx)}
                          onChange={() => toggleSelect(globalIdx)}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-sm">{shortName(t.subject)}</TableCell>
                      <TableCell className="font-mono text-sm">{shortName(t.predicate)}</TableCell>
                      <TableCell className="font-mono text-sm">{shortName(t.object)}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="icon" onClick={() => setDeleteTarget(t)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

      </div>

      {/* Detail modal */}
      {selectedTriple && (
        <TripleDetailPanel
          triple={selectedTriple}
          onClose={() => setSelectedTriple(null)}
        />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}

      {/* Add triple dialog */}
      {addOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setAddOpen(false)} />
          <div className="relative rounded-lg border bg-background p-6 shadow-lg w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Add Triple</h3>
            <form onSubmit={handleAdd} className="space-y-3">
              <div className="space-y-1">
                <Label>Subject *</Label>
                <Input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="e.g. Mehdi" required />
              </div>
              <div className="space-y-1">
                <Label>Predicate *</Label>
                <Input value={predicate} onChange={(e) => setPredicate(e.target.value)} placeholder="e.g. founded" required />
              </div>
              <div className="space-y-1">
                <Label>Object *</Label>
                <Input value={object} onChange={(e) => setObject(e.target.value)} placeholder="e.g. BrandPulse" required />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setAddOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={adding || !subject || !predicate || !object}>
                  {adding ? "Adding..." : "Add"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Delete triple?"
        description={deleteTarget ? `This will remove: ${deleteTarget.subject} → ${deleteTarget.predicate} → ${deleteTarget.object}` : ""}
        onConfirm={() => { if (deleteTarget) handleDelete(deleteTarget); }}
      />

      {/* Batch delete confirmation */}
      <ConfirmDialog
        open={batchDeleteConfirm}
        onOpenChange={(open) => { if (!open) setBatchDeleteConfirm(false); }}
        title={`Delete ${selected.size} triple${selected.size > 1 ? "s" : ""}?`}
        description="This action cannot be undone."
        confirmLabel={`Delete ${selected.size}`}
        onConfirm={handleBatchDelete}
      />
    </div>
  );
}

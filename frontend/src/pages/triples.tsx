import { useCallback, useEffect, useState } from "react";
import { api } from "@/api/client";
import type { Triple } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Trash2 } from "lucide-react";

export function TriplesPage() {
  const [triples, setTriples] = useState<Triple[]>([]);
  const [loading, setLoading] = useState(true);

  // Add form state
  const [subject, setSubject] = useState("");
  const [predicate, setPredicate] = useState("");
  const [object, setObject] = useState("");

  // Filter state
  const [filterSubject, setFilterSubject] = useState("");
  const [filterPredicate, setFilterPredicate] = useState("");
  const [filterObject, setFilterObject] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAllTriples();
      setTriples(data);
    } catch (err) {
      console.error("Failed to load triples", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject || !predicate || !object) return;
    await api.addTriple({ subject, predicate, object });
    setSubject("");
    setPredicate("");
    setObject("");
    refresh();
  };

  const handleDelete = async (triple: Triple) => {
    await api.deleteTriple(triple);
    refresh();
  };

  const filtered = triples.filter((t) => {
    const s = filterSubject.toLowerCase();
    const p = filterPredicate.toLowerCase();
    const o = filterObject.toLowerCase();
    return (
      (!s || t.subject.toLowerCase().includes(s)) &&
      (!p || t.predicate.toLowerCase().includes(p)) &&
      (!o || t.object.toLowerCase().includes(o))
    );
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold tracking-tight">Triples</h2>

      {/* Add triple form */}
      <form onSubmit={handleAdd} className="flex gap-3 items-end">
        <div className="space-y-1">
          <Label htmlFor="subject">Subject</Label>
          <Input
            id="subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="e.g. Mehdi"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="predicate">Predicate</Label>
          <Input
            id="predicate"
            value={predicate}
            onChange={(e) => setPredicate(e.target.value)}
            placeholder="e.g. founded"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="object">Object</Label>
          <Input
            id="object"
            value={object}
            onChange={(e) => setObject(e.target.value)}
            placeholder="e.g. BrandPulse"
          />
        </div>
        <Button type="submit">Add</Button>
      </form>

      {/* Filter inputs */}
      <div className="flex gap-3">
        <Input
          placeholder="Filter subject…"
          value={filterSubject}
          onChange={(e) => setFilterSubject(e.target.value)}
          className="max-w-[200px]"
        />
        <Input
          placeholder="Filter predicate…"
          value={filterPredicate}
          onChange={(e) => setFilterPredicate(e.target.value)}
          className="max-w-[200px]"
        />
        <Input
          placeholder="Filter object…"
          value={filterObject}
          onChange={(e) => setFilterObject(e.target.value)}
          className="max-w-[200px]"
        />
      </div>

      {/* Triples table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Subject</TableHead>
              <TableHead>Predicate</TableHead>
              <TableHead>Object</TableHead>
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
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No triples found
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((t, i) => (
                <TableRow key={i}>
                  <TableCell className="font-mono text-sm">{t.subject}</TableCell>
                  <TableCell className="font-mono text-sm">{t.predicate}</TableCell>
                  <TableCell className="font-mono text-sm">{t.object}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(t)}
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
    </div>
  );
}

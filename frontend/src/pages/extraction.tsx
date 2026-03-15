import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/api/client";
import type { ExtractedTriple, PreviewTriple } from "@/types/graph";

export function ExtractionPage() {
  const [text, setText] = useState("");
  const [mode, setMode] = useState<"strict" | "open">("strict");
  const [preview, setPreview] = useState<PreviewTriple[] | null>(null);
  const [stored, setStored] = useState<ExtractedTriple[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handlePreview() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setStored(null);
    try {
      const results = await api.extractPreview({ text, mode });
      setPreview(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleExtract() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setPreview(null);
    try {
      const results = await api.extractAndStore({ text, mode });
      setStored(results);
      setText("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Extraction failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <h2 className="text-lg font-semibold">AI Triple Extraction</h2>

      {/* Input */}
      <div className="space-y-2">
        <Label htmlFor="extract-text">Paste unstructured text</Label>
        <Textarea
          id="extract-text"
          rows={6}
          placeholder="e.g. Mehdi established BrandPulse Analytics in 2023..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </div>

      {/* Mode toggle */}
      <div className="flex items-center gap-3">
        <Label>Mode:</Label>
        <Button
          size="sm"
          variant={mode === "strict" ? "default" : "outline"}
          onClick={() => setMode("strict")}
        >
          Strict
        </Button>
        <Button
          size="sm"
          variant={mode === "open" ? "default" : "outline"}
          onClick={() => setMode("open")}
        >
          Open
        </Button>
        <span className="text-xs text-muted-foreground ml-2">
          {mode === "strict"
            ? "Uses your ontology schema to constrain extraction"
            : "Freely extracts entities and relationships"}
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button onClick={handlePreview} disabled={loading || !text.trim()} variant="outline">
          {loading ? "Processing…" : "Preview"}
        </Button>
        <Button onClick={handleExtract} disabled={loading || !text.trim()}>
          {loading ? "Processing…" : "Extract & Store"}
        </Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Preview results */}
      {preview && preview.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Preview (not stored yet)</h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subject</TableHead>
                <TableHead>Predicate</TableHead>
                <TableHead>Object</TableHead>
                <TableHead>Disambiguation</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {preview.map((t, i) => (
                <TableRow key={i}>
                  <TableCell>{t.subject}</TableCell>
                  <TableCell>{t.predicate}</TableCell>
                  <TableCell>{t.object}</TableCell>
                  <TableCell className="text-xs space-y-1">
                    {t.subject_candidates.length > 0 && (
                      <div>
                        Subject matches:{" "}
                        {t.subject_candidates.map((c, j) => (
                          <Badge key={j} variant="outline" className="mr-1">
                            {c.name} ({(c.score * 100).toFixed(0)}%)
                          </Badge>
                        ))}
                      </div>
                    )}
                    {t.object_candidates.length > 0 && (
                      <div>
                        Object matches:{" "}
                        {t.object_candidates.map((c, j) => (
                          <Badge key={j} variant="outline" className="mr-1">
                            {c.name} ({(c.score * 100).toFixed(0)}%)
                          </Badge>
                        ))}
                      </div>
                    )}
                    {t.subject_candidates.length === 0 && t.object_candidates.length === 0 && (
                      <span className="text-muted-foreground">No existing matches</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {preview && preview.length === 0 && (
        <p className="text-sm text-muted-foreground">No triples extracted from the text.</p>
      )}

      {/* Stored results */}
      {stored && stored.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Stored triples</h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subject</TableHead>
                <TableHead>Predicate</TableHead>
                <TableHead>Object</TableHead>
                <TableHead>Disambiguation</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {stored.map((t, i) => (
                <TableRow key={i}>
                  <TableCell>{t.subject}</TableCell>
                  <TableCell>{t.predicate}</TableCell>
                  <TableCell>{t.object}</TableCell>
                  <TableCell className="text-xs">
                    {t.disambiguation.subject_matched && t.disambiguation.subject_matched !== t.disambiguation.subject_original && (
                      <div>
                        <Badge variant="secondary" className="mr-1">
                          {t.disambiguation.subject_original} → {t.disambiguation.subject_matched}
                        </Badge>
                        <span className="text-muted-foreground">
                          ({((t.disambiguation.subject_score ?? 0) * 100).toFixed(0)}%)
                        </span>
                      </div>
                    )}
                    {t.disambiguation.object_matched && t.disambiguation.object_matched !== t.disambiguation.object_original && (
                      <div>
                        <Badge variant="secondary" className="mr-1">
                          {t.disambiguation.object_original} → {t.disambiguation.object_matched}
                        </Badge>
                        <span className="text-muted-foreground">
                          ({((t.disambiguation.object_score ?? 0) * 100).toFixed(0)}%)
                        </span>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {stored && stored.length === 0 && (
        <p className="text-sm text-muted-foreground">No triples extracted from the text.</p>
      )}
    </div>
  );
}

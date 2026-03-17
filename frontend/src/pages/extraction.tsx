import { useState } from "react";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";
import { api } from "@/api/client";
import type { ExtractedTriple, PreviewTriple } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { PageTabs } from "@/components/ui/page-tabs";
import { cn } from "@/lib/utils";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

interface ExtractionPageProps {
  onNavigate?: (href: string) => void;
}

export function ExtractionPage({ onNavigate }: ExtractionPageProps) {
  const [text, setText] = useState("");
  const [mode, setMode] = useState<"strict" | "open">("strict");
  const [preview, setPreview] = useState<PreviewTriple[] | null>(null);
  const [stored, setStored] = useState<ExtractedTriple[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [resultTab, setResultTab] = useState("stored");

  async function handlePreview() {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const results = await api.extractPreview({ text, mode });
      setPreview(results);
      setResultTab("preview");
      if (results.length === 0) {
        toast.info("No triples found in the text");
      }
    } catch (e) {
      toast.error("Preview failed: " + (e instanceof Error ? e.message : "Unknown error"));
    } finally {
      setLoading(false);
    }
  }

  async function handleExtract() {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const results = await api.extractAndStore({ text, mode });
      setStored(results);
      setResultTab("stored");
      if (results.length > 0) {
        toast.success(`${results.length} triples extracted and stored`);
      } else {
        toast.info("No triples extracted from the text");
      }
    } catch (e) {
      toast.error("Extraction failed: " + (e instanceof Error ? e.message : "Unknown error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Input */}
      <div className="space-y-2">
        <Label htmlFor="extract-text">Paste unstructured text</Label>
        <Textarea
          id="extract-text"
          rows={6}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Mehdi established BrandPulse Analytics in 2023..."
        />
      </div>

      {/* Mode segmented control */}
      <div className="flex items-center gap-3">
        <Label>Mode:</Label>
        <div className="inline-flex rounded-md border p-0.5">
          {(["strict", "open"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={cn(
                "px-4 py-1.5 text-sm font-medium rounded-sm transition-colors capitalize",
                mode === m
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {m}
            </button>
          ))}
        </div>
        <span className="text-xs text-muted-foreground ml-2">
          {mode === "strict" ? "Constrained to ontology schema" : "Free extraction"}
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button onClick={handlePreview} disabled={loading || !text.trim()} variant="outline">
          {loading ? "Processing..." : "Preview"}
        </Button>
        <Button onClick={handleExtract} disabled={loading || !text.trim()}>
          <Sparkles className="h-4 w-4 mr-1" />
          {loading ? "Processing..." : "Extract & Store"}
        </Button>
      </div>

      {/* Success banner */}
      {stored && stored.length > 0 && (
        <div className="rounded-md border border-green-200 bg-green-50 dark:bg-green-950/30 p-4 flex items-center justify-between">
          <p className="text-sm font-medium text-green-800 dark:text-green-200">
            {stored.length} triples extracted and stored
          </p>
          <div className="flex gap-2">
            {onNavigate && (
              <Button size="sm" variant="outline" onClick={() => onNavigate("/triples")}>
                View in Triples
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setText("");
                setStored(null);
                setPreview(null);
              }}
            >
              Extract Another
            </Button>
          </div>
        </div>
      )}

      {/* Results tabs */}
      {(preview || stored) && (
        <div className="space-y-4">
          <PageTabs
            tabs={[
              { id: "stored", label: "Stored Results" },
              { id: "preview", label: "Preview" },
            ]}
            activeTab={resultTab}
            onTabChange={setResultTab}
          />

          {/* Stored results */}
          {resultTab === "stored" && stored && stored.length > 0 && (
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
                    <TableCell className="text-xs space-y-1">
                      {t.disambiguation.subject_matched &&
                        t.disambiguation.subject_matched !== t.disambiguation.subject_original && (
                          <div>
                            <Badge variant="secondary" className="mr-1">
                              {t.disambiguation.subject_original} → {t.disambiguation.subject_matched}
                            </Badge>
                            <span className="text-muted-foreground">
                              ({((t.disambiguation.subject_score ?? 0) * 100).toFixed(0)}%)
                            </span>
                          </div>
                        )}
                      {t.disambiguation.object_matched &&
                        t.disambiguation.object_matched !== t.disambiguation.object_original && (
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
          )}

          {resultTab === "stored" && stored && stored.length === 0 && (
            <p className="text-sm text-muted-foreground py-4 text-center">No triples extracted.</p>
          )}

          {resultTab === "stored" && !stored && (
            <p className="text-sm text-muted-foreground py-4 text-center">
              Run "Extract & Store" to see stored results.
            </p>
          )}

          {/* Preview results */}
          {resultTab === "preview" && preview && preview.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subject</TableHead>
                  <TableHead>Predicate</TableHead>
                  <TableHead>Object</TableHead>
                  <TableHead>Candidates</TableHead>
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
                          Subject:{" "}
                          {t.subject_candidates.map((c, j) => (
                            <Badge key={j} variant="outline" className="mr-1">
                              {c.name} ({(c.score * 100).toFixed(0)}%)
                            </Badge>
                          ))}
                        </div>
                      )}
                      {t.object_candidates.length > 0 && (
                        <div>
                          Object:{" "}
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
          )}

          {resultTab === "preview" && preview && preview.length === 0 && (
            <p className="text-sm text-muted-foreground py-4 text-center">No triples found in preview.</p>
          )}

          {resultTab === "preview" && !preview && (
            <p className="text-sm text-muted-foreground py-4 text-center">
              Run "Preview" to see extraction candidates.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

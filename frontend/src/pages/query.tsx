import { Suspense, lazy, useState } from "react";
import { toast } from "sonner";
import { Copy, Download, Info, ChevronDown } from "lucide-react";
import { api } from "@/api/client";
import type { QueryResult } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const SparqlEditor = lazy(() =>
  import("@/components/query/sparql-editor").then((m) => ({ default: m.SparqlEditor }))
);

export function QueryPage() {
  const [question, setQuestion] = useState("");
  const [sparqlInput, setSparqlInput] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [showSparql, setShowSparql] = useState(false);
  const [advancedMode, setAdvancedMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setExplanation(null);
    try {
      const res = await api.askWithExplanation(question);
      setResult({ results: res.results, sparql: res.sparql });
      setExplanation(res.explanation);
      setHistory((prev) => [question, ...prev.filter((q) => q !== question)].slice(0, 20));
    } catch (e) {
      toast.error("Query failed: " + (e instanceof Error ? e.message : "Unknown error"));
    } finally {
      setLoading(false);
    }
  }

  async function handleSparql() {
    if (!sparqlInput.trim()) return;
    setLoading(true);
    setExplanation(null);
    try {
      const res = await api.executeSparql(sparqlInput);
      setResult(res);
    } catch (e) {
      toast.error("SPARQL execution failed: " + (e instanceof Error ? e.message : "Unknown error"));
    } finally {
      setLoading(false);
    }
  }

  const copySparql = () => {
    if (result?.sparql) {
      navigator.clipboard.writeText(result.sparql);
      toast.success("SPARQL copied to clipboard");
    }
  };

  const exportCsv = () => {
    if (!result?.results.length) return;
    const headers = Object.keys(result.results[0]);
    const rows = result.results.map((r) =>
      headers.map((h) => `"${(r[h] ?? "").replace(/"/g, '""')}"`).join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "query-results.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const columns =
    result && result.results.length > 0 ? Object.keys(result.results[0]) : [];

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Mode toggle */}
      <div className="flex items-center justify-end">
        <Button size="sm" variant="outline" onClick={() => setAdvancedMode(!advancedMode)}>
          {advancedMode ? "Natural Language" : "Raw SPARQL"}
        </Button>
      </div>

      {/* Natural language mode */}
      {!advancedMode && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              className="text-lg py-3 flex-1"
              placeholder="Ask a question about your knowledge graph..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            />
            <Button onClick={handleAsk} disabled={loading || !question.trim()}>
              {loading ? "Thinking..." : "Ask"}
            </Button>
          </div>

          {/* Collapsible history */}
          {history.length > 0 && (
            <div>
              <button
                onClick={() => setShowHistory((s) => !s)}
                className="text-xs text-muted-foreground flex items-center gap-1 hover:text-foreground"
              >
                <ChevronDown
                  className={`h-3 w-3 transition-transform ${showHistory ? "rotate-180" : ""}`}
                />
                Recent Questions ({history.length})
              </button>
              {showHistory && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {history.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setQuestion(q)}
                      className="text-xs px-2 py-1 rounded-md bg-muted hover:bg-accent truncate max-w-50"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SPARQL mode with CodeMirror */}
      {advancedMode && (
        <div className="space-y-2">
          <Label>SPARQL Query (read-only SELECT only)</Label>
          <Suspense fallback={<Skeleton className="h-40 w-full" />}>
            <SparqlEditor value={sparqlInput} onChange={setSparqlInput} />
          </Suspense>
          <Button onClick={handleSparql} disabled={loading || !sparqlInput.trim()}>
            {loading ? "Executing..." : "Execute"}
          </Button>
        </div>
      )}

      {/* Generated SPARQL toggle (NL mode only) */}
      {result && !advancedMode && (
        <div>
          <Button size="sm" variant="ghost" onClick={() => setShowSparql(!showSparql)}>
            {showSparql ? "Hide SPARQL" : "Show SPARQL"}
          </Button>
          {showSparql && (
            <pre className="mt-2 rounded-md border p-3 bg-muted/50 text-xs font-mono overflow-x-auto whitespace-pre-wrap">
              {result.sparql}
            </pre>
          )}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Row count + action buttons */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              {result.results.length} results
            </span>
            <div className="flex gap-2">
              {result.sparql && (
                <Button size="sm" variant="outline" onClick={copySparql}>
                  <Copy className="h-3 w-3 mr-1" /> Copy SPARQL
                </Button>
              )}
              {result.results.length > 0 && (
                <Button size="sm" variant="outline" onClick={exportCsv}>
                  <Download className="h-3 w-3 mr-1" /> Export CSV
                </Button>
              )}
            </div>
          </div>

          {/* Results table */}
          {result.results.length > 0 && (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {columns.map((col) => (
                      <TableHead key={col}>{col}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.results.map((row, i) => (
                    <TableRow key={i}>
                      {columns.map((col) => (
                        <TableCell key={col} className="text-sm">
                          {row[col]}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {result.results.length === 0 && (
            <p className="text-sm text-muted-foreground">No results found.</p>
          )}

          {/* Explanation callout */}
          {explanation && (
            <div className="rounded-md bg-muted p-4 flex gap-3">
              <Info className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-sm">{explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

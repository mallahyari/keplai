import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import type { QueryResult } from "@/types/graph";

export function QueryPage() {
  const [question, setQuestion] = useState("");
  const [sparqlInput, setSparqlInput] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [showSparql, setShowSparql] = useState(false);
  const [advancedMode, setAdvancedMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setExplanation(null);
    try {
      const res = await api.askWithExplanation(question);
      setResult({ results: res.results, sparql: res.sparql });
      setExplanation(res.explanation);
      setHistory((prev) => [question, ...prev.filter((q) => q !== question)].slice(0, 20));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSparql() {
    if (!sparqlInput.trim()) return;
    setLoading(true);
    setError(null);
    setExplanation(null);
    try {
      const res = await api.executeSparql(sparqlInput);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "SPARQL execution failed");
    } finally {
      setLoading(false);
    }
  }

  const columns = result && result.results.length > 0 ? Object.keys(result.results[0]) : [];

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Query Knowledge Graph</h2>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setAdvancedMode(!advancedMode)}
        >
          {advancedMode ? "Natural Language" : "Raw SPARQL"}
        </Button>
      </div>

      {!advancedMode ? (
        /* Natural language mode */
        <div className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="Ask a question… e.g. What companies did Mehdi found?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              className="flex-1"
            />
            <Button onClick={handleAsk} disabled={loading || !question.trim()}>
              {loading ? "Thinking…" : "Ask"}
            </Button>
          </div>

          {/* Query history */}
          {history.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {history.map((q, i) => (
                <Badge
                  key={i}
                  variant="outline"
                  className="cursor-pointer hover:bg-accent"
                  onClick={() => setQuestion(q)}
                >
                  {q.length > 40 ? q.slice(0, 40) + "…" : q}
                </Badge>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Raw SPARQL mode */
        <div className="space-y-2">
          <Label>SPARQL Query (read-only SELECT only)</Label>
          <Textarea
            rows={6}
            placeholder="SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
            value={sparqlInput}
            onChange={(e) => setSparqlInput(e.target.value)}
            className="font-mono text-sm"
          />
          <Button onClick={handleSparql} disabled={loading || !sparqlInput.trim()}>
            {loading ? "Executing…" : "Execute"}
          </Button>
        </div>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Explanation */}
      {explanation && (
        <div className="rounded-md border p-3 bg-muted/50 text-sm">
          {explanation}
        </div>
      )}

      {/* Generated SPARQL toggle */}
      {result && !advancedMode && (
        <div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowSparql(!showSparql)}
          >
            {showSparql ? "Hide SPARQL" : "Show SPARQL"}
          </Button>
          {showSparql && (
            <pre className="mt-2 rounded-md border p-3 bg-muted/50 text-xs font-mono overflow-x-auto whitespace-pre-wrap">
              {result.sparql}
            </pre>
          )}
        </div>
      )}

      {/* Results table */}
      {result && result.results.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium">Results</h3>
            <Badge variant="secondary">{result.results.length}</Badge>
          </div>
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
        </div>
      )}

      {result && result.results.length === 0 && (
        <p className="text-sm text-muted-foreground">No results found.</p>
      )}
    </div>
  );
}

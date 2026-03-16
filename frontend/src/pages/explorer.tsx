import { useCallback, useEffect, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import type { Triple, GraphNode, GraphLink } from "@/types/graph";

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

function triplesToGraph(triples: Triple[]): GraphData {
  const nodeMap = new Map<string, GraphNode>();
  const links: GraphLink[] = [];

  for (const t of triples) {
    const sLabel = shortName(t.subject);
    const oLabel = shortName(t.object);

    if (!nodeMap.has(t.subject)) {
      nodeMap.set(t.subject, { id: t.subject, label: sLabel });
    }
    if (!nodeMap.has(t.object)) {
      nodeMap.set(t.object, { id: t.object, label: oLabel });
    }
    links.push({
      source: t.subject,
      target: t.object,
      label: shortName(t.predicate),
    });
  }

  return { nodes: Array.from(nodeMap.values()), links };
}

function shortName(uri: string): string {
  if (uri.includes("/")) return uri.split("/").pop() || uri;
  if (uri.includes("#")) return uri.split("#").pop() || uri;
  return uri;
}

export function ExplorerPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [allTriples, setAllTriples] = useState<Triple[]>([]);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [selectedTriples, setSelectedTriples] = useState<Triple[]>([]);
  const [loading, setLoading] = useState(true);
  const graphRef = useRef<any>(null);

  const loadTriples = useCallback(async () => {
    setLoading(true);
    try {
      const triples = await api.getAllTriples();
      setAllTriples(triples);
      setGraphData(triplesToGraph(triples));
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTriples();
  }, [loadTriples]);

  // Filter graph
  useEffect(() => {
    if (!filter.trim()) {
      setGraphData(triplesToGraph(allTriples));
      return;
    }
    const lower = filter.toLowerCase();
    const filtered = allTriples.filter(
      (t) =>
        shortName(t.subject).toLowerCase().includes(lower) ||
        shortName(t.predicate).toLowerCase().includes(lower) ||
        shortName(t.object).toLowerCase().includes(lower)
    );
    setGraphData(triplesToGraph(filtered));
  }, [filter, allTriples]);

  // Handle node click
  function handleNodeClick(node: any) {
    setSelected(node.id);
    const related = allTriples.filter(
      (t) => t.subject === node.id || t.object === node.id
    );
    setSelectedTriples(related);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Graph Explorer</h2>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Filter nodes…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-60"
          />
          <Button size="sm" variant="outline" onClick={loadTriples}>
            Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading graph…</p>
      ) : graphData.nodes.length === 0 ? (
        <p className="text-sm text-muted-foreground">No triples in the graph yet.</p>
      ) : (
        <div className="border rounded-md overflow-hidden bg-background" style={{ height: 500 }}>
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeLabel="label"
            nodeAutoColorBy="label"
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.label || "";
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              const isSelected = node.id === selected;

              // Node circle
              ctx.beginPath();
              ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI);
              ctx.fillStyle = isSelected ? "#f97316" : node.color || "#6366f1";
              ctx.fill();

              // Label
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = isSelected ? "#f97316" : "#a1a1aa";
              ctx.fillText(label, node.x, node.y + 9);
            }}
            linkLabel="label"
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkColor={() => "#52525b"}
            onNodeClick={handleNodeClick}
            width={undefined}
            height={500}
          />
        </div>
      )}

      {/* Stats */}
      <div className="flex gap-2">
        <Badge variant="secondary">{graphData.nodes.length} nodes</Badge>
        <Badge variant="secondary">{graphData.links.length} edges</Badge>
      </div>

      {/* Selected node details */}
      {selected && selectedTriples.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium">
              Triples for <span className="font-semibold">{shortName(selected)}</span>
            </h3>
            <Button size="sm" variant="ghost" onClick={() => setSelected(null)}>
              Clear
            </Button>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subject</TableHead>
                <TableHead>Predicate</TableHead>
                <TableHead>Object</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {selectedTriples.map((t, i) => (
                <TableRow key={i}>
                  <TableCell className="text-sm">{shortName(t.subject)}</TableCell>
                  <TableCell className="text-sm">{shortName(t.predicate)}</TableCell>
                  <TableCell className="text-sm">{shortName(t.object)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

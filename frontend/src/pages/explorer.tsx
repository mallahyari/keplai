import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { Plus, Minus, X, RefreshCw } from "lucide-react";
import { api } from "@/api/client";
import type { Triple, GraphNode, GraphLink } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const NODE_LIMIT = 200;

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

function shortName(uri: string): string {
  if (uri.includes("/")) return uri.split("/").pop() || uri;
  if (uri.includes("#")) return uri.split("#").pop() || uri;
  return uri;
}

function triplesToGraph(triples: Triple[], limit: number = NODE_LIMIT): GraphData {
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

    if (nodeMap.size >= limit) break;
  }

  // Only include links where both source and target are in the node set
  const nodeIds = new Set(nodeMap.keys());
  const filteredLinks = links.filter(
    (l) => nodeIds.has(l.source as string) && nodeIds.has(l.target as string)
  );

  return { nodes: Array.from(nodeMap.values()), links: filteredLinks };
}

export function ExplorerPage() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- react-force-graph-2d lacks typed refs
  const graphRef = useRef<any>(null);
  const [allTriples, setAllTriples] = useState<Triple[]>([]);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const triples = await api.getAllTriples();
      setAllTriples(triples);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Build graph with filter and limit
  const graphData = useMemo(() => {
    let triples = allTriples;
    if (filter.trim()) {
      const lower = filter.toLowerCase();
      triples = allTriples.filter(
        (t) =>
          shortName(t.subject).toLowerCase().includes(lower) ||
          shortName(t.predicate).toLowerCase().includes(lower) ||
          shortName(t.object).toLowerCase().includes(lower)
      );
    }
    return triplesToGraph(triples, NODE_LIMIT);
  }, [allTriples, filter]);

  // Total unique node count (before limit)
  const totalNodeCount = useMemo(() => {
    const nodeSet = new Set<string>();
    for (const t of allTriples) {
      nodeSet.add(t.subject);
      nodeSet.add(t.object);
    }
    return nodeSet.size;
  }, [allTriples]);

  // Connected triples for selected node
  const selectedTriples = useMemo(() => {
    if (!selected) return [];
    return allTriples.filter((t) => t.subject === selected || t.object === selected);
  }, [allTriples, selected]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- react-force-graph-2d node type
  const handleNodeClick = useCallback((node: any) => {
    setSelected((prev) => (prev === node.id ? null : node.id));
  }, []);

  const zoomIn = () => graphRef.current?.zoom(graphRef.current.zoom() * 1.5, 300);
  const zoomOut = () => graphRef.current?.zoom(graphRef.current.zoom() / 1.5, 300);

  return (
    <div className="space-y-4">
      {/* Controls row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Input
            placeholder="Filter nodes..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-64 text-sm"
          />
          <span className="text-xs text-muted-foreground">
            Showing {graphData.nodes.length} of {totalNodeCount} nodes
          </span>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-4 w-4 mr-1" /> Refresh
        </Button>
      </div>

      {/* Graph + detail panel side by side */}
      <div className="flex gap-4">
        {/* Graph container */}
        <div
          className="relative flex-1 rounded-md border bg-card overflow-hidden"
          style={{ height: 500 }}
        >
          {loading ? (
            <Skeleton className="h-full w-full" />
          ) : graphData.nodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
              No triples in the graph yet.
            </div>
          ) : (
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              onNodeClick={handleNodeClick}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any -- react-force-graph-2d callback types
              nodeLabel={(node: any) => node.label}
              nodeAutoColorBy="label"
              // eslint-disable-next-line @typescript-eslint/no-explicit-any -- react-force-graph-2d callback types
              nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                const label = node.label || "";
                const fontSize = 12 / globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                const isSelected = node.id === selected;

                ctx.beginPath();
                ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI);
                ctx.fillStyle = isSelected ? "#f97316" : node.color || "#6366f1";
                ctx.fill();

                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillStyle = isSelected ? "#f97316" : "#a1a1aa";
                ctx.fillText(label, node.x, node.y + 9);
              }}
              linkLabel="label"
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
              linkColor={() => "#52525b"}
              width={undefined}
              height={500}
            />
          )}

          {/* Zoom controls overlay */}
          <div className="absolute bottom-3 right-3 flex flex-col gap-1">
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={zoomIn}>
              <Plus className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={zoomOut}>
              <Minus className="h-4 w-4" />
            </Button>
          </div>

          {/* Legend overlay */}
          <div className="absolute top-3 right-3 rounded-md border bg-card/90 p-2 text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-indigo-500 inline-block" />
              <span>Entity</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-orange-500 inline-block" />
              <span>Selected</span>
            </div>
          </div>

          {/* Onboarding hint */}
          {!selected && !loading && graphData.nodes.length > 0 && (
            <p className="absolute bottom-3 left-3 text-xs text-muted-foreground bg-card/80 px-2 py-1 rounded">
              Click a node to see its connections
            </p>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="w-80 shrink-0 rounded-md border bg-card overflow-hidden">
            <div className="flex items-center justify-between p-3 border-b">
              <h3 className="text-sm font-medium truncate">{shortName(selected)}</h3>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => setSelected(null)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="overflow-y-auto" style={{ maxHeight: 450 }}>
              {selectedTriples.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-xs">Subject</TableHead>
                      <TableHead className="text-xs">Predicate</TableHead>
                      <TableHead className="text-xs">Object</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedTriples.map((t, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-xs font-mono">
                          {shortName(t.subject)}
                        </TableCell>
                        <TableCell className="text-xs font-mono">
                          {shortName(t.predicate)}
                        </TableCell>
                        <TableCell className="text-xs font-mono">
                          {shortName(t.object)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="p-3 text-xs text-muted-foreground">No connected triples.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

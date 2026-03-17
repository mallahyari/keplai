import { Tag } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import type { EntityContext as EntityContextType, Triple } from "@/types/graph";
import { shortName } from "@/lib/graph-utils";

interface EntityContextProps {
  context: EntityContextType | null | undefined;
  loading: boolean;
  error?: string;
  currentTriple?: Triple;
  onEntityClick?: (entityName: string) => void;
}

export function EntityContextSection({ context, loading, error, currentTriple, onEntityClick }: EntityContextProps) {
  if (loading) {
    return (
      <div className="space-y-2 p-3">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
      </div>
    );
  }

  if (error) {
    return <p className="p-3 text-xs text-muted-foreground">{error}</p>;
  }

  if (!context) return null;

  // Combine all related triples, excluding the currently viewed one
  const allTriples = [...context.triples_as_subject, ...context.triples_as_object];
  const filtered = currentTriple
    ? allTriples.filter(
        (t) =>
          !(t.subject === currentTriple.subject &&
            t.predicate === currentTriple.predicate &&
            t.object === currentTriple.object)
      )
    : allTriples;

  return (
    <div className="space-y-2 p-3">
      {/* Entity type badge */}
      {context.entity_type && (
        <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
          <Tag className="h-3 w-3" />
          {context.entity_type}
        </span>
      )}

      {/* Related triples mini-table */}
      {filtered.length > 0 ? (
        <div className="rounded border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-xs py-1">Subject</TableHead>
                <TableHead className="text-xs py-1">Predicate</TableHead>
                <TableHead className="text-xs py-1">Object</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((t, i) => (
                <TableRow key={i}>
                  <TableCell className="text-xs font-mono py-1">
                    <button
                      className="hover:text-primary hover:underline text-left"
                      onClick={() => onEntityClick?.(t.subject)}
                    >
                      {shortName(t.subject)}
                    </button>
                  </TableCell>
                  <TableCell className="text-xs font-mono py-1">
                    {shortName(t.predicate)}
                  </TableCell>
                  <TableCell className="text-xs font-mono py-1">
                    <button
                      className="hover:text-primary hover:underline text-left"
                      onClick={() => onEntityClick?.(t.object)}
                    >
                      {shortName(t.object)}
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No other connections found</p>
      )}

      {/* Similar entities */}
      {context.similar_entities.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-1">Similar entities</p>
          <div className="flex flex-wrap gap-1">
            {context.similar_entities.map((e) => (
              <button
                key={e.name}
                className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono hover:bg-muted/80"
                onClick={() => onEntityClick?.(e.name)}
              >
                {shortName(e.name)}
                <span className="ml-1 text-muted-foreground">
                  {Math.round(e.score * 100)}%
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

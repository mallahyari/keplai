import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { Triple } from "@/types/graph";
import { shortName } from "@/lib/graph-utils";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

interface RecentTriplesProps {
  onNavigate: (href: string) => void;
}

export function RecentTriples({ onNavigate }: RecentTriplesProps) {
  const [triples, setTriples] = useState<Triple[] | null>(null);

  useEffect(() => {
    api.getAllTriples()
      .then((data) => setTriples(data.slice(-10).reverse()))
      .catch(() => setTriples([]));
  }, []);

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="text-sm font-medium">Recent Triples</h3>
        <button
          onClick={() => onNavigate("/triples")}
          className="text-xs text-primary hover:underline"
        >
          View all
        </button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="text-xs">Subject</TableHead>
            <TableHead className="text-xs">Predicate</TableHead>
            <TableHead className="text-xs">Object</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {triples === null ? (
            Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={i}>
                <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                <TableCell><Skeleton className="h-4 w-32" /></TableCell>
              </TableRow>
            ))
          ) : triples.length === 0 ? (
            <TableRow>
              <TableCell colSpan={3} className="text-center text-xs text-muted-foreground py-6">
                No triples yet
              </TableCell>
            </TableRow>
          ) : (
            triples.map((t, i) => (
              <TableRow key={i}>
                <TableCell className="text-xs font-mono">{shortName(t.subject)}</TableCell>
                <TableCell className="text-xs font-mono">{shortName(t.predicate)}</TableCell>
                <TableCell className="text-xs font-mono">{shortName(t.object)}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}

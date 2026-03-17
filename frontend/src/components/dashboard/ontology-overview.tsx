import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { OntologyMetadata } from "@/types/graph";
import { Skeleton } from "@/components/ui/skeleton";
import { BookOpen } from "lucide-react";

interface OntologyOverviewProps {
  onNavigate: (href: string) => void;
}

export function OntologyOverview({ onNavigate }: OntologyOverviewProps) {
  const [ontologies, setOntologies] = useState<OntologyMetadata[] | null>(null);

  useEffect(() => {
    api.getOntologies()
      .then(setOntologies)
      .catch(() => setOntologies([]));
  }, []);

  if (ontologies === null) {
    return (
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Imported Ontologies</h3>
        <div className="flex gap-3 overflow-x-auto">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-48 shrink-0 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (ontologies.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-6 text-center">
        <BookOpen className="h-8 w-8 text-muted-foreground/50 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">No ontologies imported yet.</p>
        <button
          onClick={() => onNavigate("/ontology")}
          className="text-xs text-primary hover:underline mt-1"
        >
          Import your first ontology
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium">Imported Ontologies</h3>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {ontologies.map((ont) => (
          <div
            key={ont.id}
            className="shrink-0 rounded-lg border bg-card p-4 w-52 space-y-1"
          >
            <p className="text-sm font-medium truncate">{ont.name}</p>
            <p className="text-xs text-muted-foreground">
              {ont.classes_count} classes, {ont.properties_count} properties
            </p>
            <p className="text-xs text-muted-foreground">
              {new Date(ont.import_date).toLocaleDateString()}
            </p>
            <button
              onClick={() => onNavigate("/ontology")}
              className="text-xs text-primary hover:underline"
            >
              View Schema
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

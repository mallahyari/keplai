import { useState } from "react";
import { ChevronDown, ChevronRight, Clock, FileText, Upload, PenTool } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import type { ProvenanceRecord } from "@/types/graph";
import { cn } from "@/lib/utils";

const METHOD_STYLES: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  manual: { label: "Manual", color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300", icon: PenTool },
  extraction: { label: "Extraction", color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300", icon: FileText },
  import: { label: "Import", color: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300", icon: Upload },
};

interface ProvenanceCardProps {
  provenance: ProvenanceRecord | null | undefined;
  loading: boolean;
  error?: string;
}

export function ProvenanceCard({ provenance, loading, error }: ProvenanceCardProps) {
  const [sourceExpanded, setSourceExpanded] = useState(false);

  if (loading) {
    return (
      <div className="space-y-2 p-3">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-40" />
      </div>
    );
  }

  if (error) {
    return <p className="p-3 text-xs text-muted-foreground">{error}</p>;
  }

  if (!provenance) {
    return <p className="p-3 text-xs text-muted-foreground">No provenance recorded</p>;
  }

  const style = METHOD_STYLES[provenance.method] || METHOD_STYLES.manual;
  const Icon = style.icon;
  const createdDate = new Date(provenance.created_at).toLocaleDateString(undefined, {
    year: "numeric", month: "short", day: "numeric",
  });

  return (
    <div className="space-y-2 p-3">
      {/* Method badge + timestamp */}
      <div className="flex items-center gap-2">
        <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", style.color)}>
          <Icon className="h-3 w-3" />
          {style.label}
        </span>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {createdDate}
        </span>
      </div>

      {/* Source text (extraction only) */}
      {provenance.source_text && (
        <div>
          <button
            onClick={() => setSourceExpanded((s) => !s)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            {sourceExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            Source text
          </button>
          {sourceExpanded && (
            <p className="mt-1 rounded bg-muted/50 p-2 text-xs leading-relaxed">
              {provenance.source_text}
            </p>
          )}
        </div>
      )}

      {/* Disambiguation (extraction only) */}
      {provenance.disambiguation && (
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Disambiguation</p>
          <div className="flex flex-wrap gap-1">
            {provenance.disambiguation.subject_original && (
              <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono">
                {provenance.disambiguation.subject_original} → {provenance.disambiguation.subject_matched ?? "—"}
                {provenance.disambiguation.subject_score != null && (
                  <span className="ml-1 text-muted-foreground">({Math.round(provenance.disambiguation.subject_score * 100)}%)</span>
                )}
              </span>
            )}
            {provenance.disambiguation.object_original && (
              <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono">
                {provenance.disambiguation.object_original} → {provenance.disambiguation.object_matched ?? "—"}
                {provenance.disambiguation.object_score != null && (
                  <span className="ml-1 text-muted-foreground">({Math.round(provenance.disambiguation.object_score * 100)}%)</span>
                )}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Ontology source (import only) */}
      {provenance.ontology_source && (
        <p className="text-xs text-muted-foreground">
          Imported from <span className="font-mono">{provenance.ontology_source}</span>
        </p>
      )}
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";
import { X, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/api/client";
import type { Triple, ProvenanceRecord, EntityContext } from "@/types/graph";
import { shortName } from "@/lib/graph-utils";
import { ProvenanceCard } from "./provenance-card";
import { EntityContextSection } from "./entity-context";

interface TripleDetailPanelProps {
  triple: Triple;
  onClose: () => void;
}

export function TripleDetailPanel({ triple, onClose }: TripleDetailPanelProps) {
  // Provenance state
  const [provenance, setProvenance] = useState<ProvenanceRecord | null | undefined>(undefined);
  const [provLoading, setProvLoading] = useState(true);
  const [provError, setProvError] = useState<string>();

  // Entity context state
  const [subjectCtx, setSubjectCtx] = useState<EntityContext | null | undefined>(undefined);
  const [subjectLoading, setSubjectLoading] = useState(true);
  const [subjectError, setSubjectError] = useState<string>();

  const [objectCtx, setObjectCtx] = useState<EntityContext | null | undefined>(undefined);
  const [objectLoading, setObjectLoading] = useState(true);
  const [objectError, setObjectError] = useState<string>();

  // Entity hop state: null = showing triple view, string = showing entity view
  const [hoppedEntity, setHoppedEntity] = useState<string | null>(null);
  const [hoppedCtx, setHoppedCtx] = useState<EntityContext | null | undefined>(undefined);
  const [hoppedLoading, setHoppedLoading] = useState(false);
  const [hoppedError, setHoppedError] = useState<string>();

  // Load provenance
  useEffect(() => {
    setProvLoading(true);
    setProvError(undefined);
    api
      .getTripleProvenance(triple.subject, triple.predicate, triple.object)
      .then(setProvenance)
      .catch(() => setProvError("Failed to load provenance"))
      .finally(() => setProvLoading(false));
  }, [triple.subject, triple.predicate, triple.object]);

  // Load subject context
  useEffect(() => {
    setSubjectLoading(true);
    setSubjectError(undefined);
    api
      .getEntityContext(triple.subject)
      .then(setSubjectCtx)
      .catch(() => setSubjectError("Failed to load context"))
      .finally(() => setSubjectLoading(false));
  }, [triple.subject]);

  // Load object context
  useEffect(() => {
    setObjectLoading(true);
    setObjectError(undefined);
    api
      .getEntityContext(triple.object)
      .then(setObjectCtx)
      .catch(() => setObjectError("Failed to load context"))
      .finally(() => setObjectLoading(false));
  }, [triple.object]);

  // Entity hop handler
  const handleEntityClick = useCallback((entityName: string) => {
    setHoppedEntity(entityName);
    setHoppedLoading(true);
    setHoppedError(undefined);
    api
      .getEntityContext(entityName)
      .then(setHoppedCtx)
      .catch(() => setHoppedError("Failed to load entity context"))
      .finally(() => setHoppedLoading(false));
  }, []);

  const handleBack = () => {
    setHoppedEntity(null);
    setHoppedCtx(undefined);
  };

  return (
    <div className="w-96 shrink-0 rounded-md border bg-card overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b shrink-0">
        {hoppedEntity ? (
          <div className="flex items-center gap-2 min-w-0">
            <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={handleBack}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h3 className="text-sm font-medium truncate">Entity: {shortName(hoppedEntity)}</h3>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-sm font-medium min-w-0 truncate">
            <span className="font-mono truncate">{shortName(triple.subject)}</span>
            <span className="text-muted-foreground">→</span>
            <span className="font-mono truncate">{shortName(triple.predicate)}</span>
            <span className="text-muted-foreground">→</span>
            <span className="font-mono truncate">{shortName(triple.object)}</span>
          </div>
        )}
        <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0 ml-2" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Scrollable content */}
      <div className="overflow-y-auto flex-1">
        {hoppedEntity ? (
          /* Entity hop view */
          <EntityContextSection
            context={hoppedCtx}
            loading={hoppedLoading}
            error={hoppedError}
            onEntityClick={handleEntityClick}
          />
        ) : (
          /* Triple detail view */
          <>
            {/* Provenance */}
            <div className="border-b">
              <p className="px-3 pt-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Provenance</p>
              <ProvenanceCard provenance={provenance} loading={provLoading} error={provError} />
            </div>

            {/* Subject context */}
            <div className="border-b">
              <p className="px-3 pt-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                About {shortName(triple.subject)}
              </p>
              <EntityContextSection
                context={subjectCtx}
                loading={subjectLoading}
                error={subjectError}
                currentTriple={triple}
                onEntityClick={handleEntityClick}
              />
            </div>

            {/* Object context */}
            <div>
              <p className="px-3 pt-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                About {shortName(triple.object)}
              </p>
              <EntityContextSection
                context={objectCtx}
                loading={objectLoading}
                error={objectError}
                currentTriple={triple}
                onEntityClick={handleEntityClick}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

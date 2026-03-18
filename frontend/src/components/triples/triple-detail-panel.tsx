import { useCallback, useEffect, useState } from "react";
import { X, ArrowLeft, Copy, Check, Loader2 } from "lucide-react";
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

function CopyableUri({ label, uri }: { label: string; uri: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(uri);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="space-y-0.5">
      <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
      <div className="flex items-start gap-1.5 group">
        <p className="text-xs font-mono break-all leading-relaxed flex-1">{uri}</p>
        <button
          onClick={handleCopy}
          className="shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
          title="Copy URI"
        >
          {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
        </button>
      </div>
    </div>
  );
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
    setProvLoading(true); // eslint-disable-line react-hooks/set-state-in-effect -- reset loading state on dependency change
    setProvError(undefined);
    api
      .getTripleProvenance(triple.subject, triple.predicate, triple.object)
      .then(setProvenance)
      .catch(() => setProvError("Failed to load provenance"))
      .finally(() => setProvLoading(false));
  }, [triple.subject, triple.predicate, triple.object]);

  // Load subject context
  useEffect(() => {
    setSubjectLoading(true); // eslint-disable-line react-hooks/set-state-in-effect -- reset loading state on dependency change
    setSubjectError(undefined);
    api
      .getEntityContext(triple.subject)
      .then(setSubjectCtx)
      .catch(() => setSubjectError("Failed to load context"))
      .finally(() => setSubjectLoading(false));
  }, [triple.subject]);

  // Load object context
  useEffect(() => {
    setObjectLoading(true); // eslint-disable-line react-hooks/set-state-in-effect -- reset loading state on dependency change
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

  const initialLoading = provLoading || subjectLoading || objectLoading;

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative rounded-lg bg-background shadow-xl w-full max-w-2xl max-h-[85vh] min-h-[50vh] mx-6 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b shrink-0">
          {hoppedEntity ? (
            <div className="flex items-center gap-2 min-w-0">
              <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={handleBack}>
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <h3 className="text-sm font-semibold">Entity: {shortName(hoppedEntity)}</h3>
            </div>
          ) : (
            <h3 className="text-sm font-semibold">Triple Details</h3>
          )}
          <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Scrollable content */}
        <div className="overflow-y-auto flex-1">
          {initialLoading && !hoppedEntity ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : hoppedEntity ? (
            /* Entity hop view */
            <div className="p-4">
              <CopyableUri label="Entity URI" uri={hoppedEntity} />
              <div className="mt-4">
                <EntityContextSection
                  context={hoppedCtx}
                  loading={hoppedLoading}
                  error={hoppedError}
                  onEntityClick={handleEntityClick}
                />
              </div>
            </div>
          ) : (
            /* Triple detail view */
            <>
              {/* Full URIs */}
              <div className="p-4 border-b space-y-3 bg-muted/30">
                <CopyableUri label="Subject" uri={triple.subject} />
                <CopyableUri label="Predicate" uri={triple.predicate} />
                <CopyableUri label="Object" uri={triple.object} />
              </div>

              {/* Provenance */}
              <div className="border-b">
                <p className="px-4 pt-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">Provenance</p>
                <ProvenanceCard provenance={provenance} loading={provLoading} error={provError} />
              </div>

              {/* Subject context */}
              <div className="border-b">
                <p className="px-4 pt-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
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
              <div className="pb-6">
                <p className="px-4 pt-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
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
    </div>
  );
}

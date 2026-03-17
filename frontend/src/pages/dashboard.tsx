import { useEffect, useState } from "react";
import { Database, Users, BookOpen, Network } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/api/client";
import type { GraphStats } from "@/types/graph";
import { StatCard } from "@/components/dashboard/stat-card";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentTriples } from "@/components/dashboard/recent-triples";
import { OntologyOverview } from "@/components/dashboard/ontology-overview";

interface DashboardPageProps {
  onNavigate: (href: string) => void;
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const [stats, setStats] = useState<GraphStats | null>(null);

  useEffect(() => {
    api.getStats()
      .then(setStats)
      .catch((err) => {
        toast.error("Failed to load stats: " + (err instanceof Error ? err.message : "Unknown error"));
      });
  }, []);

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Database}
          value={stats?.triple_count ?? null}
          label="Total Triples"
          tint="bg-blue-50 dark:bg-blue-950/30"
          onClick={() => onNavigate("/triples")}
        />
        <StatCard
          icon={Users}
          value={stats?.entity_count ?? null}
          label="Unique Entities"
          tint="bg-emerald-50 dark:bg-emerald-950/30"
          onClick={() => onNavigate("/triples")}
        />
        <StatCard
          icon={BookOpen}
          value={stats?.ontology_count ?? null}
          label="Imported Ontologies"
          tint="bg-amber-50 dark:bg-amber-950/30"
          onClick={() => onNavigate("/ontology")}
        />
        <StatCard
          icon={Network}
          value={stats !== null ? stats.class_count + stats.property_count : null}
          label="Classes & Properties"
          tint="bg-purple-50 dark:bg-purple-950/30"
          onClick={() => onNavigate("/ontology")}
        />
      </div>

      {/* Middle row */}
      <div className="grid lg:grid-cols-[3fr_2fr] gap-4">
        <RecentTriples onNavigate={onNavigate} />
        <QuickActions onNavigate={onNavigate} />
      </div>

      {/* Ontology overview */}
      <OntologyOverview onNavigate={onNavigate} />
    </div>
  );
}

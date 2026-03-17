import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
  icon: LucideIcon;
  value: number | null;
  label: string;
  tint?: string;
  onClick?: () => void;
}

export function StatCard({ icon: Icon, value, label, tint, onClick }: StatCardProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-4 rounded-lg border p-5 text-left transition-colors hover:bg-accent/50 w-full",
        tint ?? "bg-card"
      )}
    >
      <div className="rounded-md bg-muted p-2.5">
        <Icon className="h-5 w-5 text-muted-foreground" />
      </div>
      <div>
        {value === null ? (
          <Skeleton className="h-7 w-12 mb-1" />
        ) : (
          <p className="text-2xl font-bold">{value}</p>
        )}
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </button>
  );
}

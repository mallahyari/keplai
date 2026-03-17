import { Database, Sparkles, BookOpen, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QuickActionsProps {
  onNavigate: (href: string) => void;
}

export function QuickActions({ onNavigate }: QuickActionsProps) {
  const actions = [
    { icon: Database, label: "Add Triple", href: "/triples" },
    { icon: Sparkles, label: "Extract from Text", href: "/extraction" },
    { icon: BookOpen, label: "Import Ontology", href: "/ontology" },
    { icon: MessageSquare, label: "Ask a Question", href: "/query" },
  ];

  return (
    <div className="rounded-lg border bg-card">
      <div className="p-4 border-b">
        <h3 className="text-sm font-medium">Quick Actions</h3>
      </div>
      <div className="p-4 grid grid-cols-2 gap-2">
        {actions.map((a) => (
          <Button
            key={a.href}
            variant="outline"
            className="flex items-center gap-2 h-auto py-3 justify-start"
            onClick={() => onNavigate(a.href)}
          >
            <a.icon className="h-4 w-4" />
            <span className="text-xs">{a.label}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}

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
    <div className="flex items-center gap-2">
      {actions.map((a) => (
        <Button
          key={a.href}
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => onNavigate(a.href)}
        >
          <a.icon className="h-3.5 w-3.5" />
          {a.label}
        </Button>
      ))}
    </div>
  );
}

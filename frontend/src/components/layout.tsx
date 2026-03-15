import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useEngineStatus } from "@/hooks/use-engine-status";
import { useHashRoute } from "@/hooks/use-hash-route";

function NavLink({ href, children }: { href: string; children: ReactNode }) {
  const route = useHashRoute();
  const active = route === href;
  return (
    <a
      href={`#${href}`}
      className={active ? "text-foreground font-medium" : "hover:text-foreground transition-colors"}
    >
      {children}
    </a>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const status = useEngineStatus();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold tracking-tight">KeplAI</h1>
          <Separator orientation="vertical" className="h-6" />
          <nav className="flex gap-4 text-sm text-muted-foreground">
            <NavLink href="/">Triples</NavLink>
            <NavLink href="/ontology">Ontology</NavLink>
            <NavLink href="/extraction">Extraction</NavLink>
            <NavLink href="/query">Query</NavLink>
            <NavLink href="/explorer">Explorer</NavLink>
          </nav>
        </div>
        <Badge variant={status?.healthy ? "default" : "destructive"}>
          {status?.healthy ? "Engine Online" : "Engine Offline"}
        </Badge>
      </header>

      {/* Main content */}
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}

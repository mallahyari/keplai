import type { ReactNode } from "react";
import { Toaster } from "sonner";
import { Sidebar } from "./sidebar";

const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/triples": "Triples",
  "/ontology": "Ontology",
  "/extraction": "Extraction",
  "/query": "Query",
  "/explorer": "Explorer",
};

interface AppShellProps {
  currentRoute: string;
  onNavigate: (href: string) => void;
  headerAction?: ReactNode;
  children: ReactNode;
}

export function AppShell({ currentRoute, onNavigate, headerAction, children }: AppShellProps) {
  const pageTitle = PAGE_TITLES[currentRoute] ?? "KeplAI";

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar currentRoute={currentRoute} onNavigate={onNavigate} />

      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top header bar */}
        <header className="flex items-center justify-between h-14 border-b px-6 shrink-0 bg-background">
          <h1 className="text-lg font-semibold">{pageTitle}</h1>
          {headerAction && <div>{headerAction}</div>}
        </header>

        {/* Content area */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1200px] p-6">
            {children}
          </div>
        </main>
      </div>

      <Toaster
        position="bottom-right"
        richColors
        closeButton
        toastOptions={{ classNames: { error: "!duration-[999999ms]" } }}
      />
    </div>
  );
}

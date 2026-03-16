# Frontend UX Overhaul Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the KeplAI frontend from a basic functional UI into a polished application with sidebar navigation, dashboard home page, toast notifications, loading skeletons, delete confirmations, and improved UX across all 5 existing pages.

**Architecture:** Replace the current top-nav Layout with a collapsible sidebar AppShell. Add shared UX primitives (toasts, confirm dialogs, skeletons, empty states) that all pages consume. Add a new Dashboard page as the landing page. Refactor each existing page to use the new patterns. Add one new backend endpoint for dashboard stats.

**Tech Stack:** React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Vite 7, sonner (toasts), CodeMirror (SPARQL editor), lucide-react (icons)

**Spec:** `docs/superpowers/specs/2026-03-16-frontend-ux-overhaul-design.md`

---

## Chunk 1: Foundation — Dependencies, Shared UI Components, Backend Stats Endpoint

### Task 1: Install New Dependencies

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install sonner**

```bash
cd frontend && npm install sonner
```

- [ ] **Step 2: Install CodeMirror packages**

```bash
cd frontend && npm install codemirror @codemirror/view @codemirror/state @codemirror/lang-sql @codemirror/basic-setup
```

- [ ] **Step 3: Verify build succeeds**

```bash
cd frontend && npm run build
```
Expected: Build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add sonner and codemirror dependencies"
```

---

### Task 2: Create Skeleton Component

**Files:**
- Create: `frontend/src/components/ui/skeleton.tsx`

- [ ] **Step 1: Create the Skeleton component**

```tsx
// frontend/src/components/ui/skeleton.tsx
import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  );
}

export { Skeleton };
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/skeleton.tsx
git commit -m "feat(ui): add Skeleton loading component"
```

---

### Task 3: Create ConfirmDialog Component

**Files:**
- Create: `frontend/src/components/ui/confirm-dialog.tsx`

- [ ] **Step 1: Create the ConfirmDialog component**

Uses native HTML `<dialog>` element + Tailwind for styling (no Radix dependency needed).

```tsx
// frontend/src/components/ui/confirm-dialog.tsx
import { useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Delete",
  onConfirm,
}: ConfirmDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    else if (!open && dialog.open) dialog.close();
  }, [open]);

  const handleClose = useCallback(() => onOpenChange(false), [onOpenChange]);

  return (
    <dialog
      ref={ref}
      onClose={handleClose}
      className="rounded-lg border bg-background p-0 shadow-lg backdrop:bg-black/50"
    >
      <div className="p-6 space-y-4 max-w-md">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={() => {
              onConfirm();
              handleClose();
            }}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </dialog>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/confirm-dialog.tsx
git commit -m "feat(ui): add ConfirmDialog component"
```

---

### Task 4: Create EmptyState Component

**Files:**
- Create: `frontend/src/components/ui/empty-state.tsx`

- [ ] **Step 1: Create the EmptyState component**

```tsx
// frontend/src/components/ui/empty-state.tsx
import type { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateAction {
  label: string;
  onClick: () => void;
  variant?: "default" | "outline";
}

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  actions?: EmptyStateAction[];
}

export function EmptyState({ icon: Icon, title, description, actions }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Icon className="h-12 w-12 text-muted-foreground/50 mb-4" />
      <h3 className="text-lg font-medium">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mt-1 max-w-sm">{description}</p>
      )}
      {actions && actions.length > 0 && (
        <div className="flex gap-2 mt-4">
          {actions.map((action) => (
            <Button
              key={action.label}
              variant={action.variant ?? "default"}
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/empty-state.tsx
git commit -m "feat(ui): add EmptyState component"
```

---

### Task 5: Create PageTabs Component

**Files:**
- Create: `frontend/src/components/ui/page-tabs.tsx`

- [ ] **Step 1: Create the PageTabs component**

Built with plain HTML + Tailwind (no Radix/Base UI needed for simple tabs).

```tsx
// frontend/src/components/ui/page-tabs.tsx
import { cn } from "@/lib/utils";

interface Tab {
  id: string;
  label: string;
}

interface PageTabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (id: string) => void;
}

export function PageTabs({ tabs, activeTab, onTabChange }: PageTabsProps) {
  return (
    <div className="border-b">
      <nav className="flex gap-0 -mb-px" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "px-4 py-2.5 text-sm font-medium border-b-2 transition-colors",
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
            )}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/page-tabs.tsx
git commit -m "feat(ui): add PageTabs component"
```

---

### Task 6: Backend Stats Endpoint

**Files:**
- Modify: `api/routers/graph.py`
- Modify: `api/schemas.py`
- Modify: `tests/unit/test_api.py`

- [ ] **Step 1: Add StatsResponse schema**

Add to `api/schemas.py` after `StatusResponse`:

```python
class StatsResponse(BaseModel):
    triple_count: int
    entity_count: int
    ontology_count: int
    class_count: int
    property_count: int
```

- [ ] **Step 2: Add stats endpoint**

Add to `api/routers/graph.py`:

```python
from api.schemas import StatsResponse

@router.get("/stats", response_model=StatsResponse)
def get_stats(graph: KeplAI = Depends(get_graph)):
    triples = graph.get_all_triples()
    ontologies = graph.ontology.list_ontologies()
    schema = graph.ontology.get_schema()
    entities = set()
    for t in triples:
        entities.add(t.get("s", t.get("subject", "")))
        entities.add(t.get("o", t.get("object", "")))
    return {
        "triple_count": len(triples),
        "entity_count": len(entities),
        "ontology_count": len(ontologies),
        "class_count": len(schema.get("classes", [])),
        "property_count": len(schema.get("properties", [])),
    }
```

- [ ] **Step 3: Add test for stats endpoint**

Add to `tests/unit/test_api.py`:

```python
def test_get_stats(client, mock_graph):
    mock_graph.ontology.list_ontologies.return_value = [
        {"id": "test-id", "name": "Test", "source": "test.ttl",
         "graph_uri": "http://keplai.io/graph/test",
         "import_date": "2026-03-15T00:00:00Z",
         "classes_count": 2, "properties_count": 3}
    ]
    resp = client.get("/api/graph/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["triple_count"] == 1
    assert data["entity_count"] == 2  # Mehdi + BrandPulse from mock
    assert data["ontology_count"] == 1
    assert data["class_count"] == 1
    assert data["property_count"] == 1
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/mehdiallahyari/environments/uv_projects/keplai && /Users/mehdiallahyari/environments/uv_projects/.venv/bin/python -m pytest tests/unit/test_api.py -v
```
Expected: All tests pass including `test_get_stats`.

- [ ] **Step 5: Add frontend API client and types**

Add to `frontend/src/types/graph.ts`:

```typescript
export interface GraphStats {
  triple_count: number;
  entity_count: number;
  ontology_count: number;
  class_count: number;
  property_count: number;
}
```

Add to the `api` object in `frontend/src/api/client.ts`:

```typescript
import type { GraphStats } from "@/types/graph";

// Inside api object:
getStats: () => request<GraphStats>(`${BASE}/stats`),
```

- [ ] **Step 6: Verify frontend build**

```bash
cd frontend && npm run build
```

- [ ] **Step 7: Commit**

```bash
git add api/routers/graph.py api/schemas.py tests/unit/test_api.py frontend/src/types/graph.ts frontend/src/api/client.ts
git commit -m "feat: add /api/graph/stats endpoint and frontend client"
```

---

## Chunk 2: Layout Shell — AppShell, Sidebar, Header

### Task 7: Create Sidebar Component

**Files:**
- Create: `frontend/src/components/layout/sidebar.tsx`
- Create: `frontend/src/components/layout/sidebar-item.tsx`

- [ ] **Step 1: Create SidebarItem**

```tsx
// frontend/src/components/layout/sidebar-item.tsx
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarItemProps {
  icon: LucideIcon;
  label: string;
  href: string;
  active: boolean;
  collapsed: boolean;
  onClick: () => void;
}

export function SidebarItem({ icon: Icon, label, active, collapsed, onClick }: SidebarItemProps) {
  return (
    <button
      onClick={onClick}
      title={collapsed ? label : undefined}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors w-full text-left",
        active
          ? "bg-accent text-accent-foreground"
          : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
    </button>
  );
}
```

- [ ] **Step 2: Create Sidebar**

```tsx
// frontend/src/components/layout/sidebar.tsx
import { useState, useEffect } from "react";
import {
  LayoutDashboard, Database, Sparkles, BookOpen, MessageSquare, Globe,
  ChevronsLeft, ChevronsRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { SidebarItem } from "./sidebar-item";
import { useEngineStatus } from "@/hooks/use-engine-status";

const NAV_GROUPS = [
  {
    label: "Overview",
    items: [
      { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    ],
  },
  {
    label: "Data",
    items: [
      { icon: Database, label: "Triples", href: "/triples" },
      { icon: Sparkles, label: "Extraction", href: "/extraction" },
    ],
  },
  {
    label: "Schema",
    items: [
      { icon: BookOpen, label: "Ontology", href: "/ontology" },
    ],
  },
  {
    label: "Explore",
    items: [
      { icon: MessageSquare, label: "Query", href: "/query" },
      { icon: Globe, label: "Explorer", href: "/explorer" },
    ],
  },
];

interface SidebarProps {
  currentRoute: string;
  onNavigate: (href: string) => void;
}

export function Sidebar({ currentRoute, onNavigate }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("sidebar-collapsed") === "true";
  });
  const status = useEngineStatus();

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  // Auto-collapse on small screens
  useEffect(() => {
    const mql = window.matchMedia("(max-width: 1024px)");
    const handler = (e: MediaQueryListEvent) => setCollapsed(e.matches);
    mql.addEventListener("change", handler);
    if (mql.matches) setCollapsed(true);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return (
    <aside
      className={cn(
        "flex flex-col h-screen border-r bg-card transition-[width] duration-200 ease-in-out shrink-0",
        collapsed ? "w-[60px]" : "w-[240px]"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 h-14 border-b shrink-0">
        <span className="text-lg font-bold">K</span>
        {!collapsed && <span className="font-semibold tracking-tight">KeplAI</span>}
      </div>

      {/* Engine status */}
      <div className="px-4 py-2 shrink-0">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "h-2 w-2 rounded-full shrink-0",
              status?.healthy ? "bg-green-500" : "bg-red-500"
            )}
          />
          {!collapsed && (
            <span className="text-xs text-muted-foreground">
              {status?.healthy ? "Online" : "Offline"}
            </span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <p className="px-3 mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {group.label}
              </p>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <SidebarItem
                  key={item.href}
                  icon={item.icon}
                  label={item.label}
                  href={item.href}
                  active={currentRoute === item.href}
                  collapsed={collapsed}
                  onClick={() => onNavigate(item.href)}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="flex items-center justify-center h-10 border-t text-muted-foreground hover:text-foreground transition-colors shrink-0"
      >
        {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
      </button>
    </aside>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/sidebar.tsx frontend/src/components/layout/sidebar-item.tsx
git commit -m "feat(layout): add collapsible Sidebar with grouped navigation"
```

---

### Task 8: Create AppShell and Wire Up Routing

**Files:**
- Create: `frontend/src/components/layout/app-shell.tsx`
- Modify: `frontend/src/App.tsx`
- Delete: `frontend/src/components/layout.tsx` (after migration)

- [ ] **Step 1: Create AppShell**

```tsx
// frontend/src/components/layout/app-shell.tsx
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
```

- [ ] **Step 2: Update App.tsx to use AppShell**

Replace the entire content of `frontend/src/App.tsx`:

```tsx
// frontend/src/App.tsx
import { useHashRoute } from "@/hooks/use-hash-route";
import { AppShell } from "@/components/layout/app-shell";
import { TriplesPage } from "@/pages/triples";
import { OntologyPage } from "@/pages/ontology";
import { ExtractionPage } from "@/pages/extraction";
import { QueryPage } from "@/pages/query";
import { ExplorerPage } from "@/pages/explorer";

function App() {
  const route = useHashRoute();

  const navigate = (href: string) => {
    window.location.hash = href;
  };

  let page: React.ReactNode;
  switch (route) {
    case "/triples":
      page = <TriplesPage onNavigate={navigate} />;
      break;
    case "/ontology":
      page = <OntologyPage />;
      break;
    case "/extraction":
      page = <ExtractionPage onNavigate={navigate} />;
      break;
    case "/query":
      page = <QueryPage />;
      break;
    case "/explorer":
      page = <ExplorerPage />;
      break;
    default:
      // Dashboard placeholder — will be built in Task 9
      page = <div className="text-muted-foreground">Dashboard coming soon...</div>;
      break;
  }

  return (
    <AppShell currentRoute={route} onNavigate={navigate}>
      {page}
    </AppShell>
  );
}

export default App;
```

Note: `TriplesPage` and `ExtractionPage` receive `onNavigate` for cross-page navigation (e.g., "View in Triples" link, "Extract from Text" empty state button). Other pages don't need it.

- [ ] **Step 3: Delete old layout.tsx**

```bash
rm frontend/src/components/layout.tsx
```

- [ ] **Step 4: Verify build and visual check**

```bash
cd frontend && npm run build
```
Expected: Build succeeds. Old Layout component is gone, AppShell renders sidebar + header + content.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/layout/app-shell.tsx frontend/src/App.tsx
git rm frontend/src/components/layout.tsx
git commit -m "feat(layout): replace top-nav with AppShell sidebar layout"
```

---

## Chunk 3: Dashboard Page

### Task 9: Create Dashboard Page with Stat Cards, Recent Triples, Quick Actions, Ontology Overview

**Files:**
- Create: `frontend/src/components/dashboard/stat-card.tsx`
- Create: `frontend/src/components/dashboard/quick-actions.tsx`
- Create: `frontend/src/components/dashboard/recent-triples.tsx`
- Create: `frontend/src/components/dashboard/ontology-overview.tsx`
- Create: `frontend/src/pages/dashboard.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create StatCard**

```tsx
// frontend/src/components/dashboard/stat-card.tsx
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
  icon: LucideIcon;
  value: number | null;
  label: string;
  tint?: string; // e.g. "bg-blue-50 dark:bg-blue-950/30"
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
```

- [ ] **Step 2: Create QuickActions**

```tsx
// frontend/src/components/dashboard/quick-actions.tsx
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
```

- [ ] **Step 3: Create RecentTriples**

```tsx
// frontend/src/components/dashboard/recent-triples.tsx
import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { Triple } from "@/types/graph";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

interface RecentTriplesProps {
  onNavigate: (href: string) => void;
}

export function RecentTriples({ onNavigate }: RecentTriplesProps) {
  const [triples, setTriples] = useState<Triple[] | null>(null);

  useEffect(() => {
    api.getAllTriples()
      .then((data) => setTriples(data.slice(-10).reverse()))
      .catch(() => setTriples([]));
  }, []);

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="text-sm font-medium">Recent Triples</h3>
        <button
          onClick={() => onNavigate("/triples")}
          className="text-xs text-primary hover:underline"
        >
          View all
        </button>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">Subject</TableHead>
              <TableHead className="text-xs">Predicate</TableHead>
              <TableHead className="text-xs">Object</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {triples === null ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                </TableRow>
              ))
            ) : triples.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-xs text-muted-foreground py-6">
                  No triples yet
                </TableCell>
              </TableRow>
            ) : (
              triples.map((t, i) => (
                <TableRow key={i}>
                  <TableCell className="text-xs font-mono truncate max-w-[150px]">{t.subject}</TableCell>
                  <TableCell className="text-xs font-mono truncate max-w-[120px]">{t.predicate}</TableCell>
                  <TableCell className="text-xs font-mono truncate max-w-[150px]">{t.object}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create OntologyOverview**

```tsx
// frontend/src/components/dashboard/ontology-overview.tsx
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
```

- [ ] **Step 5: Create DashboardPage**

```tsx
// frontend/src/pages/dashboard.tsx
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
```

- [ ] **Step 6: Wire DashboardPage into App.tsx**

In `frontend/src/App.tsx`, add the import and update the default case:

```tsx
import { DashboardPage } from "@/pages/dashboard";

// In the switch, replace the default case:
    default:
      page = <DashboardPage onNavigate={navigate} />;
      break;
```

- [ ] **Step 7: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/dashboard/ frontend/src/pages/dashboard.tsx frontend/src/App.tsx
git commit -m "feat: add Dashboard home page with stats, recent triples, and quick actions"
```

---

## Chunk 4: Existing Page Improvements — Triples, Ontology

### Task 10: Refactor Triples Page

**Files:**
- Modify: `frontend/src/pages/triples.tsx`

Rewrite the Triples page with: add-triple dialog, collapsible filters, sortable columns, client-side pagination (50/page), delete confirmation, toast notifications, empty state.

- [ ] **Step 1: Rewrite triples.tsx**

The full replacement for `frontend/src/pages/triples.tsx`:

```tsx
import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, Filter, Trash2, Database } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/api/client";
import type { Triple } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const PAGE_SIZE = 50;

interface TriplesPageProps {
  onNavigate?: (href: string) => void;
}

export function TriplesPage({ onNavigate }: TriplesPageProps) {
  const [triples, setTriples] = useState<Triple[]>([]);
  const [loading, setLoading] = useState(true);

  // Add dialog
  const [addOpen, setAddOpen] = useState(false);
  const [subject, setSubject] = useState("");
  const [predicate, setPredicate] = useState("");
  const [object, setObject] = useState("");
  const [adding, setAdding] = useState(false);

  // Filters
  const [showFilters, setShowFilters] = useState(false);
  const [filterSubject, setFilterSubject] = useState("");
  const [filterPredicate, setFilterPredicate] = useState("");
  const [filterObject, setFilterObject] = useState("");

  // Sort
  const [sortCol, setSortCol] = useState<"subject" | "predicate" | "object" | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  // Pagination
  const [page, setPage] = useState(1);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<Triple | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAllTriples();
      setTriples(data);
    } catch (err) {
      toast.error("Failed to load triples");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Filter + sort + paginate
  const filtered = useMemo(() => {
    let result = triples.filter((t) => {
      if (filterSubject && !t.subject.toLowerCase().includes(filterSubject.toLowerCase())) return false;
      if (filterPredicate && !t.predicate.toLowerCase().includes(filterPredicate.toLowerCase())) return false;
      if (filterObject && !t.object.toLowerCase().includes(filterObject.toLowerCase())) return false;
      return true;
    });
    if (sortCol) {
      result = [...result].sort((a, b) => {
        const av = a[sortCol].toLowerCase();
        const bv = b[sortCol].toLowerCase();
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      });
    }
    return result;
  }, [triples, filterSubject, filterPredicate, filterObject, sortCol, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Reset page when filters change
  useEffect(() => { setPage(1); }, [filterSubject, filterPredicate, filterObject]);

  const toggleSort = (col: "subject" | "predicate" | "object") => {
    if (sortCol === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortCol(col);
      setSortDir("asc");
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject || !predicate || !object) return;
    setAdding(true);
    try {
      await api.addTriple({ subject, predicate, object });
      toast.success("Triple added");
      setSubject(""); setPredicate(""); setObject("");
      setAddOpen(false);
      refresh();
    } catch (err) {
      toast.error("Failed to add triple: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (t: Triple) => {
    try {
      await api.deleteTriple(t);
      toast.success("Triple deleted");
      refresh();
    } catch (err) {
      toast.error("Failed to delete triple");
    }
  };

  const sortIndicator = (col: string) => {
    if (sortCol !== col) return "";
    return sortDir === "asc" ? " \u2191" : " \u2193";
  };

  return (
    <div className="space-y-4">
      {/* Actions row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowFilters((s) => !s)}>
            <Filter className="h-4 w-4 mr-1" /> Filters
          </Button>
          {filtered.length !== triples.length && (
            <span className="text-xs text-muted-foreground">
              Showing {filtered.length} of {triples.length}
            </span>
          )}
          {filtered.length === triples.length && !loading && (
            <span className="text-xs text-muted-foreground">{triples.length} triples</span>
          )}
        </div>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus className="h-4 w-4 mr-1" /> Add Triple
        </Button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex gap-3 rounded-md border p-3">
          <Input placeholder="Filter subject..." value={filterSubject} onChange={(e) => setFilterSubject(e.target.value)} className="text-sm" />
          <Input placeholder="Filter predicate..." value={filterPredicate} onChange={(e) => setFilterPredicate(e.target.value)} className="text-sm" />
          <Input placeholder="Filter object..." value={filterObject} onChange={(e) => setFilterObject(e.target.value)} className="text-sm" />
        </div>
      )}

      {/* Table */}
      <div className="rounded-md border overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="cursor-pointer select-none" onClick={() => toggleSort("subject")}>
                Subject{sortIndicator("subject")}
              </TableHead>
              <TableHead className="cursor-pointer select-none" onClick={() => toggleSort("predicate")}>
                Predicate{sortIndicator("predicate")}
              </TableHead>
              <TableHead className="cursor-pointer select-none" onClick={() => toggleSort("object")}>
                Object{sortIndicator("object")}
              </TableHead>
              <TableHead className="w-[50px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                  <TableCell />
                </TableRow>
              ))
            ) : paginated.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4}>
                  <EmptyState
                    icon={Database}
                    title="No triples yet"
                    description="Add your first triple or extract from text."
                    actions={[
                      { label: "Add Triple", onClick: () => setAddOpen(true) },
                      ...(onNavigate ? [{ label: "Extract from Text", onClick: () => onNavigate("/extraction"), variant: "outline" as const }] : []),
                    ]}
                  />
                </TableCell>
              </TableRow>
            ) : (
              paginated.map((t, i) => (
                <TableRow key={i}>
                  <TableCell className="font-mono text-sm">{t.subject}</TableCell>
                  <TableCell className="font-mono text-sm">{t.predicate}</TableCell>
                  <TableCell className="font-mono text-sm">{t.object}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" onClick={() => setDeleteTarget(t)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}

      {/* Add triple dialog */}
      {addOpen && (
        <dialog open className="fixed inset-0 z-50 flex items-center justify-center bg-transparent">
          <div className="fixed inset-0 bg-black/50" onClick={() => setAddOpen(false)} />
          <div className="relative rounded-lg border bg-background p-6 shadow-lg w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Add Triple</h3>
            <form onSubmit={handleAdd} className="space-y-3">
              <div className="space-y-1">
                <Label>Subject *</Label>
                <Input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="e.g. Mehdi" required />
              </div>
              <div className="space-y-1">
                <Label>Predicate *</Label>
                <Input value={predicate} onChange={(e) => setPredicate(e.target.value)} placeholder="e.g. founded" required />
              </div>
              <div className="space-y-1">
                <Label>Object *</Label>
                <Input value={object} onChange={(e) => setObject(e.target.value)} placeholder="e.g. BrandPulse" required />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setAddOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={adding || !subject || !predicate || !object}>
                  {adding ? "Adding..." : "Add"}
                </Button>
              </div>
            </form>
          </div>
        </dialog>
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Delete triple?"
        description={deleteTarget ? `This will remove: ${deleteTarget.subject} → ${deleteTarget.predicate} → ${deleteTarget.object}` : ""}
        onConfirm={() => { if (deleteTarget) handleDelete(deleteTarget); }}
      />
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/triples.tsx
git commit -m "feat(triples): add dialog, filters, sorting, pagination, confirmations, toasts"
```

---

### Task 11: Refactor Ontology Page with Tabs

**Files:**
- Modify: `frontend/src/pages/ontology.tsx`

Refactor to use in-page tabs: "Imported Ontologies" (default) | "Classes" | "Properties" | "Import". Add toast notifications, delete confirmations, validation, and empty states.

- [ ] **Step 1: Rewrite ontology.tsx**

Full rewrite of `frontend/src/pages/ontology.tsx`. Key structure:

```tsx
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Trash2, Eye, BookOpen, Upload } from "lucide-react";
import { api } from "@/api/client";
import type { OntologyClass, OntologyProperty, OntologyImportResponse, OntologyMetadata, OntologySchema } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { PageTabs } from "@/components/ui/page-tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const TABS = [
  { id: "ontologies", label: "Imported Ontologies" },
  { id: "classes", label: "Classes" },
  { id: "properties", label: "Properties" },
  { id: "import", label: "Import" },
];

export function OntologyPage() {
  const [activeTab, setActiveTab] = useState("ontologies");
  const [classes, setClasses] = useState<OntologyClass[]>([]);
  const [properties, setProperties] = useState<OntologyProperty[]>([]);
  const [ontologies, setOntologies] = useState<OntologyMetadata[]>([]);
  const [loading, setLoading] = useState(true);

  // Class form
  const [className, setClassName] = useState("");
  // Property form
  const [propName, setPropName] = useState("");
  const [propDomain, setPropDomain] = useState("");
  const [propRange, setPropRange] = useState("");
  // Import
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importUrl, setImportUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<OntologyImportResponse | null>(null);
  // Schema viewer
  const [selectedSchema, setSelectedSchema] = useState<{ id: string; schema: OntologySchema } | null>(null);
  // Delete confirmations
  const [deleteOntTarget, setDeleteOntTarget] = useState<OntologyMetadata | null>(null);
  const [deleteClassTarget, setDeleteClassTarget] = useState<string | null>(null);
  const [deletePropTarget, setDeletePropTarget] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [cls, props, onts] = await Promise.all([
        api.getClasses(), api.getProperties(), api.getOntologies(),
      ]);
      setClasses(cls);
      setProperties(props);
      setOntologies(onts);
    } catch {
      toast.error("Failed to load ontology data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Handlers: each wraps in try/catch with toast.success / toast.error
  const handleAddClass = async (e: React.FormEvent) => { /* validate, api.defineClass, toast.success, refresh */ };
  const handleDeleteClass = async (name: string) => { /* api.removeClass, toast.success, refresh */ };
  const handleAddProperty = async (e: React.FormEvent) => { /* validate, api.defineProperty, toast.success, refresh */ };
  const handleDeleteProperty = async (name: string) => { /* api.removeProperty, toast.success, refresh */ };
  const handleDeleteOntology = async (ont: OntologyMetadata) => { /* api.deleteOntology, toast.success, refresh */ };
  const handleViewSchema = async (id: string, graphUri: string) => { /* api.getOntologySchema, setSelectedSchema */ };
  const handleFileUpload = async (e: React.FormEvent) => { /* api.uploadOntologyFile, toast.success, refresh */ };
  const handleUrlImport = async (e: React.FormEvent) => { /* api.importOntologyUrl, toast.success, refresh */ };

  return (
    <div className="space-y-6">
      <PageTabs tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === "ontologies" && (
        <div className="space-y-4">
          {/* Table of ontologies with Eye and Trash2 action buttons */}
          {/* Skeleton rows when loading, EmptyState when empty */}
          {/* selectedSchema card below table when viewing schema */}
        </div>
      )}

      {activeTab === "classes" && (
        <div className="space-y-4">
          {/* Add class form (Input + Button) */}
          {/* Classes table with Skeleton loading, EmptyState, delete with ConfirmDialog */}
        </div>
      )}

      {activeTab === "properties" && (
        <div className="space-y-4">
          {/* Add property form (3 inputs + Button) */}
          {/* Properties table with Skeleton, EmptyState, delete with ConfirmDialog */}
        </div>
      )}

      {activeTab === "import" && (
        <div className="space-y-4">
          {/* Same grid layout as current: file upload card + URL import card */}
          {/* importResult success banner, importError via toast */}
        </div>
      )}

      {/* Delete confirmation dialogs */}
      <ConfirmDialog
        open={deleteOntTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteOntTarget(null); }}
        title="Delete ontology?"
        description={deleteOntTarget ? `Delete "${deleteOntTarget.name}"? This removes all its triples.` : ""}
        onConfirm={() => { if (deleteOntTarget) handleDeleteOntology(deleteOntTarget); }}
      />
      <ConfirmDialog
        open={deleteClassTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteClassTarget(null); }}
        title="Delete class?"
        description={`Remove class "${deleteClassTarget}"?`}
        onConfirm={() => { if (deleteClassTarget) handleDeleteClass(deleteClassTarget); }}
      />
      <ConfirmDialog
        open={deletePropTarget !== null}
        onOpenChange={(open) => { if (!open) setDeletePropTarget(null); }}
        title="Delete property?"
        description={`Remove property "${deletePropTarget}"?`}
        onConfirm={() => { if (deletePropTarget) handleDeleteProperty(deletePropTarget); }}
      />
    </div>
  );
}
```

The handler bodies follow the existing patterns from the current `ontology.tsx` but replace `console.error` with `toast.error()` and add `toast.success()`. Each tab section follows the same table patterns as the current file but adds `Skeleton` loading rows and `EmptyState` for empty tables. The key architectural change is the tab-based layout via `PageTabs` — all state is shared and `refresh()` reloads everything.

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ontology.tsx
git commit -m "feat(ontology): refactor to tabbed layout with toasts, confirmations, skeletons"
```

---

## Chunk 5: Remaining Page Improvements — Extraction, Query, Explorer

### Task 12: Improve Extraction Page

**Files:**
- Modify: `frontend/src/pages/extraction.tsx`

- [ ] **Step 1: Update extraction.tsx**

Full structural changes to `frontend/src/pages/extraction.tsx`:

```tsx
import { useState } from "react";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";
import { api } from "@/api/client";
import type { ExtractedTriple, PreviewTriple } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { PageTabs } from "@/components/ui/page-tabs";
import { cn } from "@/lib/utils";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface ExtractionPageProps {
  onNavigate?: (href: string) => void;
}

export function ExtractionPage({ onNavigate }: ExtractionPageProps) {
  const [text, setText] = useState("");
  const [mode, setMode] = useState<"strict" | "open">("strict");
  const [preview, setPreview] = useState<PreviewTriple[] | null>(null);
  const [stored, setStored] = useState<ExtractedTriple[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [resultTab, setResultTab] = useState("stored");

  async function handlePreview() { /* same as current but toast.error on fail */ }

  async function handleExtract() {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const results = await api.extractAndStore({ text, mode });
      setStored(results);
      setResultTab("stored");
      toast.success(`${results.length} triples extracted and stored`);
      // Do NOT clear text — user clicks "Extract Another"
    } catch (e) {
      toast.error("Extraction failed: " + (e instanceof Error ? e.message : "Unknown"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Input */}
      <div className="space-y-2">
        <Label htmlFor="extract-text">Paste unstructured text</Label>
        <Textarea id="extract-text" rows={6} value={text} onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Mehdi established BrandPulse Analytics in 2023..." />
      </div>

      {/* Mode segmented control */}
      <div className="flex items-center gap-3">
        <Label>Mode:</Label>
        <div className="inline-flex rounded-md border p-0.5">
          {(["strict", "open"] as const).map((m) => (
            <button key={m} onClick={() => setMode(m)}
              className={cn("px-4 py-1.5 text-sm font-medium rounded-sm transition-colors capitalize",
                mode === m ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
              )}>{m}</button>
          ))}
        </div>
        <span className="text-xs text-muted-foreground ml-2">
          {mode === "strict" ? "Constrained to ontology schema" : "Free extraction"}
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button onClick={handlePreview} disabled={loading || !text.trim()} variant="outline">
          {loading ? "Processing..." : "Preview"}
        </Button>
        <Button onClick={handleExtract} disabled={loading || !text.trim()}>
          <Sparkles className="h-4 w-4 mr-1" /> {loading ? "Processing..." : "Extract & Store"}
        </Button>
      </div>

      {/* Success banner */}
      {stored && stored.length > 0 && (
        <div className="rounded-md border border-green-200 bg-green-50 dark:bg-green-950/30 p-4 flex items-center justify-between">
          <p className="text-sm font-medium text-green-800 dark:text-green-200">
            {stored.length} triples extracted and stored
          </p>
          <div className="flex gap-2">
            {onNavigate && (
              <Button size="sm" variant="outline" onClick={() => onNavigate("/triples")}>View in Triples</Button>
            )}
            <Button size="sm" variant="outline" onClick={() => { setText(""); setStored(null); setPreview(null); }}>
              Extract Another
            </Button>
          </div>
        </div>
      )}

      {/* Results tabs — show both preview and stored */}
      {(preview || stored) && (
        <div className="space-y-4">
          <PageTabs
            tabs={[{ id: "stored", label: "Stored Results" }, { id: "preview", label: "Preview" }]}
            activeTab={resultTab}
            onTabChange={setResultTab}
          />
          {/* Render the appropriate results table based on resultTab */}
          {/* Same table rendering as current extraction.tsx for each tab */}
        </div>
      )}
    </div>
  );
}
```

The result tables (preview with candidate badges, stored with disambiguation info) remain the same as the current implementation. The key changes are: segmented mode control, success banner with "View in Triples" and "Extract Another" buttons, `PageTabs` to switch between stored and preview results, and toast notifications replacing the error state.

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/extraction.tsx
git commit -m "feat(extraction): add mode toggle, success banner, result tabs, toasts"
```

---

### Task 13: Improve Query Page with CodeMirror

**Files:**
- Create: `frontend/src/components/query/sparql-editor.tsx`
- Modify: `frontend/src/pages/query.tsx`

- [ ] **Step 1: Create lazy-loaded SparqlEditor**

```tsx
// frontend/src/components/query/sparql-editor.tsx
import { useEffect, useRef } from "react";
import { EditorView } from "@codemirror/view";
import { basicSetup } from "@codemirror/basic-setup";
import { EditorState } from "@codemirror/state";
import { sql } from "@codemirror/lang-sql";

interface SparqlEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export function SparqlEditor({ value, onChange }: SparqlEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const state = EditorState.create({
      doc: value,
      extensions: [
        basicSetup,
        sql(),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            onChange(update.state.doc.toString());
          }
        }),
        EditorView.theme({
          "&": { fontSize: "14px", border: "1px solid hsl(var(--border))", borderRadius: "0.375rem" },
          ".cm-content": { fontFamily: "monospace", padding: "8px" },
          ".cm-gutters": { display: "none" },
          ".cm-focused": { outline: "none" },
        }),
      ],
    });

    const view = new EditorView({ state, parent: containerRef.current });
    viewRef.current = view;

    return () => view.destroy();
    // Only create once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <div ref={containerRef} />;
}
```

- [ ] **Step 2: Update query.tsx**

Key structural changes to `frontend/src/pages/query.tsx`:

```tsx
import { Suspense, lazy, useState } from "react";
import { toast } from "sonner";
import { Copy, Download, Info, ChevronDown } from "lucide-react";
import { api } from "@/api/client";
import type { QueryResult, QueryResultWithExplanation } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const SparqlEditor = lazy(() => import("@/components/query/sparql-editor").then(m => ({ default: m.SparqlEditor })));

export function QueryPage() {
  // ... existing state ...
  const [showHistory, setShowHistory] = useState(false);

  // Copy SPARQL to clipboard
  const copySparql = () => {
    if (result?.sparql) {
      navigator.clipboard.writeText(result.sparql);
      toast.success("SPARQL copied to clipboard");
    }
  };

  // Export results as CSV
  const exportCsv = () => {
    if (!result?.results.length) return;
    const headers = Object.keys(result.results[0]);
    const rows = result.results.map(r => headers.map(h => `"${(r[h] ?? "").replace(/"/g, '""')}"`).join(","));
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "query-results.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Mode toggle */}
      {/* ... same as current but styled consistently ... */}

      {/* NL mode: larger input */}
      {!advancedMode && (
        <div className="space-y-2">
          <Input className="text-lg py-3" placeholder="Ask a question about your knowledge graph..."
            value={question} onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAsk()} />

          {/* Collapsible history */}
          {history.length > 0 && (
            <div>
              <button onClick={() => setShowHistory(s => !s)}
                className="text-xs text-muted-foreground flex items-center gap-1 hover:text-foreground">
                <ChevronDown className={`h-3 w-3 transition-transform ${showHistory ? "rotate-180" : ""}`} />
                Recent Questions ({history.length})
              </button>
              {showHistory && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {history.map((q, i) => (
                    <button key={i} onClick={() => setQuestion(q)}
                      className="text-xs px-2 py-1 rounded-md bg-muted hover:bg-accent truncate max-w-[200px]">{q}</button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SPARQL mode: CodeMirror editor */}
      {advancedMode && (
        <Suspense fallback={<Skeleton className="h-40 w-full" />}>
          <SparqlEditor value={sparqlInput} onChange={setSparqlInput} />
        </Suspense>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Row count + action buttons */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{result.results.length} results</span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={copySparql}>
                <Copy className="h-3 w-3 mr-1" /> Copy SPARQL
              </Button>
              <Button size="sm" variant="outline" onClick={exportCsv}>
                <Download className="h-3 w-3 mr-1" /> Export CSV
              </Button>
            </div>
          </div>

          {/* Results table — same as current */}

          {/* Explanation callout */}
          {explanation && (
            <div className="rounded-md bg-muted p-4 flex gap-3">
              <Info className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-sm">{explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

The SparqlEditor is lazy-loaded via `React.lazy()` so the ~150kb CodeMirror bundle only loads when the user switches to SPARQL mode. The CSV export generates a proper CSV blob and triggers a download. The SPARQL copy uses the clipboard API with a toast confirmation.

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/query/sparql-editor.tsx frontend/src/pages/query.tsx
git commit -m "feat(query): add CodeMirror SPARQL editor, copy/export, result count, callout"
```

---

### Task 14: Improve Explorer Page

**Files:**
- Modify: `frontend/src/pages/explorer.tsx`

- [ ] **Step 1: Update explorer.tsx**

Key structural changes to `frontend/src/pages/explorer.tsx`:

```tsx
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { Plus, Minus, X, RefreshCw } from "lucide-react";
import { api } from "@/api/client";
import type { Triple } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const NODE_LIMIT = 200;

export function ExplorerPage() {
  const graphRef = useRef<any>(null);
  const [allTriples, setAllTriples] = useState<Triple[]>([]);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // ... existing data fetch and graph building logic ...

  // Limit nodes
  const totalNodeCount = /* total unique nodes from allTriples */;
  const limitedGraphData = useMemo(() => {
    // Build nodes/links from allTriples, cap at NODE_LIMIT
    // Show filtered subset if filter is set
  }, [allTriples, filter]);

  // Get connected triples for selected node
  const selectedTriples = useMemo(() => {
    if (!selected) return [];
    return allTriples.filter(t => t.subject === selected || t.object === selected);
  }, [allTriples, selected]);

  const handleNodeClick = useCallback((node: any) => {
    setSelected(prev => prev === node.id ? null : node.id); // Toggle
  }, []);

  // Zoom controls
  const zoomIn = () => graphRef.current?.zoom(graphRef.current.zoom() * 1.5, 300);
  const zoomOut = () => graphRef.current?.zoom(graphRef.current.zoom() / 1.5, 300);

  return (
    <div className="space-y-4">
      {/* Controls row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Input placeholder="Filter nodes..." value={filter} onChange={e => setFilter(e.target.value)}
            className="w-64 text-sm" />
          <span className="text-xs text-muted-foreground">
            Showing {limitedGraphData.nodes.length} of {totalNodeCount} nodes
          </span>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          <RefreshCw className="h-4 w-4 mr-1" /> Refresh
        </Button>
      </div>

      {/* Graph + detail panel side by side */}
      <div className="flex gap-4">
        {/* Graph container */}
        <div className="relative flex-1 rounded-md border bg-card overflow-hidden" style={{ height: 500 }}>
          {loading ? (
            <Skeleton className="h-full w-full" />
          ) : (
            <ForceGraph2D
              ref={graphRef}
              graphData={limitedGraphData}
              onNodeClick={handleNodeClick}
              nodeLabel={(node: any) => node.label} /* hover tooltip */
              /* ... existing rendering props ... */
            />
          )}

          {/* Zoom controls overlay */}
          <div className="absolute bottom-3 right-3 flex flex-col gap-1">
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={zoomIn}>
              <Plus className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={zoomOut}>
              <Minus className="h-4 w-4" />
            </Button>
          </div>

          {/* Legend overlay */}
          <div className="absolute top-3 right-3 rounded-md border bg-card/90 p-2 text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-indigo-500 inline-block" />
              <span>Entity</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-orange-500 inline-block" />
              <span>Selected</span>
            </div>
          </div>

          {/* Onboarding hint */}
          {!selected && !loading && (
            <p className="absolute bottom-3 left-3 text-xs text-muted-foreground bg-card/80 px-2 py-1 rounded">
              Click a node to see its connections
            </p>
          )}
        </div>

        {/* Detail panel — slides in when node selected */}
        {selected && (
          <div className="w-80 shrink-0 rounded-md border bg-card overflow-hidden">
            <div className="flex items-center justify-between p-3 border-b">
              <h3 className="text-sm font-medium truncate">{selected}</h3>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setSelected(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="overflow-y-auto" style={{ maxHeight: 450 }}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs">Subject</TableHead>
                    <TableHead className="text-xs">Predicate</TableHead>
                    <TableHead className="text-xs">Object</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {selectedTriples.map((t, i) => (
                    <TableRow key={i}>
                      <TableCell className="text-xs font-mono">{t.subject}</TableCell>
                      <TableCell className="text-xs font-mono">{t.predicate}</TableCell>
                      <TableCell className="text-xs font-mono">{t.object}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

The graph data building and rendering logic carries over from the existing `explorer.tsx`. The key additions are: zoom controls using `graphRef.current.zoom()`, a legend overlay, `nodeLabel` prop for hover tooltips, a slide-in detail panel on the right when a node is clicked (close via X or re-click), node count limit of 200, and an onboarding hint.

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/explorer.tsx
git commit -m "feat(explorer): add zoom controls, legend, detail panel, node limit"
```

---

## Chunk 6: Final Polish and Integration

### Task 15: Run Full Test Suite and Final Build

**Files:**
- No new files

- [ ] **Step 1: Run backend tests**

```bash
cd /Users/mehdiallahyari/environments/uv_projects/keplai && /Users/mehdiallahyari/environments/uv_projects/.venv/bin/python -m pytest tests/unit/ -v
```
Expected: All tests pass (including the new `test_get_stats`).

- [ ] **Step 2: Run frontend build**

```bash
cd frontend && npm run build
```
Expected: Clean build, no TypeScript errors.

- [ ] **Step 3: Run frontend lint**

```bash
cd frontend && npm run lint
```
Expected: No lint errors.

- [ ] **Step 4: Manual visual verification**

Start the dev server and check each page:
```bash
cd frontend && npm run dev
```

Verify:
- Dashboard loads with stat cards and recent triples
- Sidebar navigation works, collapse/expand works
- Triples page: add dialog, filters, sorting, pagination, delete confirmation
- Ontology page: tabs work, all CRUD operations show toasts
- Extraction page: mode toggle, success banner, result tabs
- Query page: CodeMirror editor loads in SPARQL mode, copy/export work
- Explorer page: zoom controls visible, node click shows detail panel

- [ ] **Step 5: Push to GitHub**

```bash
git push
```

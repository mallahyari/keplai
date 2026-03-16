# Frontend UX Overhaul — Design Spec

**Sub-project 1 of 2.** This spec covers the global UX overhaul, sidebar navigation, and dashboard home page. Sub-project 2 (ontology visual editor, batch import, triple detail view, conversational query) will be specced separately.

**Goal:** Transform the KeplAI frontend from a basic functional UI into a polished, professional application that serves both developers and non-technical domain experts.

**Audience:** Both technical users (developers, data engineers) and non-technical users (researchers, analysts). The UI must be powerful yet approachable.

**Tech Stack:** React 19 + TypeScript, Tailwind CSS 4, shadcn/ui components, Vite 7, lucide-react icons. New dependencies: sonner (toast notifications).

---

## 1. Layout Shell & Sidebar Navigation

### Sidebar

- **Width:** 240px expanded, 60px collapsed (icon-only mode)
- **Position:** Fixed left, full viewport height
- **Top section:** KeplAI logo/wordmark. Collapses to a "K" icon mark.
- **Engine status:** Green/red dot indicator always visible below the logo. Expanded mode shows "Online" / "Offline" text.
- **Navigation groups:**
  - **Overview:** Dashboard
  - **Data:** Triples, Extraction
  - **Schema:** Ontology
  - **Explore:** Query, Explorer
- **Each nav item:** Lucide icon + label. Label hidden when collapsed. Active page gets accent background highlight.
- **Collapse toggle:** Button at the bottom of the sidebar (chevron icon). State persisted in `localStorage`.
- **Responsive:** Auto-collapses below 1024px breakpoint.

### Top Header Bar

- **Left:** Dynamic page title based on current route.
- **Right:** Contextual quick action button (e.g., "+ Add Triple" on Triples page, "Import" on Ontology page). Engine status detail available on hover/click.

### Content Area

- **Max-width:** 1200px, centered horizontally.
- **Padding:** Comfortable spacing (p-6 or p-8).
- **Page structure convention:** Title row (h1 + page-level action buttons), then content sections separated by whitespace.

### Migration from Current Layout

The existing `components/layout.tsx` (horizontal top-nav bar) is replaced entirely by `AppShell`. Delete `layout.tsx` once `AppShell` is wired up. Update `App.tsx` to wrap all pages in `AppShell` instead of `Layout`.

### Routing

- Keep the existing hash-based `useHashRoute` hook. Update the route map:
  - `/` — Dashboard (new default)
  - `/triples` — Triples page
  - `/ontology` — Ontology page
  - `/extraction` — Extraction page
  - `/query` — Query page
  - `/explorer` — Explorer page

### Header vs. Page Title

The **Top Header Bar** is part of `AppShell` and renders the dynamic page title + contextual action button. There is no separate `PageHeader` inside the content area — the header bar serves that role. Each page passes its title and actions to `AppShell` via props or a context/slot pattern.

### New Layout Components

- `AppShell` — wraps the entire app: sidebar + top header bar + content area. Mounts `<Toaster />` from sonner at the root.
- `Sidebar` — collapsible navigation with grouped items
- `SidebarItem` — individual nav link (icon + label)

### Sidebar Animation

Collapse/expand animates over 200ms with ease-in-out transition on width. Content fades between icon-only and icon+label states.

---

## 2. Global UX Patterns

### Toast Notifications

- **Library:** sonner (lightweight, works well with shadcn)
- **Position:** Bottom-right of viewport
- **Usage:**
  - Success: "Triple added", "Ontology imported (42 triples loaded)", "Class deleted"
  - Error: "Failed to delete triple: [server error message]"
- **Behavior:** Success toasts auto-dismiss after 4 seconds. Error toasts persist until manually dismissed.
- **Integration:** Replace all `console.error` calls and silent failures across every page with toast notifications.

### Delete Confirmations

- **Component:** Alert dialog (shadcn `AlertDialog`)
- **Trigger:** All destructive actions (delete triple, delete ontology, remove class, remove property)
- **Content:** Clear description of what will be deleted. E.g., "Delete ontology 'Cat Ontology'? This will remove all its triples and cannot be undone."
- **Buttons:** Cancel (outline variant) + Delete (destructive red variant)

### Loading States

- **Tables:** Skeleton rows (pulsing gray bars matching column widths). Show 5 skeleton rows.
- **Cards:** Skeleton placeholders matching card dimensions.
- **Buttons:** Spinner icon + disabled state during async operations. Button text changes (e.g., "Deleting..." / "Importing...").
- **Page-level:** Skeleton version of the full page layout on initial load.

### Form Validation

- **Required fields:** Marked with subtle asterisk on label.
- **Inline errors:** Red text below the field on blur or submit attempt.
- **Submit buttons:** Disabled until all required fields are filled and valid.
- **Specific validations:**
  - Triple form: subject, predicate, object all required
  - Class form: name required, non-empty
  - Property form: name, domain, range all required
  - URL import: valid URL format
  - Extraction text: non-empty

### Empty States

- **Design:** Centered icon (from lucide) + descriptive message + primary action button.
- **Examples:**
  - Triples: "No triples yet" + "Add Triple" and "Extract from Text" buttons
  - Ontology classes: "No classes defined" + "Define a Class" button
  - Imported ontologies: "No ontologies imported" + "Import Ontology" button
  - Query results: "Ask a question to get started" (no button, just guidance)

### Responsive Behavior

- **Below 1024px:** Sidebar auto-collapses to icon-only mode.
- **Below 768px:** Sidebar becomes a hamburger menu overlay. Tables scroll horizontally. Form grids stack to single column.
- **Tables:** Horizontal scroll wrapper on small screens.
- **Forms:** Multi-column form layouts stack vertically on mobile.

---

## 3. Dashboard Home Page

### Route: `/` (new default landing page)

### Backend Requirement

New API endpoint: `GET /api/graph/stats`

Response schema:
```json
{
  "triple_count": 142,
  "entity_count": 58,
  "ontology_count": 2,
  "class_count": 12,
  "property_count": 8
}
```

This aggregates counts in a single request to avoid multiple round-trips on page load.

**Loading state:** Show skeleton stat cards while loading. **Error state:** If the stats endpoint fails, show stat cards with "—" values and an error toast. Do not block the rest of the dashboard.

### Layout

**Top row — Stat Cards (4-column grid):**

| Card | Icon | Value | Label |
|------|------|-------|-------|
| Triples | `Database` | 142 | Total Triples |
| Entities | `Users` | 58 | Unique Entities |
| Ontologies | `BookOpen` | 2 | Imported Ontologies |
| Schema | `Network` | 20 | Classes & Properties |

- Each card: icon (muted color), large number, label below.
- The "Schema" card shows the sum of `class_count + property_count` (e.g., "20" if 12 classes + 8 properties).
- Subtle distinct background tint per card.
- Clickable — navigates to the relevant page.

**Middle row — Two columns:**

Left column (60% width): **Recent Triples**
- Compact table showing the latest 10 triples (subject, predicate, object).
- "View all" link in card header navigates to `/triples`.
- Data source: `GET /api/graph/triples/all` (existing endpoint, take last 10).

Right column (40% width): **Quick Actions**
- Card with 4 action buttons, each with icon + label:
  - "Add Triple" — navigates to `/triples`
  - "Extract from Text" — navigates to `/extraction`
  - "Import Ontology" — navigates to `/ontology`
  - "Ask a Question" — navigates to `/query`

**Bottom row — full width:**

**Ontology Overview**
- Horizontal scrollable row of cards, one per imported ontology.
- Each card: ontology name, class count, property count, import date.
- "View Schema" link per card.
- Empty state if no ontologies imported: "Import your first ontology to get started."

---

## 4. Existing Page Improvements

### Triples Page (`/triples`)

**Current problems:** Add form takes space, no sorting, no pagination, no result count, silent errors.

**Changes:**
- Move "Add Triple" into a dialog triggered by the page header action button ("+ Add Triple").
- Add result count badge: "Showing 12 of 48 triples".
- Collapsible "Filters" bar above table with subject/predicate/object filter inputs. Collapsed by default, toggle button to show.
- Column headers clickable for sorting (ascending/descending toggle).
- Client-side pagination: fetch all triples, display 50 per page with prev/next page controls and page number. All filtering and sorting also client-side on the full dataset.
- Delete actions get confirmation dialog and toast feedback.

### Ontology Page (`/ontology`)

**Current problems:** Long page with all sections stacked, no clear hierarchy.

**Changes:**
- In-page tabs: "Imported Ontologies" (default) | "Classes" | "Properties" | "Import"
- Imported Ontologies tab: table with ontologies, view-schema and delete actions. Schema details shown in a card below the table (current behavior, cleaned up).
- Classes tab: add form + table (same as current, with validation and confirmations).
- Properties tab: add form + table (same as current, with validation and confirmations).
- Import tab: file upload + URL import side-by-side (current layout, relocated).
- All tabs share the same refresh/loading state.

### Extraction Page (`/extraction`)

**Current problems:** No success feedback, mode distinction unclear, results replace each other.

**Changes:**
- Mode selector: proper segmented control / toggle group with visual distinction and description text.
- After successful extraction: success banner "5 triples extracted and stored" with "View in Triples" link and "Extract Another" button.
- Results section: tabs for "Preview" and "Stored" results so both can coexist and be compared.
- Toast notifications for success/error.

### Query Page (`/query`)

**Current problems:** No syntax highlighting, history badges truncate, no result export.

**Changes:**
- Natural Language mode: larger input field. History moves to a collapsible dropdown or popover below the input.
- SPARQL mode: replace textarea with a code editor component (codemirror with SPARQL syntax highlighting).
- Results table: row count display, "Copy SPARQL" button, "Export CSV" button for results.
- Explanation shown in a styled callout card (info icon + blue/gray background).
- Add CodeMirror with SQL language support (closest available to SPARQL). Lazy-load the editor component to avoid impacting initial bundle size (~150kb).

### Explorer Page (`/explorer`)

**Current problems:** No zoom controls, no legend, labels overlap, no interaction hints.

**Changes:**
- Zoom controls: +/- buttons overlaid on the graph canvas.
- Legend panel: shows node type colors and what they mean.
- Node hover: tooltip with full entity name and type.
- Node click: detail panel slides in from the right showing connected triples in a mini-table. Close via X button in the panel or by clicking the same node again.
- Node count limit: "Showing 200 of 1,432 nodes" with filter controls to narrow down.
- Add onboarding hint on first visit: "Click a node to see its connections."

---

## 5. New Components Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| `AppShell` | `components/layout/app-shell.tsx` | Sidebar + header bar + content area + Toaster |
| `Sidebar` | `components/layout/sidebar.tsx` | Collapsible navigation with grouped items |
| `SidebarItem` | `components/layout/sidebar-item.tsx` | Nav link (icon + label) |
| `DashboardPage` | `pages/dashboard.tsx` | Dashboard home page |
| `StatCard` | `components/dashboard/stat-card.tsx` | Clickable metric card |
| `QuickActions` | `components/dashboard/quick-actions.tsx` | Action button grid |
| `RecentTriples` | `components/dashboard/recent-triples.tsx` | Compact recent triples table |
| `OntologyOverview` | `components/dashboard/ontology-overview.tsx` | Horizontal ontology cards |
| `ConfirmDialog` | `components/ui/confirm-dialog.tsx` | Reusable delete confirmation |
| `EmptyState` | `components/ui/empty-state.tsx` | Icon + message + action |
| `Skeleton` | `components/ui/skeleton.tsx` | Loading placeholder |
| `PageTabs` | `components/ui/page-tabs.tsx` | In-page tab navigation |
| `SparqlEditor` | `components/query/sparql-editor.tsx` | Lazy-loaded CodeMirror SPARQL editor |

**Deleted:** `components/layout.tsx` (replaced by `AppShell`)

---

## 6. New Dependencies

The project currently uses `@base-ui/react` as its component primitive library (not Radix directly). New UI primitives should come from Base UI or be built with plain HTML + Tailwind to stay consistent.

| Package | Purpose | Size | Notes |
|---------|---------|------|-------|
| `sonner` | Toast notifications | ~5kb | |
| `codemirror` + `@codemirror/view` + `@codemirror/state` + `@codemirror/lang-sql` | SPARQL editor | ~150kb | Lazy-loaded via `React.lazy()` to avoid bundle impact |

For alert dialogs and tabs, use Base UI primitives or build with native HTML elements + Tailwind (shadcn pattern). No additional Radix packages needed.

### Dark Mode

The existing shadcn/Tailwind setup supports dark mode via CSS variables. All new components must use the existing CSS variable tokens (e.g., `bg-card`, `text-muted-foreground`) to automatically support both themes. No additional dark mode work is required beyond using the token system consistently.

---

## 7. Backend Change

One new endpoint required:

**`GET /api/graph/stats`**

Returns aggregated counts for the dashboard.

```python
# api/routers/graph.py
@router.get("/stats")
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

Response model added to `api/schemas.py`:
```python
class StatsResponse(BaseModel):
    triple_count: int
    entity_count: int
    ontology_count: int
    class_count: int
    property_count: int
```

---

## 8. Out of Scope (Sub-project 2)

The following features are deferred to a separate spec:

- Ontology visual editor (drag-and-drop class/property builder)
- Batch triple import from CSV/JSON
- Triple detail view (click to see context, related entities, provenance)
- Conversational query interface (chat-style follow-up questions)

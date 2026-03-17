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
    if (mql.matches) setCollapsed(true); // eslint-disable-line react-hooks/set-state-in-effect -- initial sync with media query
    mql.addEventListener("change", handler);
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

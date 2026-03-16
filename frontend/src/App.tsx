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
      page = <TriplesPage />;
      break;
    case "/ontology":
      page = <OntologyPage />;
      break;
    case "/extraction":
      page = <ExtractionPage />;
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

import { useHashRoute } from "@/hooks/use-hash-route";
import { AppShell } from "@/components/layout/app-shell";
import { TriplesPage } from "@/pages/triples";
import { OntologyPage } from "@/pages/ontology";
import { ExtractionPage } from "@/pages/extraction";
import { QueryPage } from "@/pages/query";
import { ExplorerPage } from "@/pages/explorer";
import { DashboardPage } from "@/pages/dashboard";

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
      page = <DashboardPage onNavigate={navigate} />;
      break;
  }

  return (
    <AppShell currentRoute={route} onNavigate={navigate}>
      {page}
    </AppShell>
  );
}

export default App;

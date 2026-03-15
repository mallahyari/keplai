import { Layout } from "@/components/layout";
import { TriplesPage } from "@/pages/triples";
import { OntologyPage } from "@/pages/ontology";
import { ExtractionPage } from "@/pages/extraction";
import { QueryPage } from "@/pages/query";
import { ExplorerPage } from "@/pages/explorer";
import { useHashRoute } from "@/hooks/use-hash-route";

function App() {
  const route = useHashRoute();

  let page;
  switch (route) {
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
      page = <TriplesPage />;
  }

  return <Layout>{page}</Layout>;
}

export default App;

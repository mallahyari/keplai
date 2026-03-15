import { Layout } from "@/components/layout";
import { TriplesPage } from "@/pages/triples";
import { OntologyPage } from "@/pages/ontology";
import { ExtractionPage } from "@/pages/extraction";
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
    default:
      page = <TriplesPage />;
  }

  return <Layout>{page}</Layout>;
}

export default App;

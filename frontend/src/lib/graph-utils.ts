/**
 * Extract the local name from a URI.
 * "http://keplai.io/entity/Mehdi" → "Mehdi"
 * "http://xmlns.com/foaf/0.1/Person" → "Person"
 */
export function shortName(uri: string): string {
  if (uri.includes("/")) return uri.split("/").pop() || uri;
  if (uri.includes("#")) return uri.split("#").pop() || uri;
  return uri;
}

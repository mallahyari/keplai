import { useCallback, useEffect, useState } from "react";
import { api } from "@/api/client";
import type { OntologyClass, OntologyProperty } from "@/types/graph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Trash2 } from "lucide-react";

export function OntologyPage() {
  const [classes, setClasses] = useState<OntologyClass[]>([]);
  const [properties, setProperties] = useState<OntologyProperty[]>([]);
  const [loading, setLoading] = useState(true);

  // Add class form
  const [className, setClassName] = useState("");

  // Add property form
  const [propName, setPropName] = useState("");
  const [propDomain, setPropDomain] = useState("");
  const [propRange, setPropRange] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [cls, props] = await Promise.all([
        api.getClasses(),
        api.getProperties(),
      ]);
      setClasses(cls);
      setProperties(props);
    } catch (err) {
      console.error("Failed to load ontology", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleAddClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!className) return;
    await api.defineClass(className);
    setClassName("");
    refresh();
  };

  const handleDeleteClass = async (name: string) => {
    await api.removeClass(name);
    refresh();
  };

  const handleAddProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!propName || !propDomain || !propRange) return;
    await api.defineProperty(propName, propDomain, propRange);
    setPropName("");
    setPropDomain("");
    setPropRange("");
    refresh();
  };

  const handleDeleteProperty = async (name: string) => {
    await api.removeProperty(name);
    refresh();
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold tracking-tight">Ontology</h2>

      {/* Classes section */}
      <section className="space-y-4">
        <h3 className="text-lg font-medium">Classes</h3>

        <form onSubmit={handleAddClass} className="flex gap-3 items-end">
          <div className="space-y-1">
            <Label htmlFor="class-name">Class Name</Label>
            <Input
              id="class-name"
              value={className}
              onChange={(e) => setClassName(e.target.value)}
              placeholder="e.g. Person"
            />
          </div>
          <Button type="submit">Add Class</Button>
        </form>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>URI</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    Loading…
                  </TableCell>
                </TableRow>
              ) : classes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    No classes defined
                  </TableCell>
                </TableRow>
              ) : (
                classes.map((c) => (
                  <TableRow key={c.uri}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">
                      {c.uri}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteClass(c.name)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </section>

      {/* Properties section */}
      <section className="space-y-4">
        <h3 className="text-lg font-medium">Properties</h3>

        <form onSubmit={handleAddProperty} className="flex gap-3 items-end">
          <div className="space-y-1">
            <Label htmlFor="prop-name">Property Name</Label>
            <Input
              id="prop-name"
              value={propName}
              onChange={(e) => setPropName(e.target.value)}
              placeholder="e.g. founded"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="prop-domain">Domain</Label>
            <Input
              id="prop-domain"
              value={propDomain}
              onChange={(e) => setPropDomain(e.target.value)}
              placeholder="e.g. Person"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="prop-range">Range</Label>
            <Input
              id="prop-range"
              value={propRange}
              onChange={(e) => setPropRange(e.target.value)}
              placeholder="e.g. Company"
            />
          </div>
          <Button type="submit">Add Property</Button>
        </form>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Domain</TableHead>
                <TableHead>Range</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    Loading…
                  </TableCell>
                </TableRow>
              ) : properties.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    No properties defined
                  </TableCell>
                </TableRow>
              ) : (
                properties.map((p) => (
                  <TableRow key={p.uri}>
                    <TableCell className="font-medium">{p.name}</TableCell>
                    <TableCell>{p.domain}</TableCell>
                    <TableCell>{p.range}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteProperty(p.name)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  );
}

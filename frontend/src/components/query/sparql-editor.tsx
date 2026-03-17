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
          "&": {
            fontSize: "14px",
            border: "1px solid hsl(var(--border))",
            borderRadius: "0.375rem",
          },
          ".cm-content": { fontFamily: "monospace", padding: "8px" },
          ".cm-gutters": { display: "none" },
          ".cm-focused": { outline: "none" },
        }),
      ],
    });

    const view = new EditorView({ state, parent: containerRef.current });
    viewRef.current = view;

    return () => view.destroy();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <div ref={containerRef} />;
}

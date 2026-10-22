"use client";
import dynamic from "next/dynamic";
import { useTheme } from "next-themes";
const Monaco = dynamic(() => import("@monaco-editor/react"), { ssr: false });
export default function CodeView({ code, line }: { code: string; line: number | null }) {
  const { resolvedTheme } = useTheme();
  return (
    <Monaco height="420px" language="python" theme={resolvedTheme === "dark" ? "vs-dark" : "light"} value={code}
      options={{ readOnly: true, minimap: { enabled: false }, fontSize: 13, lineNumbers: "on", scrollBeyondLastLine: false,
        revealLine: line || 1 } as any}
      onMount={(editor) => { if (line) { editor.revealLineInCenter(line); editor.setPosition({ lineNumber: line, column: 1 }); } }} />
  );
}

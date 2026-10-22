"use client";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { useTheme } from "next-themes";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import { Upload, Play, Loader2 } from "lucide-react";

const Monaco = dynamic(() => import("@monaco-editor/react"), { ssr: false });
const STARTER = `import os

def load_config(path, cache={}):
    if path in cache:
        return cache[path]
    with open(path) as f:
        data = eval(f.read())
    cache[path] = data
    return data

def divide(a, b):
    try:
        return a / b
    except:
        pass
`;

export default function ReviewPage() {
  const router = useRouter(); const { resolvedTheme } = useTheme();
  const [code, setCode] = useState(STARTER); const [filename, setFilename] = useState("submitted.py");
  const [title, setTitle] = useState("Code review"); const [llm, setLlm] = useState(true);
  const [busy, setBusy] = useState(false); const [err, setErr] = useState(""); const fileRef = useRef<HTMLInputElement>(null);

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]; if (!f) return;
    if (f.size > 100_000) return setErr("File exceeds 100 KB limit.");
    if (!f.name.endsWith(".py")) return setErr("Only .py files are supported in this version.");
    setFilename(f.name); setCode(await f.text()); setErr("");
  }
  async function analyze() {
    if (!code.trim()) return setErr("Paste some Python code first.");
    setBusy(true); setErr("");
    try {
      const r = await api<any>("/api/v1/reviews/code", { method: "POST", body: JSON.stringify({ title, files: [{ path: filename, content: code }], include_llm: llm }) });
      router.push(`/reviews/${r.id}`);
    } catch (e:any) { setErr(e.message); setBusy(false); }
  }
  return (
    <AppShell>
      <p className="mono-strip text-accent">// review workspace</p>
      <h1 className="headline text-5xl mt-1 mb-6">New code review</h1>
      <div className="grid xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 panel">
          <div className="flex flex-wrap items-center gap-3 px-4 py-3 border-b-2 border-app bg-surface2">
            <input className="font-mono font-bold bg-transparent border-b-2 border-app outline-none w-44" value={filename} onChange={e=>setFilename(e.target.value)} aria-label="Filename"/>
            <span className="badge bg-accent3 text-black">python</span>
            <button className="btn btn-ghost !py-1.5 !px-3 ml-auto" onClick={()=>fileRef.current?.click()}><Upload size={16}/> Upload .py</button>
            <input ref={fileRef} type="file" accept=".py,text/x-python" className="hidden" onChange={onFile}/>
          </div>
          <Monaco height="480px" language="python" theme={resolvedTheme==="dark"?"vs-dark":"light"} value={code} onChange={v=>setCode(v||"")}
            options={{ minimap:{enabled:false}, fontSize:13.5, scrollBeyondLastLine:false }} />
          <p className="px-4 py-2 text-xs text-muted2 border-t border-app font-mono">Your code is parsed, never executed. Max 100 KB/file.</p>
        </div>
        <aside className="space-y-5">
          <div className="panel p-5 hard-shadow-sm">
            <h2 className="headline text-2xl mb-4">Analysis setup</h2>
            <label className="mono-strip" htmlFor="title">Review title</label>
            <input id="title" className="input mt-1 mb-4" value={title} onChange={e=>setTitle(e.target.value)}/>
            <div className="space-y-2 text-sm font-mono">
              <p>✓ AST checks (always)</p><p>✓ Ruff lint (always)</p><p>✓ Bandit security (always)</p>
              <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={llm} onChange={e=>setLlm(e.target.checked)}/> LLM hypotheses {llm ? "(on)" : "(off)"}</label>
            </div>
            {err && <p role="alert" className="mt-4 text-sm font-bold" style={{color:"#dc2626"}}>{err}</p>}
            <button onClick={analyze} disabled={busy} className="btn btn-primary w-full justify-center mt-5 text-lg disabled:opacity-60">
              {busy ? <><Loader2 className="animate-spin" size={20}/> Analyzing…</> : <><Play size={20}/> Analyze code</>}
            </button>
            <p className="text-xs text-muted2 mt-3">If no LLM key is configured on the server, you still get full static results and the review is marked “partial” — never faked.</p>
          </div>
          <div className="panel-flat p-5">
            <p className="mono-strip text-accent mb-2">// try it</p>
            <p className="text-sm text-muted2">The starter code contains a mutable default, <code className="font-mono">eval()</code>, and a bare <code className="font-mono">except:</code> — the analyzers should catch all three.</p>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}

"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { api, fmtDate, SEV_ORDER, type ReviewDetail, type Finding } from "@/lib/api";
import { SevBadge, SourceBadge } from "@/components/ui";
import CodeView from "./codeview";
import { Download, ExternalLink, Search } from "lucide-react";

export default function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [err, setErr] = useState("");
  const [sel, setSel] = useState<Finding | null>(null);
  const [q, setQ] = useState(""); const [sev, setSev] = useState("all"); const [cat, setCat] = useState("all");
  const [src, setSrc] = useState("all"); const [sort, setSort] = useState("severity");

  useEffect(() => { api<ReviewDetail>(`/api/v1/reviews/${id}`).then(r => { setReview(r); setSel(r.findings[0] || null); }).catch(e => setErr(e.message)); }, [id]);

  const findings = useMemo(() => {
    if (!review) return [];
    let list = review.findings.filter(f =>
      (sev === "all" || f.severity === sev) && (cat === "all" || f.category === cat) && (src === "all" || f.source === src) &&
      (q === "" || (f.title + f.file_path + f.description).toLowerCase().includes(q.toLowerCase())));
    if (sort === "severity") list = [...list].sort((a,b) => SEV_ORDER[b.severity] - SEV_ORDER[a.severity]);
    if (sort === "confidence") list = [...list].sort((a,b) => ({high:3,medium:2,low:1} as any)[b.confidence] - ({high:3,medium:2,low:1} as any)[a.confidence]);
    if (sort === "file") list = [...list].sort((a,b) => (a.file_path + (a.start_line||0)).localeCompare(b.file_path + (b.start_line||0)));
    return list;
  }, [review, q, sev, cat, src, sort]);

  if (err) return <AppShell><p role="alert" className="panel p-6 font-bold">{err}</p></AppShell>;
  if (!review) return <AppShell><p className="mono-strip">Loading review…</p></AppShell>;
  const fileContent = review.files.find(f => f.path === sel?.file_path)?.content || review.files[0]?.content || "";
  const cats = Array.from(new Set(review.findings.map(f => f.category)));

  return (
    <AppShell>
      <div className="flex flex-wrap gap-4 items-start justify-between mb-5">
        <div>
          <p className="mono-strip text-accent">// findings explorer · {review.status}</p>
          <h1 className="headline text-4xl mt-1">{review.title}</h1>
          <p className="text-sm text-muted2 font-mono mt-1">{review.source_label} · {fmtDate(review.created_at)}{review.head_sha ? ` · SHA ${review.head_sha.slice(0,7)}` : ""}
            {review.github_url && <a className="text-accent2 underline ml-2 inline-flex items-center gap-1" href={review.github_url} target="_blank" rel="noreferrer">Open PR <ExternalLink size={13}/></a>}</p>
        </div>
        <div className="flex gap-2">
          <a className="btn btn-ghost hard-shadow-sm" href={`/api/v1/reviews/${review.id}/export?format=json`}><Download size={16}/> JSON</a>
          <a className="btn btn-ghost hard-shadow-sm" href={`/api/v1/reviews/${review.id}/export?format=csv`}><Download size={16}/> CSV</a>
        </div>
      </div>

      {review.warnings?.length > 0 && <div className="panel-flat p-3 mb-5 text-sm"><strong>Warnings:</strong> {review.warnings.join(" · ")}</div>}
      {review.summary?.llm_summary && <div className="panel p-4 mb-5"><p className="mono-strip text-accent mb-1">PR / review summary (AI)</p><p className="text-sm whitespace-pre-wrap">{review.summary.llm_summary}</p></div>}
      {review.summary?.changed_files && <div className="panel-flat p-3 mb-5 text-sm font-mono">Changed files: {review.summary.changed_files.join(", ")}<br/><span className="text-muted2">{review.summary.analysis_scope}</span></div>}

      <div className="flex gap-1.5 flex-wrap mb-5">
        {Object.entries(review.finding_counts || {}).map(([k,v]) => <span key={k} className={`badge sev-${k}`}>{k}: {v}</span>)}
        <span className="badge">total: {review.findings.length}</span>
      </div>

      <div className="panel p-3 mb-5 flex flex-wrap gap-3 items-center">
        <label className="flex items-center gap-2 flex-1 min-w-[200px]"><Search size={16}/><input className="input" placeholder="Search findings…" value={q} onChange={e=>setQ(e.target.value)} aria-label="Search findings"/></label>
        <select className="input !w-auto" value={sev} onChange={e=>setSev(e.target.value)} aria-label="Filter severity"><option value="all">All severities</option>{["critical","high","medium","low","info"].map(s=><option key={s}>{s}</option>)}</select>
        <select className="input !w-auto" value={cat} onChange={e=>setCat(e.target.value)} aria-label="Filter category"><option value="all">All categories</option>{cats.map(s=><option key={s}>{s}</option>)}</select>
        <select className="input !w-auto" value={src} onChange={e=>setSrc(e.target.value)} aria-label="Filter source"><option value="all">All sources</option>{["ast","ruff","bandit","llm"].map(s=><option key={s}>{s}</option>)}</select>
        <select className="input !w-auto" value={sort} onChange={e=>setSort(e.target.value)} aria-label="Sort findings"><option value="severity">Sort: severity</option><option value="confidence">Sort: confidence</option><option value="file">Sort: file/line</option></select>
      </div>

      <div className="grid xl:grid-cols-2 gap-6">
        <div className="panel divide-y divide-[var(--border)] max-h-[720px] overflow-auto">
          {findings.length === 0 && <p className="p-6 text-muted2">No findings match these filters. That is a real result — not every file has findings.</p>}
          {findings.map(f => (
            <button key={f.id} onClick={() => setSel(f)} className={`w-full text-left p-4 hover:bg-surface2 ${sel?.id===f.id ? "bg-surface2 border-l-4 border-l-[var(--accent)]" : ""}`}>
              <div className="flex gap-2 flex-wrap items-center mb-1"><SevBadge sev={f.severity}/><SourceBadge source={f.source} verification={f.verification_status}/><span className="badge">{f.confidence} confidence</span></div>
              <p className="font-bold">{f.title}</p>
              <p className="text-xs text-muted2 font-mono">{f.file_path}{f.start_line ? `:${f.start_line}` : " (line unverified)"} · {f.rule_id} · {f.category}</p>
            </button>
          ))}
        </div>
        <div>
          {sel ? (
            <div className="panel p-5 hard-shadow-sm sticky top-24">
              <div className="flex gap-2 flex-wrap mb-3"><SevBadge sev={sel.severity}/><SourceBadge source={sel.source} verification={sel.verification_status}/></div>
              <h2 className="headline text-2xl mb-2">{sel.title}</h2>
              <p className="font-mono text-xs text-muted2 mb-3">{sel.file_path}{sel.start_line ? `:${sel.start_line}${sel.end_line && sel.end_line!==sel.start_line ? `-${sel.end_line}` : ""}` : ""} · rule {sel.rule_id || "—"}</p>
              <h3 className="mono-strip text-accent mt-4 mb-1">Why it matters</h3><p className="text-sm">{sel.explanation || sel.description}</p>
              {sel.evidence && <><h3 className="mono-strip text-accent mt-4 mb-1">Evidence</h3><pre className="bg-surface2 border border-app p-3 font-mono text-xs overflow-x-auto">{sel.evidence}</pre></>}
              <h3 className="mono-strip text-accent mt-4 mb-1">Suggested fix (unverified — review before applying)</h3><p className="text-sm">{sel.remediation}</p>
              {sel.suggested_patch && <pre className="bg-surface2 border border-app p-3 font-mono text-xs overflow-x-auto mt-2">{sel.suggested_patch}</pre>}
              {sel.suggested_tests?.length > 0 && <><h3 className="mono-strip text-accent mt-4 mb-1">Proposed tests (not yet run)</h3>{sel.suggested_tests.map((t,i)=><pre key={i} className="bg-surface2 border border-app p-3 font-mono text-xs overflow-x-auto mt-2">{t}</pre>)}</>}
              <h3 className="mono-strip text-accent mt-5 mb-2">Source code</h3>
              <div className="border-2 border-app"><CodeView code={fileContent} line={sel.start_line}/></div>
            </div>
          ) : <div className="panel p-6 text-muted2">Select a finding to inspect it.</div>}
        </div>
      </div>
    </AppShell>
  );
}

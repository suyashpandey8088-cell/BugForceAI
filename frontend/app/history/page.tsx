"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { api, fmtDate, type Review } from "@/lib/api";
import { EmptyState } from "@/components/ui";
import { Download, Trash2 } from "lucide-react";
export default function History(){
  const [rows,setRows]=useState<Review[]>([]); const [err,setErr]=useState("");
  const load=()=>api<Review[]>("/api/v1/reviews").then(setRows).catch(e=>setErr(e.message));
  useEffect(()=>{ load(); },[]);
  async function del(id:string){ if(!confirm("Delete this review and its stored source?")) return; await api(`/api/v1/reviews/${id}`,{method:"DELETE"}); load(); }
  return <AppShell>
    <p className="mono-strip text-accent">// review history</p><h1 className="headline text-5xl mt-1 mb-6">History</h1>
    {err && <p role="alert" className="panel-flat p-3 mb-4">{err}</p>}
    {rows.length===0 ? <EmptyState title="No reviews yet" body="Run your first analysis from the workspace." action={<Link className="btn btn-primary" href="/review">New review</Link>}/> :
    <div className="panel divide-y divide-[var(--border)]">{rows.map(r=>(
      <div key={r.id} className="flex flex-wrap items-center gap-3 p-4 hover:bg-surface2">
        <Link href={`/reviews/${r.id}`} className="flex-1 min-w-[220px]"><p className="font-bold">{r.title}</p>
        <p className="text-xs text-muted2 font-mono">{r.source_label} · {fmtDate(r.created_at)} · {r.status} · {r.source_type}</p></Link>
        <div className="flex gap-1.5">{Object.entries(r.finding_counts||{}).map(([k,v])=><span key={k} className={`badge sev-${k}`}>{k} {v}</span>)}</div>
        <a className="btn btn-ghost !p-2" href={`/api/v1/reviews/${r.id}/export?format=json`} aria-label="Export JSON"><Download size={16}/></a>
        <button className="btn btn-ghost !p-2" onClick={()=>del(r.id)} aria-label="Delete review"><Trash2 size={16}/></button>
      </div>))}</div>}
  </AppShell>;
}

"use client";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from "recharts";
import { useTheme } from "next-themes";
import { EmptyState } from "@/components/ui";
import Link from "next/link";
const COLORS=["#dc2626","#FF6B35","#f59e0b","#5B7CFA","#C5F467","#888"];
export default function Analytics(){
  const [d,setD]=useState<any>(null); const {resolvedTheme}=useTheme();
  useEffect(()=>{ api<any>("/api/v1/analytics/summary").then(setD).catch(()=>setD({reviews:0})); },[]);
  if(!d) return <AppShell><p className="mono-strip">Loading…</p></AppShell>;
  const sev=Object.entries(d.by_severity||{}).map(([name,value])=>({name,value}));
  const cat=Object.entries(d.by_category||{}).map(([name,value])=>({name,value}));
  const axis = resolvedTheme==="dark" ? "#A8ADBA" : "#626571";
  const tip={contentStyle:{background:"var(--surface)",border:"2px solid var(--border)",color:"var(--text)",fontFamily:"monospace",fontSize:12}};
  return <AppShell>
    <p className="mono-strip text-accent">// analytics — your data only</p><h1 className="headline text-5xl mt-1 mb-2">Analytics</h1>
    <p className="text-muted2 mb-8">Computed from your stored reviews. AI hypotheses are counted as findings, not confirmed defects.</p>
    {d.reviews===0 ? <EmptyState title="No data yet" body="Analytics appear after your first completed review." action={<Link className="btn btn-primary" href="/review">Run a review</Link>}/> : <>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">{[["Reviews",d.reviews],["Completed",d.completed],["Partial",d.partial],["Failed",d.failed]].map(([l,v])=><div key={l} className="panel-flat p-4 text-center"><p className="headline text-4xl">{v}</p><p className="mono-strip text-muted2">{l}</p></div>)}</div>
    <div className="grid lg:grid-cols-2 gap-6">
      <div className="panel p-5"><h2 className="headline text-2xl mb-4">Findings by severity</h2><ResponsiveContainer width="100%" height={260}><PieChart><Pie data={sev} dataKey="value" nameKey="name" label>{sev.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} stroke="var(--border)"/>)}</Pie><Tooltip {...tip}/></PieChart></ResponsiveContainer></div>
      <div className="panel p-5"><h2 className="headline text-2xl mb-4">Findings by category</h2><ResponsiveContainer width="100%" height={260}><BarChart data={cat}><CartesianGrid stroke="var(--border)" strokeDasharray="3 3"/><XAxis dataKey="name" tick={{fill:axis,fontSize:11}}/><YAxis tick={{fill:axis}}/><Tooltip {...tip}/><Bar dataKey="value" fill="#FF6B35" stroke="var(--border)"/></BarChart></ResponsiveContainer></div>
      <div className="panel p-5"><h2 className="headline text-2xl mb-4">Reviews over time</h2><ResponsiveContainer width="100%" height={240}><LineChart data={d.over_time}><CartesianGrid stroke="var(--border)" strokeDasharray="3 3"/><XAxis dataKey="date" tick={{fill:axis,fontSize:11}}/><YAxis tick={{fill:axis}}/><Tooltip {...tip}/><Line dataKey="reviews" stroke="#5B7CFA" strokeWidth={3}/></LineChart></ResponsiveContainer></div>
      <div className="panel p-5"><h2 className="headline text-2xl mb-4">Most-flagged files</h2>{(d.top_files||[]).length===0?<p className="text-muted2">No findings yet.</p>:<ul className="space-y-2 font-mono text-sm">{d.top_files.map((f:any)=><li key={f.file} className="flex justify-between border-b border-app pb-1"><span>{f.file}</span><strong>{f.findings}</strong></li>)}</ul>}
      <h3 className="headline text-xl mt-6 mb-2">By source</h3><ul className="font-mono text-sm space-y-1">{Object.entries(d.by_source||{}).map(([k,v]:any)=><li key={k} className="flex justify-between"><span>{k==="llm"?"LLM (hypotheses)":k+" (tool-confirmed)"}</span><strong>{v}</strong></li>)}</ul></div>
    </div></>}
  </AppShell>;
}

"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import { Github, Loader2, Play } from "lucide-react";
export default function GithubPage(){
  const router=useRouter();
  const [cfg,setCfg]=useState<any>(null); const [me,setMe]=useState<any>(null);
  const [repos,setRepos]=useState<any[]>([]); const [pulls,setPulls]=useState<any[]>([]);
  const [repo,setRepo]=useState(""); const [err,setErr]=useState(""); const [busy,setBusy]=useState(""); const [q,setQ]=useState("");
  useEffect(()=>{ api<any>("/api/v1/auth/config").then(setCfg).catch(()=>{}); api<any>("/api/v1/auth/me").then(u=>{setMe(u); if(u.github_connected) loadRepos();}).catch(()=>{}); },[]);
  async function loadRepos(){ try{ const r=await api<any>("/api/v1/github/repositories"); setRepos(r.repositories); }catch(e:any){ setErr(e.message);} }
  async function loadPulls(full:string){ setRepo(full); const [o,r]=full.split("/"); try{ const d=await api<any>(`/api/v1/github/repositories/${o}/${r}/pulls`); setPulls(d.pulls);}catch(e:any){setErr(e.message);} }
  async function review(p:any){ const [o,r]=repo.split("/"); setBusy(String(p.number)); try{ const rev=await api<any>("/api/v1/reviews/pull-request",{method:"POST",body:JSON.stringify({owner:o,repo:r,number:p.number})}); router.push(`/reviews/${rev.id}`);}catch(e:any){setErr(e.message); setBusy("");} }
  const shown=repos.filter(x=>x.full_name.toLowerCase().includes(q.toLowerCase()));
  return <AppShell>
    <p className="mono-strip text-accent">// github — read-only</p><h1 className="headline text-5xl mt-1 mb-6">Pull request review</h1>
    {err && <p role="alert" className="panel-flat p-3 mb-4 font-semibold">{err}</p>}
    {!me?.github_connected ? (
      <div className="panel p-8 hard-shadow-sm max-w-2xl"><Github size={36} className="text-accent mb-4"/>
      <h2 className="headline text-3xl mb-2">Connect GitHub</h2>
      <p className="text-muted2 mb-5">Read-only OAuth (scope: repo, read:user). Tokens are encrypted at rest on the server and never shown in the browser. BugForge never pushes commits, comments, or merges.</p>
      {cfg && !cfg.github_configured ? <p className="panel-flat p-3 text-sm">GitHub is not configured on this server. Add GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET (see docs/github-integration.md), then reload.</p>
      : <a className="btn btn-primary" href="/api/v1/github/connect"><Github size={18}/> Connect GitHub</a>}
      </div>
    ) : <>
      <div className="flex flex-wrap gap-3 items-center mb-5"><span className="badge bg-accent3 text-black">connected: @{me.github_username}</span>
      <button className="btn btn-ghost !py-1.5" onClick={async()=>{await api("/api/v1/github/disconnect",{method:"POST"}); location.reload();}}>Disconnect</button>
      <input className="input !w-64" placeholder="Search repositories…" value={q} onChange={e=>setQ(e.target.value)} aria-label="Search repositories"/></div>
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="panel divide-y divide-[var(--border)] max-h-[560px] overflow-auto">
          {shown.length===0 && <p className="p-5 text-muted2">No repositories loaded. If this stays empty, check backend GitHub configuration or reconnect.</p>}
          {shown.map((r:any)=><button key={r.full_name} onClick={()=>loadPulls(r.full_name)} className={`w-full text-left p-4 hover:bg-surface2 ${repo===r.full_name?"bg-surface2":""}`}>
            <p className="font-bold font-mono text-sm">{r.full_name} {r.private && <span className="badge sev-medium">private</span>}</p>
            <p className="text-xs text-muted2">{r.description||"—"} · default: {r.default_branch}</p></button>)}
        </div>
        <div className="panel divide-y divide-[var(--border)] max-h-[560px] overflow-auto">
          {!repo && <p className="p-5 text-muted2">Select a repository to list its pull requests.</p>}
          {repo && pulls.length===0 && <p className="p-5 text-muted2">No pull requests found for {repo}.</p>}
          {pulls.map((p:any)=><div key={p.number} className="p-4 flex gap-3 items-center justify-between">
            <div><p className="font-bold">#{p.number} {p.title}</p><p className="text-xs text-muted2 font-mono">@{p.author} · {p.state} · {p.head} → {p.base} · SHA {p.head_sha.slice(0,7)}</p></div>
            <button className="btn btn-primary !py-2 shrink-0" disabled={!!busy} onClick={()=>review(p)}>{busy===String(p.number)?<Loader2 className="animate-spin" size={16}/>:<Play size={16}/>} Review</button>
          </div>)}
        </div>
      </div>
    </>}
  </AppShell>;
}

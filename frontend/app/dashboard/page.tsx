"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { api, fmtDate, type Review } from "@/lib/api";
import { EmptyState } from "@/components/ui";
import { ArrowRight, GitPullRequest, Code2 } from "lucide-react";

export default function Dashboard() {
  const [reviews, setReviews] = useState<Review[]>([]); const [err, setErr] = useState(""); const [user, setUser] = useState<any>(null);
  useEffect(() => { api<any>("/api/v1/auth/me").then(setUser).catch(()=>{}); api<Review[]>("/api/v1/reviews").then(setReviews).catch(e=>setErr(e.message)); }, []);
  const totalFindings = reviews.reduce((a, r) => a + Object.values(r.finding_counts || {}).reduce((x,y)=>x+y,0), 0);
  return (
    <AppShell>
      <p className="mono-strip text-accent">// dashboard</p>
      <h1 className="headline text-5xl mt-1 mb-2">Welcome{user ? `, ${user.display_name || user.email.split("@")[0]}` : ""}.</h1>
      <p className="text-muted2 mb-8">Submit code or pick a GitHub PR. Static findings are tool-confirmed; AI findings are labeled hypotheses.</p>
      <div className="grid md:grid-cols-2 gap-5 mb-8">
        <Link href="/review" className="panel p-6 hard-shadow hover:-translate-y-0.5 transition-transform">
          <Code2 className="text-accent mb-3" size={32}/><h2 className="headline text-3xl">Review pasted code</h2>
          <p className="text-muted2 mt-1">Paste Python or upload a .py file. AST + Ruff + Bandit run instantly; LLM review when configured.</p>
          <span className="btn btn-primary mt-5">Start code review <ArrowRight size={18}/></span>
        </Link>
        <Link href="/github" className="panel p-6 hard-shadow hover:-translate-y-0.5 transition-transform">
          <GitPullRequest className="text-accent2 mb-3" size={32}/><h2 className="headline text-3xl">Review a GitHub PR</h2>
          <p className="text-muted2 mt-1">Read-only access to repos you authorize. Findings mapped to changed Python files at the PR head SHA.</p>
          <span className="btn btn-blue mt-5">Choose a pull request <ArrowRight size={18}/></span>
        </Link>
      </div>
      <div className="grid grid-cols-3 gap-4 mb-8 max-w-xl">
        {[["Reviews", reviews.length], ["Findings", totalFindings], ["Partial", reviews.filter(r=>r.status==="partial").length]].map(([l,v]) => (
          <div key={l} className="panel-flat p-4 text-center"><p className="headline text-3xl">{v}</p><p className="mono-strip text-muted2">{l}</p></div>
        ))}
      </div>
      <h2 className="headline text-3xl mb-4">Recent reviews</h2>
      {err && <p role="alert" className="panel-flat p-3 mb-4">{err}</p>}
      {reviews.length === 0 ? (
        <EmptyState title="No reviews yet" body="Your first review takes under a minute: paste a Python file and hit Analyze. Try code with eval(), a mutable default argument, or a bare except to see real findings."
          action={<Link href="/review" className="btn btn-primary">Run my first review</Link>} />
      ) : (
        <div className="panel divide-y divide-[var(--border)]">
          {reviews.slice(0,6).map(r => (
            <Link key={r.id} href={`/reviews/${r.id}`} className="flex flex-wrap gap-3 items-center justify-between p-4 hover:bg-surface2">
              <div><p className="font-bold">{r.title}</p><p className="text-xs text-muted2 font-mono">{r.source_label} · {fmtDate(r.created_at)} · {r.status}</p></div>
              <div className="flex gap-1.5">{Object.entries(r.finding_counts||{}).map(([k,v]) => <span key={k} className={`badge sev-${k}`}>{k} {v}</span>)}</div>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}

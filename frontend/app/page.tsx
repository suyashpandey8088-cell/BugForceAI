import Link from "next/link";
import { ArrowRight, ShieldCheck, ScanSearch, GitPullRequest, FileWarning, TerminalSquare } from "lucide-react";
import { Logo, ThemeToggle } from "@/components/ui";

const SAMPLE = `def get_user(db, user_id, cache=[]):
    cache.append(user_id)
    query = "SELECT * FROM users WHERE id=" + user_id
    return eval(db.execute(query))  # ← AST103 · Bandit B307`;

export default function Home() {
  return (
    <div className="min-h-screen bg-app text-app relative overflow-hidden">
      <div className="absolute inset-0 tick-bg pointer-events-none" aria-hidden />
      <header className="relative flex items-center justify-between px-5 lg:px-12 h-16 border-b-2 border-app bg-surface">
        <Logo />
        <nav className="flex items-center gap-3">
          <Link href="/about" className="hidden sm:inline font-semibold hover:text-accent">How it works</Link>
          <ThemeToggle />
          <Link href="/login" className="btn btn-ghost hard-shadow-sm">Sign in</Link>
          <Link href="/register" className="btn btn-primary">Start free</Link>
        </nav>
      </header>

      <section className="relative px-5 lg:px-12 pt-14 pb-10 grid lg:grid-cols-12 gap-10 max-w-[1500px] mx-auto">
        <div className="lg:col-span-7">
          <p className="mono-strip text-accent mb-4">{"// code review, forged properly"}</p>
          <h1 className="headline text-6xl md:text-8xl">FIND BUGS<br/>BEFORE THEY<br/><span className="text-accent">SHIP.</span></h1>
          <p className="mt-6 text-lg text-muted2 max-w-xl">BugForge AI runs real Python AST checks, Ruff and Bandit static analysis, then a validated LLM review — and labels exactly which findings are tool-confirmed and which are AI hypotheses.</p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link href="/register" className="btn btn-primary text-lg">Start a code review <ArrowRight size={20}/></Link>
            <Link href="/login" className="btn btn-ghost hard-shadow-sm text-lg">Review a GitHub PR</Link>
          </div>
          <div className="mt-10 grid grid-cols-3 max-w-lg border-2 border-app bg-surface text-center">
            {[["AST","syntax-tree checks"],["Ruff + Bandit","static & security"],["LLM","hypotheses, labeled"]].map(([a,b]) => (
              <div key={a} className="p-3 border-r-2 last:border-r-0 border-app"><p className="headline">{a}</p><p className="text-xs text-muted2">{b}</p></div>
            ))}
          </div>
        </div>
        <div className="lg:col-span-5">
          <div className="panel hard-shadow rotate-1">
            <div className="flex items-center justify-between px-4 py-2 border-b-2 border-app bg-surface2">
              <span className="font-mono text-sm font-bold">app.py — analysis</span><span className="badge sev-high">3 findings</span>
            </div>
            <pre className="p-4 overflow-x-auto font-mono text-[13px] leading-6">{SAMPLE}</pre>
            <div className="border-t-2 border-app divide-y divide-[var(--border)]">
              {[["critical-ish → high","eval() on dynamic input","AST · tool-confirmed"],["medium","Mutable default argument","Ruff/Bandit + AST"],["AI hypothesis","Possible SQL injection — verify query construction","LLM · unverified"]].map(([s,t,src]) => (
                <div key={t} className="px-4 py-3 flex gap-3 items-start"><FileWarning className="text-accent shrink-0 mt-0.5" size={18}/><div><p className="font-bold text-sm">{t}</p><p className="text-xs text-muted2 font-mono">{src} · {s}</p></div></div>
              ))}
            </div>
          </div>
          <p className="mono-strip text-muted2 mt-4 text-center">illustrative UI — real findings come from your code</p>
        </div>
      </section>

      <section className="relative px-5 lg:px-12 pb-16 max-w-[1500px] mx-auto grid md:grid-cols-3 gap-5">
        {[
          { icon: ScanSearch, title: "Deterministic first", body: "AST traversal, Ruff and Bandit run locally on parsed code — never by executing it. Reproducible, explainable findings with rule IDs." },
          { icon: ShieldCheck, title: "AI, honestly labeled", body: "LLM output must pass strict JSON schema validation and line-number checks. Unverifiable lines are flagged, never invented." },
          { icon: GitPullRequest, title: "PR-aware review", body: "Connect GitHub read-only, pick a pull request, and get findings mapped to changed Python files at the exact head SHA." },
        ].map(({icon:Icon,title,body}) => (
          <article key={title} className="panel p-6 hard-shadow-sm">
            <Icon className="text-accent mb-4" size={30}/><h2 className="headline text-2xl mb-2">{title}</h2><p className="text-muted2">{body}</p>
          </article>
        ))}
      </section>

      <footer className="relative border-t-2 border-app bg-surface px-5 lg:px-12 py-6 flex flex-wrap gap-4 items-center justify-between">
        <Logo />
        <p className="text-sm text-muted2 flex items-center gap-2"><TerminalSquare size={16}/> BugForge AI never executes your code and never auto-merges anything.</p>
        <Link href="/about" className="font-semibold hover:text-accent">Limitations & security →</Link>
      </footer>
    </div>
  );
}

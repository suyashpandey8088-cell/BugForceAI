import AppShell from "@/components/AppShell";
export default function About(){
  return <AppShell>
    <p className="mono-strip text-accent">// about & limitations</p><h1 className="headline text-5xl mt-1 mb-6">How BugForge works</h1>
    <div className="max-w-4xl space-y-6">
      {[
        ["1 · Parse, never execute","Submitted Python is parsed with the ast module and written only to an isolated temp directory for Ruff/Bandit. Your code is never imported or run on the server."],
        ["2 · Deterministic static analysis","Custom AST checks (mutable defaults, eval/exec, bare excepts, unreachable code…), Ruff lint rules, and Bandit security checks produce tool-confirmed findings with rule IDs and real line numbers."],
        ["3 · Validated LLM hypotheses","If an LLM key is configured server-side, the model receives only relevant code, must return strict JSON, and every line reference is validated against your source. Unverifiable findings are labeled 'line unverified'. Nothing is auto-applied or auto-merged."],
        ["What it cannot do","Only Python is analyzed today. AST/static checks find patterns, not proof — a clean report does not mean bug-free code, and an AI hypothesis is not a confirmed vulnerability. Human review remains essential. Semgrep rules are not bundled in this version."],
        ["Privacy","OAuth tokens are encrypted at rest and never sent to the browser. Delete any review (or your whole account) to remove its stored source. GitHub access is read-only."],
      ].map(([t,b])=><section key={t} className="panel p-6"><h2 className="headline text-2xl mb-2">{t}</h2><p className="text-muted2">{b}</p></section>)}
    </div>
  </AppShell>;
}

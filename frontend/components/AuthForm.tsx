"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { api } from "@/lib/api";
import { Logo, ThemeToggle } from "./ui";
import { z } from "zod";

const schema = z.object({ email: z.string().email("Enter a valid email"), password: z.string().min(1, "Password required") });

export default function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState(""); const [name, setName] = useState("");
  const [show, setShow] = useState(false); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const [cfg, setCfg] = useState<any>(null); const [agreed, setAgreed] = useState(false);
  useEffect(() => { api<any>("/api/v1/auth/config").then(setCfg).catch(() => setCfg({ google_configured: false })); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr("");
    const parsed = schema.safeParse({ email, password });
    if (!parsed.success) return setErr(parsed.error.issues[0].message);
    if (mode === "register") {
      if (password.length < 8 || !/[a-zA-Z]/.test(password) || !/\d/.test(password)) return setErr("Password must be 8+ characters with a letter and a number.");
      if (password !== confirm) return setErr("Passwords do not match.");
      if (!agreed) return setErr("Please accept the Terms and Privacy Policy.");
    }
    setBusy(true);
    try {
      if (mode === "register") await api("/api/v1/auth/register", { method: "POST", body: JSON.stringify({ email, password, display_name: name }) });
      else await api("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      router.push("/dashboard");
    } catch (e:any) { setErr(e.message); } finally { setBusy(false); }
  }

  return (
    <div className="min-h-screen bg-app text-app grid lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-between p-10 bg-accent text-white border-r-2 border-app">
        <Logo />
        <div><p className="mono-strip mb-3">{"// welcome to the forge"}</p>
          <h1 className="headline text-6xl">{mode === "login" ? "WELCOME\nBACK." : "FORGE YOUR\nFIRST REVIEW."}</h1>
          <p className="mt-4 max-w-md text-white/85">Real AST + static analysis. AI hypotheses, clearly labeled. No fake findings, ever.</p></div>
        <p className="font-mono text-xs">AST · Ruff · Bandit · validated LLM · GitHub read-only</p>
      </div>
      <div className="p-6 lg:p-12 flex flex-col">
        <div className="flex justify-between lg:justify-end"><span className="lg:hidden"><Logo/></span><ThemeToggle/></div>
        <div className="my-auto w-full max-w-md mx-auto">
          <h2 className="headline text-4xl mb-2">{mode === "login" ? "Sign in" : "Create account"}</h2>
          <p className="text-muted2 mb-6">{mode === "login" ? "Review code, track findings, export reports." : "Free to start. Google sign-up needs no password."}</p>
          {cfg?.google_configured ? (
            <a href="/api/v1/auth/google" className="btn btn-ghost hard-shadow-sm w-full justify-center mb-4">
              <span className="font-black text-lg">G</span> Continue with Google
            </a>
          ) : (
            <div className="panel-flat p-3 mb-4 text-sm text-muted2"><strong className="text-app">Google sign-in not configured.</strong> Set GOOGLE_CLIENT_ID/SECRET on the server (see docs), or use email below.</div>
          )}
          <div className="flex items-center gap-3 my-4"><hr className="flex-1 border-app"/><span className="mono-strip text-muted2">or with email</span><hr className="flex-1 border-app"/></div>
          <form onSubmit={submit} className="space-y-4" noValidate>
            {mode === "register" && <div><label className="mono-strip" htmlFor="name">Display name</label><input id="name" className="input mt-1" value={name} onChange={e=>setName(e.target.value)} autoComplete="name"/></div>}
            <div><label className="mono-strip" htmlFor="email">Email</label><input id="email" type="email" className="input mt-1" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email" required/></div>
            <div><label className="mono-strip" htmlFor="password">Password</label>
              <div className="relative mt-1"><input id="password" type={show?"text":"password"} className="input pr-11" value={password} onChange={e=>setPassword(e.target.value)} autoComplete={mode==="login"?"current-password":"new-password"} required/>
              <button type="button" aria-label={show?"Hide password":"Show password"} className="absolute right-3 top-1/2 -translate-y-1/2" onClick={()=>setShow(!show)}>{show?<EyeOff size={18}/>:<Eye size={18}/>}</button></div></div>
            {mode === "register" && <>
              <div><label className="mono-strip" htmlFor="confirm">Confirm password</label><input id="confirm" type={show?"text":"password"} className="input mt-1" value={confirm} onChange={e=>setConfirm(e.target.value)} autoComplete="new-password" required/></div>
              <label className="flex gap-2 text-sm"><input type="checkbox" checked={agreed} onChange={e=>setAgreed(e.target.checked)} className="mt-1"/> I agree to the <Link className="underline" href="/about">Terms & Privacy</Link></label>
            </>}
            {err && <p role="alert" className="panel-flat p-3 text-sm font-semibold" style={{borderColor:"#dc2626"}}>{err}</p>}
            <button disabled={busy} className="btn btn-primary w-full justify-center hard-shadow-sm disabled:opacity-60">{busy ? "Working…" : mode==="login" ? "Sign in" : "Create account"}</button>
          </form>
          <p className="mt-5 text-sm text-muted2">{mode==="login" ? <>New here? <Link className="font-bold text-accent underline" href="/register">Create account</Link> · <span title="Password reset is via Google or admin in this version">Forgot password?</span></> : <>Already registered? <Link className="font-bold text-accent underline" href="/login">Sign in</Link></>}</p>
        </div>
      </div>
    </div>
  );
}

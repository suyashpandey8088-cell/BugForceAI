"use client";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";
import { ThemeToggle } from "@/components/ui";
export default function Settings(){
  const [s,setS]=useState<any>(null); const [msg,setMsg]=useState(""); const {setTheme}=useTheme();
  useEffect(()=>{ api<any>("/api/v1/settings").then(setS).catch(e=>setMsg(e.message)); },[]);
  async function save(patch:any){ try{ const u=await api<any>("/api/v1/settings",{method:"PATCH",body:JSON.stringify(patch)}); setS(u); if(patch.theme) setTheme(patch.theme); setMsg("Saved."); }catch(e:any){ setMsg(e.message);} }
  if(!s) return <AppShell><p className="mono-strip">Loading settings…</p>{msg&&<p>{msg}</p>}</AppShell>;
  return <AppShell>
    <p className="mono-strip text-accent">// settings</p><h1 className="headline text-5xl mt-1 mb-6">Settings</h1>
    {msg && <p className="panel-flat p-3 mb-4 font-semibold">{msg}</p>}
    <div className="grid lg:grid-cols-2 gap-6 max-w-5xl">
      <section className="panel p-6"><h2 className="headline text-2xl mb-4">Profile</h2>
        <label className="mono-strip">Display name</label><input className="input mt-1 mb-3" value={s.display_name} onChange={e=>setS({...s,display_name:e.target.value})}/>
        <label className="mono-strip">Email (verified via provider)</label><input className="input mt-1" value={s.email} disabled/>
        <button className="btn btn-primary mt-4" onClick={()=>save({display_name:s.display_name})}>Save profile</button>
        <div className="mt-5 font-mono text-sm space-y-1"><p>Google: {s.google_connected?"connected":"not connected"}</p><p>GitHub: {s.github_connected?`connected (@${s.github_username})`:"not connected"}</p></div>
      </section>
      <section className="panel p-6"><h2 className="headline text-2xl mb-4">Appearance & review</h2>
        <p className="mono-strip mb-2">Theme</p><div className="flex items-center gap-3 mb-4"><ThemeToggle/><select className="input !w-auto" value={s.theme} onChange={e=>save({theme:e.target.value})} aria-label="Theme preference"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></div>
        <p className="text-xs text-muted2 mb-4">Theme also persists locally for instant load; signed-in preference syncs here.</p>
        <label className="mono-strip">Default language</label><select className="input mt-1 mb-4" value={s.default_language} onChange={e=>save({default_language:e.target.value})}><option value="python">Python (supported)</option></select>
        <label className="flex gap-2 items-center font-semibold"><input type="checkbox" checked={s.llm_enabled} onChange={e=>save({llm_enabled:e.target.checked})}/> Enable LLM review by default</label>
        <p className="text-xs text-muted2 mt-2">Provider & API key are server-managed via environment variables — never entered or exposed in the browser.</p>
      </section>
      <section className="panel p-6" style={{borderColor:"#dc2626"}}><h2 className="headline text-2xl mb-2">Danger zone</h2>
        <p className="text-sm text-muted2 mb-4">Deleting your account permanently deletes your reviews, stored source, findings, and connected identities.</p>
        <button className="btn" style={{background:"#dc2626",color:"#fff"}} onClick={async()=>{ if(confirm("Permanently delete your account and all reviews?")){ await api("/api/v1/account",{method:"DELETE"}); location.href="/register"; }}}>Delete account</button>
      </section>
    </div>
  </AppShell>;
}

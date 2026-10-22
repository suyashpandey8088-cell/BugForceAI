"use client";
import { useTheme } from "next-themes";
import { Sun, Moon, Bug } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const isDark = resolvedTheme === "dark";
  return (
    <button aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"} title="Toggle theme"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="btn btn-ghost !px-3 !py-2 hard-shadow-sm">
      {mounted && isDark ? <Sun size={18}/> : <Moon size={18}/>}
      <span className="hidden sm:inline mono-strip">{mounted ? (isDark ? "Light" : "Dark") : "Theme"}</span>
    </button>
  );
}

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2.5 group">
      <span className="bg-accent text-white border-2 border-app p-1.5 hard-shadow-sm group-hover:rotate-6 transition-transform"><Bug size={22} strokeWidth={2.5}/></span>
      <span className="headline text-xl">BUG<span className="text-accent">FORGE</span> <span className="text-accent2">AI</span></span>
    </Link>
  );
}

export function SevBadge({ sev }: { sev: string }) {
  return <span className={`badge sev-${sev}`}>{sev}</span>;
}
export function SourceBadge({ source, verification }: { source: string; verification: string }) {
  const label = source === "llm" ? "AI hypothesis" : `${source} · tool-confirmed`;
  return <span className="badge" style={{background: source==="llm" ? "var(--accent3)" : "var(--surface2)", color: source==="llm" ? "#111" : "var(--text)"}}>{label}{verification==="line-unverified" ? " · line unverified" : ""}</span>;
}
export function EmptyState({ title, body, action }: { title:string; body:string; action?:React.ReactNode }) {
  return (
    <div className="panel p-8 text-center">
      <p className="mono-strip text-accent mb-2">// nothing here yet</p>
      <h3 className="headline text-2xl mb-2">{title}</h3>
      <p className="text-muted2 max-w-md mx-auto mb-5">{body}</p>
      {action}
    </div>
  );
}

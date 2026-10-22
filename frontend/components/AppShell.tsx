"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LayoutDashboard, ScanSearch, History, BarChart3, Github, Settings, Info, LogOut, Menu, X } from "lucide-react";
import { Logo, ThemeToggle } from "./ui";
import { api } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/review", label: "New Review", icon: ScanSearch },
  { href: "/history", label: "History", icon: History },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/github", label: "GitHub PRs", icon: Github },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/about", label: "About & Limits", icon: Info },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    api<any>("/api/v1/auth/me").then(setUser).catch(() => router.push("/login"));
  }, [router]);
  async function logout() { await api("/api/v1/auth/logout", { method: "POST" }).catch(()=>{}); router.push("/login"); }
  return (
    <div className="min-h-screen bg-app text-app">
      <header className="sticky top-0 z-40 bg-surface border-b-2 border-app">
        <div className="flex items-center justify-between gap-3 px-4 lg:px-8 h-16">
          <div className="flex items-center gap-3">
            <button className="lg:hidden btn btn-ghost !p-2" aria-label="Toggle menu" onClick={() => setOpen(!open)}>{open ? <X size={20}/> : <Menu size={20}/>}</button>
            <Logo />
            <span className="hidden md:inline badge bg-accent3 text-black ml-2">AST + Ruff + Bandit + LLM</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden md:block mono-strip text-muted2">{user ? user.email : "…"}</span>
            <ThemeToggle />
            <button onClick={logout} className="btn btn-ghost !px-3 !py-2" aria-label="Log out"><LogOut size={18}/><span className="hidden sm:inline">Logout</span></button>
          </div>
        </div>
      </header>
      <div className="flex">
        <aside className={`${open ? "block" : "hidden"} lg:block w-60 shrink-0 border-r-2 border-app bg-surface min-h-[calc(100vh-4rem)] p-4 sticky top-16 self-start`}>
          <p className="mono-strip text-muted2 mb-3">// workspace</p>
          <nav className="space-y-1.5" aria-label="Main">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || pathname.startsWith(href + "/");
              return (
                <Link key={href} href={href} onClick={() => setOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 font-semibold border-2 transition-all ${active ? "bg-accent text-white border-app hard-shadow-sm" : "border-transparent hover:border-app hover:bg-surface2"}`}>
                  <Icon size={18}/>{label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-8 panel-flat p-3">
            <p className="mono-strip text-accent mb-1">Honest AI</p>
            <p className="text-xs text-muted2">Static findings are tool-confirmed. LLM findings are hypotheses — always verify before merging.</p>
          </div>
        </aside>
        <main className="flex-1 min-w-0 p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
}

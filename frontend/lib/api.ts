export type Finding = { id:string; title:string; description:string; category:string; severity:string; confidence:string;
  file_path:string; start_line:number|null; end_line:number|null; evidence:string; explanation:string; remediation:string;
  suggested_patch:string; suggested_tests:string[]; source:string; verification_status:string; rule_id:string };
export type Review = { id:string; title:string; source_type:string; language:string; status:string; source_label:string;
  github_url:string; pr_number:number|null; head_sha:string; summary:any; warnings:string[]; created_at:string; finding_counts:Record<string,number> };
export type ReviewDetail = Review & { findings:Finding[]; files:{path:string;content:string}[] };

function csrf(): string {
  if (typeof document === "undefined") return "";
  const m = document.cookie.match(/(?:^|; )bugforge_csrf=([^;]*)/);
  return m ? decodeURIComponent(m[1]) : "";
}

export async function api<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const method = (opts.method || "GET").toUpperCase();
  const headers: Record<string,string> = { "Content-Type": "application/json", ...(opts.headers as any) };
  if (["POST","PATCH","PUT","DELETE"].includes(method)) { const t = csrf(); if (t) headers["x-csrf-token"] = t; }
  const res = await fetch(path, { ...opts, headers, credentials: "include" });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { const j = await res.json(); msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || j); } catch {}
    throw new Error(msg);
  }
  return res.json();
}
export const fmtDate = (s:string) => { try { return new Date(s).toLocaleString(); } catch { return s; } };
export const SEV_ORDER: Record<string,number> = { critical:4, high:3, medium:2, low:1, info:0 };

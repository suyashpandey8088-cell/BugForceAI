"""GitHub REST client — read-only. Token stays server-side; never logged."""
import httpx

BASE = "https://api.github.com"

def _headers(token: str):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}

async def _get(token, url, params=None):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, headers=_headers(token), params=params)
        if r.status_code == 401: raise PermissionError("GitHub authorization revoked or expired — reconnect GitHub.")
        if r.status_code == 403 and r.headers.get("x-ratelimit-remaining") == "0":
            raise RuntimeError("GitHub API rate limit reached. Try again later.")
        if r.status_code == 404: raise LookupError("Repository or pull request not found, or you lack access.")
        if r.status_code >= 400: raise RuntimeError(f"GitHub API error (HTTP {r.status_code})")
        return r

async def list_repos(token: str, page: int = 1):
    r = await _get(token, f"{BASE}/user/repos", {"per_page": 50, "page": page, "sort": "updated", "affiliation": "owner,collaborator"})
    return [{"full_name": x["full_name"], "name": x["name"], "owner": x["owner"]["login"],
             "private": x["private"], "default_branch": x["default_branch"],
             "updated_at": x["updated_at"], "html_url": x["html_url"], "description": x.get("description") or ""} for x in r.json()]

async def list_pulls(token: str, owner: str, repo: str, page: int = 1):
    r = await _get(token, f"{BASE}/repos/{owner}/{repo}/pulls", {"per_page": 30, "page": page, "state": "all"})
    return [{"number": x["number"], "title": x["title"], "state": x["state"], "author": x["user"]["login"],
             "base": x["base"]["ref"], "head": x["head"]["ref"], "head_sha": x["head"]["sha"],
             "html_url": x["html_url"], "created_at": x["created_at"], "updated_at": x["updated_at"]} for x in r.json()]

async def get_pr_with_files(token: str, owner: str, repo: str, number: int):
    pr_r = await _get(token, f"{BASE}/repos/{owner}/{repo}/pulls/{number}")
    pr = pr_r.json()
    files_r = await _get(token, f"{BASE}/repos/{owner}/{repo}/pulls/{number}/files", {"per_page": 100})
    files = []
    for f in files_r.json():
        content = ""
        # Fetch raw file content at head sha for supported source files (read-only)
        if f["filename"].endswith(".py") and f.get("raw_url"):
            try:
                async with httpx.AsyncClient(timeout=30) as c:
                    cr = await c.get(f["raw_url"], headers=_headers(token))
                    if cr.status_code == 200 and len(cr.content) <= 100_000: content = cr.text
            except Exception: pass
        files.append({"path": f["filename"], "status": f["status"], "additions": f["additions"],
                      "deletions": f["deletions"], "patch": f.get("patch") or "", "content": content})
    return {"number": pr["number"], "title": pr["title"], "state": pr["state"],
            "author": pr["user"]["login"], "base": pr["base"]["ref"], "head": pr["head"]["ref"],
            "head_sha": pr["head"]["sha"], "html_url": pr["html_url"], "body": pr.get("body") or "", "files": files}

#!/usr/bin/env python3
"""hfapi - Higgsfield API helper (docs, validation, estimate, submit, wait, download).

Usage:
  hfapi.py docs-sync [--force]          download llms-full.txt into ~/works/data/higgsfield/docs/, build catalog.json
  hfapi.py models [QUERY]               list endpoint IDs (filter by substring)
  hfapi.py show ENDPOINT                print the endpoint's doc page
  hfapi.py check SHOT.md                validate a shot file's last ```json block against the schema
  hfapi.py estimate SHOT.md             expected API cost: POST /estimate if a key exists, else the
                                        price table in references/api-prices.json (snapshot)
  hfapi.py upload FILE                  upload local media, print public_url
  hfapi.py submit SHOT.md [-y]          check, estimate, confirm, submit; print request_id
  hfapi.py status REQUEST_ID            print current status JSON
  hfapi.py wait REQUEST_ID [--timeout S] [--no-download]
  hfapi.py run SHOT.md [-y]             submit + wait + download (the common case)
  hfapi.py draft SHOT.md [-y]           CREDITS lane: run the shot's "draft" block through the
                                        `higgsfield` CLI (web plan credits, NOT the API wallet)

Two wallets, two lanes. [API] commands (estimate/submit/run/wait/upload) spend the API console
wallet. [CREDITS] (draft) spends higgsfield.ai web plan credits via the official CLI.

Shot file: Markdown whose LAST ```json block is
  {"endpoint": "...", "params": {...},                  # API lane
   "draft": {"model": "<cli job_type>", "params": {}}}  # optional CREDITS lane (CLI param names)
Credentials: env HF_API_KEY_ID/HF_API_KEY_SECRET, else ~/.secrets/higgsfield-api.json
({"key_id": "...", "key_secret": "..."}). Outputs go to ~/works/data/higgsfield/<YYYY-MM-DD>/.
Request log (append-only): ~/works/data/higgsfield/requests.jsonl

Exit codes: 0 ok, 1 runtime failure (HTTP, failed/nsfw generation, validation), 2 usage error.

Examples:
  hfapi.py models kling-video/v3.0
  hfapi.py check prompts/opening.md && hfapi.py estimate prompts/opening.md
  hfapi.py run prompts/opening.md
"""
import datetime
import json
import mimetypes
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://api.higgsfield.ai"
DOCS_URL = "https://docs.higgsfield.ai/docs/llms-full.txt"
DATA_DIR = os.path.expanduser("~/works/data/higgsfield")
DOCS_DIR = os.path.join(DATA_DIR, "docs")
CATALOG = os.path.join(DOCS_DIR, "catalog.json")
PRICES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "api-prices.json")
SECRET_FILE = os.path.expanduser("~/.secrets/higgsfield-api.json")
TERMINAL = {"completed", "failed", "nsfw", "canceled"}
UA = "higgsfield-studio-hfapi/0.1"


class Usage(Exception):
    pass


def err(msg):
    print(msg, file=sys.stderr)


# ---------- credentials / http ----------

def auth_header():
    kid, sec = os.environ.get("HF_API_KEY_ID"), os.environ.get("HF_API_KEY_SECRET")
    if not (kid and sec) and os.path.exists(SECRET_FILE):
        with open(SECRET_FILE) as f:
            d = json.load(f)
        kid, sec = d.get("key_id"), d.get("key_secret")
    if not (kid and sec):
        raise RuntimeError(f"no credentials: set HF_API_KEY_ID/HF_API_KEY_SECRET or create {SECRET_FILE} (0600)")
    return f"Key {kid}:{sec}"


def http(method, url, body=None, auth=True, headers=None, raw=None, timeout=60):
    h = {"User-Agent": UA}
    if auth:
        h["Authorization"] = auth_header()
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode() if method != "GET" or "json" in r.headers.get("Content-Type", "") else r.read()
            return r.status, (json.loads(txt) if isinstance(txt, str) and txt.strip() else txt)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        cid = e.headers.get("X-Correlation-ID", "-")
        raise RuntimeError(f"HTTP {e.code} {method} {url}: {detail} (X-Correlation-ID {cid})")


def log_request(rec):
    os.makedirs(DATA_DIR, exist_ok=True)
    rec["ts"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    with open(os.path.join(DATA_DIR, "requests.jsonl"), "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------- docs / catalog ----------

def docs_sync(force=False):
    if os.path.exists(CATALOG) and not force:
        err(f"catalog exists: {CATALOG} (use --force to refresh)")
        return 0
    with urllib.request.urlopen(urllib.request.Request(DOCS_URL, headers={"User-Agent": UA}), timeout=60) as r:
        text = r.read().decode()
    lines = text.split("\n")
    pages, cur = [], None
    for i, ln in enumerate(lines):
        if ln.startswith("# ") and i + 1 < len(lines) and lines[i + 1].startswith("Source: "):
            if cur:
                pages.append(cur)
            cur = {"src": lines[i + 1][8:].strip(), "body": []}
        if cur:
            cur["body"].append(ln)
    if cur:
        pages.append(cur)
    os.makedirs(DOCS_DIR, exist_ok=True)
    catalog = {}
    for p in pages:
        slug = p["src"].split("/docs/", 1)[-1].replace("/", "__") or "index"
        body = "\n".join(p["body"])
        with open(os.path.join(DOCS_DIR, slug + ".md"), "w") as f:
            f.write(body)
        m = re.search(r"\*\*Endpoint ID:\*\* `([^`]+)`", body)
        if not m:
            continue
        sch = re.search(r'Complete JSON schema">\s*```json[^\n]*\n(.*?)\n\s*```', body, re.S)
        lim = re.search(r"within ([\d,]+) characters", body)
        catalog[m.group(1)] = {
            "title": p["body"][0][2:].removesuffix(" API"),
            "doc": f"{slug}.md",
            "schema": json.loads(sch.group(1)) if sch else None,
            "prompt_limit": int(lim.group(1).replace(",", "")) if lim else None,
        }
    with open(CATALOG, "w") as f:
        json.dump(catalog, f, indent=1, ensure_ascii=False)
    print(f"{len(pages)} pages, {len(catalog)} endpoints -> {CATALOG}")
    return 0


def load_catalog():
    if not os.path.exists(CATALOG):
        raise RuntimeError("no catalog: run `hfapi.py docs-sync` first")
    with open(CATALOG) as f:
        return json.load(f)


def endpoint_entry(ep):
    cat = load_catalog()
    if ep not in cat:
        near = [k for k in cat if ep.split("/")[0] in k][:8]
        raise RuntimeError(f"unknown endpoint {ep!r}" + (f"; similar: {', '.join(near)}" if near else ""))
    return cat[ep]


# ---------- shot files ----------

def read_shot_block(path):
    with open(path) as f:
        blocks = re.findall(r"```json\s*\n(.*?)\n```", f.read(), re.S)
    if not blocks:
        raise RuntimeError(f"{path}: no ```json block")
    return json.loads(blocks[-1])


def read_shot(path):
    shot = read_shot_block(path)
    if "endpoint" not in shot or "params" not in shot:
        raise RuntimeError(f"{path}: last json block needs \"endpoint\" and \"params\"")
    return shot["endpoint"], shot["params"]


def validate(ep, params):
    e = endpoint_entry(ep)
    sch, problems = e["schema"] or {}, []
    props = sch.get("properties", {})
    for k in sch.get("required", []):
        if k not in params:
            problems.append(f"missing required: {k}")
        elif params[k] in ("", None):
            problems.append(f"empty required: {k}")
    for k, v in params.items():
        if k not in props:
            problems.append(f"unknown field: {k} (allowed: {', '.join(props)})")
            continue
        p = props[k]
        if "enum" in p and v not in p["enum"]:
            problems.append(f"{k}={v!r} not in {p['enum']}")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if "minimum" in p and v < p["minimum"]:
                problems.append(f"{k}={v} < minimum {p['minimum']}")
            if "maximum" in p and v > p["maximum"]:
                problems.append(f"{k}={v} > maximum {p['maximum']}")
        if isinstance(v, str) and "maxLength" in p and len(v) > p["maxLength"]:
            problems.append(f"{k} length {len(v)} > maxLength {p['maxLength']}")
    prompt = params.get("prompt")
    if isinstance(prompt, str) and e.get("prompt_limit") and len(prompt) > e["prompt_limit"]:
        problems.append(f"prompt length {len(prompt)} > documented limit {e['prompt_limit']} (truncated)")
    return problems


def cmd_check(path):
    ep, params = read_shot(path)
    problems = validate(ep, params)
    for p in problems:
        err(f"{path}: {p}")
    if problems:
        return 1
    n = len(params.get("prompt", "") or "")
    print(f"ok {ep} ({n} prompt chars)")
    return 0


def estimate(ep, params):
    _, res = http("POST", f"{BASE}/estimate/{ep}", params)
    return res


def est_text(est):
    """Some endpoints (e.g. Wan 3.0) answer /estimate with a pricing_description instead of usd."""
    if est.get("usd") is not None:
        return f"${est['usd']}"
    return est.get("pricing_description") or json.dumps(est, ensure_ascii=False)


def has_credentials():
    try:
        auth_header()
        return True
    except RuntimeError:
        return False


def api_cost_line(ep, params):
    """Expected API wallet cost: live POST /estimate if a key exists, else the local price table."""
    if has_credentials():
        try:
            return f"[API 예상] {est_text(estimate(ep, params))} (POST /estimate, 실시간)"
        except RuntimeError as e:
            err(f"estimate failed, falling back to price table: {e}")
    with open(PRICES) as f:
        table = json.load(f)
    hits = [p for p in table["prices"] if ep.startswith(p["prefix"])]
    if not hits:
        return f"[API 예상] 가격표에 {ep} 없음. API 키를 만든 뒤 estimate 로 확인"
    p = max(hits, key=lambda h: len(h["prefix"]))
    props = ((endpoint_entry(ep).get("schema") or {}).get("properties") or {})
    res = params.get("resolution", props.get("resolution", {}).get("default"))
    price = p.get("by_resolution", {}).get(res, p)
    on_sale = datetime.datetime.now().astimezone() < datetime.datetime.fromisoformat(table["sale_ends"])
    unit = p["unit"]
    if unit == "s":
        qty = params.get("duration", props.get("duration", {}).get("default")) or 5
        label = f"{qty}초"
    elif unit == "image":
        qty = params.get("num_images", 1)
        label = f"{qty}장"
    else:
        return (f"[API 예상, 가격표 {table['snapshot']}] 입력 영상 초당 ${price['sale' if on_sale else 'list']}"
                f" (입력 영상 길이 x 단가). {p.get('note', '')}").strip()
    now = price["sale" if on_sale else "list"] * qty
    tail = f", 할인 끝나면 ${price['list'] * qty:.3f}" if on_sale and price["list"] != price["sale"] else ""
    return (f"[API 예상, 가격표 {table['snapshot']} 기준] 약 ${now:.3f} ({label}{', ' + res if res else ''}{tail})."
            f" 키가 생기면 estimate 로 정확한 값 확인. {p.get('note', '')}").strip()


# ---------- generation ----------

def submit(path, yes):
    ep, params = read_shot(path)
    problems = validate(ep, params)
    if problems:
        for p in problems:
            err(f"{path}: {p}")
        raise RuntimeError("validation failed; not submitting")
    est = estimate(ep, params)
    err(f"[API wallet] estimate {ep}: {est_text(est)}")
    if not yes:
        if not sys.stdin.isatty():
            raise Usage("submitting spends the API wallet; confirm on a TTY or pass -y")
        if input("[API wallet] submit? [y/N] ").strip().lower() != "y":
            err("aborted")
            return None
    _, res = http("POST", f"{BASE}/{ep}", params)
    rid = res["request_id"]
    log_request({"event": "submit", "shot": os.path.abspath(path), "endpoint": ep,
                 "request_id": rid, "estimate_usd": est.get("usd"), "params": params})
    print(rid)
    return rid


def outputs(res):
    urls = [i["url"] for i in res.get("images", []) or []]
    for k in ("video", "audio"):
        if isinstance(res.get(k), dict) and res[k].get("url"):
            urls.append(res[k]["url"])
    return urls


def download(rid, urls):
    day = os.path.join(DATA_DIR, datetime.date.today().isoformat())
    os.makedirs(day, exist_ok=True)
    paths = []
    for i, u in enumerate(urls):
        ext = os.path.splitext(u.split("?")[0])[1] or ".bin"
        dst = os.path.join(day, f"{rid}{'' if len(urls) == 1 else f'-{i + 1}'}{ext}")
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=300) as r, open(dst, "wb") as f:
            f.write(r.read())
        paths.append(dst)
    return paths


def wait(rid, timeout=900, dl=True):
    delay, start = 2.0, time.time()
    while True:
        try:
            _, res = http("GET", f"{BASE}/requests/{rid}/status")
        except RuntimeError as e:
            if not re.search(r"HTTP 5\d\d", str(e)):
                raise
            err(f"retrying status: {e}")
            res = {"status": "retry"}
        st = res.get("status")
        if st in TERMINAL:
            break
        if time.time() - start > timeout:
            raise RuntimeError(f"timeout after {timeout}s (last status {st}); resume with `hfapi.py wait {rid}`")
        err(f"{rid}: {st}")
        time.sleep(delay + random.uniform(0, 0.5))
        delay = min(delay * 1.5, 10.0)
    rec = {"event": "done", "request_id": rid, "status": st, "urls": outputs(res)}
    if st != "completed":
        rec["error"] = res.get("error")
        log_request(rec)
        raise RuntimeError(f"{rid}: {st} {res.get('error') or ''} (not charged)")
    if dl:
        rec["files"] = download(rid, rec["urls"])
    log_request(rec)
    for p in rec.get("files") or rec["urls"]:
        print(p)
    return 0


def upload(path):
    ctype = mimetypes.guess_type(path)[0]
    if not ctype:
        raise Usage(f"cannot infer content type for {path}")
    _, up = http("POST", f"{BASE}/files/generate-upload-url", {"content_type": ctype})
    with open(path, "rb") as f:
        http("PUT", up["upload_url"], auth=False, headers=up.get("upload_headers", {}), raw=f.read(), timeout=300)
    log_request({"event": "upload", "file": os.path.abspath(path), "public_url": up["public_url"]})
    print(up["public_url"])
    return 0


# ---------- credits lane (official higgsfield CLI, web plan credits) ----------

def cli_args(model, params):
    args = [model]
    for k, v in params.items():
        args += [f"--{k}", v if isinstance(v, str) else json.dumps(v)]
    return args


def draft(path, yes, timeout):
    import subprocess
    shot = read_shot_block(path)
    d = shot.get("draft")
    if not d or "model" not in d:
        raise RuntimeError(f"{path}: no \"draft\": {{\"model\": ..., \"params\": ...}} in the last json block")
    base = cli_args(d["model"], d.get("params", {}))
    if "endpoint" in shot and "params" in shot:
        err(api_cost_line(shot["endpoint"], shot["params"]) + "  <- 같은 샷을 API 로 뽑을 때")
    cost = subprocess.run(["higgsfield", "generate", "cost", *base], capture_output=True, text=True)
    if cost.returncode:
        raise RuntimeError(f"higgsfield generate cost failed: {cost.stderr.strip() or cost.stdout.strip()}")
    err(f"[CREDITS web plan] cost {d['model']}: {cost.stdout.strip()}")
    if not yes:
        if not sys.stdin.isatty():
            raise Usage("draft spends web plan credits; confirm on a TTY or pass -y")
        if input("[CREDITS web plan] generate? [y/N] ").strip().lower() != "y":
            err("aborted")
            return 1
    run = subprocess.run(["higgsfield", "--json", "generate", "create", *base, "--wait",
                          "--wait-timeout", f"{timeout}s"], capture_output=True, text=True)
    out = run.stdout + run.stderr
    job = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", out)
    urls = []
    if job:
        got = subprocess.run(["higgsfield", "--json", "generate", "get", job.group(0)], capture_output=True, text=True)
        try:
            info = json.loads(got.stdout)
            urls = [info["result_url"]] if info.get("status") == "completed" and info.get("result_url") else []
        except (json.JSONDecodeError, KeyError):
            pass
    rid = f"draft-{job.group(0) if job else int(time.time())}"
    rec = {"event": "draft", "lane": "credits", "shot": os.path.abspath(path), "model": d["model"],
           "params": d.get("params", {}), "job": rid, "urls": urls}
    if run.returncode or not urls:
        rec["error"] = out.strip()[-500:]
        log_request(rec)
        raise RuntimeError(f"draft failed (exit {run.returncode}): {out.strip()[-500:]}")
    rec["files"] = download(rid, urls)
    log_request(rec)
    for p in rec["files"]:
        print(p)
    return 0


# ---------- cli ----------

def main(argv):
    args = [a for a in argv if a != "--"]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    cmd, rest = args[0], args[1:]
    yes = any(a in ("-y", "--yes") for a in rest)
    flags = {a for a in rest if a.startswith("-")}
    pos = [a for a in rest if not a.startswith("-")]
    known = {"-y", "--yes", "--force", "--no-download", "--timeout"}
    if flags - known:
        raise Usage(f"unknown option(s): {' '.join(sorted(flags - known))}")

    def need(n):
        if len(pos) < n:
            raise Usage(f"{cmd}: missing argument (see -h)")

    if cmd == "docs-sync":
        return docs_sync("--force" in flags)
    if cmd == "models":
        q = pos[0] if pos else ""
        for k, v in sorted(load_catalog().items()):
            if q.lower() in (k + v["title"]).lower():
                print(f"{k}\t{v['title']}")
        return 0
    if cmd == "show":
        need(1)
        with open(os.path.join(DOCS_DIR, endpoint_entry(pos[0])["doc"])) as f:
            print(f.read())
        return 0
    if cmd == "check":
        need(1)
        return cmd_check(pos[0])
    if cmd == "estimate":
        need(1)
        ep, params = read_shot(pos[0])
        print(api_cost_line(ep, params))
        return 0
    if cmd == "upload":
        need(1)
        return upload(pos[0])
    if cmd == "status":
        need(1)
        print(json.dumps(http("GET", f"{BASE}/requests/{pos[0]}/status")[1], indent=1))
        return 0
    if cmd in ("wait", "run", "submit", "draft"):
        need(1)
        timeout = 900
        if "--timeout" in flags:
            i = rest.index("--timeout")
            if i + 1 >= len(rest) or not rest[i + 1].isdigit():
                raise Usage("--timeout needs seconds")
            timeout = int(rest[i + 1])
        if cmd == "wait":
            return wait(pos[0], timeout, "--no-download" not in flags)
        if cmd == "draft":
            return draft(pos[0], yes, timeout)
        rid = submit(pos[0], yes)
        if rid is None:
            return 1
        return 0 if cmd == "submit" else wait(rid, timeout, "--no-download" not in flags)
    raise Usage(f"unknown command: {cmd} (see -h)")


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Usage as e:
        err(f"usage: {e}")
        sys.exit(2)
    except (RuntimeError, OSError, json.JSONDecodeError) as e:
        err(f"error: {e}")
        sys.exit(1)

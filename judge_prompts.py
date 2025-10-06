import os, json, pathlib, re
from datetime import datetime
import httpx, certifi
from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent
RUNS_DIR = ROOT / "runs"
PROMPT_TMPL = (ROOT / "agent_e_prompts" / "JUDGE_prompt_quality.txt").read_text(encoding="utf-8")
SCHEMA_PATH = ROOT / "final_schema.json"
BRD_PATH    = ROOT / "resources" / "brd_summary.md"
GUARD_PATH  = ROOT / "resources" / "guardrails.md"
RULES_PATH  = ROOT / "resources" / "architecture_rules.xml"

# NEW: generic Terraform templates (patterns agent outputs) and translated Python (code build agent)
TF_ROOT   = ROOT / "infra" / "patterns" / "templates"
PY_ROOT   = ROOT / "src"

load_dotenv()

# --- optional reads (gracefully skip if missing) ---
def safe_read(p: pathlib.Path, encoding="utf-8") -> str:
    try:
        return p.read_text(encoding=encoding)
    except Exception:
        return ""

SCHEMA = safe_read(SCHEMA_PATH)
BRD    = safe_read(BRD_PATH)
GUARD  = safe_read(GUARD_PATH)
RULES  = safe_read(RULES_PATH)

# --- gather code assets ---
def gather_files_text(root: pathlib.Path, globs: list[str], max_bytes: int | None = None) -> str:
    """
    Concatenate files matched by globs into a single string with file headers.
    If max_bytes is set, truncate the total aggregate to this size with a clear notice.
    """
    if not root.exists():
        return ""
    parts = []
    for pattern in globs:
        for f in sorted(root.rglob(pattern)):
            try:
                txt = f.read_text(encoding="utf-8")
            except Exception:
                continue
            parts.append(f"\n===== FILE: {f.relative_to(ROOT)} =====\n{txt}\n")
    blob = "".join(parts)
    if max_bytes is not None and len(blob.encode("utf-8")) > max_bytes:
        # truncate on a UTF-8 boundary
        truncated = blob.encode("utf-8")[:max_bytes]
        try:
            blob = truncated.decode("utf-8")
        except UnicodeDecodeError:
            blob = truncated.decode("utf-8", errors="ignore")
        blob += "\n\n===== NOTE =====\n[TRUNCATED to fit token/size budget]\n"
    return blob

# Tune these budgets as needed (roughly a couple thousand tokens each)
MAX_TF_BYTES = 350_000
MAX_PY_BYTES = 350_000

TF_TEMPLATES = gather_files_text(TF_ROOT, ["*.tf"], max_bytes=MAX_TF_BYTES)
PY_SOURCES   = gather_files_text(PY_ROOT, ["*.py"], max_bytes=MAX_PY_BYTES)

# pick latest run folder
latest = sorted((d for d in RUNS_DIR.iterdir() if d.is_dir()), reverse=True)[0]
xml_files = sorted([p for p in latest.glob("*.json")])

if not xml_files:
    raise SystemExit(f"No XML candidates found in {latest}")

# quick auto metrics (hint features for the judge)
REQ_TAGS = {"Context","Decisions","Patterns","NonFunctionals","Services","Constraints","CloudMapping","Risks"}
def auto_metrics(xml_text: str):
    m = {}
    # shallow tag presence
    def has(tag): return bool(re.search(fr"<{tag}\b", xml_text))
    present = [t for t in REQ_TAGS if has(t)]
    m["required_tags_present"] = len(present)
    m["missing_tags"] = sorted(list(REQ_TAGS - set(present)))

    # CloudMapping coverage
    cmap = {}
    for sec in ["Compute","Networking","Data","Messaging","Identity"]:
        cmap[sec] = bool(re.search(fr"<{sec}\b[^>]*>.*?</{sec}>", xml_text, flags=re.S|re.I))
    m["cloudmapping_coverage_count"] = sum(1 for v in cmap.values() if v)
    m["cloudmapping_sections"] = cmap

    # Numeric NFRs present?
    m["nfr_p95_ms_present"] = bool(re.search(r'p95_ms="?\d+', xml_text))
    m["nfr_rps_present"] = bool(re.search(r'Throughput[^>]*rps="?\d+', xml_text))
    m["availability_target_present"] = bool(re.search(r'Availability[^>]*target="?\d', xml_text))

    # Vendor specificity hint (helps IaC)
    vendor_terms = ["Lambda","API Gateway","S3","DynamoDB","Aurora","EKS","KMS",
                    "Cloud Run","GKE","Pub/Sub","Cloud SQL","Secret Manager",
                    "Azure Functions","AKS","Event Grid","Service Bus","Key Vault","Cosmos"]
    m["vendor_specific_hits"] = sum(1 for t in vendor_terms if re.search(fr"\b{re.escape(t)}\b", xml_text))
    m["bytes"] = len(xml_text)
    return m

# ------- build candidate blocks with size caps to avoid context overflow -------
MAX_XML_CHARS = int(os.environ.get("JUDGE_MAX_XML_CHARS", "20000"))  # 20k per candidate
blocks = []
for f in xml_files:
    xml = f.read_text(encoding="utf-8")
    if len(xml) > MAX_XML_CHARS:
        xml = xml[:MAX_XML_CHARS] + "\n<!-- TRUNCATED FOR JUDGE -->"
    stem = f.stem
    # simple auto metrics (same as you had)
    def auto_metrics(x: str):
        REQ_TAGS = {"Context","Decisions","Patterns","NonFunctionals","Services","Constraints","CloudMapping","Risks"}
        m = {}
        def has(tag): return bool(re.search(fr"<{tag}\b", x))
        present = [t for t in REQ_TAGS if has(t)]
        m["required_tags_present"] = len(present)
        m["missing_tags"] = sorted(list(REQ_TAGS - set(present)))
        sec_ok = {}
        for sec in ["Compute","Networking","Data","Messaging","Identity"]:
            sec_ok[sec] = bool(re.search(fr"<{sec}\b[^>]*>.*?</{sec}>", x, flags=re.S|re.I))
        m["cloudmapping_coverage_count"] = sum(1 for v in sec_ok.values())
        m["cloudmapping_sections"] = sec_ok
        m["nfr_p95_ms_present"] = bool(re.search(r'p95_ms="?\d+', x))
        m["nfr_rps_present"] = bool(re.search(r'Throughput[^>]*rps="?\d+', x))
        m["availability_target_present"] = bool(re.search(r'Availability[^>]*target="?\d', x))
        vendor_terms = ["Lambda","API Gateway","S3","DynamoDB","Aurora","EKS","KMS",
                        "Cloud Run","GKE","Pub/Sub","Cloud SQL","Secret Manager",
                        "Azure Functions","AKS","Event Grid","Service Bus","Key Vault","Cosmos"]
        m["vendor_specific_hits"] = sum(1 for t in vendor_terms if re.search(fr"\b{re.escape(t)}\b", x))
        m["bytes"] = len(x)
        return m

    auto = json.dumps(auto_metrics(xml), ensure_ascii=False)
    blocks.append(f"---BEGIN---\nprompt: {stem}\nauto_metrics_json: {auto}\nxml:\n{xml}\n---END---")

filled = (
    PROMPT_TMPL
         .replace("{RULES_TEXT}", RULES or "")
         .replace("{SCHEMA}", SCHEMA or "")
         .replace("{GUARDRAILS_TEXT}", GUARD or "")
         .replace("{BRD_TEXT}", BRD or "")
         .replace("{TF_TEMPLATES}", TF_TEMPLATES or "")
         .replace("{PY_SOURCES}", PY_SOURCES or "")
    + "\n" + "\n".join(blocks)
)

# ------- call Claude with sane TLS and a deterministic judge model -------
client = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    http_client=httpx.Client(timeout=60, verify=certifi.where()),
)
JUDGE_MODEL = os.environ.get("ANTHROPIC_JUDGE_MODEL", "claude-sonnet-4-5-20250929")

resp = client.messages.create(
    model=JUDGE_MODEL,
    max_tokens=5000,
    temperature=0,
    system="Return STRICT JSON only. No Markdown, no commentary.",
    messages=[{"role": "user", "content": [{"type": "text", "text": filled}]}],
)

# ------- robust text & JSON extraction -------
def extract_text(r):
    parts = []
    try:
        for b in getattr(r, "content", []) or []:
            if getattr(b, "type", "") == "text" and hasattr(b, "text"):
                parts.append(b.text)
    except Exception:
        pass
    return "".join(parts).strip()

raw_text = extract_text(resp)

# Save the raw response for debugging
latest = latest  # reuse your variable
(latest / "raw_judge_response.txt").write_text(raw_text or str(resp), encoding="utf-8")

def coerce_json(s: str):
    if not s:
        raise ValueError("Empty judge response (no text). Check raw_judge_response.txt")
    s = s.strip()
    # 1) direct parse
    try:
        return json.loads(s)
    except Exception:
        pass
    # 2) strip code fences if any
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, flags=re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 3) greedy JSON object extraction (first balanced-ish {...})
    m = re.search(r"\{.*\}", s, flags=re.S)
    if m:
        candidate = m.group(0)
        # attempt to trim trailing garbage after last closing brace
        # find the last closing brace index that yields valid JSON
        for i in range(len(candidate), 0, -1):
            try:
                return json.loads(candidate[:i])
            except Exception:
                continue
    raise ValueError("Judge did not return valid JSON. See raw_judge_response.txt")

result = coerce_json(raw_text)

# ------- write result and print ranking -------
out = latest / "judge_prompts.json"
out.write_text(json.dumps(result, indent=2), encoding="utf-8")

print("Best prompt:", result.get("winner"))
print("\nRanking:")
for r in result.get("ranking", []):
    print(f"- {r['prompt']}: {r['score']}  — {r['reasons']}")
print(f"\nSaved: {out}")
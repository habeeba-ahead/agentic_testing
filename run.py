import os, pathlib, time
from datetime import datetime
from anthropic import Anthropic
from validate_xml import validate_xml
import httpx
from dotenv import load_dotenv 
import json

OUTPUT_TYPES = {
    "A_BRD_creation": "json", 
    "B_schema_compiler": "xml",
    "C_critic_refine": "xml",
    "D_catalog_first": "xml", 
    "E_diff_to_target": "xml",
    "F_combined": "xml",
    "JUDGE_prompt_quality": "json"
}

# --- setup paths ---
ROOT = pathlib.Path(__file__).resolve().parent
PROMPTS = (ROOT / "prompts").glob("*.txt")
SCHEMA = (ROOT / "schema.xml").read_text(encoding="utf-8")

GUARD = (ROOT / "data" / "guardrails.md").read_text(encoding="utf-8")

# --- model config (edit inline) ---
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 7000
TEMPERATURE = 0
SYSTEM_PROMPT = "Output XML only. No prose."
load_dotenv()

# --- output dir ---
STAMP = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
OUT_DIR = ROOT / "runs" / STAMP
OUT_DIR.mkdir(parents=True, exist_ok=True)


with open(f"{OUT_DIR}/A_BRD_creation.json", 'w') as f:
    json.dump({}, f, indent=4)


# --- supply our own httpx client so Anthropic doesn't pass proxies ---
httpx_client = httpx.Client(timeout=200.0)  # keep it simple; no proxies arg

# --- client ---
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise SystemExit("Please set ANTHROPIC_API_KEY in your environment.")
client = Anthropic(api_key=api_key, http_client=httpx_client)

def fill_template(t: str) -> str:
    BRD = (OUT_DIR / "A_BRD_creation.json").read_text(encoding="utf-8")
    return t.replace("{SCHEMA}", SCHEMA)\
            .replace("{BRD_TEXT}", BRD)\
            .replace("{GUARDRAILS_TEXT}", GUARD)

print(f"Running prompts... outputs -> {OUT_DIR}\n")
print("prompt | valid_xml | bytes | secs | note | file")

for p in sorted(PROMPTS):
    name = p.stem
    user_text = fill_template(p.read_text(encoding="utf-8"))

    t0 = time.time()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=[{"role":"user","content":[{"type":"text","text":user_text}]}]
    )
    elapsed = round(time.time() - t0, 2)
    xml_text = msg.content[0].text if msg.content else ""

    xml_text = xml_text.replace("```json", "").replace("```","")

    out_file = OUT_DIR / f"{name}.{OUTPUT_TYPES[name]}"
    out_file.write_text(xml_text, encoding="utf-8")

    ok, note = validate_xml(xml_text)
    print(f"{name} | {ok} | {len(xml_text)} | {elapsed}s | {note} | {out_file.name}")
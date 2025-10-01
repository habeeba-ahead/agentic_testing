import xml.etree.ElementTree as ET

REQUIRED = [
    "Context","Decisions","Patterns","NonFunctionals",
    "Services","Constraints","CloudMapping","Risks"
]

def validate_xml(xml_text: str):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return False, f"ParseError: {e}"
    missing = [t for t in REQUIRED if root.find(f".//{t}") is None]
    if missing:
        return False, f"Missing sections: {', '.join(missing)}"
    return True, "OK"

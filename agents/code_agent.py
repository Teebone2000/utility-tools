#!/usr/bin/env python3
"""
code_agent.py — generates a tool HTML page from a spec dict.

Supports single and multi-input tools.
New template placeholders:
  {{INPUTS}}           — rendered input fields from the spec's "inputs" array
  {{CUSTOM_STYLES}}    — extra CSS for tool-specific styling
  {{CUSTOM_SCRIPT}}    — extra JS (e.g. dropdown converters)
  {{CUSTOM_HTML_BEFORE_SCRIPT}} — HTML placed just before </body> script
  {{EXAMPLES}}         — rendered example boxes
  {{FORMULA_JS}}       — JS expression/function that returns result (can read inputs via $(id))

Legacy single-input spec ({{INPUT_UNIT}}, {{OUTPUT_UNIT}}) still works:
  Uses "inputValue" as the single input ID.

Usage:
  python3 code_agent.py --spec '<json>'
  python3 code_agent.py --batch config/batch_specs.json
"""

import os, json, argparse
from pathlib import Path
from datetime import datetime

TEMPLATE_PATH = Path(__file__).parent.parent / "workspace" / "tool_template.html"
TOOLS_DIR = Path(__file__).parent.parent / "tools"
MANIFEST_PATH = Path(__file__).parent.parent / "config" / "tools_manifest.json"

REQUIRED_SINGLE = ["slug", "title", "input_unit", "output_unit", "formula_js", "seo_description", "how_it_works"]
REQUIRED_MULTI = ["slug", "title", "inputs", "formula_js", "seo_description", "how_it_works"]


def validate_spec(spec):
    has_inputs = "inputs" in spec
    if has_inputs:
        fields = REQUIRED_MULTI
    else:
        fields = REQUIRED_SINGLE
    for field in fields:
        if field not in spec or not spec[field]:
            raise ValueError(f"Missing required field: {field}")
    # Basic safety check on formula
    dangerous = ["eval(", "exec(", "import ", "document.write", "__"]
    for d in dangerous:
        if d in spec["formula_js"]:
            raise ValueError(f"Unsafe formula_js: contains '{d}'")


def render_inputs(spec):
    """Render HTML input fields. Handles both legacy single-input and multi-input specs."""
    inputs = spec.get("inputs")
    if not inputs:
        # Legacy: single input
        return f'''        <div class="input-group">
            <label for="inputValue">{spec.get("input_unit", "Value")}</label>
            <input type="number" id="inputValue" placeholder="0" autofocus>
        </div>'''

    html = []
    for i, inp in enumerate(inputs):
        inp_type = inp.get("type", "number")
        inp_id = inp.get("id", f"input{i}")
        inp_label = inp.get("label", f"Input {i+1}")
        inp_placeholder = inp.get("placeholder", "0")
        inp_extra = ""

        if inp_type == "select":
            opts = inp.get("options", [])
            opt_html = "".join(f'<option value="{o["value"]}">{o["label"]}</option>' for o in opts)
            inp_extra = f'<select id="{inp_id}">{opt_html}</select>'
        elif inp_type == "number":
            inp_extra = f'<input type="number" id="{inp_id}" placeholder="{inp_placeholder}"{" autofocus" if i == 0 else ""}>'
        elif inp_type == "text":
            inp_extra = f'<input type="text" id="{inp_id}" placeholder="{inp_placeholder}"{" autofocus" if i == 0 else ""}>'
        else:
            inp_extra = f'<input type="{inp_type}" id="{inp_id}" placeholder="{inp_placeholder}">'

        html.append(
            f'        <div class="input-group">\n'
            f'            <label for="{inp_id}">{inp_label}</label>\n'
            f'            {inp_extra}\n'
            f'        </div>'
        )
    return "\n".join(html)


def render_examples(spec):
    """Render example boxes if spec has examples."""
    examples = spec.get("examples", [])
    if not examples:
        return ""
    lines = ["", '        <div class="examples">', "            <strong>Examples:</strong>"]
    for ex in examples:
        lines.append(f'            {ex}')
    lines.append("        </div>")
    return "\n".join(lines)


def generate_html(spec):
    template = TEMPLATE_PATH.read_text()
    slug = spec["slug"]

    replacements = {
        "{{TITLE}}": spec["title"],
        "{{SLUG}}": slug,
        "{{SEO_DESCRIPTION}}": spec["seo_description"],
        "{{INPUT_UNIT}}": spec.get("input_unit", "Value"),
        "{{OUTPUT_UNIT}}": spec.get("output_unit", ""),
        "{{FORMULA_JS}}": spec["formula_js"],
        "{{HOW_IT_WORKS}}": spec["how_it_works"],
        "{{INPUTS}}": render_inputs(spec),
        "{{EXAMPLES}}": render_examples(spec),
        "{{CUSTOM_STYLES}}": spec.get("custom_styles", ""),
        "{{CUSTOM_SCRIPT}}": spec.get("custom_script", ""),
        "{{CUSTOM_HTML_BEFORE_SCRIPT}}": spec.get("custom_html", ""),
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html


def save_tool(spec, html):
    TOOLS_DIR.mkdir(exist_ok=True)
    out_path = TOOLS_DIR / f"{spec['slug']}.html"
    out_path.write_text(html)
    print(f"  ✅ Written: {out_path}")
    return str(out_path)


def update_manifest(spec, file_path):
    manifest = json.loads(MANIFEST_PATH.read_text())
    # Remove existing entry for this slug if any
    manifest["tools"] = [t for t in manifest["tools"] if t["slug"] != spec["slug"]]
    manifest["tools"].append({
        "slug": spec["slug"],
        "title": spec["title"],
        "status": "generated",
        "file_path": file_path,
        "generated_at": datetime.now().isoformat(),
        "deployed_url": ""
    })
    manifest["last_updated"] = datetime.now().isoformat()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def process_spec(spec):
    print(f"\nProcessing: {spec.get('slug', 'unknown')}")
    validate_spec(spec)
    html = generate_html(spec)
    file_path = save_tool(spec, html)
    update_manifest(spec, file_path)
    return file_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", help="JSON string of a single tool spec")
    parser.add_argument("--batch", help="Path to JSON file with array of specs")
    args = parser.parse_args()

    if args.spec:
        spec = json.loads(args.spec)
        process_spec(spec)
    elif args.batch:
        specs = json.loads(Path(args.batch).read_text())
        for spec in specs:
            try:
                process_spec(spec)
            except Exception as e:
                print(f"  ❌ Failed {spec.get('slug')}: {e}")
    else:
        print("Usage: --spec '<json>' or --batch <file>")


if __name__ == "__main__":
    main()

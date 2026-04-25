# Utility Sites

Autonomous system for creating, deploying, and monetising single-purpose utility websites.

**Stack:** Python, Cloudflare Pages (free tier), Google Sheets (future), Groq/Llama 3 (future)

## Project Structure

```
utility-sites/
├── agents/
│   ├── code_agent.py       — generates HTML from spec
│   ├── deploy_agent.py     — pushes to Cloudflare Pages (future)
│   └── monitor_agent.py    — checks deployment health (future)
├── workspace/
│   ├── tool_template.html   — base HTML template
│   └── seo_guidelines.txt   — prompt guidelines for LLM (future)
├── tools/                   — generated HTML files
├── config/
│   └── tools_manifest.json  — tracks all tools + status
├── requirements.txt
└── README.md
```

## Usage

### Generate a single tool:
```bash
python3 agents/code_agent.py --spec '{"slug":"px-to-rem","title":"PX to REM Converter",...}'
```

### Generate all tools from batch:
```bash
python3 agents/code_agent.py --batch config/batch_specs.json
```

### Deployment
Requires Cloudflare Pages project + GitHub Actions. See Phase 2 in the full task spec.

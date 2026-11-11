# Copyright (c) 2026 SDLC Harness Contributors
# Licensed under MIT
"""Generate the hands-on guide's step images (.design/images/guide/).

Stylized cards in the same visual language as generate_terminal_images.py —
VS Code explorer trees, chat responses, terminal output, editor code, a
browser mock, and summary tables. The content mirrors what the current
harness produces at each SDLC phase; regenerate after any guide edit that
changes a step's expected output.
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / ".design" / "images" / "guide"

_FONT_DIRS = [
    Path(os.environ["SDLC_JBMONO_DIR"]) if os.environ.get("SDLC_JBMONO_DIR") else None,
    Path("/tmp/jbmono/fonts/ttf"),
    Path.home() / ".local" / "share" / "fonts",
]


def _font_path(filename):
    for base in _FONT_DIRS:
        if base is not None and (base / filename).is_file():
            return str(base / filename)
    raise FileNotFoundError(
        f"{filename} not found; set SDLC_JBMONO_DIR to the directory "
        "containing the JetBrains Mono TTFs."
    )


FONT_PATH = _font_path("JetBrainsMono-Regular.ttf")
FONT_BOLD_PATH = _font_path("JetBrainsMono-Bold.ttf")

# Catppuccin Mocha palette (matches generate_terminal_images.py)
BG = (30, 30, 46)
TITLEBAR = (49, 50, 68)
TEXT = (205, 214, 244)
DIM = (108, 112, 134)
GREEN = (166, 227, 161)
YELLOW = (249, 226, 175)
BLUE = (137, 180, 250)
RED = (243, 139, 168)
MAUVE = (203, 166, 247)
TEAL = (148, 226, 213)
SURFACE = (69, 71, 90)

BTN_CLOSE = (255, 95, 86)
BTN_MIN = (255, 189, 46)
BTN_MAX = (39, 201, 63)

SCALE = 2
FONT_SIZE = 14 * SCALE
LINE_HEIGHT = 22 * SCALE
PADDING = 20 * SCALE
TITLEBAR_H = 38 * SCALE
CORNER_R = 12 * SCALE
BTN_R = 7 * SCALE


def _fonts():
    regular = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    bold = ImageFont.truetype(FONT_BOLD_PATH, FONT_SIZE)
    title = ImageFont.truetype(FONT_BOLD_PATH, 13 * SCALE)
    return regular, bold, title


def window(width, n_lines, title_text):
    """Create a macOS-style window and return (img, draw, fonts, y0)."""
    height = TITLEBAR_H + PADDING + n_lines * LINE_HEIGHT + PADDING
    w = width * SCALE
    img = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    regular, bold, title_font = _fonts()
    draw.rounded_rectangle([(0, 0), (w - 1, height - 1)], CORNER_R, fill=BG)
    draw.rounded_rectangle([(0, 0), (w - 1, TITLEBAR_H)], CORNER_R, fill=TITLEBAR)
    draw.rectangle([(0, TITLEBAR_H - CORNER_R), (w - 1, TITLEBAR_H)], fill=TITLEBAR)
    btn_y = TITLEBAR_H // 2
    for i, color in enumerate((BTN_CLOSE, BTN_MIN, BTN_MAX)):
        x = PADDING + i * 24 * SCALE
        draw.ellipse([(x, btn_y - BTN_R), (x + BTN_R * 2, btn_y + BTN_R)], fill=color)
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    draw.text(
        ((w - (bbox[2] - bbox[0])) // 2, btn_y - 8 * SCALE),
        title_text,
        fill=DIM,
        font=title_font,
    )
    return img, draw, (regular, bold), TITLEBAR_H + PADDING


def line(draw, fonts, y, segments, x=PADDING):
    """Draw one line of (text, color) segments; bold for accent colors."""
    regular, bold = fonts
    for text, color in segments:
        font = bold if color in (GREEN, YELLOW, BLUE, MAUVE, TEAL) else regular
        draw.text((x, y), text, fill=color, font=font)
        x = draw.textbbox((x, y), text, font=font)[2]
    return y + LINE_HEIGHT


def render(width, title_text, lines, out_name):
    """lines: list of segment-lists (or "" for blank)."""
    img, draw, fonts, y = window(width, len(lines), title_text)
    for ln in lines:
        if ln == "---":
            ly = y + LINE_HEIGHT // 2
            draw.line(
                [(PADDING, ly), (width * SCALE - PADDING, ly)], fill=SURFACE, width=SCALE
            )
            y += LINE_HEIGHT
        elif ln == "":
            y += LINE_HEIGHT
        else:
            y = line(draw, fonts, y, ln)
    img.save(OUTPUT_DIR / out_name, "PNG")
    print(f"  ✓ {out_name}")


def tree_lines(entries):
    """entries: (depth, label, color, note) → segment lines for an explorer tree."""
    out = []
    for depth, label, color, note in entries:
        prefix = "  " * depth
        segs = [(f"{prefix}{label}", color)]
        if note:
            segs.append((f"   {note}", DIM))
        out.append(segs)
    return out


# ---------------------------------------------------------------- images

def gen_01():
    entries = [
        (0, "▾ document-manager", YELLOW, ""),
        (1, "▾ .github", TEXT, ""),
        (2, "copilot-instructions.md", TEXT, ""),
        (2, "reference-catalog.md", TEXT, ""),
        (2, "▾ instructions", TEXT, "14 quality files"),
        (2, "▾ prompts", TEXT, "6 prompt files"),
        (2, "▾ workflows", TEXT, ""),
        (1, "▾ .vscode", TEXT, ""),
        (2, "mcp.json", TEAL, "7 MCP servers"),
        (1, "▾ .SDLC", TEXT, ""),
        (2, "project-manifest.md", TEXT, ""),
        (1, "▸ src", TEXT, ""),
        (1, "▸ docs", TEXT, ""),
        (1, "README.md", TEXT, ""),
    ]
    render(620, "VS Code — Explorer", tree_lines(entries), "01-repo-structure.png")


def gen_02():
    lines = [
        [("Analyst", MAUVE), (" — design proposal (Phase 1–2)", DIM)],
        "",
        [("  Requirements clarified: upload / browse / download / delete,", TEXT)],
        [("  per-user scoping, 50 MB limit, Entra ID auth.", TEXT)],
        "",
        [("  Recommended design", YELLOW)],
        [("  • API      FastAPI (python/api template) → Container Apps", TEXT)],
        [("  • Agent    Python service, Azure AI Foundry, MCP tools", TEXT)],
        [("  • Web      Next.js (typescript/web template)", TEXT)],
        [("  • Data     Cosmos DB (metadata) + Blob Storage (files)", TEXT)],
        [("  • Infra    Bicep + AVM, deployed with azd", TEXT)],
        "",
        [("  ✓ ", GREEN), ("docs/adr/ADR-001-document-manager-design.md", GREEN)],
        [("  ✓ ", GREEN), ("Exit criteria Phase 1–2 met — grade: Large", GREEN)],
    ]
    render(620, "Copilot Chat — Harness › Analyst", lines, "02-requirement-design.png")


def gen_03():
    entries = [
        (0, "▾ document-manager", YELLOW, ""),
        (1, "▾ src", TEXT, ""),
        (2, "▾ api", TEXT, "FastAPI"),
        (3, "app/  tests/  Dockerfile  pyproject.toml", DIM, ""),
        (2, "▾ agent", TEXT, "AI agent service"),
        (3, "src/  tests/  Dockerfile  pyproject.toml", DIM, ""),
        (2, "▾ web", TEXT, "Next.js"),
        (3, "src/  package.json  Dockerfile", DIM, ""),
        (1, "▾ infra", TEXT, "Bicep + AVM"),
        (2, "main.bicep  modules/", DIM, ""),
        (1, "▾ .github/workflows", TEXT, ""),
        (2, "ci.yml  deploy.yml", DIM, ""),
        (1, "azure.yaml", TEXT, ""),
        (1, ".SDLC/project-manifest.md", TEAL, "templates recorded"),
    ]
    render(620, "VS Code — Explorer (scaffolded)", tree_lines(entries), "03-scaffolded-structure.png")


def gen_04():
    lines = [
        [("❯ ", BLUE), ("azd up", TEXT)],
        "",
        [("  Packaging services (api, agent, web)...", DIM)],
        [("  ✓ ", GREEN), ("Provisioned rg-document-manager (East US)", GREEN)],
        [("  ✓ ", GREEN), ("Cosmos DB account + Blob Storage", GREEN)],
        [("  ✓ ", GREEN), ("Container Apps environment (shared)", GREEN)],
        [("  ✓ ", GREEN), ("Azure AI Foundry + model deployment", GREEN)],
        [("  ✓ ", GREEN), ("Key Vault + Log Analytics", GREEN)],
        [("  ✓ ", GREEN), ("Deployed api    → https://api.<env>.azurecontainerapps.io", GREEN)],
        [("  ✓ ", GREEN), ("Deployed agent  → https://agent.<env>.azurecontainerapps.io", GREEN)],
        [("  ✓ ", GREEN), ("Deployed web    → https://web.<env>.azurecontainerapps.io", GREEN)],
        "",
        [("  SUCCESS: ", YELLOW), ("Your application was provisioned and deployed in 6m 12s.", TEXT)],
    ]
    render(620, "Terminal — azd up", lines, "04-azd-up-output.png")


def gen_05():
    """Resource-group card with fixed columns (custom layout)."""
    rows = [
        ("Cosmos DB account", "Azure Cosmos DB"),
        ("Storage account", "Storage"),
        ("Container App — api", "Container Apps"),
        ("Container App — agent", "Container Apps"),
        ("Container App — web", "Container Apps"),
        ("Container Apps environment", "Container Apps"),
        ("Container registry", "Container Registry"),
        ("AI Foundry project", "Azure AI Foundry"),
        ("Key Vault", "Key Vault"),
        ("Log Analytics workspace", "Log Analytics"),
    ]
    width = 620
    img, draw, fonts, y = window(width, len(rows) + 2, "Azure Portal — Resource group")
    regular, bold = fonts
    w = width * SCALE
    line(draw, fonts, y, [("Resource group", DIM), ("  rg-document-manager", YELLOW), ("   East US", DIM)])
    y += LINE_HEIGHT
    ly = y + LINE_HEIGHT // 2
    draw.line([(PADDING, ly), (w - PADDING, ly)], fill=SURFACE, width=SCALE)
    y += LINE_HEIGHT
    for name, rtype in rows:
        draw.text((PADDING + 8 * SCALE, y), name, fill=TEXT, font=regular)
        draw.text((PADDING + 300 * SCALE, y), rtype, fill=DIM, font=regular)
        y += LINE_HEIGHT
    img.save(OUTPUT_DIR / "05-azure-resources.png", "PNG")
    print("  ✓ 05-azure-resources.png")


def gen_06():
    lines = [
        [("document_service.py", DIM)],
        "---",
        [("class ", MAUVE), ("DocumentService", YELLOW), (":", TEXT)],
        [("    async def ", BLUE), ("upload_async", TEAL), ("(self, document, file_content):", TEXT)],
        [("        \"\"\"Upload file to Blob Storage, save metadata", DIM)],
        [("        to Cosmos DB.\"\"\"", DIM)],
        [("        async with ", TEXT), ("self._blob_helper as ", TEXT), ("helper:", TEXT)],
        [("            await ", TEXT), ("helper.upload_blob(", TEXT)],
        [("                \"documents\", document.blob_path, file_content)", TEXT)],
        [("        async with ", TEXT), ("self._repository:", TEXT)],
        [("            await ", TEXT), ("self._repository.add_async(document)", TEXT)],
        [("        return ", MAUVE), ("document", TEXT)],
    ]
    render(620, "Editor — document_service.py", lines, "06-implementation.png")


def gen_07():
    lines = [
        [("❯ ", BLUE), ("uv run pytest tests/ -v --cov=app", TEXT)],
        "",
        [("  collected 24 items", DIM)],
        "",
        [("  tests/unit/test_document_service.py ", TEXT), ("........", GREEN), (" [ 33%]", DIM)],
        [("  tests/unit/test_document_repository.py ", TEXT), ("......", GREEN), (" [ 58%]", DIM)],
        [("  tests/integration/test_documents_api.py ", TEXT), ("..........", GREEN), (" [100%]", DIM)],
        "",
        [("  ---------- coverage ----------", DIM)],
        [("  app/services/document_service.py     96%", TEXT)],
        [("  app/repositories/                      92%", TEXT)],
        [("  TOTAL                                  91%", TEXT)],
        "",
        [("  ", TEXT), ("24 passed", GREEN), (" in 3.41s", TEXT)],
    ]
    render(620, "Terminal — pytest", lines, "07-test-results.png")


def gen_08():
    """Browser mock of the Document Manager web app (custom layout)."""
    width, rows = 620, 12
    img, draw, fonts, y = window(width, rows, "Browser — Document Manager")
    regular, bold = fonts
    w = width * SCALE
    # Header bar
    draw.rounded_rectangle(
        [(PADDING, y), (w - PADDING, y + LINE_HEIGHT)], 6 * SCALE, fill=SURFACE
    )
    draw.text((PADDING + 10 * SCALE, y), "Document Manager", fill=YELLOW, font=bold)
    bx = w - PADDING - 150 * SCALE
    draw.rounded_rectangle(
        [(bx, y + 3 * SCALE), (w - PADDING - 10 * SCALE, y + LINE_HEIGHT - 3 * SCALE)],
        4 * SCALE,
        fill=BLUE,
    )
    draw.text((bx + 22 * SCALE, y), "Upload", fill=BG, font=bold)
    y += LINE_HEIGHT * 2
    # Search box (left column)
    draw.rounded_rectangle(
        [(PADDING, y), (PADDING + 300 * SCALE, y + LINE_HEIGHT - 4 * SCALE)],
        4 * SCALE,
        outline=DIM,
    )
    draw.text((PADDING + 8 * SCALE, y), "Search documents…", fill=DIM, font=regular)
    # Chat panel (right column): question + answer, drawn once.
    chat_x = PADDING + 330 * SCALE
    panel_top = y
    draw.rounded_rectangle(
        [(chat_x, panel_top), (w - PADDING, panel_top + LINE_HEIGHT * 6 + 6 * SCALE)],
        6 * SCALE,
        fill=SURFACE,
    )
    cy = panel_top + 6 * SCALE
    draw.text((chat_x + 10 * SCALE, cy), "Ask about a document", fill=MAUVE, font=bold)
    cy += LINE_HEIGHT
    draw.text((chat_x + 10 * SCALE, cy), "“Summarize the key", fill=TEXT, font=regular)
    cy += LINE_HEIGHT
    draw.text((chat_x + 10 * SCALE, cy), "obligations in §4.”", fill=TEXT, font=regular)
    cy += LINE_HEIGHT
    draw.text((chat_x + 10 * SCALE, cy), "§4 sets a 30-day notice", fill=TEAL, font=regular)
    cy += LINE_HEIGHT
    draw.text((chat_x + 10 * SCALE, cy), "period and caps liability", fill=TEAL, font=regular)
    cy += LINE_HEIGHT
    draw.text((chat_x + 10 * SCALE, cy), "at 12% of contract value.", fill=TEAL, font=regular)
    y += LINE_HEIGHT
    # Document rows (left column): name + size, then tags + actions.
    docs = [
        ("contract-2026.pdf", "contract · legal", "2.4 MB"),
        ("q3-report.docx", "report · finance", "812 KB"),
        ("architecture.png", "diagram · infra", "1.1 MB"),
        ("onboarding.pdf", "guide · hr", "640 KB"),
    ]
    for name, tags, size in docs:
        draw.text((PADDING + 8 * SCALE, y), name, fill=TEXT, font=regular)
        draw.text((PADDING + 240 * SCALE, y), size, fill=DIM, font=regular)
        y += LINE_HEIGHT
        draw.text((PADDING + 8 * SCALE, y), tags, fill=DIM, font=regular)
        draw.text((PADDING + 170 * SCALE, y), "Download", fill=BLUE, font=regular)
        draw.text((PADDING + 245 * SCALE, y), "Delete", fill=RED, font=regular)
        y += LINE_HEIGHT
    img.save(OUTPUT_DIR / "08-web-app.png", "PNG")
    print("  ✓ 08-web-app.png")


def gen_09():
    lines = [
        [("QA Coordinator", MAUVE), (" — Phase 6 panel, 9 reviewers in parallel", DIM)],
        "---",
        [("  Architecture                  ", TEXT), ("9/10", GREEN), ("  ✓ Pass", GREEN)],
        [("  Azure Compliance              ", TEXT), ("9/10", GREEN), ("  ✓ Pass", GREEN)],
        [("  Code Quality                  ", TEXT), ("8/10", GREEN), ("  ✓ Pass", GREEN)],
        [("  Security                      ", TEXT), ("9/10", GREEN), ("  ✓ Pass", GREEN), ("  (≥ 8 required)", DIM)],
        [("  Test Coverage                 ", TEXT), ("8/10", GREEN), ("  ✓ Pass", GREEN)],
        [("  Requirements Completeness     ", TEXT), ("10/10", GREEN), (" ✓ Pass", GREEN)],
        [("  UX & Accessibility            ", TEXT), ("8/10", GREEN), ("  ✓ Pass", GREEN)],
        [("  LLM Behavior                  ", TEXT), ("8/10", GREEN), ("  ✓ Pass", GREEN)],
        [("  Deployment Readiness          ", TEXT), ("9/10", GREEN), ("  ✓ Pass", GREEN)],
        "---",
        [("  Composite 8.7 — ", TEXT), ("Verdict: ✓ Approve", GREEN)],
    ]
    render(620, "Copilot Chat — QA Review Summary", lines, "09-quality-pass.png")


def gen_10():
    lines = [
        [("feat: Document Manager — full-stack implementation", YELLOW)],
        [("Dongbumlee", TEXT), (" wants to merge into ", DIM), ("main", TEXT)],
        "---",
        [("  ✓ ", GREEN), ("CI — build, lint, test (api, agent, web)", GREEN)],
        [("  ✓ ", GREEN), ("Security — gitleaks + dependency scan", GREEN)],
        [("  ✓ ", GREEN), ("SDLC exit criteria — Phases 1–9 complete", GREEN)],
        [("  ✓ ", GREEN), ("QA panel — composite 8.7, no critical findings", GREEN)],
        "",
        [("  ADR: ", DIM), ("docs/adr/ADR-001-document-manager-design.md", TEXT)],
        [("  Docs: ", DIM), ("README + docs/api/documents.md updated", TEXT)],
        "",
        [("  ", TEXT), ("Ready to merge", GREEN)],
    ]
    render(620, "GitHub — Pull Request", lines, "10-pull-request.png")


def gen_11():
    lines = [
        [("document_analyzer.py", DIM)],
        "---",
        [("class ", MAUVE), ("DocumentAnalyzerAgent", YELLOW), (":", TEXT)],
        [("    async def ", BLUE), ("analyze_async", TEAL), ("(self, document_id):", TEXT)],
        [("        # 1. Read content via the blob MCP tool", DIM)],
        [("        content = await ", TEXT), ("self._mcp.call_tool(", TEXT)],
        [("            \"blob_reader\", \"read_document\", document_id)", TEXT)],
        [("        # 2. Summarize + extract tags (AI Foundry)", DIM)],
        [("        summary = await ", TEXT), ("self._generate_summary(content)", TEXT)],
        [("        tags = await ", TEXT), ("self._extract_tags(content)", TEXT)],
        [("        # 3. Save the analysis with the metadata", DIM)],
        [("        return ", MAUVE), ("{\"summary\": summary, \"tags\": tags}", TEXT)],
    ]
    render(620, "Editor — document_analyzer.py", lines, "11-agent-implementation.png")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating hands-on guide images with JetBrains Mono...")
    gen_01()
    gen_02()
    gen_03()
    gen_04()
    gen_05()
    gen_06()
    gen_07()
    gen_08()
    gen_09()
    gen_10()
    gen_11()
    print("Done.")

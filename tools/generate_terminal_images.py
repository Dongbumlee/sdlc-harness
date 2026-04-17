# Copyright (c) 2026 SDLC Harness Contributors
# Licensed under MIT
"""Generate macOS-style terminal screenshot PNGs for README."""

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/tmp/jbmono/fonts/ttf/JetBrainsMono-Regular.ttf"
FONT_BOLD_PATH = "/tmp/jbmono/fonts/ttf/JetBrainsMono-Bold.ttf"
OUTPUT_DIR = "/home/donlee/works/sdlc-harness-dev/docs/assets"

# Catppuccin Mocha palette
BG = (30, 30, 46)
TITLEBAR = (49, 50, 68)
TEXT = (205, 214, 244)
DIM = (108, 112, 134)
GREEN = (166, 227, 161)
YELLOW = (249, 226, 175)
BLUE = (137, 180, 250)
RED = (243, 139, 168)
SURFACE = (69, 71, 90)

BTN_CLOSE = (255, 95, 86)
BTN_MIN = (255, 189, 46)
BTN_MAX = (39, 201, 63)

SCALE = 2  # Retina
FONT_SIZE = 14 * SCALE
LINE_HEIGHT = 22 * SCALE
PADDING = 20 * SCALE
TITLEBAR_H = 38 * SCALE
CORNER_R = 12 * SCALE
BTN_R = 7 * SCALE


def load_fonts():
    """Load JetBrains Mono fonts."""
    regular = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    bold = ImageFont.truetype(FONT_BOLD_PATH, FONT_SIZE)
    title = ImageFont.truetype(FONT_BOLD_PATH, 13 * SCALE)
    return regular, bold, title


def create_terminal(width, lines, title_text):
    """Create a terminal window image."""
    height = TITLEBAR_H + PADDING + len(lines) * LINE_HEIGHT + PADDING
    w = width * SCALE
    img = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    regular, bold, title_font = load_fonts()

    # Background with rounded corners
    draw.rounded_rectangle([(0, 0), (w - 1, height - 1)], CORNER_R, fill=BG)

    # Title bar
    draw.rounded_rectangle(
        [(0, 0), (w - 1, TITLEBAR_H)], CORNER_R, fill=TITLEBAR
    )
    draw.rectangle([(0, TITLEBAR_H - CORNER_R), (w - 1, TITLEBAR_H)], fill=TITLEBAR)

    # Traffic lights
    btn_y = TITLEBAR_H // 2
    draw.ellipse(
        [(PADDING, btn_y - BTN_R), (PADDING + BTN_R * 2, btn_y + BTN_R)],
        fill=BTN_CLOSE,
    )
    draw.ellipse(
        [
            (PADDING + 24 * SCALE, btn_y - BTN_R),
            (PADDING + 24 * SCALE + BTN_R * 2, btn_y + BTN_R),
        ],
        fill=BTN_MIN,
    )
    draw.ellipse(
        [
            (PADDING + 48 * SCALE, btn_y - BTN_R),
            (PADDING + 48 * SCALE + BTN_R * 2, btn_y + BTN_R),
        ],
        fill=BTN_MAX,
    )

    # Title text (centered)
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, btn_y - 8 * SCALE), title_text, fill=DIM, font=title_font)

    # Content lines
    y = TITLEBAR_H + PADDING
    for line in lines:
        x = PADDING
        if isinstance(line, str):
            draw.text((x, y), line, fill=TEXT, font=regular)
        elif isinstance(line, list):
            for segment in line:
                text, color = segment
                font = bold if color in (GREEN, YELLOW, BLUE) else regular
                draw.text((x, y), text, fill=color, font=font)
                bbox = draw.textbbox((x, y), text, font=font)
                x = bbox[2]
        elif line == "---":
            line_y = y + LINE_HEIGHT // 2
            draw.line([(PADDING, line_y), (w - PADDING, line_y)], fill=SURFACE, width=SCALE)
        y += LINE_HEIGHT

    return img


def generate_vscode():
    """Generate VS Code install screenshot."""
    lines = [
        [("❯ ", BLUE), ("Command Palette (Ctrl+Shift+P)", DIM)],
        "",
        [("  > ", TEXT), ("Chat: Install Plugin From Source", TEXT)],
        "",
        [("  Enter plugin source URL:", DIM)],
        [("  https://github.com/Dongbumlee/sdlc-harness", YELLOW)],
        "",
        [("  ✓ ", GREEN), ("Cloning repository...", GREEN)],
        [("  ✓ ", GREEN), ("Found plugin.json — 19 agents, 16 skills", GREEN)],
        [("  ✓ ", GREEN), ("Plugin \"sdlc-harness\" installed successfully", GREEN)],
    ]
    img = create_terminal(620, lines, "VS Code — Command Palette")
    img.save(f"{OUTPUT_DIR}/install-vscode.png", "PNG")
    print("  ✓ install-vscode.png")


def generate_cli():
    """Generate Copilot CLI install screenshot."""
    lines = [
        [("❯ ", BLUE), ("copilot plugin install Dongbumlee/sdlc-harness", TEXT)],
        "",
        [("  Cloning Dongbumlee/sdlc-harness...", DIM)],
        [("  Detecting plugin format...", DIM)],
        "",
        [("  ✓ ", GREEN), ("Found .github/plugin/plugin.json", GREEN)],
        [("  ✓ ", GREEN), ("Loaded 19 agents", GREEN)],
        [("  ✓ ", GREEN), ("Loaded 16 skills (13 core + 3 Azure Pack)", GREEN)],
        [("  ✓ ", GREEN), ("Loaded 7 MCP server configurations", GREEN)],
        "",
        [("  Plugin ", TEXT), ("sdlc-harness", YELLOW), (" installed successfully.", TEXT)],
        "",
        [("❯ ", BLUE), ("█", DIM)],
    ]
    img = create_terminal(620, lines, "Terminal — GitHub Copilot CLI")
    img.save(f"{OUTPUT_DIR}/install-copilot-cli.png", "PNG")
    print("  ✓ install-copilot-cli.png")


def generate_marketplace():
    """Generate Marketplace browse & install screenshot."""
    lines = [
        [("── ", DIM), ("Register marketplace (one-time)", DIM), (" ──", DIM)],
        [("❯ ", BLUE), ("copilot plugin marketplace add Dongbumlee/sdlc-harness", TEXT)],
        [("  ✓ ", GREEN), ("Marketplace \"sdlc-harness\" added", GREEN)],
        "",
        "---",
        "",
        [("── ", DIM), ("Browse available plugins", DIM), (" ──", DIM)],
        [("❯ ", BLUE), ("copilot plugin marketplace browse sdlc-harness", TEXT)],
        [("    sdlc-harness", YELLOW), ("  v1.0.0", DIM)],
        [("    19 agents · 16 skills · 7 MCP servers", DIM)],
        [("    Multi-agent SDLC orchestration with adversarial QA", DIM)],
        "",
        "---",
        "",
        [("── ", DIM), ("Install by name", DIM), (" ──", DIM)],
        [("❯ ", BLUE), ("copilot plugin install sdlc-harness@sdlc-harness", TEXT)],
        [("  ✓ ", GREEN), ("Plugin \"sdlc-harness\" installed successfully", GREEN)],
        "",
        [("❯ ", BLUE), ("█", DIM)],
    ]
    img = create_terminal(620, lines, "Terminal — Marketplace Browse & Install")
    img.save(f"{OUTPUT_DIR}/install-marketplace.png", "PNG")
    print("  ✓ install-marketplace.png")


if __name__ == "__main__":
    print("Generating terminal screenshots with JetBrains Mono...")
    generate_vscode()
    generate_cli()
    generate_marketplace()
    print("Done.")

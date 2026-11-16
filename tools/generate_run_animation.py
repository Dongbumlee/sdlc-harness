#!/usr/bin/env python3
"""Generate the README run animation (docs/assets/harness-run-{dark,light}.gif).

One run loops the phase ring: phases light in order, the QA panel scores
the work, a domain below the gate sends it back to Build, the fix goes
through a second Test round, and the re-check passes. Two themes —
Catppuccin Mocha (dark) and Latte (light) — selected in the README by the
reader's color scheme via a <picture> element.

Regenerate after changing the scene:  python3 tools/generate_run_animation.py
Requires Pillow and the JetBrains Mono TTFs (same fonts as
tools/generate_terminal_images.py; set SDLC_JBMONO_DIR to their folder).
"""
import math, os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1560, 940
_FONT_DIR = os.environ.get("SDLC_JBMONO_DIR", "")
JB = os.path.join(_FONT_DIR, "JetBrainsMono-Bold.ttf")
JR = os.path.join(_FONT_DIR, "JetBrainsMono-Regular.ttf")

def F(path, px):
    return ImageFont.truetype(path, px)

THEMES = {
    "dark": dict(  # Catppuccin Mocha
        BASE=(30, 30, 46), CARD=(24, 24, 37), SURFACE=(49, 50, 68), SURFACE2=(69, 71, 90),
        TEXT=(205, 214, 244), SUB=(166, 173, 200), DIM=(108, 112, 134),
        BLUE=(137, 180, 250), GREEN=(166, 227, 161), PEACH=(250, 179, 135), RED=(243, 139, 168),
        MAUVE=(203, 166, 247), YELLOW=(249, 226, 175), TEAL=(148, 226, 213),
        STEEL=(116, 152, 199), VEIL=(30, 30, 46)),
    "light": dict(  # Catppuccin Latte
        BASE=(239, 241, 245), CARD=(250, 250, 251), SURFACE=(204, 208, 218), SURFACE2=(172, 176, 190),
        TEXT=(76, 79, 105), SUB=(92, 95, 119), DIM=(140, 143, 161),
        BLUE=(30, 102, 245), GREEN=(64, 160, 43), PEACH=(254, 100, 11), RED=(210, 15, 57),
        MAUVE=(136, 57, 239), YELLOW=(223, 142, 29), TEAL=(23, 146, 153),
        STEEL=(122, 140, 186), VEIL=(239, 241, 245)),
}

def use_theme(name):
    for key, value in THEMES[name].items():
        globals()[key] = value

PHASES = [
    ("0", "Intake",   "Harness",        ["design conversation", "envelope + grade set"]),
    ("1", "Specify",  "Analyst",        ["discovery summary", "requirements approved"]),
    ("2", "Design",   "Architect",      ["architecture + ADR", "design gate passed"]),
    ("3", "Scaffold", "Scaffolder",     ["repo laid out", "manifest completed"]),
    ("4", "Build",    "Implementer",    ["code + tests written", "build green"]),
    ("5", "Test",     "Implementer",    ["suite executed", "failures triaged"]),
    ("6", "QA review","QA Coordinator", ["panel scores the work", "below the gate? back it goes"]),
    ("7", "Document", "Harness",        ["docs synced to code", "runbook written"]),
    ("8", "Deploy",   "Deployer",       ["target deployed", "health verified"]),
    ("9", "Close",    "Harness",        ["records sealed", "run retrospective"]),
]

START = {0: 6, 1: 12, 2: 18, 3: 24, 4: 30, 5: 36, 6: 42, 7: 94, 8: 100, 9: 106}
FIX_START, FIX_END = 70, 77
TEST2_START, TEST2_END = 78, 85
RECHECK = 86
PASS_AT = 92

CX, CY, RAD = 500, 430, 168

def node_pos(i):
    a = math.radians(-90 + i * 36)
    return (CX + RAD * math.cos(a), CY + RAD * math.sin(a))

def phase_at(f):
    if f < 6: return -1
    for i in range(10):
        s = START[i]
        e = START[i + 1] if i + 1 < 10 else 112
        if s <= f < e: return i
    return 9

def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def rr(d, box, r, **kw):
    d.rounded_rectangle(box, radius=r, **kw)

def bezier(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1])

def draw(f):
    img = Image.new("RGB", (W, H), BASE)
    d = ImageDraw.Draw(img, "RGBA")
    cur = phase_at(f)
    fixing = FIX_START <= f <= FIX_END
    testing2 = TEST2_START <= f <= TEST2_END
    stage_phase = 4 if fixing else (5 if testing2 else cur)
    eff_cur = stage_phase if (fixing or testing2) else cur
    cycle2 = f >= 60

    # header
    d.text((64, 46), "SDLC HARNESS", font=F(JB, 25), fill=TEXT)
    d.text((64, 82), "one run, looping the ring", font=F(JR, 19), fill=SUB)

    # ---------- ring panel ----------
    rr(d, [64, 150, 950, 700], 18, fill=CARD, outline=SURFACE2, width=2)
    # cycle chip
    chip = "CYCLE 2 · FIX LOOP" if 60 <= f < PASS_AT else ("CYCLE 2 · RE-CHECK PASSED" if f >= PASS_AT else "CYCLE 1 · FULL PASS")
    chip_col = RED if 60 <= f < PASS_AT else (GREEN if f >= PASS_AT else BLUE)
    cw = d.textlength(chip, font=F(JB, 15)) + 36
    rr(d, [950 - 28 - cw, 172, 950 - 28, 208], 18, outline=chip_col, width=2)
    d.text((950 - 28 - cw / 2, 190), chip, font=F(JB, 15), fill=chip_col, anchor="mm")
    d.text((92, 190), "THE RUN RING", font=F(JB, 15), fill=DIM, anchor="lm")

    # ring track + progress arc
    bbox = [CX - RAD, CY - RAD, CX + RAD, CY + RAD]
    d.ellipse(bbox, outline=SURFACE2, width=4)
    if cur >= 0:
        prog = 9 if f >= 112 else (6 if cur == 6 else cur)
        sweep = 36 * prog + (36 * 0.45 if f < 112 and cur != 6 else 0)
        if sweep > 4:
            d.arc(bbox, start=270, end=270 + sweep, fill=BLUE, width=5)
    # spokes
    for i in range(10):
        nx, ny = node_pos(i)
        col = (PEACH if i == 6 else BLUE) if i == eff_cur else SURFACE
        d.line([CX, CY, nx, ny], fill=col + (120,) if i == eff_cur else SURFACE + (70,), width=2)
    # send-back chord QA(6) -> Build(4)
    if 62 <= f <= FIX_END:
        p0 = node_pos(6)
        p2 = node_pos(4)
        p1 = (CX - 20, CY + 105)
        col = RED if f < RECHECK else GREEN
        prev = None
        for k in range(41):
            tt = k / 40
            pt = bezier(p0, p1, p2, tt)
            if prev is not None and k % 4 < 2:
                d.line([prev, pt], fill=col, width=3)
            prev = pt
        if 64 <= f <= 75:
            for j in range(3):
                tt = ((f - 64) / 11 + j * 0.16) % 1.0
                xx, yy = bezier(p0, p1, p2, tt)
                d.ellipse([xx - 7, yy - 7, xx + 7, yy + 7], fill=RED)
    # nodes
    for i, (num, name, *_r) in enumerate(PHASES):
        nx, ny = node_pos(i)
        active = (i == eff_cur and f < 112)
        finished = (i < cur) or f >= 112
        r = 23 if active else 18
        if i == 6 and 42 <= f < 94:
            fillc = PEACH
        elif active:
            fillc = BLUE
        elif finished:
            fillc = STEEL
        else:
            fillc = SURFACE
        pulse = (62 <= f <= FIX_END and i == 4) or (testing2 and i == 5)
        if pulse:
            pr = r + 9 + int(3 * math.sin(f * 1.4))
            d.ellipse([nx - pr, ny - pr, nx + pr, ny + pr], outline=BLUE if testing2 else RED, width=3)
        d.ellipse([nx - r, ny - r, nx + r, ny + r], fill=fillc)
        d.text((nx, ny + 1), "✓" if finished and not active else num, font=F(JB, 17),
               fill=BASE if (active or finished) else DIM, anchor="mm")
        # label outside the ring
        a = math.radians(-90 + i * 36)
        lx = CX + (RAD + 40) * math.cos(a)
        ly = CY + (RAD + 40) * math.sin(a)
        anch = "lm" if math.cos(a) > 0.3 else ("rm" if math.cos(a) < -0.3 else "mm")
        d.text((lx, ly), name, font=F(JB, 15) if active else F(JR, 15),
               fill=TEXT if active else (SUB if finished else DIM), anchor=anch)
    # hub
    rr(d, [CX - 86, CY - 44, CX + 86, CY + 44], 16, fill=SURFACE, outline=SURFACE2, width=2)
    d.text((CX, CY - 12), "HARNESS", font=F(JB, 21), fill=TEXT, anchor="mm")
    d.text((CX, CY + 18), "coordinator", font=F(JR, 14), fill=SUB, anchor="mm")

    if testing2:
        a4 = math.radians(-90 + 4 * 36)
        seg = [CX - RAD, CY - RAD, CX + RAD, CY + RAD]
        d.arc(seg, start=a4 * 180 / math.pi, end=a4 * 180 / math.pi + 36, fill=GREEN, width=6)
        tt = ((f - TEST2_START) / 7)
        hx = CX + RAD * math.cos(a4 + tt * math.radians(36))
        hy = CY + RAD * math.sin(a4 + tt * math.radians(36))
        d.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=GREEN)

    # ---------- stage card (right top) ----------
    rr(d, [986, 150, W - 64, 428], 18, fill=CARD, outline=SURFACE2, width=2)
    if stage_phase >= 0:
        if fixing:
            num, name, agent, lines = "4", "Build — round 2", "Implementer", \
                ["finding: unhandled error path", "fix applied → re-test"]
            ac = RED
            local = f - FIX_START
        elif testing2:
            num, name, agent, lines = "5", "Test — round 2", "Implementer", \
                ["suite re-executed", "all green → back to QA"]
            ac = BLUE
            local = f - TEST2_START
        else:
            num, name, agent, lines = PHASES[stage_phase]
            ac = PEACH if stage_phase == 6 else BLUE
            local = f - START[stage_phase]
        off = (1 - ease(local / 3)) * 20 if local < 3 else 0
        x0 = 1026 + off
        tag = f"PHASE {num}" + ("  ·  SENT BACK" if fixing else ("  ·  ROUND 2" if testing2 else ""))
        d.text((x0, 182), tag, font=F(JB, 17), fill=ac)
        d.text((x0, 210), name, font=F(JB, 42), fill=TEXT)
        d.text((x0, 272), f"Harness  →  {agent}", font=F(JR, 19), fill=SUB)
        d.line([x0, 306, W - 104, 306], fill=SURFACE, width=2)
        for j, ln in enumerate(lines):
            if local < 2 + j * 2: continue
            yy = 326 + j * 44
            d.ellipse([x0 + 2, yy + 7, x0 + 13, yy + 18], fill=ac)
            d.text((x0 + 27, yy), ln, font=F(JR, 20), fill=TEXT)
    else:
        d.text((1026, 210), "Waiting for a task…", font=F(JB, 32), fill=DIM)

    # ---------- QA card (right bottom) ----------
    rr(d, [986, 444, W - 64, 700], 18, fill=CARD, outline=SURFACE2, width=2)
    in_qa = 42 <= f < 94
    d.text((1026, 468), "QA PANEL", font=F(JB, 17), fill=PEACH if in_qa else SUB)
    if f >= 48:
        if f < RECHECK:
            t = ease((f - 47) / 12)
            vals = [9.0 * t, 6.4 * t, 8.8 * t]
        else:
            t = ease((f - (RECHECK - 1)) / 6)
            vals = [9.0, 6.4 + (8.1 - 6.4) * t, 8.8]
        for j, (label, val) in enumerate([("Security", vals[0]), ("Correctness", vals[1]), ("Tests", vals[2])]):
            yy = 500 + j * 38
            failed = (j == 1 and 60 <= f < RECHECK)
            if failed:
                col = RED
            elif f >= PASS_AT:
                col = GREEN
            elif 60 <= f < RECHECK:
                col = GREEN
            elif RECHECK <= f < PASS_AT and j == 1:
                col = BLUE
            elif RECHECK <= f < PASS_AT:
                col = GREEN
            else:
                col = BLUE
            d.text((1026, yy), label, font=F(JR, 16), fill=SUB)
            if f >= 59:
                d.text((W - 104, yy), f"{val:.1f}", font=F(JB, 16), fill=RED if failed else TEXT, anchor="ra")
            rr(d, [1170, yy + 3, W - 160, yy + 13], 5, fill=SURFACE)
            wb = (W - 160 - 1170) * (val / 10)
            if wb > 10:
                rr(d, [1170, yy + 3, 1170 + wb, yy + 13], 5, fill=col)
            gx = 1170 + (W - 160 - 1170) * 0.7
            d.line([gx, yy, gx, yy + 16], fill=TEXT, width=2)
        d.text((1170 + (W - 160 - 1170) * 0.7, 664), "gate 7 — below it, work goes back", font=F(JR, 12), fill=DIM, anchor="ma")
        if 60 <= f < RECHECK:
            rr(d, [1026, 616, 1170 - 16, 656], 10, fill=(243, 139, 168, 46), outline=RED, width=2)
            if (f % 4) < 3:
                d.text(((1026 + 1154) / 2, 636), "✗ SENT BACK", font=F(JB, 16), fill=RED, anchor="mm")
        elif f >= PASS_AT:
            rr(d, [1026, 616, 1170 - 16, 656], 10, fill=(166, 227, 161, 36), outline=GREEN, width=2)
            d.text(((1026 + 1154) / 2, 636), "✓ PASS", font=F(JB, 16), fill=GREEN, anchor="mm")
    else:
        d.text((1026, 502), "Panel convenes at Phase 6.", font=F(JR, 16), fill=DIM)
        d.text((1026, 530), "Nine domains score the work;", font=F(JR, 16), fill=DIM)
        d.text((1026, 558), "below the gate, the work goes back.", font=F(JR, 16), fill=DIM)

    # ---------- records ----------
    ry = 736
    d.text((64, ry), "RECORDS", font=F(JB, 16), fill=DIM)
    chips = [("design brief", 11), ("project manifest", 29), ("failure ledger", 60), ("QA report", PASS_AT)]
    cx = 190
    for label, tick_f in chips:
        wch = d.textlength(label, font=F(JR, 17)) + 58
        on = f >= tick_f
        rr(d, [cx, ry - 8, cx + wch, ry + 34], 21, fill=SURFACE if on else CARD,
           outline=GREEN if on else SURFACE2, width=2)
        d.text((cx + 18, ry + 13), "✓" if on else "·", font=F(JB, 17), fill=GREEN if on else DIM, anchor="lm")
        d.text((cx + 40, ry + 13), label, font=F(JR, 17), fill=TEXT if on else DIM, anchor="lm")
        cx += wch + 18

    # ---------- finale ----------
    if f >= 114:
        a = min(1.0, (f - 113) / 3)
        ov = Image.new("RGBA", (W, H), VEIL + (int(185 * a),))
        img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"), (0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        cxm, cym = W / 2, H / 2 - 30
        rr(d, [cxm - 350, cym - 128, cxm + 350, cym + 128], 22, fill=CARD, outline=GREEN, width=3)
        d.ellipse([cxm - 44, cym - 96, cxm + 44, cym - 8], outline=GREEN, width=6)
        d.line([cxm - 22, cym - 52, cxm - 6, cym - 34], fill=GREEN, width=7, joint="curve")
        d.line([cxm - 6, cym - 34, cxm + 26, cym - 72], fill=GREEN, width=7, joint="curve")
        d.text((cxm, cym + 22), "Delivered", font=F(JB, 46), fill=TEXT, anchor="ma")
        d.text((cxm, cym + 84), "and the next run loops the same ring", font=F(JR, 19), fill=SUB, anchor="ma")
    return img

def main():
    out_dir = Path(__file__).resolve().parent.parent / "docs" / "assets"
    for theme in ("dark", "light"):
        use_theme(theme)
        frames = [draw(f) for f in range(126)]
        montage = Image.new("RGB", (W * 2, H * 2))
        for k, fi in enumerate((30, 58, 73, 96)):
            montage.paste(frames[fi], ((k % 2) * W, (k // 2) * H))
        pal = montage.quantize(colors=256, method=Image.MEDIANCUT)
        qframes = [fr.quantize(colors=256, palette=pal, dither=Image.NONE) for fr in frames]
        target = out_dir / f"harness-run-{theme}.gif"
        qframes[0].save(target, save_all=True, append_images=qframes[1:],
                        duration=130, loop=0, optimize=True)
        print("wrote", target)


if __name__ == "__main__":
    sys.exit(main())

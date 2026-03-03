"""
Pythia App Icon v2 — Clean, Modern, Minimal
Design: Golden φ (phi) with ascending chart, deep blue background
Concept: φ = Pythia + Golden Ratio (finance) — elegant and meaningful
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os
import json

SIZE = 1024
CENTER = SIZE // 2
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "Pythia", "Assets.xcassets", "AppIcon.appiconset")

# Theme colors
BG_DARK = (11, 15, 30)             # Very dark navy
BG_MID = (20, 40, 100)             # Deep blue center
GOLD = (245, 178, 40)              # Warm gold
GOLD_BRIGHT = (255, 210, 80)       # Bright gold highlight
GOLD_DIM = (180, 130, 30)          # Subtle gold
WHITE_SOFT = (220, 230, 245)       # Soft white-blue


def radial_gradient(img):
    """Smooth radial gradient background"""
    for y in range(SIZE):
        for x in range(SIZE):
            dx = (x - CENTER) / (SIZE * 0.5)
            dy = (y - CENTER) / (SIZE * 0.5)
            d = min(math.sqrt(dx * dx + dy * dy), 1.0)
            # Smooth ease
            t = d * d
            r = int(BG_MID[0] * (1 - t) + BG_DARK[0] * t)
            g = int(BG_MID[1] * (1 - t) + BG_DARK[1] * t)
            b = int(BG_MID[2] * (1 - t) + BG_DARK[2] * t)
            img.putpixel((x, y), (r, g, b, 255))


def draw_smooth_line(draw, points, color, width):
    """Draw anti-aliased line through points"""
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=color, width=width)


def draw_phi(draw):
    """Draw a beautiful stylized φ (phi) symbol — large and centered"""
    cx, cy = CENTER, int(SIZE * 0.44)

    # The circle part of φ
    circle_r = int(SIZE * 0.18)

    # Golden glow rings
    for glow in range(20, 0, -1):
        r = circle_r + glow * 2
        alpha_factor = 1 - glow / 20
        gc = (
            int(GOLD_DIM[0] * alpha_factor),
            int(GOLD_DIM[1] * alpha_factor),
            int(GOLD_DIM[2] * alpha_factor),
        )
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=gc, width=1
        )

    # Main circle outline
    draw.ellipse(
        [cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r],
        outline=GOLD, width=7
    )

    # Inner bright circle
    inner_r = circle_r - 4
    draw.ellipse(
        [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
        outline=GOLD_BRIGHT, width=2
    )

    # Vertical stroke of φ — extends above and below circle
    bar_top = cy - int(SIZE * 0.28)
    bar_bottom = cy + int(SIZE * 0.28)

    # Glow for bar
    for glow in range(8, 0, -1):
        gc = (
            int(GOLD_DIM[0] * (1 - glow / 8) * 0.5),
            int(GOLD_DIM[1] * (1 - glow / 8) * 0.5),
            int(GOLD_DIM[2] * (1 - glow / 8) * 0.5),
        )
        draw.line([(cx, bar_top), (cx, bar_bottom)], fill=gc, width=glow * 3 + 6)

    # Main vertical bar
    draw.line([(cx, bar_top), (cx, bar_bottom)], fill=GOLD, width=7)
    draw.line([(cx, bar_top), (cx, bar_bottom)], fill=GOLD_BRIGHT, width=2)

    # Small serifs at top and bottom
    serif_w = 18
    draw.line([(cx - serif_w, bar_top), (cx + serif_w, bar_top)], fill=GOLD, width=5)
    draw.line([(cx - serif_w, bar_bottom), (cx + serif_w, bar_bottom)], fill=GOLD, width=5)


def draw_ascending_chart(draw):
    """Ascending chart line weaving through the φ symbol"""
    # Chart points — smooth ascending curve
    raw = [
        (0.18, 0.55),
        (0.25, 0.52),
        (0.30, 0.54),
        (0.35, 0.49),
        (0.40, 0.50),
        (0.45, 0.44),
        (0.50, 0.46),
        (0.55, 0.40),
        (0.60, 0.42),
        (0.65, 0.36),
        (0.70, 0.38),
        (0.75, 0.32),
        (0.80, 0.30),
        (0.83, 0.28),
    ]
    points = [(int(x * SIZE), int(y * SIZE)) for x, y in raw]

    # Glow under chart line
    for glow in range(12, 0, -1):
        gc = (
            int(GOLD[0] * 0.15 * (1 - glow / 12)),
            int(GOLD[1] * 0.15 * (1 - glow / 12)),
            int(GOLD[2] * 0.15 * (1 - glow / 12)),
        )
        draw_smooth_line(draw, points, gc, glow * 4)

    # Main chart line
    draw_smooth_line(draw, points, GOLD, 6)
    draw_smooth_line(draw, points, GOLD_BRIGHT, 2)

    # Glowing dot at end
    lx, ly = points[-1]
    for glow in range(15, 0, -1):
        gc = (
            int(GOLD_BRIGHT[0] * (1 - glow / 15) * 0.6),
            int(GOLD_BRIGHT[1] * (1 - glow / 15) * 0.6),
            int(GOLD_BRIGHT[2] * (1 - glow / 15) * 0.6),
        )
        draw.ellipse([lx - glow, ly - glow, lx + glow, ly + glow], fill=gc)
    draw.ellipse([lx - 6, ly - 6, lx + 6, ly + 6], fill=GOLD_BRIGHT)


def draw_text(draw):
    """PYTHIA text at the bottom"""
    try:
        # Try system fonts
        for font_path in [
            "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSDisplay.ttf",
        ]:
            try:
                font = ImageFont.truetype(font_path, 72)
                break
            except:
                continue
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    text = "P Y T H I A"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = CENTER - tw // 2
    y = int(SIZE * 0.80)

    # Subtle glow
    for glow in range(4, 0, -1):
        gc = (
            int(GOLD_DIM[0] * 0.4),
            int(GOLD_DIM[1] * 0.4),
            int(GOLD_DIM[2] * 0.4),
        )
        draw.text((x, y + glow), text, fill=gc, font=font)
        draw.text((x, y - glow), text, fill=gc, font=font)

    draw.text((x, y), text, fill=GOLD, font=font)


def draw_subtle_grid(draw):
    """Very subtle horizontal grid lines"""
    for i in range(7):
        y = int(SIZE * (0.20 + i * 0.08))
        for x in range(int(SIZE * 0.12), int(SIZE * 0.88), 16):
            draw.point((x, y), fill=(30, 50, 90))


def generate():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # 1. Background gradient
    radial_gradient(img)
    draw = ImageDraw.Draw(img)

    # 2. Very subtle grid
    draw_subtle_grid(draw)

    # 3. φ symbol (the hero)
    draw_phi(draw)

    # 4. Chart line through it
    draw_ascending_chart(draw)

    # 5. PYTHIA text
    draw_text(draw)

    # Round corners (macOS standard)
    mask = Image.new("L", (SIZE, SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, SIZE, SIZE], radius=int(SIZE * 0.22), fill=255)
    img.putalpha(mask)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for s in sizes:
        resized = img.resize((s, s), Image.LANCZOS)
        resized.save(os.path.join(OUTPUT_DIR, f"icon_{s}.png"), "PNG")
        print(f"  icon_{s}.png")

    # Contents.json
    contents = {
        "images": [
            {"filename": "icon_16.png", "idiom": "mac", "scale": "1x", "size": "16x16"},
            {"filename": "icon_32.png", "idiom": "mac", "scale": "2x", "size": "16x16"},
            {"filename": "icon_32.png", "idiom": "mac", "scale": "1x", "size": "32x32"},
            {"filename": "icon_64.png", "idiom": "mac", "scale": "2x", "size": "32x32"},
            {"filename": "icon_128.png", "idiom": "mac", "scale": "1x", "size": "128x128"},
            {"filename": "icon_256.png", "idiom": "mac", "scale": "2x", "size": "128x128"},
            {"filename": "icon_256.png", "idiom": "mac", "scale": "1x", "size": "256x256"},
            {"filename": "icon_512.png", "idiom": "mac", "scale": "2x", "size": "256x256"},
            {"filename": "icon_512.png", "idiom": "mac", "scale": "1x", "size": "512x512"},
            {"filename": "icon_1024.png", "idiom": "mac", "scale": "2x", "size": "512x512"},
        ],
        "info": {"author": "xcode", "version": 1}
    }
    with open(os.path.join(OUTPUT_DIR, "Contents.json"), "w") as f:
        json.dump(contents, f, indent=2)

    print("Done!")


if __name__ == "__main__":
    generate()

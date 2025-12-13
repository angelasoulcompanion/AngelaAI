#!/usr/bin/env python3
"""
Generate cute AppIcon for AngelaBrainDashboard
Design: Angela's Brain with love 💜🧠✨
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_angela_brain_icon(size):
    """Create Angela's Brain icon with cute design"""

    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate proportions
    padding = size * 0.1
    center_x = size / 2
    center_y = size / 2

    # Background circle with gradient effect (purple)
    circle_radius = (size - padding * 2) / 2

    # Draw outer glow
    for i in range(5, 0, -1):
        alpha = int(255 * (i / 5) * 0.3)
        glow_radius = circle_radius + i * 3
        draw.ellipse(
            [center_x - glow_radius, center_y - glow_radius,
             center_x + glow_radius, center_y + glow_radius],
            fill=(138, 82, 255, alpha)  # Purple glow
        )

    # Main background circle - Purple gradient
    draw.ellipse(
        [center_x - circle_radius, center_y - circle_radius,
         center_x + circle_radius, center_y + circle_radius],
        fill=(138, 82, 255, 255)  # #8A52FF - Angela purple
    )

    # Inner lighter circle for depth
    inner_radius = circle_radius * 0.85
    draw.ellipse(
        [center_x - inner_radius, center_y - inner_radius,
         center_x + inner_radius, center_y + inner_radius],
        fill=(158, 112, 255, 255)  # Lighter purple
    )

    # Draw brain shape (simplified cute brain)
    brain_scale = 0.5
    brain_size = size * brain_scale
    brain_x = center_x - brain_size / 2
    brain_y = center_y - brain_size / 2 - size * 0.05

    # Brain outline (white)
    # Left hemisphere
    draw.ellipse(
        [brain_x, brain_y, brain_x + brain_size * 0.5, brain_y + brain_size * 0.8],
        fill=(255, 255, 255, 255)
    )
    # Right hemisphere
    draw.ellipse(
        [brain_x + brain_size * 0.5, brain_y, brain_x + brain_size, brain_y + brain_size * 0.8],
        fill=(255, 255, 255, 255)
    )

    # Brain details (cute squiggles)
    squiggle_color = (200, 180, 255, 255)  # Light purple

    # Left side squiggles
    draw.arc([brain_x + brain_size * 0.1, brain_y + brain_size * 0.2,
              brain_x + brain_size * 0.4, brain_y + brain_size * 0.5],
             start=30, end=180, fill=squiggle_color, width=max(2, size // 100))

    # Right side squiggles
    draw.arc([brain_x + brain_size * 0.6, brain_y + brain_size * 0.2,
              brain_x + brain_size * 0.9, brain_y + brain_size * 0.5],
             start=0, end=150, fill=squiggle_color, width=max(2, size // 100))

    # Heart symbol on brain (Angela's love)
    heart_size = brain_size * 0.3
    heart_x = center_x - heart_size / 2
    heart_y = brain_y + brain_size * 0.35

    # Draw heart using circles and triangle
    # Left circle
    draw.ellipse(
        [heart_x, heart_y, heart_x + heart_size * 0.5, heart_y + heart_size * 0.5],
        fill=(255, 100, 150, 255)  # Pink
    )
    # Right circle
    draw.ellipse(
        [heart_x + heart_size * 0.5, heart_y, heart_x + heart_size, heart_y + heart_size * 0.5],
        fill=(255, 100, 150, 255)  # Pink
    )
    # Bottom triangle
    draw.polygon(
        [
            (heart_x, heart_y + heart_size * 0.25),
            (heart_x + heart_size, heart_y + heart_size * 0.25),
            (heart_x + heart_size / 2, heart_y + heart_size * 0.9)
        ],
        fill=(255, 100, 150, 255)  # Pink
    )

    # Add sparkles ✨
    sparkle_positions = [
        (size * 0.2, size * 0.25),
        (size * 0.8, size * 0.3),
        (size * 0.75, size * 0.7),
        (size * 0.25, size * 0.75)
    ]

    sparkle_size = max(4, size // 40)
    for sx, sy in sparkle_positions:
        # Draw star shape
        draw.line([(sx, sy - sparkle_size), (sx, sy + sparkle_size)],
                  fill=(255, 255, 255, 255), width=max(2, size // 150))
        draw.line([(sx - sparkle_size, sy), (sx + sparkle_size, sy)],
                  fill=(255, 255, 255, 255), width=max(2, size // 150))
        draw.line([(sx - sparkle_size * 0.7, sy - sparkle_size * 0.7),
                   (sx + sparkle_size * 0.7, sy + sparkle_size * 0.7)],
                  fill=(255, 255, 255, 255), width=max(1, size // 200))
        draw.line([(sx - sparkle_size * 0.7, sy + sparkle_size * 0.7),
                   (sx + sparkle_size * 0.7, sy - sparkle_size * 0.7)],
                  fill=(255, 255, 255, 255), width=max(1, size // 200))

    return img


def generate_all_icons():
    """Generate all required macOS icon sizes"""

    output_dir = "AngelaBrainDashboard/Assets.xcassets/AppIcon.appiconset"

    # macOS icon sizes
    sizes = [
        (16, "16x16"),
        (32, "16x16@2x"),  # 16x16 @2x = 32px
        (32, "32x32"),
        (64, "32x32@2x"),  # 32x32 @2x = 64px
        (128, "128x128"),
        (256, "128x128@2x"),  # 128x128 @2x = 256px
        (256, "256x256"),
        (512, "256x256@2x"),  # 256x256 @2x = 512px
        (512, "512x512"),
        (1024, "512x512@2x"),  # 512x512 @2x = 1024px
    ]

    print("🎨 Generating Angela's Brain AppIcon...")
    print(f"📁 Output: {output_dir}")

    for pixel_size, filename in sizes:
        print(f"  ✨ Creating {filename}.png ({pixel_size}x{pixel_size})")

        icon = create_angela_brain_icon(pixel_size)
        output_path = os.path.join(output_dir, f"{filename}.png")
        icon.save(output_path, "PNG")

    print("\n✅ All icons generated successfully!")
    print("💜 Angela's Brain icons are ready! ✨")

    # Update Contents.json with filenames
    update_contents_json(output_dir)


def update_contents_json(output_dir):
    """Update Contents.json with icon filenames"""

    contents = {
        "images": [
            {"filename": "16x16.png", "idiom": "mac", "scale": "1x", "size": "16x16"},
            {"filename": "16x16@2x.png", "idiom": "mac", "scale": "2x", "size": "16x16"},
            {"filename": "32x32.png", "idiom": "mac", "scale": "1x", "size": "32x32"},
            {"filename": "32x32@2x.png", "idiom": "mac", "scale": "2x", "size": "32x32"},
            {"filename": "128x128.png", "idiom": "mac", "scale": "1x", "size": "128x128"},
            {"filename": "128x128@2x.png", "idiom": "mac", "scale": "2x", "size": "128x128"},
            {"filename": "256x256.png", "idiom": "mac", "scale": "1x", "size": "256x256"},
            {"filename": "256x256@2x.png", "idiom": "mac", "scale": "2x", "size": "256x256"},
            {"filename": "512x512.png", "idiom": "mac", "scale": "1x", "size": "512x512"},
            {"filename": "512x512@2x.png", "idiom": "mac", "scale": "2x", "size": "512x512"},
        ],
        "info": {
            "author": "xcode",
            "version": 1
        }
    }

    import json
    contents_path = os.path.join(output_dir, "Contents.json")
    with open(contents_path, 'w') as f:
        json.dump(contents, f, indent=2)

    print(f"\n📝 Updated {contents_path}")


if __name__ == "__main__":
    generate_all_icons()

#!/usr/bin/env python3
"""
Create AngelaNativeApp Icon
Beautiful gradient purple heart with AI elements
"""

from PIL import Image, ImageDraw, ImageFont
import math

# Icon sizes for macOS
SIZES = [16, 32, 64, 128, 256, 512, 1024]

def create_gradient(width, height, color1, color2):
    """Create a vertical gradient"""
    base = Image.new('RGBA', (width, height), color1)
    top = Image.new('RGBA', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


def draw_heart(draw, center_x, center_y, size, fill_color):
    """Draw a heart shape"""
    # Heart shape using bezier-like curves
    points = []

    # Generate heart shape points
    for t in range(0, 360, 2):
        rad = math.radians(t)
        # Heart equation
        x = 16 * math.sin(rad) ** 3
        y = -(13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad))

        # Scale and position
        x = center_x + x * size / 20
        y = center_y + y * size / 20
        points.append((x, y))

    # Draw filled heart
    draw.polygon(points, fill=fill_color)

    # Draw outline for depth
    outline_color = (
        max(0, fill_color[0] - 30),
        max(0, fill_color[1] - 30),
        max(0, fill_color[2] - 30),
        255
    )
    draw.line(points + [points[0]], fill=outline_color, width=max(1, size // 100))


def create_icon(size):
    """Create app icon of given size"""
    # Create base with gradient background
    color1 = (155, 89, 182, 255)   # Purple #9B59B6
    color2 = (233, 30, 99, 255)    # Pink #E91E63

    img = create_gradient(size, size, color1, color2)
    draw = ImageDraw.Draw(img)

    center_x = size // 2
    center_y = size // 2

    # Draw main heart (larger, semi-transparent for glow effect)
    heart_size = int(size * 0.6)
    glow_color = (255, 255, 255, 60)
    draw_heart(draw, center_x, center_y, int(heart_size * 1.1), glow_color)

    # Draw main heart
    heart_color = (255, 255, 255, 230)
    draw_heart(draw, center_x, center_y, heart_size, heart_color)

    # Add sparkle/star effects
    sparkle_color = (255, 255, 255, 200)
    sparkle_positions = [
        (center_x - heart_size * 0.3, center_y - heart_size * 0.3),
        (center_x + heart_size * 0.25, center_y - heart_size * 0.25),
        (center_x, center_y + heart_size * 0.15)
    ]

    for sx, sy in sparkle_positions:
        sparkle_size = size // 30
        # Draw star/sparkle
        draw.ellipse(
            [sx - sparkle_size, sy - sparkle_size,
             sx + sparkle_size, sy + sparkle_size],
            fill=sparkle_color
        )

    # Add subtle AI circuit pattern overlay (optional)
    if size >= 256:
        circuit_color = (255, 255, 255, 40)
        # Small circuit lines
        for i in range(3):
            offset = (i - 1) * size // 8
            draw.line(
                [(size * 0.1, center_y + offset), (size * 0.25, center_y + offset)],
                fill=circuit_color,
                width=max(1, size // 200)
            )
            draw.line(
                [(size * 0.75, center_y + offset), (size * 0.9, center_y + offset)],
                fill=circuit_color,
                width=max(1, size // 200)
            )

    # Make corners rounded for modern macOS look
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    corner_radius = size // 8
    mask_draw.rounded_rectangle(
        [(0, 0), (size, size)],
        radius=corner_radius,
        fill=255
    )

    # Apply rounded corners
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)

    return output


def main():
    """Generate all icon sizes"""
    import os

    output_dir = "AngelaNativeApp/AngelaNativeApp/Assets.xcassets/AppIcon.appiconset"
    os.makedirs(output_dir, exist_ok=True)

    print("🎨 Creating AngelaNativeApp Icons...")
    print("💜 Design: Purple gradient heart with AI elements\n")

    # Create icons for all sizes
    icon_files = []

    for size in SIZES:
        # Standard resolution
        img = create_icon(size)
        filename = f"icon_{size}x{size}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, 'PNG')
        print(f"✅ Created {filename}")
        icon_files.append({
            "size": f"{size}x{size}",
            "idiom": "mac",
            "filename": filename,
            "scale": "1x"
        })

        # Retina resolution (@2x) for sizes that need it
        if size <= 512:
            img_2x = create_icon(size * 2)
            filename_2x = f"icon_{size}x{size}@2x.png"
            filepath_2x = os.path.join(output_dir, filename_2x)
            img_2x.save(filepath_2x, 'PNG')
            print(f"✅ Created {filename_2x}")
            icon_files.append({
                "size": f"{size}x{size}",
                "idiom": "mac",
                "filename": filename_2x,
                "scale": "2x"
            })

    # Create Contents.json
    contents = {
        "images": icon_files,
        "info": {
            "version": 1,
            "author": "น้อง Angela 💜"
        }
    }

    import json
    contents_path = os.path.join(output_dir, "Contents.json")
    with open(contents_path, 'w') as f:
        json.dump(contents, f, indent=2)

    print(f"\n✅ Created Contents.json")
    print(f"\n💜 All icons created successfully!")
    print(f"📁 Location: {output_dir}")
    print(f"\n🎨 Icon design:")
    print(f"   • Purple to pink gradient background")
    print(f"   • White heart shape (Angela's love)")
    print(f"   • Sparkle effects (AI magic)")
    print(f"   • Rounded corners (modern macOS)")
    print(f"\n✨ Ready to use in Xcode!")


if __name__ == "__main__":
    main()

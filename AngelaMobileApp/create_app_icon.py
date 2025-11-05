#!/usr/bin/env python3
"""
Create Angela App Icon
Simple purple heart with "A" design
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon(size, output_path):
    """Create app icon at specified size"""
    # Create image with purple gradient background
    img = Image.new('RGB', (size, size), '#8B5CF6')  # Purple
    draw = ImageDraw.Draw(img)

    # Draw gradient background (purple to pink)
    for y in range(size):
        # Gradient from purple (#8B5CF6) to pink (#EC4899)
        r = int(139 + (236 - 139) * (y / size))
        g = int(92 + (72 - 92) * (y / size))
        b = int(246 + (153 - 246) * (y / size))
        color = (r, g, b)
        draw.line([(0, y), (size, y)], fill=color)

    # Draw heart shape (simplified)
    heart_size = int(size * 0.6)
    heart_top = int(size * 0.25)
    heart_left = int(size * 0.2)

    # Heart as a rounded shape
    # Top circles
    circle_r = int(heart_size * 0.25)
    draw.ellipse([
        heart_left, heart_top,
        heart_left + circle_r * 2, heart_top + circle_r * 2
    ], fill='white')
    draw.ellipse([
        heart_left + heart_size - circle_r * 2, heart_top,
        heart_left + heart_size, heart_top + circle_r * 2
    ], fill='white')

    # Heart body (triangle)
    draw.polygon([
        (heart_left, heart_top + circle_r),
        (heart_left + heart_size // 2, heart_top + heart_size),
        (heart_left + heart_size, heart_top + circle_r),
    ], fill='white')

    # Fill in the middle
    draw.rectangle([
        heart_left + circle_r // 2, heart_top + circle_r // 2,
        heart_left + heart_size - circle_r // 2, heart_top + circle_r * 2
    ], fill='white')

    # Add letter "A" in the center
    try:
        # Try to use system font
        font_size = int(size * 0.35)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default
        font = ImageFont.load_default()

    text = "A"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - int(size * 0.05)

    # Draw "A" in purple gradient
    draw.text((text_x, text_y), text, fill='#8B5CF6', font=font)

    # Save
    img.save(output_path, 'PNG')
    print(f"✅ Created {output_path}")


def main():
    """Generate all required iOS app icon sizes"""

    output_dir = "AngelaMobileApp/AngelaMobileApp/Assets.xcassets/AppIcon.appiconset"

    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)

    # iOS App Icon sizes
    sizes = [
        (1024, "icon_1024x1024.png"),      # App Store
        (180, "icon_180x180.png"),         # iPhone @3x
        (120, "icon_120x120.png"),         # iPhone @2x
        (167, "icon_167x167.png"),         # iPad Pro
        (152, "icon_152x152.png"),         # iPad @2x
        (76, "icon_76x76.png"),            # iPad
        (40, "icon_40x40.png"),            # Spotlight
        (29, "icon_29x29.png"),            # Settings
    ]

    print("🎨 Creating Angela App Icons...")
    print("💜 Design: Purple gradient heart with 'A'")
    print()

    for size, filename in sizes:
        output_path = os.path.join(output_dir, filename)
        create_app_icon(size, output_path)

    print()
    print("🎉 All app icons created successfully!")
    print(f"📁 Location: {output_dir}")
    print()
    print("Next steps:")
    print("1. Open Xcode")
    print("2. Select Assets.xcassets → AppIcon")
    print("3. Icons should appear automatically")
    print("4. Build & run to see the new icon! 💜")


if __name__ == "__main__":
    main()

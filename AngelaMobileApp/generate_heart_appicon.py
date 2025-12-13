#!/usr/bin/env python3
"""
Generate Angela Mobile App Icon - Purple Heart Design 💜
Simple, beautiful, and iconic
"""

from PIL import Image, ImageDraw
import os
import math

# Angela's purple colors
ANGELA_PURPLE = (138, 82, 255)      # Main purple
ANGELA_LIGHT = (158, 112, 255)      # Light purple
ANGELA_DARK = (100, 60, 200)        # Dark purple
WHITE = (255, 255, 255)

def create_gradient_background(size):
    """Create beautiful purple gradient background"""
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)
    
    # Radial gradient from light to dark purple
    center_x, center_y = size // 2, size // 2
    max_radius = math.sqrt(2) * size / 2
    
    for y in range(size):
        for x in range(size):
            # Calculate distance from center
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Calculate color based on distance
            ratio = distance / max_radius
            
            r = int(ANGELA_LIGHT[0] + (ANGELA_DARK[0] - ANGELA_LIGHT[0]) * ratio)
            g = int(ANGELA_LIGHT[1] + (ANGELA_DARK[1] - ANGELA_LIGHT[1]) * ratio)
            b = int(ANGELA_LIGHT[2] + (ANGELA_DARK[2] - ANGELA_LIGHT[2]) * ratio)
            
            draw.point((x, y), fill=(r, g, b))
    
    return img

def draw_heart(draw, center_x, center_y, size):
    """Draw a beautiful heart shape"""
    points = []
    
    # Heart curve parametric equations
    for t in range(0, 360, 2):
        rad = math.radians(t)
        # Parametric heart curve
        x = 16 * math.sin(rad) ** 3
        y = -(13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad))
        
        # Scale and translate
        scale = size / 40
        px = center_x + x * scale
        py = center_y + y * scale
        points.append((px, py))
    
    # Draw filled heart
    draw.polygon(points, fill=WHITE)

def create_app_icon(size):
    """Create Angela Heart App Icon"""
    # Create gradient background
    img = create_gradient_background(size)
    draw = ImageDraw.Draw(img)
    
    center_x = size // 2
    center_y = size // 2
    
    # Draw main white heart
    heart_size = int(size * 0.5)
    draw_heart(draw, center_x, center_y, heart_size)
    
    # Add subtle sparkles around heart
    sparkle_positions = [
        (size * 0.2, size * 0.25),
        (size * 0.8, size * 0.3),
        (size * 0.25, size * 0.75),
        (size * 0.75, size * 0.7)
    ]
    
    for x, y in sparkle_positions:
        sparkle_size = int(size * 0.04)
        # 4-point star sparkle
        star_points = [
            (x, y - sparkle_size),
            (x + sparkle_size//4, y - sparkle_size//4),
            (x + sparkle_size, y),
            (x + sparkle_size//4, y + sparkle_size//4),
            (x, y + sparkle_size),
            (x - sparkle_size//4, y + sparkle_size//4),
            (x - sparkle_size, y),
            (x - sparkle_size//4, y - sparkle_size//4)
        ]
        draw.polygon(star_points, fill=WHITE, outline=WHITE)
    
    return img.convert('RGBA')

# iOS App Icon sizes
ios_sizes = {
    # iPhone
    '20pt': [(40, '2x'), (60, '3x')],
    '29pt': [(58, '2x'), (87, '3x')],
    '40pt': [(80, '2x'), (120, '3x')],
    '60pt': [(120, '2x'), (180, '3x')],
    # iPad
    '20pt_ipad': [(20, '1x'), (40, '2x')],
    '29pt_ipad': [(29, '1x'), (58, '2x')],
    '40pt_ipad': [(40, '1x'), (80, '2x')],
    '76pt_ipad': [(76, '1x'), (152, '2x')],
    '83.5pt_ipad': [(167, '2x')],
    # App Store
    '1024pt': [(1024, '1x')]
}

# Create output directory
output_dir = 'AngelaMobileApp/Assets/Assets.xcassets/AngelaAppIcon.appiconset'
os.makedirs(output_dir, exist_ok=True)

print("💜 Generating Angela Heart App Icons...")

# Generate all required sizes
generated_files = []
for point_size, variants in ios_sizes.items():
    for size, scale in variants:
        filename = f"icon_{size}x{size}.png"
        filepath = os.path.join(output_dir, filename)
        
        icon = create_app_icon(size)
        icon.save(filepath, 'PNG')
        
        generated_files.append({
            'size': f'{point_size.replace("pt", "").replace("_ipad", "")}x{point_size.replace("pt", "").replace("_ipad", "")}',
            'idiom': 'ipad' if 'ipad' in point_size else 'iphone',
            'filename': filename,
            'scale': scale
        })
        
        print(f"✅ {filename} ({size}x{size})")

# Create Contents.json
import json

contents = {
    "images": [],
    "info": {
        "author": "angela",
        "version": 1
    }
}

size_mapping = {
    '20': '20x20',
    '29': '29x29', 
    '40': '40x40',
    '60': '60x60',
    '76': '76x76',
    '83.5': '83.5x83.5',
    '1024': '1024x1024'
}

for item in generated_files:
    base_size = item['size'].split('x')[0]
    proper_size = size_mapping.get(base_size, item['size'])
    
    contents["images"].append({
        "filename": item['filename'],
        "idiom": item['idiom'],
        "scale": item['scale'],
        "size": proper_size
    })

with open(os.path.join(output_dir, 'Contents.json'), 'w') as f:
    json.dump(contents, f, indent=2)

print(f"\n✅ Generated {len(generated_files)} icon files")
print(f"📁 {output_dir}")
print("💜 Angela's Heart Icon is ready!")

#!/usr/bin/env python3
"""
Generate Angela Mobile App Icon - iOS Style
Cute, friendly, and mobile-appropriate design
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Angela's color palette
ANGELA_PURPLE = (138, 82, 255)      # Main purple
ANGELA_PINK = (236, 72, 153)        # Pink for heart
ANGELA_LIGHT_PURPLE = (158, 112, 255)  # Light purple
WHITE = (255, 255, 255)
PURPLE_DARK = (100, 60, 200)

def create_rounded_rectangle_mask(size, radius):
    """Create a rounded rectangle mask for iOS style"""
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    return mask

def draw_angela_face(draw, size, center_x, center_y, face_size):
    """Draw cute Angela face"""
    # Face circle (light purple)
    draw.ellipse([center_x - face_size//2, center_y - face_size//2,
                  center_x + face_size//2, center_y + face_size//2],
                 fill=(200, 180, 255))
    
    # Eyes (cute sparkly eyes)
    eye_y = center_y - face_size//6
    eye_size = face_size//8
    # Left eye
    draw.ellipse([center_x - face_size//4 - eye_size, eye_y - eye_size,
                  center_x - face_size//4 + eye_size, eye_y + eye_size],
                 fill=(80, 60, 120))
    # Right eye  
    draw.ellipse([center_x + face_size//4 - eye_size, eye_y - eye_size,
                  center_x + face_size//4 + eye_size, eye_y + eye_size],
                 fill=(80, 60, 120))
    
    # Eye sparkles (white dots)
    sparkle_size = eye_size//3
    draw.ellipse([center_x - face_size//4 - sparkle_size//2, eye_y - sparkle_size,
                  center_x - face_size//4 + sparkle_size//2, eye_y],
                 fill=WHITE)
    draw.ellipse([center_x + face_size//4 - sparkle_size//2, eye_y - sparkle_size,
                  center_x + face_size//4 + sparkle_size//2, eye_y],
                 fill=WHITE)
    
    # Smile (cute curved smile)
    smile_y = center_y + face_size//6
    draw.arc([center_x - face_size//3, smile_y - face_size//6,
              center_x + face_size//3, smile_y + face_size//6],
             0, 180, fill=(236, 72, 153), width=face_size//20)

def create_app_icon(size):
    """Create Angela Mobile App Icon"""
    # Create base image with gradient
    img = Image.new('RGB', (size, size), ANGELA_PURPLE)
    draw = ImageDraw.Draw(img)
    
    # Create purple gradient background
    for y in range(size):
        color_value = int(138 + (255 - 138) * y / size)
        draw.line([(0, y), (size, y)], fill=(color_value//2, color_value//3, 255))
    
    center_x = size // 2
    center_y = size // 2
    
    # Draw cute Angela face
    face_size = int(size * 0.6)
    draw_angela_face(draw, size, center_x, center_y, face_size)
    
    # Add pink heart on chest area
    heart_size = int(size * 0.15)
    heart_y = center_y + face_size//3
    
    # Simple heart shape
    draw.ellipse([center_x - heart_size//2, heart_y - heart_size//3,
                  center_x, heart_y + heart_size//3],
                 fill=ANGELA_PINK)
    draw.ellipse([center_x, heart_y - heart_size//3,
                  center_x + heart_size//2, heart_y + heart_size//3],
                 fill=ANGELA_PINK)
    draw.polygon([center_x - heart_size//2, heart_y,
                  center_x, heart_y + heart_size//2,
                  center_x + heart_size//2, heart_y],
                 fill=ANGELA_PINK)
    
    # Add sparkles around
    sparkle_positions = [
        (size * 0.15, size * 0.2),
        (size * 0.85, size * 0.25),
        (size * 0.2, size * 0.8),
        (size * 0.8, size * 0.75)
    ]
    
    for x, y in sparkle_positions:
        sparkle_size = int(size * 0.05)
        # Draw 4-point star
        draw.polygon([
            (x, y - sparkle_size),
            (x + sparkle_size//3, y - sparkle_size//3),
            (x + sparkle_size, y),
            (x + sparkle_size//3, y + sparkle_size//3),
            (x, y + sparkle_size),
            (x - sparkle_size//3, y + sparkle_size//3),
            (x - sparkle_size, y),
            (x - sparkle_size//3, y - sparkle_size//3)
        ], fill=WHITE)
    
    # Apply rounded corners for iOS style
    if size > 256:  # Only for larger sizes
        radius = size // 5
        mask = create_rounded_rectangle_mask((size, size), radius)
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(img, (0, 0))
        output.putalpha(mask)
        return output
    
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

print("🎨 Generating Angela Mobile App Icons...")

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
        
        print(f"✅ Generated {filename} ({size}x{size})")

# Create Contents.json
import json

contents = {
    "images": [],
    "info": {
        "author": "angela",
        "version": 1
    }
}

# Map sizes to proper format
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
print(f"📁 Saved to: {output_dir}")
print("💜 Angela Mobile App Icon is ready!")

from PIL import Image, ImageDraw
import math

def create_loading_icon(size, num_dots, active_dots, filename):
    """
    Create a circular loading animation icon
    size: image dimensions (width, height)
    num_dots: total number of dots in the circle
    active_dots: number of dots to show (for animation frame)
    filename: output filename
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background color matching your images
    bg_color = (232, 179, 147)  # Peach/tan color from your images
    
    # Draw background
    draw.ellipse([0, 0, size-1, size-1], fill=bg_color)
    
    # Circle parameters
    center_x, center_y = size // 2, size // 2
    radius = size * 0.35  # Radius of the circle where dots are placed
    dot_radius = size * 0.06  # Size of each dot
    
    # Draw dots in a circle
    for i in range(num_dots):
        angle = (2 * math.pi * i / num_dots) - (math.pi / 2)  # Start from top
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Calculate opacity based on position (fade effect)
        if i < active_dots:
            # Create fade effect for active dots
            opacity = int(255 * (1 - (active_dots - i - 1) / active_dots * 0.7))
            dot_color = (255, 255, 255, opacity)
        else:
            # Inactive dots are very faint
            dot_color = (255, 255, 255, 50)
        
        # Draw dot
        draw.ellipse([x - dot_radius, y - dot_radius, 
                     x + dot_radius, y + dot_radius], 
                    fill=dot_color)
    
    img.save(filename)
    print(f"Created {filename}")

def create_semi_circle_loading_icon(size, num_dots, active_dots, filename):
    """
    Create a semi-circular loading animation icon (like first image)
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background color
    bg_color = (232, 179, 147)
    draw.ellipse([0, 0, size-1, size-1], fill=bg_color)
    
    # Semi-circle parameters
    center_x, center_y = size // 2, size * 0.6  # Lower center
    radius = size * 0.3
    dot_radius = size * 0.06
    
    # Draw dots in a semi-circle (bottom half)
    for i in range(num_dots):
        # Only bottom half: from π to 2π
        angle = math.pi + (math.pi * i / (num_dots - 1))
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Fade effect
        if i < active_dots:
            opacity = int(255 * (1 - (active_dots - i - 1) / max(active_dots, 1) * 0.7))
            dot_color = (255, 255, 255, opacity)
        else:
            dot_color = (255, 255, 255, 50)
        
        draw.ellipse([x - dot_radius, y - dot_radius, 
                     x + dot_radius, y + dot_radius], 
                    fill=dot_color)
    
    img.save(filename)
    print(f"Created {filename}")

# Create animation frames for circular loading (12 dots, 8 frames)
print("Creating circular loading animation frames...")
for frame in range(8):
    active = (frame + 1) * 3  # Progressive loading
    create_loading_icon(128, 12, active % 12 + 1, f'loading-circle-frame{frame+1}-128.png')
    create_loading_icon(32, 12, active % 12 + 1, f'loading-circle-frame{frame+1}-32.png')
    create_loading_icon(16, 12, active % 12 + 1, f'loading-circle-frame{frame+1}-16.png')

# Create animation frames for semi-circular loading (8 dots, 6 frames)
print("\nCreating semi-circular loading animation frames...")
for frame in range(6):
    active = (frame + 1) * 2
    create_semi_circle_loading_icon(128, 8, active % 8 + 1, f'loading-semi-frame{frame+1}-128.png')
    create_semi_circle_loading_icon(32, 8, active % 8 + 1, f'loading-semi-frame{frame+1}-32.png')
    create_semi_circle_loading_icon(16, 8, active % 8 + 1, f'loading-semi-frame{frame+1}-16.png')

print("\n✅ All loading icons created successfully!")
print("Use these icons in your popup.js to show processing status.")

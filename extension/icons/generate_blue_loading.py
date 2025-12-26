from PIL import Image, ImageDraw
import math

def create_semi_circle_loading_icon(size, num_dots, frame, total_frames, filename):
    """
    Create a semi-circular loading animation icon with blue background
    size: image dimensions (width, height)
    num_dots: total number of dots in the circle
    frame: current frame number (0-based)
    total_frames: total number of frames
    filename: output filename
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Blue background color (matching the gradient middle tone)
    bg_color = (66, 165, 245)  # #42A5F5
    draw.ellipse([0, 0, size-1, size-1], fill=bg_color)
    
    # Semi-circle parameters
    center_x, center_y = size // 2, size * 0.6  # Lower center
    radius = size * 0.3
    dot_radius = size * 0.07
    
    # Animation: wave effect moving through dots
    animation_offset = (frame / total_frames) * num_dots
    
    # Draw dots in a semi-circle (bottom half)
    for i in range(num_dots):
        # Only bottom half: from π to 2π (right to left)
        angle = math.pi + (math.pi * i / (num_dots - 1))
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Calculate distance from animation wave
        distance = abs((i - animation_offset) % num_dots)
        if distance > num_dots / 2:
            distance = num_dots - distance
        
        # Create smooth wave effect
        wave_intensity = max(0, 1 - (distance / (num_dots / 3)))
        
        # Opacity based on wave position (180-255 range for visibility)
        base_opacity = 100
        wave_opacity = int(155 * wave_intensity)
        opacity = base_opacity + wave_opacity
        
        # Scale dots slightly based on wave intensity
        current_dot_radius = dot_radius * (0.8 + 0.4 * wave_intensity)
        
        # White dots with varying opacity
        dot_color = (255, 255, 255, opacity)
        
        draw.ellipse([x - current_dot_radius, y - current_dot_radius, 
                     x + current_dot_radius, y + current_dot_radius], 
                    fill=dot_color)
    
    img.save(filename)
    print(f"Created {filename}")

# Create 8 frames for smooth animation (more frames = smoother)
print("Creating blue semi-circular loading animation frames...")
num_dots = 8
total_frames = 8

for frame in range(total_frames):
    create_semi_circle_loading_icon(128, num_dots, frame, total_frames, 
                                   f'loading-semi-frame{frame+1}-128.png')
    create_semi_circle_loading_icon(32, num_dots, frame, total_frames, 
                                   f'loading-semi-frame{frame+1}-32.png')
    create_semi_circle_loading_icon(16, num_dots, frame, total_frames, 
                                   f'loading-semi-frame{frame+1}-16.png')

print("\n✅ All blue loading icons created successfully!")
print("8 frames with smooth wave animation effect")

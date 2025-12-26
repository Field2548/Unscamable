from PIL import Image, ImageDraw
import math

def create_frame(size, num_dots, frame, total_frames):
    """Create a single frame of the loading animation"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Blue background color
    bg_color = (66, 165, 245)  # #42A5F5
    draw.ellipse([0, 0, size-1, size-1], fill=bg_color)
    
    # Semi-circle parameters
    center_x, center_y = size // 2, size * 0.6
    radius = size * 0.3
    dot_radius = size * 0.07
    
    # Animation: wave effect moving through dots
    animation_offset = (frame / total_frames) * num_dots
    
    # Draw dots in a semi-circle
    for i in range(num_dots):
        angle = math.pi + (math.pi * i / (num_dots - 1))
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Calculate distance from animation wave
        distance = abs((i - animation_offset) % num_dots)
        if distance > num_dots / 2:
            distance = num_dots - distance
        
        # Create smooth wave effect
        wave_intensity = max(0, 1 - (distance / (num_dots / 3)))
        
        # Opacity based on wave position
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
    
    return img

# Generate animated GIF
print("Creating animated loading icons...")
num_dots = 8
total_frames = 12  # More frames for smoother animation in GIF

for size in [16, 32, 128]:
    frames = []
    for frame in range(total_frames):
        frames.append(create_frame(size, num_dots, frame, total_frames))
    
    # Save as animated GIF
    filename = f'loading-animated-{size}.gif'
    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        duration=100,  # 100ms per frame
        loop=0  # Loop forever
    )
    print(f"Created {filename}")

print("\n✅ Animated loading GIF icons created successfully!")
print("Use loading-animated-16.gif, loading-animated-32.gif, loading-animated-128.gif")

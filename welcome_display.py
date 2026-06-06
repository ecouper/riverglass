import asyncio
import sys
import os
import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw

# --- HARDWARE MATRIX CONFIGURATION ---
def create_matrix():
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'regular'       # Golden Parameter: Triple Bonnet Pinout
    options.multiplexing = 0                  # Golden Parameter: Direct panel sync
    options.pixel_mapper_config = "Rotate:90"
    options.drop_privileges = False
    options.gpio_slowdown = 4                 # Gives fast Pi Zero 2 WH clock stability
    options.pwm_bits = 7                      # Lightens pin-flipping single-core overhead
    return RGBMatrix(options=options)

# --- IN RAINBOWS TRACKING ENGINE ---
def draw_tracked_text(draw, text, x, y, spacing, fill):
    """Draws text letter-by-letter with custom pixel spacing for a stylized look."""
    current_x = x
    for char in text:
        draw.text((current_x, y), char, fill=fill)
        current_x += 5 + spacing

async def main():
    try:
        matrix = create_matrix()
    except Exception as e:
        print(f"Matrix hardware connection failed: {e}")
        sys.exit(1)

    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    # Expanded naming convention list (6 slots total)
    photo_slots = ["a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg", "f.jpg"]
    image_cache = {}
    
    # State Engine
    start_time = time.time()
    current_mode = 0  # 0: Thank You, 1: Trip Tapestry, 2+: Photo Slots
    cycle_duration = 8.0  # Seconds per screen
    
    print("Flexible Smart-Cycling Engine Active! Press Ctrl+C to terminate.")
    
    while True:
        # Clear background to pure matte black
        draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
        
        # Check if it's time to advance the screen
        if time.time() - start_time > cycle_duration:
            # Clear out the cache periodically so it catches newly uploaded files
            image_cache.clear()
            
            # Smart Skip Logic Loop
            attempts = 0
            while attempts < 8:  # Safety ceiling to prevent infinite loops
                # Advance mode index
                current_mode += 1
                total_possible_modes = 2 + len(photo_slots) # Text screens (2) + Photo slots (6) = 8 total
                if current_mode >= total_possible_modes:
                    current_mode = 0
                
                # Modes 0 and 1 are always text, so they never get skipped
                if current_mode < 2:
                    break
                    
                # For modes 2+, check if the specific image file exists right now
                img_index = current_mode - 2
                filename = photo_slots[img_index]
                if os.path.exists(filename):
                    break  # Found a valid file! Break out of the skip finder.
                    
                attempts += 1
                
            start_time = time.time()
            
        # --- SCREEN 0: THE THANK YOU BANNER ---
        if current_mode == 0:
            draw_tracked_text(draw, "THANK YOU", x=2, y=2, spacing=2, fill=(0, 255, 150))   
            draw_tracked_text(draw, "FOR VISITING!", x=2, y=12, spacing=1, fill=(0, 180, 255)) 
            draw_tracked_text(draw, "LOVE,", x=2, y=28, spacing=3, fill=(255, 100, 0))       
            draw_tracked_text(draw, "LEO,", x=2, y=38, spacing=3, fill=(255, 0, 150))        
            draw_tracked_text(draw, "RACHEL,", x=2, y=46, spacing=1, fill=(255, 230, 0))     
            draw_tracked_text(draw, "AND ERIC", x=2, y=54, spacing=2, fill=(255, 255, 255))  

        # --- SCREEN 1: THE TRIP HIGHLIGHT TAPESTRY ---
        elif current_mode == 1:
            draw_tracked_text(draw, "SAFARI", x=2, y=1, spacing=4, fill=(255, 50, 50))       
            draw_tracked_text(draw, "LAKE JAMES", x=2, y=10, spacing=1, fill=(0, 235, 255))   
            draw_tracked_text(draw, "MUSEUM", x=2, y=19, spacing=4, fill=(50, 255, 50))      
            draw_tracked_text(draw, "TRAIN BOAT", x=2, y=28, spacing=1, fill=(255, 0, 200))   
            draw_tracked_text(draw, "BASEBALL", x=2, y=37, spacing=2, fill=(255, 140, 0))    
            draw_tracked_text(draw, "FOAM PARTY", x=2, y=46, spacing=1, fill=(200, 100, 255)) 
            draw_tracked_text(draw, "BLUEBERRIES", x=2, y=55, spacing=1, fill=(255, 255, 0))  

        # --- SCREENS 2+: SMART IMAGE SLOTS (a.jpg through f.jpg) ---
        else:
            img_index = current_mode - 2
            filename = photo_slots[img_index]
            
            if filename not in image_cache:
                try:
                    loaded_img = Image.open(filename).convert("RGB")
                    image_cache[filename] = loaded_img.resize((64, 64), Image.Resampling.NEAREST)
                except Exception as e:
                    print(f"Error decoding image file {filename}: {e}")
                    image_cache[filename] = None
            
            target_photo = image_cache.get(filename)
            if target_photo:
                canvas.paste(target_photo, (0, 0))

        # Push frame buffer to matrix display
        matrix.SetImage(canvas)
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWelcome Engine closed successfully.")
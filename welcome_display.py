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

# --- CONTINUOUS SEAMLESS WRAPPING TRACKING ENGINE ---
def draw_wrapping_tapestry(draw, word_color_list, start_x, start_y, char_spacing, line_height):
    """Flows a sequence of differently colored words across lines seamlessly, wrapping characters."""
    current_x = start_x
    current_y = start_y
    
    for word, color in word_color_list:
        # Append a space after the word to separate it from the next chunk
        word_to_draw = word + " "
        
        for char in word_to_draw:
            # Check if this single character will overflow the 64-pixel right boundary
            if current_x + 5 > 64:
                current_x = start_x       # Carriage return to left margin
                current_y += line_height  # Drop down to the next row
                
            # Draw the character at the current coordinates
            draw.text((current_x, current_y), char, fill=color)
            
            # Step forward by character width (5px) + tracking space
            current_x += 5 + char_spacing

async def main():
    try:
        matrix = create_matrix()
    except Exception as e:
        print(f"Matrix hardware connection failed: {e}")
        sys.exit(1)

    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    photo_slots = ["a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg", "f.jpg"]
    image_cache = {}
    
    # State Engine
    start_time = time.time()
    current_mode = 0  
    cycle_duration = 8.0  
    
    # Pre-compile the color tapestry tuple array (Word, RGB Color)
    tapestry_words = [
        ("SAFARI", (255, 50, 50)),       # Neon Red
        ("LAKE", (0, 235, 255)),         # Cyan
        ("JAMES", (0, 235, 255)),        # Cyan
        ("MUSEUM", (50, 255, 50)),       # Emerald Green
        ("TRAIN", (255, 0, 200)),        # Magenta
        ("BOAT", (255, 0, 200)),         # Magenta
        ("BASEBALL", (255, 140, 0)),     # Bright Orange
        ("FOAM", (200, 100, 255)),       # Electric Purple
        ("PARTY", (200, 100, 255)),      # Electric Purple
        ("CHOCOLATE", (255, 255, 255)),  # White
        ("PORK", (255, 100, 0)),         # Deep Amber
        ("BLUEBERRIES", (255, 230, 0))   # Laser Yellow
    ]
    
    print("Polished Wrapped Showcase Engine Active! Press Ctrl+C to stop.")
    
    while True:
        draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
        
        if time.time() - start_time > cycle_duration:
            image_cache.clear() # Clear memory map to automatically catch newly dropped files
            attempts = 0
            while attempts < 8:
                current_mode += 1
                total_possible_modes = 2 + len(photo_slots)
                if current_mode >= total_possible_modes:
                    current_mode = 0
                
                if current_mode < 2:
                    break
                    
                img_index = current_mode - 2
                filename = photo_slots[img_index]
                if os.path.exists(filename):
                    break  
                attempts += 1
                
            start_time = time.time()
            
        # --- SCREEN 0: RE-COLORED CLEAN THANK YOU DISPLAY ---
        if current_mode == 0:
            # Block A: Mint Green Greeting Tones
            mint_green = (0, 255, 150)
            # Custom character tracking built in manually: letter + spacing width
            for i, char in enumerate("THANK YOU"):
                draw.text((2 + (i * 7), 2), char, fill=mint_green)
            for i, char in enumerate("FOR VISITING!"):
                draw.text((2 + (i * 6), 12), char, fill=mint_green)
                
            # Block B: Electric Blue Family Signature Tones
            electric_blue = (0, 180, 255)
            for i, char in enumerate("LOVE,"):
                draw.text((2 + (i * 8), 28), char, fill=electric_blue)
            for i, char in enumerate("LEO,"):
                draw.text((2 + (i * 8), 38), char, fill=electric_blue)
            for i, char in enumerate("RACHEL,"):
                draw.text((2 + (i * 6), 46), char, fill=electric_blue)
            for i, char in enumerate("AND ERIC"):
                draw.text((2 + (i * 7), 54), char, fill=electric_blue)

        # --- SCREEN 1: SEAMLESS WRAPPING TRIP TAPESTRY ---
        elif current_mode == 1:
            # Flows all elements seamlessly together with custom uniform grid padding
            draw_wrapping_tapestry(
                draw, 
                word_color_list=tapestry_words, 
                start_x=1, 
                start_y=2, 
                char_spacing=1, # Consistent spacing between adjacent letters
                line_height=9   # Roomy line cushion preventing overlap
            )

        # --- SCREENS 2+: PHOTO SLOTS (a.jpg through f.jpg) ---
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

        matrix.SetImage(canvas)
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWelcome Engine closed successfully.")
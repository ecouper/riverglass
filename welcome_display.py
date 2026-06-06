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

# --- UNIFORM GRID TAPESTRY ENGINE ---
def draw_wrapping_tapestry(draw, word_color_list, start_x, start_y, char_step, line_height):
    """Flows differently colored words across lines with flawless, uniform grid character spacing."""
    current_x = start_x
    current_y = start_y
    
    for word, color in word_color_list:
        # Draw the letters of the word
        for char in word:
            # Wrap to next line if character block exceeds the right screen margin
            if current_x + 5 > 64:
                current_x = start_x
                current_y += line_height
            draw.text((current_x, current_y), char, fill=color)
            current_x += char_step
        
        # Draw a single space slot after the word using the EXACT same character step size
        if current_x + 5 > 64:
            current_x = start_x
            current_y += line_height
        # A space is blank, so we just advance current_x uniformly without drawing a character
        current_x += char_step

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
    
    # State Engine Setup
    start_time = time.time()
    current_mode = 0  
    cycle_duration = 8.0  
    
    # Pre-compiled layout colors for the Thank You page
    mint_green = (0, 255, 150)
    electric_blue = (0, 180, 255)
    
    thank_you_lines = [
        ("THANK YOU", mint_green),
        ("FOR", mint_green),
        ("VISITING!", mint_green),
        ("LOVE,", electric_blue),
        ("LEO,", electric_blue),
        ("RACHEL,", electric_blue),
        ("AND ERIC", electric_blue)
    ]
    
    # Pre-compiled list of words for the continuous crossword tapestry
    tapestry_words = [
        ("SAFARI", (255, 50, 50)),       
        ("LAKE", (0, 235, 255)),         
        ("JAMES", (0, 235, 255)),        
        ("MUSEUM", (50, 255, 50)),       
        ("TRAIN", (255, 0, 200)),        
        ("BOAT", (255, 0, 200)),         
        ("BASEBALL", (255, 140, 0)),     
        ("FOAM", (200, 100, 255)),       
        ("PARTY", (200, 100, 255)),      
        ("CHOCOLATE", (255, 255, 255)),  
        ("PORK", (255, 100, 0)),         
        ("BLUEBERRIES", (255, 230, 0))   
    ]
    
    print("Grid-Perfect Layout Engine Active! Press Ctrl+C to terminate.")
    
    while True:
        draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
        
        # Image cache clearing and look-ahead file loop matching the 8-second ceiling
        if time.time() - start_time > cycle_duration:
            image_cache.clear() 
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
            
        # --- SCREEN 0: GRID-PERFECT COHESIVE THANK YOU ---
        if current_mode == 0:
            char_step = 6      # Strict horizontal grid spacing width
            line_height = 9    # Flawless vertical spacing tracking across every single line
            
            for line_idx, (text, color) in enumerate(thank_you_lines):
                y_pos = 2 + (line_idx * line_height)
                for char_idx, char in enumerate(text):
                    x_pos = 2 + (char_idx * char_step)
                    draw.text((x_pos, y_pos), char, fill=color)

        # --- SCREEN 1: SEAMLESS WRAPPING CROSSWORD TAPESTRY ---
        elif current_mode == 1:
            draw_wrapping_tapestry(
                draw, 
                word_color_list=tapestry_words, 
                start_x=2, 
                start_y=2, 
                char_step=6,    # Matches horizontal alignment step perfectly
                line_height=9   # Matches vertical grid spacing exactly
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
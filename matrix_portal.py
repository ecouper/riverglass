import time
import sys
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont

def create_matrix():
    # Configure the hardware options to match your 64x64 setup
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    
    # Use the multiplexing mapping that gave you the sharpest image
    options.multiplexing = 1
    
    # Drop privileges to keep the Pi secure while running as root
    options.drop_privileges = False

    return RGBMatrix(options=options)

def main():
    try:
        # Initialize the physical screen
        matrix = create_matrix()
        
        # Create a blank digital canvas (RGB mode) matching our screen size
        canvas = Image.new("RGB", (64, 64))
        draw = ImageDraw.Draw(canvas)
        
        print("Press Ctrl+C to stop the matrix portal script.")
        
        while True:
            # Clear the canvas to pure black
            draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
            
            # --- LAYOUT ZONE ---
            # Draw a bright blue border around the outer edge
            draw.rectangle((0, 0, 63, 63), outline=(0, 0, 255))
            
            # Draw a simple test line of text
            # (Using default font for now, we will add crisp pixel fonts next!)
            draw.text((4, 8), "RIVER", fill=(255, 255, 255))
            draw.text((4, 20), "GLASS", fill=(0, 255, 0))
            
            # Draw a small animated red square that moves back and forth
            # This will help us test the screen refresh rate
            pulse = int((time.time() * 20) % 40)
            draw.rectangle((4 + pulse, 45, 12 + pulse, 53), fill=(255, 0, 0))
            # -------------------
            
            # Send our digital canvas to the physical LED panels
            matrix.SetImage(canvas)
            
            # Throttle the loop to ~30 frames per second to save CPU
            time.sleep(0.03)
            
    except KeyboardInterrupt:
        print("\nExiting and clearing matrix...")
        sys.exit(0)

if __name__ == "__main__":
    main()
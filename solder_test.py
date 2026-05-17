import time
import sys
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw

def create_matrix():
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    options.multiplexing = 1
    options.pixel_mapper_config = "Rotate:90"
    options.drop_privileges = False
    return RGBMatrix(options=options)

def main():
    try:
        matrix = create_matrix()
        canvas = Image.new("RGB", (64, 64))
        draw = ImageDraw.Draw(canvas)
        
        print("Solder test running! Press Ctrl+C to stop.")
        
        while True:
            # Clear the screen to pure black
            draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
            
            # Draw a solid white horizontal bar right across the middle of the canvas
            # (Row 32, scanning from column 0 all the way to column 63)
            draw.line((0, 32, 63, 32), fill=(255, 255, 255), width=3)
            
            # Send the image to the physical panel
            matrix.SetImage(canvas)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
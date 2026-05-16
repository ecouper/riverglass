import time
import sys
import sounddevice as sd
import numpy as np
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw

# --- HARDWARE CONFIGURATION ---
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

# --- AUDIO SETTINGS ---
# Targets 'plughw:1,0' directly by name matching Card 1
DEVICE_NAME = "hw:1,0"  
CHANNELS = 1
RATE = 44100          
CHUNK = 1024          

def main():
    try:
        matrix = create_matrix()
    except Exception as e:
        print(f"Error initializing matrix: {e}")
        sys.exit(1)

    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    NUM_BARS = 8
    peak_heights = [0] * NUM_BARS
    
    print("Audio visualizer running! Press Ctrl+C to exit.")

    # Open a direct hardware input stream using sounddevice
    try:
        stream = sd.InputStream(
            device=DEVICE_NAME,
            channels=CHANNELS,
            samplerate=RATE,
            blocksize=CHUNK,
            dtype='int16'
        )
        stream.start()
    except Exception as e:
        print(f"Hardware Audio Error: {e}")
        print("Verify your device with 'arecord -l'")
        sys.exit(1)

    try:
        while True:
            # 1. Read raw audio frames from the stream
            audio_data, overflowed = stream.read(CHUNK)
            if overflowed:
                continue
                
            # Flatten the array to 1D for math processing
            audio_data = audio_data.flatten()
            
            # 2. Run the FFT to extract frequencies
            fft_data = np.abs(np.fft.rfft(audio_data))
            
            # 3. Group frequencies into our 8 display bars
            bands = np.array_split(fft_data, NUM_BARS)
            bar_heights = []
            
            for i, band in enumerate(bands):
                amplitude = np.mean(band) if len(band) > 0 else 0
                
                # Scale amplitude to fit the 64-pixel high screen
                height = int(amplitude / 500)
                height = max(0, min(height, 60))
                
                if height < peak_heights[i]:
                    peak_heights[i] = max(0, peak_heights[i] - 3)
                else:
                    peak_heights[i] = height
                    
                bar_heights.append(peak_heights[i])

            # 4. Render graphics ONLY on working columns (1 and 3)
            draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
            
            SUB_BAR_WIDTH = 3
            SPACING = 1

            for i in range(NUM_BARS):
                h = bar_heights[i]
                
                if i < 4:
                    x0 = 0 + (i * (SUB_BAR_WIDTH + SPACING))
                else:
                    x0 = 32 + ((i - 4) * (SUB_BAR_WIDTH + SPACING))
                
                x1 = x0 + SUB_BAR_WIDTH - 1
                y0 = 63 - h  
                y1 = 63
                
                if i < 2:
                    color = (255, 0, 0)     # Bass
                elif i < 6:
                    color = (0, 255, 0)     # Mids
                else:
                    color = (0, 0, 255)     # Treble
                    
                if h > 0:
                    draw.rectangle((x0, y0, x1, y1), fill=color)

            matrix.SetImage(canvas)
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopping audio visualizer...")
    finally:
        stream.stop()
        stream.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
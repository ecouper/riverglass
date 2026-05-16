import time
import sys
import pyaudio
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
    
    # Use the multiplexing mapping that gave you the sharpest image
    options.multiplexing = 1
    
    # Rotate the canvas 90 degrees clockwise to match your physical orientation
    options.pixel_mapper_config = "Rotate:90"
    
    # Drop privileges to keep the Pi secure while running as root
    options.drop_privileges = False

    return RGBMatrix(options=options)

# --- AUDIO SETTINGS ---
# Matches the hardware card configuration: hw:1,0 -> Card 1
DEVICE_INDEX = 1  
CHANNELS = 1
RATE = 44100          # Standard audio sampling rate
CHUNK = 1024          # Number of audio frames per buffer read

def main():
    # Initialize Matrix
    try:
        matrix = create_matrix()
    except Exception as e:
        print(f"Error initializing matrix: {e}")
        sys.exit(1)

    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print(f"Error opening audio input device index {DEVICE_INDEX}: {e}")
        print("Double check your device index with 'arecord -l'")
        p.terminate()
        sys.exit(1)

    # Canvas Setup
    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    # We will map the audio into 8 vertical frequency bands (bars)
    NUM_BARS = 8
    
    # Keep track of previous peaks to create a smooth "falling dot" effect
    peak_heights = [0] * NUM_BARS
    
    print("Audio visualizer running! Press Ctrl+C to exit.")

    try:
        while True:
            # 1. Read raw binary audio data from the microphone stream
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
            except IOError:
                continue # Skip frame if audio buffer overflows momentarily
                
            # 2. Convert raw binary data to numerical audio wave arrays
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # 3. Run the Fast Fourier Transform (FFT) to extract frequencies
            fft_data = np.abs(np.fft.rfft(audio_data))
            
            # 4. Group the frequencies into our 8 visual display bars
            bands = np.array_split(fft_data, NUM_BARS)
            bar_heights = []
            
            for i, band in enumerate(bands):
                amplitude = np.mean(band) if len(band) > 0 else 0
                
                # Scale amplitude to fit our 64-pixel high screen
                # Adjust the 500 divider down if bars are too small, up if they max out easily
                height = int(amplitude / 500)
                height = max(0, min(height, 60))
                
                # Apply an ease-down decay so the bars glide smoothly instead of flickering
                if height < peak_heights[i]:
                    peak_heights[i] = max(0, peak_heights[i] - 3)
                else:
                    peak_heights[i] = height
                    
                bar_heights.append(peak_heights[i])

            # 5. Render the graphics ONLY on working hardware columns (1 and 3)
            draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0)) # Clear frame to pure black
            
            # Width of each individual bar and spacing between them
            SUB_BAR_WIDTH = 3
            SPACING = 1

            for i in range(NUM_BARS):
                h = bar_heights[i]
                
                # Split the 8 bars: first 4 go to Column 1, last 4 go to Column 3
                if i < 4:
                    # Column 1 starts at X=0 (Active zone: 0 to 15)
                    x0 = 0 + (i * (SUB_BAR_WIDTH + SPACING))
                else:
                    # Column 3 starts at X=32 (Active zone: 32 to 47)
                    x0 = 32 + ((i - 4) * (SUB_BAR_WIDTH + SPACING))
                
                x1 = x0 + SUB_BAR_WIDTH - 1
                y0 = 63 - h  # Rising up from the bottom edge (row 63)
                y1 = 63
                
                # Color spectrum mapping: Bass (Red), Mids (Green), Treble (Blue)
                if i < 2:
                    color = (255, 0, 0)     # Bass
                elif i < 6:
                    color = (0, 255, 0)     # Mids
                else:
                    color = (0, 0, 255)     # Treble
                    
                if h > 0:
                    draw.rectangle((x0, y0, x1, y1), fill=color)

            # 6. Update the physical LED matrix
            matrix.SetImage(canvas)
            
            # Tiny sleep to let the CPU breathe
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopping audio visualizer...")
    finally:
        # Clean shutdown of audio streams and engine
        stream.stop_stream()
        stream.close()
        p.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
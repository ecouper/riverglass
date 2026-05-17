import asyncio
import time
import sys
import numpy as np
import sounddevice as sd
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw

# --- HARDWARE MATRIX SETUP ---
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

# --- SYSTEM STATES ---
class RiverglassState:
    def __init__(self):
        self.current_mode = "WEATHER"  # Options: "WEATHER", "MUSIC"
        self.album_art_image = None    # Holds the downloaded PIL Image object
        self.current_song_id = None    # Tracks the currently playing track string
        self.weather_data = {"temp": "--", "condition": "Loading..."}
        self.is_running = True

system = RiverglassState()

# --- TASK 1: WEATHER & TIME UPDATER ---
async def weather_updater_task():
    """Background loop to fetch weather every 15 minutes and update local time."""
    print("Weather and Time engine initialized.")
    while system.is_running:
        try:
            # TODO: Integrate local weather API fetch here later
            system.weather_data["temp"] = "72°F"
            system.weather_data["condition"] = "Clear"
            
            # Sleep for 15 minutes between API calls
            await asyncio.sleep(900)
        except asyncio.CancelledError:
            break

# --- TASK 2: ACOUSTIC FINGERPRINTING ENGINE (THE 10-SEC LISTEN) ---
async def music_listener_task():
    """Wakes up every 10 seconds, samples audio, and identifies music."""
    print("Acoustic listening engine initialized.")
    
    # Audio sampling parameters
    device_index = 0
    sample_rate = 16000  # Most music ID APIs prefer 16kHz mono
    duration = 4        # Record a 4-second snippet to identify the song
    
    while system.is_running:
        # Wait 10 seconds before the next check loop
        await asyncio.sleep(10)
        
        print("Listening for music...")
        try:
            # Record audio non-blocking using sounddevice
            # We wrap sd.rec in an asyncio executor so it doesn't freeze the screen graphics
            loop = asyncio.get_event_loop()
            audio_snippet = await loop.run_in_executor(
                None, 
                lambda: sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16', device=device_index)
            )
            # Wait for the 4-second recording hardware buffer to fill cleanly
            await asyncio.sleep(duration) 
            
            # --- API SONG IDENTIFICATION LOGIC ---
            # TODO: Send 'audio_snippet' to AudD / Shazam API here
            detected_song = None  # Temporary placeholder simulating no music found
            
            if detected_song:
                if system.current_song_id != detected_song["id"]:
                    print(f"New song detected: {detected_song['title']}")
                    system.current_song_id = detected_song["id"]
                    # TODO: Download album art URL and convert to PIL Image
                    # system.album_art_image = downloaded_image
                    system.current_mode = "MUSIC"
            else:
                # No music heard, fall back to default weather view
                if system.current_mode == "MUSIC":
                    print("Music stopped. Reverting to weather view.")
                    system.current_song_id = None
                    system.album_art_image = None
                    system.current_mode = "WEATHER"
                    
        except Exception as e:
            print(f"Audio listening engine error: {e}")

# --- TASK 3: GRAPHICS RENDERING CORE ---
async def display_renderer_task(matrix):
    """Main rendering loop hitting the physical panel canvas at 30FPS."""
    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    print("Graphics rendering core active.")
    while system.is_running:
        # Clear frame
        draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
        
        if system.current_mode == "WEATHER":
            # --- DRAW WEATHER & CLOCK VIEW ---
            current_time = time.strftime("%I:%M")
            # Simple placeholder text graphics layout
            draw.text((4, 8), current_time, fill=(255, 255, 255))
            draw.text((4, 28), system.weather_data["temp"], fill=(0, 255, 255))
            draw.text((4, 44), system.weather_data["condition"], fill=(0, 255, 0))
            
            matrix.SetImage(canvas)
            
        elif system.current_mode == "MUSIC" and system.album_art_image:
            # --- DRAW ALBUM ART VIEW ---
            # Resize downloaded art to a perfect 64x64 square and blast it across the panel
            resized_art = system.album_art_image.resize((64, 64))
            matrix.SetImage(resized_art)
            
        else:
            # Fallback if mode is music but image hasn't loaded yet
            matrix.SetImage(canvas)
            
        # Run at ~30 frames per second
        await asyncio.sleep(0.03)

# --- MAIN ASYNC ORCHESTRATOR ---
async def main():
    try:
        matrix = create_matrix()
    except Exception as e:
        print(f"Matrix hardware connection failed: {e}")
        sys.exit(1)
        
    # Schedule all three loops to run completely independent and parallel
    try:
        await asyncio.gather(
            weather_updater_task(),
            music_listener_task(),
            display_renderer_task(matrix)
        )
    except KeyboardInterrupt:
        print("\nShutting down Riverglass framework cleanly...")
    finally:
        system.is_running = False

if __name__ == "__main__":
    asyncio.run(main())
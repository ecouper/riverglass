import asyncio
import time
import sys
import io
import wave
import aiohttp
import sounddevice as sd
import numpy as np
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
        self.current_mode = "WEATHER"  # "WEATHER" or "MUSIC"
        self.album_art_image = None    # Holds the active PIL Image object
        self.current_song_id = None    # Tracks unique song signature
        self.weather_data = {"temp": "72°F", "condition": "Clear"}
        self.is_running = True

system = RiverglassState()

# --- HELPER: CONVERT RAW AUDIO TO WAV BYTES ---
def convert_to_wav_bytes(audio_data, sample_rate):
    byte_io = io.BytesIO()
    with wave.open(byte_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit audio
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    return byte_io.getvalue()

# --- TASK 1: WEATHER & TIME UPDATER ---
async def weather_updater_task():
    print("Weather and Time engine initialized.")
    while system.is_running:
        try:
            # Placeholder for future live local weather integration
            system.weather_data["temp"] = "72°F"
            system.weather_data["condition"] = "Clear"
            await asyncio.sleep(900)
        except asyncio.CancelledError:
            break

# --- TASK 2: ACOUSTIC FINGERPRINTING ENGINE WITH SILENCE GUARD ---
async def music_listener_task():
    print("Acoustic listening engine initialized.")
    
    device_index = 0
    sample_rate = 44100  
    duration = 5  
    
    # Linked to your verified AudD account
    AUDD_API_TOKEN = "8f2f40bd8c4816ce7fd2ffea57676bab" 
    
    async with aiohttp.ClientSession() as session:
        while system.is_running:
            # Check for music every 10 seconds
            await asyncio.sleep(10)
            
            try:
                # 1. Record ambient room noise
                loop = asyncio.get_event_loop()
                audio_snippet = await loop.run_in_executor(
                    None, 
                    lambda: sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16', device=device_index)
                )
                await asyncio.sleep(duration)
                
                flattened_audio = audio_snippet.flatten()
                
                # 2. LOCAL VOLUME GUARD
                # Calculate Root-Mean-Square (RMS) amplitude to check ambient volume
                rms_volume = np.sqrt(np.mean(flattened_audio.astype(np.float32)**2))
                
                # If the room is fundamentally quiet, skip hitting the cloud entirely
                if rms_volume < 40.0:
                    if system.current_mode == "MUSIC":
                        print(f"Room is quiet (Vol: {rms_volume:.1f}). Reverting to weather view.")
                        system.current_song_id = None
                        system.album_art_image = None
                        system.current_mode = "WEATHER"
                    continue
                
                print(f"Audio detected (Vol: {rms_volume:.1f}). Querying AudD...")
                
                # 3. Pack and send to API
                wav_bytes = convert_to_wav_bytes(flattened_audio, sample_rate)
                
                data = aiohttp.FormData()
                data.add_field('api_token', AUDD_API_TOKEN)
                data.add_field('file', wav_bytes, filename='audio.wav', content_type='audio/wav')
                data.add_field('return', 'apple_music,spotify') 
                
                async with session.post('https://api.audd.io/', data=data) as response:
                    result = await response.json()
                    
                if result.get("status") == "success" and result.get("result"):
                    song_info = result["result"]
                    song_id = f"{song_info.get('artist')}-{song_info.get('title')}"
                    
                    # If it's a new song, download the artwork
                    if system.current_song_id != song_id:
                        print(f"🎵 Identified Track: {song_info.get('title')} by {song_info.get('artist')}")
                        system.current_song_id = song_id
                        
                        # Extract best high-res artwork URL available
                        art_url = None
                        if 'spotify' in song_info and song_info['spotify']:
                            images = song_info['spotify'].get('album', {}).get('images', [])
                            if images:
                                art_url = images[0].get('url')
                        if not art_url:
                            art_url = song_info.get('album', {}).get('cover_image')
                            
                        if art_url:
                            print(f"📥 Downloading artwork: {art_url}")
                            async with session.get(art_url) as img_resp:
                                if img_resp.status == 200:
                                    img_data = await img_resp.read()
                                    system.album_art_image = Image.open(io.BytesIO(img_data))
                                    system.current_mode = "MUSIC"
                else:
                    # Sound was heard but no music matched; drop back to weather after track ends
                    if system.current_mode == "MUSIC":
                        print("No music match found. Swapping back to weather mode.")
                        system.current_song_id = None
                        system.album_art_image = None
                        system.current_mode = "WEATHER"
                        
            except Exception as e:
                print(f"Audio listening engine error: {e}")

# --- TASK 3: GRAPHICS RENDERING CORE ---
async def display_renderer_task(matrix):
    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    print("Graphics rendering core active.")
    while system.is_running:
        draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
        
        if system.current_mode == "WEATHER":
            # Default Clock & Weather View
            current_time = time.strftime("%I:%M")
            draw.text((4, 4), current_time, fill=(255, 255, 255))
            draw.text((4, 24), system.weather_data["temp"], fill=(0, 255, 255))
            draw.text((4, 40), system.weather_data["condition"], fill=(0, 255, 0))
            matrix.SetImage(canvas)
            
        elif system.current_mode == "MUSIC" and system.album_art_image:
            # Scale and display real album artwork across the grid configuration
            resized_art = system.album_art_image.resize((64, 64))
            matrix.SetImage(resized_art)
        else:
            matrix.SetImage(canvas)
            
        await asyncio.sleep(0.03)

async def main():
    try:
        matrix = create_matrix()
    except Exception as e:
        print(f"Matrix hardware connection failed: {e}")
        sys.exit(1)
        
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
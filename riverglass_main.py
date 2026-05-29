import asyncio
import time
import sys
import io
import wave
import aiohttp
import sounddevice as sd
import numpy as np
from datetime import datetime
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw

# --- HARDWARE MATRIX SETUP ---
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
    
    # --- PERFORMANCE TUNING FOR ZERO 2 WH FLICKER ---
    options.gpio_slowdown = 4                 # Gives fast Pi Zero 2 WH clock stability
    options.pwm_bits = 7                      # Lightens single-core pin-flipping overhead
    
    
    return RGBMatrix(options=options)

# --- SYSTEM STATES ---
class RiverglassState:
    def __init__(self):
        self.current_mode = "WEATHER"  # "WEATHER" or "MUSIC"
        self.album_art_image = None    # Holds the active PIL Image object
        self.current_song_id = None    # Tracks unique song signature
        self.weather_data = {"temp": "72", "low": "54", "high": "88", "condition": "Clear"}
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

# --- TASK 1: LIVE WEATHER DATA FETCH ---
async def weather_updater_task():
    print("Weather data synchronization engine initialized.")
    while system.is_running:
        try:
            # Placeholder: Hook your local weather API provider here
            system.weather_data["temp"] = "72"
            system.weather_data["low"] = "54"
            system.weather_data["high"] = "88"
            system.weather_data["condition"] = "Clear"  # Options: Clear, Cloudy, Rainy
            await asyncio.sleep(900)
        except asyncio.CancelledError:
            break

# --- TASK 2: ADAPTIVE ACOUSTIC ENGINE + DSP SPEECH FILTER ---
async def music_listener_task():
    print("Adaptive acoustic fingerprinting engine initialized.")
    
    device_index = 0
    sample_rate = 44100  
    duration = 4  # Total 4-second listening window
    
    # Slice parameters for time-domain speech filtering
    num_slices = 8
    slice_length = int((duration * sample_rate) / num_slices) # 22,050 samples per 0.5s chunk
    hardware_noise_floor = 15.0  # Calibrated above your 340.0 room-hum baseline
    
    AUDD_API_TOKEN = "8f2f40bd8c4816ce7fd2ffea57676bab" 
    
    async with aiohttp.ClientSession() as session:
        while system.is_running:
            current_hour = datetime.now().hour
            
            # 1. NIGHTTIME CURFEW GUARD (11:00 PM - 9:00 AM)
            if current_hour >= 23 or current_hour < 9:
                if system.current_mode == "MUSIC":
                    print("Nighttime curfew active. Forcing display into Weather Mode.")
                    system.current_song_id = None
                    system.album_art_image = None
                    system.current_mode = "WEATHER"
                await asyncio.sleep(60)
                continue
            
            # VARIABLE REFRESH CONTROL: 8s if searching, 30s if cruising on active track
            sleep_interval = 30 if system.current_mode == "MUSIC" else 8
            await asyncio.sleep(sleep_interval)
            
            try:
                # 2. RECORD SNIPPET (Bypass explicit device mapping to clear the root freeze)
                loop = asyncio.get_event_loop()
                audio_snippet = await loop.run_in_executor(
                    None, 
                    lambda: sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
                )
                await asyncio.sleep(duration)
                flattened_audio = audio_snippet.flatten()
                
                # 3. ADVANCED DSP: MULTI-SLICE TIME VARIANCE ANALYSIS (SPEECH VS MUSIC)
                silent_slices_count = 0
                
                for i in range(num_slices):
                    start_idx = i * slice_length
                    end_idx = start_idx + slice_length
                    slice_data = flattened_audio[start_idx:end_idx].astype(np.float32)
                    
                    # --- THE DC OFFSET REMOVAL ---
                    # Subtract the mean to center the audio wave perfectly on 0
                    zero_centered_slice = slice_data - np.mean(slice_data)
                    
                    # Calculate the true RMS of just the audio movement
                    slice_rms = np.sqrt(np.mean(zero_centered_slice**2))
                    
                    if slice_rms < hardware_noise_floor:
                        silent_slices_count += 1

                # If the room has dynamic gaps (like talking/TV dialogue), drop it
                # Max 1 empty slice allowed (to handle brief song transitions or ambient drops)
                if silent_slices_count > 1:
                    if system.current_mode == "MUSIC" and silent_slices_count >= 6:
                        print(f"Room fell silent or track ended ({silent_slices_count}/{num_slices} empty slices). Reverting to weather.")
                        system.current_song_id = None
                        system.album_art_image = None
                        system.current_mode = "WEATHER"
                    else:
                        print(f"Speech/TV dynamic dialogue detected ({silent_slices_count}/{num_slices} empty slices). Discarding block.")
                    continue
                
                # Total overall window volume check for sanity
                total_rms = np.sqrt(np.mean(flattened_audio.astype(np.float32)**2))
                print(f"Valid continuous music confirmed (Vol: {total_rms:.1f}, Gaps: {silent_slices_count}/{num_slices}). Querying AudD API...")
                
                # 4. API COOLDOWN TRANSMIT
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
                    
                    if system.current_song_id != song_id:
                        print(f"🎵 Track Identified: {song_info.get('title')} by {song_info.get('artist')}")
                        system.current_song_id = song_id
                        
                        art_url = None
                        if 'spotify' in song_info and song_info['spotify']:
                            images = song_info['spotify'].get('album', {}).get('images', [])
                            if images:
                                art_url = images[0].get('url')
                        if not art_url:
                            art_url = song_info.get('album', {}).get('cover_image')
                            
                        if art_url:
                            async with session.get(art_url) as img_resp:
                                if img_resp.status == 200:
                                    img_data = await img_resp.read()
                                    system.album_art_image = Image.open(io.BytesIO(img_data))
                                    system.current_mode = "MUSIC"
                else:
                    # Clear visual cue when the API scans but doesn't find a fingerprint match
                    if system.current_mode == "MUSIC":
                        print("Track boundary or unknown audio source hit. Reverting to weather.")
                        system.current_song_id = None
                        system.album_art_image = None
                        system.current_mode = "WEATHER"
                    else:
                        print("AudD API scanned successfully, but no matching song fingerprint was discovered.")

            except Exception as e:
                print(f"Audio processing engine error: {e}")

# --- TASK 3: GRAPHICS RENDERING CORE ---
async def display_renderer_task(matrix):
    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    print("Graphics rendering core active.")
    while system.is_running:
        draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
        
        if system.current_mode == "WEATHER":
            condition = system.weather_data["condition"]
            
            # --- PROCEDURAL VECTOR WEATHER ICON GENERATOR (Top 4/5ths) ---
            if condition == "Clear":
                # Draw sharp vector yellow sun disk and beams
                draw.ellipse([22, 12, 42, 32], fill=(255, 215, 0))
                draw.line([32, 4, 32, 9], fill=(255, 215, 0), width=1)
                draw.line([32, 35, 32, 40], fill=(255, 215, 0), width=1)
                draw.line([14, 22, 19, 22], fill=(255, 215, 0), width=1)
                draw.line([45, 22, 50, 22], fill=(255, 215, 0), width=1)
            elif condition == "Cloudy":
                # Overlapping vector geometric cloud puffs
                draw.ellipse([14, 20, 28, 34], fill=(180, 180, 180))
                draw.ellipse([22, 14, 42, 34], fill=(220, 220, 220))
                draw.ellipse([36, 18, 50, 34], fill=(180, 180, 180))
                draw.rectangle([20, 26, 44, 34], fill=(200, 200, 200))
            elif condition == "Rainy":
                # Cloud baseline with geometric rain streaks dropping down
                draw.ellipse([20, 14, 44, 30], fill=(130, 130, 130))
                draw.line([24, 34, 22, 40], fill=(0, 150, 255), width=1)
                draw.line([32, 34, 30, 40], fill=(0, 150, 255), width=1)
                draw.line([40, 34, 38, 40], fill=(0, 150, 255), width=1)
            
            # --- TRI-COLOR TEMPERATURE DISPLAY BANNER (Bottom 1/5th) ---
            # Columns calibrated horizontally across 64 pixels to avoid overlaps
            draw.text((2, 52),  f"{system.weather_data['temp']}", fill=(255, 255, 0))   # Yellow (Current)
            draw.text((24, 52), f"{system.weather_data['low']}",  fill=(0, 150, 255))  # Blue (Daily Low)
            draw.text((46, 52), f"{system.weather_data['high']}", fill=(255, 50, 50))   # Red (Daily High)
            
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
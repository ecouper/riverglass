import asyncio
import aiohttp
import sounddevice as sd
import numpy as np
import io
import wave

# --- AUDIO & API CONFIGURATION ---
DEVICE_INDEX = 0
SAMPLE_RATE = 44100
DURATION = 5  # Seconds to record

# ⚠️ PASTE YOUR COPIED API TOKEN HERE:
AUDD_API_TOKEN = "8f2f40bd8c4816ce7fd2ffea57676bab" 

def convert_to_wav_bytes(audio_data, sample_rate):
    byte_io = io.BytesIO()
    with wave.open(byte_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit audio
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    return byte_io.getvalue()

async def test_identification():
    if AUDD_API_TOKEN == "YOUR_ACTUAL_API_TOKEN_HERE":
        print("❌ Error: Please update the AUDD_API_TOKEN variable with your real token first!")
        return

    print(f"🎙️ Recording {DURATION} seconds of audio from the room... Play a song now!")
    
    # Capture raw audio
    loop = asyncio.get_event_loop()
    audio_snippet = await loop.run_in_executor(
        None, 
        lambda: sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=DEVICE_INDEX)
    )
    await asyncio.sleep(DURATION)
    
    print("📦 Processing audio and sending to AudD servers...")
    wav_bytes = convert_to_wav_bytes(audio_snippet.flatten(), SAMPLE_RATE)
    
    # Build payload
    data = aiohttp.FormData()
    data.add_field('api_token', AUDD_API_TOKEN)
    data.add_field('file', wav_bytes, filename='audio.wav', content_type='audio/wav')
    # Request Spotify/Apple music metadata layouts to get high-res images
    data.add_field('return', 'apple_music,spotify') 

    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.audd.io/', data=data) as response:
            result = await response.json()
            
    print("\n--- API RESPONSE RESULT ---")
    if result.get("status") == "success" and result.get("result"):
        song_info = result["result"]
        print(f"🎵 SUCCESS! Track Found!")
        print(f"   Title:  {song_info.get('title')}")
        print(f"   Artist: {song_info.get('artist')}")
        print(f"   Album:  {song_info.get('album')}")
        
        # Pull the best high-res artwork URL available
        art_url = None
        if 'spotify' in song_info and song_info['spotify']:
            images = song_info['spotify'].get('album', {}).get('images', [])
            if images:
                art_url = images[0].get('url') # Spotify high-res square image
                
        if not art_url:
            art_url = song_info.get('album', {}).get('cover_image')
            
        print(f"🖼️ Album Art URL: {art_url}")
    else:
        print("❌ Match Failed or Room was Silent.")
        print(f"   Server Response: {result}")

if __name__ == "__main__":
    asyncio.run(test_identification())
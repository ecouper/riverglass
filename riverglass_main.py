import asyncio
import sys
import os
import io
import aiohttp
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
    options.gpio_slowdown = 4                 # Gives fast Pi Zero 2 WH clock stability
    options.pwm_bits = 7                      # Lightens single-core pin-flipping overhead
    return RGBMatrix(options=options)

# --- SYSTEM STATES ---
class RiverglassState:
    def __init__(self):
        self.weather_data = {"temp": "--", "low": "--", "high": "--", "condition": "clear"}
        self.is_running = True

system = RiverglassState()

# --- TASK 1: LIVE WEATHER DATA FETCH (OPENWEATHERMAP) ---
async def weather_updater_task():
    print("OpenWeatherMap synchronization engine initialized.")
    
    API_KEY = "b4d97d57f1f3ed1e0e683fad8fd06794"
    LAT = "35.9940"  # Durham, NC
    LON = "-78.8986"
    URL = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=imperial"
    
    async with aiohttp.ClientSession() as session:
        while system.is_running:
            try:
                async with session.get(URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        current_temp = round(data["main"]["temp"])
                        temp_min = round(data["main"]["temp_min"])
                        temp_max = round(data["main"]["temp_max"])
                        
                        main_cond = data["weather"][0]["main"]
                        if main_cond in ["Clear"]:
                            condition = "clear"
                        elif main_cond in ["Clouds"]:
                            condition = "cloudy"
                        elif main_cond in ["Rain", "Drizzle", "Thunderstorm"]:
                            condition = "rainy"
                        elif main_cond in ["Snow"]:
                            condition = "snowy"
                        else:
                            condition = "cloudy"
                        
                        system.weather_data["temp"] = str(current_temp)
                        system.weather_data["low"] = str(temp_min)
                        system.weather_data["high"] = str(temp_max)
                        system.weather_data["condition"] = condition
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Live Weather Cached: {current_temp}°F, {condition}")
                    else:
                        print(f"Weather API Error: HTTP Status {response.status}")
            except Exception as e:
                print(f"Weather sync connection drop: {e}")
                
            await asyncio.sleep(600)

# --- TASK 2: IMAGE-BASED GRAPHICS RENDERING CORE ---
async def display_renderer_task(matrix):
    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    icon_cache = {}
    icon_size = (32, 32)  # Dynamically tuned for your specific 32x32 assets
    
    print("Graphics rendering core active (32x32 Asset Engine).")
    while system.is_running:
        # Clear back canvas to pure unlit black
        draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
        
        condition = system.weather_data["condition"]
        filename = f"{condition}.png"
        
        if filename not in icon_cache:
            if os.path.exists(filename):
                try:
                    # Open with RGBA to carefully track the transparent mask
                    raw_img = Image.open(filename).convert("RGBA")
                    
                    # Create a solid black background layer matching the icon size
                    backdrop = Image.new("RGB", raw_img.size, (0, 0, 0))
                    # Flatten the transparency safely over the black background
                    backdrop.paste(raw_img, (0, 0), raw_img)
                    
                    # Cache it precisely scaled to 32x32 using clean pixel matching
                    icon_cache[filename] = backdrop.resize(icon_size, Image.Resampling.NEAREST)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    icon_cache[filename] = None
            else:
                icon_cache[filename] = None
        
        # Paste the asset centered horizontally: (64 wide - 32 icon wide) / 2 = 16 left offset
        # Set 4 pixels down from the very top to optimize breathing room
        cached_icon = icon_cache.get(filename)
        if cached_icon:
            canvas.paste(cached_icon, (16, 4))
        else:
            # Subtle minimal indicator loop if file is missing
            draw.ellipse([29, 17, 35, 23], fill=(40, 40, 40))

        # --- LIVE TYPOGRAPHY BANNER ---
        # Adjusted rendering floor slightly lower to maximize separation from 32x32 icon box
        draw.text((4, 50), f"{system.weather_data['temp']}°", fill=(255, 215, 0))
        draw.text((34, 46), f"H {system.weather_data['high']}", fill=(255, 60, 60))
        draw.text((34, 54), f"L {system.weather_data['low']}", fill=(0, 160, 255))
        
        matrix.SetImage(canvas)
        await asyncio.sleep(0.1)

async def main():
    try:
        matrix = create_matrix()
    except Exception as e:
        print(f"Matrix hardware connection failed: {e}")
        sys.exit(1)
        
    try:
        await asyncio.gather(
            weather_updater_task(),
            display_renderer_task(matrix)
        )
    except KeyboardInterrupt:
        print("\nShutting down Riverglass Dashboard cleanly...")
    finally:
        system.is_running = False

if __name__ == "__main__":
    asyncio.run(main())
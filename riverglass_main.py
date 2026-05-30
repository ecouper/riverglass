import asyncio
import sys
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
    
    # --- PERFORMANCE TUNING FOR ZERO 2 WH FLICKER ---
    options.gpio_slowdown = 4                 # Gives fast Pi Zero 2 WH clock stability
    options.pwm_bits = 7                      # Lightens single-core pin-flipping overhead
    
    return RGBMatrix(options=options)

# --- SYSTEM STATES ---
class RiverglassState:
    def __init__(self):
        self.weather_data = {"temp": "--", "low": "--", "high": "--", "condition": "Clear"}
        self.is_running = True

system = RiverglassState()

# --- TASK 1: LIVE WEATHER DATA FETCH (OPENWEATHERMAP) ---
async def weather_updater_task():
    print("OpenWeatherMap synchronization engine initialized.")
    
    API_KEY = "b4d97d57f1f3ed1e0e683fad8fd06794"
    # Hardcoded for Durham, NC coordinates
    LAT = "35.9940"
    LON = "-78.8986"
    URL = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=imperial"
    
    async with aiohttp.ClientSession() as session:
        while system.is_running:
            try:
                async with session.get(URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract main metrics
                        current_temp = round(data["main"]["temp"])
                        temp_min = round(data["main"]["temp_min"])
                        temp_max = round(data["main"]["temp_max"])
                        
                        # Map OpenWeatherMap condition codes to our vector generator categories
                        main_cond = data["weather"][0]["main"]
                        if main_cond in ["Clear"]:
                            condition = "Clear"
                        elif main_cond in ["Clouds"]:
                            condition = "Cloudy"
                        elif main_cond in ["Rain", "Drizzle", "Thunderstorm"]:
                            condition = "Rainy"
                        elif main_cond in ["Snow"]:
                            condition = "Snowy"
                        else:
                            condition = "Cloudy"  # Fallback safety
                        
                        system.weather_data["temp"] = str(current_temp)
                        system.weather_data["low"] = str(temp_min)
                        system.weather_data["high"] = str(temp_max)
                        system.weather_data["condition"] = condition
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Weather Synced: {current_temp}°F, {condition}")
                    else:
                        print(f"Weather API Error: HTTP Status {response.status}")
                        
            except Exception as e:
                print(f"Weather sync connection drop: {e}")
                
            # Refresh every 10 minutes to stay accurate without hitting API limits
            await asyncio.sleep(600)

# --- TASK 2: MODERN GRAPHICS RENDERING CORE ---
async def display_renderer_task(matrix):
    canvas = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(canvas)
    
    print("Graphics rendering core active.")
    while system.is_running:
        # Clear background to crisp black
        draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0))
        
        condition = system.weather_data["condition"]
        
        # --- MODERN PROCEDURAL VECTOR ICON SET ---
        if condition == "Clear":
            # Sharp modern sun architecture
            draw.ellipse([22, 12, 42, 32], fill=(255, 200, 0)) # Sun core
            # Symmetrical clean accent lines
            draw.line([32, 4, 32, 9], fill=(255, 160, 0), width=1)
            draw.line([32, 35, 32, 40], fill=(255, 160, 0), width=1)
            draw.line([14, 22, 19, 22], fill=(255, 160, 0), width=1)
            draw.line([45, 22, 50, 22], fill=(255, 160, 0), width=1)
            
        elif condition == "Cloudy":
            # Sleek layered flat-design cloud compilation
            draw.ellipse([14, 20, 28, 34], fill=(100, 110, 120))  # Left base puff
            draw.ellipse([34, 18, 48, 32], fill=(120, 130, 140))  # Right puff
            draw.ellipse([20, 14, 40, 34], fill=(160, 170, 180))  # Main center cap
            draw.rectangle([20, 24, 42, 34], fill=(160, 170, 180)) # Bottom joiner
            
        elif condition == "Rainy":
            # Dark slate cloud foundation
            draw.ellipse([18, 12, 32, 26], fill=(70, 80, 90))
            draw.ellipse([28, 10, 44, 26], fill=(90, 100, 110))
            draw.rectangle([22, 18, 40, 26], fill=(90, 100, 110))
            # Precise neon vertical rain streaks
            draw.line([24, 30, 24, 35], fill=(0, 180, 255), width=1)
            draw.line([32, 32, 32, 37], fill=(0, 140, 255), width=1)
            draw.line([40, 29, 40, 34], fill=(0, 180, 255), width=1)
            
        elif condition == "Snowy":
            # Soft gray cloud shelf
            draw.ellipse([20, 12, 44, 26], fill=(110, 120, 130))
            # Minimal geometric falling ice points
            draw.point([24, 32], fill=(240, 248, 255))
            draw.point([32, 35], fill=(255, 255, 255))
            draw.point([40, 31], fill=(240, 248, 255))

        # --- MODERN ALIGNED WEATHER TYPOGRAPHY BANNER ---
        # Current temp showcased prominently in bold yellow
        draw.text((4, 50), f"{system.weather_data['temp']}°", fill=(255, 230, 0))
        
        # High and Low grouped cleanly on the right hand side
        draw.text((32, 46), f"H:{system.weather_data['high']}", fill=(255, 70, 70))
        draw.text((32, 54), f"L:{system.weather_data['low']}", fill=(0, 180, 255))
        
        # Swap hardware matrix framework display pipeline
        matrix.SetImage(canvas)
        await asyncio.sleep(0.05) # Silky smooth 20 FPS refresh ceiling

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
        print("\nShutting down Riverglass Weather Dashboard cleanly...")
    finally:
        system.is_running = False

if __name__ == "__main__":
    asyncio.run(main())
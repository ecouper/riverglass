import tkinter as tk
import requests
import time

# --- CONFIGURATION ---
API_KEY = "b4d97d57f1f3ed1e0e683fad8fd06794"  # Use your OpenWeatherMap Key
CITY = "Durham,US"
# ---------------------

def get_durham_data():
    """Fetches real-time weather and metadata."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=imperial"
        response = requests.get(url)
        data = response.json()
        
        # This is the magic line! It will show the error message in the terminal.
        if response.status_code != 200:
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return {"error": data.get('message', 'API Error')}

        main_weather = data['weather'][0]['main']
        temp = data['main']['temp']

        return {
            "weather": main_weather,
            "temp": temp,
            "is_night": is_night,
            "error": None
        }
    except Exception as e:
        return {"error": str(e)}

def run_emulator():
    root = tk.Tk()
    root.title("Riverglass 64x64 Debug Portal")

    # Emulator Settings
    GRID_SIZE = 64
    PIXEL_SPACING = 7  
    LED_RADIUS = 3.0    # Smaller radius to make the 'pixels' distinct

    canvas_dim = GRID_SIZE * PIXEL_SPACING
    # We add 100 pixels of height at the bottom for our debug text
    canvas = tk.Canvas(root, width=canvas_dim, height=canvas_dim + 100, bg="black")
    canvas.pack()

    def update_display():
        canvas.delete("all")
        
        # 1. Get Data
        info = get_durham_data()
        
        if info.get("error"):
            vibe_color = "#FF0000" # Red if there is an error
            display_text = f"Error: {info['error']}"
        else:
            # 2. Force Amber Logic (No Teal)
            if info["is_night"]:
                vibe_color = "#4D3900" # Dim Amber
                time_status = "Night"
            else:
                vibe_color = "#FFBF00" # Bright Amber
                time_status = "Day"
            
            display_text = f"Durham: {info['weather']} | {info['temp']}F | Mode: {time_status}"

        # 3. Draw 64x64 Pixel Grid
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = col * PIXEL_SPACING + (PIXEL_SPACING // 2)
                y = row * PIXEL_SPACING + (PIXEL_SPACING // 2)
                canvas.create_oval(
                    x - LED_RADIUS, y - LED_RADIUS,
                    x + LED_RADIUS, y + LED_RADIUS,
                    fill=vibe_color, outline=""
                )
        
        # 4. Draw Debug Text underneath the grid
        canvas.create_text(
            canvas_dim // 2, canvas_dim + 50,
            text=display_text, fill="white", font=("Courier", 14)
        )

        # Refresh every 30 seconds for testing
        root.after(30000, update_display)

    update_display()
    root.mainloop()

if __name__ == "__main__":
    run_emulator()
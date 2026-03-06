# LILA BLACK Operational Viewer

This project is a visual dashboard for analyzing match data from the game LILA BLACK. It uses player data to show how people move, where they fight, and how matches play out on the map.

## What it Does
- **Interactive Map:** View player movements over time using a simple slider.
- **Combat Tracking:** See exactly where and when combat events happen.
- **Data Filtering:** Sort through match logs to find specific players or events.
- **Fast Performance:** Uses Parquet files to handle large amounts of match data quickly.

## Built With
- **Python:** The core language used for data processing.
- **Streamlit:** Creates the web interface and dashboard.
- **Pandas:** Manages the player tables and game statistics.
- **Plotly:** Powers the interactive map and data points.

## Project Structure
- `app.py`: The main script that runs the dashboard.
- `player_data/`: The folder where the match files are stored.
- `requirements.txt`: A list of the Python tools needed to run this app.

## How to Setup
1. **Clone the project** to your computer.
2. **Install the tools** by typing this in your terminal:
   `pip install -r requirements.txt`
3. **Run the dashboard** with this command:
   `streamlit run app.py`

## Future Plans
- Add a search bar to find specific players by name.
- Improve the map to show heights and vertical movement.
- Add automatic detection for players moving too fast or through walls.
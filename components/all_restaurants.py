from shiny import ui
import pandas as pd

def all_restaurants_card(csv_path):
    # Read the CSV file
    data = pd.read_csv(csv_path)
    
    # Create a grid layout to display the table
    rows = []
    for _, row in data.iterrows():
        cells = [ui.column(2, ui.p(str(value))) for value in row]
        rows.append(ui.row(*cells))
    
    # Return the grid layout
    return ui.div(*rows)
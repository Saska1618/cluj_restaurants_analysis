from shiny import App, ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mplcursors

from places_api.restaurants import ClujRestaurants, Restaurant
from credentials.credentials_provider import get_gplaces_api_key

API_KEY = get_gplaces_api_key()
data_file = './data/google_restaurants.csv'

locations = [
        "46.770439,23.591423",
]

locations_long = [
    "46.770439,23.591423",  # Central Cluj-Napoca
    "46.785,23.590",        # Slightly north
    "46.755,23.590",        # Slightly south
    "46.770,23.630",        # Slightly east
    "46.760,23.550",        # Slightly west
]
radius = 1000

restaurants = ClujRestaurants(api_key=API_KEY, locations=locations_long, radius=radius)

ROWS_PER_PAGE = 10

app_ui = ui.page_navbar(  
    ui.nav_panel(
        "All restaurants", 

        ui.row(
            ui.column(
                7, 
                ui.card(
                    "All the collected restaurants:",
                    ui.output_data_frame("restaurants_table"),
                    ui.column(3,
                        ui.input_action_button("refresh_btn", "Refresh Data")      
                    )
                    
                )
                
            ),

            ui.column(
                5, 
                ui.card(

                    ui.tags.style("""
                        .nav-pills .nav-link {
                            background-color: white;
                            color: black;
                            border: none;
                        }
                        .nav-pills .nav-link.active {
                            background-color: white;  /* Darker shade for active tab */
                            color: black;
                            border: 1px solid #333;
                            border-radius: 12px;
                        }
                        .nav-link:hover{
                            color: black;
                        }
                    """),

                    ui.navset_pill(
                        ui.nav_panel(
                            "Rating histogram",
                            ui.card(ui.output_plot("pie_chart_ratings")),
                        ),
                        ui.nav_panel(
                            "Distance/Rating",
                            ui.card(ui.output_plot("regression_dr"))
                        )
                    )
        
                )
            )
        )
    ),  

    ui.nav_panel("Get specific", "Details about one restaurant"),  

    ui.nav_panel("Clustering", "Clustered restaurants"),

    title="Cluj Restaurants",  
    id="page",  
)  


def server(input, output, session):
    
    @render.data_frame
    @reactive.event(input.refresh_btn, ignore_none=False)
    def restaurants_table():

        print("Loading the data")
        restaurants.fetch_restaurants()
        restaurants.export_to_csv(data_file)
        print("The data is loaded")

        # Load the CSV data
        df = pd.read_csv(data_file)

        # Remove the 'reviews' column if it exists
        if 'Reviews' in df.columns:
            df = df.drop(columns=['Reviews', 'Place ID'])

        # Add an 'index' column and move it to the leftmost position
        df['index'] = [i for i in range(1, len(df) + 1)]
        df = df[['index'] + [col for col in df.columns if col != 'index']]

        # Return the DataFrame as a DataGrid for display
        return render.DataGrid(df, selection_mode="rows", filters=True)
    
    @render.plot
    @reactive.event(input.refresh_btn, ignore_none=False)
    def pie_chart_ratings():
        #print("olvasom")
        df = pd.read_csv(data_file)

        # Create custom bins from 3.0 to 5.0 with a step of 0.1
        bins = [x / 10.0 for x in range(10, 52)]  # This will create bins: [3.0, 3.1, 3.2, ..., 5.0]

        fig, ax = plt.subplots()

        # Plot the histogram with custom bins
        ax.hist(df['Rating'], bins=bins, edgecolor='black', alpha=0.7)

        # Set the labels and title
        ax.set_xlabel('Rating')
        ax.set_ylabel('Count')
        ax.set_title('Distribution of Ratings')

        # Set the x-axis ticks to match the bins (so each rating is clearly labeled)
        ax.set_xticks(bins)
        ax.set_xticklabels([f'{x:.1f}' for x in bins], fontsize=6)

        plt.xticks(rotation=90)

        # Show the histogram
        return fig
    
    
    @render.plot
    @reactive.event(input.refresh_btn, ignore_none=False)
    def regression_dr():
        # Read the CSV data
        df = pd.read_csv(data_file)

        # Check if the necessary columns exist
        if 'Distance from Center' not in df.columns or 'Rating' not in df.columns:
            print("Error: Required columns not found in the data.")
            return None  # Return None if the required columns are missing

        # Extract the distance and rating data
        distances = df['Distance from Center']  # Remove any NaN values
        ratings = df['Rating']  # Remove any NaN values
        restaurant_names = df['Name']  # Assuming the column 'Name' contains restaurant names

        # Create the plot
        fig, ax = plt.subplots(figsize=(8, 6))

        # Scatter plot
        scatter = ax.scatter(distances, ratings, alpha=0.7, color='blue')

        # Set the labels and title
        ax.set_xlabel('Distance from City Center (km)', fontsize=12)
        ax.set_ylabel('Restaurant Rating', fontsize=12)
        ax.set_title('Distance vs Restaurant Rating', fontsize=14)

        # Add a regression line
        sns.regplot(x=distances, y=ratings, ax=ax, scatter=False)

        # Add hover functionality with mplcursors
        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(
            f"Name: {restaurant_names.iloc[sel.index]}\n"
            f"Distance: {distances.iloc[sel.index]} km\n"
            f"Rating: {ratings.iloc[sel.index]}"
        ))

        # Show the plot
        return fig


app = App(app_ui, server)
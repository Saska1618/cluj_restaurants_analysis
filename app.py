from shiny import App, ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.cluster import KMeans

import plotly.express as px
import numpy as np

import json
import os

import plotly.graph_objects as go

from places_api.restaurants import ClujRestaurants, Restaurant
from credentials.credentials_provider import get_gplaces_api_key
from webscraping.scraper import scrape_restaurant_data

ability_to_load_data = False

API_KEY = get_gplaces_api_key()
#data_file = './data/google_restaurants.csv'
data_file = './data/merged_data.csv'

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
                        ui.input_action_button("refresh_btn", "Refresh Data"),
                        #ui.input_action_button("scrape_data", "Scrape Data")      
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

    ui.nav_panel(
        "Get specific", 
        ui.row(
            ui.column(
                6,
                ui.card(
                    "Search for a restaurant:",
                    ui.card(
                        ui.row(
                            ui.column(
                                6,
                                ui.tags.style("""
                                    .btn{
                                        width: 300px;
                                    }
                                    """),
                                    ui.input_text("search_query", "", placeholder="Type a restaurant name", value="bulga"),
                                    ui.input_action_button("search_btn", "Search"
                                )
                            ),
                            ui.column(
                                6,
                                ui.card(
                                    "Employee number",
                                    ui.output_text("employee_num")
                                )
                            )
                            
                        )
                        
                    ),
                    ui.card(
                        "Name",
                        ui.output_text("name_name")
                    ),
                    ui.card(
                        "Rating",
                        ui.output_text("rating_rating")
                    ),
                    ui.card(
                        "Address",
                        ui.output_text("address_address")
                    ),
                    ui.card(
                        "Distance",
                        ui.output_text("distance_distance")
                    ),
                    
                    
                )
            ),
            ui.column(
                6,
                ui.card(
                    "Restaurant Reviews",
                    ui.output_ui("restaurant_details"),
                    ui.output_plot("restaurant_reviews_plot")
                )
            )
        )
    ), 

    ui.nav_panel(
        "Clustering",
        ui.card(
            ui.row(
                ui.column(
                    2,
                    ui.card(
                        "Select Number of Clusters:",
                        ui.input_slider("num_clusters", "Number of Clusters", min=2, max=7, value=3)
                    )
                ),
                ui.column(
                    10,
                    ui.tags.style("""
                        .scene{
                            height: 500px !important;
                        }
                    """),
                    ui.card(
                        "Clustering Results",
                        ui.output_ui("clustering_plot")
                    ),
                )
            )
            
            
        )
    ),

    title="Cluj Restaurants",  
    id="page",  
)  


def server(input, output, session):
    
    @render.data_frame
    @reactive.event(input.refresh_btn, ignore_none=False)
    def restaurants_table():

        json_file_path = './data/reviews_with_emotions_google.json'

        if ability_to_load_data:
            print("Loading the data")
            if os.path.exists(json_file_path):
               # Delete the file
               os.remove(json_file_path)
            restaurants.fetch_restaurants()
            restaurants.export_to_csv(data_file)
            restaurants.scrape_employee_data()
            restaurants.merge_csvs(restaurant_csv="./data/google_restaurants.csv", employee_csv="./data/employee_data.csv", merged_csv='./data/merged_data.csv')
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

        # Show the plot
        return fig
    
    @render.ui
    @reactive.event(input.search_btn, ignore_none=False)
    def restaurant_details():
        # Load the JSON data
        with open('./data/reviews_with_emotions_google.json', 'r', encoding='utf-8') as file:
            reviews_data = json.load(file)

        query = input.search_query().strip().lower()

        # Filter reviews for restaurants that match the query
        matching_reviews = [
            review for review in reviews_data
            if query in review['restaurant_name'].lower()
        ]

        if matching_reviews:
            # Group reviews by restaurant name
            grouped_reviews = {}
            for review in matching_reviews:
                restaurant_name = review['restaurant_name']
                if restaurant_name not in grouped_reviews:
                    grouped_reviews[restaurant_name] = []
                grouped_reviews[restaurant_name].append(review)

            # Format the reviews for display
            formatted_reviews = ""
            for restaurant_name, reviews in grouped_reviews.items():
                #formatted_reviews += f"<h4>{restaurant_name}</h4>"
                for review in reviews:
                    review_text = review['review_text']
                    emotion = review['emotion']
                    confidence = review['confidence']

                    formatted_reviews += (
                        f"{review_text}<br><br>"
                        f"Emotion: {emotion} <br>Confidence: {confidence:.2f}<br>"
                        f"-------------------------<br><br>"
                    )

            # Return the formatted reviews
            return ui.HTML(f"<div style='overflow-x: auto; max-height: 220px; padding: 10px; "
                        f"border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9;'>"
                        f"{formatted_reviews}</div>")
        else:
            # If no restaurants match the query
            return ui.HTML("<div style='padding: 10px;'>No restaurants found matching your search.</div>")

        
    @render.text
    @reactive.event(input.search_btn, ignore_none=False)
    def name_name():
        df = pd.read_csv(data_file)
        query = input.search_query().strip().lower()
        results = df[df['Name'].str.lower().str.contains(query, na=False)]

        if len(results['Name'].tolist()) > 0:
            return results['Name'].tolist()[0]
        return "No such place"
    
    @render.text
    @reactive.event(input.search_btn, ignore_none=False)
    def rating_rating():
        df = pd.read_csv(data_file)
        query = input.search_query().strip().lower()
        results = df[df['Name'].str.lower().str.contains(query, na=False)]

        if len(results['Name'].tolist()) > 0:
            return results['Rating'].tolist()[0]
        return "No such place"
    
    @render.text
    @reactive.event(input.search_btn, ignore_none=False)
    def address_address():
        df = pd.read_csv(data_file)
        query = input.search_query().strip().lower()
        results = df[df['Name'].str.lower().str.contains(query, na=False)]

        if len(results['Name'].tolist()) > 0:
            return results['Address'].tolist()[0]
        return "No such place"
    
    @render.text
    @reactive.event(input.search_btn, ignore_none=False)
    def distance_distance():
        df = pd.read_csv(data_file)
        query = input.search_query().strip().lower()
        results = df[df['Name'].str.lower().str.contains(query, na=False)]

        if len(results['Name'].tolist()) > 0:
            return results['Distance from Center'].tolist()[0]
        return "No such place"
    
    @render.text
    @reactive.event(input.search_btn, ignore_none=False)
    def employee_num():
        df = pd.read_csv(data_file)
        query = input.search_query().strip().lower()
        results = df[df['Name'].str.lower().str.contains(query, na=False)]

        if len(results['Name'].tolist()) > 0:
            return scrape_restaurant_data([results['Name'].tolist()[0]])
        return "No such place"
    
    @render.plot
    @reactive.event(input.search_btn, ignore_none=False)
    def restaurant_reviews_plot():
        # Load the JSON data for reviews
        with open('./data/reviews_with_emotions_google.json', 'r', encoding='utf-8') as file:
            reviews_data = json.load(file)

        query = input.search_query().strip().lower()

        # Filter reviews for restaurants that match the query
        matching_reviews = [
            review for review in reviews_data
            if query in review['restaurant_name'].lower()
        ]

        if matching_reviews:
            # Group reviews by emotion
            emotions = [review['emotion'] for review in matching_reviews]
            
            # Create a count of each emotion
            emotion_counts = pd.Series(emotions).value_counts()

            # Create the plot
            fig, ax = plt.subplots(figsize=(8, 6))

            # Bar plot for emotions
            ax.bar(emotion_counts.index, emotion_counts.values, color='skyblue')

            # Set the labels and title
            ax.set_xlabel('Emotion')
            ax.set_ylabel('Count')
            ax.set_title(f'Emotion Distribution for {query.capitalize()}')

            # Show the plot
            return fig
        else:
            # If no reviews match the query, return an empty plot or a message
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'No reviews found for this restaurant', ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig
        

    @render.ui
    @reactive.event(input.num_clusters, ignore_none=False)
    def clustering_plot():
        # Load the CSV data
        df = pd.read_csv(data_file)

        # Check if the necessary columns exist
        if 'Distance from Center' not in df.columns or 'Rating' not in df.columns:
            print("Error: Required columns not found in the data.")
            return None  # Return None if the required columns are missing

        # Extract the relevant data for clustering
        distances = df['Distance from Center']
        ratings = df['Rating']
        restaurant_names = df['Name']
        
        # For emotions, we'll use a simple encoding scheme: map emotions to numerical values
        with open('./data/reviews_with_emotions_google.json', 'r', encoding='utf-8') as file:
            reviews_data = json.load(file)

        # Create a mapping of emotions to numerical values
        emotion_map = {'anger': 1, 'joy': 6, 'sadness': 3, 'neutral': 5, 'surprise': 4, 'disgust': 2}
        
        # Calculate the average emotion value for each restaurant
        emotion_values = []
        for name in restaurant_names:
            # Get the reviews for the current restaurant
            restaurant_reviews = [review for review in reviews_data if review['restaurant_name'].lower() == name.lower()]
            
            # Calculate the average emotion score for this restaurant
            if restaurant_reviews:
                avg_emotion = np.mean([emotion_map.get(review['emotion'], 0) for review in restaurant_reviews])
            else:
                avg_emotion = 0  # No reviews, so we assign a default value
            
            emotion_values.append(avg_emotion)

        # Add the emotion values to the dataframe
        df['Emotion'] = emotion_values

        # Remove rows with NaN values in 'Distance from Center', 'Rating', or 'Emotion'
        df = df.dropna(subset=['Distance from Center', 'Rating', 'Emotion'])

        # Prepare the data for clustering
        clustering_data = np.array(list(zip(df['Rating'], df['Distance from Center'], df['Emotion'])))

        # Perform KMeans clustering with the number of clusters from the slider
        num_clusters = input.num_clusters()
        kmeans = KMeans(n_clusters=num_clusters)  # Use the number of clusters selected by the user
        df['Cluster'] = kmeans.fit_predict(clustering_data)

        # Create the 3D plot using Plotly's graph_objects
        fig = go.Figure()

        # Add scatter plot for clustering in 3D
        fig.add_trace(go.Scatter3d(
            x=df['Distance from Center'],
            y=df['Rating'],
            z=df['Emotion'],
            mode='markers',
            marker=dict(color=df['Cluster'], colorscale='Viridis', size=10),
            text=df['Name'],  # Display restaurant names on hover
            hoverinfo='text'
        ))

        # Set the layout for the 3D plot
        fig.update_layout(
            title=f'3D Clustering of Restaurants Based on Rating, Distance, and Emotions ({num_clusters} Clusters)',
            scene=dict(
                xaxis_title='Distance from City Center (km)',
                yaxis_title='Restaurant Rating',
                zaxis_title='Emotion'
            ),
            height=600,
            showlegend=False
        )

        # Convert Plotly figure to HTML and return it
        return ui.HTML(fig.to_html(full_html=False))


    



app = App(app_ui, server)
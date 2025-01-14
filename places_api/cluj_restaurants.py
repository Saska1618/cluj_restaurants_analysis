import requests
import time
import csv

from webscraping.scraper import scrape_restaurant_data

import pandas as pd

from .restaurant import *

class ClujRestaurants:

    def __init__(self, api_key, locations, radius=1000, place_type="restaurant"):
        """
        Initialize the ClujRestaurants class.

        :param api_key: Google Places API key.
        :param locations: List of location coordinates (latitude, longitude) as strings.
        :param radius: Radius in meters for the search.
        :param place_type: Type of place to search (default is 'restaurant').
        """
        self.api_key = api_key
        self.locations = locations
        self.radius = radius
        self.place_type = place_type
        self.restaurants = {}
        self.city_center_coordinates = "46.770439,23.591423"

    def fetch_restaurants(self, json_file="./data/reviews_with_emotions_google.json"):
        """
        Fetch unique restaurants from the Google Places API for all locations.
        """
        for loc in self.locations:
            self._fetch_from_location(loc, json_file)

    def _fetch_from_location(self, location, json_file):
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={self.radius}&type={self.place_type}&key={self.api_key}"
        while url:
            response = requests.get(url)
            data = response.json()
            
            for place in data.get('results', []):
                if place['place_id'] not in self.restaurants:
                    restaurant = Restaurant(
                        name=place['name'],
                        address=place.get('vicinity', 'N/A'),
                        place_id=place['place_id'],
                        rating=place.get('rating')
                    )
                    restaurant.fetch_reviews(self.api_key, json_file)
                    restaurant.calculate_distance_from_city_center(self.city_center_coordinates, self.api_key)
                    self.restaurants[place['place_id']] = restaurant
            
            next_page_token = data.get('next_page_token')
            if next_page_token:
                time.sleep(2)
                url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={next_page_token}&key={self.api_key}"
            else:
                break

    def get_restaurant_by_name(self, name):
        """
        Get the details of a restaurant by name.

        :param name: The name of the restaurant to search for.
        :return: A Restaurant object with the restaurant's details (None if not found).
        """
        query = name.strip().lower()
        for restaurant in self.restaurants.values():      
            if query in restaurant.name.strip().lower():
                return restaurant
        return None

    def get_restaurants(self):
        """
        Get the list of unique restaurants.
        
        :return: List of unique restaurants.
        """
        print("Jon")
        return list(self.restaurants.values())

    def export_to_csv(self, filename="./data/google_restaurants.csv"):
        """
        Export the fetched restaurant data to a CSV file.

        :param filename: The name of the CSV file to save the data.
        """
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the header
            writer.writerow(["Name", "Address", "Rating", "Place ID", "Reviews", "Distance from Center"])
            
            # Write restaurant details
            for restaurant in self.restaurants.values():
                reviews_text = "; ".join(
                    [f"{review['author_name']}: {review['text'][:1000]}" for review in restaurant.reviews]
                )
                writer.writerow([restaurant.name, restaurant.address, restaurant.rating, restaurant.place_id, reviews_text, restaurant.distance_from_city_center])

    def scrape_employee_data(self, restaurant_csv="./data/googe_restaurants.csv", employee_csv="./data/employee_data.csv", merged_csv='./data/merged_data.csv'):
        """
        Use the scraper to fetch employee data for the restaurants and append it to the existing restaurant CSV file.

        :param restaurant_csv: The existing CSV file with restaurant details.
        :param employee_csv: The temporary CSV file to save scraped employee data.
        """
        # Extract the names of the restaurants
        restaurant_names = [restaurant.name for restaurant in self.restaurants.values()]
        
        # Call the scraper function to get employee data
        scrape_restaurant_data(restaurant_names, employee_csv)

    def merge_csvs(self, restaurant_csv="./data/google_restaurants.csv", employee_csv="./data/employee_data.csv", merged_csv='./data/merged_data.csv'):
        # Load both the restaurant CSV and the scraped employee data
        try:
            restaurant_data = pd.read_csv(restaurant_csv)
            print("olvas")
            employee_data = pd.read_csv(employee_csv)

            print("eddig")

            # Merge the two datasets on the restaurant name
            merged_data = pd.merge(restaurant_data, employee_data, on="Name", how="left")

            # Save the updated data back to the original CSV
            merged_data.to_csv(merged_csv, index=False)
            print(f"Updated restaurant data saved to {restaurant_csv}")
        except Exception as e:
            print(f"Error processing CSV files: {e}")

    def load_from_csv(self, filename="./data/merged_data.csv"):
        """
        Load restaurant data from a CSV file into the ClujRestaurants instance.

        :param filename: The path to the CSV file containing restaurant data.
        """
        try:
            # Read the CSV file into a pandas DataFrame
            data = pd.read_csv(filename)

            # Populate the self.restaurants dictionary
            for _, row in data.iterrows():
                # Create a Restaurant object
                restaurant = Restaurant(
                    name=row["Name"],
                    address=row["Address"],
                    place_id=row["Place ID"],
                    rating=row["Rating"] if not pd.isna(row["Rating"]) else None,
                    employee_num=row["Employees"] if not pd.isna(row["Employees"]) else None
                )

                # loading the data from the json file
                restaurant.load_reviews_from_json()

                # Set the distance from the city center if available
                if not pd.isna(row["Distance from Center"]):
                    restaurant.distance_from_city_center = row["Distance from Center"]

                # Set the employees field if available
                if "Employees" in row and not pd.isna(row["Employees"]):
                    restaurant.employees = row["Employees"]

                # Add the restaurant to the dictionary
                self.restaurants[row["Place ID"]] = restaurant

            print(f"Successfully loaded data from {filename}")
        except Exception as e:
            print(f"Error loading data from {filename}: {e}")

    def full_refresh(self, data_file='./data/merged_data.csv'):
        self.fetch_restaurants()
        self.export_to_csv(data_file)
        self.scrape_employee_data()
        self.merge_csvs(restaurant_csv="./data/google_restaurants.csv", employee_csv="./data/employee_data.csv", merged_csv='./data/merged_data.csv')

    def refresh_restaurants(self, data_file='./data/merged_data.csv'):
        self.fetch_restaurants()
        self.export_to_csv(data_file)
        self.merge_csvs(restaurant_csv="./data/google_restaurants.csv", employee_csv="./data/employee_data.csv", merged_csv='./data/merged_data.csv')

    def scrape_refresh(self):
        self.scrape_employee_data()
        self.merge_csvs(restaurant_csv="./data/google_restaurants.csv", employee_csv="./data/employee_data.csv", merged_csv='./data/merged_data.csv')

    def get_display_restaurant_data(self):
        """
        Process the restaurant data from the self.restaurants dictionary by removing specific attributes
        and adding an index column.

        :return: Processed pandas DataFrame with the index column added.
        """
        try:
            # Prepare a list of dictionaries for each restaurant
            restaurant_data = []
            for restaurant in self.restaurants.values():
                restaurant_info = {
                    "Name": restaurant.name,
                    "Address": restaurant.address,
                    "Rating": restaurant.rating,
                    "Distance from Center": restaurant.distance_from_city_center,
                    "Employees": getattr(restaurant, 'employees', None),  # If employees attribute exists
                }
                restaurant_data.append(restaurant_info)

            # Convert the list of dictionaries to a pandas DataFrame
            df = pd.DataFrame(restaurant_data)

            # Remove the 'Reviews' and 'Place ID' columns if they exist
            if 'Reviews' in df.columns:
                df = df.drop(columns=['Reviews', 'Place ID'])

            # Add an 'index' column and move it to the leftmost position
            df['index'] = [i for i in range(1, len(df) + 1)]
            df = df[['index'] + [col for col in df.columns if col != 'index']]

            return df
        except Exception as e:
            print(f"Error processing the data: {e}")
            return None

    

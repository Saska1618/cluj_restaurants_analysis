import requests
import time
import csv
import math
import json
from transformers import pipeline

from webscraping.scraper import scrape_restaurant_data

import pandas as pd

class Restaurant:

    emotion_analyzer = pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')

    def __init__(self, name, address, place_id, rating=None):
        """
        Initialize a Restaurant instance.

        :param name: Name of the restaurant.
        :param address: Address of the restaurant.
        :param place_id: Google Places place_id of the restaurant.
        :param rating: Rating of the restaurant (optional).
        """
        self.name = name
        self.address = address
        self.place_id = place_id
        self.rating = rating
        self.reviews = []
        self.distance_from_city_center = None

    def fetch_reviews(self, api_key, json_file):
        """
        Fetch reviews for this restaurant from the Google Places API.

        :param api_key: Google Places API key.
        """
        url = f"https://maps.googleapis.com/maps/api/place/details/json?placeid={self.place_id}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        reviews = data.get("result", {}).get("reviews", [])
        self.reviews = reviews[:50]  # Limit to 50 reviews

        # Analyze emotions and save to JSON
        review_data = []
        for review in self.reviews:
            text = review.get("text", "")
            if text:
                emotion_results = self.emotion_analyzer(text[:512])
                if emotion_results:
                    emotion = emotion_results[0]['label']
                    confidence = emotion_results[0]['score']
                else:
                    emotion = "Unknown"
                    confidence = 0.0

                review_entry = {
                    "restaurant_name": self.name,
                    "review_text": text,
                    "emotion": emotion,
                    "confidence": confidence
                }
                review_data.append(review_entry)

        # Write to JSON file
        self._write_to_json(json_file, review_data)

    @staticmethod
    def _write_to_json(json_file, review_data):
        """
        Write review data to a JSON file.

        :param json_file: Path to the JSON file.
        :param review_data: List of reviews with emotions.
        """
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        existing_data.extend(review_data)

        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)

    def calculate_distance_from_city_center(self, city_center_coordinates, api_key):
        """
        Calculate the distance from the restaurant to the city center using the Haversine formula.

        :param city_center_coordinates: Coordinates of the city center (latitude, longitude).
        """
        # Restaurant's coordinates (latitude, longitude)
        lat1, lon1 = self.get_coordinates(api_key)
        
        # City center coordinates (latitude, longitude)
        lat2, lon2 = map(float, city_center_coordinates.split(","))
        
        # Haversine formula
        R = 6371  # Earth radius in kilometers
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Distance in kilometers
        distance = R * c
        self.distance_from_city_center = round(distance, 2)  # Round to 2 decimal places


    def get_coordinates(self, api_key):
        """
        Fetch the restaurant's coordinates from the Google Places API.
        
        :return: Tuple of (latitude, longitude)
        """
        url = f"https://maps.googleapis.com/maps/api/place/details/json?placeid={self.place_id}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        result = data.get("result", {})
        location = result.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")
        
        return lat, lng

    def __str__(self):
        """
        Return a string representation of the restaurant's basic details.
        """
        return f"Name: {self.name}, Address: {self.address}, Rating: {self.rating if self.rating else 'N/A'}"

class ClujRestaurants:

    def __init__(self, api_key, locations, radius=5000, place_type="restaurant"):
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
        for restaurant in self.restaurants.values():
            if restaurant.name.lower() == name.lower():
                return restaurant
        return None

    def get_restaurants(self):
        """
        Get the list of unique restaurants.
        
        :return: List of unique restaurants.
        """
        print("Jon")
        return list(self.restaurants.values())

    def print_restaurants(self):
        """
        Print the details of the unique restaurants.
        """
        restaurants = self.get_restaurants()

        for place in restaurants:
            print(place)
        # for place in restaurants:
        #     print(f"Name: {place['name']}, Address: {place['vicinity']}, Rating: {place.get('rating', 'N/A')}")
        print(f"Total unique restaurants found: {len(restaurants)}")

    def print_restaurants_with_reviews(self):
        """
        Print the details of all the restaurants and their reviews.
        """
        restaurants = self.get_restaurants()
        print(f"Total restaurants found: {len(restaurants)}")
        for restaurant in restaurants:
            print(restaurant)
            restaurant.fetch_reviews(self.api_key)  # Fetch reviews for the restaurant
            
            if restaurant.reviews:
                print(f"Reviews for {restaurant.name}:")
                for review in restaurant.reviews:
                    print(f"  - {review['author_name']}: {review['text'][:200]}...")  # Print the first 200 chars of the review
            else:
                print("  No reviews available.")
            print("\n---")

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

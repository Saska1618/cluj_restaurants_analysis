import requests
import math
import json
from transformers import pipeline # type: ignore
import os

from webscraping.scraper import scrape_restaurant_data

import pandas as pd

class Restaurant:

    emotion_analyzer = pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')

    def __init__(self, name, address, place_id, rating=None, employee_num=None):
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
        self.employee_num = employee_num

    def fetch_reviews(self, api_key, json_file=None):
        """
        Fetch reviews for this restaurant from the Google Places API.

        :param api_key: Google Places API key.
        """
        print("FETCHING REVIEWS")
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
        print("WRITING TO JSON")
        if json_file is not None:
            self._write_to_json(json_file, review_data)

    @staticmethod
    def _write_to_json(json_file, review_data):
        """
        Write review data to a JSON file.

        :param json_file: Path to the JSON file.
        :param review_data: List of reviews with emotions.
        """
        print("WRITING")
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
    
    def load_reviews_from_json(self, json_file='./data/reviews_with_emotions_google.json'):
        """
        Load reviews for this restaurant from a JSON file.

        :param json_file: Path to the JSON file containing reviews.
        """
        if not os.path.exists(json_file):
            print(f"File {json_file} does not exist.")
            return

        try:
            with open(json_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return
        
        query = self.name.strip().lower()

        # Filter reviews for the current restaurant
        filtered_reviews = [
            review for review in data if query in review.get("restaurant_name").strip().lower()
        ]

        # Update the restaurant's reviews
        self.reviews = filtered_reviews
        #print(f"Loaded {len(filtered_reviews)} reviews for {self.name}.")
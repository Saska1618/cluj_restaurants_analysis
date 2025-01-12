import requests
import time
import csv
import math

class Restaurant:
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

    def fetch_reviews(self, api_key):
        """
        Fetch reviews for this restaurant from the Google Places API.

        :param api_key: Google Places API key.
        """
        url = f"https://maps.googleapis.com/maps/api/place/details/json?placeid={self.place_id}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        reviews = data.get("result", {}).get("reviews", [])
        self.reviews = reviews[:50]  # Limit to 50 reviews

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

    def fetch_restaurants(self):
        """
        Fetch unique restaurants from the Google Places API for all locations.
        """
        for loc in self.locations:
            self._fetch_from_location(loc)

    def _fetch_from_location(self, location):
        """
        Fetch restaurants for a single location, handling pagination and deduplication.

        :param location: Latitude and longitude as a string (e.g., "46.770439,23.591423").
        """
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={self.radius}&type={self.place_type}&key={self.api_key}"
        while url:
            response = requests.get(url)
            data = response.json()
            
            # Add results to the restaurants dictionary using place_id as the key
            for place in data.get('results', []):

                if place['place_id'] not in self.restaurants:
                    restaurant = Restaurant(
                        name=place['name'],
                        address=place.get('vicinity', 'N/A'),
                        place_id=place['place_id'],
                        rating=place.get('rating')
                    )
                    restaurant.fetch_reviews(self.api_key)
                    restaurant.calculate_distance_from_city_center(self.city_center_coordinates, self.api_key)
                    self.restaurants[place['place_id']] = restaurant
            
            # Check for next_page_token
            next_page_token = data.get('next_page_token')
            if next_page_token:
                time.sleep(2)  # Pause to allow the token to become valid
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
import requests
import time

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
        self.unique_restaurants = {}

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
            
            # Add results to the unique restaurants dictionary using place_id as the key
            for place in data.get('results', []):
                self.unique_restaurants[place['place_id']] = place
            
            # Check for next_page_token
            next_page_token = data.get('next_page_token')
            if next_page_token:
                time.sleep(2)  # Pause to allow the token to become valid
                url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={next_page_token}&key={self.api_key}"
            else:
                break

    def get_restaurants(self):
        """
        Get the list of unique restaurants.
        
        :return: List of unique restaurants.
        """
        return list(self.unique_restaurants.values())

    def print_restaurants(self):
        """
        Print the details of the unique restaurants.
        """
        restaurants = self.get_restaurants()
        for place in restaurants:
            print(f"Name: {place['name']}, Address: {place['vicinity']}, Rating: {place.get('rating', 'N/A')}")
        print(f"Total unique restaurants found: {len(restaurants)}")
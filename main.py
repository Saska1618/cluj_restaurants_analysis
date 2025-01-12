from places_api.restaurants import ClujRestaurants
from credentials.credentials_provider import get_gplaces_api_key

# Example usage
if __name__ == "__main__":
    API_KEY = get_gplaces_api_key()

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
    radius = 5000

    cluj_restaurants = ClujRestaurants(api_key=API_KEY, locations=locations, radius=radius)
    cluj_restaurants.fetch_restaurants()
    cluj_restaurants.export_to_csv()
    #cluj_restaurants.print_restaurants_with_reviews()

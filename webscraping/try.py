import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

BASE_URL = "https://www.tripadvisor.com"

def fetch_restaurant_data():
    # List to store restaurant data
    restaurants = []
    url = "https://www.tripadvisor.com/Restaurants-g298474-Cluj_Napoca_Cluj_County_Northwest_Romania_Transylvania.html"
    
    # Loop through pages (adjust based on the pagination structure of the site)
    for page in range(0, 150, 30):  # Adjust the step if each page contains a different number of restaurants
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find restaurant entries
        restaurant_entries = soup.find_all('div', class_='list_item')
        
        for entry in restaurant_entries:
            try:
                # Extract restaurant details
                name = entry.find('a', class_='restaurant_name').text.strip()
                rating = entry.find('span', class_='ui_bubble_rating')['class'][1].split('_')[-1]
                type = entry.find('div', class_='cuisines').text.strip()
                
                # Extract restaurant page link
                link = BASE_URL + entry.find('a', class_='restaurant_name')['href']
                
                # Scrape reviews from the restaurant page
                reviews = fetch_reviews(link)
                
                restaurants.append({
                    'Name': name,
                    'Rating': rating,
                    'Type': type,
                    'Reviews': reviews
                })
            except Exception as e:
                print(f"Error fetching data for a restaurant: {e}")
        
        # Find next page URL
        next_page = soup.find('a', class_='next')
        if next_page:
            url = BASE_URL + next_page['href']
        else:
            break
    
    # Save data to a file
    df = pd.DataFrame(restaurants)
    df.to_csv('restaurants.csv', index=False)
    print("Data saved to restaurants.csv")

def fetch_reviews(link):
    reviews = []
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    review_entries = soup.find_all('div', class_='review-container')
    for entry in review_entries:
        try:
            review_date = entry.find('span', class_='ratingDate')['title']
            review_date = datetime.strptime(review_date, '%B %d, %Y')
            
            if review_date.year < 2024:
                continue
            
            review_text = entry.find('p', class_='partial_entry').text.strip()
            reviews.append({
                'Date': review_date,
                'Review': review_text
            })
            
            if len(reviews) >= 100:
                break
        except Exception as e:
            print(f"Error fetching a review: {e}")
    
    return reviews

# Run the scraper
fetch_restaurant_data()

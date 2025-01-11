from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://www.tripadvisor.com"

def fetch_restaurant_data():
    # Set up Selenium WebDriver
    driver = webdriver.Chrome()  # Replace with the path to your WebDriver if needed
    driver.get(BASE_URL + "/Restaurants-g298474-Cluj_Napoca_Cluj_County_Northwest_Romania_Transylvania.html")

    restaurants = []

    try:
        # Loop through pages
        while True:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'vIjFZ'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Find restaurant entries
            restaurant_entries = soup.find_all('div', class_='vIjFZ')
            for entry in restaurant_entries:
                try:
                    name = entry.find('a', class_='name-class').text.strip()  # Update class name
                    rating = entry.find('span', class_='rating-class')['aria-label']  # Update class name
                    type = entry.find('div', class_='type-class').text.strip()  # Update class name
                    restaurants.append({'Name': name, 'Rating': rating, 'Type': type})
                except Exception as e:
                    print(f"Error parsing restaurant: {e}")

            # Click the next page button
            next_button = driver.find_element(By.CLASS_NAME, 'BrOJk')
            if next_button:
                next_button.click()
            else:
                break
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        driver.quit()

    # Save data to CSV
    # df = pd.DataFrame(restaurants)
    # df.to_csv('restaurants.csv', index=False)
    # print("Data saved to restaurants.csv")

fetch_restaurant_data()

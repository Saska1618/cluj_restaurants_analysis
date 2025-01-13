from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import pandas as pd

def scrape_restaurant_data(restaurants, filename=None):

    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run browser in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model (for some environments)
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--window-size=1920x1080")  # Set a specific window size

    driver = webdriver.Chrome(options=chrome_options)
    data = []

    for i, restaurant in enumerate(restaurants):
        search_query = f"{restaurant} cluj restaurant listafirme"
        driver.get("https://www.google.com")

        print(f"{i}. Working with restaurant {restaurant}\n")
        
        # Handle Google's cookie pop-up in Romanian
        try:
            # Locate the button by a partial match of the text inside the div
            accept_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//button[div[contains(text(), 'Acceptă')]]"))
            )
            accept_button.click()
            print("Google cookie pop-up dismissed.")
        except Exception as e:
            print("No Google cookie pop-up found:", e)
        
        # Perform Google search
        try:
            search_box = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)
        except Exception as e:
            print(f"Error interacting with search box for {restaurant}: {e}")
            continue
        
        # Click on the first Listafirme link
        try:
            results = driver.find_elements(By.CSS_SELECTOR, "a")
            links = []

            for index, element in enumerate(results):
                try:
                    # Replace 'href' with the desired attribute name
                    attribute_value = element.get_attribute('href')
                    links.append(attribute_value)
                    #print(f"Element {index}: {attribute_value}")
                except Exception as e:
                    print(f"Error processing element {index}: {e}")

            for href in links:
                #href = link.get_attribute("href")
                if href is None:
                    continue
                if "listafirme.ro" in href:
                    print(f"Good {restaurant} : {href}")
                    driver.get(href)
                    time.sleep(1)
                    break
        except Exception as e:
            print(f"Error finding Listafirme link for {restaurant}: {e}")
            continue
        
        # Scrape Listafirme Page
        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table", class_="table-bilant")
            if table:
                rows = table.find_all("tr")
                if len(rows) > 1:
                    cols = rows[1].find_all("td")
                    if len(cols) >= 8:
                        employees = cols[7].text.strip()
                    else:
                        employees = "Column Not Found"
                else:
                    employees = "Row Not Found"
            else:
                employees = "Table Not Found"
            
            data.append({"Name": restaurant, "Employees": employees})
        except Exception as e:
            print(f"Error scraping data for {restaurant}: {e}")
            data.append({"Name": restaurant, "Employees": "Error"})
    
    driver.quit()
    
    if filename is not None:
        # Save Data to CSV
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

    return data[0]['Employees']

# List of restaurants to scrape
#restaurants = ["rosa", "bulgakov cafe", "via"]

# Run the scraper
#scrape_restaurant_data(restaurants, "employee_data.csv")

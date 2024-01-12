import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

from fetch_lat_and_long import get_zip_details


def scrape_city_stores(city):
    url = "https://www.apple.com/retail/"

    try:
        response = requests.get(url + (city.lower()).replace(" ", "").replace(".","").replace("'",""))
        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        location_address = soup.find("div", {"class": "store-address-block"})

        address = location_address.find("address").get_text(separator=" ", strip=True)

        location_contact_number = location_address.find(
            "div", class_="store-address-block-telephone"
        ).get_text(separator=" ", strip=True)

        store_name = "Not available"
        phone_number = "Not available"
        zip_code = 0
        latitude = 0
        longitude = 0

        if address:
            store_details = address.split(",")
            store_name = store_details[0].strip()
            last_space_index = (store_name).rfind(" ")
            updated_store_name = (
                store_name[:last_space_index]
                + ", "
                + store_name[last_space_index + 1 :]
            )
            store_address_parts = store_details[1].strip().split(" ")
            zip_code = store_address_parts[-1]

        if location_contact_number:
            phone_number = location_contact_number

        if zip_code:

            if "-" in zip_code:
                zip_code = zip_code.split("-")[0]
                zip_details = get_zip_details(zip_code)

            else:
                zip_details = get_zip_details(zip_code)

            latitude = str(zip_details["lat"])
            longitude = str(zip_details["long"])

        location_details = {
            "store_name": updated_store_name.split(",")[0],
            "store_address": updated_store_name,
            "phone_number": phone_number,
            "zip_code": zip_code,
            "latitude": latitude,
            "longitude": longitude,
        }

        return location_details

    except Exception as e:
        print(f"Something went wrong: {e}")
        return {"response": f"Something went wrong: {e}", "status": 400}


def scrape_apple_stores(url):
    all_locations = []

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return {
                "response": f"Failed to fetch {url}. Status code: {response.status_code}",
                "status": 400,
            }

        soup = BeautifulSoup(response.text, "html.parser")

        states = soup.find("div", {"class": "states-list"})

        for state in states.find_all("div", class_="state"):
            store_location = state.find("span", "label")

            state_name = store_location.text.strip()
            print(f"scrapping data for: {state_name}")

            location_details = []

            for city in state.find_all("div", {"class": "address-lines"}):
                city_name = city.text.strip()

                city_stores = scrape_city_stores(city_name.split(",")[1])
                
                city_stores['city_name'] = city_name
                location_details.append(city_stores)
            
            all_locations.append({
                'state': state_name,
                'sub_locations': location_details
            })

            # if state_name == "New York":
            #     print(f"Scraping data for: {state_name}")

            #     location_details = []
            #     for city in state.find_all("div", {"class": "address-lines"}):
            #         city_name = city.text.strip()

            #         city_stores = scrape_city_stores(city_name.split(",")[1])
            #         city_stores['city_name'] = city_name
            #         location_details.append(city_stores)

            #     all_locations.append({
            #         'state': state_name,
            #         'sub_locations': location_details
            #     })

            #     print(all_locations)            

            print(f"total length of object: {len(all_locations)}")

    except Exception as e:
        return {"response": f"Something went wrong: {e}", "status": 400}

    return all_locations


def generate_excel(locations, output_file="apple_store_locations.csv"):
    # Create a DataFrame from the list of store locations
    df = pd.json_normalize(locations, "sub_locations", ["state"])

    # print(df)
    # Write the DataFrame to a CSV file
    df.to_csv(output_file, index=False)

    print(f"CSV file '{output_file}' generated successfully.")


if __name__ == "__main__":
	# List of website URLs to scrape
    website_url = "https://www.apple.com/retail/storelist/"

	# Scrape store locations
    all_locations = scrape_apple_stores(website_url)

	# Generate CSV file
    generate_excel(all_locations)

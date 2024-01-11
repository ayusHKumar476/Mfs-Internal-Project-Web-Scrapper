import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

from fetch_lat_and_long import get_zip_details


def scrape_local_stores(city, state_url):
    scraped_details = {}
    try:
        url = state_url + city.replace(" ", "-").replace(".", "") + "/"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        city_sub_locations = soup.find("div", class_="location-data-wrapper")

        location = city_sub_locations.find(
            "div", class_="location-nearby-address"
        ).text.strip()

        stripped_location = re.split("  +", location.replace("\n", ""))

        if len(stripped_location) >= 3:
            city_parts = [
                stripped_location[0]
                + " "
                + stripped_location[len(stripped_location) // 2]
                + " "
                + stripped_location[len(stripped_location) - 1].split(",")[0]
            ]
            city_parts.append(stripped_location[len(stripped_location) - 1])
            stripped_location = city_parts

        store_phone_number = soup.find(
            "a", class_="location-nearby-phone-number"
        ).text.strip()

        scraped_details["store_name"] = (
            stripped_location[0] if stripped_location else "Not available"
        )

        scraped_details["store_address"] = (
            stripped_location[0] + ", " + stripped_location[1].split()[0].replace(",", "")
            if stripped_location
            else "Not available"
        )

        scraped_details["phone_number"] = (
            store_phone_number if store_phone_number else "Not available"
        )

        updated_zip_code = stripped_location[1].split()[-1]

        scraped_details["zip_code"] = (
            updated_zip_code if stripped_location else "Not available"
        )

        scraped_details["latitude"] = "0"
        scraped_details["longitude"] = "0"

        if scraped_details["zip_code"]:
            zip_details = get_zip_details(scraped_details["zip_code"])

            scraped_details["latitude"] = str(zip_details["lat"])
            scraped_details["longitude"] = str(zip_details["long"])

        return scraped_details

    except Exception as e:
        return {"response": f"Something went wrong: {e}", "status": 400}


def scrape_city_stores(state):
    city_locations = []

    try:
        url = website_url + state.replace(" ", "-") + "/"
        response = requests.get(url)

        print(f"scrapping data for - {state}")

        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return city_locations  # or raise an exception based on your needs

        soup = BeautifulSoup(response.text, "html.parser")
        cities = soup.find("div", {"id": "contains-place"})

        if cities:

            city_counter = 0

            for city in cities.find_all("li"):
                city_name = city.text.strip()

                scrape_sub_locations = scrape_local_stores(city_name.lower(), url)

                location = {
                    "city_name": city_name,
                    "sub_locations": scrape_sub_locations,
                }

                city_locations.append(location)
                city_counter += 1

                if city_counter >= 20:
                    break

        return city_locations

    except Exception as e:
        print(f"Something went wrong: {e}")
        return {"response": f"Something went wrong: {e}", "status": 400}


def scrape_dominos_stores(website_url):
    store_locations = []
    try:
        response = requests.get(website_url)
        if response.status_code != 200:
            print(f"Failed to fetch {website_url}. Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        states = soup.find("div", {"id": "contains-place"})

        state_locations = {}

        for state in states.find_all("li"):
            state = state.text.strip()

            city_details = scrape_city_stores(state.lower())

            state_locations = {"state": state, "city_details": city_details}

            store_locations.append(state_locations)

            print(
                f"Location wrapping done for {state} sub_locations found: {len(city_details)}"
            )
            print("in append ", len(store_locations))

        return store_locations

    except Exception as e:
        return {"response": f"Something went wrong: {e}", "status": 400}


def generate_excel(locations, output_file="dominos_store_locations.csv"):
    # Create a DataFrame from the list of store locations
    df = pd.json_normalize(locations, "city_details", ["state"])
    df.columns = [col.replace("sub_locations.", "") for col in df.columns]

    # Write the DataFrame to a CSV file
    df.to_csv(output_file, index=False)

    print(f"CSV file '{output_file}' generated successfully.")


if __name__ == "__main__":
	# List of website URLs to scrape
    website_url = "https://pizza.dominos.com/"

	# Scrape store locations
    all_locations = scrape_dominos_stores(website_url)

	# Generate CSV file
    generate_excel(all_locations)

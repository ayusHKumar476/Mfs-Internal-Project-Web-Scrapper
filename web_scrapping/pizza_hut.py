import requests
from bs4 import BeautifulSoup
import pandas as pd

from get_lat_log_details import get_lat_long_details

def get_zip_details(zip_code):
    try:
        response = get_lat_long_details(int(zip_code))

        if response['status'] == 200:
            return response
        else:
            return {
                'lat': "0",
                'long': "0",
            }

    except Exception as e:
        print(f"Something went wrong: {e}")
        return {
            'lat': "0",
            'long': "0",
        }

def extract_sub_location_data(store_location, website_url):
    sub_locations = []
    href_value = store_location.find("a", class_="Directory-listLink")["href"]

    response = requests.get(website_url + href_value)

    if response.status_code != 200:
        print(f"Failed to fetch {website_url}. Status code: {response.status_code}")
        return sub_locations

    soup = BeautifulSoup(response.text, "html.parser")
    container = soup.find("ul", class_="Directory-listLinks")

    if not container:
        return sub_locations

    sub_location_counter = 0

    for store_element in container.find_all("li"):
        if sub_location_counter >= 20:
            break

        name = store_element.find(class_="Directory-listLink").text.strip()
        location_details = {"city_name": name}
        sub_location_2_href = store_element.find("a", class_="Directory-listLink")["href"]

        sub_location_2_response = requests.get(website_url + sub_location_2_href)

        if sub_location_2_response.status_code == 200:
            soup = BeautifulSoup(sub_location_2_response.text, "html.parser")
            sub_container = soup.find("div", class_="Directory-content")

            for items in sub_container.find_all("li"):
                if sub_location_counter >= 30:
                    break

                store_name = items.find("span", class_="LocationName-geo").text.strip()
                store_type = items.find("div", class_="Teaser-storeType").text.strip()
                store_address = items.find("div", class_="Teaser-address").text.strip()
                phone_div = items.find("div", class_="c-phone-number c-phone-main-number")
                store_phone_number = (
                    phone_div.find(
                        "span", class_="c-phone-number-span c-phone-main-number-span"
                    ).text.strip()
                    if phone_div
                    else "Not available"
                )
                zip_postal_code = items.find("span", class_="c-address-postal-code").text.strip()

                location_details["store_name"] = (
                    store_name if store_name else "Not available"
                )
                location_details["store_type"] = (
                    store_type if store_type else "Not available"
                )
                location_details["store_address"] = (
                    store_address if store_address else "Not available"
                )
                location_details["zip_code"] = (
                    zip_postal_code if zip_postal_code else "Not available"
                )

                location_details["latitude"] = "0"
                location_details["longitude"] = "0"

                if location_details["zip_code"] != "Not available":
                    zip_details = get_zip_details(location_details["zip_code"])

                    location_details["latitude"] = str(zip_details["lat"])
                    location_details["longitude"] = str(zip_details["long"])

                location_details["store_phone_number"] = store_phone_number

                sub_locations.append(location_details.copy())

                sub_location_counter += 1

        else:
            print(
                f"Failed to fetch {website_url}. Status code: {sub_location_2_response.status_code}"
            )

    print('length of sublocations - ', len(sub_locations))
    return sub_locations

def extract_store_locations(soup, website_url):
    locations = []

    # Find the container that holds the store locations
    container = soup.find("ul", class_="Directory-listLinks")
    if container:
        # Extract information for each store
        for store_element in container.find_all("li"):
            name = store_element.find(class_="Directory-listLink").text.strip()
            sub_location_details = extract_sub_location_data(store_element, website_url)

            location = {
                "state": name,
                "sub_locations": sub_location_details
            }

            locations.append(location)

            print(
                f"Location wrapping done for {name} sublocations found: {len(sub_location_details)}"
            )
            print("in append ", len(locations))

    return locations

def scrape_store_locations(website_url):
    all_locations = []
    print(f"Scraping {website_url}...")

    # Fetch the web page content
    response = requests.get(website_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract store locations from the 'Store Locator' page
        locations = extract_store_locations(soup, website_url)

        # Add the locations to the list
        all_locations.extend(locations)
        # print(all_locations)
    else:
        print(f"Failed to fetch {website_url}. Status code: {response.status_code}")

    return all_locations

def generate_excel(locations, output_file="store_locations.csv"):
    # Create a DataFrame from the list of store locations
    df = pd.json_normalize(locations, "sub_locations", ["state"])

    # print(df)

    # # Write the DataFrame to a CSV file
    df.to_csv(output_file, index=False)

    print(f"CSV file '{output_file}' generated successfully.")

if __name__ == "__main__":
    # List of website URLs to scrape
    website_url = "https://locations.pizzahut.com/"

    # Scrape store locations
    all_locations = scrape_store_locations(website_url)

    # Generate CSV file
    generate_excel(all_locations)

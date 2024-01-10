import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_store_locations(website_urls):
    all_locations = []

    for website_url in website_urls:
        print(f"Scraping {website_url}...")

        # Fetch the web page content
        response = requests.get(website_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract store locations from the 'Store Locator' page
            locations = extract_store_locations(soup, website_urls)

            # Add the locations to the list
            all_locations.extend(locations)
        else:
            print(f"Failed to fetch {website_url}. Status code: {response.status_code}")

    return all_locations

def extract_sub_location_data(store_location, website_urls):

    sub_locations = []
    href_value = store_location.find('a', class_='Directory-listLink')['href']

    response = requests.get(website_urls[0]+href_value)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('ul', class_='Directory-listLinks')

        if container:

            location_details = {}
            sub_location_counter = 0

            for store_element in container.find_all('li'):

                if sub_location_counter >= 20:
                    break

                name = store_element.find(class_='Directory-listLink').text.strip()
                location_details['city_name'] = name
                sub_location_2_href = store_element.find('a', class_='Directory-listLink')['href']
                
                sub_location_2_response = requests.get(website_urls[0]+sub_location_2_href)

                if sub_location_2_response.status_code == 200:
                    soup = BeautifulSoup(sub_location_2_response.text, 'html.parser')
                    sub_container = soup.find('div', class_='Directory-content')

                    for items in sub_container.find_all('li'):
                        store_name = items.find("span", class_="LocationName-geo").text.strip()
                        store_type = items.find("div", class_="Teaser-storeType").text.strip()
                        store_address = items.find("div", class_="Teaser-address").text.strip()
                        phone_div = items.find('div', class_='c-phone-number c-phone-main-number')
                        store_phone_number = 0
                        if phone_div:
                            # Extract the phone number from the text of the span element
                            phone_span = phone_div.find('span', class_='c-phone-number-span c-phone-main-number-span')
                            
                            if phone_span:
                                store_phone_number = phone_span.text.strip()

                            else:
                                store_phone_number = 0
                        zip_postal_code = items.find("span", class_="c-address-postal-code").text.strip()

                        location_details['store_name'] = store_name if store_name else "Not available"
                        location_details['store_type'] = store_type if store_type else "Not available"
                        location_details['store_address'] = store_address if store_address else "Not available"
                        location_details['zip_code'] = zip_postal_code if zip_postal_code else "Not available"
                        location_details['store_phone_number'] = store_phone_number

                        sub_locations.append(location_details.copy())

                        sub_location_counter += 1

                        if sub_location_counter >= 30:
                            break

                else:
                    print(f"Failed to fetch {website_urls[0]}. Status code: {sub_location_2_response.status_code}")

    else:
        print(f"Failed to fetch {website_urls[0]}. Status code: {response.status_code}")

    return sub_locations




def extract_store_locations(soup, website_urls):
    locations = []

    # Find the container that holds the store locations
    container = soup.find('ul', class_='Directory-listLinks')
    if container:
        location = {}
        # Extract information for each store
        for store_element in container.find_all('li'):
            name = store_element.find(class_='Directory-listLink').text.strip()
            sub_location_details = extract_sub_location_data(store_element, website_urls)

            location['state'] = name
            location['sub_locations'] = sub_location_details
            locations.append(location)

            print(f"Location swrapping done for {name} sublocations found: {len(sub_location_details)}")

    return locations

def generate_excel(locations, output_file='store_locations.xlsx'):
    # Create a DataFrame from the list of store locations
    df = pd.DataFrame(locations)

    print(df.head(50))

    # Write the DataFrame to a CSV file
    df.to_csv(output_file, index=False)

    print(f"CSV file '{output_file}' generated successfully.")

if __name__ == "__main__":
    # List of website URLs to scrape
    website_urls = [
        'https://locations.pizzahut.com/',
    ]

    # Scrape store locations
    all_locations = scrape_store_locations(website_urls)

    # Generate Excel file
    generate_excel(all_locations)
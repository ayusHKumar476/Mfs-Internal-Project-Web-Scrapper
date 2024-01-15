import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

from fetch_lat_and_long import get_zip_details


def get_location_details(url, location):
    try:
        location = location.rstrip("-")
        location = re.sub(r"-+", "-", location)
        location_url = url + "/" + location + "/"
        response = requests.get(location_url)
        if response.status_code != 200:
            print(f"failed to scrape for: {location}")
            print(
                f"Failed to fetch {location_url}. Status code: {response.status_code}"
            )
            return

        soup = BeautifulSoup(response.text, "html.parser")

        address = soup.find("address", class_="c-address")

        street_address_1 = (
            address.find("span", class_="c-address-street-1").text.strip()
            if address.find("span", class_="c-address-street-1")
            else "Not available"
        )

        city = (
            address.find("span", class_="c-address-city").text.strip()
            if address.find("span", class_="c-address-city")
            else "Not available"
        )

        postal_code = (
            address.find("span", class_="c-address-postal-code").text.strip()
            if address.find("span", class_="c-address-postal-code")
            else "Not available"
        )

        main_number = (
            soup.find("a", class_="Phone-link")["href"]
            if soup.find("a", class_="Phone-link")
            else "Not available"
        )

        location_details = {
            "store_address": street_address_1 + "," + city,
            "store_name": street_address_1,
            "city_name": city,
            "phone_number": main_number,
            "zip_code": postal_code,
            "latitude": "",
            "longitude": "",
        }

        if postal_code:
            zip_details = get_zip_details(postal_code)

            location_details["latitude"] = str(zip_details["lat"])
            location_details["longitude"] = str(zip_details["long"])

            if location_details["latitude"] == "0":
                print(
                    f"zip_code for: {city} is {postal_code} {location_details['latitude']} and {location_details['longitude']}"
                )
        return location_details

    except Exception as e:
        print(f"Something went wrong: {e}")
        return {"response": f"Something went wrong: {e}", "status": 400}


def scrape_sub_location_details(city, sub_location):
    url = "https://restaurants.subway.com/united-states"

    try:
        url = (
            url
            + "/"
            + str(city)
            + "/"
            + str(sub_location)
            .lower()
            .replace(" ", "-")
            .replace(".", "-")
            .replace("'", "-")
            .replace(",", "")
        )
        response = requests.get(url)
        if response.status_code != 200:
            print(f"failed to scrape for: {sub_location}")
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        sub_location_stores = soup.find_all("div", class_="Teaser-address")
        locations = []

        for location in sub_location_stores:
            store_name = location.find("span", class_="c-address-street-1").text.strip()

            locations.append(
                get_location_details(
                    url,
                    (
                        store_name.replace(" ", "-")
                        .replace("'", "-")
                        .replace(".", "-")
                        .replace(",", "")
                    ).lower(),
                )
            )

        return locations

    except Exception as e:
        print(f"Something went wrong: {e}")
        return {"response": f"Something went wrong: {e}", "status": 400}


def scrape_city_stores(city):
    url = "https://restaurants.subway.com/united-states"

    try:
        response = requests.get(url + "/" + city)
        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        city_stores = soup.find("ul", "Directory-listLinks")

        city_limit = 10
        city_counter = 0
        city_details = []

        for city_location in city_stores.find_all("li"):
            sub_location = city_location.text.strip()

            city_details = scrape_sub_location_details(city, sub_location)

            city_counter += 1

            print(f"scrapping done for - {sub_location}")

            if city_counter == city_limit:
                break

        return city_details

    except Exception as e:
        print(f"Something went wrong: {e}")
        return {"response": f"Something went wrong: {e}", "status": 400}


def scrape_subway_stores(url):
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

        states = soup.find("ul", "Directory-listLinks")

        total_states = len(states.find_all("li"))
        counter = 0

        for state in states.find_all("li"):
            state_name = state.get_text()
            href_value = state.a["href"].split("/")[1]

            location_details = scrape_city_stores(href_value)

            all_locations.append(
                {"state": state_name, "sub_locations": location_details}
            )

            # print(all_locations)

            counter += 1

            if counter == total_states:
                break

            print(f"total length of object: {len(all_locations)}")

    except Exception as e:
        return {"response": f"Something went wrong: {e}", "status": 400}

    return all_locations


import sys


def generate_excel(locations, output_file="subway_store_locations.csv"):
    # Create a DataFrame from the list of store locations
    df_list = []

    for location in locations:
        state_name = location["state"]
        sub_locations = location["sub_locations"]

        if sub_locations is not None:
            for sub_location in sub_locations:
                df_list.append(
                    {
                        "state": state_name,
                        "store_address": sub_location["store_address"],
                        "store_name": sub_location["store_name"],
                        "city_name": sub_location["city_name"],
                        "phone_number": sub_location["phone_number"],
                        "latitude": sub_location["latitude"],
                        "longitude": sub_location["longitude"],
                    }
                )

    df = pd.DataFrame(df_list)

    # Write the DataFrame to a CSV file
    df.to_csv(output_file, index=False)

    print(f"CSV file '{output_file}' generated successfully.")


if __name__ == "__main__":
    # List of website URLs to scrape
    website_url = "https://restaurants.subway.com/united-states"

    # Scrape store locations
    # all_locations = scrape_subway_stores(website_url)

    # Save the output to a text file
    # with open("output.json", "w") as file:
    #     # Redirect the standard output to the file
    #     sys.stdout = file

    #     # Print the output (this will be written to the file)
    #     print(all_locations)

    #     # Reset the standard output
    #     sys.stdout = sys.__stdout__

    all_locations = [
        {
            "state": "Alabama",
            "sub_locations": [
                {
                    "store_address": "111 N Brindlee Mtn Pwy,Arab",
                    "store_name": "111 N Brindlee Mtn Pwy",
                    "city_name": "Arab",
                    "phone_number": "tel:+12565861285",
                    "zip_code": "35016",
                    "latitude": "34.32387",
                    "longitude": "-86.502006",
                },
                {
                    "store_address": "1450 No Brindlee Mtn Pkwy,Arab",
                    "store_name": "1450 No Brindlee Mtn Pkwy",
                    "city_name": "Arab",
                    "phone_number": "tel:+12569312199",
                    "zip_code": "35016",
                    "latitude": "34.32387",
                    "longitude": "-86.502006",
                },
            ],
        },
        {
            "state": "Alaska",
            "sub_locations": [
                {
                    "store_address": "3726 Lake Street,Homer",
                    "store_name": "3726 Lake Street",
                    "city_name": "Homer",
                    "phone_number": "tel:+19072352782",
                    "zip_code": "99603",
                    "latitude": "0",
                    "longitude": "0",
                }
            ],
        },
        {
            "state": "Arizona",
            "sub_locations": [
                {
                    "store_address": "15250 N Oracle Rd,Catalina",
                    "store_name": "15250 N Oracle Rd",
                    "city_name": "Catalina",
                    "phone_number": "tel:+15208256593",
                    "zip_code": "85739",
                    "latitude": "32.621072",
                    "longitude": "-110.989667",
                }
            ],
        },
        {
            "state": "Arkansas",
            "sub_locations": [
                {
                    "store_address": "4 Cunningham Corner,Bella Vista",
                    "store_name": "4 Cunningham Corner",
                    "city_name": "Bella Vista",
                    "phone_number": "tel:+14798554822",
                    "zip_code": "72714",
                    "latitude": "36.46735",
                    "longitude": "-94.222151",
                }
            ],
        },
        {
            "state": "California",
            "sub_locations": [
                {
                    "store_address": "100 W 12th Street,Alturas",
                    "store_name": "100 W 12th Street",
                    "city_name": "Alturas",
                    "phone_number": "tel:+15302334468",
                    "zip_code": "96101",
                    "latitude": "41.452711",
                    "longitude": "-120.53846",
                }
            ],
        },
        {
            "state": "Colorado",
            "sub_locations": [
                {
                    "store_address": "965 S First St,Bennett",
                    "store_name": "965 S First St",
                    "city_name": "Bennett",
                    "phone_number": "tel:+13036443080",
                    "zip_code": "80102",
                    "latitude": "39.74599",
                    "longitude": "-104.442841",
                }
            ],
        },
        {
            "state": "Connecticut",
            "sub_locations": [
                {
                    "store_address": "1197 Farmington Ave,Bristol",
                    "store_name": "1197 Farmington Ave",
                    "city_name": "Bristol",
                    "phone_number": "tel:+18605859099",
                    "zip_code": "06010",
                    "latitude": "41.681578",
                    "longitude": "-72.940749",
                },
                {
                    "store_address": "123 Farmington Ave,Bristol",
                    "store_name": "123 Farmington Ave",
                    "city_name": "Bristol",
                    "phone_number": "tel:+18605849816",
                    "zip_code": "06010",
                    "latitude": "41.681578",
                    "longitude": "-72.940749",
                },
                {
                    "store_address": "1400 Farmington Ave,Bristol",
                    "store_name": "1400 Farmington Ave",
                    "city_name": "Bristol",
                    "phone_number": "tel:+18605400699",
                    "zip_code": "06010",
                    "latitude": "41.681578",
                    "longitude": "-72.940749",
                },
                {
                    "store_address": "296 Middle St,Bristol",
                    "store_name": "296 Middle St",
                    "city_name": "Bristol",
                    "phone_number": "tel:+18605834014",
                    "zip_code": "06010",
                    "latitude": "41.681578",
                    "longitude": "-72.940749",
                },
                {
                    "store_address": "45 North Main Street,Bristol",
                    "store_name": "45 North Main Street",
                    "city_name": "Bristol",
                    "phone_number": "tel:+18603140229",
                    "zip_code": "06010",
                    "latitude": "41.681578",
                    "longitude": "-72.940749",
                },
                {
                    "store_address": "815 Pine Street,Bristol",
                    "store_name": "815 Pine Street",
                    "city_name": "Bristol",
                    "phone_number": "tel:+18605841352",
                    "zip_code": "06010",
                    "latitude": "41.681578",
                    "longitude": "-72.940749",
                },
            ],
        },
        {
            "state": "Delaware",
            "sub_locations": [
                {
                    "store_address": "216 Atlantic Avenue,Millville",
                    "store_name": "216 Atlantic Avenue",
                    "city_name": "Millville",
                    "phone_number": "tel:+13025371900",
                    "zip_code": "19970",
                    "latitude": "38.556507",
                    "longitude": "-75.100246",
                }
            ],
        },
        {
            "state": "Florida",
            "sub_locations": [
                {
                    "store_address": "20695 Biscayne Boulevard,Aventura",
                    "store_name": "20695 Biscayne Boulevard",
                    "city_name": "Aventura",
                    "phone_number": "tel:+13059331901",
                    "zip_code": "33180",
                    "latitude": "25.960389",
                    "longitude": "-80.143113",
                }
            ],
        },
        {
            "state": "Georgia",
            "sub_locations": [
                {
                    "store_address": "1194 Prince Avenue,Athens",
                    "store_name": "1194 Prince Avenue",
                    "city_name": "Athens",
                    "phone_number": "tel:+17063532286",
                    "zip_code": "30606",
                    "latitude": "33.937551",
                    "longitude": "-83.424964",
                },
                {
                    "store_address": "1573 S Lumpkin St,Athens",
                    "store_name": "1573 S Lumpkin St",
                    "city_name": "Athens",
                    "phone_number": "tel:+17065480080",
                    "zip_code": "30605",
                    "latitude": "33.905911",
                    "longitude": "-83.323577",
                },
                {
                    "store_address": "1911 Epps Bridge Road,Athens",
                    "store_name": "1911 Epps Bridge Road",
                    "city_name": "Athens",
                    "phone_number": "tel:+17063538004",
                    "zip_code": "30606",
                    "latitude": "33.937551",
                    "longitude": "-83.424964",
                },
                {
                    "store_address": "3465 Jefferson Rd.,Athens",
                    "store_name": "3465 Jefferson Rd.",
                    "city_name": "Athens",
                    "phone_number": "tel:+16785445845",
                    "zip_code": "30607",
                    "latitude": "34.017305",
                    "longitude": "-83.447551",
                },
                {
                    "store_address": "824 Hull Rd,Athens",
                    "store_name": "824 Hull Rd",
                    "city_name": "Athens",
                    "phone_number": "tel:+17065485583",
                    "zip_code": "30604",
                    "latitude": "0",
                    "longitude": "0",
                },
            ],
        },
        {
            "state": "Hawaii",
            "sub_locations": [
                {
                    "store_address": "1020 Keolu Dr,Kailua",
                    "store_name": "1020 Keolu Dr",
                    "city_name": "Kailua",
                    "phone_number": "tel:+18082624216",
                    "zip_code": "96734",
                    "latitude": "21.395084",
                    "longitude": "-157.758188",
                },
                {
                    "store_address": "200 Hamakua Drive,Kailua",
                    "store_name": "200 Hamakua Drive",
                    "city_name": "Kailua",
                    "phone_number": "tel:+18082622829",
                    "zip_code": "96734",
                    "latitude": "21.395084",
                    "longitude": "-157.758188",
                },
                {
                    "store_address": "Marine Corps Air Station,Kailua",
                    "store_name": "Marine Corps Air Station",
                    "city_name": "Kailua",
                    "phone_number": "tel:+18083670027",
                    "zip_code": "96734",
                    "latitude": "21.395084",
                    "longitude": "-157.758188",
                },
            ],
        },
        {
            "state": "Idaho",
            "sub_locations": [
                {
                    "store_address": "2205 Overland Rd,Burley",
                    "store_name": "2205 Overland Rd",
                    "city_name": "Burley",
                    "phone_number": "tel:+12086784225",
                    "zip_code": "83318",
                    "latitude": "42.439675",
                    "longitude": "-113.815864",
                },
                {
                    "store_address": "702 N Overland Ave,Burley",
                    "store_name": "702 N Overland Ave",
                    "city_name": "Burley",
                    "phone_number": "tel:+12086792721",
                    "zip_code": "83318",
                    "latitude": "42.439675",
                    "longitude": "-113.815864",
                },
            ],
        },
        {
            "state": "Illinois",
            "sub_locations": [
                {
                    "store_address": "3565 East Vienna Street,Anna",
                    "store_name": "3565 East Vienna Street",
                    "city_name": "Anna",
                    "phone_number": "tel:+16188335049",
                    "zip_code": "62906",
                    "latitude": "37.462109",
                    "longitude": "-89.17253",
                }
            ],
        },
        {
            "state": "Indiana",
            "sub_locations": [
                {
                    "store_address": "517 Green Blvd,Aurora",
                    "store_name": "517 Green Blvd",
                    "city_name": "Aurora",
                    "phone_number": "tel:+18129263509",
                    "zip_code": "47001",
                    "latitude": "39.072665",
                    "longitude": "-84.965538",
                }
            ],
        },
        {
            "state": "Kansas",
            "sub_locations": [
                {
                    "store_address": "509 W 8th St.,Beloit",
                    "store_name": "509 W 8th St.",
                    "city_name": "Beloit",
                    "phone_number": "tel:+17857384100",
                    "zip_code": "67420",
                    "latitude": "39.400935",
                    "longitude": "-98.085468",
                }
            ],
        },
        {
            "state": "Kentucky",
            "sub_locations": [
                {
                    "store_address": "45 Fairfield Ave,Bellevue",
                    "store_name": "45 Fairfield Ave",
                    "city_name": "Bellevue",
                    "phone_number": "tel:+18594314362",
                    "zip_code": "41073",
                    "latitude": "39.101364",
                    "longitude": "-84.478768",
                }
            ],
        },
        {
            "state": "Louisiana",
            "sub_locations": [
                {
                    "store_address": "278 Main St,Baker",
                    "store_name": "278 Main St",
                    "city_name": "Baker",
                    "phone_number": "tel:+12257758173",
                    "zip_code": "70714",
                    "latitude": "30.587189",
                    "longitude": "-91.127633",
                }
            ],
        },
        {
            "state": "Maine",
            "sub_locations": [
                {
                    "store_address": "989 Wiscasset Rd,Boothbay",
                    "store_name": "989 Wiscasset Rd",
                    "city_name": "Boothbay",
                    "phone_number": "tel:+12076339925",
                    "zip_code": "04537",
                    "latitude": "43.875449",
                    "longitude": "-69.620688",
                }
            ],
        },
        {
            "state": "Maryland",
            "sub_locations": [
                {
                    "store_address": "100 Back River Neck Rd,Baltimore",
                    "store_name": "100 Back River Neck Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103913470",
                    "zip_code": "21221",
                    "latitude": "39.289205",
                    "longitude": "-76.43477",
                },
                {
                    "store_address": "110 Reisterstown Rd,Baltimore",
                    "store_name": "110 Reisterstown Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104865066",
                    "zip_code": "21208",
                    "latitude": "39.381174",
                    "longitude": "-76.721002",
                },
                {
                    "store_address": "1209 North Charles St.,Baltimore",
                    "store_name": "1209 North Charles St.",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102441317",
                    "zip_code": "21201",
                    "latitude": "39.294832",
                    "longitude": "-76.622229",
                },
                {
                    "store_address": "1251 W Pratt St,Baltimore",
                    "store_name": "1251 W Pratt St",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103851118",
                    "zip_code": "21223",
                    "latitude": "39.28283",
                    "longitude": "-76.654",
                },
                {
                    "store_address": "1407 Sulphur Spring Rd,Baltimore",
                    "store_name": "1407 Sulphur Spring Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102427802",
                    "zip_code": "21227",
                    "latitude": "39.23997",
                    "longitude": "-76.67945",
                },
                {
                    "store_address": "1520 West North Ave.,Baltimore",
                    "store_name": "1520 West North Ave.",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102255103",
                    "zip_code": "21217",
                    "latitude": "39.308473",
                    "longitude": "-76.639154",
                },
                {
                    "store_address": "1600 W. Mount Royal Avenue,Baltimore",
                    "store_name": "1600 W. Mount Royal Avenue",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102253047",
                    "zip_code": "21217",
                    "latitude": "39.308473",
                    "longitude": "-76.639154",
                },
                {
                    "store_address": "1700 E Cold Spring Lane,Baltimore",
                    "store_name": "1700 E Cold Spring Lane",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14438854666",
                    "zip_code": "21251",
                    "latitude": "39.344707",
                    "longitude": "-76.581242",
                },
                {
                    "store_address": "1718 Reistertown Rd,Baltimore",
                    "store_name": "1718 Reistertown Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14105801133",
                    "zip_code": "21208",
                    "latitude": "39.381174",
                    "longitude": "-76.721002",
                },
                {
                    "store_address": "1722 East Northern Parkway,Baltimore",
                    "store_name": "1722 East Northern Parkway",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14439613347",
                    "zip_code": "21239",
                    "latitude": "39.367099",
                    "longitude": "-76.589171",
                },
                {
                    "store_address": "1725 Chesaco Ave,Baltimore",
                    "store_name": "1725 Chesaco Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14109298559",
                    "zip_code": "21237",
                    "latitude": "39.341939",
                    "longitude": "-76.495443",
                },
                {
                    "store_address": "1800 Russell St,Baltimore",
                    "store_name": "1800 Russell St",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106855167",
                    "zip_code": "21230",
                    "latitude": "39.26613",
                    "longitude": "-76.623803",
                },
                {
                    "store_address": "1800 Washington Blvd,Baltimore",
                    "store_name": "1800 Washington Blvd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14107521777",
                    "zip_code": "21230",
                    "latitude": "39.26613",
                    "longitude": "-76.623803",
                },
                {
                    "store_address": "19 Shipping Place,Baltimore",
                    "store_name": "19 Shipping Place",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102822796",
                    "zip_code": "21222",
                    "latitude": "39.26484",
                    "longitude": "-76.492566",
                },
                {
                    "store_address": "1950 N Broadway,Baltimore",
                    "store_name": "1950 N Broadway",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106626665",
                    "zip_code": "21213",
                    "latitude": "39.315031",
                    "longitude": "-76.577429",
                },
                {
                    "store_address": "2149 Patapsco Ave.,Baltimore",
                    "store_name": "2149 Patapsco Ave.",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14105252994",
                    "zip_code": "21230",
                    "latitude": "39.26613",
                    "longitude": "-76.623803",
                },
                {
                    "store_address": "22 S. Greene Street,Baltimore",
                    "store_name": "22 S. Greene Street",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103282397",
                    "zip_code": "21201",
                    "latitude": "39.294832",
                    "longitude": "-76.622229",
                },
                {
                    "store_address": "2309 Cleanleigh Dr,Baltimore",
                    "store_name": "2309 Cleanleigh Dr",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14108820052",
                    "zip_code": "21234",
                    "latitude": "39.393417",
                    "longitude": "-76.534228",
                },
                {
                    "store_address": "2401 Liberty Heights Ave,Baltimore",
                    "store_name": "2401 Liberty Heights Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104628962",
                    "zip_code": "21215",
                    "latitude": "39.345241",
                    "longitude": "-76.683566",
                },
                {
                    "store_address": "2401 West Belvedere Avenue,Baltimore",
                    "store_name": "2401 West Belvedere Avenue",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106016556",
                    "zip_code": "21215",
                    "latitude": "39.345241",
                    "longitude": "-76.683566",
                },
                {
                    "store_address": "2407 Frederick Ave,Baltimore",
                    "store_name": "2407 Frederick Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106245258",
                    "zip_code": "21223",
                    "latitude": "39.28283",
                    "longitude": "-76.654",
                },
                {
                    "store_address": "2500 W North Ave,Baltimore",
                    "store_name": "2500 W North Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14109511236",
                    "zip_code": "21216",
                    "latitude": "39.310595",
                    "longitude": "-76.671717",
                },
                {
                    "store_address": "2552 Quarry Lake Drive,Baltimore",
                    "store_name": "2552 Quarry Lake Drive",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104155206",
                    "zip_code": "21209",
                    "latitude": "39.373191",
                    "longitude": "-76.670003",
                },
                {
                    "store_address": "2623 Washington Blvd,Baltimore",
                    "store_name": "2623 Washington Blvd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106245489",
                    "zip_code": "21230",
                    "latitude": "39.26613",
                    "longitude": "-76.623803",
                },
                {
                    "store_address": "2701 Rolling Rd,Baltimore",
                    "store_name": "2701 Rolling Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14434293507",
                    "zip_code": "21244",
                    "latitude": "39.334931",
                    "longitude": "-76.776589",
                },
                {
                    "store_address": "2725 Sisson St,Baltimore",
                    "store_name": "2725 Sisson St",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104672111",
                    "zip_code": "21211",
                    "latitude": "39.329817",
                    "longitude": "-76.639408",
                },
                {
                    "store_address": "2801 Edmondson Ave,Baltimore",
                    "store_name": "2801 Edmondson Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102330050",
                    "zip_code": "21223",
                    "latitude": "39.28283",
                    "longitude": "-76.654",
                },
                {
                    "store_address": "300 North Charles St,Baltimore",
                    "store_name": "300 North Charles St",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14105450688",
                    "zip_code": "21201",
                    "latitude": "39.294832",
                    "longitude": "-76.622229",
                },
                {
                    "store_address": "3009-A Eastern Blvd,Baltimore",
                    "store_name": "3009-A Eastern Blvd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14105743434",
                    "zip_code": "21220",
                    "latitude": "39.34728",
                    "longitude": "-76.39008",
                },
                {
                    "store_address": "31 South Calvert Street,Baltimore",
                    "store_name": "31 South Calvert Street",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102448873",
                    "zip_code": "21202",
                    "latitude": "39.296526",
                    "longitude": "-76.607016",
                },
                {
                    "store_address": "3107 Hammons Ferry Road,Baltimore",
                    "store_name": "3107 Hammons Ferry Road",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102422610",
                    "zip_code": "21227",
                    "latitude": "39.23997",
                    "longitude": "-76.67945",
                },
                {
                    "store_address": "3232 Greenmount Ave.,Baltimore",
                    "store_name": "3232 Greenmount Ave.",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14108780694",
                    "zip_code": "21218",
                    "latitude": "39.330107",
                    "longitude": "-76.601451",
                },
                {
                    "store_address": "3233 St Paul St,Baltimore",
                    "store_name": "3233 St Paul St",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102350050",
                    "zip_code": "21218",
                    "latitude": "39.330107",
                    "longitude": "-76.601451",
                },
                {
                    "store_address": "3601 Dolfield Ave.,Baltimore",
                    "store_name": "3601 Dolfield Ave.",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106647100",
                    "zip_code": "21215",
                    "latitude": "39.345241",
                    "longitude": "-76.683566",
                },
                {
                    "store_address": "37 E 25th St,Baltimore",
                    "store_name": "37 E 25th St",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106625762",
                    "zip_code": "21218",
                    "latitude": "39.330107",
                    "longitude": "-76.601451",
                },
                {
                    "store_address": "37 S. Charles Street,Baltimore",
                    "store_name": "37 S. Charles Street",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14109625548",
                    "zip_code": "21202",
                    "latitude": "39.296526",
                    "longitude": "-76.607016",
                },
                {
                    "store_address": "3705 Falls Rd,Baltimore",
                    "store_name": "3705 Falls Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103664800",
                    "zip_code": "21211",
                    "latitude": "39.329817",
                    "longitude": "-76.639408",
                },
                {
                    "store_address": "4206 Frankford Ave,Baltimore",
                    "store_name": "4206 Frankford Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104856392",
                    "zip_code": "21206",
                    "latitude": "39.338428",
                    "longitude": "-76.538877",
                },
                {
                    "store_address": "4600-D Northern Parkway,Baltimore",
                    "store_name": "4600-D Northern Parkway",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103585803",
                    "zip_code": "21215",
                    "latitude": "39.345241",
                    "longitude": "-76.683566",
                },
                {
                    "store_address": "4628 Wilkens Ave,Baltimore",
                    "store_name": "4628 Wilkens Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102424633",
                    "zip_code": "21229",
                    "latitude": "39.284242",
                    "longitude": "-76.691404",
                },
                {
                    "store_address": "4901 Erdman Ave,Baltimore",
                    "store_name": "4901 Erdman Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14105633963",
                    "zip_code": "21205",
                    "latitude": "39.30229",
                    "longitude": "-76.564482",
                },
                {
                    "store_address": "5112 Sinclair Lane,Baltimore",
                    "store_name": "5112 Sinclair Lane",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103259181",
                    "zip_code": "21206",
                    "latitude": "39.338428",
                    "longitude": "-76.538877",
                },
                {
                    "store_address": "5209 Windsor Mill Road,Baltimore",
                    "store_name": "5209 Windsor Mill Road",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104484979",
                    "zip_code": "21207",
                    "latitude": "39.324167",
                    "longitude": "-76.719484",
                },
                {
                    "store_address": "5250 Campbell Blvd,Baltimore",
                    "store_name": "5250 Campbell Blvd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14109339303",
                    "zip_code": "21236",
                    "latitude": "39.388421",
                    "longitude": "-76.48355",
                },
                {
                    "store_address": "5311 Baltimore National Pike,Baltimore",
                    "store_name": "5311 Baltimore National Pike",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104558396",
                    "zip_code": "21229",
                    "latitude": "39.284242",
                    "longitude": "-76.691404",
                },
                {
                    "store_address": "5417 Reisterstown Rd,Baltimore",
                    "store_name": "5417 Reisterstown Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14105851085",
                    "zip_code": "21215",
                    "latitude": "39.345241",
                    "longitude": "-76.683566",
                },
                {
                    "store_address": "55 Market Place,Baltimore",
                    "store_name": "55 Market Place",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14107796361",
                    "zip_code": "21202",
                    "latitude": "39.296526",
                    "longitude": "-76.607016",
                },
                {
                    "store_address": "5520 Reisterstown Rd.,Baltimore",
                    "store_name": "5520 Reisterstown Rd.",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103188955",
                    "zip_code": "21215",
                    "latitude": "39.345241",
                    "longitude": "-76.683566",
                },
                {
                    "store_address": "5638 Baltimore National Pike,Baltimore",
                    "store_name": "5638 Baltimore National Pike",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104550557",
                    "zip_code": "21228",
                    "latitude": "39.272857",
                    "longitude": "-76.747741",
                },
                {
                    "store_address": "5650 The Alameda,Baltimore",
                    "store_name": "5650 The Alameda",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103234661",
                    "zip_code": "21239",
                    "latitude": "39.367099",
                    "longitude": "-76.589171",
                },
                {
                    "store_address": "600 N Wolfe St,Baltimore",
                    "store_name": "600 N Wolfe St",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14105025098",
                    "zip_code": "21287",
                    "latitude": "0",
                    "longitude": "0",
                },
                {
                    "store_address": "6109 Belair Road,Baltimore",
                    "store_name": "6109 Belair Road",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14104889388",
                    "zip_code": "21206",
                    "latitude": "39.338428",
                    "longitude": "-76.538877",
                },
                {
                    "store_address": "632 S. Broadway,Baltimore",
                    "store_name": "632 S. Broadway",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14438737033",
                    "zip_code": "21231",
                    "latitude": "39.2872",
                    "longitude": "-76.591953",
                },
                {
                    "store_address": "6322 Kenwood Ave.,Baltimore",
                    "store_name": "6322 Kenwood Ave.",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14438680999",
                    "zip_code": "21237",
                    "latitude": "39.341939",
                    "longitude": "-76.495443",
                },
                {
                    "store_address": "6350 York Road,Baltimore",
                    "store_name": "6350 York Road",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14438417190",
                    "zip_code": "21212",
                    "latitude": "39.368561",
                    "longitude": "-76.614898",
                },
                {
                    "store_address": "6500 D Eastern Avenue,Baltimore",
                    "store_name": "6500 D Eastern Avenue",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14437596890",
                    "zip_code": "21224",
                    "latitude": "39.27486",
                    "longitude": "-76.542833",
                },
                {
                    "store_address": "6616 Holabird Ave,Baltimore",
                    "store_name": "6616 Holabird Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106333260",
                    "zip_code": "21224",
                    "latitude": "39.27486",
                    "longitude": "-76.542833",
                },
                {
                    "store_address": "6638 Security Blvd,Baltimore",
                    "store_name": "6638 Security Blvd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102651307",
                    "zip_code": "21207",
                    "latitude": "39.324167",
                    "longitude": "-76.719484",
                },
                {
                    "store_address": "6900 Dogwood Rd,Baltimore",
                    "store_name": "6900 Dogwood Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14434366111",
                    "zip_code": "21244",
                    "latitude": "39.334931",
                    "longitude": "-76.776589",
                },
                {
                    "store_address": "6901 Security Boulevard,Baltimore",
                    "store_name": "6901 Security Boulevard",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14432727973",
                    "zip_code": "21244",
                    "latitude": "39.334931",
                    "longitude": "-76.776589",
                },
                {
                    "store_address": "7031 Liberty Road,Baltimore",
                    "store_name": "7031 Liberty Road",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14433487857",
                    "zip_code": "21207",
                    "latitude": "39.324167",
                    "longitude": "-76.719484",
                },
                {
                    "store_address": "7050 Friendship Road,Baltimore",
                    "store_name": "7050 Friendship Road",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14108504040",
                    "zip_code": "21240",
                    "latitude": "39.17428",
                    "longitude": "-76.671514",
                },
                {
                    "store_address": "750 Concourse Circle,Baltimore",
                    "store_name": "750 Concourse Circle",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106302481",
                    "zip_code": "21220",
                    "latitude": "39.34728",
                    "longitude": "-76.39008",
                },
                {
                    "store_address": "7698-A Belair Rd,Baltimore",
                    "store_name": "7698-A Belair Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14106656091",
                    "zip_code": "21236",
                    "latitude": "39.388421",
                    "longitude": "-76.48355",
                },
                {
                    "store_address": "7839 Eastern Avenue,Baltimore",
                    "store_name": "7839 Eastern Avenue",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102841599",
                    "zip_code": "21224",
                    "latitude": "39.27486",
                    "longitude": "-76.542833",
                },
                {
                    "store_address": "8037 Liberty Rd,Baltimore",
                    "store_name": "8037 Liberty Rd",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14109227827",
                    "zip_code": "21244",
                    "latitude": "39.334931",
                    "longitude": "-76.776589",
                },
                {
                    "store_address": "827 N Charles Street,Baltimore",
                    "store_name": "827 N Charles Street",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14102441468",
                    "zip_code": "21201",
                    "latitude": "39.294832",
                    "longitude": "-76.622229",
                },
                {
                    "store_address": "8335 Harford Road,Baltimore",
                    "store_name": "8335 Harford Road",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14108824532",
                    "zip_code": "21234",
                    "latitude": "39.393417",
                    "longitude": "-76.534228",
                },
                {
                    "store_address": "845 E Fort Ave,Baltimore",
                    "store_name": "845 E Fort Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14105390511",
                    "zip_code": "21230",
                    "latitude": "39.26613",
                    "longitude": "-76.623803",
                },
                {
                    "store_address": "900 Canton Ave,Baltimore",
                    "store_name": "900 Canton Ave",
                    "city_name": "Baltimore",
                    "phone_number": "tel:+14103682960",
                    "zip_code": "21229",
                    "latitude": "39.284242",
                    "longitude": "-76.691404",
                },
            ],
        },
        {
            "state": "Massachusetts",
            "sub_locations": [
                {
                    "store_address": "68-70 Auburn Street,Auburn",
                    "store_name": "68-70 Auburn Street",
                    "city_name": "Auburn",
                    "phone_number": "tel:+15084078997",
                    "zip_code": "01501",
                    "latitude": "42.198708",
                    "longitude": "-71.846006",
                }
            ],
        },
        {
            "state": "Michigan",
            "sub_locations": [
                {
                    "store_address": "1 Campus Drive,Allendale",
                    "store_name": "1 Campus Drive",
                    "city_name": "Allendale",
                    "phone_number": "tel:+16163313127",
                    "zip_code": "49401",
                    "latitude": "42.975656",
                    "longitude": "-85.939287",
                },
                {
                    "store_address": "6175 Lake Michigan Dr,Allendale",
                    "store_name": "6175 Lake Michigan Dr",
                    "city_name": "Allendale",
                    "phone_number": "tel:+16168957820",
                    "zip_code": "49401",
                    "latitude": "42.975656",
                    "longitude": "-85.939287",
                },
            ],
        },
        {
            "state": "Minnesota",
            "sub_locations": [
                {
                    "store_address": "228 East Main Street,Anoka",
                    "store_name": "228 East Main Street",
                    "city_name": "Anoka",
                    "phone_number": "tel:+17632053914",
                    "zip_code": "55303",
                    "latitude": "45.288298",
                    "longitude": "-93.431102",
                },
                {
                    "store_address": "3603 Round Lake Blvd,Anoka",
                    "store_name": "3603 Round Lake Blvd",
                    "city_name": "Anoka",
                    "phone_number": "tel:+17634211983",
                    "zip_code": "55303",
                    "latitude": "45.288298",
                    "longitude": "-93.431102",
                },
            ],
        },
        {
            "state": "Mississippi",
            "sub_locations": [
                {
                    "store_address": "14880 US Highway 49,Belzoni",
                    "store_name": "14880 US Highway 49",
                    "city_name": "Belzoni",
                    "phone_number": "tel:+16622470037",
                    "zip_code": "39038",
                    "latitude": "33.18606",
                    "longitude": "-90.484577",
                }
            ],
        },
        {
            "state": "Missouri",
            "sub_locations": [
                {
                    "store_address": "4852 South Hwy FF,Battlefield",
                    "store_name": "4852 South Hwy FF",
                    "city_name": "Battlefield",
                    "phone_number": "tel:+14177715752",
                    "zip_code": "65619",
                    "latitude": "37.121719",
                    "longitude": "-93.394691",
                }
            ],
        },
        {
            "state": "Montana",
            "sub_locations": [
                {
                    "store_address": "215 North Main,Conrad",
                    "store_name": "215 North Main",
                    "city_name": "Conrad",
                    "phone_number": "tel:+14062780195",
                    "zip_code": "59425",
                    "latitude": "48.187163",
                    "longitude": "-111.898576",
                }
            ],
        },
        {
            "state": "Nebraska",
            "sub_locations": [
                {
                    "store_address": "308 W. Main Street,Battle Creek",
                    "store_name": "308 W. Main Street",
                    "city_name": "Battle Creek",
                    "phone_number": "tel:+14026751485",
                    "zip_code": "68715",
                    "latitude": "41.963891",
                    "longitude": "-97.609897",
                }
            ],
        },
        {
            "state": "Nevada",
            "sub_locations": [
                {
                    "store_address": "1550 E Newlands Dr,Fernley",
                    "store_name": "1550 E Newlands Dr",
                    "city_name": "Fernley",
                    "phone_number": "tel:+17758356677",
                    "zip_code": "89408",
                    "latitude": "39.565417",
                    "longitude": "-119.174165",
                },
                {
                    "store_address": "470 E Main Street,Fernley",
                    "store_name": "470 E Main Street",
                    "city_name": "Fernley",
                    "phone_number": "tel:+17755756200",
                    "zip_code": "89408",
                    "latitude": "39.565417",
                    "longitude": "-119.174165",
                },
            ],
        },
        {
            "state": "New Hampshire",
            "sub_locations": [
                {
                    "store_address": "45 Central Ave,Dover",
                    "store_name": "45 Central Ave",
                    "city_name": "Dover",
                    "phone_number": "tel:+16033435907",
                    "zip_code": "03820",
                    "latitude": "43.190658",
                    "longitude": "-70.887655",
                },
                {
                    "store_address": "892 Central Avenue,Dover",
                    "store_name": "892 Central Avenue",
                    "city_name": "Dover",
                    "phone_number": "tel:+16037409666",
                    "zip_code": "03820",
                    "latitude": "43.190658",
                    "longitude": "-70.887655",
                },
            ],
        },
        {
            "state": "New Jersey",
            "sub_locations": [
                {
                    "store_address": "300 Wooton St,Boonton",
                    "store_name": "300 Wooton St",
                    "city_name": "Boonton",
                    "phone_number": "tel:+19733341122",
                    "zip_code": "07005",
                    "latitude": "40.932771",
                    "longitude": "-74.417304",
                }
            ],
        },
        {
            "state": "New Mexico",
            "sub_locations": [
                {
                    "store_address": "2009 W Pierce,Carlsbad",
                    "store_name": "2009 W Pierce",
                    "city_name": "Carlsbad",
                    "phone_number": "tel:+15752341393",
                    "zip_code": "88220",
                    "latitude": "32.311474",
                    "longitude": "-104.431928",
                },
                {
                    "store_address": "2401 S Canal St,Carlsbad",
                    "store_name": "2401 S Canal St",
                    "city_name": "Carlsbad",
                    "phone_number": "tel:+15756288890",
                    "zip_code": "88220",
                    "latitude": "32.311474",
                    "longitude": "-104.431928",
                },
                {
                    "store_address": "2521 S Canal St,Carlsbad",
                    "store_name": "2521 S Canal St",
                    "city_name": "Carlsbad",
                    "phone_number": "tel:+15758853608",
                    "zip_code": "88220",
                    "latitude": "32.311474",
                    "longitude": "-104.431928",
                },
            ],
        },
        {
            "state": "New York",
            "sub_locations": [
                {
                    "store_address": "The New York State Thruway,Angola",
                    "store_name": "The New York State Thruway",
                    "city_name": "Angola",
                    "phone_number": "tel:+17165490020",
                    "zip_code": "14006",
                    "latitude": "42.63313",
                    "longitude": "-79.021745",
                }
            ],
        },
        {
            "state": "North Carolina",
            "sub_locations": [
                {
                    "store_address": "1226 East Dixie Drive,Ashboro",
                    "store_name": "1226 East Dixie Drive",
                    "city_name": "Ashboro",
                    "phone_number": "tel:+13366262355",
                    "zip_code": "27203",
                    "latitude": "35.728464",
                    "longitude": "-79.786527",
                }
            ],
        },
        {
            "state": "North Dakota",
            "sub_locations": [
                {
                    "store_address": "113 1st Street North,Ellendale",
                    "store_name": "113 1st Street North",
                    "city_name": "Ellendale",
                    "phone_number": "tel:+18008884848",
                    "zip_code": "58436",
                    "latitude": "46.089591",
                    "longitude": "-98.581639",
                }
            ],
        },
        {
            "state": "Ohio",
            "sub_locations": [
                {
                    "store_address": "104 S Main St,Antwerp",
                    "store_name": "104 S Main St",
                    "city_name": "Antwerp",
                    "phone_number": "tel:+14192582363",
                    "zip_code": "45813",
                    "latitude": "41.192303",
                    "longitude": "-84.733158",
                }
            ],
        },
        {
            "state": "Oklahoma",
            "sub_locations": [
                {
                    "store_address": "228 Odor St,Arcadia",
                    "store_name": "228 Odor St",
                    "city_name": "Arcadia",
                    "phone_number": "tel:+14053962754",
                    "zip_code": "73007",
                    "latitude": "35.685355",
                    "longitude": "-97.327459",
                }
            ],
        },
        {
            "state": "Oregon",
            "sub_locations": [
                {
                    "store_address": "19745 Baker Rd,Bend",
                    "store_name": "19745 Baker Rd",
                    "city_name": "Bend",
                    "phone_number": "tel:+15413890503",
                    "zip_code": "97702",
                    "latitude": "44.000626",
                    "longitude": "-121.233812",
                },
                {
                    "store_address": "515 NE Bellevue Dr,Bend",
                    "store_name": "515 NE Bellevue Dr",
                    "city_name": "Bend",
                    "phone_number": "tel:+15413301155",
                    "zip_code": "97701",
                    "latitude": "44.112338",
                    "longitude": "-121.20634",
                },
                {
                    "store_address": "61292 Highway 97,Bend",
                    "store_name": "61292 Highway 97",
                    "city_name": "Bend",
                    "phone_number": "tel:+15413833961",
                    "zip_code": "97702",
                    "latitude": "44.000626",
                    "longitude": "-121.233812",
                },
                {
                    "store_address": "62929 N Hwy 97,Bend",
                    "store_name": "62929 N Hwy 97",
                    "city_name": "Bend",
                    "phone_number": "tel:+15413888847",
                    "zip_code": "97701",
                    "latitude": "44.112338",
                    "longitude": "-121.20634",
                },
            ],
        },
        {
            "state": "Pennsylvania",
            "sub_locations": [
                {
                    "store_address": "801 W Centre St,Ashland",
                    "store_name": "801 W Centre St",
                    "city_name": "Ashland",
                    "phone_number": "tel:+15708751782",
                    "zip_code": "17921",
                    "latitude": "40.751575",
                    "longitude": "-76.360586",
                }
            ],
        },
        {
            "state": "Rhode Island",
            "sub_locations": [
                {
                    "store_address": "99 Fortin Rd,Kingston",
                    "store_name": "99 Fortin Rd",
                    "city_name": "Kingston",
                    "phone_number": "tel:+14017894490",
                    "zip_code": "02881",
                    "latitude": "41.478083",
                    "longitude": "-71.524717",
                }
            ],
        },
        {
            "state": "South Carolina",
            "sub_locations": [
                {
                    "store_address": "860 Parris Island Gateway,Beaufort",
                    "store_name": "860 Parris Island Gateway",
                    "city_name": "Beaufort",
                    "phone_number": "tel:+18435251551",
                    "zip_code": "29906",
                    "latitude": "32.445112",
                    "longitude": "-80.752875",
                },
                {
                    "store_address": "Hwy 21,Beaufort",
                    "store_name": "Hwy 21",
                    "city_name": "Beaufort",
                    "phone_number": "tel:+18435223130",
                    "zip_code": "29904",
                    "latitude": "32.457441",
                    "longitude": "-80.717905",
                },
            ],
        },
        {
            "state": "South Dakota",
            "sub_locations": [
                {
                    "store_address": "411 N Hwy 77,Dell Rapids",
                    "store_name": "411 N Hwy 77",
                    "city_name": "Dell Rapids",
                    "phone_number": "tel:+16054286075",
                    "zip_code": "57022",
                    "latitude": "43.8409",
                    "longitude": "-96.717205",
                }
            ],
        },
        {
            "state": "Tennessee",
            "sub_locations": [
                {
                    "store_address": "2813-2815 Bartlett Blvd.,Bartlett",
                    "store_name": "2813-2815 Bartlett Blvd.",
                    "city_name": "Bartlett",
                    "phone_number": "tel:+19016569120",
                    "zip_code": "38134",
                    "latitude": "35.174957",
                    "longitude": "-89.859879",
                },
                {
                    "store_address": "6490 Memphis Arlington,Bartlett",
                    "store_name": "6490 Memphis Arlington",
                    "city_name": "Bartlett",
                    "phone_number": "tel:+19014465199",
                    "zip_code": "38135",
                    "latitude": "35.238915",
                    "longitude": "-89.848589",
                },
                {
                    "store_address": "8070 Hwy 64,Bartlett",
                    "store_name": "8070 Hwy 64",
                    "city_name": "Bartlett",
                    "phone_number": "tel:+19013836515",
                    "zip_code": "38133",
                    "latitude": "35.212893",
                    "longitude": "-89.794288",
                },
            ],
        },
        {
            "state": "Texas",
            "sub_locations": [
                {
                    "store_address": "310 Highway 67 W,Alvarado",
                    "store_name": "310 Highway 67 W",
                    "city_name": "Alvarado",
                    "phone_number": "tel:+18177835954",
                    "zip_code": "76009",
                    "latitude": "32.414937",
                    "longitude": "-97.200076",
                }
            ],
        },
        {
            "state": "Utah",
            "sub_locations": [
                {
                    "store_address": "282 W Parrish Ln,Centerville",
                    "store_name": "282 W Parrish Ln",
                    "city_name": "Centerville",
                    "phone_number": "tel:+18012950999",
                    "zip_code": "84014",
                    "latitude": "40.932087",
                    "longitude": "-111.884033",
                }
            ],
        },
        {
            "state": "Vermont",
            "sub_locations": [
                {
                    "store_address": "159 Pearl St,Essex Junction",
                    "store_name": "159 Pearl St",
                    "city_name": "Essex Junction",
                    "phone_number": "tel:+18028729669",
                    "zip_code": "05452",
                    "latitude": "44.538624",
                    "longitude": "-73.050223",
                }
            ],
        },
        {
            "state": "Virginia",
            "sub_locations": [
                {
                    "store_address": "109 N Washington Hwy,Ashland",
                    "store_name": "109 N Washington Hwy",
                    "city_name": "Ashland",
                    "phone_number": "tel:+18043680255",
                    "zip_code": "23005",
                    "latitude": "37.759696",
                    "longitude": "-77.48187",
                },
                {
                    "store_address": "11670 Lakeridge Parkway,Ashland",
                    "store_name": "11670 Lakeridge Parkway",
                    "city_name": "Ashland",
                    "phone_number": "tel:+18047983663",
                    "zip_code": "23005",
                    "latitude": "37.759696",
                    "longitude": "-77.48187",
                },
                {
                    "store_address": "9523 Kings Charter Drive,Ashland",
                    "store_name": "9523 Kings Charter Drive",
                    "city_name": "Ashland",
                    "phone_number": "tel:+18045501725",
                    "zip_code": "23005",
                    "latitude": "37.759696",
                    "longitude": "-77.48187",
                },
            ],
        },
        {
            "state": "Washington",
            "sub_locations": [
                {
                    "store_address": "1 Bellis Fair Pky,Bellingham",
                    "store_name": "1 Bellis Fair Pky",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13606476697",
                    "zip_code": "98226",
                    "latitude": "48.798606",
                    "longitude": "-122.445693",
                },
                {
                    "store_address": "105 Samish Way,Bellingham",
                    "store_name": "105 Samish Way",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13606712861",
                    "zip_code": "98225",
                    "latitude": "48.75094",
                    "longitude": "-122.501286",
                },
                {
                    "store_address": "1310 Lakeway Dr,Bellingham",
                    "store_name": "1310 Lakeway Dr",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13609334635",
                    "zip_code": "98229",
                    "latitude": "48.696127",
                    "longitude": "-122.413538",
                },
                {
                    "store_address": "1317 W Bakerview Rd,Bellingham",
                    "store_name": "1317 W Bakerview Rd",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13607388879",
                    "zip_code": "98226",
                    "latitude": "48.798606",
                    "longitude": "-122.445693",
                },
                {
                    "store_address": "1920 King Street,Bellingham",
                    "store_name": "1920 King Street",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13607151661",
                    "zip_code": "98225",
                    "latitude": "48.75094",
                    "longitude": "-122.501286",
                },
                {
                    "store_address": "3011 Cinema Place,Bellingham",
                    "store_name": "3011 Cinema Place",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13605436976",
                    "zip_code": "98226",
                    "latitude": "48.798606",
                    "longitude": "-122.445693",
                },
                {
                    "store_address": "3123 Old Fairhaven Pkwy,Bellingham",
                    "store_name": "3123 Old Fairhaven Pkwy",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13603895233",
                    "zip_code": "98225",
                    "latitude": "48.75094",
                    "longitude": "-122.501286",
                },
                {
                    "store_address": "3212 NW Ave.,Bellingham",
                    "store_name": "3212 NW Ave.",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13606475494",
                    "zip_code": "98225",
                    "latitude": "48.75094",
                    "longitude": "-122.501286",
                },
                {
                    "store_address": "4152 Meridian,Bellingham",
                    "store_name": "4152 Meridian",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13607159190",
                    "zip_code": "98226",
                    "latitude": "48.798606",
                    "longitude": "-122.445693",
                },
                {
                    "store_address": "504 High Street,Bellingham",
                    "store_name": "504 High Street",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+18008884848",
                    "zip_code": "98225",
                    "latitude": "48.75094",
                    "longitude": "-122.501286",
                },
                {
                    "store_address": "516 High St - Viking Union,Bellingham",
                    "store_name": "516 High St - Viking Union",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13606502340",
                    "zip_code": "98225",
                    "latitude": "48.75094",
                    "longitude": "-122.501286",
                },
                {
                    "store_address": "5927 Guide Meridian,Bellingham",
                    "store_name": "5927 Guide Meridian",
                    "city_name": "Bellingham",
                    "phone_number": "tel:+13606565192",
                    "zip_code": "98226",
                    "latitude": "48.798606",
                    "longitude": "-122.445693",
                },
            ],
        },
        {
            "state": "Washington DC",
            "sub_locations": [
                {
                    "store_address": "2201 C Street NW,Washington, DC",
                    "store_name": "2201 C Street NW",
                    "city_name": "Washington, DC",
                    "phone_number": "tel:+13017428350",
                    "zip_code": "20037",
                    "latitude": "38.898889",
                    "longitude": "-77.055456",
                }
            ],
        },
        {
            "state": "West Virginia",
            "sub_locations": [
                {
                    "store_address": "2497 Valley Rd,Berkeley Springs",
                    "store_name": "2497 Valley Rd",
                    "city_name": "Berkeley Springs",
                    "phone_number": "tel:+13042587884",
                    "zip_code": "25411",
                    "latitude": "39.548748",
                    "longitude": "-78.22147",
                }
            ],
        },
        {
            "state": "Wisconsin",
            "sub_locations": [
                {
                    "store_address": "2500 East Lake Shore Drive,Ashland",
                    "store_name": "2500 East Lake Shore Drive",
                    "city_name": "Ashland",
                    "phone_number": "tel:+17156824005",
                    "zip_code": "54806",
                    "latitude": "46.552396",
                    "longitude": "-90.870143",
                },
                {
                    "store_address": "901 W Lakeshore Dr,Ashland",
                    "store_name": "901 W Lakeshore Dr",
                    "city_name": "Ashland",
                    "phone_number": "tel:+17156828884",
                    "zip_code": "54806",
                    "latitude": "46.552396",
                    "longitude": "-90.870143",
                },
            ],
        },
        {
            "state": "Wyoming",
            "sub_locations": [
                {
                    "store_address": "168 Front Street,Evanston",
                    "store_name": "168 Front Street",
                    "city_name": "Evanston",
                    "phone_number": "tel:+13074443118",
                    "zip_code": "82930",
                    "latitude": "41.016132",
                    "longitude": "-110.64493",
                },
                {
                    "store_address": "1920 Harrison Drive,Evanston",
                    "store_name": "1920 Harrison Drive",
                    "city_name": "Evanston",
                    "phone_number": "tel:+13077894304",
                    "zip_code": "82930",
                    "latitude": "41.016132",
                    "longitude": "-110.64493",
                },
                {
                    "store_address": "289 Bear River Dr,Evanston",
                    "store_name": "289 Bear River Dr",
                    "city_name": "Evanston",
                    "phone_number": "tel:+13077835906",
                    "zip_code": "82930",
                    "latitude": "41.016132",
                    "longitude": "-110.64493",
                },
            ],
        },
    ]

    # Generate CSV file
    generate_excel(all_locations)

import requests
from bs4 import BeautifulSoup
import pandas as pd


def generate_lat_and_long_csv():
    url = "https://gist.github.com/erichurst/7882666"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        headers = soup.find(
            class_="blob-code blob-code-inner js-file-line"
        ).text.strip()
        table = soup.find(
            "table",
            class_="highlight tab-size js-file-line-container js-code-nav-container js-tagsearch-file",
        )

        col_names = headers.split(",")

        df = pd.DataFrame(columns=col_names)

        # Check if the table is found
        if table:
            # Extract the rows and columns from the table
            rows = table.find_all("tr")

            # Skip the first row (header)
            data_rows = rows[1:]

            # Iterate through each row in the table
            for index, row in enumerate(data_rows):
                # Extract the columns from each row
                columns = row.find_all(
                    "td", class_="blob-code blob-code-inner js-file-line"
                )

                # Check if there are columns in the row
                if columns:
                    # Extract ZIP, LAT, and LNG from the columns
                    table_details = columns[0].text.split(",")
                    pin_code = table_details[0].strip()
                    latitude = float(table_details[1].strip())
                    longitude = float(table_details[2].strip())

                    df.loc[index] = [pin_code, latitude, longitude]

        df.to_csv("lat_long.csv", index=False)
        print(f"CSV file generated successfully.")


    else:
        print(f"Error while fetching api: {response.status_code}")
        return


if __name__ == "__main__":
    generate_lat_and_long_csv()
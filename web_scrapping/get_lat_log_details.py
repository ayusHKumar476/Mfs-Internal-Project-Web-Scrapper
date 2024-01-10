import pandas as pd

def get_lat_long_details(zip_code):
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv("lat_long.csv", index_col="ZIP")
        # Check if the ZIP code is present in the DataFrame
        if zip_code not in df.index:
            return {'error': 'ZIP code not found', 'status': 404}

        # Extract latitude and longitude for the specified ZIP code
        latitude = df.loc[zip_code, 'LAT']
        longitude = df.loc[zip_code, 'LNG']

        # print(f"Latitude: {latitude}, Longitude: {longitude}")

        return {
            'lat': latitude,
            'long': longitude,
            'status': 200
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'error': 'Internal Server Error' , 'status': 500}
    

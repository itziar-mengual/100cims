# src/data_processing.py

import geopandas as gpd
import pandas as pd
import os
import numpy as np
from scipy.interpolate import griddata
from shapely.geometry import Point, LineString


def load_shapefiles(shapefile_folder):
    """
    Load shapefiles that contain '_PUN_ACO' in their filename.
    """
    shapefiles = [os.path.join(shapefile_folder, f) for f in os.listdir(shapefile_folder) if
                  "_PUN_ACO" in f and f.endswith(".shp")]
    print("Shapefiles encontrados:", shapefiles)
    return shapefiles


def process_shapefiles(shapefiles):
    """
    Read and combine shapefiles into a single GeoDataFrame.
    """
    combined_gdf = gpd.GeoDataFrame(pd.concat([gpd.read_file(shp) for shp in shapefiles], ignore_index=True))
    combined_gdf = combined_gdf.to_crs("EPSG:3857")  # Set CRS to EPSG:3857
    return combined_gdf


def extract_coordinates(geometry):
    """
    Extract coordinates from geometry.
    """
    if isinstance(geometry, Point):
        return [(geometry.x, geometry.y, geometry.z)]
    elif isinstance(geometry, LineString):
        return list(geometry.coords)
    return None


def process_coordinates(combined_gdf):
    """
    Process coordinates and return valid data.
    """
    geometry_coordinates = combined_gdf.geometry.apply(extract_coordinates)

    def extract_xyz(coords):
        if coords and len(coords) > 0:
            x, y, z = coords[0]
            return x, y, z
        return None, None, None

    combined_gdf['longitude'], combined_gdf['latitude'], combined_gdf['altitude'] = zip(
        *geometry_coordinates.apply(extract_xyz))
    data = combined_gdf[['longitude', 'latitude', 'altitude']].dropna()

    # Data cleaning and interpolation
    return clean_and_interpolate_data(data)


def clean_and_interpolate_data(data):
    """
    Clean the data and interpolate missing altitude values.
    """
    invalid_altitude = data[data['altitude'] <= 0]
    duplicates = data.groupby(['latitude', 'longitude']).filter(lambda x: x['altitude'].nunique() > 1)
    invalid_data = pd.concat([invalid_altitude, duplicates]).drop_duplicates()

    valid_data = data[~data.index.isin(invalid_data.index)]

    points = valid_data[['latitude', 'longitude']].values
    values = valid_data['altitude'].values
    query_points = invalid_data[['latitude', 'longitude']].values
    invalid_data['altitude'] = griddata(points, values, query_points, method='linear')
    data.update(invalid_data)

    data['latitude'] = data['latitude'] / 100000
    data['longitude'] = data['longitude'] / 10000

    return data


def categorize_and_sort(data, bin_size=50):
    """
    Categorizes the data based on altitude and sorts the categories by mean altitude.

    Parameters:
    - data (DataFrame): DataFrame with 'altitude' column.
    - bin_size (int): Size of the bins for categorization (default is 50 meters).

    Returns:
    - sorted_categories (list): Sorted list of category labels.
    """
    # Categorize the data into bins
    data['category'] = (data['altitude'] // bin_size).astype(int) * bin_size
    data['category'] = data['category'].astype(str) + "m to " + (data['category'] + bin_size).astype(str) + "m"

    # Calculate the mean altitude for each category and sort by it
    category_means = data.groupby('category')['altitude'].mean().reset_index()
    category_means = category_means.sort_values(by='altitude', ascending=True)

    # Return the sorted categories
    sorted_categories = category_means['category'].tolist()
    return data, sorted_categories


def save_processed_data(data, filename):
    """
    Save the processed data to a file.

    Parameters:
    - data (DataFrame): The processed data to save.
    - filename (str): Path where the data will be saved (e.g., CSV or Pickle).
    """
    data.to_csv(filename, index=False)  # Save as CSV. You can also use other formats like .feather or .pickle.


def load_processed_data(filename):
    """
    Load the processed data from a file.

    Parameters:
    - filename (str): Path to the saved data file.

    Returns:
    - DataFrame: The loaded data.
    """
    return pd.read_csv(filename)  # Modify based on the format you choose (e.g., .feather, .pickle)


def rescale_data(data, xy_range):
    """
    Rescale the latitude and altitude columns in the data so that they form square axes.
    Both latitude and altitude will be scaled to have the same range.

    Parameters:
    - data (DataFrame): The dataframe with 'latitude' and 'altitude' columns.
    - x_range (list): The target range for the x-axis (default: [0, 1]).
    - y_range (list): The target range for the y-axis (default: [0, 1]).

    Returns:
    - data (DataFrame): The dataframe with rescaled latitude and altitude.
    """
    # Find the minimum and maximum values for latitude and altitude
    lat_min, lat_max = data['latitude'].min(), data['latitude'].max()
    alt_min, alt_max = data['longitude'].min(), data['longitude'].max()

    # Scale latitude and altitude to the [0, 1] range
    data['latitude'] = (data['latitude'] - lat_min) / (lat_max - lat_min) * (xy_range[1] - xy_range[0]) + xy_range[0]
    data['longitude'] = (data['longitude'] - alt_min) / (alt_max - alt_min) * (xy_range[1] - xy_range[0]) + xy_range[0]

    return data

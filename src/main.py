# main.py

import os
from src.data_processing import load_shapefiles, process_shapefiles, process_coordinates, rescale_data, categorize_and_sort, save_processed_data, load_processed_data
from src.data_maps import plot_concave_hull

# Define paths
shapefile_folder = "data/shapefiles"
output_folder = "data/output"
processed_data_file = os.path.join(output_folder, "processed_data.csv")
processed_peak_file = os.path.join("../data/CimsCatalunya.csv")

# Check if the processed data file exists
if os.path.exists(processed_peak_file):
    print("Loading preprocessed peak data...")
    data = load_processed_data(processed_peak_file)
elif os.path.exists(processed_data_file):
    print("Loading preprocessed data...")
    data = load_processed_data(processed_data_file)
else:
    # Load and process shapefiles
    shapefiles = load_shapefiles(shapefile_folder)
    combined_gdf = process_shapefiles(shapefiles)
    data = process_coordinates(combined_gdf)
    # Save the processed data for future use
    save_processed_data(data, processed_data_file)

data, sorted_categories = categorize_and_sort(data)
xy_range = [0, 333]
data = rescale_data(data, xy_range = xy_range)
start = 0; end = -1
save_dxf = True
alpha = 0.6; smoothing_factor = 10
plot_concave_hull(data, sorted_categories, alpha=alpha,
    start=start, end=end, smoothing_factor=smoothing_factor, save_dxf=save_dxf)
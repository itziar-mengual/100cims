# src/data_maps.py

import alphashape
import plotly.graph_objects as go
from shapely.geometry import MultiPolygon, Polygon
from scipy.interpolate import splprep, splev
import numpy as np
import ezdxf

def smooth_boundary(x, y, smoothing_factor=0.01):
    """
    Smooths the boundary points using cubic splines and ensures the polygon is closed.

    Parameters:
    - x, y (array-like): Arrays of x and y coordinates of the boundary points.
    - smoothing_factor (float): Smoothing factor for the spline.

    Returns:
    - smoothed_x, smoothed_y (array-like): Smoothed x and y coordinates, with the polygon closed.
    """
    tck, u = splprep([x, y], s=smoothing_factor)
    u_fine = np.linspace(0, 1, 500)  # Number of points for smooth curve
    smoothed_x, smoothed_y = splev(u_fine, tck)

    # Ensure the polygon is closed by adding the first point at the end
    smoothed_x = np.append(smoothed_x, smoothed_x[0])
    smoothed_y = np.append(smoothed_y, smoothed_y[0])

    return smoothed_x, smoothed_y

def plot_concave_hull(data, sorted_categories, alpha=20, start=0, end=1, smoothing_factor=0.01, save_dxf=False):
    from main import xy_range  # Assuming this is a valid import

    """
    Plots the concave hull of points for specified categories with optional smoothing.
    If save_dxf is True, saves the smoothed boundaries as a DXF file and the red crosses as another DXF file.

    Parameters:
    - data (DataFrame): DataFrame containing 'category', 'longitude', and 'latitude' columns.
    - sorted_categories (list): List of sorted categories to be analyzed.
    - alpha (float): Alpha parameter for the alphashape to control concavity.
    - start (int): Starting index for the categories to include in the plot.
    - smoothing_factor (float): Smoothing factor for the boundary.
    - save_dxf (bool): Whether to save the red boundaries and crosses to DXF files.
    - dxf_boundaries_filename (str): Path to save the DXF file with boundaries.
    - dxf_crosses_filename (str): Path to save the DXF file with red crosses.
    """
    area_threshold = 4.0
    for idx, category in enumerate(sorted_categories[start:end], start=start):

        all_smoothed_boundaries = []
        all_red_crosses = []

        subsequent_categories = sorted_categories[idx:]
        category_data = data[data['category'].isin(subsequent_categories)]
        points = category_data[['longitude', 'latitude']].values

        hull = alphashape.alphashape(points, alpha)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=category_data['longitude'],
            y=category_data['latitude'],
            mode='markers',
            marker=dict(size=3),
            name='Data Points'
        ))

        if isinstance(hull, MultiPolygon):
            for polygon in hull.geoms:
                # Check if the area of the polygon is greater than the threshold
                if polygon.area > area_threshold:
                    x, y = polygon.exterior.coords.xy
                    smoothed_x, smoothed_y = smooth_boundary(x, y, smoothing_factor)
                    all_smoothed_boundaries.append((smoothed_x, smoothed_y))  # Add to the list of boundaries
                    fig.add_trace(go.Scatter(
                        x=smoothed_x, y=smoothed_y, mode='lines', line=dict(color='red', width=2), name='Smoothed Hull'
                    ))
                else:
                    print(f"Polygon with area {polygon.area:.2f} is smaller than the threshold and has been excluded.")

        elif isinstance(hull, Polygon):
            x, y = hull.exterior.coords.xy
            smoothed_x, smoothed_y = smooth_boundary(x, y, smoothing_factor)
            all_smoothed_boundaries.append((smoothed_x, smoothed_y))  # Add to the list of boundaries
            fig.add_trace(go.Scatter(
                x=smoothed_x, y=smoothed_y, mode='lines', line=dict(color='red', width=2), name='Smoothed Hull'
            ))

        area_threshold -= 0.02

        # Now filter only the points belonging to the current category
        category_peak_data = category_data[category_data['category'] == category]

        # Check if 'nom' exists and filter for non-null 'nom'
        if 'nom' in category_peak_data.columns:
            points_with_nom = category_peak_data[category_peak_data['nom'].notna()]
            if not points_with_nom.empty:
                print(f'There are peaks with names for category {category}.')
                fig.add_trace(go.Scatter(
                    x=points_with_nom['longitude'],
                    y=points_with_nom['latitude'],
                    mode='markers',
                    marker=dict(symbol='circle', color='orange', size=10),  # Red 'X' markers
                    name=f'Points with Name - {category}'
                ))

                # Collect the cross lines for DXF (instead of points, we collect lines)
                for _, row in points_with_nom.iterrows():
                    #line1, line2 = create_cross_lines(row['longitude'], row['latitude'])
                    coordinate = (row['longitude'], row['latitude'])
                    all_red_crosses.append(coordinate)

        # Update layout and axis settings
        fig.update_layout(
            title=f'Concave Hull for {category}',
            xaxis=dict(title='Longitude', range=xy_range),
            yaxis=dict(title='Latitude', range=xy_range),
            showlegend=False,
            autosize=False,
            width=1250,
            height=1250,
        )

        fig.show()
        import os
        from main import output_folder
        if save_dxf:
            category_name = sorted_categories[idx]
            dxf_filename = os.path.join(output_folder, f"{category_name}.dxf50")
            save_combined_to_dxf(all_smoothed_boundaries, all_red_crosses, filename=dxf_filename)

import math
import math

def create_circle(x, y, radius, num_segments=100):
    """
    Creates the coordinates for a circle centered at a given point.

    Parameters:
    - x (float): The x-coordinate (longitude) of the circle center.
    - y (float): The y-coordinate (latitude) of the circle center.
    - radius (float): The radius of the circle.
    - num_segments (int): The number of segments to approximate the circle (higher value for smoother circle).

    Returns:
    - list of tuples: Coordinates for the points forming the circle.
    """
    circle_points = []
    for i in range(num_segments):
        angle = 2 * math.pi * i / num_segments  # Calculate the angle for this segment
        px = x + radius * math.cos(angle)      # x-coordinate of the point
        py = y + radius * math.sin(angle)      # y-coordinate of the point
        circle_points.append((px, py))

    # Close the circle by repeating the first point at the end
    circle_points.append(circle_points[0])
    return circle_points

def create_cross_lines(x, y, size=1):
    """
    Creates the coordinates for the lines forming a cross at a given point,
    rotated by 45 degrees (diagonal cross). This will be saved as a cross
    shape in the DXF file.

    Parameters:
    - x (float): The x-coordinate (longitude) of the cross center.
    - y (float): The y-coordinate (latitude) of the cross center.
    - size (int or float): The size of each arm of the cross (same size used in the plot).

    Returns:
    - list of tuples: Coordinates for the lines forming the rotated cross.
    """

    line1 = [(x - size, y - size), (x + size, y + size)]  # / direction
    line2 = [(x - size, y + size), (x + size, y - size)]  # \ direction

    return line1, line2

import ezdxf
import math
from ezdxf.math import Vec3

def save_combined_to_dxf(all_smoothed_boundaries, crosses, filename="combined.dxf50"):
    """
    Save boundaries, crosses, and a margin square to a single DXF file with different layers and colors.

    Parameters:
    - all_smoothed_boundaries (list): List of tuples where each tuple contains two lists (x, y) of smoothed coordinates.
    - crosses (list): List of crosses where each cross is represented by two lines (as tuples of coordinates).
    - filename (str): The name of the output DXF file.
    """
    doc = ezdxf.new()
    msp = doc.modelspace()

    # Create layers for boundaries, crosses, and the margin
    doc.layers.add(name="Boundaries", color=7)  # Black color for boundaries
    doc.layers.add(name="Crosses", color=1)     # Red color for crosses
    doc.layers.add(name="Margin", color=3)      # Green color for the margin square

    # Add the smoothed boundaries to the "Boundaries" layer
    for smoothed_x, smoothed_y in all_smoothed_boundaries:
        msp.add_lwpolyline(list(zip(smoothed_x, smoothed_y)), dxfattribs={"layer": "Boundaries"})

    # Add the cross lines to the "Crosses" layer
    for cross in crosses:
        x, y = cross
        #start = Vec3(line1[0], line1[1])
        #end = Vec3(line2[0], line2[1])
        #msp.add_line(start, end, dxfattribs={"layer": "Crosses"})
        msp.add_circle(center=(x, y), radius=0.5, dxfattribs={"layer": 'Crosses'})

    # Add the margin square to the "Margin" layer
    margin_square = [(0, 0), (333, 0), (333, 333), (0, 333), (0, 0)]
    msp.add_lwpolyline(margin_square, dxfattribs={"layer": "Margin"})

    # Save the combined DXF file
    doc.saveas(filename)
    print(f"Combined DXF file saved as {filename}")
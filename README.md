# Geospatial Concave Hull Processing and Visualization

This project processes geospatial shapefile data, extracts altitude information, categorizes and sorts the data by altitude, and visualizes the concave hull boundaries of different altitude categories with smoothing. It can also export smoothed boundaries and points of interest to DXF files for CAD applications.

---

## Table of Contents

- [Features](#features)  
- [Installation](#installation)  
- [Project Structure](#project-structure)  
- [Dependencies](#dependencies)  
- [Author](#license)  

---

## Features

- Load and combine multiple shapefiles containing specific geographical data.
- Process 3D coordinates (longitude, latitude, altitude) from geometries.
- Clean and interpolate missing or invalid altitude data.
- Categorize data into altitude bins and sort categories.
- Rescale coordinates to a uniform range for visualization.
- Plot concave hull boundaries with smoothing using alpha shapes.
- Visualize points with named peaks highlighted.
- Export boundaries and points to DXF files with layers for use in CAD software.

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/itziar-mengual/100cims.git
cd itziar-mengual
```

## Project Structure

```python
├── data/
│   ├── shapefiles/         # Input shapefiles with _PUN_ACO suffix
│   └── output/             # Output folder for processed CSV and DXF files
├── src/
│   ├── data_processing.py  # Functions to load/process shapefiles and data
│   └── data_maps.py        # Visualization and DXF export utilities
├── main.py                 # Main execution script
├── README.md               # This file
└── requirements.txt        # Python dependencies (optional)
```
## Dependencies

Python 3.7+
geopandas
pandas
numpy
scipy
shapely
alphashape
plotly
ezdxf

## Author
Itziar Mengual, 2025

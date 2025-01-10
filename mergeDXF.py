import ezdxf
from pathlib import Path

def merge_dxf_files_by_gap(dxf_files, gap, output_directory):
    """
    Merge DXF files into groups based on the specified gap.

    Parameters:
    - dxf_files (list of Path): List of sorted DXF file paths.
    - gap (int): The gap in meters for each combined DXF file (e.g., 100 for 0m-100m).
    - output_directory (Path): Directory to save the combined DXF files.
    """
    num_files_per_gap = gap // 50   # Each file covers a 50m range
    output_directory.mkdir(exist_ok=True)

    for i in range(0, len(dxf_files), num_files_per_gap):
        try:
            selected_files = [dxf_files[i], dxf_files[i + num_files_per_gap]]
        except:
            selected_files = [dxf_files[i], dxf_files[len(dxf_files)-1]]

        # Determine output file name
        start_meter = selected_files[0].stem.split()[0]
        end_meter = selected_files[-1].stem.split()[0]
        output_file = output_directory / f"{start_meter} to {end_meter}.dxf"

        combine_dxf_files(selected_files, output_file, dxf_files)


def combine_dxf_files(selected_files, output_file, all_dxf_files):
    """
    Combine a list of DXF files into a single DXF file with specific rules for layers.
    Retains crosses from all DXFs starting from the start layer.

    Parameters:
    - selected_files (list of Path): List of DXF file paths to merge.
    - output_file (Path): Output file path.
    - all_dxf_files (list of Path): List of all DXF file paths.
    """
    combined_doc = ezdxf.new()
    combined_msp = combined_doc.modelspace()

    # Ensure the layers exist in the combined document with correct colors
    combined_doc.layers.add(name="Boundaries_start", color=7)  # Black
    combined_doc.layers.add(name="Boundaries_end", color=5)    # Blue
    combined_doc.layers.add(name="Crosses", color=1)           # Red
    combined_doc.layers.add(name="Margin", color=3)            # Green

    # Process the start layer
    start_doc = ezdxf.readfile(selected_files[0])
    boundaries_entities = start_doc.modelspace().query('LWPOLYLINE[layer=="Boundaries"]')
    process_layer(boundaries_entities, "Boundaries_start", combined_msp)
    print(f"Copied {len(boundaries_entities)} boundaries from {selected_files[0]}")
    margin_entities = start_doc.modelspace().query('LWPOLYLINE[layer=="Margin"]')
    process_layer(margin_entities, "Margin", combined_msp)

    # Process the end layer
    end_doc = ezdxf.readfile(selected_files[-1])
    boundaries_entities = end_doc.modelspace().query('LWPOLYLINE[layer=="Boundaries"]')
    process_layer(boundaries_entities, "Boundaries_end", combined_msp)
    print(f"Copied {len(boundaries_entities)} boundaries from {selected_files[-1]}")

    # Retain crosses from all DXFs starting from the start layer
    start_index = all_dxf_files.index(selected_files[0])
    for dxf_file in all_dxf_files[start_index:]:
        doc = ezdxf.readfile(dxf_file)
        cross_entities = doc.modelspace().query('CIRCLE[layer=="Crosses"]')
        process_layer(cross_entities, "Crosses", combined_msp)
        print(f"Copied {len(cross_entities)} entities from layer 'Crosses' in {dxf_file}.")

    # Save the combined DXF
    combined_doc.saveas(output_file)
    print(f"Combined DXF saved as {output_file}")

def process_layer(entities, layer, msp):
    for entity in entities:
        entity.dxf.layer = layer # Update layer
        msp.add_entity(entity.copy()) # Add to the combined DXF
    return msp

# Example usage
dxf_files = list(Path("data/output").glob("*.dxf"))
dxf_files = sorted(dxf_files, key=lambda p: int(p.stem.split()[0].rstrip('m')))
output_directory = Path("data/dxf100")

merge_dxf_files_by_gap(dxf_files, gap=100, output_directory=output_directory)
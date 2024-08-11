ghenv.Component.Name = "Gcode Generation LDM"
ghenv.Component.Message = "240811"

#region COMPONENT DESCRIPTION
""" COMPONENT DESCRIPTION 240811
Gcode Generation LDM

This script generates G-code for 3D printing based on a set of 3D curves representing the toolpaths
for each layer of a print. The script outputs a G-code file that directs the printer's movements,
controls extrusion, and manages layer transitions.

Inputs:
    printing_path (List of Curves):
        A list of 3D curves that define the path the 3D printer head will follow for each layer
        of the print. Each curve corresponds to a segment of the printing path for a specific layer.

    nozzle_diameter (Float):
        The diameter of the 3D printer's nozzle, in millimeters. This value is used to determine
        the spacing between points along each curve in the toolpath.

    printing_speed (Float):
        The speed at which the printer head moves while extruding material, specified in millimeters
        per minute (mm/min). The script validates that the speed is within a typical operational range
        (1800 to 11000 mm/min).

    printing_flux (Float or List of Floats):
        A value or list of values that specify the extrusion rate as a percentage for each layer.
        If a single value is provided, it is used for all layers. If a list is provided, each value
        corresponds to a specific layer. The script ensures the list length matches the number
        of layers in the print.

    layer_h (Float):
        The height of each layer in the print, specified in millimeters. This value is used to
        determine the Z-coordinate for each layer and to manage layer transitions.

Outputs:
    gcode (List of Strings):
        The generated G-code commands as a list of strings. This includes all movement, extrusion,
        and retraction commands, as well as start and end G-code blocks, and comments indicating
        the start and end of each layer.

    printing_time (String):
        The estimated time required to complete the print, calculated based on the total length of
        the toolpath and the specified printing speed. The output is formatted as a string in minutes.

    printing_points (List of Points):
        A list of all the points generated along the curves in the toolpath. These points represent
        the exact positions the printer head will move to during the print.

    printing_path_len (String):
        The total length of the printing path in millimeters, formatted as a string.

    layers (Integer):
        The total number of layers in the print, calculated based on the height of the curves
        and the specified layer height.
"""
#endregion

import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
from collections import defaultdict

def generate_gcode(printing_path, nozzle_diameter, printing_speed, printing_flux, layer_h, retract=True):
    # Validate printing speed
    if printing_speed < 1800 or printing_speed > 11000:
        rs.MessageBox("Warning: Printing speed must be between 1800 and 11000 mm/minute.", 0, "Speed Warning")
        return None, None, None, None, None
    
    # Ensure printing_flux is a list, even if a single value is provided
    if not isinstance(printing_flux, list):
        printing_flux = [printing_flux]
    
    # Calculate the number of layers
    max_z = max(curve.PointAtEnd.Z for curve in printing_path)
    num_layers = int(max_z / layer_h) + 1
    
    # Check if the length of printing_flux matches the number of layers
    if len(printing_flux) != 1 and len(printing_flux) < num_layers:
        rs.MessageBox("Warning: The number of flux values does not match the number of layers.", 0, "Flux Mismatch")
        return None, None, None, None, num_layers

    # Group curves by layer
    curves_by_layer = defaultdict(list)
    for curve in printing_path:
        if curve.IsValid and curve.GetLength() > 0:
            layer_index = int(curve.PointAtEnd.Z / layer_h)
            curves_by_layer[layer_index].append(curve)
    
    # Initialize the G-code list and points list
    gcode = []
    printing_points = []
    total_extrusion_distance = 0.0
    total_travel_distance = 0.0  # To store travel distance
    extrusion_amount = 0.0  # Initialize the total extrusion amount
    
    # Start G-code with printing information
    printing_info = [
        ";PRINTING INFORMATION:",
        f";Printing speed: {printing_speed} [mm/min]",
        f";Nozzle diameter: {nozzle_diameter} [mm]",
        f";Number of layers: {num_layers}",
        f";Layer height: {layer_h} [mm]",
        "; -- START GCODE --",
        "G90",  # Absolute positioning
        "M82",  # Set extruder to absolute mode
        "G28",  # Home all axes
        "G92 E0.0000",  # Reset extruder position
        "G1 E-4.0000 F6000",  # Retract filament
        "G1 Z2.000 F12000",  # Move Z-axis
        "; -- END OF START GCODE --"
    ]
    gcode.extend(printing_info)
    
    previous_point = None  # Keep track of the end point of the previous curve
    
    # Iterate through each layer and generate G-code
    for layer_index in sorted(curves_by_layer.keys()):
        # Start of the layer
        gcode.append(f"; Start of layer {layer_index + 1}")
        current_flux = printing_flux[0] if len(printing_flux) == 1 else printing_flux[min(layer_index, len(printing_flux) - 1)]
        
        for curve in curves_by_layer[layer_index]:
            # Divide the curve by the specified segment length
            curve_params = curve.DivideByLength(nozzle_diameter / 2, True)
            if curve_params is None:
                continue
            
            # Create points for each segment
            points = [curve.PointAt(t) for t in curve_params]
            points.insert(0, curve.PointAtStart)
            points.append(curve.PointAtEnd)
            
            for i, pt in enumerate(points):
                if i > 0:  # Skip the first point, as it's only for moving to the start
                    segment_distance = points[i - 1].DistanceTo(pt)
                    total_extrusion_distance += segment_distance
                    extrusion_amount += segment_distance * current_flux
                    gcode_line = f"G1 F{printing_speed:.0f} X{pt.X:.4f} Y{pt.Y:.4f} Z{pt.Z:.4f} E{extrusion_amount:.4f}"
                    gcode.append(gcode_line)
                    printing_points.append(pt)
            
            # Calculate travel distance if there is a previous point
            if previous_point:
                travel_distance = previous_point.DistanceTo(points[0])
                total_travel_distance += travel_distance

            previous_point = points[-1]
        
        # Handle retraction after finishing a curve only if retract is explicitly True
        if bool(retract):
            last_point = points[-1]
            retract_gcode = f"G1 F{printing_speed:.0f} Z{last_point.Z + layer_h:.4f} ; Retract to avoid pulling"
            gcode.append(retract_gcode)
            previous_point.Z += layer_h  # Update the previous point's Z height to account for retraction
        
        # End of the layer
        gcode.append(f"; End of layer {layer_index + 1}")
    
    # End G-code
    end_gcode = [
        "; -- END GCODE --",
        "G92 E0.0000",  # Reset extruder position
        "G1 E-4.0000 F6000",  # Retract filament
        "G28",  # Home all axes
        "; -- END OF END GCODE --"
    ]
    gcode.extend(end_gcode)

    # Calculate total length for printing time calculation
    total_length = total_extrusion_distance + total_travel_distance
    printing_time_minutes = total_length / printing_speed if total_length else 0
    printing_time = f"{printing_time_minutes:.2f} minutes"

    # Outputs for Grasshopper
    printing_path_len =  f"{total_extrusion_distance:.2f} mm"
    printing_speed = f"{printing_speed:.0f} mm/min"
    layers = num_layers

    # Return the list of G-code lines, and the other outputs
    return gcode, printing_time, printing_points, printing_path_len, layers

# Example usage with retract option defaulting to True
g_code, printing_time, printing_points, printing_path_len, layers = generate_gcode(printing_path, nozzle_diameter, printing_speed, printing_flux, layer_h)

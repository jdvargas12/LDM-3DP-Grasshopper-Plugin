ghenv.Component.Message = "240720" 
ghenv.Component.Name = "Gcode Generation LDM"

""" COMPONENT DESCRIPTION v240720
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

    printing_flux (Float):
        A single value that specifies the extrusion rate as a percentage. This value is applied
        uniformly across all layers of the print.

    layer_h (Float):
        The height of each layer in the print, specified in millimeters. This value is used to
        determine the Z-coordinate for each layer and to manage layer transitions.

Outputs:
    gcode (List of Strings):
        The generated G-code commands as a list of strings. This includes all movement, extrusion,
        and retraction commands, as well as start and end G-code blocks.

    printing_time (String):
        The estimated time required to complete the print, calculated based on the total length of
        the toolpath and the specified printing speed. The output is formatted as a string in minutes.

    printing_points (List of Points):
        A list of all the points generated along the curves in the toolpath. These points represent
        the exact positions the printer head will move to during the print.

    printing_path_len (Float):
        The total length of the printing path in millimeters.
"""


import Rhino.Geometry as rg
import rhinoscriptsyntax as rs

def generate_gcode(printing_path, nozzle_diameter, printing_speed, printing_flux, layer_h):
    # Validate printing speed
    if printing_speed < 1800 or printing_speed > 11000:
        rs.MessageBox("Warning: Printing speed must be between 1800 and 11000 mm/minute.", 0, "Speed Warning")
        return None, None, None, None
    
    # Initialize the G-code list and points list
    gcode = []
    printing_points = []
    total_extrusion_distance = 0.0
    total_travel_distance = 0.0
    extrusion_amount = 0.0
    
    # Calculate total printing path length
    printing_path_len = sum(curve.GetLength() for curve in printing_path if curve.IsValid and curve.GetLength() > 0)
    
    # Start G-code with printing information
    printing_info = [
        ";PRINTING INFORMATION:",
        f";Printing path length: {printing_path_len:.2f} [mm]",
        f";Printing speed: {printing_speed} [mm/min]",
        f";Printing flux: {printing_flux} [%]",
        f";Nozzle diameter: {nozzle_diameter} [mm]",
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

    # Main G-code generation
    segment_length = nozzle_diameter / 2
    previous_point = None  # Keeps track of the end point of the previous curve
    
    for curve in printing_path:
        if not curve.IsValid or curve.GetLength() <= 0:
            continue
        
        # Divide the curve by the specified segment length
        curve_params = curve.DivideByLength(segment_length, True)
        if curve_params is None:
            continue
        
        # Create G-code for each segment
        points = [curve.PointAt(t) for t in curve_params]
        points.insert(0, curve.PointAtStart)
        points.append(curve.PointAtEnd)
        
        # Calculate travel distance if there is a previous point
        if previous_point:
            travel_distance = previous_point.DistanceTo(points[0])
            total_travel_distance += travel_distance
        
        # Generate G-code for each segment
        for i, pt in enumerate(points):
            if i > 0:  # Skip the first point, as it's only for moving to the start
                segment_distance = previous_point.DistanceTo(pt)
                total_extrusion_distance += segment_distance
                extrusion_amount += segment_distance * printing_flux
                gcode_line = f"G1 F{printing_speed:.0f} X{pt.X:.4f} Y{pt.Y:.4f} Z{pt.Z:.4f} E{extrusion_amount:.4f}"
                gcode.append(gcode_line)
                printing_points.append(pt)
            previous_point = pt

    # End G-code
    end_gcode = [
        "; -- END GCODE --",
        "G92 E0.0000",  # Reset extruder position
        "G1 E-4.0000 F6000",  # Retract filament
        "G28",  # Home all axes
        "; -- END OF END GCODE --"
    ]
    gcode.extend(end_gcode)

    # Calculate the estimated printing time in minutes
    travel_speed = 12000  # Rapid move speed (adjust based on your printer's capabilities)
    printing_time_minutes = (total_extrusion_distance / printing_speed) + (total_travel_distance / travel_speed)
    printing_time_output = f"{printing_time_minutes:.2f} minutes"

    # Return the list of G-code lines, and the other outputs
    return gcode, printing_time_output, printing_points, printing_path_len

"""
# Sample inputs (replace with actual values from Grasshopper)
curves = # ... Insert the curves from the optimized path
nozzle_diameter = # ... Insert the nozzle diameter input
printing_speed = # ... Insert the printing speed input
printing_flux = # ... Insert the printing flux input
layer_h = # ... Insert the layer height input
"""

# Generate G-code and other outputs
g_code, printing_time, printing_points, printing_path_len = generate_gcode(printing_path, nozzle_diameter, printing_speed, printing_flux, layer_h)

# Outputs for Grasshopper
g_code_output = g_code
printing_time_output = printing_time
printing_points_output = printing_points
printing_path_len_output = printing_path_len

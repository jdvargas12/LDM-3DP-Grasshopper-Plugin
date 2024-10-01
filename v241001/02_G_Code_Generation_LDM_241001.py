ghenv.Component.Name = "Marvin Gcode - LDM"
ghenv.Component.Message = "280930"

#region COMPONENT DESCRIPTION
""" COMPONENT DESCRIPTION
Gcode Generation LDM

This script generates G-code for LDM (Liquid Deposition Modeling) 3D printers based on a set of 3D curves representing the toolpaths for each layer of a print. The script outputs a G-code file that directs the printer's movements, controls extrusion, and manages layer transitions. It supports both absolute (M82) and relative (M83) extrusion modes and allows for variable flux and printing speed along each curve.

Key Features:
- Supports variable flux modes (constant and linear).
- Allows variable printing speeds (global, per layer, or per curve).
- Adjusted for LDM printers with appropriate start and end G-code.
- Validates printing speeds within the LDM-specific range (1800 to 8000 mm/min).
- Calculates extrusion increments based on the nozzle diameter and material properties.
- **Adjustable decimal precision for floating-point numbers in G-code output.**

Inputs:
    printing_path (List of Curves):
        A list of 3D curves that define the path the 3D printer head will follow for each layer of the print.

    nozzle_diameter (Float):
        The diameter of the 3D printer's nozzle, in millimeters.

    printing_speed (Float or List of Floats):
        Printing speed(s) in mm/min. Can be a single value, a list per layer, or a list per curve.

    m1_flux (Float or List of Floats):
        Flux multiplier(s) for constant flux mode (flux_mode = 1). Can be a single value, a list per layer, or a list per curve.

    layer_h (Float):
        The height of each layer in the print, specified in millimeters.

    e_absolute (Boolean):
        Specifies whether to use absolute (M82) or relative (M83) extrusion mode.

    flux_mode (Integer):
        Specifies the mode of flux variation along the curves.
        - 1: Constant flux mode with enhanced functionality.
        - 2: Linear flux mode.

    m2_flux_start (Float or List of Floats):
        Starting flux multiplier(s) for linear flux variation in flux_mode 2.

    m2_flux_end (Float or List of Floats):
        Ending flux multiplier(s) for linear flux variation in flux_mode 2.

    density_kg_m3 (Float):
        The density of the printing material in kg/m^3.

Outputs:
    gcode (List of Strings):
        The generated G-code commands.

    printing_time (String):
        The estimated time required to complete the print.

    printing_points (List of Points):
        The points generated along the curves in the toolpath.

    printing_path_len (String):
        The total length of the printing path in millimeters.

    layers (Integer):
        The total number of layers in the print.
"""
#endregion

import Rhino.Geometry as rg
from collections import defaultdict
import math

nozzle_div = 2

def flatten(lst):
    """Flatten a nested list into a flat list."""
    flat_list = []
    for item in lst:
        if isinstance(item, (list, tuple)):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list

def generate_gcode(printing_path, nozzle_diameter, printing_speed, m1_flux, layer_h,
                   e_absolute=True, retract=True, flux_mode=1, m2_flux_start=None, m2_flux_end=None,
                   density_kg_m3=None):
    # ----------------------------
    # Variable for decimal precision
    decimal_places = 2  # You can change this value to adjust the number of decimal places
    # ----------------------------

    # Validate and process printing_speed
    if not isinstance(printing_speed, list):
        printing_speed = [printing_speed]
    else:
        printing_speed = flatten(printing_speed)

    # Prepare list of all valid curves
    all_curves = [curve for curve in printing_path if curve.IsValid and curve.GetLength() > 0]
    num_curves = len(all_curves)

    if num_curves == 0:
        print("Error: No valid curves provided in printing_path.")
        return None, None, None, None, None

    # Calculate Z coordinates and number of layers
    min_z = min(min(curve.PointAtStart.Z, curve.PointAtEnd.Z) for curve in all_curves)
    max_z = max(max(curve.PointAtStart.Z, curve.PointAtEnd.Z) for curve in all_curves)
    num_layers = int((max_z - min_z) / layer_h) + 1

    # Determine printing speed mode
    if len(printing_speed) == 1:
        speed_mode_detail = "global"
    elif len(printing_speed) == num_layers:
        speed_mode_detail = "per_layer"
    elif len(printing_speed) == num_curves:
        speed_mode_detail = "per_curve"
    else:
        print("Warning: The number of printing speed values does not match the number of layers or curves.")
        return None, None, None, None, num_layers

    # Ensure all printing speeds are within valid range
    for speed in printing_speed:
        if speed < 1800 or speed > 10000:
            print("Warning: Printing speeds must be between 1800 and 10000 mm/minute. Check your printer manual")
            return None, None, None, None, None

    # Handle flux_mode and flux values
    if flux_mode == 1:
        # Ensure m1_flux is a list
        m1_flux = flatten([m1_flux]) if not isinstance(m1_flux, list) else flatten(m1_flux)
        # Determine flux mode: global, per layer, or per curve
        if len(m1_flux) == 1:
            flux_mode_detail = "global"
        elif len(m1_flux) == num_layers:
            flux_mode_detail = "per_layer"
        elif len(m1_flux) == num_curves:
            flux_mode_detail = "per_curve"
        else:
            print("Warning: The number of flux values does not match the number of layers or curves.")
            return None, None, None, None, num_layers
    elif flux_mode == 2:
        if m2_flux_start is None or m2_flux_end is None:
            print("Error: m2_flux_start and m2_flux_end must be provided when flux_mode is set to 2 (Linear).")
            return None, None, None, None, None

        # Ensure m2_flux_start and m2_flux_end are lists
        if not isinstance(m2_flux_start, list):
            m2_flux_start = [m2_flux_start]
        else:
            m2_flux_start = flatten(m2_flux_start)

        if not isinstance(m2_flux_end, list):
            m2_flux_end = [m2_flux_end]
        else:
            m2_flux_end = flatten(m2_flux_end)

        # If m2_flux_start and m2_flux_end have length 1, repeat them to match num_curves
        if len(m2_flux_start) == 1:
            m2_flux_start = m2_flux_start * num_curves
        if len(m2_flux_end) == 1:
            m2_flux_end = m2_flux_end * num_curves

        # Check that m2_flux_start and m2_flux_end lists have the same length and match number of curves
        if len(m2_flux_start) != len(m2_flux_end) or len(m2_flux_start) != num_curves:
            print("Error: m2_flux_start and m2_flux_end must be lists of the same length as the number of curves.")
            return None, None, None, None, None

    # Set default density if not provided or invalid
    if density_kg_m3 is None or density_kg_m3 <= 0:
        density_kg_m3 = 2000  # Default value in kg/m^3
        density_warning = ";Note: Invalid or missing density value. Using default density of 2000 kg/m^3."
    else:
        density_warning = ""

    # Group curves by layer
    curves_by_layer = defaultdict(list)
    for idx, curve in enumerate(all_curves):
        layer_index = int((curve.PointAtEnd.Z - min_z) / layer_h)
        curves_by_layer[layer_index].append((curve, idx))

    # Initialize variables
    total_extruded_volume = 0.0  # in mm^3
    total_printing_distance = 0.0  # in mm
    previous_point = None
    gcode = []
    printing_points = []

    # Preprocessing for estimation
    for layer_index in sorted(curves_by_layer.keys()):
        # Determine current printing speed
        if speed_mode_detail == "global":
            current_speed = printing_speed[0]
        elif speed_mode_detail == "per_layer":
            current_speed = printing_speed[layer_index]
        # For 'per_curve', we'll handle it inside the curve loop

        if flux_mode == 1:
            if flux_mode_detail == "global":
                current_flux = m1_flux[0]
            elif flux_mode_detail == "per_layer":
                current_flux = m1_flux[layer_index]
            # For 'per_curve', we'll handle it inside the curve loop
        elif flux_mode == 2:
            # Not applicable here
            pass

        for curve, curve_index in curves_by_layer[layer_index]:
            # Determine current printing speed for per_curve mode
            if speed_mode_detail == "per_curve":
                current_speed = printing_speed[curve_index]

            if flux_mode == 1:
                if flux_mode_detail == "per_curve":
                    current_flux = m1_flux[curve_index]
                # For 'global' and 'per_layer', current_flux is already set
                start_flux = current_flux
                end_flux = current_flux
            elif flux_mode == 2:
                start_flux = float(m2_flux_start[curve_index])
                end_flux = float(m2_flux_end[curve_index])

            curve_params = curve.DivideByLength(nozzle_diameter / nozzle_div, True)
            if curve_params is None:
                continue

            points = [curve.PointAt(t) for t in curve_params]
            points.insert(0, curve.PointAtStart)
            points.append(curve.PointAtEnd)

            cumulative_distances = [0.0]
            for i in range(1, len(points)):
                dist = points[i - 1].DistanceTo(points[i])
                cumulative_distances.append(cumulative_distances[-1] + dist)

            total_curve_length = cumulative_distances[-1]
            normalized_distances = [d / total_curve_length if total_curve_length > 0 else 0.0 for d in cumulative_distances]

            for i in range(1, len(points)):
                segment_distance = points[i - 1].DistanceTo(points[i])

                if flux_mode == 2:
                    t_norm = normalized_distances[i]
                    flux = start_flux + t_norm * (end_flux - start_flux)
                else:
                    flux = current_flux

                cross_sectional_area = (nozzle_diameter * 1.1 * flux) * layer_h  # in mm^2
                amount_per_segment = cross_sectional_area * segment_distance  # in mm^3
                total_extruded_volume += amount_per_segment
                total_printing_distance += segment_distance

            if previous_point:
                travel_distance = previous_point.DistanceTo(points[0])
                total_printing_distance += travel_distance

            previous_point = points[-1]

    # Calculate total length and time
    average_speed = sum(printing_speed) / len(printing_speed)
    printing_time_minutes = total_printing_distance / average_speed if total_printing_distance else 0
    printing_time = f"{printing_time_minutes:.{decimal_places}f} minutes"

    # Calculate estimated volume and mass
    volume_m3 = total_extruded_volume / 1e9  # Convert mm^3 to m^3
    volume_liters = volume_m3 * 1000  # Convert m^3 to liters
    mass_kg = volume_m3 * density_kg_m3
    mass_g = mass_kg * 1000  # Convert kg to grams

    # Start G-code with printing information
    e_mode = "M82 ;Absolute" if e_absolute else "M83 ;Relative"
    flux_mode_str = 'Constant' if flux_mode == 1 else 'Linear'
    printing_info = [
        ";PRINTING INFORMATION:",
        f";Nozzle diameter: {nozzle_diameter} [mm]",
        f";Number of layers: {num_layers}",
        f";Layer height: {layer_h} [mm]",
        f";Extrusion mode: {'Absolute' if e_absolute else 'Relative'}",
        f";Flux mode: {flux_mode_str}"
    ]

    # Add printing speed information
    if speed_mode_detail == "global":
        printing_info.append(f";Printing speed (global): {printing_speed[0]} mm/min")
    elif speed_mode_detail == "per_layer":
        min_speed = min(printing_speed)
        max_speed = max(printing_speed)
        printing_info.append(f";Printing speed per layer: From {min_speed} to {max_speed} mm/min")
    elif speed_mode_detail == "per_curve":
        min_speed = min(printing_speed)
        max_speed = max(printing_speed)
        printing_info.append(f";Printing speed per curve: From {min_speed} to {max_speed} mm/min")

    # Add flux information
    if flux_mode == 1:
        if flux_mode_detail == "global":
            printing_info.append(f";Flux multiplier (global): {m1_flux[0]}")
        elif flux_mode_detail == "per_layer":
            min_flux = min(m1_flux)
            max_flux = max(m1_flux)
            printing_info.append(f";Flux multiplier per layer: From {min_flux} to {max_flux}")
        elif flux_mode_detail == "per_curve":
            min_flux = min(m1_flux)
            max_flux = max(m1_flux)
            printing_info.append(f";Flux multiplier per curve: From {min_flux} to {max_flux}")
    elif flux_mode == 2:
        min_flux = min(flatten([m2_flux_start, m2_flux_end]))
        max_flux = max(flatten([m2_flux_start, m2_flux_end]))
        printing_info.append(f";Flux multiplier: From {min_flux} to {max_flux}")

    # Add density, volume, and mass information
    printing_info.append(f";Material density: {density_kg_m3} kg/m^3")
    if density_warning:
        printing_info.append(density_warning)
    printing_info.append(f";Estimated printing volume: {volume_liters:.{decimal_places}f}L")
    printing_info.append(f";Estimated printing mass: {mass_g:.{decimal_places}f}g")

    # Start G-code
    printing_info.extend([
        "; -- START GCODE --",
        "G90",
        e_mode,
        "G28",
    ])

    if e_absolute:
        printing_info.extend([
            "G92 E0.0000",
            "G1 E-4.0000 F6000",
        ])
    else:
        printing_info.append("G1 E-4.0000 F6000")

    first_layer_z = min_z
    printing_info.append(f"G1 Z{(first_layer_z + 2.000):.{decimal_places}f} F12000")
    printing_info.append("; -- END OF START GCODE --")
    gcode.extend(printing_info)

    # G-code generation
    extrusion_amount = 0.0
    previous_point = None

    constant_denominator = ((5.25 / 2) ** 2) * math.pi  # For LDM nozzle diameter

    for layer_index in sorted(curves_by_layer.keys()):
        gcode.append(f"; Start of layer {layer_index + 1}")

        # Determine current printing speed
        if speed_mode_detail == "global":
            current_speed = printing_speed[0]
        elif speed_mode_detail == "per_layer":
            current_speed = printing_speed[layer_index]

        for curve, curve_index in curves_by_layer[layer_index]:
            # Determine current printing speed for per_curve mode
            if speed_mode_detail == "per_curve":
                current_speed = printing_speed[curve_index]

            if flux_mode == 1:
                if flux_mode_detail == "global":
                    current_flux = m1_flux[0]
                elif flux_mode_detail == "per_layer":
                    current_flux = m1_flux[layer_index]
                elif flux_mode_detail == "per_curve":
                    current_flux = m1_flux[curve_index]
                start_flux = current_flux
                end_flux = current_flux
            elif flux_mode == 2:
                start_flux = float(m2_flux_start[curve_index])
                end_flux = float(m2_flux_end[curve_index])

            curve_params = curve.DivideByLength(nozzle_diameter / nozzle_div, True)
            if curve_params is None:
                continue

            points = [curve.PointAt(t) for t in curve_params]
            points.insert(0, curve.PointAtStart)
            points.append(curve.PointAtEnd)

            cumulative_distances = [0.0]
            for i in range(1, len(points)):
                dist = points[i - 1].DistanceTo(points[i])
                cumulative_distances.append(cumulative_distances[-1] + dist)

            total_curve_length = cumulative_distances[-1]
            normalized_distances = [d / total_curve_length if total_curve_length > 0 else 0.0 for d in cumulative_distances]

            for i, pt in enumerate(points):
                if i == 0:
                    gcode_line = f"G0 F{current_speed:.0f} X{pt.X:.{decimal_places}f} Y{pt.Y:.{decimal_places}f} Z{pt.Z:.{decimal_places}f}"
                    gcode.append(gcode_line)
                    printing_points.append(pt)
                else:
                    segment_distance = points[i - 1].DistanceTo(pt)

                    if flux_mode == 2:
                        t_norm = normalized_distances[i]
                        flux = start_flux + t_norm * (end_flux - start_flux)
                    else:
                        flux = current_flux

                    # Calculate extrusion increment
                    extrusion_increment = ((nozzle_diameter * layer_h) / constant_denominator) * flux * segment_distance

                    if e_absolute:
                        extrusion_amount += extrusion_increment
                        e_value = extrusion_amount
                    else:
                        e_value = extrusion_increment

                    gcode_line = f"G1 F{current_speed:.0f} X{pt.X:.{decimal_places}f} Y{pt.Y:.{decimal_places}f} Z{pt.Z:.{decimal_places}f} E{e_value:.{decimal_places}f}"
                    gcode.append(gcode_line)
                    printing_points.append(pt)

            previous_point = points[-1]

        if bool(retract):
            last_point = previous_point
            retract_gcode = f"G1 F{current_speed:.0f} Z{(last_point.Z + layer_h):.{decimal_places}f} ; Retract to avoid pulling"
            gcode.append(retract_gcode)
            previous_point.Z += layer_h

        gcode.append(f"; End of layer {layer_index + 1}")

    # End G-code
    end_gcode = ["; -- END GCODE --"]
    if e_absolute:
        end_gcode.extend([
            "G92 E0.0000",
            "G1 E-4.0000 F6000",
        ])
    else:
        end_gcode.append("G1 E-4.0000 F6000")
    end_gcode.append("G28")
    end_gcode.append("; -- END OF END GCODE --")
    gcode.extend(end_gcode)

    printing_path_len = f"{total_printing_distance:.{decimal_places}f} mm"
    layers = num_layers

    return gcode, printing_time, printing_points, printing_path_len, layers

# Example usage
g_code, printing_time, printing_points, printing_path_len, layers = generate_gcode(
    printing_path, nozzle_diameter, printing_speed, m1_flux, layer_h,
    e_absolute, flux_mode=flux_mode, m2_flux_start=m2_flux_start, m2_flux_end=m2_flux_end,
    density_kg_m3=density_kg_m3
)

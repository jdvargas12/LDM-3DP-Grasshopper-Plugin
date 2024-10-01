ghenv.Component.Name = "PrintingPathOptimizer"
ghenv.Component.Message = "240811"

""" #COPMONENT DESCRIPTION v240811
Curve Path Optimization Component for 3D Printing

This component optimizes the toolpath for 3D printing a set of input curves by sorting them to minimize travel distance. 
It uses the Nearest Neighbor heuristic to ensure that the print head moves efficiently between endpoints 
within the same layer and transitions optimally between different layers. 
The process starts at a user-specified reference point, ensuring the path begins at a 
designated start position.

The optimization happens in two stages:

Layer Organization: Curves are grouped by their Z-height into layers to process each layer separately. This grouping considers a tolerance level to account for minor variations in Z-heights.
Intra-Layer Optimization: Within each layer, curves are sorted to minimize the end-to-start travel for consecutive curves.
Inter-Layer Transitions: After sorting within a layer, the algorithm identifies the shortest move to the next layer's starting curve, considering Z-height transitions.
The output is a sequence of curves ordered to provide an effective and time-efficient 3D printing path.
"""

import Rhino.Geometry as rg
import scriptcontext as sc

def sort_curves_nearest_neighbor(curves, start_point):
    if not curves:
        return []
    
    sorted_curves = []
    unvisited = curves[:]
    
    # Find the curve closest to the start_point
    closest_curve_index = None
    closest_distance = float('inf')
    for i, curve in enumerate(unvisited):
        d_start = start_point.DistanceTo(curve.PointAtStart)
        d_end = start_point.DistanceTo(curve.PointAtEnd)
        if min(d_start, d_end) < closest_distance:
            closest_curve_index = i
            closest_distance = min(d_start, d_end)
            flip = d_start > d_end
    
    # Flip the curve if needed and set it as the first curve
    if flip:
        unvisited[closest_curve_index].Reverse()
    sorted_curves.append(unvisited.pop(closest_curve_index))
    current_point = sorted_curves[-1].PointAtEnd
    
    # Continue with the nearest neighbor algorithm
    while unvisited:
        closest_curve_index = None
        closest_distance = float('inf')
        for i, curve in enumerate(unvisited):
            d_start = current_point.DistanceTo(curve.PointAtStart)
            d_end = current_point.DistanceTo(curve.PointAtEnd)
            if min(d_start, d_end) < closest_distance:
                closest_curve_index = i
                closest_distance = min(d_start, d_end)
                flip = d_start > d_end
        
        # Flip the curve if the end point is closer
        if flip:
            unvisited[closest_curve_index].Reverse()
        
        # Append the closest curve and update the current point
        sorted_curves.append(unvisited.pop(closest_curve_index))
        current_point = sorted_curves[-1].PointAtEnd
    
    return sorted_curves

def group_curves_by_layer(curves, tolerance=0.01):
    layers = {}
    for curve in curves:
        z_value = round((curve.PointAtStart.Z + curve.PointAtEnd.Z) / 2, 2)
        layer_key = round(z_value / tolerance) * tolerance
        if layer_key not in layers:
            layers[layer_key] = []
        layers[layer_key].append(curve)
    return layers

def sort_curves_within_layers(curves_by_layer, start_point):
    sorted_layers = {}
    for z, layer_curves in sorted(curves_by_layer.items()):
        sorted_layers[z] = sort_curves_nearest_neighbor(layer_curves, start_point)
        # Update the start point for the next layer to the end of the last curve
        if sorted_layers[z]:
            start_point = sorted_layers[z][-1].PointAtEnd
    return sorted_layers

def optimize_path_across_layers(sorted_layers):
    optimized_path = []
    for z, layer_curves in sorted_layers.items():
        optimized_path.extend(layer_curves)
    return optimized_path
"""
# Get the curves and start point from the Grasshopper inputs
curves = # ... assume this is filled with the input curves from Grasshopper
start_point = # ... assume this is filled with the input start point from Grasshopper
"""
# Process the optimization
curves_by_layer = group_curves_by_layer(curves)
sorted_curves_within_layers = sort_curves_within_layers(curves_by_layer, start_point)
optimized_path = optimize_path_across_layers(sorted_curves_within_layers)

# The output to Grasshopper
optimized_path

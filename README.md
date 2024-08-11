# LDM-3DP Components - v240811

This repository contains components and scripts for developing a Grasshopper plugin for 3D printing with LDM (Liquid Deposition Modeling) technologies, such as the WASP40100. The plugin facilitates G-code generation, path optimization, and export for large-scale, clay-based, and other viscous material printing processes.

## Files Included in v240811:

1. **00_LDM_3DP_Components_240811.gh**
   - **Type:** Grasshopper Definition
   - **Size:** 1,528 KB
   - **Description:** Preassembled Grasshopper definition that contains all the components required for the LDM 3D printing workflow.

2. **01_Printing_Path_Optimizer_240811.py**
   - **Type:** Python Source File
   - **Size:** 5 KB
   - **Description:** Python script for optimizing the 3D printing path based on the given toolpaths. It rearranges the curves to minimize travel distance between them.

3. **02_G_Code_Generation_240811.py**
   - **Type:** Python Source File
   - **Size:** 9 KB
   - **Description:** Python script that generates G-code from a set of 3D curves. It calculates the number of layers, optimizes extrusion, and adds necessary retraction commands to avoid issues during printing.

4. **03_G_Code_Export_240811.py**
   - **Type:** Python Source File
   - **Size:** 4 KB
   - **Description:** Python script that handles the exporting of the generated G-code to a specified file location with a given file name and extension. It also includes options for file overwrite protection.

## How to Use:

1. **Open the Grasshopper definition**: 
   - Load the `00_LDM_3DP_Components_240811.gh` file in Grasshopper.
   - This definition includes all the components necessary for generating and exporting G-code for LDM 3D printing.

2. **Customize the Workflow**:
   - Use the `01_Printing_Path_Optimizer_240811.py` to optimize the toolpaths before generating the G-code.
   - Generate the G-code with `02_G_Code_Generation_240811.py`.
   - Export the G-code to your desired location using `03_G_Code_Export_240811.py`.

3. **Run the Process**:
   - Adjust input parameters as needed (such as nozzle diameter, printing speed, and printing flux).
   - Execute the Grasshopper definition to generate and save the G-code.

## Requirements:

- **Rhino 6 or 7**
- **Grasshopper**
- **Python (RhinoScriptSyntax)**

## Version History:

- **v240811** - Initial version with basic functionality for path optimization, G-code generation, and export.

---

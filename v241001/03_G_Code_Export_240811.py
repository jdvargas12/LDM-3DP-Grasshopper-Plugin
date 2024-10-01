ghenv.Component.Name = "Save G-Code"
ghenv.Component.Message = "240811"

#region COMPONENT DESCRIPTION 240811
"""
Component Name: Save G-Code
Component Version: 240811

Description:
This component saves a list of G-code strings to a specified file location on your system. 
It provides functionality to name the file, choose a file extension (such as .gcode), 
and decide whether to override an existing file. The component is particularly useful 
for finalizing and exporting G-code after generating it with Grasshopper-based 3D printing workflows.

Inputs:
- g_code: (List of Strings) The G-code lines that you want to save to a file.
- file_path: (String) The directory path where the file will be saved.
- file_name: (String) The desired name of the file, without the extension.
- file_extension: (String) The desired file extension, such as .gcode.
- run: (Boolean) Triggers the file-saving operation. When set to True, the file is saved.
- override: (Boolean) Determines whether an existing file with the same name should be overwritten. 
  If False and the file exists, a warning is displayed and the file is not saved.

Outputs:
- out: (None) This component does not produce an output, but it will display a message confirming the save 
  or showing an error if something goes wrong.

Usage:
1. Connect the G-code list to the g_code input.
2. Specify the directory path and file name using the file_path and file_name inputs.
3. Choose a file extension (e.g., .gcode).
4. Set run to True to save the file.
5. If you want to overwrite an existing file, set override to True.

Error Handling:
- If the file already exists and override is set to False, a message box will appear warning that the file was not saved.
- Any exceptions during the file-writing process will be printed in the console.
"""
#endregion

import os
import rhinoscriptsyntax as rs

# Inputs
g_code = g_code  # List of strings (G-code)
file_path = file_path  # Full directory path
file_name = file_name  # Desired file name without extension
file_extension = file_extension  # Desired file extension (e.g., ".gcode")
run = run  # Boolean to trigger saving
override = override  # Boolean to allow file override

# Initialize output
out = None

if run:
    # Construct the full file path
    full_file_path = os.path.join(file_path, file_name + file_extension)
    
    # Check if the file exists and if override is allowed
    if not os.path.exists(full_file_path) or override:
        try:
            # Write the G-code to the file
            with open(full_file_path, 'w') as file:
                for line in g_code:
                    file.write(line + '\n')
            print(f"File {file_name} saved successfully at {full_file_path}")
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        # Show a message box warning about the file already existing and override set to False
        rs.MessageBox(f"The file '{file_name}' already exists in the directory '{file_path}'. Please set override to True or change the file's name. No file was saved.", 0, "File Save Warning")

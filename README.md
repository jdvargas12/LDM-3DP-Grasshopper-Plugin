# LDM 3DP

# LDM-3DP Plugin for Grasshopper

This repository contains components and scripts for developing a Grasshopper plugin aimed at 3D printing 
with LDM (Liquid Deposition Modeling) cartesian technologies, such as the WASP40100. The plugin is designed 
to facilitate the creation of G-code for complex 3D printing paths, optimizing the workflow for large-scale, 
clay-based, and other viscous material printing processes.

## Repository Contents

### Components and Scripts

- **G_Code_Generation**
  - **Version 240720:** 
    - Basic G-code generation for 3D printing paths.
  - **Version 240811:** 
    - Enhanced G-code generation with added functionalities such as layer-specific flux control 
      and improved path optimization.

- **Printing_Path_Optimizer**
  - **Version 240811:** 
    - Tools for optimizing 3D printing paths for efficiency, including retraction management and extrusion control.

- **W_AM_Components**
  - **Version 240811:** 
    - A preassembled Grasshopper definition file (.gh) containing all components and logic required for a complete 
      3D printing workflow using LDM technologies.

### Technologies Supported

- **WASP40100**: 
  - The components and preassembled algorithm are specifically tailored for use with the WASP40100 3D printer, 
    a cartesian LDM printer known for its capability to handle large-scale, clay-based printing.

### How to Use

1. **Download or Clone the Repository**:
    - Clone the repository using `git clone` or download the zip file from GitHub.

2. **Install Components in Grasshopper**:
    - Place the Python scripts in your Grasshopper components folder.
    - Open the Grasshopper definition file (`W_AM_Components_240811.gh`) in Rhino and start experimenting 
      with the 3D printing components.

3. **Customize for Your Printer**:
    - The scripts and components are customizable for different LDM printers by adjusting parameters such as 
      nozzle diameter, printing speed, and layer height.

### Future Development

- **Plugin Packaging**:
  - The current components will be packaged into a user-friendly Grasshopper plugin for easy distribution 
    and installation.
  
- **Additional Features**:
  - Future versions will include more advanced path optimization, real-time printing feedback, and support 
    for multi-material printing.

### Contribution

- We welcome contributions to this project. If you have suggestions, find a bug, or want to contribute new features, 
  please submit a pull request or open an issue.

### License

- This project is licensed under the MIT License. See the LICENSE file for details.

### Contact

- For questions or support, contact [Your Name or Organization] at [Your Email].

 

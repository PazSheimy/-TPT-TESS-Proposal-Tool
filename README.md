# Project Title: TPT-TESS-Proposal-Tool
TESS proposal tool (TPT) will be a web app that helps users propose for time to deeply look at targets and helps users visualize what is observed and when. the system goal is to make the satellite data accessible for users through features like:
 Sky map: where users can locate and examine targets of importance.
 
 Target Date: where users can search for target by Ra/Dec, Object name, or TIC id to query information like 
 The sector of observation, cycle, camera, and observation date.
 
 Diagram page: where users can upload a list of targets to analyze them in HR diagrams, Magnitude histograms.
 Distance Histogram, and sector graph that can be highlighted to download only the desired data.

# Getting Started 
Follow these instructions to clone the project and set up the environment on your local machine.

# Prerequisites
Before you start, make sure you have the following software installed on your computer:

Python (version 3.6 or later)
pip (Python Package Installer)

# Installation
1- Clone the repository to your local machine:
git clone https://github.com/your_username/satellite-target-visualization.git
cd satellite-target-visualization

2- Create a virtual environment and activate it:
python -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate  # For Windows

3- Install the required dependencies:
pip install -r requirements.txt

4- Run the web application locally:
python main.py

5- Open your web browser and navigate to http://127.0.0.1:5000 to view the application.

# Usage
1- Navigate to the "Sky Map" page to visualize satellite targets on a sky map.

2- You can either search for a specific target by entering its coordinates(ra/dec, tic id or target name), or upload a CSV file containing a list of targets.

3- Navigate to the "Target List" page to view and analyze the targets using HR diagrams, Distance Histogram, Magnitud Histogram, etc.

3- You can download the graph data for further analysis.

# Contributing
Feel free to submit issues, feature requests, and pull requests.

# License

# Acknowledgments



# Images: 
Basic layout
![tess_basic_layout](https://user-images.githubusercontent.com/51823622/212510485-9d1bb208-7b4e-4552-b048-af1479adb2bf.png)

![tess_basic_layout](https://github.com/PazSheimy/-TPT-TESS-Proposal-Tool/blob/main/TPTborn(1152).png)





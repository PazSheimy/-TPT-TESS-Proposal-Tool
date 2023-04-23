# Project Title: TPT-TESS-Proposal-Tool
TESS proposal tool (TPT) is a web app that helps users propose for time to deeply look at targets and helps users visualize what is observed and when. the system goal is to make the satellite data accessible for users through features like:

 Sky map: where users can locate and examine targets of importance.
 
 Target Data: where users can search for target by Ra/Dec, Object name, or TIC id to query information like 
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
1- Clone the repository to your local machine [Here](https://github.com/PazSheimy/-TPT-TESS-Proposal-Tool.git)


2- Create a virtual environment and activate it: (optional)

  - python -m venv venv

  - source venv/bin/activate  # For Linux/Mac

  - venv\Scripts\activate  # For Windows

3- Install the required dependencies:

pip install -r requirements.txt

4- Inside of utils there is a file named visualization.py that has a function 
def sector_graph. this function creates a graph based on the sectors that have been observed 
and allows the user to highlight the desire sector information to download it. User will have to change the 
path for this feature to work when app is being runned locally 

code:
#Create a button for downloading the selected data
    download_button = Button(label="Download", button_type="success")
    download_button.js_on_click(CustomJS(args=dict(source=source),
                            code=open("c:\\Users\\sheim\\Desktop\\tptwebapp\\utils\\download.js").read()))
                        
this is how it works for my, you should be able to make it work by changing it to your personal path.



5- Run the web application locally:

python main.py


6- Open your web browser and navigate to http://127.0.0.1:5000 to view the application.


# Usage
1- Navigate to the "Sky Map" page to visualize satellite targets on a sky map.

2- You can either search for a specific target by entering its coordinates(ra/dec, tic id or target name), or upload a CSV file containing a list of targets.

3- Navigate to the "Target List" page to view and analyze the targets using HR diagrams, Distance Histogram, Magnitud Histogram, etc.

3- You can download the graph data for further analysis.

4- csv files example to download:

[Tic_id](https://github.com/PazSheimy/-TPT-TESS-Proposal-Tool/blob/main/csv%20files%20to%20test/TIC3inputs.csv)

[Target_Name](https://github.com/PazSheimy/-TPT-TESS-Proposal-Tool/blob/main/csv%20files%20to%20test/5targnamesneartoeachother.csv)

[Ra, Dec](https://github.com/PazSheimy/-TPT-TESS-Proposal-Tool/blob/main/csv%20files%20to%20test/fiveradecdata.csv)


# Contributing
Feel free to submit issues, feature requests, and pull requests.

# License

# Acknowledgments



# Images: 

![tess_basic_layout](https://github.com/PazSheimy/-TPT-TESS-Proposal-Tool/blob/main/Images%20File/homescreen.png)

![tess_basic_layout](https://github.com/PazSheimy/-TPT-TESS-Proposal-Tool/blob/main/Images%20File/frontendskyandquerytable.png)

![tess_basic_layout](https://github.com/PazSheimy/-TPT-TESS-Proposal-Tool/blob/main/Images%20File/frontend3screengraphs.png)




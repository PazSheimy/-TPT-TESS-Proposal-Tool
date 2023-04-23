"""
This module contains functions for rendering the main page and generating an HR Diagram, Sector Graph, Distance Histogram.
Magnitud Histogram

Dependencies:
- flask
- bokeh
- numpy
- astropy
"""

from bokeh.plotting import figure
from bokeh.resources import Resources
from bokeh.embed import file_html
from flask import render_template, request
import numpy as np
from bokeh.models import ColumnDataSource, BoxSelectTool, Button, CustomJS, LogAxis
from bokeh.layouts import column
from astropy import units as u
from bokeh.models import Range1d
import math
from bokeh.palettes import RdYlBu11
from bokeh.transform import linear_cmap
from bokeh.models.tickers import FixedTicker


def index():

    """
    Render the main index page with a hidden table container.

    Returns:
        A rendered HTML template for the index page.
    """
    # sets <table> container visibility to 'hidden' upon page load
    table_visibility = 'hidden'

    return render_template("index.html", table_visibility=table_visibility)


def hr_diagram(luminosity, temperature, star_name):
    """
    Generate an HR Diagram for the given star data.

    Args:
        luminosity (list): A list of luminosity values for the star.
        temperature (list): A list of temperature values for the star.
        star_name (str): The name of the star.

    Returns:
        An HTML string containing the generated HR Diagram.
    """


    print("Temperature:", temperature)
    print("Luminosity:", luminosity)


    # Filter out invalid temperature values
    filtered_data = [(t.value, l.value) for t, l in zip(temperature, luminosity) if not (math.isnan(t.value) or math.isnan(l.value))]
    filtered_temperature, filtered_luminosity = zip(*filtered_data)

    # Extract the float values from the Quantity objects
    float_filtered_temperature = [t for t in filtered_temperature]
    float_filtered_luminosity = [l for l in filtered_luminosity]

    # Create a ColumnDataSource with the filtered data
    source = ColumnDataSource(data=dict(
        temperature=filtered_temperature,
        luminosity=filtered_luminosity,
        float_luminosity=float_filtered_luminosity
    ))

    #Create a custom color palette
    custom_palette = RdYlBu11[::-1][1:]  # To remove the darkest red


    # Create a figure with the title HR Diagram for [star_name]
    p = figure(title=f"HR Diagram for {star_name}", x_axis_type="log", y_axis_type="log")

    # Define a color mapper based on the luminosity values
    color_mapper = linear_cmap(field_name='temperature', palette=custom_palette, low=min(filtered_temperature), high=max(filtered_temperature))


    # Add a scatter plot of temperature vs. luminosity to the figure with color mapping
    p.circle(x='temperature', y='luminosity', color=color_mapper, source=source)

    # Label the x-axis as Temperature (K)
    p.xaxis.axis_label = "Temperature (K)"

    # Label the y-axis as Luminosity (solLum)
    p.yaxis.axis_label = "Luminosity (solLum)"

    # Set the y_range to be flipped
    p.y_range.flipped = False

    # Reverse the x-axis to get values from max to min
    p.x_range = Range1d(start=max(float_filtered_temperature), end=min(float_filtered_temperature))

    # Set the sizing mode of the component
    p.sizing_mode = "scale_both"

    # Set the mode of resources to cdn for faster loading
    resources = Resources(mode='cdn')

    # Create HTML file from figure with the specified title
    html1 = file_html(p, resources=resources, title=f"HR Diagram for {star_name}")
    
    # Create HTML file from figure with the specified title
    return html1
  
def generate_magnitude_histogram(star_name, magnitudes):
    """
    Generate a histogram of TESS magnitudes for a given star.

    Args:
        star_name (str): The name of the star.
        magnitudes (list): A list of TESS magnitudes for the star.

    Returns:
        An HTML string containing the generated magnitude histogram, or None if the magnitudes list is empty.
    """
    
    # Return None if the input magnitudes list is empty
    if not magnitudes:  
        return None
    
    # Compute the histogram data using numpy
    hist, edges = np.histogram(magnitudes, bins="auto")

    # Define the data source for the histogram
    source = ColumnDataSource(data=dict(
        top=hist,
        bottom=np.zeros_like(hist),
        left=edges[:-1],
        right=edges[1:],
    ))

    # Create a Bokeh figure object and add the histogram to it
    p = figure(title=f"{star_name} Magnitude Histogram",
               x_axis_label='Magnitude', y_axis_label='Frequency',
               x_range=(0, max(edges)), y_range=(0, max(hist)))
    p.quad(top='top', bottom='bottom', left='left',
           right='right', source=source, line_color='black')
    

    # Set the x-axis label
    p.xaxis.axis_label = "TESS Magnitude"

    # Set the y-axis label
    p.yaxis.axis_label = "Frequency"

    # Set the sizing mode of the component to scale with window size
    p.sizing_mode = "scale_both"

    # Generate the HTML for the magnitude histogram
    resources = Resources(mode='cdn')
    html2 = file_html(p, resources=resources,
                      title=f"Magnitude Histogram for {star_name}")

    return html2


def distance_histogram(star_name, distance):
    """
    Generate a histogram of distances for a given star.

    Args:
        star_name (str): The name of the star.
        distance (list): A list of distances for the star in parsecs.

    Returns:
        An HTML string containing the generated distance histogram.
    """

    # Create a histogram of the distances using numpy
    hist, edges = np.histogram(distance, bins=50)

    # Define the data source for the histogram
    source = ColumnDataSource(data=dict(
        top=hist,
        bottom=np.zeros_like(hist),
        left=edges[:-1],
        right=edges[1:],
    ))

    # Create a Bokeh figure object and add the histogram to it
    p = figure(title="Distance Histogram",
               x_axis_label='Distance (parsecs)', y_axis_label='Frequency',
               x_range=(min(edges), max(edges)), y_range=(0, max(hist)),
               x_axis_type="log")  # Use a log scale for the x-axis
    p.quad(top='top', bottom='bottom', left='left',
           right='right', source=source, line_color="#033649")

    # Set the sizing mode of the component to scale with window size
    p.sizing_mode = "scale_both"

    # Generate the HTML for the distance histogram
    resources = Resources(mode='cdn')
    html3 = file_html(p, resources=resources,
                      title=f"Distance Histogram for {star_name}")
    return html3



def sector_graph(object_name, results, cycle):
    """
    Generate a bar graph of observed sectors for a given object.

    Args:
        object_name (str): The name of the object.
        results (list): A list of lists, where each inner list contains
                        sector, cycle, camera, and observation date information.
        cycle (int): The cycle number.

    Returns:
        An HTML string containing the generated sector graph.
    """

    # Extract the sector, cycle, camera, and observation date information from the results list
    sectors = []
    cycles = []
    cameras = []
    observation_dates = []

    for array in results:
        sector = array[2]
        observed_cycle = array[4]
        camera = array[3]
        observation_date = array[5]
        sectors.append(sector)
        cycles.append(observed_cycle)
        cameras.append(camera)
        observation_dates.append(observation_date)

    # Create a ColumnDataSource with the extracted data
    source = ColumnDataSource(data=dict(sectors=sectors, cycles=cycles, cameras=cameras, observation_dates=observation_dates))

    # Create a Bokeh figure object with appropriate labels
    p = figure(title='Observed Sectors',
           x_axis_label='Sector', y_axis_label='Cycle')

    # Add vertical bars to the figure
    p.vbar(x='sectors', top='cycles', source=source,
           width=0.9, line_color="#033649")
    
    # Set the start values for the x and y ranges
    p.x_range.start = 0
    p.y_range.start = 0

    # Set the y-axis to use whole numbers
    max_cycle = max(cycles) + 1
    p.yaxis.ticker = FixedTicker(ticks=list(range(max_cycle)))

    # Add the BoxSelectTool to the plot
    p.add_tools(BoxSelectTool())

    # Create a button for downloading the selected data
    download_button = Button(label="Download", button_type="success")
    download_button.js_on_click(CustomJS(args=dict(source=source),
                            code=open("c:\\Users\\sheim\\Desktop\\tptwebapp\\static\\download.js").read()))


    # Add the button to a layout and then add the layout to the plot
    layout = column(p, download_button, sizing_mode="fixed", width=400, height=350)
 
    # Generate the HTML for the sector graph
    resources = Resources(mode='cdn')
    html4 = file_html(layout, resources=resources,
                      title=f"Sectors Observed for {object_name}")
    return html4

from bokeh.plotting import figure
from bokeh.resources import Resources
from bokeh.embed import file_html
from flask import render_template, request
import numpy as np
from bokeh.models import ColumnDataSource, BoxSelectTool, Button, CustomJS
from bokeh.layouts import column
from astropy import units as u



def index():
    # sets <table> container visibility to 'hidden' upon page load
    table_visibility = 'hidden'

    return render_template("index.html", table_visibility=table_visibility)


def hr_diagram(luminosity, temperature, star_name, sector_number):
    # Create a figure with the title HR Diagram for [star_name] (Sector [sector_number])
    p = figure(title=f"HR Diagram for {star_name} (Sector {sector_number})")
    # Add a scatter plot of temperature vs. luminosity to the figure
    p.circle(temperature, luminosity.to(u.W))
    # Label the x-axis as Temperature (K)
    p.xaxis.axis_label = "Temperature (K)"
    # Label the y-axis as Lumin
    p.yaxis.axis_label = "Luminosity (solLum)"

    # how the component should size itself
    p.sizing_mode = "scale_both"

    # Set mode of resources to cdn for faster loading
    resources = Resources(mode='cdn')
    # Create HTML file from figure with specified title
    html1 = file_html(p, resources=resources,
                      title=f"HR Diagram for {star_name} (Sector {sector_number})")

    return html1


def generate_magnitude_histogram(star_name, magnitudes, sector_number):
    min_value = np.min(magnitudes)
    max_value = np.max(magnitudes)
    hist, edges = np.histogram(magnitudes, bins=200)

    # Define the data source for the histogram
    source = ColumnDataSource(data=dict(
        top=hist,
        bottom=np.zeros_like(hist),
        left=edges[:-1],
        right=edges[1:],
    ))

    # Create a Bokeh figure object and add the histogram to it
    p = figure(title=f"{star_name} Magnitude Histogram",
               x_axis_label='Magnitude', y_axis_label='Frequency')
    p.quad(top='top', bottom='bottom', left='left',
           right='right', source=source)

    p.xaxis.axis_label = "TESS Magnitude"
    p.yaxis.axis_label = "Density"

    # how the component should size itself
    p.sizing_mode = "scale_both"

    # Generate the HTML for the magnitude histogram
    resources = Resources(mode='cdn')
    html2 = file_html(p, resources=resources,
                      title=f"Magnitude Histogram for {star_name} (Sector {sector_number})")

    return html2


def distance_histogram(star_name, sector_num, distance):
    # Generate some sample data
    distances = distance

    # Create a histogram of the distances
    hist, edges = np.histogram(distances, bins=50)

    # Define the data source for the histogram
    source = ColumnDataSource(data=dict(
        top=hist,
        bottom=np.zeros_like(hist),
        left=edges[:-1],
        right=edges[1:],
    ))

    # Create a Bokeh figure object and add the histogram to it
    p = figure(title="Distance Histogram",
               x_axis_label='Distance (parsecs)', y_axis_label='Frequency')
    p.quad(top='top', bottom='bottom', left='left',
           right='right', source=source, line_color="#033649")

    # how the component should size itself
    p.sizing_mode = "scale_both"

    # shows the histogram of distances with the x-axis showing the distance in parsecs and
    # the y-axis showing the frequency of each distance.
    resources = Resources(mode='cdn')
    html3 = file_html(p, resources=resources,
                      title=f"Magnitude Histogram for {star_name} (Sector {sector_num})")
    return html3


def sector_graph(object_name, results, cycle):
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

    source = ColumnDataSource(data=dict(sectors=sectors, cycles=cycles, cameras=cameras, observation_dates=observation_dates))

    p = figure(title='Observed Sectors',
           x_axis_label='Sector', y_axis_label='Cycle')

    p.vbar(x='sectors', top='cycles', source=source,
           width=0.9, line_color="#033649")

    p.x_range.start = 0
    p.y_range.start = 0


    # Add the BoxSelectTool to the plot
    p.add_tools(BoxSelectTool())

    # Create a button for downloading the selected data
    download_button = Button(label="Download", button_type="success")
    download_button.js_on_click(CustomJS(args=dict(source=source),
                            code=open("c:\\Users\\sheim\\Desktop\\tptwebapp\\utils\\download.js").read()))


    # Add the button to a layout and then add the layout to the plot
    layout = column(p, download_button, sizing_mode="fixed", width=400, height=450)

    resources = Resources(mode='cdn')
    html4 = file_html(layout, resources=resources,
                      title=f"Sectors Observed for {object_name}")
    return html4

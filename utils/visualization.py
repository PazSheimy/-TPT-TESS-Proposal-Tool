from bokeh.plotting import figure
from bokeh.resources import Resources
from bokeh.embed import file_html
from flask import render_template
import numpy as np
from bokeh.models import ColumnDataSource
from astropy import units as u


def index():
    # sets <table> container visibility to 'hidden' upon page load
    table_visibility = 'hidden'

    return render_template("index.html", table_visibility=table_visibility)


def generate_sector_graphs(object_name, results):
    sector_graphs = []
    for result in results:
        sector_graphs.append(sector_graph(object_name, [result], result[1]))
    return sector_graphs



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

    for array in results:
        sector = array[0]
        cycle = array[1]
        sectors.append(sector)
        cycles.append(cycle)

    # Create a ColumnDataSource object with the sector and cycle data
    source = ColumnDataSource(data=dict(sectors=sectors, cycles=cycles))

    # Create a new plot with a title and axis labels
    p = figure(title='Observed Sectors',
               x_axis_label='Sector', y_axis_label='Cycle')

    # Add a scatter plot with the sector and cycle data
    p.vbar(x='sectors', top='cycles', source=source,
           width=0.9, line_color="#033649")

    # Set the chart range for the x-axis and y-axis
    p.x_range.start = 0
    p.y_range.start = 0

    # # how the component should size itself
    p.sizing_mode = "scale_both"

    # shows the histogram of distances with the x-axis showing the distance in parsecs and
    # the y-axis showing the frequency of each distance.
    resources = Resources(mode='cdn')
    html4 = file_html(p, resources=resources,
                      title=f"Sectors Observed for {object_name}")
    return html4


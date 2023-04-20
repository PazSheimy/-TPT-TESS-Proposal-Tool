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


def index():
    # sets <table> container visibility to 'hidden' upon page load
    table_visibility = 'hidden'

    return render_template("index.html", table_visibility=table_visibility)

# def default_hr_diagram():
#     example_stars = [
#         {"name": "Sun", "luminosity": 1.0, "temperature": 5778},
#         {"name": "Betelgeuse", "luminosity": 120000, "temperature": 3590},
#         {"name": "Sirius B", "luminosity": 0.0026, "temperature": 25100},
#         # Add more stars if needed
#     ]

#     luminosities = [star["luminosity"] for star in example_stars]
#     temperatures = [star["temperature"] for star in example_stars]
#     print(luminosities,temperatures)

#     return luminosities, temperatures

# def hr_diagram(luminosities, temperatures, title, additional_luminosities=None, additional_temperatures=None):
#     luminosities = [math.log10(lum) for lum in luminosities]
#     temperatures = [math.log10(temp) for temp in temperatures]

#     # Add the additional points if provided
#     if additional_luminosities and additional_temperatures:
#         additional_luminosities = [math.log10(lum.value) for lum in additional_luminosities]
#         additional_temperatures = [math.log10(temp.value) for temp in additional_temperatures]
#         luminosities.extend(additional_luminosities)
#         temperatures.extend(additional_temperatures)

#     # Filter out invalid temperature values
#     filtered_data = [(t, l) for t, l in zip(temperatures, luminosities) if not (math.isnan(t) or math.isnan(l))]
#     filtered_temperature, filtered_luminosity = zip(*filtered_data)

#     # Extract the float values from the Quantity objects
#     float_filtered_temperature = [t for t in filtered_temperature]
#     float_filtered_luminosity = [l for l in filtered_luminosity]

#     # Create a ColumnDataSource with the filtered data
#     source = ColumnDataSource(data=dict(
#         temperature=filtered_temperature,
#         luminosity=filtered_luminosity,
#         float_luminosity=float_filtered_luminosity
#     ))

#     # Create a figure with the title HR Diagram for [star_name]
#     p = figure(title=f"HR Diagram for {title}", x_axis_type="log", y_axis_type="log")

#     # Create a custom color palette
#     custom_palette = RdYlBu11[::-1][1:]  # Remove the darkest red

#     # Use the custom palette in the linear_cmap function
#     color_mapper = linear_cmap(field_name='temperature', palette=custom_palette, low=min(filtered_temperature), high=max(filtered_temperature))

#     # Add a scatter plot of temperature vs. luminosity to the figure with color mapping
#     p.circle(x='temperature', y='luminosity', color=color_mapper, source=source)

#     # Label the x-axis as Temperature (K)
#     p.xaxis.axis_label = "Temperature (K)"

#     # Label the y-axis as Luminosity (L_sun)
#     p.yaxis.axis_label = "Luminosity (L_sun)"

#     # Set the y_range to be flipped
#     p.y_range.flipped = False

#     # Reverse the x-axis
#     p.x_range = Range1d(start=max(float_filtered_temperature), end=min(float_filtered_temperature))

#     # Set the sizing mode of the component
#     p.sizing_mode = "scale_both"

#     # Set the mode of resources to cdn for faster loading
#     resources = Resources(mode='cdn')

#     # Create HTML file from figure with the specified title
#     html1 = file_html(p, resources=resources, title=f"HR Diagram for {title}")

#     return html1


def hr_diagram(luminosity, temperature, star_name):
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
    custom_palette = RdYlBu11[::-1][1:]  # Remove the darkest red


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

    # Reverse the x-axis
    p.x_range = Range1d(start=max(float_filtered_temperature), end=min(float_filtered_temperature))

    # Set the sizing mode of the component
    p.sizing_mode = "scale_both"

    # Set the mode of resources to cdn for faster loading
    resources = Resources(mode='cdn')

    # Create HTML file from figure with the specified title
    html1 = file_html(p, resources=resources, title=f"HR Diagram for {star_name}")

    return html1
  
def generate_magnitude_histogram(star_name, magnitudes):

    if not magnitudes:  # Add this check to ensure the input array is not empty
        return None
    
    
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
                      title=f"Magnitude Histogram for {star_name}")

    return html2


def distance_histogram(star_name, distance):
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
                      title=f"Magnitude Histogram for {star_name}")
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

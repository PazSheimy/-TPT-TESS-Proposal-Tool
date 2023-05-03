console.log("Starting download.js");

try {
    // Get the selected data from the source
    var selected_indices = source.selected.indices;
    var selected_data = source.data;

    // Create a list to store the CSV data
    var csv_data = [];

    // Loop through the selected indices and extract the corresponding data
    for (var i = 0; i < selected_indices.length; i++) {
        var index = selected_indices[i];
        var row_data = [
            selected_data['temperature'][index],
            selected_data['luminosity'][index],
            selected_data['magnitudes'][index],
            selected_data['distance'][index],
            selected_data['sectors'][index],
            selected_data['cycles'][index],
            selected_data['cameras'][index],
            selected_data['observation_dates'][index],
        ];
        csv_data.push(row_data.join(','));
    }

    // Create a CSV file from the extracted data
    var csv_string = "temperature,luminosity,magnitudes,distance,sectors,cycles,cameras,observation_dates\n" + csv_data.join('\n');
    var blob = new Blob([csv_string], { type: 'text/csv;charset=utf-8;' });

    // Create a download link and trigger the download
    var link = document.createElement('a');
    var url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'selected_data.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
} catch (error) {
    console.error("Error in download.js:", error);
}


/**
 * Convert a table to CSV format.
 * 
 * This function takes a source object as an argument, which is expected to have
 * data in a tabular format. It converts the data into a CSV (Comma Separated Values)
 * formatted string and returns it.
 * 
 * @param {Object} source - The source object containing table data.
 * @returns {string} - The CSV-formatted string.
 */

function table_to_csv(source) {
    const columns = Object.keys(source.data);
    const nrows = source.get_length();
    const lines = [columns.join(',')];

    if (source.selected.indices.length == 0) {
        console.log("No rows selected, using all row indices");
        const firstKey = Object.keys(source.data)[0];
        source.selected.indices = [...Array(source.data[firstKey].length).keys()];
        console.log("hi",source.selected.indices); // Added this line to print the generated indices array
    }
    
}


function download(source) {
    const filename = 'data_result.csv';
    const filetext = table_to_csv(source);
    const blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });
  
    // Create a temporary link element
    let link = document.createElement('a');
    const url = URL.createObjectURL(blob);
  
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
  
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

console.log("hi1")
button.on_click(function () {
    console.log("hi2")
    // If no rows are selected, use all row indices.
    if (source.selected.indices.length == 0) {
        console.log("No rows selected, using all row indices");
        const firstKey = Object.keys(source.data)[0];
        source.selected.indices = [...Array(source.data[firstKey].length).keys()];
        console.log("hi",source.selected.indices); // Added this line to print the generated indices array
    }
    download(source);
});
  
  
button.on_click(function () {
    if (source.selected.indices.length == 0) {
        source.selected.indices = [...Array(source.data['x'].length).keys()];
    }
    download(source);
});
  
  // Define the desired name of the downloaded CSV file.
  const filename = 'data.csv';

  // Call the table_to_csv function, passing in the source object,
  // and store the resulting CSV string in filetext.
  const filetext = table_to_csv(source);

  // Call the download function with the specified filename and filetext arguments,
  // triggering a download of the CSV file with the provided content.
  download(filename, filetext);
  
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
    const columns = Object.keys(source.data); //Extracts the column names from the source.data object.
    const nrows = source.get_length();//Gets the number of rows in the table
    const lines = [columns.join(',')];//Creates an array with the column names joined by commas as its first element
  
    // Gets the selected row indices from the source object.
    const selected_indices = source.selected.indices;

    // Loop through the selected indices
    /*The outer for loop iterates through the selected row indices, 
    and the inner for loop iterates through the columns. 
    For each cell, it gets the value, converts it to a string, 
    and adds it to a temporary row array. 
    After processing all columns for a row, 
    the row array is joined with commas and added to the lines array. */
    for (let idx of selected_indices) {
        let row = [];
        for (let j = 0; j < columns.length; j++) {
            const column = columns[j];
            row.push(source.data[column][idx].toString());
        }
        lines.push(row.join(','));
    }
    return lines.join('\n').concat('\n');
}

/**
 * Trigger a download with the specified filename and content.
 * 
 * This function takes a filename and text as arguments and triggers a download
 * with the specified filename and content.
 * 
 * @param {string} filename - The desired name of the downloaded file.
 * @param {string} text - The content to be included in the downloaded file.
 */
  function download(filename, text) {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }

  // Define the desired name of the downloaded CSV file.
  const filename = 'data.csv';

  // Call the table_to_csv function, passing in the source object,
  // and store the resulting CSV string in filetext.
  const filetext = table_to_csv(source);

  // Call the download function with the specified filename and filetext arguments,
  // triggering a download of the CSV file with the provided content.
  download(filename, filetext);
  
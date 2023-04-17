function table_to_csv(source) {
    const columns = Object.keys(source.data);
    const nrows = source.get_length();
    const lines = [columns.join(',')];
  
    // Get the selected indices
    const selected_indices = source.selected.indices;

    // Loop through the selected indices
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
  
  function download(filename, text) {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }
  
  const filename = 'data.csv';
  const filetext = table_to_csv(source);
  download(filename, filetext);
  
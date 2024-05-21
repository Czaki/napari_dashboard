(() => {
  var download_table = document.getElementById('download_table');
  fetch("https://pypistats.org//api/packages/napari/recent").then(response => response.json()).then(data => {
    console.log('data:', data)
    data = data.data;
    data.forEach(function (item) {
      var row = download_table.insertRow(-1);
      var cell1 = row.insertCell(0);
      var cell2 = row.insertCell(1);
      cell1.innerHTML = item.date;
      cell2.innerHTML = item.downloads;
    });
  })

})();
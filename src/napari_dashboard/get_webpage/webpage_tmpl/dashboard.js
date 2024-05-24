/* globals Chart:false */

(() => {
  'use strict'

  // Graphs
  const ctx = document.getElementById('starsChart')
  // fetch data from stars.json file
  const data = {{ stars }};
  const labels = data.map((item) => item.day);
  const values = data.map((item) => item.stars);

  // eslint-disable-next-line no-unused-vars
  const myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff'
      }]
    },
    options: {
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          boxPadding: 3
        }
      }
    }
  })
})();

(() => {
  'use strict'

  // Graphs
  const ctx = document.getElementById('downloadChart')
  // fetch data from stars.json file
  const labels = {{ napari_downloads_per_day_dates }};
  const values = {{ napari_downloads_per_day_values }};

  // eslint-disable-next-line no-unused-vars
  const myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff'
      }]
    },
    options: {
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          boxPadding: 3
        }
      }
    }
  })
})()

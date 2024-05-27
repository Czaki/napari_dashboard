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
        pointBackgroundColor: '#007bff',
        pointStyle: false
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
        pointBackgroundColor: '#007bff',
        label: "all version downloads"
      }]
    },
    options: {
      plugins: {
        legend: {
          display: true
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
  const ctx = document.getElementById('issue_stats_chart')
  // fetch data from stars.json file
  const labels = {{ stats.pr_issue_time_stats.days }};
  const issues_open = {{ stats.pr_issue_time_stats.issues_open_cumulative }};
  const issues_closed = {{ stats.pr_issue_time_stats.issues_closed_cumulative }};

  // eslint-disable-next-line no-unused-vars
  const myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: issues_open,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff',
        label: "issues open",
        pointStyle: false
      },
      {
        data: issues_closed,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#ff0000',
        borderWidth: 4,
        pointBackgroundColor: '#ff0000',
        label: "issues closed",
        pointStyle: false
      }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true
        },
        tooltip: {
          boxPadding: 3
        },
        zoom: {
            pan: {
                enabled: true,
                mode: 'xy',
                speed: 10,
                threshold: 10,
                modifierKey: 'ctrl',
            },
            zoom: {
                wheel: {enabled: false,},
                pinch: {enabled: true},
                mode: 'xy',
                speed: 0.1,
                drag: {
                  enabled: true,
                  borderColor: 'rgb(54, 162, 235)',
                  borderWidth: 1,
                  backgroundColor: 'rgba(54, 162, 235, 0.3)'
                }
            }
        }
      }
    }
  });
  document.getElementById('issue_zoom_reset').addEventListener('click', () => {
    myChart.resetZoom();
  });
  document.getElementById('issue_zoom_toggle').addEventListener('click', () => {
    let currentState = myChart.options.plugins.zoom.zoom.wheel.enabled;
    myChart.options.plugins.zoom.zoom.wheel.enabled = !currentState;
    myChart.update();
  });
})();

(() => {
  'use strict'

  // Graphs
  const ctx = document.getElementById('pr_stats_chart')
  // fetch data from stars.json file
  const labels = {{ stats.pr_issue_time_stats.days }};
  const pr_open = {{ stats.pr_issue_time_stats.pr_open_cumulative }};
  const pr_closed = {{ stats.pr_issue_time_stats.pr_closed_cumulative }};
  const pr_merged = {{ stats.pr_issue_time_stats.pr_merged_cumulative }};

  // eslint-disable-next-line no-unused-vars
  const myChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: pr_open,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff',
        label: "pull request open",
        pointStyle: false
      },
      {
        data: pr_closed,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#ff0000',
        borderWidth: 4,
        pointBackgroundColor: '#ff0000',
        label: "pull request closed",
        pointStyle: false
      },
      {
        data: pr_merged,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#77ff00',
        borderWidth: 4,
        pointBackgroundColor: '#77ff00',
        label: "pull request merged",
        pointStyle: false
      }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true
        },
        tooltip: {
          boxPadding: 3
        },
        zoom: {
            pan: {
                enabled: true,
                mode: 'xy',
                speed: 10,
                threshold: 10,
                modifierKey: 'ctrl',
            },
            zoom: {
                wheel: {enabled: false,},
                pinch: {enabled: true},
                mode: 'xy',
                speed: 0.1,
                drag: {
                  enabled: true,
                  borderColor: 'rgb(54, 162, 235)',
                  borderWidth: 1,
                  backgroundColor: 'rgba(54, 162, 235, 0.3)'
                }
            }
        }
      }
    }
  });
  document.getElementById('pr_zoom_reset').addEventListener('click', () => {
    myChart.resetZoom();
  });
  document.getElementById('pr_zoom_toggle').addEventListener('click', () => {
    let currentState = myChart.options.plugins.zoom.zoom.wheel.enabled;
    myChart.options.plugins.zoom.zoom.wheel.enabled = !currentState;
    myChart.update();
  });
})();

(() => {
  'use strict'

  // Graphs
  const ctx = document.getElementById('issue_stats_chart2')
  // fetch data from stars.json file
  const labels = {{ stats.pr_issue_time_stats.weeks }};
  const issues_open = {{ stats.pr_issue_time_stats.issues_open_weekly }};
  const issues_closed = {{ stats.pr_issue_time_stats.issues_closed_weekly }};

  // eslint-disable-next-line no-unused-vars
  const myChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        data: issues_open,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff',
        label: "issues open",
        pointStyle: false
      },
      {
        data: issues_closed,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#ff0000',
        borderWidth: 4,
        pointBackgroundColor: '#ff0000',
        label: "issues closed",
        pointStyle: false
      }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true
        },
        tooltip: {
          boxPadding: 3
        },
        zoom: {
            pan: {
                enabled: true,
                mode: 'x',
                speed: 10,
                threshold: 10
            },
            zoom: {
                drag: {
                  enabled: true
                },
                mode: 'x',
                speed: 0.1
            }
        }
      }
    }
  })
  document.getElementById('issue_zoom_reset2').addEventListener('click', () => {
    myChart.resetZoom();
  });
})();


(() => {
  'use strict'

  // Graphs
  const ctx = document.getElementById('pr_stats_chart2')
  // fetch data from stars.json file
  const labels = {{ stats.pr_issue_time_stats.weeks }};
  const pr_open = {{ stats.pr_issue_time_stats.pr_open_weekly }};
  const pr_closed = {{ stats.pr_issue_time_stats.pr_closed_weekly }};
  const pr_merged = {{ stats.pr_issue_time_stats.pr_merged_weekly }};

  // eslint-disable-next-line no-unused-vars
  const myChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        data: pr_open,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff',
        label: "pull request open",
        pointStyle: false
      },
      {
        data: pr_closed,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#ff0000',
        borderWidth: 4,
        pointBackgroundColor: '#ff0000',
        label: "pull request closed",
        pointStyle: false
      },
      {
        data: pr_merged,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#77ff00',
        borderWidth: 4,
        pointBackgroundColor: '#77ff00',
        label: "pull merged closed",
        pointStyle: false
      }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true
        },
        tooltip: {
          boxPadding: 3
        },
        zoom: {
            pan: {
                enabled: true,
                mode: 'x',
                speed: 10,
                threshold: 10
            },
            zoom: {
                drag: {
                  enabled: true
                },
                mode: 'x',
                speed: 0.1
            }
        }
      }
    }
  })
  document.getElementById('pr_zoom_reset2').addEventListener('click', () => {
    myChart.resetZoom();
  });
})();

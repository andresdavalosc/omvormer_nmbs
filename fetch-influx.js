<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Real-Time Multiple Area Charts + Status</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
  <style>
    body {
      background-color: #f0f2f5;
      font-family: 'Segoe UI', sans-serif;
    }

    .chart-card {
      background-color: white;
      border-radius: 15px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
      padding: 20px;
      margin-bottom: 30px;
    }

    .status-indicator {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: bold;
      font-size: 1.2rem;
      margin-bottom: 30px;
    }

    .status-light {
      width: 25px;
      height: 25px;
      border-radius: 50%;
      background-color: grey;
      box-shadow: 0 0 10px #999;
      transition: background-color 0.3s ease;
    }

    .status-light.on {
      background-color: #28a745;
      box-shadow: 0 0 15px #28a745;
    }
  </style>
</head>

<body>
  <div class="container py-4">
    <h2 class="text-center mb-5">📈 Real-Time Multiple Area Charts + Status</h2>

    <div class="status-indicator">
      <div>Status:</div>
      <div id="status-light" class="status-light"></div>
      <div id="status-text">Loading...</div>
    </div>

    <div class="row" id="charts-container"></div>
  </div>

  <script>
    const influxConfig = {
      url: 'https://eu-central-1-1.aws.cloud2.influxdata.com/api/v2/query',
      org: 'WIE',
      bucket: 'omvormer_bucket',
      token: '2hMjwsBQ8KZFOJhswwCkY3y4sGWyiJLpZSMWNgO07MJ-pU5sljMBLqsLKZM8WQVrfYizasKpNtZHUJ1I-nq9tA=='
    };

    const measurementsList = [
      'amp-input',
      'dc-voltage',
      'vac-top',
      'vac-middle',
      'vac-bottom',
      'amp-top',
      'amp-middle',
      'amp-bottom',
      'kw-top',
      'kw-middle',
      'temp'
    ];

    const charts = {};
    const zoomStates = {};

    const chartsContainer = document.getElementById('charts-container');
    measurementsList.forEach(measurement => {
      const col = document.createElement('div');
      col.className = "col-md-3"; // 4 per row (12/4=3)
      col.innerHTML = `
        <div class="chart-card">
          <h5>${measurement.replace(/-/g, ' ').toUpperCase()}</h5>
          <div id="chart-${measurement}"></div>
        </div>`;
      chartsContainer.appendChild(col);
    });

    function createAreaChart(id, title) {
      const options = {
        series: [{ name: title, data: [] }],
        chart: {
          type: 'area',
          stacked: false,
          height: 280,
          zoom: {
            type: 'x',
            enabled: true,
            autoScaleYaxis: true
          },
          toolbar: { autoSelected: 'zoom' },
          events: {
            zoomed(chartContext, { xaxis }) {
              zoomStates[id] = { min: xaxis.min, max: xaxis.max };
            },
            beforeResetZoom() {
              zoomStates[id] = null;
            }
          }
        },
        dataLabels: { enabled: false },
        markers: { size: 0 },
        stroke: { width: 1 },
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            inverseColors: false,
            opacityFrom: 0.5,
            opacityTo: 0,
            stops: [0, 90, 100]
          }
        },
        title: { text: title, align: 'left' },
        yaxis: {
          labels: { formatter: val => val.toFixed(2) },
          title: { text: title }
        },
        xaxis: { type: 'datetime' },
        tooltip: {
          shared: false,
          y: { formatter: val => val.toFixed(2) }
        }
      };

      const chart = new ApexCharts(document.querySelector(`#${id}`), options);
      chart.render();
      charts[id] = chart;
    }

    function parseCSV(csv) {
      const [headerLine, ...lines] = csv.trim().split("\n");
      const headers = headerLine.split(",");
      return lines.map(line => {
        const obj = {};
        line.split(",").forEach((val, i) => {
          obj[headers[i].trim()] = val.trim();
        });
        return obj;
      });
    }

    async function fetchHistoricalData() {
      const fluxQuery = `
        from(bucket: "${influxConfig.bucket}")
          |> range(start: -10m)
          |> filter(fn: (r) => r._measurement == "omvormer")
          |> filter(fn: (r) => ${measurementsList.map(name => `r.name == "${name}"`).join(" or ")})
          |> sort(columns: ["_time"])
      `;

      const res = await fetch(`${influxConfig.url}?org=${influxConfig.org}`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${influxConfig.token}`,
          'Content-Type': 'application/vnd.flux',
          'Accept': 'application/csv'
        },
        body: fluxQuery
      });

      const csv = await res.text();
      const data = parseCSV(csv);

      const grouped = {};
      data.forEach(row => {
        const name = row.name;
        const timestamp = new Date(row._time).getTime();
        const value = parseFloat(row._value);
        if (!grouped[name]) grouped[name] = [];
        grouped[name].push({ x: timestamp, y: value });
      });

      for (const [name, datapoints] of Object.entries(grouped)) {
        const chartId = `chart-${name}`;
        if (charts[chartId]) {
          charts[chartId].updateSeries([{ name, data: datapoints }]);
        }
      }
    }

    async function fetchLatestData() {
      const fluxQuery = `
        import "experimental"
        from(bucket: "${influxConfig.bucket}")
          |> range(start: -15s)
          |> filter(fn: (r) => r._measurement == "omvormer")
          |> filter(fn: (r) => ${measurementsList.map(name => `r.name == "${name}"`).join(" or ")})
          |> last()
      `;

      const res = await fetch(`${influxConfig.url}?org=${influxConfig.org}`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${influxConfig.token}`,
          'Content-Type': 'application/vnd.flux',
          'Accept': 'application/csv'
        },
        body: fluxQuery
      });

      const csv = await res.text();
      const data = parseCSV(csv);

      data.forEach(row => {
        const name = row.name;
        const timestamp = new Date(row._time).getTime();
        const value = parseFloat(row._value);
        const chartId = `chart-${name}`;

        if (charts[chartId]) {
          const currentSeries = charts[chartId].w.config.series[0].data;
          currentSeries.push({ x: timestamp, y: value });
          if (currentSeries.length > 300) currentSeries.shift();

          const zoom = zoomStates[chartId];
          charts[chartId].updateOptions({
            xaxis: zoom ? { type: 'datetime', min: zoom.min, max: zoom.max } : { type: 'datetime' }
          }, false, false);

          charts[chartId].updateSeries([{ name, data: currentSeries }], false);
        }
      });
    }

    async function fetchStatus() {
      const fluxQuery = `
        from(bucket: "${influxConfig.bucket}")
          |> range(start: -1m)
          |> filter(fn: (r) => r._measurement == "status")
          |> filter(fn: (r) => r._field == "value")
          |> last()
      `;

      try {
        const res = await fetch(`${influxConfig.url}?org=${influxConfig.org}`, {
          method: 'POST',
          headers: {
            'Authorization': `Token ${influxConfig.token}`,
            'Content-Type': 'application/vnd.flux',
            'Accept': 'application/csv'
          },
          body: fluxQuery
        });

        const csv = await res.text();
        const data = parseCSV(csv);

        if (data.length > 0) {
          const latestStatus = data[0]._value.toLowerCase();
          const statusLight = document.getElementById('status-light');
          const statusText = document.getElementById('status-text');

          if (latestStatus === "on") {
            statusLight.classList.add('on');
            statusText.textContent = "ON";
          } else {
            statusLight.classList.remove('on');
            statusText.textContent = "OFF";
          }
        }
      } catch (error) {
        console.error('Failed to fetch status:', error);
      }
    }

    window.onload = async () => {
      measurementsList.forEach(name => createAreaChart(`chart-${name}`, name.replace(/-/g, ' ').toUpperCase()));
      await fetchHistoricalData();
      setInterval(fetchLatestData, 1000);
      setInterval(fetchStatus, 1000);
    };
  </script>
</body>

</html>

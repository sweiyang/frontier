import json
import sys
from datetime import datetime

def generate_html(json_file_path, output_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        metrics = json.load(f)

    # Sort by avg_ms descending
    metrics.sort(key=lambda x: x.get('avg_ms', 0) or 0, reverse=True)

    labels = []
    avg_times = []
    p95_times = []
    max_times = []
    counts = []

    table_rows = ""
    for m in metrics:
        scenario = m.get('scenario', '')
        endpoint = m.get('endpoint', '')
        
        # skip CHECK VALIDATE if desired
        if 'VALIDATE' in endpoint:
            continue

        short_name = f"[{scenario}] {endpoint}"
        
        labels.append(short_name)
        
        avg_v = round(m.get('avg_ms') or 0, 2)
        p50_v = round(m.get('p50_ms') or 0, 2)
        p95_v = round(m.get('p95_ms') or 0, 2)
        max_v = round(m.get('max_ms') or 0, 2)
        ttfb_v = round(m.get('ttfb_p50_ms') or 0, 2) if m.get('ttfb_p50_ms') else '-'
        
        avg_times.append(avg_v)
        p95_times.append(p95_v)
        max_times.append(max_v)
        counts.append(m.get('count', 0))

        table_rows += f"""
        <tr>
            <td>{scenario}</td>
            <td>{endpoint}</td>
            <td>{m.get('count', 0)}</td>
            <td>{m.get('failures', 0)}</td>
            <td>{avg_v}</td>
            <td>{p50_v}</td>
            <td>{p95_v}</td>
            <td>{max_v}</td>
            <td>{ttfb_v}</td>
        </tr>
        """

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backend Performance Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #fff;
            padding: 20px 40px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            border-bottom: 2px solid #f1f8ff;
            padding-bottom: 10px;
            margin-top: 40px;
        }}
        .header-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            background: #f1f8ff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            margin-top: 20px;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            width: 100%;
            margin-bottom: 50px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 40px;
            background: #fff;
        }}
        th, td {{
            padding: 14px 12px;
            text-align: right;
            border-bottom: 1px solid #edf2f7;
        }}
        th:nth-child(1), td:nth-child(1),
        th:nth-child(2), td:nth-child(2) {{
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            color: #5c6ac4;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Backend Performance Test Report</h1>
        <div class="header-info">
            <div>
                <p><strong>Generated At:</strong> {now_str}</p>
                <p><strong>Note:</strong> VALIDATE request checks are omitted from metrics charting for clarity.</p>
            </div>
        </div>

        <h2>Response Times Overview (Avg & P95)</h2>
        <div class="chart-container">
            <canvas id="timeChart"></canvas>
        </div>

        <h2>Request Volume Overview</h2>
        <div class="chart-container">
            <canvas id="volumeChart"></canvas>
        </div>

        <h2>Endpoint Metrics Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Scenario</th>
                    <th>Endpoint</th>
                    <th>Count</th>
                    <th>Failures</th>
                    <th>Avg (ms)</th>
                    <th>P50 (ms)</th>
                    <th>P95 (ms)</th>
                    <th>Max (ms)</th>
                    <th>TTFB P50 (ms)</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>

    <script>
        const ctxTime = document.getElementById('timeChart').getContext('2d');
        new Chart(ctxTime, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [
                    {{
                        label: 'Average Time (ms)',
                        data: {json.dumps(avg_times)},
                        backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    }},
                    {{
                        label: 'P95 Time (ms)',
                        data: {json.dumps(p95_times)},
                        backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        ticks: {{
                            autoSkip: false,
                            maxRotation: 45,
                            minRotation: 45
                        }}
                    }},
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Milliseconds (ms)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{ position: 'top' }}
                }}
            }}
        }});

        const ctxVolume = document.getElementById('volumeChart').getContext('2d');
        new Chart(ctxVolume, {{
            type: 'line',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [
                    {{
                        label: 'Request Count',
                        data: {json.dumps(counts)},
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        ticks: {{
                            autoSkip: false,
                            maxRotation: 45,
                            minRotation: 45
                        }}
                    }},
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Count'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Report generated successfully at {output_file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_report.py <path_to_summary.json> <output_html_path>")
        sys.exit(1)
    generate_html(sys.argv[1], sys.argv[2])

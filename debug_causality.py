import pandas as pd
from rca.ingestion.metrics_parser import parse_prometheus_json
from rca.analysis.anomaly import detect_metric_anomalies
from rca.analysis.causality import run_causality_analysis

df = parse_prometheus_json('examples/microservice_cascade/prom.json')
print('Metrics loaded:', df.shape)
print('Services:', df['service'].unique())
print('Metrics:', df['metric_name'].unique())

anomalies = detect_metric_anomalies(df)
print('Anomalies found:', len(anomalies))
for a in anomalies:
    print(a['service'], a['metric'], 'at', a['anomaly_at'])

series_dict = {}
for a in anomalies:
    key = f"{a['service']}_{a['metric']}"
    subset = df[(df['service']==a['service']) & (df['metric_name']==a['metric'])]
    series_dict[key] = pd.Series(subset['value'].values, index=subset['timestamp'].values)

print('Series pairs to test:', len(series_dict))
edges = run_causality_analysis(series_dict)
print('Causal edges found:', len(edges))
for e in edges:
    print(e)

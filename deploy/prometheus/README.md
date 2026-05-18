# Prometheus / alerting (UnuTrip)

## RAG rules

Copy `unutrip-rag-alerts.yml` into your Prometheus `rule_files` config.

Prerequisites:

- `RAG_ENABLE_METRICS=true` on the FastAPI service
- Scrape `http://<rag-host>:8001/metrics`
- Optional blackbox probe for `GET /health/ready` (used by `RagNotReady`)

## Blackbox probe example (ready)

```yaml
# prometheus.yml excerpt
scrape_configs:
  - job_name: unutrip-rag-ready
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - http://rag:8001/health/ready
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

See also `backend/rag/docs/DEPLOY_CHECKLIST.md`.

# Project Nova Architecture Notes

Project Nova uses the **Aurora API gateway** for incoming requests. Its cache is **Redis**, and cached entries expire after **12 minutes**.

## Operations

| Field | Value |
|---|---|
| Hosting region | Frankfurt |
| Nightly backup | 01:30 UTC |
| Internal service name | Aurora |
| Cache | Redis |
| Cache TTL | 12 minutes |

## Retrieval check

The cache technology and its time-to-live should be answerable from this Markdown file alone.


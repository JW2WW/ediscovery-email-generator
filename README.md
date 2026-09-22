# eDiscovery Email Generator

Synthetic email corpus for **eDiscovery / compliance testing**. It builds realistic-looking business messages (subjects, bodies, office attachments, nested forwards, ZIPs) and delivers them to a local SMTP ingestion endpoint.

This is **not** a spam tool. From/To addresses are invented (`alice.vance@enron-legacy.com`, etc.). Default delivery is `localhost:1025`.

## Requirements

- Python 3.10+
- An SMTP listener on the host/port in `config.ini` (MailHog, Mailpit, or your eDiscovery ingest). Default: `localhost:1025`.

No third-party packages are required for the main pipeline.

## Quick start

```bash
# Point config.ini at your SMTP ingest if it is not localhost:1025
python3 main.py
```

Each run:

1. Optionally harvests a public government document and seeds a few local office files under `samples/`
2. Builds `batch_size` messages (default 10)
3. Attaches generated PDFs/Office docs, pool files, nested `.eml`, or ZIP bundles
4. Sends them through SMTP

Harvest attachments only:

```bash
python3 scourer.py
```

`samples/` is created locally and is **not** in this repository.

## Config

See `config.ini`:

| Section | Keys | Notes |
|---------|------|--------|
| `[smtp]` | `host`, `port` | Ingestion server |
| `[generation]` | `batch_size` | Messages per run |
| `[dates]` | `randomize_date`, `range_years_back` | Date header; off by default |

`min_attachments` / `max_attachments` in the config file are unused; attachment mix is chosen in `main.py`.

## Layout

| File | Role |
|------|------|
| `main.py` | Batch orchestrator |
| `contentfetcher.py` | Subject/body from public sources, wrapped as business mail |
| `docgenerator.py` | PDF / XLSX / XLS / DOCX / DOC / PPTX / PPT (stdlib only) _(Note: .doc and .ppt are generated as RTF files, not native binary formats.)_ |
| `assetmanager.py` | MIME attachments, nested `.eml`, ZIP bundles |
| `mail_sender.py` | MIME assembly and SMTP send |
| `scourer.py` | GovInfo / Federal Register harvest + local doc seed |
| `generator.py` | Unused RSS helper (legacy) |

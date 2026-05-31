# MAMH Data Cache

The public comparable pipeline depends on local MAMH role files:

- `role_mtl.csv` for Montreal.
- `role_<city>.xml` and `role_<city>_index.json` for Quebec, Laval, Longueuil, Gatineau, and Sherbrooke.

These files are intentionally not committed. They are large public datasets and should be provisioned into a persistent cache before production use.

## Cache Path

The backend resolves the cache directory in this order:

1. `DATA_CACHE_DIR`, when set.
2. `backend/data_cache`, when `DATA_CACHE_DIR` is absent.

On Railway, use a persistent volume path. A practical layout is:

```bash
SESSIONS_DIR=/data/sessions
DATA_CACHE_DIR=/data/data_cache
```

Mount the Railway volume at `/data` or mount separate volumes for `/data/sessions` and `/data/data_cache`.

## Provision All Supported Data

From the `backend` directory:

```bash
python scripts/provision_mamh_cache.py --all
```

With an explicit cache path:

```bash
python scripts/provision_mamh_cache.py --cache-dir /data/data_cache --all
```

Machine-readable output for deployment logs:

```bash
python scripts/provision_mamh_cache.py --cache-dir /data/data_cache --all --json
```

The command exits non-zero if any selected source is missing or failed.

## Provision One Source

Montreal only:

```bash
python scripts/provision_mamh_cache.py --montreal
```

One XML city:

```bash
python scripts/provision_mamh_cache.py --xml-city gatineau
```

Repeat `--xml-city` for multiple cities:

```bash
python scripts/provision_mamh_cache.py --xml-city laval --xml-city longueuil
```

## Rebuild Indexes From Existing Files

If XML files were copied into the cache manually, build indexes without network calls:

```bash
python scripts/provision_mamh_cache.py --cache-dir /data/data_cache --xml-city laval --skip-download
```

Use `--force` to rebuild an index even when it is current:

```bash
python scripts/provision_mamh_cache.py --cache-dir /data/data_cache --xml-city laval --skip-download --force
```

## Operational Notes

- XML role files can be hundreds of MB; first provisioning may take several minutes.
- The backend can still run without these files. Missing MAMH data produces source diagnostics and an empty public comparable pool instead of failing the appraisal pipeline.
- Provisioning should be run during setup or as an operator task, not inside request handling.
- Keep `DATA_CACHE_DIR` on persistent storage. An ephemeral cache will disappear on Railway redeploys and public comparable matching will degrade to empty pools.

# External Source Smoke Tests

The external-source smoke suite verifies production dependencies that mocked unit tests cannot prove:

- Infolot WFS returns cadastral lots for a known coordinate.
- MAMH cache files and XML indexes are present and readable.
- SIRF credentials can enrich a known lot with a transaction price.

The suite is skipped by default. Run it only from an environment where network calls and paid SIRF lookups are acceptable.

## Run Default-Skipped Suite

```powershell
cd backend
python -m pytest tests/test_live_external_sources.py -q
```

Expected result without opt-in: all tests skipped.

## Infolot WFS

```powershell
$env:EVAL_IMMO_LIVE_EXTERNALS = "1"
python -m pytest tests/test_live_external_sources.py::test_live_infolot_wfs_returns_cadastral_lots -q
```

Optional coordinates:

```powershell
$env:EVAL_IMMO_INFOL0T_LAT = "45.5450"
$env:EVAL_IMMO_INFOL0T_LON = "-73.7450"
$env:EVAL_IMMO_INFOL0T_RADIUS_KM = "0.5"
```

Expected: at least one lot with `no_lot`, centroid, and distance within the radius.

## MAMH Cache

Provision the cache first:

```powershell
python scripts/provision_mamh_cache.py --cache-dir C:\data\eval-immo\data_cache --all
```

Then run:

```powershell
$env:EVAL_IMMO_LIVE_EXTERNALS = "1"
$env:DATA_CACHE_DIR = "C:\data\eval-immo\data_cache"
$env:EVAL_IMMO_MAMH_CITY = "laval"
python -m pytest tests/test_live_external_sources.py::test_live_mamh_cache_has_index_and_optional_lookup -q
```

Optional lot lookup:

```powershell
$env:EVAL_IMMO_MAMH_TEST_LOT = "1234567"
```

For Montreal:

```powershell
$env:EVAL_IMMO_MAMH_CITY = "montreal"
$env:EVAL_IMMO_MAMH_TEST_MATRICULE = "0000-00-0000-0-000-0"
```

Expected: cache/index files exist, `_count > 0`, and optional lookup returns one role record.

## SIRF

SIRF lookups can incur Registre foncier charges. Use a known lot with a recent transaction and run only when billing is approved.

```powershell
$env:EVAL_IMMO_LIVE_EXTERNALS = "1"
$env:EVAL_IMMO_LIVE_SIRF = "1"
$env:SIRF_USERNAME = "<user>"
$env:SIRF_PASSWORD = "<password>"
$env:SIRF_TEST_LOT = "1234567"
python -m pytest tests/test_live_external_sources.py::test_live_sirf_enriches_known_lot -q
```

Expected: SIRF diagnostic status is `ok` or `partial`, `source_type` becomes `registre_foncier`, `prix_vente > 0`, and `date_vente` is populated.

## Full Live Smoke

```powershell
$env:EVAL_IMMO_LIVE_EXTERNALS = "1"
$env:DATA_CACHE_DIR = "C:\data\eval-immo\data_cache"
$env:EVAL_IMMO_LIVE_SIRF = "1"
$env:SIRF_USERNAME = "<user>"
$env:SIRF_PASSWORD = "<password>"
$env:SIRF_TEST_LOT = "1234567"
python -m pytest tests/test_live_external_sources.py -q
```

Do not add these env vars to CI unless the runner has approved network access, persistent MAMH data, and SIRF billing approval.

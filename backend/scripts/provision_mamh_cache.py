#!/usr/bin/env python3
"""
Provision the local MAMH role cache used by enrichment and comparables.

The command downloads the Montreal CSV and/or supported city XML roles, then
builds JSON indexes for XML roles. Network errors are summarized per source so
operators can retry without losing successful cache files.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import data_enrichment as mamh  # noqa: E402


def supported_xml_cities() -> tuple[str, ...]:
    return tuple(sorted(mamh._ROLE_XML_CITIES.keys()))


def _jsonable_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path)


def _result(
    *,
    source: str,
    status: str,
    city_code: str | None = None,
    path: Path | None = None,
    index_path: Path | None = None,
    indexed_count: int | None = None,
    cache_hit: bool = False,
    index_status: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "city_code": city_code,
        "status": status,
        "path": _jsonable_path(path),
        "index_path": _jsonable_path(index_path),
        "indexed_count": indexed_count,
        "cache_hit": cache_hit,
        "index_status": index_status,
        "error": error,
    }


def _needs_index(xml_path: Path, index_path: Path, *, force: bool) -> bool:
    if force or not index_path.exists():
        return True
    try:
        return xml_path.stat().st_mtime > index_path.stat().st_mtime
    except OSError:
        return True


def _provision_montreal(
    cache_dir: Path,
    *,
    force: bool,
    skip_download: bool,
) -> dict[str, Any]:
    csv_path = cache_dir / "role_mtl.csv"
    existed = csv_path.exists()

    if skip_download:
        if not existed:
            return _result(
                source="mamh-montreal-csv",
                status="missing",
                path=csv_path,
                error="role_mtl.csv is absent and --skip-download was used",
            )
        return _result(
            source="mamh-montreal-csv",
            status="ok",
            path=csv_path,
            cache_hit=True,
        )

    try:
        path = mamh.download_role_mtl(cache_dir, force=force)
    except Exception as exc:
        return _result(
            source="mamh-montreal-csv",
            status="failed",
            path=csv_path,
            error=f"{type(exc).__name__}: {exc}",
        )

    return _result(
        source="mamh-montreal-csv",
        status="ok",
        path=path,
        cache_hit=existed and not force,
    )


def _provision_xml_city(
    city_code: str,
    cache_dir: Path,
    *,
    force: bool,
    skip_download: bool,
) -> dict[str, Any]:
    xml_path = cache_dir / f"role_{city_code}.xml"
    index_path = cache_dir / f"role_{city_code}_index.json"
    existed = xml_path.exists()

    if city_code not in supported_xml_cities():
        return _result(
            source="mamh-xml",
            city_code=city_code,
            status="failed",
            path=xml_path,
            index_path=index_path,
            error=f"unsupported city_code: {city_code}",
        )

    if skip_download:
        if not xml_path.exists():
            return _result(
                source="mamh-xml",
                city_code=city_code,
                status="missing",
                path=xml_path,
                index_path=index_path,
                error=f"{xml_path.name} is absent and --skip-download was used",
            )
    else:
        try:
            downloaded = mamh.download_role_xml(city_code, cache_dir, force=force)
        except Exception as exc:
            return _result(
                source="mamh-xml",
                city_code=city_code,
                status="failed",
                path=xml_path,
                index_path=index_path,
                error=f"{type(exc).__name__}: {exc}",
            )
        if downloaded is None:
            return _result(
                source="mamh-xml",
                city_code=city_code,
                status="failed",
                path=xml_path,
                index_path=index_path,
                error=f"no XML download configured for {city_code}",
            )
        xml_path = downloaded

    if not _needs_index(xml_path, index_path, force=force):
        return _result(
            source="mamh-xml",
            city_code=city_code,
            status="ok",
            path=xml_path,
            index_path=index_path,
            cache_hit=existed and not force,
            index_status="current",
        )

    try:
        indexed_count = mamh.build_role_xml_index(xml_path, index_path, city_code)
    except Exception as exc:
        return _result(
            source="mamh-xml",
            city_code=city_code,
            status="failed",
            path=xml_path,
            index_path=index_path,
            cache_hit=existed and not force,
            index_status="failed",
            error=f"{type(exc).__name__}: {exc}",
        )

    return _result(
        source="mamh-xml",
        city_code=city_code,
        status="ok",
        path=xml_path,
        index_path=index_path,
        indexed_count=indexed_count,
        cache_hit=existed and not force,
        index_status="built",
    )


def provision_mamh_cache(
    cache_dir: Path,
    *,
    include_montreal: bool = False,
    xml_cities: Iterable[str] = (),
    force: bool = False,
    skip_download: bool = False,
) -> list[dict[str, Any]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    if include_montreal:
        results.append(
            _provision_montreal(cache_dir, force=force, skip_download=skip_download)
        )

    for city_code in dict.fromkeys(xml_cities):
        results.append(
            _provision_xml_city(
                city_code,
                cache_dir,
                force=force,
                skip_download=skip_download,
            )
        )

    return results


def _default_cache_dir() -> Path:
    configured = os.environ.get("DATA_CACHE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    return mamh.get_data_cache_dir(ROOT / "data_cache")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and index MAMH role data into DATA_CACHE_DIR.",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(_default_cache_dir()),
        help="Cache directory. Defaults to DATA_CACHE_DIR or backend/data_cache.",
    )
    parser.add_argument(
        "--montreal",
        action="store_true",
        help="Provision the Montreal role CSV.",
    )
    parser.add_argument(
        "--xml-city",
        action="append",
        choices=supported_xml_cities(),
        default=[],
        help="Provision one XML city. May be repeated.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Provision Montreal plus all supported XML cities.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download selected files and rebuild XML indexes.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Build indexes only from files already present in the cache.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON summary.",
    )
    return parser


def _summarize(cache_dir: Path, results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    failed = [r for r in results if r["status"] == "failed"]
    missing = [r for r in results if r["status"] == "missing"]
    ok = [r for r in results if r["status"] == "ok"]
    return {
        "cache_dir": str(cache_dir),
        "ok_count": len(ok),
        "missing_count": len(missing),
        "failed_count": len(failed),
        "results": list(results),
    }


def _print_human_summary(summary: dict[str, Any]) -> None:
    print(f"MAMH cache: {summary['cache_dir']}")
    for item in summary["results"]:
        label = item["source"]
        if item.get("city_code"):
            label += f":{item['city_code']}"
        status = item["status"].upper()
        details: list[str] = []
        if item.get("cache_hit"):
            details.append("cached")
        if item.get("index_status"):
            details.append(f"index={item['index_status']}")
        if item.get("indexed_count") is not None:
            details.append(f"records={item['indexed_count']}")
        if item.get("error"):
            details.append(item["error"])
        suffix = f" ({'; '.join(details)})" if details else ""
        print(f"[{status}] {label}{suffix}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    include_montreal = bool(args.montreal or args.all)
    xml_cities = list(supported_xml_cities()) if args.all else list(args.xml_city)
    if not include_montreal and not xml_cities:
        parser.error("select at least one target: --montreal, --xml-city, or --all")

    cache_dir = Path(args.cache_dir).expanduser()
    results = provision_mamh_cache(
        cache_dir,
        include_montreal=include_montreal,
        xml_cities=xml_cities,
        force=bool(args.force),
        skip_download=bool(args.skip_download),
    )
    summary = _summarize(cache_dir, results)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_human_summary(summary)

    return 1 if summary["failed_count"] or summary["missing_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

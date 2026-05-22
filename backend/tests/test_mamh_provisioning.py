import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from engine.data_enrichment import get_data_cache_dir
from scripts import provision_mamh_cache as provision


def test_provision_downloads_montreal_and_builds_xml_index(tmp_path, monkeypatch):
    calls: list[tuple[str, str | None, bool]] = []

    def fake_download_role_mtl(cache_dir: Path, force: bool = False) -> Path:
        calls.append(("mtl", None, force))
        path = cache_dir / "role_mtl.csv"
        path.write_text("MATRICULE83\n", encoding="utf-8")
        return path

    def fake_download_role_xml(city_code: str, cache_dir: Path, force: bool = False) -> Path:
        calls.append(("xml", city_code, force))
        path = cache_dir / f"role_{city_code}.xml"
        path.write_text("<RLUEsAll />", encoding="utf-8")
        return path

    def fake_build_role_xml_index(xml_path: Path, index_path: Path, city_code: str) -> int:
        calls.append(("index", city_code, False))
        index_path.write_text("{}", encoding="utf-8")
        return 17

    monkeypatch.setattr(provision.mamh, "download_role_mtl", fake_download_role_mtl)
    monkeypatch.setattr(provision.mamh, "download_role_xml", fake_download_role_xml)
    monkeypatch.setattr(provision.mamh, "build_role_xml_index", fake_build_role_xml_index)

    results = provision.provision_mamh_cache(
        tmp_path,
        include_montreal=True,
        xml_cities=["gatineau", "gatineau"],
        force=True,
    )

    assert [r["status"] for r in results] == ["ok", "ok"]
    assert results[0]["source"] == "mamh-montreal-csv"
    assert results[1]["city_code"] == "gatineau"
    assert results[1]["indexed_count"] == 17
    assert results[1]["index_status"] == "built"
    assert calls == [
        ("mtl", None, True),
        ("xml", "gatineau", True),
        ("index", "gatineau", False),
    ]


def test_skip_download_builds_index_from_existing_xml(tmp_path, monkeypatch):
    xml_path = tmp_path / "role_laval.xml"
    xml_path.write_text("<RLUEsAll />", encoding="utf-8")
    build_calls: list[tuple[Path, Path, str]] = []

    def fail_download(*_args, **_kwargs):
        raise AssertionError("download should not be called with --skip-download")

    def fake_build_role_xml_index(xml_path_arg: Path, index_path: Path, city_code: str) -> int:
        build_calls.append((xml_path_arg, index_path, city_code))
        index_path.write_text("{}", encoding="utf-8")
        return 3

    monkeypatch.setattr(provision.mamh, "download_role_xml", fail_download)
    monkeypatch.setattr(provision.mamh, "build_role_xml_index", fake_build_role_xml_index)

    results = provision.provision_mamh_cache(
        tmp_path,
        xml_cities=["laval"],
        skip_download=True,
    )

    assert results == [
        {
            "source": "mamh-xml",
            "city_code": "laval",
            "status": "ok",
            "path": str(xml_path),
            "index_path": str(tmp_path / "role_laval_index.json"),
            "indexed_count": 3,
            "cache_hit": True,
            "index_status": "built",
            "error": None,
        }
    ]
    assert build_calls == [(xml_path, tmp_path / "role_laval_index.json", "laval")]


def test_skip_download_reports_missing_xml_without_building(tmp_path, monkeypatch):
    def fail_build(*_args, **_kwargs):
        raise AssertionError("index build should not run when XML is missing")

    monkeypatch.setattr(provision.mamh, "build_role_xml_index", fail_build)

    results = provision.provision_mamh_cache(
        tmp_path,
        xml_cities=["quebec"],
        skip_download=True,
    )

    assert results[0]["status"] == "missing"
    assert results[0]["city_code"] == "quebec"
    assert "skip-download" in results[0]["error"]


def test_default_cache_dir_honors_data_cache_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_CACHE_DIR", str(tmp_path))

    assert provision._default_cache_dir() == tmp_path
    assert get_data_cache_dir() == tmp_path


def test_cli_json_summary_returns_nonzero_for_missing_target(tmp_path, capsys):
    code = provision.main(
        ["--cache-dir", str(tmp_path), "--xml-city", "sherbrooke", "--skip-download", "--json"]
    )

    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["cache_dir"] == str(tmp_path)
    assert payload["missing_count"] == 1
    assert payload["results"][0]["city_code"] == "sherbrooke"

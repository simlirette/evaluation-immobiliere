import json
from pathlib import Path
import tempfile
import pytest
from engine.data_enrichment import build_role_xml_index, lookup_role_by_lot

MINIMAL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RLUEsAll>
  <RLUEx>
    <RL0101>
      <RL0101x>
        <RL0101Ax>123</RL0101Ax>
        <RL0101Ex>RUE</RL0101Ex>
        <RL0101Gx>PRINCIPALE</RL0101Gx>
      </RL0101x>
    </RL0101>
    <RL0104>
      <RL0104A>1234</RL0104A>
      <RL0104B>56</RL0104B>
      <RL0104C>7890</RL0104C>
      <RL0104D>A</RL0104D>
      <RL0104E>0</RL0104E>
      <RL0104F>0</RL0104F>
    </RL0104>
    <RL0103>
      <RL0103x>
        <RL0103Ax>4567890</RL0103Ax>
      </RL0103x>
    </RL0103>
    <RL0307A>1985</RL0307A>
    <RL0308A>120.5</RL0308A>
    <RL0302A>350.0</RL0302A>
    <RL0311A>1</RL0311A>
    <RL0105A>1000</RL0105A>
    <RL0402A>125000</RL0402A>
    <RL0403A>215000</RL0403A>
    <RL0404A>340000</RL0404A>
    <RL0405A>340000</RL0405A>
  </RLUEx>
</RLUEsAll>
"""

def test_by_lot_in_index():
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "role.xml"
        index_path = Path(tmp) / "index.json"
        xml_path.write_text(MINIMAL_XML, encoding="utf-8")
        build_role_xml_index(xml_path, index_path, city_code="test")
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        assert "by_lot" in idx
        assert "4567890" in idx["by_lot"]
        rec = idx["by_lot"]["4567890"]
        assert rec["superficie_batiment_m2"] == pytest.approx(120.5)
        assert rec["annee_construction"] == 1985

def test_lookup_role_by_lot_found():
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "role.xml"
        index_path = Path(tmp) / "index.json"
        xml_path.write_text(MINIMAL_XML, encoding="utf-8")
        build_role_xml_index(xml_path, index_path, city_code="test")
        result = lookup_role_by_lot(index_path, no_lot=4567890)
        assert result["annee_construction"] == 1985
        assert result["superficie_batiment_m2"] == pytest.approx(120.5)
        assert result["no_lot"] == 4567890

def test_lookup_role_by_lot_missing():
    with tempfile.TemporaryDirectory() as tmp:
        index_path = Path(tmp) / "nonexistent.json"
        result = lookup_role_by_lot(index_path, no_lot=9999)
        assert result == {}

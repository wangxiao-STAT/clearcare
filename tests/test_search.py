from app.search import search_services, SERVICE_CATALOG


def test_exact_service_name():
    results = search_services("MRI Knee")
    assert len(results) == 1
    assert results[0]["name"] == "MRI Knee"
    assert set(results[0]["hcpcs_codes"]) == {"73721", "73723"}


def test_synonym_match():
    results = search_services("knee scan")
    assert len(results) == 1
    assert results[0]["name"] == "MRI Knee"


def test_partial_match():
    results = search_services("colonoscopy")
    assert len(results) == 1
    assert results[0]["name"] == "Colonoscopy"


def test_broad_term_returns_multiple():
    results = search_services("MRI")
    names = {r["name"] for r in results}
    assert "MRI Brain" in names
    assert "MRI Knee" in names


def test_no_match_returns_all():
    results = search_services("xyz nonsense")
    assert len(results) == len(SERVICE_CATALOG)


def test_case_insensitive():
    results = search_services("mri knee")
    assert len(results) == 1
    assert results[0]["name"] == "MRI Knee"


def test_blood_test_synonym():
    results = search_services("blood test")
    assert len(results) == 1
    assert results[0]["name"] == "Blood Work (CBC + Lipid Panel)"


def test_catalog_has_six_services():
    assert len(SERVICE_CATALOG) == 6


def test_each_service_has_required_fields():
    for svc in SERVICE_CATALOG:
        assert "name" in svc
        assert "category" in svc
        assert "hcpcs_codes" in svc
        assert "synonyms" in svc
        assert len(svc["hcpcs_codes"]) > 0

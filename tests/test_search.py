from app.search import search_services, SERVICE_CATALOG


def test_exact_service_name():
    result = search_services("MRI Knee")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "MRI Knee"
    assert set(result.services[0]["hcpcs_codes"]) == {"73721", "73723"}


def test_synonym_match():
    result = search_services("knee scan")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "MRI Knee"


def test_partial_match():
    result = search_services("colonoscopy")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Colonoscopy"


def test_broad_term_returns_multiple():
    result = search_services("MRI")
    names = {r["name"] for r in result.services}
    assert "MRI Brain" in names
    assert "MRI Knee" in names


def test_no_match_returns_all():
    result = search_services("xyz nonsense")
    assert len(result.services) == len(SERVICE_CATALOG)


def test_case_insensitive():
    result = search_services("mri knee")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "MRI Knee"


def test_cbc_synonym():
    result = search_services("cbc")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "CBC (Complete Blood Count)"


def test_catalog_has_sixteen_services():
    assert len(SERVICE_CATALOG) == 16


def test_each_service_has_required_fields():
    for svc in SERVICE_CATALOG:
        assert "name" in svc
        assert "category" in svc
        assert "hcpcs_codes" in svc
        assert "synonyms" in svc
        assert "symptoms" in svc
        assert len(svc["hcpcs_codes"]) > 0


def test_a1c_synonym():
    result = search_services("a1c")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "HbA1c (Diabetes Test)"


def test_thyroid_synonym():
    result = search_services("thyroid")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "TSH (Thyroid Test)"


def test_echo_synonym():
    result = search_services("echo")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Echocardiogram"


def test_egd_synonym():
    result = search_services("egd")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Upper GI Endoscopy (EGD)"


def test_chest_xray_synonym():
    result = search_services("chest xray")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Chest X-ray"


def test_symptom_knee_pain_returns_mri_and_pt():
    result = search_services("knee pain")
    names = {s["name"] for s in result.services}
    assert "MRI Knee" in names
    assert "Physical Therapy Evaluation" in names


def test_symptom_heartburn_returns_egd():
    result = search_services("heartburn")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Upper GI Endoscopy (EGD)"


def test_symptom_sets_matched_symptom_field():
    result = search_services("knee pain")
    assert result.matched_symptom is not None
    assert "knee pain" in result.matched_symptom.lower()


def test_out_of_scope_primary_care():
    result = search_services("primary care")
    assert result.services == []
    assert result.out_of_scope == "primary care"
    assert result.matched_symptom is None


def test_out_of_scope_emergency_room():
    result = search_services("emergency room")
    assert result.services == []
    assert result.out_of_scope == "emergency"

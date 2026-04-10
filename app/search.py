SERVICE_CATALOG = [
    {
        "name": "MRI Brain",
        "category": "Imaging",
        "hcpcs_codes": ["70551", "70553"],
        "variants": {"70551": "without contrast", "70553": "with contrast"},
        "synonyms": ["mri brain", "brain mri", "brain scan", "head mri", "mri head"],
    },
    {
        "name": "MRI Knee",
        "category": "Imaging",
        "hcpcs_codes": ["73721", "73723"],
        "variants": {"73721": "without contrast", "73723": "with contrast"},
        "synonyms": ["mri knee", "knee mri", "knee scan", "leg mri", "mri leg joint"],
    },
    {
        "name": "CT Head",
        "category": "Imaging",
        "hcpcs_codes": ["70450"],
        "variants": {"70450": "without contrast"},
        "synonyms": ["ct head", "head ct", "ct brain", "cat scan head", "head scan", "brain ct"],
    },
    {
        "name": "CT Abdomen & Pelvis",
        "category": "Imaging",
        "hcpcs_codes": ["74177", "74178"],
        "variants": {"74177": "with contrast", "74178": "before and after contrast"},
        "synonyms": [
            "ct abdomen",
            "ct pelvis",
            "ct scan abdomen",
            "ct scan pelvis",
            "abdominal ct",
            "cat scan abdomen",
            "cat scan",
        ],
    },
    {
        "name": "Chest X-ray",
        "category": "Imaging",
        "hcpcs_codes": ["71046"],
        "variants": {"71046": "2 views"},
        "synonyms": [
            "chest xray",
            "chest x-ray",
            "x-ray chest",
            "chest xr",
            "lung xray",
            "chest radiograph",
        ],
    },
    {
        "name": "Ultrasound Abdomen",
        "category": "Imaging",
        "hcpcs_codes": ["76700", "76705"],
        "variants": {"76700": "complete", "76705": "limited"},
        "synonyms": [
            "ultrasound abdomen",
            "abdominal ultrasound",
            "belly ultrasound",
            "abdomen sonogram",
            "abdomen ultrasound",
        ],
    },
    {
        "name": "Screening Mammogram",
        "category": "Imaging",
        "hcpcs_codes": ["77067"],
        "variants": {"77067": "screening"},
        "synonyms": [
            "mammogram",
            "mammography",
            "breast screening",
            "breast scan",
            "screening mammogram",
        ],
    },
    {
        "name": "Echocardiogram",
        "category": "Imaging",
        "hcpcs_codes": ["93306"],
        "variants": {"93306": "complete with Doppler"},
        "synonyms": [
            "echo",
            "echocardiogram",
            "heart ultrasound",
            "heart echo",
            "cardiac ultrasound",
            "echocardiography",
        ],
    },
    {
        "name": "Colonoscopy",
        "category": "GI/Outpatient",
        "hcpcs_codes": ["45378", "45380", "45385"],
        "variants": {
            "45378": "diagnostic",
            "45380": "with biopsy",
            "45385": "with polyp removal",
        },
        "synonyms": [
            "colonoscopy",
            "colon scope",
            "colon screening",
            "colon exam",
            "lower endoscopy",
        ],
    },
    {
        "name": "Upper GI Endoscopy (EGD)",
        "category": "GI/Outpatient",
        "hcpcs_codes": ["43235", "43239"],
        "variants": {"43235": "diagnostic", "43239": "with biopsy"},
        "synonyms": [
            "egd",
            "upper endoscopy",
            "upper gi",
            "stomach scope",
            "esophagus scope",
            "upper gi scope",
            "esophagogastroduodenoscopy",
        ],
    },
    {
        "name": "CBC (Complete Blood Count)",
        "category": "Labs",
        "hcpcs_codes": ["85025"],
        "variants": {"85025": "automated with differential"},
        "synonyms": [
            "cbc",
            "complete blood count",
            "blood count",
            "white cell count",
            "blood cell count",
        ],
    },
    {
        "name": "Lipid Panel",
        "category": "Labs",
        "hcpcs_codes": ["80061"],
        "variants": {"80061": "cholesterol & triglycerides"},
        "synonyms": [
            "lipid panel",
            "cholesterol test",
            "cholesterol",
            "lipid",
            "triglycerides",
            "lipid profile",
        ],
    },
    {
        "name": "CMP (Comprehensive Metabolic Panel)",
        "category": "Labs",
        "hcpcs_codes": ["80053"],
        "variants": {"80053": "14-test panel"},
        "synonyms": [
            "cmp",
            "comprehensive metabolic panel",
            "metabolic panel",
            "chem 14",
            "metabolic test",
            "chemistry panel",
        ],
    },
    {
        "name": "HbA1c (Diabetes Test)",
        "category": "Labs",
        "hcpcs_codes": ["83036"],
        "variants": {"83036": "glycated hemoglobin"},
        "synonyms": [
            "a1c",
            "hba1c",
            "hemoglobin a1c",
            "diabetes test",
            "glycated hemoglobin",
            "sugar test",
            "blood sugar test",
        ],
    },
    {
        "name": "TSH (Thyroid Test)",
        "category": "Labs",
        "hcpcs_codes": ["84443"],
        "variants": {"84443": "thyroid stimulating hormone"},
        "synonyms": [
            "tsh",
            "thyroid",
            "thyroid test",
            "thyroid stimulating hormone",
            "thyroid panel",
            "thyroid function",
        ],
    },
    {
        "name": "Physical Therapy Evaluation",
        "category": "Rehab",
        "hcpcs_codes": ["97161", "97162"],
        "variants": {"97161": "low complexity (20 min)", "97162": "moderate complexity (30 min)"},
        "synonyms": [
            "pt eval",
            "physical therapy eval",
            "pt evaluation",
            "physical therapy evaluation",
            "pt assessment",
        ],
    },
]


def search_services(query: str) -> list[dict]:
    """Match a plain-English query to services. Returns all services if no match."""
    query_lower = query.lower().strip()
    scored = []
    for svc in SERVICE_CATALOG:
        name_lower = svc["name"].lower()
        # Exact name match
        if query_lower == name_lower:
            scored.append((100, svc))
            continue
        # Name contains query or query contains name
        if query_lower in name_lower or name_lower in query_lower:
            scored.append((80, svc))
            continue
        # Synonym match
        synonym_matched = False
        for syn in svc["synonyms"]:
            if query_lower == syn or query_lower in syn or syn in query_lower:
                scored.append((60, svc))
                synonym_matched = True
                break
        if synonym_matched:
            continue
        # Word overlap
        query_words = set(query_lower.split())
        name_words = set(name_lower.split())
        synonym_words = set()
        for syn in svc["synonyms"]:
            synonym_words.update(syn.split())
        overlap = query_words & (name_words | synonym_words)
        if overlap:
            scored.append((len(overlap) * 20, svc))

    if not scored:
        return list(SERVICE_CATALOG)
    scored.sort(key=lambda x: x[0], reverse=True)
    top_score = scored[0][0]
    return [svc for score, svc in scored if score >= top_score]

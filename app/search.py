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
            "scope",
            "colon screening",
            "colon exam",
        ],
    },
    {
        "name": "Blood Work (CBC + Lipid Panel)",
        "category": "Labs",
        "hcpcs_codes": ["85025", "80061"],
        "variants": {
            "85025": "CBC (complete blood count)",
            "80061": "lipid panel (cholesterol & triglycerides)",
        },
        "synonyms": [
            "blood test",
            "blood work",
            "bloodwork",
            "cbc",
            "lipid panel",
            "cholesterol test",
            "cholesterol",
            "lab work",
            "labs",
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

# Service Explanation Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add hand-curated plain-English explanations for each of the 16 services, displayed in an expandable "About this service" section below the stats bar.

**Architecture:** A hand-written JSON file (`data/processed/service_explanations.json`) holds all 16 entries. A small runtime module (`app/explanations.py`) loads and queries it. The Streamlit UI adds a cached loader and an expander block. No new dependencies, no API keys, no runtime LLM calls.

**Tech Stack:** Python 3.11, streamlit, pytest (no new deps)

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `app/explanations.py` | Create | `load_explanations`, `get_explanation` |
| `tests/test_explanations.py` | Create | 5 tests |
| `data/processed/service_explanations.json` | Create (committed) | 16 hand-curated entries |
| `app/streamlit_app.py` | Modify | Add cached loader + expander section |

---

### Task 1: Runtime Module and Unit Tests

**Files:**
- Create: `app/explanations.py`
- Create: `tests/test_explanations.py`

- [ ] **Step 1: Write failing tests for `load_explanations` and `get_explanation`**

Create `tests/test_explanations.py` with this exact content:

```python
import json
import tempfile
import os
import pytest
from app.explanations import load_explanations, get_explanation, REQUIRED_FIELDS


def _make_test_explanations():
    return {
        "MRI Knee": {
            "description": "Test description.",
            "typically_included": ["a", "b"],
            "billed_separately": ["c", "d"],
            "what_to_expect": "Test expectations.",
            "questions_to_ask": ["q1", "q2"],
        }
    }


def test_load_explanations_returns_dict():
    data = _make_test_explanations()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(data, f)
        path = f.name
    try:
        result = load_explanations(path)
    finally:
        os.unlink(path)
    assert isinstance(result, dict)
    assert "MRI Knee" in result
    assert result["MRI Knee"]["description"] == "Test description."


def test_load_explanations_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_explanations("/nonexistent/path/to/explanations.json")


def test_get_explanation_found():
    data = _make_test_explanations()
    result = get_explanation(data, "MRI Knee")
    assert result is not None
    assert result["description"] == "Test description."


def test_get_explanation_not_found():
    data = _make_test_explanations()
    result = get_explanation(data, "Unknown Service")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_explanations.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.explanations'`

- [ ] **Step 3: Implement `app/explanations.py`**

Create `app/explanations.py`:

```python
"""Load and query pre-generated service explanations."""

import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent.parent / "data" / "processed" / "service_explanations.json"

REQUIRED_FIELDS = [
    "description",
    "typically_included",
    "billed_separately",
    "what_to_expect",
    "questions_to_ask",
]


def load_explanations(path: str | None = None) -> dict[str, dict]:
    """Load service explanations from JSON.

    Returns a dict mapping service_name to an explanation dict.
    Raises FileNotFoundError if the file is missing (fail loudly).
    """
    p = Path(path) if path else DEFAULT_PATH
    with p.open() as f:
        return json.load(f)


def get_explanation(explanations: dict, service_name: str) -> dict | None:
    """Return the explanation for a service, or None if not found."""
    return explanations.get(service_name)
```

- [ ] **Step 4: Run tests to verify the 4 unit tests pass**

```bash
python3 -m pytest tests/test_explanations.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/explanations.py tests/test_explanations.py
git commit -m "feat: add explanations runtime module"
```

---

### Task 2: Create the Hand-Curated JSON File

**Files:**
- Create: `data/processed/service_explanations.json`

- [ ] **Step 1: Create the JSON file with exactly this content**

Create `data/processed/service_explanations.json` with this exact content (preserve all keys, values, order, and indentation):

```json
{
  "CBC (Complete Blood Count)": {
    "description": "A CBC is a common blood test that measures your red blood cells, white blood cells, and platelets. Doctors use it to check your overall health, look for infections, anemia, and many other conditions.",
    "typically_included": [
      "Drawing the blood sample",
      "The lab test itself",
      "A report sent to your doctor"
    ],
    "billed_separately": [
      "Office visit if the blood draw happens during a doctor's appointment",
      "Additional tests ordered alongside the CBC (each test is usually billed separately)",
      "Hospital outpatient facility fee if drawn at a hospital lab"
    ],
    "what_to_expect": "A quick blood draw from your arm, usually taking less than 5 minutes. No prep is needed. You can eat normally unless other tests are ordered that require fasting.",
    "questions_to_ask": [
      "Is this being drawn at a hospital outpatient lab or a freestanding lab like Quest or LabCorp? Freestanding labs are usually much cheaper.",
      "Is the lab in my insurance network?",
      "Is the blood draw fee (venipuncture) included, or billed separately?",
      "If my doctor ordered multiple tests, can I see the price for each one?",
      "Does my insurance require I use a specific lab for in-network coverage?"
    ]
  },
  "CMP (Comprehensive Metabolic Panel)": {
    "description": "A CMP is a blood test that measures 14 things in your blood, including kidney and liver function, blood sugar, and electrolytes. Doctors use it as a general health check or to monitor conditions like diabetes and high blood pressure.",
    "typically_included": [
      "Drawing the blood sample",
      "All 14 lab tests in the panel",
      "A report sent to your doctor"
    ],
    "billed_separately": [
      "Office visit if drawn during a doctor's appointment",
      "Other tests ordered at the same time",
      "Hospital outpatient facility fee if drawn at a hospital"
    ],
    "what_to_expect": "A quick blood draw from your arm. You may be asked to fast beforehand for the most accurate glucose reading. The draw itself takes a few minutes.",
    "questions_to_ask": [
      "Is the blood drawn at a hospital lab or a freestanding lab? Freestanding is usually much cheaper.",
      "Is the lab in my insurance network?",
      "Is the venipuncture (blood draw) fee included or separate?",
      "If multiple tests are ordered together, can I see the price per test?",
      "Does my insurance require a specific lab for in-network pricing?"
    ]
  },
  "CT Abdomen & Pelvis": {
    "description": "A CT scan of the abdomen and pelvis takes detailed cross-section pictures of your belly and hip area organs, including your liver, kidneys, intestines, and bladder. Doctors order this to investigate pain, kidney stones, possible appendicitis, or to check for other abdominal issues.",
    "typically_included": [
      "Use of the CT scanner",
      "The scan images",
      "Radiologist interpretation and report"
    ],
    "billed_separately": [
      "Facility fee (usually higher at a hospital than a freestanding imaging center)",
      "Contrast dye — most abdomen/pelvis scans use contrast, which you may get by IV, by drinking it, or both",
      "The contrast dye itself as a separate line item",
      "Your doctor's follow-up visit"
    ],
    "what_to_expect": "You may need to fast for a few hours and drink contrast fluid before the scan. The scan itself is quick — about 10-15 minutes. If IV contrast is used, you might feel a warm flush briefly.",
    "questions_to_ask": [
      "Can I have this done at a freestanding imaging center rather than a hospital outpatient department?",
      "Will both oral and IV contrast be used, and are they billed separately?",
      "How much is the facility fee?",
      "Is the radiologist in my insurance network?",
      "Can I get a Good Faith Estimate that includes contrast and facility fees before I schedule?"
    ]
  },
  "CT Head": {
    "description": "A CT scan of the head uses X-rays to create cross-section images of your brain and skull. Doctors often order it after a head injury, stroke symptoms, or severe headaches because it's faster than an MRI and good at spotting bleeding or fractures.",
    "typically_included": [
      "Use of the CT scanner",
      "The scan images",
      "Radiologist interpretation and report"
    ],
    "billed_separately": [
      "Facility fee (usually higher at hospital outpatient than at imaging centers)",
      "Contrast dye if ordered (most head CTs don't use it)",
      "Emergency department visit fee if done in an ER",
      "Your doctor's follow-up visit to discuss results"
    ],
    "what_to_expect": "The scan itself takes only a few minutes. You'll lie on a table that slides through a donut-shaped machine. It's quick, painless, and doesn't feel as enclosed as an MRI.",
    "questions_to_ask": [
      "Can I get this scan at an outpatient imaging center instead of a hospital or ER? The price difference can be large.",
      "Is a facility fee charged, and how much?",
      "Is the radiologist in my network?",
      "Is contrast needed? What does it cost if yes?",
      "Can I get a written Good Faith Estimate before the scan?"
    ]
  },
  "Chest X-ray": {
    "description": "A chest X-ray uses a small amount of radiation to take pictures of your lungs, heart, ribs, and the bones in your chest. It's one of the most common imaging tests and is used to check for pneumonia, broken ribs, heart problems, and many other conditions.",
    "typically_included": [
      "The X-ray images (usually 2 views — front and side)",
      "A radiologist reading the images and writing a report",
      "Use of the X-ray equipment"
    ],
    "billed_separately": [
      "Facility fee if done at a hospital or ER (freestanding imaging centers are usually cheaper)",
      "Your doctor's office visit to order and review the X-ray",
      "Additional views if the radiologist requests more images"
    ],
    "what_to_expect": "The X-ray takes just a few minutes. You'll stand in front of a plate and hold your breath briefly. You'll be asked to remove jewelry and wear a gown. Tell the tech if you might be pregnant.",
    "questions_to_ask": [
      "Can I have this done at a freestanding imaging center rather than a hospital?",
      "Will there be a separate reading fee by the radiologist? Is the radiologist in my insurance network?",
      "Is a facility fee added to the price?",
      "What's the total estimated cost including reading fees?",
      "If this is for an urgent issue, is urgent care cheaper than the ER?"
    ]
  },
  "Colonoscopy": {
    "description": "A colonoscopy is a procedure where a doctor uses a flexible tube with a camera to look inside your large intestine. It's used to screen for colon cancer, find the cause of bleeding or bowel changes, and remove polyps before they can turn cancerous.",
    "typically_included": [
      "The procedure performed by a gastroenterologist",
      "Use of the endoscopy suite and equipment",
      "Basic observation during recovery"
    ],
    "billed_separately": [
      "Anesthesia and the anesthesiologist — often a large separate bill",
      "Pathology fees if polyps or biopsies are sent to a lab",
      "Facility fee (a hospital outpatient department usually costs far more than an ambulatory surgery center)",
      "Prep medications (you pay for the bowel-cleansing prep separately)",
      "Follow-up visits to discuss results"
    ],
    "what_to_expect": "You'll spend the day before on a clear liquid diet and drink a strong laxative to clean out your colon. The procedure itself takes 30-60 minutes under sedation and you won't remember it. Plan to rest the rest of the day and have someone drive you home.",
    "questions_to_ask": [
      "Can this be done at an ambulatory surgery center instead of a hospital? The price difference is often thousands of dollars.",
      "Is the anesthesiologist in my insurance network? (This is a top source of surprise bills.)",
      "If polyps are found and sent to pathology, is that a separate bill? Is the lab in-network?",
      "Is this billed as screening (usually fully covered by insurance) or diagnostic (subject to copays and deductibles)?",
      "Can I get a Good Faith Estimate that includes the facility, doctor, anesthesia, and pathology fees?"
    ]
  },
  "Echocardiogram": {
    "description": "An echocardiogram — often just called an 'echo' — uses sound waves to create moving pictures of your heart. Doctors order it to check how well your heart is pumping, look at the valves, and detect many heart conditions.",
    "typically_included": [
      "Use of the ultrasound equipment",
      "The scan performed by a sonographer",
      "A cardiologist's interpretation and report"
    ],
    "billed_separately": [
      "Cardiologist's interpretation fee (may be a separate line item)",
      "Facility fee at hospital-based centers",
      "Stress echo add-on if your doctor orders one",
      "Your cardiologist's office visit"
    ],
    "what_to_expect": "You'll lie on your side while a technician moves a small device across your chest with gel. The scan takes 30-60 minutes and is painless. You may be asked to hold your breath briefly at times.",
    "questions_to_ask": [
      "Can this be done at a freestanding cardiology imaging center rather than a hospital outpatient department?",
      "Is the cardiologist who reads the study in my insurance network?",
      "Is the interpretation fee included in the quoted price?",
      "Is a stress echo being ordered, or just a resting echo? Stress echoes cost more.",
      "Can I get a Good Faith Estimate including all fees before scheduling?"
    ]
  },
  "HbA1c (Diabetes Test)": {
    "description": "An HbA1c test measures your average blood sugar over the past 2-3 months. It's the main test used to diagnose diabetes and monitor how well diabetes treatment is working.",
    "typically_included": [
      "The blood draw",
      "The lab test",
      "A report sent to your doctor"
    ],
    "billed_separately": [
      "Office visit if the blood draw happens during a doctor's appointment",
      "Other tests ordered at the same time",
      "Hospital outpatient facility fee if drawn at a hospital lab"
    ],
    "what_to_expect": "A quick blood draw from your arm — a few minutes total. No fasting is needed for this test. Some clinics can run it from a finger prick instead.",
    "questions_to_ask": [
      "Is this being drawn at a hospital lab or a freestanding lab? Freestanding is almost always cheaper.",
      "Is the lab in my insurance network?",
      "For people with a diabetes diagnosis, this test is often covered as diagnostic monitoring. Is my insurance covering it fully or subject to copay?",
      "Is the blood draw fee included in the quoted price?",
      "Can I use a self-pay discount if I'm uninsured?"
    ]
  },
  "Lipid Panel": {
    "description": "A lipid panel is a blood test that measures your cholesterol and triglycerides. Doctors use it to check your risk of heart disease and stroke. It's commonly done as part of a routine physical.",
    "typically_included": [
      "Drawing the blood sample",
      "The lab tests (total cholesterol, HDL, LDL, triglycerides)",
      "A report sent to your doctor"
    ],
    "billed_separately": [
      "Office visit if the blood draw happens during a doctor's appointment",
      "Additional tests ordered at the same time (each billed separately)",
      "Hospital outpatient facility fee if drawn at a hospital lab"
    ],
    "what_to_expect": "A quick blood draw from your arm. You'll usually be asked to fast for 9-12 hours beforehand (no food or drinks except water) for the most accurate results. The draw itself takes a few minutes.",
    "questions_to_ask": [
      "Is this drawn at a hospital outpatient lab or a freestanding lab like Quest or LabCorp? The price difference can be huge.",
      "Is the lab in my insurance network?",
      "Most preventive lipid panels are covered at no cost by insurance. Is this classified as preventive or diagnostic?",
      "Is the blood draw fee included in the quoted price?",
      "Can I get the bill broken down by test if multiple are ordered?"
    ]
  },
  "MRI Brain": {
    "description": "An MRI of the brain uses a powerful magnet and radio waves to create detailed pictures of your brain. Doctors order this to look for causes of headaches, stroke, tumors, multiple sclerosis, or other brain conditions.",
    "typically_included": [
      "Use of the MRI scanner for the scheduled time",
      "The scan images themselves",
      "A radiologist reading the scan and writing a report for your doctor"
    ],
    "billed_separately": [
      "Facility fee if done at a hospital outpatient center (often much higher than a freestanding imaging center)",
      "Contrast dye if your doctor orders the 'with contrast' version",
      "The referring physician's office visit",
      "Your doctor's separate follow-up visit to review results"
    ],
    "what_to_expect": "You'll lie still on a table that slides into the scanner for about 30-60 minutes. No prep is needed for most brain MRIs, but you'll remove metal objects and may need to wear earplugs because the machine is loud. Tell the staff if you're claustrophobic.",
    "questions_to_ask": [
      "Is the scan at a hospital outpatient department or a freestanding imaging center? Freestanding centers are usually much cheaper for the same scan.",
      "Will there be a separate facility fee, and what is it?",
      "Do I need contrast? If so, what's the added cost?",
      "Is the radiologist in my insurance network?",
      "Can I get a written Good Faith Estimate before scheduling?"
    ]
  },
  "MRI Knee": {
    "description": "An MRI of the knee takes detailed pictures of the bones, cartilage, ligaments, and tendons in your knee joint using a strong magnet. Doctors order this to find the cause of knee pain, swelling, or an injury that didn't show up well on an X-ray.",
    "typically_included": [
      "Use of the MRI scanner for the scheduled time",
      "The scan images themselves",
      "A radiologist reading the scan and writing a report"
    ],
    "billed_separately": [
      "Facility fee if the scan is done at a hospital outpatient center",
      "Contrast dye if your doctor orders the scan 'with contrast'",
      "The referring physician's office visit (separate from the scan)"
    ],
    "what_to_expect": "You'll lie still on a table that slides into the scanner for about 30-45 minutes. No prep needed for most knee MRIs, but you'll remove any metal (jewelry, belts). Some people find the noise loud — ask for earplugs.",
    "questions_to_ask": [
      "Is this billed as a hospital outpatient procedure or at a freestanding imaging center? Freestanding centers are usually cheaper.",
      "Will there be a separate facility fee, and how much is it?",
      "Do I need contrast dye? If yes, what does that add to the cost?",
      "Is the radiologist who reads my scan in my insurance network?",
      "Can I get a Good Faith Estimate in writing before scheduling?"
    ]
  },
  "Physical Therapy Evaluation": {
    "description": "A physical therapy evaluation is your first visit with a physical therapist. They'll assess your injury, pain, or movement problem, set goals, and create a treatment plan with exercises and therapies tailored to you.",
    "typically_included": [
      "The PT's time to review your history and examine you",
      "Basic movement and strength testing",
      "A written plan of care with goals and recommended frequency of visits"
    ],
    "billed_separately": [
      "Follow-up treatment visits (billed separately each time)",
      "Modalities like ultrasound, electrical stimulation, or heat packs added during treatment",
      "Specialized testing or equipment use",
      "Home exercise equipment the PT may recommend"
    ],
    "what_to_expect": "The evaluation usually takes 45-60 minutes. Bring any referral, imaging results, and a list of medications. Wear comfortable clothes you can move in. The PT will ask about your injury or problem, watch how you move, and test strength and range of motion.",
    "questions_to_ask": [
      "Is the PT clinic in my insurance network?",
      "How many visits does my insurance authorize, and do I need prior authorization?",
      "What's the cost difference between low-complexity and moderate-complexity evaluations?",
      "Are treatment modalities like ultrasound or electrical stim billed on top of each visit?",
      "If I don't have insurance, do you offer a self-pay cash discount? What's the cash price per visit?"
    ]
  },
  "Screening Mammogram": {
    "description": "A screening mammogram is an X-ray of your breasts used to check for early signs of breast cancer in women who don't have any symptoms. Guidelines generally recommend screening mammograms starting in your 40s or 50s, depending on risk factors.",
    "typically_included": [
      "The mammogram itself (usually 2 views of each breast)",
      "A radiologist reading the images and writing a report",
      "Use of the mammography equipment"
    ],
    "billed_separately": [
      "A follow-up diagnostic mammogram if the screening finds something unclear (this is a different procedure)",
      "Ultrasound or other imaging if the radiologist wants a closer look",
      "Your doctor's visit to discuss results",
      "Facility fee at hospital-based centers"
    ],
    "what_to_expect": "The appointment takes about 20-30 minutes. The technician will position each breast on the machine and press it briefly for clear images — it may feel uncomfortable but is quick. Don't wear deodorant, lotion, or powder on the day of the scan.",
    "questions_to_ask": [
      "Most insurance plans cover screening mammograms at no cost as preventive care. Is mine confirmed as fully covered?",
      "If follow-up imaging is needed, how much will that cost, and will it be billed as diagnostic (not preventive)?",
      "Is the facility in my insurance network?",
      "Is the radiologist reading the scan in my network?",
      "What's the difference in price between a freestanding imaging center and a hospital-based center?"
    ]
  },
  "TSH (Thyroid Test)": {
    "description": "A TSH (thyroid stimulating hormone) test is a blood test that checks how your thyroid gland is working. Doctors order it to diagnose and monitor thyroid problems like hypothyroidism (underactive) and hyperthyroidism (overactive).",
    "typically_included": [
      "The blood draw",
      "The lab test",
      "A report sent to your doctor"
    ],
    "billed_separately": [
      "Office visit if the draw happens at a doctor's appointment",
      "Follow-up thyroid tests (free T3, free T4) if your TSH is abnormal — these are billed separately",
      "Hospital outpatient facility fee if drawn at a hospital"
    ],
    "what_to_expect": "A simple blood draw from your arm, usually taking just a few minutes. No fasting is needed. Take any thyroid medications as prescribed unless your doctor says otherwise.",
    "questions_to_ask": [
      "Is this drawn at a hospital lab or a freestanding lab like Quest or LabCorp? Freestanding labs are usually much cheaper.",
      "Is the lab in my insurance network?",
      "Is the venipuncture fee included in the quoted price?",
      "If my TSH is abnormal and follow-up tests are needed, will those be billed separately?",
      "Can I use a self-pay cash discount if I don't have insurance?"
    ]
  },
  "Ultrasound Abdomen": {
    "description": "An abdominal ultrasound uses sound waves (no radiation) to take pictures of the organs in your belly, including your liver, gallbladder, kidneys, pancreas, and spleen. Doctors order this to look for gallstones, cysts, or causes of abdominal pain.",
    "typically_included": [
      "Use of the ultrasound machine",
      "The scan performed by a trained sonographer",
      "A radiologist reviewing the images and writing a report"
    ],
    "billed_separately": [
      "Facility fee if done at a hospital",
      "Radiologist reading fee (may be a separate charge)",
      "The referring doctor's office visit to order and review the scan"
    ],
    "what_to_expect": "You'll likely be asked to fast for 8-12 hours beforehand for the clearest pictures, especially of the gallbladder. The scan takes about 30-45 minutes. You'll lie down while a technician moves a small handheld device over your belly with warm gel.",
    "questions_to_ask": [
      "Is this done at a hospital outpatient center or a freestanding imaging center? The latter is usually cheaper.",
      "Is the radiologist's interpretation included in the quoted price, or billed separately?",
      "Is the radiologist in my insurance network?",
      "Is there a facility fee?",
      "Can I get a Good Faith Estimate before scheduling?"
    ]
  },
  "Upper GI Endoscopy (EGD)": {
    "description": "An EGD (upper GI endoscopy) is a procedure where a doctor uses a flexible tube with a camera to look at your esophagus, stomach, and the first part of your small intestine. It's used to find causes of heartburn, swallowing problems, abdominal pain, or to check for ulcers and other issues.",
    "typically_included": [
      "The procedure performed by a gastroenterologist",
      "Use of the endoscopy suite and equipment",
      "Basic observation during recovery"
    ],
    "billed_separately": [
      "Anesthesia and anesthesiologist fees (often a separate, sizable bill)",
      "Pathology fees if biopsies are taken and sent to a lab",
      "Facility fee (ambulatory surgery centers cost less than hospital outpatient departments)",
      "Follow-up visits to discuss results"
    ],
    "what_to_expect": "You'll fast for 8+ hours beforehand. The procedure takes 15-30 minutes under sedation, so you won't remember it. You'll need a driver to take you home and should plan to rest the rest of the day.",
    "questions_to_ask": [
      "Can I have this done at an ambulatory surgery center instead of a hospital outpatient department? Price difference is usually significant.",
      "Is the anesthesiologist in my insurance network?",
      "If biopsies are taken, is the pathology lab in-network? What's the cost range?",
      "What's the total estimated bill including doctor, facility, anesthesia, and any biopsy fees?",
      "Can I get a written Good Faith Estimate before the procedure?"
    ]
  }
}
```

- [ ] **Step 2: Verify the JSON is valid and has 16 entries**

```bash
python3 -c "
import json
with open('data/processed/service_explanations.json') as f:
    data = json.load(f)
print(f'Services: {len(data)}')
print(f'Keys: {sorted(data.keys())}')
for name, entry in data.items():
    assert 'description' in entry, f'{name} missing description'
    assert 'typically_included' in entry, f'{name} missing typically_included'
    assert 'billed_separately' in entry, f'{name} missing billed_separately'
    assert 'what_to_expect' in entry, f'{name} missing what_to_expect'
    assert 'questions_to_ask' in entry, f'{name} missing questions_to_ask'
print('All 16 services have all 5 required fields')
"
```

Expected output:
```
Services: 16
Keys: ['CBC (Complete Blood Count)', 'CMP (Comprehensive Metabolic Panel)', 'CT Abdomen & Pelvis', 'CT Head', 'Chest X-ray', 'Colonoscopy', 'Echocardiogram', 'HbA1c (Diabetes Test)', 'Lipid Panel', 'MRI Brain', 'MRI Knee', 'Physical Therapy Evaluation', 'Screening Mammogram', 'TSH (Thyroid Test)', 'Ultrasound Abdomen', 'Upper GI Endoscopy (EGD)']
All 16 services have all 5 required fields
```

- [ ] **Step 3: Commit**

```bash
git add data/processed/service_explanations.json
git commit -m "data: add hand-curated service explanations for all 16 services"
```

---

### Task 3: Integration Test for Committed JSON

**Files:**
- Modify: `tests/test_explanations.py` (append one test)

- [ ] **Step 1: Append the integration test**

Append this test to the end of `tests/test_explanations.py`:

```python
def test_committed_json_has_all_services_with_required_fields():
    """Verify the real committed JSON has an entry for every service in SERVICE_CATALOG."""
    from pathlib import Path
    from app.search import SERVICE_CATALOG

    json_path = Path(__file__).parent.parent / "data" / "processed" / "service_explanations.json"
    if not json_path.exists():
        pytest.skip("service_explanations.json not yet generated")

    explanations = load_explanations(str(json_path))

    missing = []
    for svc in SERVICE_CATALOG:
        name = svc["name"]
        if name not in explanations:
            missing.append(name)
            continue
        entry = explanations[name]
        for field in REQUIRED_FIELDS:
            assert field in entry, f"{name} missing field '{field}'"
        assert isinstance(entry["description"], str), f"{name} description not a string"
        assert isinstance(entry["what_to_expect"], str), f"{name} what_to_expect not a string"
        assert isinstance(entry["typically_included"], list), f"{name} typically_included not a list"
        assert isinstance(entry["billed_separately"], list), f"{name} billed_separately not a list"
        assert isinstance(entry["questions_to_ask"], list), f"{name} questions_to_ask not a list"
        for item in entry["typically_included"]:
            assert isinstance(item, str), f"{name} has non-string in typically_included"
        for item in entry["billed_separately"]:
            assert isinstance(item, str), f"{name} has non-string in billed_separately"
        for item in entry["questions_to_ask"]:
            assert isinstance(item, str), f"{name} has non-string in questions_to_ask"

    assert not missing, f"Missing explanation entries for: {missing}"
```

- [ ] **Step 2: Run the test**

```bash
python3 -m pytest tests/test_explanations.py::test_committed_json_has_all_services_with_required_fields -v
```

Expected: PASS (the committed JSON from Task 2 must have all 16 services with all 5 fields).

- [ ] **Step 3: Run all explanation tests together**

```bash
python3 -m pytest tests/test_explanations.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_explanations.py
git commit -m "test: add integration test for committed service explanations"
```

---

### Task 4: Streamlit UI — Expander Integration

**Files:**
- Modify: `app/streamlit_app.py`

- [ ] **Step 1: Add the explanations import**

Open `app/streamlit_app.py`. Find this existing import block:

```python
import streamlit as st
import pandas as pd
from app.data_loader import load_data, get_providers_for_service, get_statewide_stats
from app.search import search_services, SERVICE_CATALOG
from app.geo import load_zip_coords, filter_by_radius
```

Add an import for explanations right after the geo import:

```python
from app.explanations import load_explanations, get_explanation
```

- [ ] **Step 2: Add the cached explanations helper**

Find the existing `cached_zip_coords` function:

```python
@st.cache_data
def cached_zip_coords():
    return load_zip_coords()
```

Add a new cached function directly after it:

```python
@st.cache_data
def cached_explanations():
    try:
        return load_explanations()
    except FileNotFoundError:
        return {}
```

- [ ] **Step 3: Add the expander block**

In `main()`, find this existing block:

```python
    # Statewide summary
    stats = get_statewide_stats(df, selected_hcpcs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Low (10th percentile)", f"${stats['charge_p10']:,.0f}")
    col2.metric("Typical (median)", f"${stats['charge_median']:,.0f}")
    col3.metric("High (90th percentile)", f"${stats['charge_p90']:,.0f}")
    st.caption("Statewide billed charges — Indiana providers, Medicare data 2023")

    st.divider()
```

Insert the expander block between the caption and the divider. The updated block should be:

```python
    # Statewide summary
    stats = get_statewide_stats(df, selected_hcpcs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Low (10th percentile)", f"${stats['charge_p10']:,.0f}")
    col2.metric("Typical (median)", f"${stats['charge_median']:,.0f}")
    col3.metric("High (90th percentile)", f"${stats['charge_p90']:,.0f}")
    st.caption("Statewide billed charges — Indiana providers, Medicare data 2023")

    # About this service (from pre-generated explanations)
    explanations = cached_explanations()
    explanation = get_explanation(explanations, selected_name)
    if explanation:
        with st.expander("About this service"):
            st.markdown("**What it is**")
            st.markdown(explanation["description"])

            st.markdown("**Typically included**")
            for item in explanation["typically_included"]:
                st.markdown(f"- {item}")

            st.markdown("**May be billed separately**")
            for item in explanation["billed_separately"]:
                st.markdown(f"- {item}")

            st.markdown("**What to expect**")
            st.markdown(explanation["what_to_expect"])

            st.markdown("**Questions to ask before scheduling**")
            for q in explanation["questions_to_ask"]:
                st.markdown(f"- {q}")

    st.divider()
```

- [ ] **Step 4: Syntax check**

```bash
python3 -c "import ast; ast.parse(open('app/streamlit_app.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

- [ ] **Step 5: Run all tests to confirm nothing regressed**

```bash
python3 -m pytest tests/ -q
```

Expected: all tests PASS (should now be 36: 5 build_dataset + 4 data_loader + 14 search + 8 geo + 5 explanations).

- [ ] **Step 6: Commit**

```bash
git add app/streamlit_app.py
git commit -m "feat: add About this service expander to UI"
```

---

### Task 5: Smoke Test and Push

**Files:** None modified — verification only.

- [ ] **Step 1: Launch the app locally**

```bash
pkill -f "streamlit run" || true
python3 -m streamlit run app/streamlit_app.py
```

Expected: App launches at `http://localhost:8501`.

- [ ] **Step 2: Manual verification**

In the browser, verify:

1. Select "MRI Knee" — expander "About this service" appears between the price stats and the provider table
2. Click the expander — 5 sections render (What it is, Typically included, May be billed separately, What to expect, Questions to ask before scheduling)
3. Content reads naturally, no JSON leakage, no medical jargon
4. Switch to "HbA1c (Diabetes Test)" — different explanation appears and is specific to HbA1c
5. Switch through these additional services, verifying each shows distinct content: Colonoscopy, Chest X-ray, Echocardiogram, Upper GI Endoscopy (EGD), Lipid Panel, Physical Therapy Evaluation
6. Click to collapse the expander — clean collapse
7. Provider table, radius filter, sort dropdown, and caveats footer still work unchanged
8. Enter ZIP `46202` + 25 miles — radius filter still works, expander still visible

- [ ] **Step 3: Stop Streamlit**

Press `Ctrl+C` in the terminal running the app.

- [ ] **Step 4: Push to GitHub**

```bash
git push
```

Expected: 4 new commits pushed to `main`. Streamlit Cloud auto-redeploys.

- [ ] **Step 5: Verify the deployed app**

Open the Streamlit Cloud URL. Select any service and verify the "About this service" expander appears and renders correctly on both desktop and mobile (if possible).

---

"""
Hardcoded FEMA Disaster Aid Form 009-0-3 template.
Each field maps to an exact position on the PDF.
"""

FEMA_TEMPLATE = {
    "template_id": "fema_009_0_3",
    "title": "FEMA Disaster Aid Form",
    "subtitle": "Form 009-0-3",
    "agency": "FEMA",
    "description": (
        "The FEMA Disaster Aid application is used to apply for Individual "
        "Assistance including housing assistance and other disaster-related needs. "
        "Complete all applicable fields."
    ),
    "fields": [
        {
            "id": 1,
            "field_name": "applicant_name",
            "prompt": "What is your full legal name?",
            "type": "text",
            "sensitive": False,
            "pdf_coordinates": {"page": 1, "x": 80, "y": 680, "width": 200},
            "audio_file": "q1_name.mp3",
        },
        {
            "id": 2,
            "field_name": "date_of_birth",
            "prompt": "What is your date of birth?",
            "type": "date",
            "sensitive": False,
            "pdf_coordinates": {"page": 1, "x": 80, "y": 640, "width": 200},
            "audio_file": "q2_dob.mp3",
        },
        {
            "id": 3,
            "field_name": "ssn",
            "prompt": "What is your Social Security Number?",
            "type": "ssn",
            "sensitive": True,
            "pdf_coordinates": {"page": 1, "x": 80, "y": 600, "width": 200},
            "audio_file": "q3_ssn.mp3",
        },
        {
            "id": 4,
            "field_name": "mailing_address",
            "prompt": "What is your current mailing address?",
            "type": "address",
            "sensitive": False,
            "pdf_coordinates": {"page": 1, "x": 80, "y": 560, "width": 400},
            "audio_file": "q4_address.mp3",
        },
        {
            "id": 5,
            "field_name": "phone_number",
            "prompt": "What is your phone number?",
            "type": "phone",
            "sensitive": False,
            "pdf_coordinates": {"page": 1, "x": 80, "y": 520, "width": 200},
            "audio_file": "q5_phone.mp3",
        },
        {
            "id": 6,
            "field_name": "disaster_type",
            "prompt": "What type of disaster affected you?",
            "type": "text",
            "sensitive": False,
            "pdf_coordinates": {"page": 1, "x": 80, "y": 480, "width": 200},
            "audio_file": "q6_disaster.mp3",
        },
        {
            "id": 7,
            "field_name": "damaged_property_address",
            "prompt": "What is the address of the damaged property?",
            "type": "address",
            "sensitive": False,
            "pdf_coordinates": {"page": 1, "x": 80, "y": 440, "width": 400},
            "audio_file": "q7_property.mp3",
        },
        {
            "id": 8,
            "field_name": "has_insurance",
            "prompt": "Do you have insurance coverage for the damaged property?",
            "type": "yes_no",
            "sensitive": False,
            "pdf_coordinates": {"page": 1, "x": 80, "y": 400, "width": 100},
            "audio_file": "q8_insurance.mp3",
        },
    ],
}


def get_template(template_id: str) -> dict | None:
    """Look up a form template by ID. Only FEMA is available for MVP."""
    if template_id == "fema_009_0_3":
        return FEMA_TEMPLATE
    return None


def get_field(template_id: str, field_index: int) -> dict | None:
    """Get a specific field from a template by index."""
    template = get_template(template_id)
    if template and 0 <= field_index < len(template["fields"]):
        return template["fields"][field_index]
    return None


def get_total_fields(template_id: str) -> int:
    """Return the total number of fields in a template."""
    template = get_template(template_id)
    return len(template["fields"]) if template else 0

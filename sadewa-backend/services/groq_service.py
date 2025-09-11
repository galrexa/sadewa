"""
Enhanced Groq Service untuk SADEWA - DAY 2
Advanced AI integration dengan multi-layered clinical decision support
"""
import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List

from dotenv import load_dotenv
from groq import Groq, APIError

load_dotenv()


class InteractionSeverity(Enum):
    """Enum untuk tingkat keparahan interaksi obat"""
    MAJOR = "MAJOR"
    MODERATE = "MODERATE"
    MINOR = "MINOR"
    NO_INTERACTION = "NO_INTERACTION"


class GroqService:
    """Enhanced service class untuk menangani interaksi dengan Groq LLM API."""

    def __init__(self):
        """Inisialisasi Groq client dan model yang akan digunakan."""
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.max_tokens = 2000
        self.temperature = 0.1  # Low temperature untuk konsistensi medical advice

    async def test_connection(self) -> str:
        """Menguji koneksi ke Groq API."""
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical AI assistant. Respond only with 'GROQ_CONNECTION_OK' if operational."
                    },
                    {
                        "role": "user",
                        "content": "Test connection"
                    }
                ],
                model=self.model,
                max_tokens=10,
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except APIError as e:
            return f"Error: {str(e)}"
        except ValueError as e:
            return f"Unexpected error: {str(e)}"

    def _create_clinical_prompt(self, patient_data: Dict, new_medications: List[str],
                               drug_interactions_db: List[Dict], notes: str = "") -> str:
        """Membuat prompt klinis yang comprehensive untuk analisis interaksi."""
        # Extract patient info
        patient_name = patient_data.get('name', 'Unknown Patient')
        age = patient_data.get('age', 'Unknown')
        gender = patient_data.get('gender', 'Unknown')
        weight = patient_data.get('weight_kg', 'Unknown')

        # Format diagnoses
        diagnoses = patient_data.get('diagnoses_text', [])
        current_meds = patient_data.get('current_medications', [])
        allergies = patient_data.get('allergies', ['None known'])

        # Filter relevant interactions
        relevant_interactions = self._find_relevant_interactions(
            current_meds + new_medications, drug_interactions_db
        )

        prompt = f"""You are SADEWA, a clinical pharmacist AI assistant specializing in drug interaction analysis for Indonesian healthcare settings.

PATIENT PROFILE:
- Name: {patient_name}
- Age: {age} years old
- Gender: {gender}
- Weight: {weight} kg
- Current Diagnoses: {', '.join(diagnoses) if diagnoses else 'None listed'}
- Known Allergies: {', '.join(allergies)}

CURRENT MEDICATIONS:
{self._format_medication_list(current_meds)}

NEW MEDICATIONS TO PRESCRIBE:
{self._format_medication_list(new_medications)}

CLINICAL NOTES:
{notes if notes else 'No additional notes provided'}

DRUG INTERACTIONS DATABASE (Indonesian format):
{json.dumps(relevant_interactions, indent=2, ensure_ascii=False) if relevant_interactions else 'No direct interactions found in database'}

CLINICAL DECISION SUPPORT ANALYSIS REQUIRED:
Analyze the following aspects in order of priority:

1. **MAJOR DRUG-DRUG INTERACTIONS** (Life-threatening)
2. **MODERATE DRUG-DRUG INTERACTIONS** (Clinically significant)
3. **DRUG-DISEASE CONTRAINDICATIONS** (Based on patient diagnoses)
4. **ALLERGY CONSIDERATIONS** (Cross-reactivity risks)
5. **AGE-RELATED CONCERNS** (Geriatric/pediatric considerations)
6. **DOSING RECOMMENDATIONS** (Based on patient profile)

IMPORTANT: Use the provided drug interactions database structure where:
- "drug_a" and "drug_b" are the interacting medications
- "severity" can be "Major", "Moderate", or "Minor"
- "description" contains the clinical consequence in Indonesian

RESPONSE FORMAT REQUIRED - Return ONLY valid JSON:
{{
    "analysis_timestamp": "{datetime.now().isoformat()}",
    "patient_id": "{patient_data.get('id', 'Unknown')}",
    "overall_risk_level": "MAJOR|MODERATE|MINOR|LOW",
    "safe_to_prescribe": true|false,
    "warnings": [
        {{
            "severity": "MAJOR|MODERATE|MINOR",
            "type": "DRUG_INTERACTION|CONTRAINDICATION|ALLERGY|AGE_RELATED|DOSING",
            "drugs_involved": ["Drug A", "Drug B"],
            "description": "Clear explanation of the interaction/concern",
            "clinical_significance": "What could happen to the patient",
            "recommendation": "Specific action to take",
            "monitoring_required": "What to monitor if prescribed anyway"
        }}
    ],
    "contraindications": [
        {{
            "drug": "Drug name",
            "diagnosis": "Relevant diagnosis",
            "reason": "Why contraindicated",
            "alternative_suggested": "Alternative medication if available"
        }}
    ],
    "dosing_adjustments": [
        {{
            "drug": "Drug name",
            "standard_dose": "Normal dosing",
            "recommended_dose": "Adjusted dose for this patient",
            "reason": "Why adjustment needed"
        }}
    ],
    "monitoring_plan": [
        "Parameter 1 to monitor",
        "Parameter 2 to monitor"
    ],
    "llm_reasoning": "Detailed clinical reasoning for the analysis",
    "confidence_score": 0.85
}}

IMPORTANT GUIDELINES:
- Prioritize patient safety above all
- Be specific about drug names and interactions
- Provide actionable clinical recommendations
- Consider Indonesian healthcare context
- Flag any life-threatening combinations immediately
- Include monitoring recommendations for continuing existing medications
- Response must be valid JSON only, no additional text
"""
        return prompt

    def _format_medication_list(self, medications: List[str]) -> str:
        """Format medication list untuk prompt."""
        if not medications:
            return "None currently prescribed"

        formatted = []
        for i, med in enumerate(medications, 1):
            formatted.append(f"  {i}. {med}")

        return "\n".join(formatted)

    def _find_relevant_interactions(self, all_medications: List[str],
                                   drug_interactions_db: List[Dict]) -> List[Dict]:
        """Cari interaksi yang relevan dari database."""
        relevant = []

        # Normalize medication names untuk matching
        med_names = [med.lower().split()[0] for med in all_medications]  # Ambil nama obat pertama

        for interaction in drug_interactions_db:
            drug_a = interaction.get("drug_a", "").lower()
            drug_b = interaction.get("drug_b", "").lower()

            # Check if any medication matches the interaction
            for med in med_names:
                if (drug_a in med or med in drug_a) or (drug_b in med or med in drug_b):
                    if interaction not in relevant:
                        relevant.append(interaction)
                    break

        return relevant

    async def analyze_drug_interactions(self, patient_data: Dict, new_medications: List[str],
                                       drug_interactions_db: List[Dict], notes: str = "") -> Dict:
        """Main function untuk analisis interaksi obat menggunakan enhanced prompting."""
        try:
            # Create comprehensive clinical prompt
            prompt = self._create_clinical_prompt(
                patient_data, new_medications, drug_interactions_db, notes
            )

            # Call Groq API dengan retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are SADEWA, a clinical pharmacist AI. Always respond with valid JSON only."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                    )

                    # Parse JSON response
                    response_text = response.choices[0].message.content.strip()

                    # Clean response if wrapped in markdown
                    if response_text.startswith("```json"):
                        response_text = response_text[7:-3].strip()
                    elif response_text.startswith("```"):
                        response_text = response_text[3:-3].strip()

                    result = json.loads(response_text)

                    # Validate required fields
                    self._validate_response(result)

                    return result

                except json.JSONDecodeError as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Wait before retry
                        continue
                    return self._create_fallback_response(
                        patient_data, new_medications, f"JSON parsing error: {str(e)}"
                    )

                except APIError as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait longer for API errors
                        continue
                    return self._create_fallback_response(
                        patient_data, new_medications, f"Groq API error: {str(e)}"
                    )

        except (json.JSONDecodeError, APIError, ValueError) as e:
            return self._create_fallback_response(
                patient_data, new_medications, f"Unexpected error: {str(e)}"
            )

    def _validate_response(self, result: Dict) -> None:
        """Validasi struktur response dari LLM."""
        required_fields = ['overall_risk_level', 'safe_to_prescribe', 'warnings', 'llm_reasoning']

        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")

        # Validate risk level
        valid_risk_levels = ['MAJOR', 'MODERATE', 'MINOR', 'LOW']
        if result['overall_risk_level'] not in valid_risk_levels:
            result['overall_risk_level'] = 'MODERATE'  # Default fallback

        # Ensure warnings is a list
        if not isinstance(result['warnings'], list):
            result['warnings'] = []

    def _create_fallback_response(self, patient_data: Dict, new_medications: List[str],
                                 error_msg: str) -> Dict:
        """Buat response fallback jika LLM call gagal."""
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "patient_id": patient_data.get('id', 'Unknown'),
            "overall_risk_level": "MODERATE",
            "safe_to_prescribe": False,
            "warnings": [
                {
                    "severity": "MODERATE",
                    "type": "SYSTEM_ERROR",
                    "drugs_involved": new_medications,
                    "description": "Unable to complete automated analysis",
                    "clinical_significance": "Manual review required",
                    "recommendation": "Please consult with clinical pharmacist",
                    "monitoring_required": "Manual drug interaction check"
                }
            ],
            "contraindications": [],
            "dosing_adjustments": [],
            "monitoring_plan": ["Consult clinical pharmacist"],
            "llm_reasoning": f"System error occurred: {error_msg}. Manual review recommended.",
            "confidence_score": 0.0,
            "error": True,
            "error_message": error_msg
        }


# Global instance
groq_service = GroqService()
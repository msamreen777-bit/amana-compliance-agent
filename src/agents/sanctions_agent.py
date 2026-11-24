from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.config import settings
from src.state import ComplianceState

llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name=settings.GROQ_MODEL,
    temperature=0.0
)

SANCTIONS_PROMPT = ChatPromptTemplate.from_template("""
You are a Financial Intelligence Sanctions & PEP Specialist for the UAE FIU / DIFC framework.

SCREENING SUBJECT:
- Entity / Individual: {entity_name}
- Jurisdiction: {country}
- Dossier Information: {dossier}

TASK:
1. Determine if there is any indication of Politically Exposed Persons (PEPs) or association with PEPs.
2. Check if the jurisdiction is a FATF high-risk jurisdiction (e.g., sanctioned countries, enhanced due diligence lists).
3. Flag any suspicious patterns such as circular ownership or nominee directors.

Summarize your findings clearly and specify whether PEP or Sanctions risk is DETECTED or NOT_DETECTED.
""")

def sanctions_screener_node(state: ComplianceState) -> dict:
    """Screens subject for Sanctions, PEP, and FATF jurisdiction alerts."""
    chain = SANCTIONS_PROMPT | llm
    response = chain.invoke({
        "entity_name": state["entity_name"],
        "country": state["country_of_origin"],
        "dossier": state["raw_dossier_text"]
    })
    
    finding = f"[SANCTIONS & PEP SCREENING]: {response.content.strip()}"
    return {
        "sanctions_findings": [finding],
        "audit_trail": ["Sanctions & PEP intelligence scan completed."]
    }

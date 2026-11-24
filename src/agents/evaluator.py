import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.config import settings
from src.state import ComplianceState
from src.schemas import ComplianceAuditReport

# Set up strict Pydantic parser
parser = PydanticOutputParser(pydantic_object=ComplianceAuditReport)

llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name=settings.GROQ_MODEL,
    temperature=0.0
)

EVALUATOR_PROMPT = ChatPromptTemplate.from_template("""
You are the Chief Compliance Officer issuing the final binding audit verdict under UAE regulatory standards (DIFC / CBUAE).

TRANSACTION DETAILS:
- Entity: {entity_name}
- Country: {country}
- Amount (USD): ${amount}

EVIDENCE ACCUMULATED:
Regulatory Findings:
{regulatory_findings}

Sanctions & PEP Findings:
{sanctions_findings}

Human Analyst Feedback (if any):
{human_feedback}

SCORING POLICY:
- Risk Score between 0.0 and 100.0.
- If PEP found without senior management approval, risk score >= 65.
- If FATF High Risk jurisdiction, risk score >= 75.
- If direct Sanctions hit or illegal shell company structure, risk score >= 90 (overall_verdict: REJECTED).
- If minor discrepancies: risk score 40-75 (overall_verdict: FLAGGED_FOR_MANUAL_REVIEW).
- If Clean: risk score < 40 (overall_verdict: APPROVED).

{format_instructions}

Return ONLY valid JSON matching the schema. No markdown ticks outside the JSON.
""")

def compliance_evaluator_node(state: ComplianceState) -> dict:
    """Synthesizes all findings into a typed Pydantic audit report."""
    prompt_text = EVALUATOR_PROMPT.format_prompt(
        entity_name=state["entity_name"],
        country=state["country_of_origin"],
        amount=state["transaction_amount_usd"],
        regulatory_findings="\n".join(state.get("regulatory_findings", [])),
        sanctions_findings="\n".join(state.get("sanctions_findings", [])),
        human_feedback=state.get("human_analyst_feedback") or "None provided",
        format_instructions=parser.get_format_instructions()
    )
    
    raw_response = llm.invoke(prompt_text.to_messages())
    
    # Clean possible markdown wrapping
    content = raw_response.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    try:
        report = parser.parse(content)
    except Exception:
        # Fallback parsing in case of minor JSON formatting variation
        data = json.loads(content)
        report = ComplianceAuditReport(**data)
        
    needs_human = report.risk_score >= 60.0 and state.get("human_analyst_feedback") is None
    
    return {
        "final_report": report,
        "risk_score": report.risk_score,
        "requires_human_review": needs_human,
        "audit_trail": [f"Risk Evaluator generated verdict: {report.overall_verdict} (Risk Score: {report.risk_score})"]
    }

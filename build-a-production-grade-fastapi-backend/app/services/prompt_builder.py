def build_executive_summary_prompt(project_id: str, risk_data: dict, compliance_data: dict) -> str:
    return f"""
    You are an expert Chief Risk Officer (CRO) evaluating project {project_id}.
    Based on the following data:
    Risk Exposure: {risk_data}
    Compliance Flags: {compliance_data}
    
    Provide a highly professional executive summary, followed by a JSON array of strategic optimization actions.
    """

def build_waiver_prompt(flag_details: dict) -> str:
    return f"""
    You are an expert Legal & Compliance Strategist.
    We have a compliance violation: {flag_details}
    
    Generate a compelling waiver strategy, including a strong justification and a compensating control that mitigates the risk.
    """
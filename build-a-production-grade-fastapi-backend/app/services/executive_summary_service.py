def generate_summary_and_actions(severity_level: str, total_exposure: float):
    # Future integration: LLM API calls go here
    if severity_level == "CRITICAL":
        return (
            "CRITICAL SOVEREIGN RISK DETECTED: Immediate action required. Board-level escalation recommended.",
            ["Restructure supply chain immediately", "Replace imported mandatory items with local alternatives"]
        )
    elif severity_level == "HIGH":
        return (
            "HIGH RISK: Significant financial exposure. Procurement strategy needs revision.",
            ["Negotiate with local vendors", "Optimize RHQ compliance"]
        )
    elif severity_level == "MODERATE":
        return (
            "MODERATE RISK: Exposure within manageable limits but requires monitoring.",
            ["Plan phased localization for items", "Audit payroll leakage"]
        )
    else:
        return (
            "LOW RISK: Compliant and highly competitive. Optimal state for tender submission.",
            ["Maintain current sourcing strategy", "Proceed with bid preparation"]
        )
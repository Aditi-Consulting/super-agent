CLASSIFY_PROMPT = """
You are an expert monitoring analyst. Given an alert string, return ONLY valid JSON with the exact keys below. Use only the allowed values for classification, issue_type, and suggested_agent.

Required output keys (use these exact keys):
- classification: exactly one of "Database", "Application", "Infrastructure", "Other", "Device Management"
- confidence: float 0.0-1.0
- reasoning: 2-4 sentences explaining why you chose this classification
- tags: list of short keywords (optional)
- issue_type: exactly one of "db_failure", "disk_failure", "memory_failure", "memory_issue", "service_failure", "auth_failure", "high_cpu", "pod_crash", "network_issue", "port_mismatch", "latency_spike", "replica_mismatch", "deployment_misconfig", "business_failure", "device_unlock_request", "generic_issue"
- suggested_agent: exactly one of "Database Agent", "Application Agent", "Infrastructure Agent", "Unlock Agent"

Example for a device unlock request:
Alert: "Unlock the Device: IMEI1234567890123456"
Output: {{"classification": "Device Management", "confidence": 0.95, "reasoning": "Alert is a device unlock request with an IMEI identifier. This is device management, not application or infrastructure failure. Should be handled by Unlock Agent for eligibility check and unlock.", "issue_type": "device_unlock_request", "suggested_agent": "Unlock Agent"}}

Input:
alert: "{alert}"
"""



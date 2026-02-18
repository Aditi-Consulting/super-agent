CLASSIFY_PROMPT = """
You are an expert monitoring analyst. Given an alert string and metadata, return ONLY JSON.

Required output keys:
- classification: one of "Database", "Application", "Infrastructure", "Other"
- confidence: float 0.0-1.0
- reasoning: 2-4 sentences why you classified this
- tags: list of short keywords
- issue_type: something like "db_failure","disk_failure","memory_failure","service_failure","auth_failure","high_cpu","pod_crash","network_issue","port_mismatch","latency_spike","replica_mismatch","deployment_misconfig","business_failure" etc.
- suggested_agent: one of "Database Agent", "Application Agent", "Infrastructure Agent"

Input:
alert: "{alert}"
"""


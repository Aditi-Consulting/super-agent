import re
import time
from typing import Set
from store.db import fetch_alert_by_id, update_alert_classification
from app.utility.prompts import CLASSIFY_PROMPT
from app.utility.llm import call_llm_for_json

INFRA_KEYWORDS: Set[str] = {
    "k8s","kubernetes","pod","deployment","replicaset","replica set",
    "ingress","namespace","node",
    "loadbalancer","load balancer","daemonset","statefulset",
    "crashloopbackoff","imagepullbackoff","oomkilled","evicted",
    "pod unreachable","restart count","readiness probe","liveness probe",
    "autoscaler","scaling","hpa","desired replicas","old replicasets",
    "network error","dns error","connection refused","timeout connecting",
    "incorrect port","wrong port","port mismatch",
    "cpu usage","memory usage"
}

APP_KEYWORDS: Set[str] = {
    "application error","runtime error","code exception",
    "business logic","logic failure",
    "http 500","5xx","4xx","bad gateway","gateway timeout",
    "api failure","endpoint failed","handler error",
    "authentication failed","authorization failed",
    "application config","invalid config",
    "payment failed","order failed"
}

AGENT_MAP = {
    "Application": "Application Agent",
    "Infrastructure": "Infrastructure Agent",
    "Database": "Database Agent",
    "Other": "Application Agent",
    "Device Management": "Unlock Agent",
}

VALID_AGENTS = {
    "Application Agent",
    "Infrastructure Agent",
    "Database Agent",
    "Unlock Agent",
}

# Issue type to category mapping (deterministic)
ISSUE_TYPE_TO_CATEGORY = {
    # Database
    "db_failure": "Database",

    # Infrastructure
    "memory_issue": "Infrastructure",
    "memory_failure": "Infrastructure",
    "disk_failure": "Infrastructure",
    "high_cpu": "Infrastructure",
    "network_issue": "Infrastructure",
    "port_mismatch": "Infrastructure",
    "pod_crash": "Infrastructure",
    "latency_spike": "Infrastructure",
    "replica_mismatch": "Infrastructure",
    "deployment_misconfig": "Infrastructure",

    # Application
    "auth_failure": "Application",
    "service_failure": "Application",
    "business_failure": "Application",

    # Device Management
    "device_unlock_request": "Device Management",
}

VALID_CLASSIFICATIONS = {
    "Database",
    "Application",
    "Infrastructure",
    "Other",
    "Device Management",
}

VALID_ISSUE_TYPES = {
    "db_failure", "disk_failure", "memory_failure", "memory_issue",
    "service_failure", "auth_failure", "high_cpu", "pod_crash",
    "network_issue", "port_mismatch", "latency_spike", "replica_mismatch",
    "deployment_misconfig", "business_failure", "device_unlock_request",
    "generic_issue",
}

def _normalize(text: str) -> str:
    return " ".join((text or "").lower().strip().split())

def _match_sets(text: str):
    t = _normalize(text)
    infra_hit = any(k in t for k in INFRA_KEYWORDS)
    app_hit = any(k in t for k in APP_KEYWORDS)
    return infra_hit, app_hit

def _is_device_unlock_pattern(text: str) -> bool:
    """True only for clear device unlock + IMEI pattern. Narrow override trigger."""
    t = _normalize(text)
    if "unlock" not in t or "device" not in t:
        return False
    # IMEI-like: "imei" followed by digits, or word containing imei + digits (e.g. IMEI1234567890123456)
    if "imei" in t:
        return True
    if re.search(r"imei\s*\d{10,20}", t):
        return True
    return False


def _infer_issue_type(text: str) -> str:
    t = _normalize(text)
    # Device management (narrow: unlock + device + IMEI context)
    if _is_device_unlock_pattern(text):
        return "device_unlock_request"
    # Database failures
    if any(kw in t for kw in ["database", "db"]) and any(err in t for err in ["down", "failure", "connection", "timeout", "unavailable"]):
        return "db_failure"
    # Infrastructure failures
    if "oomkilled" in t or "heap" in t or "memory usage" in t or "out of memory" in t or "jvm" in t:
        return "memory_failure"
    if any(kw in t for kw in ["disk full", "disk space", "no space", "filesystem"]):
        return "disk_failure"
    if "cpu usage" in t: return "high_cpu"
    if "connection refused" in t or "dns error" in t or "network error" in t: return "network_issue"
    if "port mismatch" in t or "wrong port" in t or "incorrect port" in t: return "port_mismatch"
    if "crashloopbackoff" in t or "imagepullbackoff" in t or "pod unreachable" in t: return "pod_crash"
    if "latency" in t and ("service" in t or "network" in t): return "latency_spike"
    if "deployment" in t and "replica" in t: return "replica_mismatch"
    if "deployment" in t: return "deployment_misconfig"
    # Application failures
    if "authentication failed" in t or "authorization failed" in t: return "auth_failure"
    service_api_context = any(kw in t for kw in ["service", "api", "endpoint"])
    service_failure_indicators = [
        "down", "timeout", "unavailable", "failed", "unreachable",
        "exception", "error", "nullpointer", "null pointer", "npe",
    ]
    if service_api_context and any(err in t for err in service_failure_indicators):
        return "service_failure"
    if "payment failed" in t or "order failed" in t: return "business_failure"
    return "generic_issue"

def _sanitize_classification(raw: str, infra_hit: bool, app_hit: bool) -> str:
    r = (raw or "").lower().strip()
    if r.startswith("infra"): return "Infrastructure"
    if r.startswith("app"): return "Application"
    if r.startswith("db") or r.startswith("database"): return "Database"
    if r.startswith("other"): return "Other"
    if "device" in r and "management" in r: return "Device Management"

    if infra_hit and not app_hit: return "Infrastructure"
    if app_hit and not infra_hit: return "Application"

    # Conflict (both): allow valid LLM output; only fallback if invalid/empty
    if infra_hit and app_hit:
        if r in {"infrastructure", "application", "database", "other", "device management"}:
            if r == "infrastructure": return "Infrastructure"
            if r == "device management": return "Device Management"
            return r.capitalize()
        # neutral fallback
        return "Application"

    # Neither set hit
    infra_tokens = ("crashloopbackoff", "oomkilled", "pod", "node", "port", "network error", "connection refused")
    if any(tok in r for tok in infra_tokens): return "Infrastructure"
    return "Application"


def _normalize_llm_classification(value: str) -> str:
    """Map LLM classification to allowed enum."""
    if not value:
        return "Other"
    v = (value or "").strip()
    lower = v.lower()
    for valid in VALID_CLASSIFICATIONS:
        if valid.lower() == lower:
            return valid
    if "device" in lower and "management" in lower:
        return "Device Management"
    if lower.startswith("infra"): return "Infrastructure"
    if lower.startswith("app"): return "Application"
    if lower.startswith("db"): return "Database"
    return "Other"


def _normalize_llm_issue_type(value: str) -> str:
    """Map LLM issue_type to allowed enum."""
    if not value:
        return "generic_issue"
    v = (value or "").strip().lower().replace(" ", "_")
    if v in VALID_ISSUE_TYPES:
        return v
    if "device_unlock" in v or "device_unlock_request" in v:
        return "device_unlock_request"
    if "auth" in v: return "auth_failure"
    if "db_" in v or "database" in v: return "db_failure"
    if "memory" in v: return "memory_failure" if "failure" in v else "memory_issue"
    if "disk" in v: return "disk_failure"
    if "cpu" in v: return "high_cpu"
    if "network" in v: return "network_issue"
    if "port" in v: return "port_mismatch"
    if "pod" in v or "crash" in v: return "pod_crash"
    if "latency" in v: return "latency_spike"
    if "replica" in v: return "replica_mismatch"
    if "deployment" in v: return "deployment_misconfig"
    if "service" in v: return "service_failure"
    if "business" in v: return "business_failure"
    return "generic_issue"

def classify_node(state):
    alert_id = state.get("alert_id")
    if not alert_id:
        state["error"] = "No alert_id provided"
        return state

    row = fetch_alert_by_id(alert_id)
    if not row:
        state["error"] = "Alert not found"
        return state

    raw_text = row.get("ticket") or ""
    norm_text = _normalize(raw_text)
    infra_hit, app_hit = _match_sets(raw_text)

    deterministic = False
    conflict = False
    locked = None

    if infra_hit ^ app_hit:
        deterministic = True
        locked = "Infrastructure" if infra_hit else "Application"

    if infra_hit and app_hit:
        conflict = True  # letting LLM decide

    if "latency" in norm_text and (("service" in norm_text) or ("network" in norm_text)) and not app_hit:
        deterministic = True
        locked = "Infrastructure"

    prompt = CLASSIFY_PROMPT.format(alert=raw_text.replace('"', '\\"'))
    llm_json = call_llm_for_json(prompt)

    # Infer issue type first
    issue_type = _infer_issue_type(raw_text)

    # Check if issue type has deterministic category mapping
    if issue_type in ISSUE_TYPE_TO_CATEGORY:
        final = ISSUE_TYPE_TO_CATEGORY[issue_type]
        confidence = 0.95
        reasoning = f"Issue type '{issue_type}' deterministically belongs to {final} category."
        deterministic = True
        locked = final

        # Get LLM reasoning if available (but ignore classification)
        if "__error__" not in llm_json:
            llm_reasoning = llm_json.get("reasoning", "")
            if llm_reasoning:
                reasoning = llm_reasoning

        suggested_agent = None
    elif "__error__" in llm_json:
        if deterministic and locked:
            final = locked
            confidence = 0.9
            reasoning = "Deterministic rule applied; LLM unavailable."
        else:
            final = _sanitize_classification("", infra_hit, app_hit)
            confidence = 0.4
            reasoning = "LLM unavailable; heuristic fallback."
        # issue_type already inferred above
        suggested_agent = None
    else:
        llm_class = _normalize_llm_classification(llm_json.get("classification", ""))
        llm_reasoning = llm_json.get("reasoning", "") or ""
        llm_conf = float(llm_json.get("confidence", 0.7))
        llm_issue = _normalize_llm_issue_type(llm_json.get("issue_type", ""))
        suggested_agent = llm_json.get("suggested_agent")
        if deterministic and locked:
            final = locked
            confidence = max(llm_conf, 0.9)
            reasoning = llm_reasoning if llm_class == final else f"{llm_reasoning} (LLM suggested {llm_class}, rule enforced {final})."
            issue_type = llm_issue or issue_type
        else:
            final = _sanitize_classification(llm_json.get("classification", ""), infra_hit, app_hit)
            confidence = llm_conf
            reasoning = llm_reasoning
            issue_type = llm_issue or issue_type

    # Use validated suggested_agent if present
    if isinstance(suggested_agent, str) and suggested_agent.strip() in VALID_AGENTS:
        agent_name = suggested_agent.strip()
    else:
        agent_name = AGENT_MAP.get(final, "Application Agent")

    # Narrow override: device unlock + IMEI pattern must be consistent (Device Management, device_unlock_request, Unlock Agent)
    if _is_device_unlock_pattern(raw_text):
        if final != "Device Management" or issue_type != "device_unlock_request":
            issue_type = "device_unlock_request"
            final = "Device Management"
            agent_name = "Unlock Agent"
            confidence = max(confidence, 0.95)
            reasoning = (
                "Device unlock request with IMEI; classified as Device Management for Unlock Agent. "
                + (reasoning if reasoning else "Override applied for consistency.")
            )

    update_alert_classification(
        id=row["id"],
        issue_type=issue_type,
        classification=final,
        confidence=confidence,
        reasoning=reasoning,
        agent_name=agent_name,
    )

    state["classified"] = [{
        "ticket_id": row["ticket_id"],
        "classification": final,
        "agent": agent_name,
        "confidence": confidence,
        "deterministic": deterministic,
        "conflict": conflict
    }]
    time.sleep(0.05)
    return state

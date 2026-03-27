"""
Shared constants used across the parser modules.
"""


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Core verbs (high-confidence indicators of a UI action)
CORE_ACTION_VERBS = [
    "click", "select", "navigate", "go to", "type", "enter",
    "open", "choose", "toggle", "enable", "disable", "copy",
    "tap", "press", "drag", "drop", "scroll", "expand", "collapse",
    "check", "uncheck", "fill", "set", "add", "remove", "delete",
    "create", "upload", "download", "sign", "log", "visit", "browse",
    "search", "find", "view", "review", "confirm", "accept", "deny",
    "approve", "merge", "close", "reopen", "assign", "label",
]

# Preamble phrases - the step starts with context *then* contains a core verb
PREAMBLE_PHRASES = [
    "in the", "under", "on the", "from the", "next to", "beside",
    "at the", "use the", "on your", "to the", "near the",
    "optionally,", "if you want",
]

ALL_ACTION_VERBS = CORE_ACTION_VERBS + PREAMBLE_PHRASES

CATEGORY_MAP = {
    "repositories": "repository",
    "get-started": "getting_started",
    "pull-requests": "collaboration",
    "issues": "collaboration",
    "actions": "automation",
    "account-and-profile": "account",
    "authentication": "security",
    "code-security": "security",
    "codespaces": "development_environment",
    "copilot": "automation",
    "desktop": "tooling",
    "education": "education",
    "organizations": "collaboration",
    "pages": "deployment",
    "packages": "deployment",
    "billing": "account",
    "admin": "administration",
    "communities": "collaboration",
    "discussions": "collaboration",
    "projects": "project_management",
    "search-github": "navigation",
}



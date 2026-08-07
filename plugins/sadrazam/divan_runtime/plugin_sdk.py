"""Public Divan Plugin SDK v1 surface.

Third-party plugins are discovered from static manifests and remain out-of-process.
Importing this module never imports third-party plugin code.
"""

from .plugin_approval import (
    ActivationValidation,
    PluginActivation,
    PluginApproval,
    approve_candidate,
    validate_activation,
)
from .plugin_contract import (
    ALLOWED_CAPABILITIES,
    DIVAN_RESERVED_CAPABILITIES,
    MUTATING_CAPABILITIES,
    PLUGIN_API_VERSION,
    PLUGIN_SCHEMA_VERSION,
    ManifestValidation,
    PluginDecision,
    PluginIssue,
    PluginKind,
    PluginManifest,
    PluginTransport,
    validate_manifest_payload,
)
from .plugin_discovery import PluginCandidate, discover_plugins, load_plugin_candidate

__all__ = [
    "ALLOWED_CAPABILITIES",
    "ActivationValidation",
    "DIVAN_RESERVED_CAPABILITIES",
    "MUTATING_CAPABILITIES",
    "ManifestValidation",
    "PLUGIN_API_VERSION",
    "PLUGIN_SCHEMA_VERSION",
    "PluginActivation",
    "PluginApproval",
    "PluginCandidate",
    "PluginDecision",
    "PluginIssue",
    "PluginKind",
    "PluginManifest",
    "PluginTransport",
    "approve_candidate",
    "discover_plugins",
    "load_plugin_candidate",
    "validate_activation",
    "validate_manifest_payload",
]

"""
OpenShift Assisted Installer Log Analyzer.

A standalone tool for analyzing OpenShift Assisted Installer logs.
"""

from .log_analyzer import LogAnalyzer, ClusterAnalyzer
from .signatures import ALL_SIGNATURES, SignatureResult

__version__ = "1.0.0"
__all__ = [
    "LogAnalyzer",
    "ClusterAnalyzer",
    "ALL_SIGNATURES",
    "SignatureResult",
]

"""Core package for BioTime attendance report generation."""

from .engine import generate_report, test_auth

__all__ = ["generate_report", "test_auth"]

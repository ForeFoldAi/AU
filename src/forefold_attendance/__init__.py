"""Core package for AU Infocity - Vendor Attendance & OT Report generation."""

from .engine import generate_report, test_auth

__all__ = ["generate_report", "test_auth"]

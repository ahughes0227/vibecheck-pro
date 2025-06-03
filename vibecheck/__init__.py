"""Core package for the VibeCheck Pro application."""

from . import vc_config
from .flask_server import app

__all__ = [
    "app",
    "vc_config",
]

"""
Team management system for workspace collaboration
"""

from .team_manager import TeamManager
from .team_ui import render_team_dashboard, render_team_management, render_team_settings
from .resource_manager import ResourceManager

__all__ = ['TeamManager', 'ResourceManager', 'render_team_dashboard', 'render_team_management', 'render_team_settings']
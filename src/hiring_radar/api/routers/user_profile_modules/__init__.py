"""Smaller user profile router modules.

The legacy ``user_profile.py`` module still owns the CV/profile mutation heavy
routes for compatibility. New profile route surfaces should be added here first
so the monolith can shrink safely over multiple patches.
"""

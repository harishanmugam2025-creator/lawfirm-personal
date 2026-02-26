"""Shared test configuration.

This file is loaded by pytest before any test module, ensuring
the TESTING flag is set before api.main (and models.database)
are imported.
"""
import os

os.environ["TESTING"] = "true"

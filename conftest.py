"""Pytest bootstrap: put the package root on sys.path and inject DUMMY creds.

Dummy creds let `config` import without exiting; tests mock all HTTP (no network).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("JIRA_BASE_URL", "https://jira.example.com")
os.environ.setdefault("JIRA_PAT", "DUMMY_TEST_TOKEN_DO_NOT_LEAK")
os.environ.setdefault("GITLAB_URL", "https://gitlab.example.com")
os.environ.setdefault("GITLAB_TOKEN", "DUMMY_GITLAB_TOKEN_DO_NOT_LEAK")

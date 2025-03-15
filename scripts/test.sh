#!/usr/bin/env bash

# Run Tests
export PYTHONPATH=src/:$PYTHONPATH
uv run pytest --cov src --cov-branch --cov-report=xml --junitxml=junit.xml -o junit_family=legacy

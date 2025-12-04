#!/bin/bash
pytest --cov=identity --cov=audits --cov=core --cov=trunk --cov=reporting --cov=cedrus --cov-report=html --cov-report=term-missing --cov-fail-under=75

#!/bin/bash
pycodestyle .
python ci/run-pyflakes.py
pylint .


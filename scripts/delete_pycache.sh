#!/usr/bin/env bash

find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf


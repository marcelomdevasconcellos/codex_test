#!/bin/bash
# Run tests with coverage for the entire Django project.
coverage erase
coverage run manage.py test
coverage html
coverage report

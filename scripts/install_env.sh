#!/bin/bash


conda remove -n conduit --all
# Create and activate conda environment
conda create -n conduit python=3.11 -y
conda activate conduit

# Install dependencies
pip install -r requirements_pip.txt

# Install frontend dependencies
# cd src/conduit/frontend/ && npm install

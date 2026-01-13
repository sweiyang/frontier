#!/bin/bash

# Check if conda is installed
if ! command -v conda &> /dev/null
then
    echo "conda could not be found. Please install conda first."
    exit 1
fi

conda remove -n conduit --all
# Create and activate conda environment
conda create -n conduit python=3.12 -y
conda activate conduit

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend/ && npm install

#!/bin/bash

conda activate conduit

# Build frontend
cd src/conduit/frontend/ && npm run build

# Build backend
cd ../../../ && python -m build

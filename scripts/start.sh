#!/bin/bash

sh scripts/build.sh
pip install dist/*.tar.gz

conda activate conduit-test
python example_project/example_agent.py
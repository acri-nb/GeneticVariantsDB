#!/bin/bash

conda activate docker-base
sleep 30 && python3 TFAPI_dwl.py
conda deactivate

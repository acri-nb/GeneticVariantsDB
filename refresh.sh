#!/bin/bash

conda activate base
sleep 15 && python3 TFAPI_dwl.py
conda deactivate

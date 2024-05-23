# README.md

## Introduction

This project contains a series of Python scripts and a shell script to download, process, insert, and visualize genetic variant data. These scripts are designed to work together to maintain and analyze the `HD827` and `EXOME` databases.

## Prerequisites

- Python 3.6 or later
- Anaconda
- MySQL
- Python Modules: `glob`, `subprocess`, `time`, `datetime`, `csv`, `requests`, `urllib3`, `sys`, `mysql.connector`, `os`, `re`, `numpy`, `pandas`, `vcf`, `json`, `io`, `ast`, `dash`, `dash_auth`, `plotly`, `statistics`

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/acri-nb/GeneticVariantsDB.git
   cd GeneticVariantsDB
   ```

2. **Set up the conda environment:**
   ```sh
   conda create --name bioinfo_env python=3.8
   conda activate bioinfo_env
   pip install -r requirements.txt
   ```

3. **Set up MySQL:**
   - Create the `HD827` and `EXOME` databases.
   - Update the credentials in `InitVarDB827.py` and `InitExomeDB_nbirdt.py`.

## Usage

### Step 1: Initialize the Databases

Before starting to download and insert data, it is necessary to initialize the databases.

1. **Initialize the HD827 database:**
   ```sh
   python InitVarDB827.py
   ```

2. **Initialize the EXOME database:**
   ```sh
   python InitExomeDB_nbirdt.py
   ```

### Step 2: Download and Process Data

The `refresh.sh` script will automate the process of downloading and processing data.

1. **Run the download and process script:**
   ```sh
   ./refresh.sh
   ```

### Step 3: Visualize the Data

Once the data is inserted into the databases, use the `stds_dash_sql.HD827.py` script to launch an interactive web interface to visualize the data.

1. **Run the Dash application:**
   ```sh
   python stds_dash_sql.HD827.py
   ```

2. **Access the web interface:**
   - Open your browser and go to `http://localhost:8050`.

## File Descriptions

1. **refresh.sh**
   - Shell script to automate activating the conda environment, running the `TFAPI_dwl827.py` script, and deactivating the environment.

2. **TFAPI_dwl827.py**
   - Downloads genetic variant data from an API, decompresses it, and calls `Add2VarDB827.py` to insert the data into the `HD827` database.

3. **InitVarDB827.py**
   - Reinitializes the `HD827` database by creating the necessary tables to store genetic variant data.

4. **InitExomeDB_nbirdt.py**
   - Reinitializes the `EXOME` database by creating the necessary tables to store exome data.

5. **Add2VarDB827.py**
   - Fixes errors in the VCF file headers, reads the data, and inserts it into the `HD827` database.

6. **stds_dash_sql.HD827.py**
   - Creates an interactive web interface using Dash to visualize and analyze the data from the `HD827` database.

## Database Structure

The databases contain several tables to organize genetic variant data, including `CallData`, `VarData`, `RunInfo`, and other metadata tables.

## Authors

- **Eric Allain** - Script Author
- **Hadrien Gayap** - Editor
- **ACRI (Atlantic Cancer Research Institute)** - Organization

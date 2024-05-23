# README.md

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
   - **Description**: This shell script automates the process of activating the conda environment, executing the `TFAPI_dwl827.py` script to download and process genetic variant data, and then deactivating the environment.
   - **Key Commands**:
     - `conda activate base`: Activates the base conda environment.
     - `sleep 15 && python3 TFAPI_dwl827.py`: Waits for 15 seconds before running the Python script `TFAPI_dwl827.py`.
     - `conda deactivate`: Deactivates the conda environment after the Python script has finished executing.
   - **Usage**:
     ```sh
     ./refresh.sh
     ```

2. **TFAPI_dwl827.py**
   - **Description**: This Python script downloads genetic variant data from a specified API, decompresses the data, and then processes it to insert into the `HD827` database using `Add2VarDB827.py`.
   - **Key Functions**:
     - **Data Download**: Fetches data from an API endpoint using `requests` and handles SSL warnings with `urllib3`.
     - **Data Decompression**: Uses `subprocess` to create directories, download files, and unzip them.
     - **Data Insertion**: Calls `Add2VarDB827.py` to insert the processed VCF files into the database.
   - **Dependencies**: `glob`, `subprocess`, `time`, `datetime`, `csv`, `requests`, `urllib3`, `sys`
   - **Usage**:
     ```sh
     python3 TFAPI_dwl827.py
     ```

3. **InitVarDB827.py**
   - **Description**: This script reinitializes the `HD827` database by creating the necessary tables for storing genetic variant data. It drops existing tables if they exist and creates new ones with the required schema.
   - **Key Tables Created**:
     - `ref_genome`, `AnnotationVersion`, `WorkFlowName`, `WorkFlowVer`, `BaseCallVer`, `Chromosomes`, `VarType`, `DisType`, `Transcripts`, `Genes`, `RunInfo`, `HGVS`, `VarData`, `CallData`
   - **Dependencies**: `mysql.connector`, `os`, `re`, `numpy`, `pandas`, `vcf`, `json`, `io`, `ast`
   - **Usage**:
     ```sh
     python InitVarDB827.py
     ```

4. **InitExomeDB_nbirdt.py**
   - **Description**: Similar to `InitVarDB827.py`, this script reinitializes the `EXOME` database. It creates the necessary tables for storing exome data and sets up the schema.
   - **Key Tables Created**:
     - `ref_genome`, `AnnotationVersion`, `WorkFlowName`, `WorkFlowVer`, `BaseCallVer`, `Chromosomes`, `VarType`, `DisType`, `Transcripts`, `Genes`, `RunInfo`, `HGVS`, `VarData`, `CallData`
   - **Dependencies**: `mysql.connector`, `os`, `re`, `numpy`, `pandas`, `vcf`, `json`, `io`, `ast`
   - **Usage**:
     ```sh
     python InitExomeDB_nbirdt.py
     ```

5. **Add2VarDB827.py**
   - **Description**: This script processes VCF files, corrects any errors in their headers, and inserts the data into the `HD827` database. It ensures that the VCF files conform to the expected format and structure for database insertion.
   - **Key Functions**:
     - **Header Correction**: Fixes common errors in VCF file headers.
     - **VCF Parsing**: Uses the `vcf` module to read VCF files and extract relevant data.
     - **Database Insertion**: Inserts data into various tables (`RunInfo`, `VarData`, `CallData`, etc.) in the `HD827` database.
   - **Dependencies**: `mysql.connector`, `os`, `re`, `numpy`, `pandas`, `vcf`, `sqlite3`, `io`, `argparse`
   - **Usage**:
     ```sh
     python Add2VarDB827.py -i input.vcf
     ```

6. **stds_dash_sql.HD827.py**
   - **Description**: This script sets up an interactive web interface using Dash to visualize and analyze the genetic variant data stored in the `HD827` database. It includes features for querying the database, displaying data tables, and generating plots.
   - **Key Features**:
     - **Data Retrieval**: Connects to the `HD827` MySQL database and retrieves relevant data for visualization.
     - **Interactive Dashboard**: Uses Dash components to create interactive tables and graphs.
     - **Conditional Formatting**: Applies conditional formatting to highlight significant data points (e.g., outliers).
   - **Dependencies**: `dash`, `dash_auth`, `dash_table`, `dash_core_components`, `dash_html_components`, `pandas`, `plotly`, `statistics`, `mysql.connector`, `time`, `datetime`, `csv`
   - **Usage**:
     ```sh
     python stds_dash_sql.HD827.py
     ```
   - **Access**:
     - Open your web browser and navigate to `http://localhost:8050` to access the Dash interface.

## Database Structure

The databases contain several tables to organize genetic variant data, including `CallData`, `VarData`, `RunInfo`, and other metadata tables.

## Authors

- **Eric Allain** - Script Author
- **Hadrien Gayap** - Editor
- **ACRI (Atlantic Cancer Research Institute)** - Organization

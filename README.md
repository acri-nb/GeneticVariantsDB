This project contains a series of Python scripts and a shell script to manage and analyze genetic variant data within the `HD827` and `EXOME` databases. The workflow automates the process of downloading new data from a ThermoFisher server, processing it, and inserting it into the databases.  A Dash application is then used to visualize and analyze the data.

# Workflow Overview

The system relies on three servers:

1. **Source Server:**  Houses the raw FASTQ sample files.
2. **ThermoFisher Server:**  Processes the raw data and provides access to the processed data through an API.
3. **Main Server:** Hosts the `HD827` and `EXOME` databases, runs the data retrieval and processing scripts, and hosts the Dash visualization application. 

**Here's the step-by-step breakdown:**
![Pipeline](Pipeline_VarDB.jpg)

1. **New Data Detection:** A cron job on the Source Server regularly checks for new FASTQ files. When a new file with the `HDXXX` identifier is detected, it triggers the workflow.
2. **Transfer to Main Server:** The new FASTQ file is securely copied (scp) from the Source Server to the Main Server.
3. **Data Request to ThermoFisher:** The Main Server sends a request to the ThermoFisher Server's API to process the transferred FASTQ file. This requires a valid ThermoFisher account and authentication token.
4. **Data Processing and Download:** The ThermoFisher Server processes the data and makes the results available for download as a zip file containing VCF (Variant Call Format) data. 
5. **Data Insertion:**
   - The Main Server downloads the zip file from the ThermoFisher server.
   - The script `TFAPI_dwl827.py` unzips the file.
   - The script `Add2VarDB827.py` reads the VCF data, performs necessary validation and corrections, and then inserts the data into the appropriate tables in the `HD827` database.
6. **Data Visualization:** The `stds_dash_sql.HD827.py` script, running on the Main Server, connects to the `HD827` database, retrieves data, and displays it in an interactive dashboard using the Dash framework. This dashboard is accessible through a web browser.

# Prerequisites

- **Source Server:**
   -  `cron` for scheduling tasks.
   -  `scp` for secure file transfer. 
- **ThermoFisher Server:**
   -  Active ThermoFisher account with API access.
   -  Authentication token for API requests.
- **Main Server:**
   - Python 3.6 or later
   - Anaconda
   - MySQL
   - Python Modules: `glob`, `subprocess`, `time`, `datetime`, `csv`, `requests`, `urllib3`, `sys`, `mysql.connector`, `os`, `re`, `numpy`, `pandas`, `vcf`, `json`, `io`, `ast`, `dash`, `dash_auth`, `plotly`, `statistics`

# Installation

1. **Clone the repository on the Main Server:**
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
   - Update the database credentials in `InitVarDB827.py` and `InitExomeDB_nbirdt.py`.

# Usage
To use our propose solution, you have 2 ways to start : 
- Directly by using your own envirronement
- Using Docker Compose (Highly recommended)

## Normal

### Step 1: Initialize the Databases (on Main Server)

```sh
python InitVarDB827.py
python InitExomeDB_nbirdt.py
```

### Step 2:  Configure Cron Job (on Source Server)

Set up a cron job to regularly execute a script that:
   - Checks for new FASTQ files with the `HDXXX` identifier.
   - Securely copies (scp) new files to the designated directory on the Main Server.
   - (Optional) Triggers the data processing script on the Main Server.

### Step 3: Run Data Processing (on Main Server)

   - **Manual Execution:**
     ```sh
     python TFAPI_dwl827.py  
     ```
   - **Automated (Triggered by Cron):**  Modify `TFAPI_dwl827.py` to automatically detect and process new files placed in the designated directory by the Source Server's cron job.

### Step 4: Visualize the Data (on Main Server)

   ```sh
   python stds_dash_sql.HD827.py
   ```
   - Access the dashboard in your web browser: `http://localhost:8050` (adjust port if necessary).


## With Docker Compose
This section of the README provides a step-by-step guide for users who want to deploy the system using Docker Compose. It covers the necessary configuration, how to build and run the containers, and how to access the Dash application.

  ```sh
   cd DockerMode
  ```

1. **Configuration:**

   -  **Edit `cronjobs/TFAPI_dwl.py`:**
     -  Set `ip_addr` to the IP address of your sequencing server.
     -  Set `auth_token` to your ThermoFisher API authorization token. 
   -  **Edit `docker-compose.yml`:**
     - Update the `source` path in the bind mount to the actual directory path on your host machine where you have placed `sample.prefixes`, `comments.txt`, and `exclusions.tsv`.
   - **Create Empty Files:**
     - In the host directory you specified for the bind mount (e.g., `/home/ionadmin/dash-files`), run the following:
        ```sh
        touch exclusions.tsv && touch comments.txt
        ```
   - **Edit `get_prefixes.sh`:**
     -  Update the `find` command's path to match the location where your Ion Reporter run directories are stored.
     -  Adjust the `grep` pattern if your sample prefixes don't start with "HD827".
   - **Edit crontab:**
      - Open your crontab (using `sudo crontab -e` if needed).
      -  Add the following line, making sure the path to `get_prefixes.sh` is correct:
         ```
         */15 * * * * /home/ionadmin/get_prefixes.sh 
         ```

2. **Build and run:**
   - Build and start the Docker containers:
      ```sh
      docker compose up --detach
      ```

3. **Access the app:**

   - The app will be available at `http://[your-server-ip]:8090` in your web browser.

4. **Stopping the app:**

   - Stop the Docker containers:
      ```sh
      docker compose down
      ```
   - **Warning:**  Using `docker compose down -v` will remove the MySQL data volume, deleting all stored data.


## Notes:

- The provided cron job runs every 15 minutes. Adjust the schedule as needed. 
- You may need to modify the regex patterns in `get_prefixes.sh` to match your specific file naming conventions.
- It is recommended to capture at least 5 runs initially to ensure the graphics in the app are interpretable and to avoid potential errors. 
-  The Docker Compose setup assumes the Dash app and the sequencing data are on the same server. If this is not the case, further adjustments will be necessary. 
 
 **Explanation:**

- **Docker Compose:** Docker Compose simplifies the management of multi-container Docker applications.
- **Cron Jobs:** Automated tasks that run on a schedule, in this case, fetching new run prefixes.
- **Bind Mounts:** Connect directories on your host machine to directories inside Docker containers, providing persistent storage.
- **ThermoFisher API:** Used to access run information and download VCF files.


# Authors

- **Eric Allain** - Script Author
- **Hadrien Gayap** - Editor
- **ACRI (Atlantic Cancer Research Institute)** - Organization 

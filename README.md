This project contains a series of Python scripts and a shell script to manage and analyze genetic variant data within the `HD827` and `EXOME` databases. The workflow automates the process of downloading new data from a ThermoFisher server, processing it, and inserting it into the databases. A Dash application is then used to visualize and analyze the data.

# Workflow Overview

This system provides quality control data management and analysis for targeted exome sequencing, using standards like HD827. It involves 2 main components:

1. **ThermoFisher Server:** Processes the raw data and provides access to analyzed data through an API. (Ion Reporter software in this example).
2. **Main Server:** Hosts the MySQL databases (e.g., `HD827`, `EXOME`), runs data retrieval and processing scripts, and hosts the Dash visualization application.

**Workflow Breakdown**


1. **New Data Generation:** New FASTQ files are generated on the **Source Server** with standardized identifier prefixes.
2. **Run Identification and API Request:** A cron job on the **Main Server**, managed by a script like `get_prefixes.sh`, identifies new runs by checking for these prefixes. It then triggers an API request to the **ThermoFisher Server**.
3. **Data Processing:** The **ThermoFisher Server** processes the raw FASTQ data using the specified workflow (e.g., IonReporter software).
4. **Data Request and Download:** End-users analyze the processed data on the **ThermoFisher Server** (e.g., using IonReporter). A zip file containing the analyzed data in VCF format is then requested through the API.
5. **Data Validation and Insertion:**
   - The **Main Server** downloads the zip file from the **ThermoFisher Server**.
   - A Python script (e.g., `TFAPI_dwl827.py`) unzips the file.
   - Another Python script (e.g., `Add2VarDB827.py`) validates and corrects the VCF data and inserts it into the appropriate MySQL database (e.g., `HD827`).
6. **Data Visualization:** A final Python script (e.g., `stds_dash_sql.HD827.py`) running on the **Main Server** retrieves the data from the database and displays it in an interactive dashboard using the Dash framework. This dashboard is accessible via a web browser.

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
To use our proposed solution, you have 2 ways to start:
- Directly by using your own environment
- Using Docker Compose (Highly recommended)

We will assume that the app runs on the same server where data is generated.

## Normal

### Step 1: Initialize the Databases (on Main Server)

```sh
python InitVarDB827.py
python InitExomeDB_nbirdt.py
```

### Step 2: Configure Cron Job (on Source Server)

Set up a cron job to regularly execute a script that:
   - Checks for new FASTQ files with the `HDXXX` identifier.
   - Securely copies (scp) new files to the designated directory on the Main Server.
   - (Optional) Triggers the data processing script on the Main Server.

In the `cronjobs/TFAPI_dwl.py` script, two parameters need to be manually set: the machine IP address (replace `0.0.0.0`) and the authorization token for communicating with the ThermoFisher API with the user account (replace the placeholder after `Authorization:`).

```python
csv_reader = reader(
    open("/var/dash-files/sample.prefixes", "r"),
    quotechar="\""
)
ip_addr = "0.0.0.0"
auth_token = "Authorization:"
```

Edit your crontab on the sequencer's server to include:

```sh
*/15 * * * * /home/ionadmin/get_prefixes.sh
```

### Step 3: Run Data Processing (on Main Server)

   - **Manual Execution:**
     ```sh
     docker exec -it acri-cronjobs-1 conda run -n docker-base --no-capture-output python3 TFAPI_dwl.py
     ```
   - **Automated (Triggered by Cron):** Modify `TFAPI_dwl827.py` to automatically detect and process new files placed in the designated directory by the Source Server's cron job.

This command should also be inserted in the `/home/ionadmin/get_prefixes.sh` file.

### Step 4: Visualize the Data (on Main Server)

   ```sh
   python stds_dash_sql.HD827.py
   ```
   - Access the dashboard in your web browser: `http://[your-server-ip]:8090` (adjust port if necessary).

## With Docker Compose
This section provides a step-by-step guide for users who want to deploy the system using Docker Compose. It covers the necessary configuration, how to build and run the containers, and how to access the Dash application.

  ```sh
   cd DockerMode
  ```

### 1. **Configuration:**

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

### 2. **Build and run:**
   - Build and start the Docker containers:
      ```sh
      docker compose up --detach
      ```

### 3. **Access the app:**

   - The app will be available at `http://[your-server-ip]:8090` in your web browser.

### 4. **Stopping the app:**

   - Stop the Docker containers:
      ```sh
      docker compose down
      ```
   - **Warning:**  Using `docker compose down -v` will remove the MySQL data volume, deleting all stored data.


## Notes:

- The provided cron job runs every 15 minutes. Adjust the schedule as needed. 
- You may need to modify the regex patterns in `get_prefixes.sh` to match your specific file naming conventions.
- It is recommended to capture at least 5 runs initially to ensure the graphics in the app are interpretable and to avoid potential errors. 
- The Docker Compose setup assumes the Dash app and the sequencing data are on the same server. If this is not the case, further adjustments will be necessary. 
 
 **Explanation:**

- **Docker Compose:** Docker Compose simplifies the management of multi-container Docker applications.
- **Cron Jobs:** Automated tasks that run on a schedule, in this case, fetching new run prefixes.
- **Bind Mounts:** Connect directories on your host machine to directories inside Docker containers, providing persistent storage.
- **ThermoFisher API:** Used to access run information and download VCF files.


# Authors

- **Eric Allain** - Script Author
- **Hadrien Gayap** - Editor
- **ACRI (Atlantic Cancer Research Institute)** - Organization

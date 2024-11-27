This project contains a series of Python scripts and a shell script to manage and analyze genetic variant data within the `vardb` and database. It displays an interactive dash app for tracking variant information run-to-run in internal standards from clinical sequencing batches.
The workflow can also automate the process of downloading new data from a ThermoFisher server, processing it, and inserting it into the databases via an API. It has been tested on thermofisher GENEXUS technology with Oncomine OMA, OCA+ and OFA kits.  

# Workflow Overview

This system provides quality control data management and analysis for targeted exome sequencing, using standards like HD827 from Horizon Discovery with known allele frequencies for specific variants. It involves 2 main components:

1. **Remote Server:** Processes the raw data and provides access to filtered, analyzed data through an API. (Ion Reporter software in our example). Alternatively, we have provided scripts to adapt DRAGEN (Illumina) generated vcf files into the existing MySQL framework.
2. **Host Server:** Hosts the MySQL databases (e.g., `vardb`), runs data retrieval and processing scripts, and hosts the Dash visualization application.

**Workflow Breakdown**
![Pipeline](Pipeline_VarDB.jpg)

1. **New Data Generation:** New FASTQ files are generated on the **Host Server** with standardized identifier prefixes (`vardb`).
2. **Run Identification and API Request:** A cron job on the **Host Server**, runs the API query for files within a 25-day window, checking for user-analyzed vcf files with the stardardized prefixes. It then triggers an API request to the **ThermoFisher Server** to download the files.
3. **Data Validation and Insertion:**
   - The **Host Server** downloads the zip file from the **ThermoFisher Server**.
   - A Python script (e.g., `TFAPI_dwl.py`) unzips the file.
   - Another Python script (e.g., `Add2VarDB.py`) validates and corrects the VCF header and inserts the data into the appropriate MySQL database (e.g., `vardb`).
6. **Data Visualization:** A final Python script (e.g., `vardb.py`) running on the **Host Server** retrieves the data from the database and displays it in an interactive dashboard using the Dash framework. This dashboard is accessible via a web browser.

# Prerequisites

- **Host Server:**
   -  `cron` for scheduling tasks.
   -  `scp` for secure file transfer.
   -  `docker` and `docker-compose`
- **ThermoFisher Server:**
   -  Active ThermoFisher account with API access.
   -  Authentication credentials for API requests.


# Installation and Testing

1. **Clone the repository on the Main Server:**
   ```sh
   git clone https://github.com/acri-nb/GeneticVariantsDB.git
   cd GeneticVariantsDB
   ```

2. **Set up the bind mount files:**
   ```sh
   mkdir /home/<user>/dash-files
   cp GeneticVariantsDB/data/*.txt /home/<user>/dash-files
   cp GeneticVariantsDB/data/*.tsv /home/<user>/dash-files
   ```

3. **Set Host Parameters:**
   - Open `/home/<user>/dash-files/config.txt` and set the desired parameters, such as ThermoFisher Sequencer IP address, login credentials, standards file prefix and number of standard deviations for boundaries.
   - Open `GeneticVariantsDB/DockerMode/compose.yaml` and edit all volume paths to `/home/<user>/dash-files`.
   - Run ``` docker compose up -d ```

4. **Access the app:**
   - The app will be available at `http://[your-server-ip]:8090` in your web browser.

5. **Stopping the app:**
   - Stop the Docker containers:
      ```sh
      docker compose down
      ```
   - **Warning:**  Using `docker compose down -v` will remove the MySQL data volume, deleting all stored data, `docker compose down` will only stop the app without removing stored data.

# Usage
## Files to Modify

The Docker mode requires modifications to specific files to run. Below is a list of the files that need to be modified.

### Files and Changes

#### 1. `config/config.txt`
- **Changes**:  
  "0.0.0.0" # line needs to be changed to your IP  
  "usr" # Your auth credentials for ThermoFishher need to be inserted  
  "pass" # Your auth credentials for ThermoFishher need to be inserted  
  "sample_prefix" # needs to match the beginning of your internal standards files  
  "3" # Scalar used to fix upper and lower bounds of acceptable deviation (scalar is multiplied by SD)

  You can then place this in your `/home/<user>/dash-files` directory

#### 2. `compose.yaml`
- **Changes**:  
  "source: /home/acri/dash-files" # in each volumes section, lines need to be changed to your host path (by default `/home/<user>/dash-files`)  

#### 3. `regions.txt`  
- **Changes**:  
  After inserting your vcf data into the MySQL tables via Add2VarDB.py, you can retrieve variant IDs with:  
  SELECT   
	  CallData.genotype,   
	  CallData.geno_qual,   
	  CallData.pass_filter,   
	  CallData.afreq,   
	  CallData.coverage,   
	  CallData.norm_count,   
	  CallData.sample,  
	  VarData.name,  
	  RunInfo.IonWF_version  
  FROM   
    CallData   
	  JOIN VarData ON VarData.id = CallData.variant  
	  JOIN RunInfo ON RunInfo.id = CallData.sample  
  Then, the variant IDs of interest can be added to `regions.txt`.  



## API

### Step 1: Initialize the cron job (on Host Server)

```sh
crontab -e
```
Then paste the following into the scheduler, replacing "acri" with your username:

```sh
*/15 * * * * docker exec -it acri-cronjobs-1 conda run -n docker-base --no-capture-output python3 TFAPI_dwl.py
```

## Sample data

To test the app with the provided sample data, populate the mysql tables with the provided vcf files, as follows, replacing `acri-cronjobs-1` with your cronjobs container name:

```sh
docker cp GeneticVariantsDB/data/*.vcf acri-cronjobs-1
```

Then, login to the container and insert data into the mysql container:

```sh
docker exec -it acri-cronjobs-1 bash
for i in *.vcf; do python3 Add2VarDB.py -i $i; done
```

## Notes:

- The provided cron job runs every 15 minutes. Adjust the schedule as needed. 
- You may need to modify the regex prefix patterns in `config.txt` to match your specific file naming conventions.
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
- **Nicolas Crapoulet and Philippe-Pierre Robichaud** - Testers & Feedback
- **ACRI (Atlantic Cancer Research Institute)** - Organization

# Files to Modify

The Docker mode requires modifications to specific files to run. Below is a list of the files that need to be modified.

## Files and Changes

### 1. `config/config.txt`
- **Changes**:  
  "0.0.0.0" # line needs to be changed to your IP  
  "usr" # Your auth credentials for ThermoFishher need to be inserted  
  "pass" # Your auth credentials for ThermoFishher need to be inserted  
  "sample_prefix" # needs to match the beginning of your internal standards files  
  "3" # Scalar used to fix upper and lower bounds of acceptable deviation (scalar is multiplied by SD)

  You can then place this in your `/home/<user>/dash-files` directory

### 2. `compose.yaml`
- **Changes**:  
  "source: /home/acri/dash-files" # in each volumes section, lines need to be changed to your host path (by default `/home/<user>/dash-files`)  

### 3. `regions.txt`  
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

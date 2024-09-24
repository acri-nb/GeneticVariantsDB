# Files to Modify

The Docker mode requires modifications to specific files to run. Below is a list of the files that need to be modified.

## Files and Changes

### 1. `cronjobs/TFAPI_dwl.py`
- **Changes**:
  - ip_addr = "0.0.0.0" # line needs to be changed to your IP
  - auth_token = "Authorization:" # Your auth token for ThermoFishher needs to be inserted

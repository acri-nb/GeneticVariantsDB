
#!/usr/bin/env python3
import glob
import subprocess
import time
from datetime import datetime, timedelta
from csv import reader
import requests
import urllib3
import sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


csv_reader = reader(open("dash-files/sample.prefixes","r"), quotechar="\"")
ip_addr = "0.0.0.0" # line needs to be changed to your IP
auth_token = "Authorization:" # Your auth token for ThermoFishher needs to be inserted

list_files =[]
for row in csv_reader:
    list_files.append(row)

if not list_files:
    sys.exit()

# datetime object containing current date and time
now = datetime.now()
then = now - timedelta(days=35)

for item in list_files:
    subprocess.call(["mkdir", "outfiles"])
    query1 = "https://%s:443/api/v1/analysis?format=json&name=%s&start_date=%s&end_date=%s" %(ip_addr, item[0], then.date(), now.date())
    query2 = "Content-Type:application/x-www-form-urlencoded"
    auth = auth_token
    out = "outfiles/%s.zip" %item[0]
    outdir = "outfiles/%s" %item[0]

    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': auth_token.split(":")[1],
    }

    params = (
    ('format', 'json'),
    ('start_date', then.date()),
    ('end_date', now.date()),
    ('name', item[0]))
    requestip = 'https://%s:443/api/v1/analysis' %ip_addr
    print(params)
    print(requestip)
    response = requests.get(requestip, headers=headers, params=params, verify=False)
    print(response)
    response.encoding = 'UTF-8'
    try:
        unfilt = response.json()[0]['data_links']['unfiltered_variants']
    except:
        continue
    subprocess.call(["mkdir", outdir])
    subprocess.call(["curl", "-v", "-X", "GET", "-k", "-H", query2, "-H", auth, unfilt, "-o", out])
    subprocess.call(["unzip", "-d", "outfiles", out])
    subprocess.call(["unzip", "outfiles/*All.zip", "-d", outdir])
    vcf = "%s.vcf" %item[0]
    target = glob.glob("./outfiles/%s/Variants/*/*Non-Filtered*.vcf" %item[0])
    subprocess.call(["mv", target[0], vcf])
    subprocess.call(["rm", "-rf", "outfiles"])
    subprocess.call(["python3", "Add2VarDB.py", "-i", vcf])
    subprocess.call(["rm", vcf])



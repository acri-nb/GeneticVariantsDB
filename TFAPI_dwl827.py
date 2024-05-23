
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


csv_reader = reader(open("HD200viz.1.names","r"), quotechar="\"")

list_files =[]
for row in csv_reader:
    list_files.append(row)

if not list_files:
    sys.exit()

# datetime object containing current date and time
now = datetime.now()
then = now - timedelta(days=30)

for item in list_files:
    subprocess.call(["mkdir", "/mnt/data/DB/HD200_DB/outfiles"])
    query1 = "https://10.111.243.2:443/api/v1/analysis?format=json&name=%s&start_date=%s&end_date=%s" %(item[0], then.date(), now.date())
    query2 = "Content-Type:application/x-www-form-urlencoded"
    auth = "####" #auth code on secure machine
    out = "/mnt/data/DB/HD200_DB/outfiles/%s.zip" %item[0]
    outdir = "/mnt/data/DB/HD200_DB/outfiles/%s" %item[0]

    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': '####',
    }

    params = (
    ('format', 'json'),
    ('start_date', then.date()),
    ('end_date', now.date()),
    ('name', item[0]))

    response = requests.get('https://10.111.243.2:443/api/v1/analysis', headers=headers, params=params, verify=False)
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
    subprocess.call(["rm", "-rf", "/mnt/data/DB/HD200_DB/outfiles"])
    subprocess.call(["python3", "Add2VarDB.py", "-i", vcf])
    subprocess.call(["rm", vcf])

open("HD200viz.1.names","w").close()
#insert call for zipfile here


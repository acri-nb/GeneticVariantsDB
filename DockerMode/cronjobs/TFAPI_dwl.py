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

#open config file to read ip address, user and pass for ThermoFisher API
with open('/dash-files/config.txt') as f:
    config = f.read().splitlines()

ip_addr = config[0]
user = config[1]
password = config[2]
sample_prefix = config[3]

#Read most recent file name prefixes
#csv_reader = reader(open("dash-files/sample.prefixes","r"), quotechar="\"")
#for row in csv_reader:
#    list_files.append(row)
def populate(ip):
    lst = []
    now = datetime.now()
    then = now - timedelta(days=25) # get only files from the past 25 days - you will pickup duplicates, but SQL insertion will not happen twice for same sample.

    headers = {
    'password': password,
    'username': user
    }

    params = (
    ('signedOff', 'FALSE'),
    ('end_date', now.date()),
    ('start_date', then.date()))

    response = requests.get('https://{0}:443/genexus/api/lims/v2/signedOffSamples'.format(ip), headers=headers, params=params, verify=False)
    response.encoding = 'UTF-8'
    data = response.json()

    baseURL = None
    for k in data['objects']:
        if k['sample']['sample_name'].startswith(sample_prefix):
            lst.append(k['sample']['sample_name'])
    return(lst)



# datetime object containing current date and time
now = datetime.now()
then = now - timedelta(days=25)
try:
    for item in populate(ip_addr):
        subprocess.call(["mkdir", "outfiles"])
        out = "outfiles/{0}.zip".format(item)
        outdir = "outfiles/{0}".format(item)

        headers = {
        'password':password,
        'username':user
        }

        params = (
        ('signedOff','FALSE'),
        ('end_date',now.date()),
        ('start_date',then.date()))

        response = requests.get('https://{0}:443/genexus/api/lims/v2/signedOffSamples'.format(ip_addr), headers=headers, params=params, verify=False)

        response.encoding = 'UTF-8'
        data = response.json()

        baseURL = None
        for k in data['objects']:
            if k['sample']['sample_name'] == item:
                baseURL =k['sample']['base_url']
        query1='https://{0}/genexus/api/lims/v2/download?file_list=*.vcf&path={1}'.format(ip_addr,baseURL)
        subprocess.call(["curl", "-v", "-k", "--header", 'username:{0}'.format(user),'--header','password:{0}'.format(password), query1, "-o", out]) #send query
        subprocess.call(["unzip", "-d", "outfiles", out]) #unzip
        #newstr = item+"_GENEXUS1"
        subprocess.call(["mv", "outfiles/*.vcf", "outfiles/{0}.vcf".format(item)]) #change the name from asterix.vcf to the correct sample name
        vcf = "outfiles/{0}.vcf".format(item)

        fh = open("outfiles/{0}.vcf".format(item), "r")
        lines = fh.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].rstrip()
            if lines[i].startswith("##IonReporterAnalysisName="):
                lines[i]= "##IonReporterAnalysisName={0}".format(item)
            else:
                continue
        with open("outfiles/{0}.vcf".format(item), "w") as fh2:
            for line in lines:
                fh2.write(line+"\n")

        subprocess.call(["python3", "Add2VarDB.py", "-i", vcf]) #add to DB, can be changes if using DRAGEN to Add2VarDB_Ilmna.py
        subprocess.call(["rm", "-rf", "outfiles"]) #remove any leftover files
except:
    pass

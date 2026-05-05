#!/usr/bin/env python3
import glob
import os
import shutil
import subprocess
from datetime import datetime, timedelta

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_PATH = os.getenv("TFAPI_CONFIG_PATH", "/dash-files/config.txt")
TOKEN_PATH = os.getenv("TFAPI_AUTH_TOKEN_FILE", "/dash-files/tfapi_auth_token.txt")
CONTENT_TYPE = os.getenv("TFAPI_CONTENT_TYPE", "application/x-www-form-urlencoded")


def read_config():
    try:
        with open(CONFIG_PATH) as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []


def read_auth_token():
    token = os.getenv("TFAPI_AUTH_TOKEN") or os.getenv("THERMOFISHER_AUTH_TOKEN")
    if token:
        return token.strip()

    try:
        with open(TOKEN_PATH) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def get_settings():
    config = read_config()
    ip_addr = os.getenv("TFAPI_IP_ADDR") or os.getenv("THERMOFISHER_IP_ADDR")
    if not ip_addr and config:
        ip_addr = config[0]
    if ip_addr == "0.0.0.0":
        ip_addr = ""

    sample_prefix = os.getenv("TFAPI_SAMPLE_PREFIX")
    if not sample_prefix and len(config) > 3:
        sample_prefix = config[3]
    sample_prefix = sample_prefix or "HD"

    try:
        lookback_days = int(os.getenv("TFAPI_LOOKBACK_DAYS", "2"))
    except ValueError:
        lookback_days = 2

    return {
        "ip_addr": ip_addr,
        "sample_prefix": sample_prefix,
        "lookback_days": lookback_days,
        "auth_token": read_auth_token(),
    }


def build_headers(auth_token):
    return {
        "Content-Type": CONTENT_TYPE,
        "Authorization": auth_token,
    }


def get_analysis(ip_addr, auth_token, params):
    response = requests.get(
        f"https://{ip_addr}:443/api/v1/analysis",
        headers=build_headers(auth_token),
        params=params,
        verify=False,
        timeout=60,
    )
    response.raise_for_status()
    response.encoding = "UTF-8"
    return response.json()


def populate(ip_addr, auth_token, sample_prefix, lookback_days):
    now = datetime.now()
    then = now - timedelta(days=lookback_days)
    params = (
        ("format", "json"),
        ("end_date", now.date()),
        ("start_date", then.date()),
        ("type", "analysis"),
        ("view", "summary"),
    )

    samples = []
    for analysis in get_analysis(ip_addr, auth_token, params):
        sample_data = analysis.get("samples", {})
        for molecule in ("RNA", "DNA"):
            sample_name = sample_data.get(molecule)
            if sample_name and sample_name.startswith(sample_prefix):
                samples.append(sample_name)

    return samples


def download_unfiltered_variants(ip_addr, auth_token, sample_name, lookback_days):
    now = datetime.now()
    then = now - timedelta(days=lookback_days)
    params = (
        ("format", "json"),
        ("end_date", now.date()),
        ("start_date", then.date()),
        ("type", "analysis"),
        ("name", sample_name),
    )

    analyses = get_analysis(ip_addr, auth_token, params)
    if not analyses:
        return None

    download_url = analyses[0].get("data_links", {}).get("unfiltered_variants")
    if not download_url:
        return None

    output_path = f"outfiles/{sample_name}.zip"
    response = requests.get(
        download_url,
        headers=build_headers(auth_token),
        verify=False,
        timeout=300,
    )
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


def process_sample(ip_addr, auth_token, sample_name, lookback_days):
    shutil.rmtree("outfiles", ignore_errors=True)
    os.makedirs("outfiles", exist_ok=True)

    zip_path = download_unfiltered_variants(ip_addr, auth_token, sample_name, lookback_days)
    if not zip_path:
        return

    sample_dir = f"outfiles/{sample_name}"
    subprocess.check_call(["unzip", "-q", "-d", "outfiles", zip_path])

    all_zips = glob.glob("outfiles/*All.zip")
    if not all_zips:
        return

    os.makedirs(sample_dir, exist_ok=True)
    subprocess.check_call(["unzip", "-q", all_zips[0], "-d", sample_dir])

    targets = glob.glob(f"./outfiles/{sample_name}/Variants/*/*Non-Filtered*.vcf")
    if not targets:
        return

    vcf_path = f"outfiles/{sample_name}.vcf"
    shutil.move(targets[0], vcf_path)
    subprocess.check_call(["python3", "Add2VarDB.py", "-i", vcf_path])


def main():
    settings = get_settings()
    if not settings["ip_addr"] or not settings["auth_token"]:
        print(
            "TFAPI_dwl.py skipped: missing TFAPI_IP_ADDR/THERMOFISHER_IP_ADDR "
            "or TFAPI_AUTH_TOKEN/TFAPI_AUTH_TOKEN_FILE."
        )
        return

    try:
        samples = populate(
            settings["ip_addr"],
            settings["auth_token"],
            settings["sample_prefix"],
            settings["lookback_days"],
        )
        print(samples)
        for sample_name in samples:
            try:
                process_sample(
                    settings["ip_addr"],
                    settings["auth_token"],
                    sample_name,
                    settings["lookback_days"],
                )
            except Exception as exc:
                print(f"Failed to process {sample_name}: {exc}")
            finally:
                shutil.rmtree("outfiles", ignore_errors=True)
    except Exception as exc:
        print(f"TFAPI download failed: {exc}")


if __name__ == "__main__":
    main()

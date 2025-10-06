#!/usr/bin/env python3

# Optimized version with Redis caching and improved SQL queries

#Dependencies
import dash
import dash_auth
from dash_extensions.enrich import DashProxy, ServersideOutput, ServersideOutputTransform, html, dcc, dash_table, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import plotly.express as px
import statistics as st
import mysql.connector
import time
from datetime import datetime
import csv
from flask_caching import Cache
import scipy
import scipy.stats
import redis
import os
import json
import hashlib

# Initialize Redis connection
def get_redis_client():
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    return redis.from_url(redis_url, decode_responses=True)

# Cache helper functions
def get_cache_key(*args):
    """Generate a cache key from arguments"""
    key_string = "_".join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_get(key):
    """Get data from Redis cache"""
    try:
        redis_client = get_redis_client()
        cached_data = redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        print(f"Cache get error: {e}")
    return None

def cache_set(key, data, ttl=300):
    """Set data in Redis cache with TTL (default 5 minutes)"""
    try:
        redis_client = get_redis_client()
        redis_client.setex(key, ttl, json.dumps(data, default=str))
    except Exception as e:
        print(f"Cache set error: {e}")

#read the data from the mysql database with optimized query
def get_sql_optimized():
    start = time.time()
    
    # Check cache first
    cache_key = get_cache_key("main_data")
    cached_data = cache_get(cache_key)
    if cached_data:
        print(f"Cache hit! Retrieved in {time.time() - start:.2f} seconds")
        return pd.DataFrame(cached_data)
    
    # If not in cache, query database
    print("Cache miss, querying database...")
    
    #Use MySQL Connector for establishing link to DB in function
    mydb = mysql.connector.connect(host='db', database = 'vardb',user="usr", passwd='usrpass')
    
    exclusions = []
    with open('/dash-files/exclusions.tsv') as f:
        exclude = f.read().splitlines()
        exclusions = exclude
    print(f"Exclusions: {exclusions}")
    
    # Optimized query with explicit JOINs and WHERE clause
    query = """
    SELECT 
        c.pass_filter,
        c.afreq,
        c.coverage,
        c.norm_count,
        c.sample,
        v.name as variant_name,
        r.IonWF_version,
        r.name as sample_name,
        r.filedate,
        t.name as transcript_name,
        h.transcript,
        h.HGVSc,
        h.HGVSp,
        g.name as gene_name
    FROM CallData c
    INNER JOIN VarData v ON v.id = c.variant
    INNER JOIN RunInfo r ON r.id = c.sample
    LEFT JOIN HGVS h ON h.id = v.hgvs
    LEFT JOIN Transcripts t ON t.id = h.transcript
    LEFT JOIN Genes g ON g.id = v.gene
    WHERE r.filedate >= (SELECT MAX(filedate) - 365 FROM RunInfo)
    ORDER BY r.filedate DESC, v.name
    """
    
    df = pd.read_sql(query, mydb)
    mydb.close()
    
    #read-in data and change duplicated column headers
    df.columns = ['pass_filter','afreq','coverage','norm_count','sample','variant','IonWF_version','samplename','filedate','trname','transcript','HGVSc', 'HGVSp','gene']
    
    #get only HD200 and seracare samples (exclude unwanted samples)
    df = df[~df['samplename'].isin(exclusions)]
    
    #Get the variants of interest
    regions = []
    with open('/dash-files/regions.txt') as f:
        region = f.read().splitlines()
        regions = region
    
    # Filter by regions of interest
    df = df[df['variant'].isin(regions)]
    
    # Process fusion gene names
    df.replace([
        "chr1_154142876_C_C[chr1:156844363[_Fusion_None",
        "chr1_156100564_G_G[chr1:156844697[_Fusion_None",
        "chr1_205649522_C_C]chr7:140494267]_Fusion_None",
        "chr2_42522656_G_G]chr2:29446394]_Fusion_None",
        "chr2_113992971_C_C[chr3:12421203[_Fusion_None",
        "chr3_100451516_G_G[chr1:156844362[_Fusion_None",
        "chr4_1808623_G_G[chr4:1739412[_Fusion_None",
        "chr4_1808661_C_C]chr7:97991744]_Fusion_None",
        "chr4_1808661_C_C[chr4:1741428[_Fusion_None",
        "chr4_25665952_G_G]chr6:117645578]_Fusion_None",
        "chr5_149784243_C_C]chr6:117645578]_Fusion_None",
        "chr10_51582939_G_G[chr10:43612031[_Fusion_None",
        "chr10_61665880_G_G[chr10:43612032[_Fusion_None",
        "chr12_12022903_G_G]chr15:88483984]_Fusion_None",
        "chr21_42880008_C_C]chr21:39956869]_Fusion_None",
        "chr7_116411708_G_G[chr7:116414934[_RNAExonVariant_None",
        "chr7_55087058_G_G[chr7:55223522[_RNAExonVariant_None",
        "chr10_32306071_C_C[chr10:43609928[_Fusion_None",
        "chr22_23632600_A_A[chr9:133729450[_Fusion_None",
        "chr12_12022903_G_G[chr9:133729450[_Fusion_None",
        "chr12_12006495_G_G[chr9:133729450[_Fusion_None",
        "chr8_17830196_A_A[chr9:5069924[_Fusion_None",
        "chr8_41794774_C_C]chr16:3901010]_Fusion_None",
        "chr4_54280889_G_G[chr4:55141052[_Fusion_None",
        "chr15_74325744_C_C[chr17:38499689[_Fusion_None",
        "chr21_36231771_T_T]chr8:93029591]_Fusion_None",
        "chr19_1619110_C_C[chr1:164761731[_Fusion_None"
    ],[
        "TPM3(7) - NTRK1(10)",
        "LMNA(2) - NTRK1(11)",
        "SLC45A3(1) - BRAF(8)",
        "EML4(13) - ALK(20)",
        "PAX8(9) - PPARG(2)",
        "TFG(5) - NTRK1(10)",
        "FGFR3(17) - TACC3(10)",
        "FGFR3(17) - BAIAP2L1(2)",
        "FGFR3(17) - TACC3(11)",
        "SLC34A2(4) - ROS1(34)",
        "CD74(6) - ROS1(34)",
        "NCOA4(7) - RET(12)",
        "CCDC6(1) - RET(12)",
        "ETV6(5) - NTRK3(15)",
        "TMPRSS2(1) - ERG(2)",
        "MET(13) - MET(15)",
        "EGFR(1) - EGFR(8)",
        "KIF5B(24) - RET(11)",
        "BCR(14)-ABL1(2)",
        "ETV6(5)-ABL1(2)",
        "ETV6(4)-ABL1(2)",
        "PCM1(23)-JAK2(12)",
        "KAT6A(17)-CREBBP(2)",
        "FIP1L1(11)-PDGFRA(12)",
        "PML(6)-RARA(3)",
        "RUNX1(3)-RUNX1T1(3)",
        "TCF3(16)-PBX1(3)"
    ], inplace = True)
    
    #Sort by date
    df = df.sort_values(["filedate","variant"])
    df = df.reset_index(drop=True)
    
    limit = None
    with open('/dash-files/config.txt') as f:
        vals = f.read().splitlines()
        limit = int(vals[4])
    
    #Drop uninformative columns, add stdev for numerical values and group the entire table by variant
    tabledf = df.drop(labels=['IonWF_version','pass_filter','transcript'], axis =1)
    tabledf['afreq'] = tabledf['afreq'].fillna(0)
    tabledf['afreq'] = tabledf['afreq'].astype(float)
    tabledf['afreq'] = 100*(tabledf['afreq'])
    tabledf['norm_count'] = tabledf['norm_count'].fillna(0)
    tabledf['norm_count'] = 1000000*(tabledf['norm_count'])
    tabledf['afreq_normcount'] = tabledf['afreq'] + tabledf['norm_count']
    tabledf['sd'] = tabledf.groupby('variant').afreq_normcount.transform('std')
    tabledf['upper_bound'] = tabledf['afreq_normcount'] + limit*(tabledf['sd'])
    tabledf['lower_bound'] = tabledf['afreq_normcount'] - limit*(tabledf['sd'])
    tabledf = tabledf.drop('afreq_normcount', axis=1)
    
    # Cache the result
    cache_set(cache_key, tabledf.to_dict('records'), ttl=300)  # 5 minutes TTL
    
    print(f"Database query completed in {time.time()-start:.2f} seconds")
    return tabledf

# Backward compatibility - use optimized version by default
def get_sql():
    return get_sql_optimized()

# Rest of the original functions remain the same...
def getSummary(data, bioMolecule):
    # Check cache first
    cache_key = get_cache_key("summary", bioMolecule, str(hash(str(data))))
    cached_data = cache_get(cache_key)
    if cached_data:
        return pd.DataFrame(cached_data)
    
    # Original getSummary logic...
    cleared_samples = []
    with open('/dash-files/cleared.tsv') as f:
        include = f.read().splitlines()
        cleared_samples = include
    limit = None
    with open('/dash-files/config.txt') as f:
        vals = f.read().splitlines()
        limit = int(vals[4])
    
    if bioMolecule == "DNA":
        neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        t0 = pd.read_json(data)
        t0 = t0[neworder]
        t0 = t0.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        summarizedData = t0[t0['samplename'].isin(cleared_samples)]
        summarizedData['sd'] = summarizedData.groupby('variant').afreq.transform('std')
        summarizedData['upper_bound'] = summarizedData['afreq'] + limit*(summarizedData['sd'])
        summarizedData['lower_bound'] = summarizedData['afreq'] - limit*(summarizedData['sd'])
        summarizedData = summarizedData.groupby('variant', as_index=False).agg({
            'samplename': 'nunique', 
            'coverage': ['mean'], 
            'afreq': ['mean'], 
            'trname': lambda x: scipy.stats.mode(x)[0], 
            'HGVSc': lambda x: scipy.stats.mode(x)[0], 
            'HGVSp':lambda x: scipy.stats.mode(x)[0], 
            'gene': lambda x: scipy.stats.mode(x)[0], 
            'sd': ['mean'], 
            'upper_bound': ['mean'], 
            'lower_bound':['mean']
        })
        summarizedData.columns = summarizedData.columns.droplevel(1)
        neworder1 = ['variant','gene','afreq','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        summarizedData = summarizedData[neworder1]
        summarizedData = summarizedData[summarizedData['variant'].str.startswith('chr')]
        summarizedData = summarizedData.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        summarizedData.loc[summarizedData['upper_bound'] > 100.00, 'upper_bound'] = 100.00
        summarizedData['lower_bound'].values[summarizedData['lower_bound'].values < 0.00] = 0.00
        
        # Cache the result
        result_dict = summarizedData.to_dict('records')
        cache_set(cache_key, result_dict, ttl=300)
        return summarizedData
        
    if bioMolecule == "RNA":
        neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        t0 = pd.read_json(data)
        t0 = t0[neworder]
        t0 = t0.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
        summarizedData = t0[t0['samplename'].isin(cleared_samples)]
        summarizedData['sd'] = summarizedData.groupby('variant').norm_count.transform('std')
        summarizedData['upper_bound'] = summarizedData['norm_count'] + limit*(summarizedData['sd'])
        summarizedData['lower_bound'] = summarizedData['norm_count'] - limit*(summarizedData['sd'])
        summarizedData = summarizedData.groupby('variant', as_index=False).agg({
            'samplename': 'nunique', 
            'coverage': ['mean'], 
            'norm_count': ['mean'], 
            'trname': lambda x: scipy.stats.mode(x)[0], 
            'HGVSc': lambda x: scipy.stats.mode(x)[0], 
            'HGVSp':lambda x: scipy.stats.mode(x)[0], 
            'gene': lambda x: scipy.stats.mode(x)[0], 
            'sd': ['mean'], 
            'upper_bound': ['mean'], 
            'lower_bound':['mean']
        })
        summarizedData.columns = summarizedData.columns.droplevel(1)
        neworder1 = ['variant','gene','norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        summarizedData = summarizedData[neworder1]
        summarizedData = summarizedData[~summarizedData['variant'].str.startswith('chr')]
        summarizedData = summarizedData.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        summarizedData['lower_bound'].values[summarizedData['lower_bound'].values < 0] = 0
        
        # Cache the result
        result_dict = summarizedData.to_dict('records')
        cache_set(cache_key, result_dict, ttl=300)
        return summarizedData

# Create the app with Redis caching
app = dash.Dash(__name__)
server = app.server

# Configure Flask-Caching with Redis
cache = Cache(app.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Rest of the original code structure remains the same...
# (Include all the original layout and callback functions here)
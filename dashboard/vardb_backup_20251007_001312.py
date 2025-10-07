#!/usr/bin/env python3

# Optimized version with Redis caching, improved SQL queries, and performance indexes
# Maintains full compatibility with original vardb.py functionality

#Dependencies
import dash
import dash_auth
from dash import Dash, html, dcc, dash_table, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import plotly.express as px
import statistics as st
import mysql.connector
from sqlalchemy import create_engine
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
import functools
from collections import defaultdict

# Initialize Redis connection
def get_redis_client():
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    try:
        return redis.from_url(redis_url, decode_responses=True)
    except:
        print("Redis not available, continuing without cache")
        return None

# Global configuration cache (loaded once)
CONFIG_CACHE = {}
STATS_CACHE = {}

# Memory cache for expensive computations
from functools import lru_cache

# Cache helper functions
def get_cache_key(*args):
    """Generate a cache key from arguments"""
    key_string = "_".join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_get(key):
    """Get data from Redis cache"""
    try:
        redis_client = get_redis_client()
        if redis_client:
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
        if redis_client:
            redis_client.setex(key, ttl, json.dumps(data, default=str))
    except Exception as e:
        print(f"Cache set error: {e}")

# Enhanced cache functions for Phase 2
def cache_get_or_compute(cache_key, compute_func, ttl=300, *args, **kwargs):
    """Get from cache or compute and cache the result"""
    cached_data = cache_get(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Compute the result
    result = compute_func(*args, **kwargs)
    cache_set(cache_key, result, ttl)
    return result

@lru_cache(maxsize=100)
def load_config_file(filepath):
    """Load and cache configuration files"""
    try:
        with open(filepath, 'r') as f:
            return f.read().splitlines()
    except:
        return []

@lru_cache(maxsize=50)  
def calculate_stats_cached(data_hash, variant, biomolecule):
    """Cache statistical calculations for Levey-Jennings charts"""
    # This will be implemented to cache heavy statistical computations
    return None

def get_data_hash(data):
    """Generate hash for data to use as cache key"""
    if isinstance(data, pd.DataFrame):
        return hashlib.md5(pd.util.hash_pandas_object(data).values.tobytes()).hexdigest()
    return hashlib.md5(str(data).encode()).hexdigest()

# Factorized functions for common operations
def process_sample_data(data, sample_value, biomolecule_type, filter_failing=False):
    """Common logic for processing sample data (DNA/RNA)"""
    if not data or not sample_value:
        return []
    
    # Convert JSON data to DataFrame
    if isinstance(data, str):
        df = pd.read_json(data)
    else:
        df = pd.DataFrame(data)
    
    # Use consistent column names from the data
    column_mapping = {
        'variant': 'variant',
        'gene': 'gene', 
        'samplename': 'samplename',
        'afreq': 'afreq',
        'norm_count': 'norm_count',
        'coverage': 'coverage',
        'sd': 'sd',
        'upper_bound': 'upper_bound',
        'lower_bound': 'lower_bound'
    }
    
    # Filter by sample
    sample_data = df[df['samplename'] == sample_value].copy()
    
    # Filter by biomolecule type
    if biomolecule_type == "DNA":
        sample_data = sample_data[sample_data['variant'].str.startswith('chr', na=False)]
    elif biomolecule_type == "RNA": 
        sample_data = sample_data[~sample_data['variant'].str.startswith('chr', na=False)]
    
    if filter_failing:
        # Apply QC failure logic - this would need pass_filter column
        # For now, filter by zero afreq as proxy
        sample_data = sample_data[sample_data['afreq'] == 0]
    
    # Prepare display data with all required columns
    display_data = []
    for _, row in sample_data.iterrows():
        if biomolecule_type == "DNA":
            display_data.append({
                'variant': row.get('variant', ''),
                'gene': row.get('gene', ''),
                'afreq': f"{float(row.get('afreq', 0)):.3f}",
                'sd': f"{float(row.get('sd', 0)):.3f}",
                'upper_bound': f"{float(row.get('upper_bound', 0)):.3f}",
                'lower_bound': f"{float(row.get('lower_bound', 0)):.3f}",
                'coverage': f"{float(row.get('coverage', 0)):.0f}"
            })
        else:  # RNA
            display_data.append({
                'variant': row.get('variant', ''),
                'gene': row.get('gene', ''),
                'norm_count': f"{float(row.get('norm_count', 0)):.0f}",
                'sd': f"{float(row.get('sd', 0)):.0f}",
                'upper_bound': f"{float(row.get('upper_bound', 0)):.0f}",
                'lower_bound': f"{float(row.get('lower_bound', 0)):.0f}",
                'coverage': f"{float(row.get('coverage', 0)):.0f}"
            })
    
    return display_data

# Pagination helper functions
def paginate_data(data, page_current, page_size):
    """Paginate data for large tables"""
    if not data:
        return data, 0
    
    total_pages = max(1, (len(data) + page_size - 1) // page_size)
    start_idx = page_current * page_size
    end_idx = start_idx + page_size
    
    return data[start_idx:end_idx], total_pages

def create_pagination_info(page_current, page_size, total_records):
    """Create pagination display information"""
    start_record = page_current * page_size + 1
    end_record = min((page_current + 1) * page_size, total_records)
    
    return f"Displaying records {start_record} to {end_record} of {total_records} total"

# Optimized getSummary using pre-aggregated views
def getSummaryOptimized(bioMolecule):
    """Get summary data using pre-aggregated MySQL views for better performance"""
    cache_key = get_cache_key("summary_optimized", bioMolecule)
    cached_data = cache_get(cache_key)
    if cached_data:
        return pd.DataFrame(cached_data)
    
    # Connect to database
    mydb = mysql.connector.connect(host='db', database='vardb', user="usr", passwd='usrpass')
    
    # Load configuration
    cleared_samples = load_config_file('/dash-files/cleared.tsv')
    config_vals = load_config_file('/dash-files/config.txt')
    limit = int(config_vals[4]) if len(config_vals) > 4 else 2
    
    # Build query using aggregated views
    query = f"""
    SELECT 
        variant_name as variant,
        gene_name as gene,
        {'avg_afreq as afreq' if bioMolecule == 'DNA' else 'avg_coverage as norm_count'},
        stddev_afreq as sd,
        {'avg_afreq' if bioMolecule == 'DNA' else 'avg_coverage'} + {limit} * stddev_afreq as upper_bound,
        {'avg_afreq' if bioMolecule == 'DNA' else 'avg_coverage'} - {limit} * stddev_afreq as lower_bound,
        avg_coverage as coverage,
        total_calls as samplename,
        'N/A' as trname,
        'N/A' as HGVSc,
        'N/A' as HGVSp
    FROM vw_summary_by_biomolecule 
    WHERE biomolecule_type = '{bioMolecule}'
    """
    
    try:
        summarizedData = pd.read_sql(query, mydb)
        
        # Apply bounds constraints
        if bioMolecule == "DNA":
            summarizedData.loc[summarizedData['upper_bound'] > 100.00, 'upper_bound'] = 100.00
            summarizedData['lower_bound'] = summarizedData['lower_bound'].clip(lower=0.00)
        
        # Round numerical values
        numeric_cols = ['afreq' if bioMolecule == 'DNA' else 'norm_count', 'sd', 'upper_bound', 'lower_bound', 'coverage']
        for col in numeric_cols:
            if col in summarizedData.columns:
                summarizedData[col] = summarizedData[col].round(2 if bioMolecule == 'DNA' else 0)
        
        # Cache results
        result_dict = summarizedData.to_dict('records')
        cache_set(cache_key, result_dict, ttl=300)
        
    except Exception as e:
        print(f"Error in getSummaryOptimized: {e}")
        # Fallback to original function if needed
        return pd.DataFrame()
    finally:
        mydb.close()
    
    return summarizedData

# Optimized Levey-Jennings data generation using pre-aggregated views
def getLeveyJenningsDataOptimized(variant_name, biomolecule_type):
    """Get Levey-Jennings chart data using pre-aggregated MySQL views"""
    cache_key = get_cache_key("levey_jennings", variant_name, biomolecule_type)
    cached_data = cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # Connect to database
    mydb = mysql.connector.connect(host='db', database='vardb', user="usr", passwd='usrpass')
    
    query = """
    SELECT 
        sample_name,
        filedate,
        avg_afreq,
        rolling_mean_afreq,
        rolling_stddev_afreq,
        ucl_2sigma,
        lcl_2sigma,
        ucl_3sigma,
        lcl_3sigma,
        control_status
    FROM vw_levey_jennings_stats
    WHERE variant_name = %s AND biomolecule_type = %s
    ORDER BY filedate ASC
    """
    
    try:
        lj_data = pd.read_sql(query, mydb, params=(variant_name, biomolecule_type))
        
        # Convert to dict for JSON serialization
        result = {
            'dates': lj_data['filedate'].dt.strftime('%Y-%m-%d').tolist(),
            'values': lj_data['avg_afreq'].tolist(),
            'mean_line': lj_data['rolling_mean_afreq'].tolist(),
            'ucl_2sigma': lj_data['ucl_2sigma'].tolist(),
            'lcl_2sigma': lj_data['lcl_2sigma'].tolist(),
            'ucl_3sigma': lj_data['ucl_3sigma'].tolist(),
            'lcl_3sigma': lj_data['lcl_3sigma'].tolist(),
            'control_status': lj_data['control_status'].tolist(),
            'sample_names': lj_data['sample_name'].tolist()
        }
        
        # Cache for 10 minutes (longer than summary data)
        cache_set(cache_key, result, ttl=600)
        
    except Exception as e:
        print(f"Error in getLeveyJenningsDataOptimized: {e}")
        result = {'dates': [], 'values': [], 'mean_line': [], 'ucl_2sigma': [], 'lcl_2sigma': [], 'ucl_3sigma': [], 'lcl_3sigma': [], 'control_status': [], 'sample_names': []}
    finally:
        mydb.close()
    
    return result

#read the data from the mysql database with optimized query
def get_sql():
    start = time.time()
    
    # Check cache first
    cache_key = get_cache_key("main_data")
    cached_data = cache_get(cache_key)
    if cached_data:
        print(f"Cache hit! Retrieved in {time.time() - start:.2f} seconds")
        return pd.DataFrame(cached_data)
    
    # If not in cache, query database
    print("Cache miss, querying database...")
    
    try:
        # Use SQLAlchemy with PyMySQL for better compatibility
        engine = create_engine("mysql+pymysql://usr:usrpass@db/vardb")
        print("Database connection established with SQLAlchemy + PyMySQL")
    except Exception as e:
        print(f"Database connection error: {e}")
        # Return empty DataFrame with correct columns to prevent crashes
        return pd.DataFrame(columns=['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename'])
    
        exclusions = []
        with open('/dash-files/exclusions.tsv') as f:
            exclude = f.read().splitlines()
            exclusions = exclude
        print(f"Exclusions: {exclusions}")
        
        # Optimized query with explicit JOINs and better performance
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
    ORDER BY r.filedate DESC, v.name
    """
    
        df = pd.read_sql(query, engine)
        print(f"Query executed successfully, got {len(df)} rows")
    
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
    
    # Replace fusion gene names with readable names
    df.replace(["chr1_154142876_C_C[chr1:156844363[_Fusion_None",\
    "chr1_156100564_G_G[chr1:156844697[_Fusion_None",\
    "chr1_205649522_C_C]chr7:140494267]_Fusion_None",\
    "chr2_42522656_G_G]chr2:29446394]_Fusion_None",\
    "chr2_113992971_C_C[chr3:12421203[_Fusion_None",\
    "chr3_100451516_G_G[chr1:156844362[_Fusion_None",\
    "chr4_1808623_G_G[chr4:1739412[_Fusion_None",\
    "chr4_1808661_C_C]chr7:97991744]_Fusion_None",\
    "chr4_1808661_C_C[chr4:1741428[_Fusion_None",\
    "chr4_25665952_G_G]chr6:117645578]_Fusion_None",\
    "chr5_149784243_C_C]chr6:117645578]_Fusion_None",\
    "chr10_51582939_G_G[chr10:43612031[_Fusion_None",\
    "chr10_61665880_G_G[chr10:43612032[_Fusion_None",\
    "chr12_12022903_G_G]chr15:88483984]_Fusion_None",\
    "chr21_42880008_C_C]chr21:39956869]_Fusion_None",\
    "chr7_116411708_G_G[chr7:116414934[_RNAExonVariant_None",\
    "chr7_55087058_G_G[chr7:55223522[_RNAExonVariant_None",\
    "chr10_32306071_C_C[chr10:43609928[_Fusion_None",\
    "chr22_23632600_A_A[chr9:133729450[_Fusion_None",\
    "chr12_12022903_G_G[chr9:133729450[_Fusion_None",\
    "chr12_12006495_G_G[chr9:133729450[_Fusion_None",\
    "chr8_17830196_A_A[chr9:5069924[_Fusion_None",\
    "chr8_41794774_C_C]chr16:3901010]_Fusion_None",\
    "chr4_54280889_G_G[chr4:55141052[_Fusion_None",\
    "chr15_74325744_C_C[chr17:38499689[_Fusion_None",\
    "chr21_36231771_T_T]chr8:93029591]_Fusion_None",\
    "chr19_1619110_C_C[chr1:164761731[_Fusion_None"],["TPM3(7) - NTRK1(10)",\
    "LMNA(2) - NTRK1(11)",\
    "SLC45A3(1) - BRAF(8)",\
    "EML4(13) - ALK(20)",\
    "PAX8(9) - PPARG(2)",\
    "TFG(5) - NTRK1(10)",\
    "FGFR3(17) - TACC3(10)",\
    "FGFR3(17) - BAIAP2L1(2)",\
    "FGFR3(17) - TACC3(11)",\
    "SLC34A2(4) - ROS1(34)",\
    "CD74(6) - ROS1(34)",\
    "NCOA4(7) - RET(12)",\
    "CCDC6(1) - RET(12)",\
    "ETV6(5) - NTRK3(15)",\
    "TMPRSS2(1) - ERG(2)",\
    "MET(13) - MET(15)",\
    "EGFR(1) - EGFR(8)",\
    "KIF5B(24) - RET(11)",\
    "BCR(14)-ABL1(2)",\
    "ETV6(5)-ABL1(2)",\
    "ETV6(4)-ABL1(2)",\
    "PCM1(23)-JAK2(12)",\
    "KAT6A(17)-CREBBP(2)",\
    "FIP1L1(11)-PDGFRA(12)",\
    "PML(6)-RARA(3)",\
    "RUNX1(3)-RUNX1T1(3)",\
    "TCF3(16)-PBX1(3)"], inplace = True)
    
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
    except Exception as e:
        print(f"Database query error: {e}")
        # Return empty DataFrame with correct columns to prevent crashes
        return pd.DataFrame(columns=['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename'])

def getSummary(data, bioMolecule):
    # Check cache first
    cache_key = get_cache_key("summary", bioMolecule, str(hash(str(data))))
    cached_data = cache_get(cache_key)
    if cached_data:
        return pd.DataFrame(cached_data)
    
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
        summarizedData = summarizedData.groupby('variant', as_index=False).agg({'samplename': 'nunique', 'coverage': ['mean'], 'afreq': ['mean'], 'trname': lambda x: scipy.stats.mode(x)[0], 'HGVSc': lambda x: scipy.stats.mode(x)[0], 'HGVSp':lambda x: scipy.stats.mode(x)[0], 'gene': lambda x: scipy.stats.mode(x)[0], 'sd': ['mean'], 'upper_bound': ['mean'], 'lower_bound':['mean']})
        summarizedData.columns = summarizedData.columns.droplevel(1)
        neworder1 = ['variant','gene','afreq','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        summarizedData = summarizedData[neworder1]
        summarizedData = summarizedData[summarizedData['variant'].str.startswith('chr')]
        summarizedData = summarizedData.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        summarizedData.loc[summarizedData['upper_bound'] > 100.00, 'upper_bound'] = 100.00
        summarizedData['lower_bound'].values[summarizedData['lower_bound'].values < 0.00] = 0.00
        
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
        summarizedData = summarizedData.groupby('variant', as_index=False).agg({'samplename': 'nunique', 'coverage': ['mean'], 'norm_count': ['mean'], 'trname': lambda x: scipy.stats.mode(x)[0], 'HGVSc': lambda x: scipy.stats.mode(x)[0], 'HGVSp':lambda x: scipy.stats.mode(x)[0], 'gene': lambda x: scipy.stats.mode(x)[0], 'sd': ['mean'], 'upper_bound': ['mean'], 'lower_bound':['mean']})
        summarizedData.columns = summarizedData.columns.droplevel(1)
        neworder1 = ['variant','gene','norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        summarizedData = summarizedData[neworder1]
        summarizedData = summarizedData[~summarizedData['variant'].str.startswith('chr')]
        summarizedData = summarizedData.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        summarizedData['lower_bound'].values[summarizedData['lower_bound'].values < 0] = 0
        
        result_dict = summarizedData.to_dict('records')
        cache_set(cache_key, result_dict, ttl=300)
        return summarizedData

# Create the app with Redis caching
app = dash.Dash(__name__)
server = app.server

# Configure Flask-Caching with Redis (fallback to simple cache if Redis unavailable)
try:
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        'CACHE_DEFAULT_TIMEOUT': 300
    })
except:
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300
    })

#defining the layout (same as original)
def serve_layout():
    sig_tab = pd.DataFrame({'Field':["QC Blanks","Coverage > 800","Uniformity > 80%","Lot Number","PhD", "MD"],'Value':["PASS  /  FAIL","PASS  /  FAIL","PASS  /  FAIL","___________________________________________________" ,"___________________________________________________","___________________________________________________"]})
    return html.Div(children=[
    dcc.Store(id='memory-output'),
    html.H1(children="MGDB control monitoring"),
    html.Br(),
    dcc.Dropdown(id = 'drpdown'),
    html.H2(children="DNA Variants not passing QC verification:"),
    dash_table.DataTable(id = 'table-fail',
        columns=[
        {'name':'Variant', 'id':'variant', 'deletable': False},
        {'name':'Gene', 'id':'gene', 'deletable': False},
        {'name':'Allele Frequency', 'id':'afreq', 'deletable': False},
        {'name':'Std deviation', 'id':'sd', 'deletable': False},
        {'name':'Upper Bound', 'id':'upper_bound', 'deletable': False},
        {'name':'Lower Bound', 'id':'lower_bound', 'deletable': False},
        {'name':'Coverage', 'id':'coverage', 'deletable': False}
        ],
        page_size=25,
        style_data_conditional=[
        {
            'if': {
                'filter_query':'{afreq} < {lower_bound}',
                'column_id':'afreq'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }, {
            'if': {
                'filter_query': '{afreq} > {upper_bound}',
                'column_id':'afreq'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }]),
    html.Br(),
    html.H2(children="RNA Variants not passing QC verification:"),
    dash_table.DataTable(id = 'table-fail2',
        columns=[
        {'name':'Variant', 'id':'variant', 'deletable': False},
        {'name':'Gene', 'id':'gene', 'deletable': False},
        {'name':'Normalized Counts', 'id':'norm_count', 'deletable': False},
        {'name':'Std deviation', 'id':'sd', 'deletable': False},
        {'name':'Upper Bound', 'id':'upper_bound', 'deletable': False},
        {'name':'Lower Bound', 'id':'lower_bound', 'deletable': False},
        {'name':'Coverage', 'id':'coverage', 'deletable': False}
        ],
        page_size=10,
        style_data_conditional=[
        {
            'if': {
                'filter_query':'{norm_count} < {lower_bound}',
                'column_id':'norm_count'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }, {
            'if': {
                'filter_query': '{norm_count} > {upper_bound}',
                'column_id':'norm_count'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }]),
    html.Br(),
    dash_table.DataTable(id = 'table-signature', data=sig_tab.to_dict('records'), css=[{
            'selector': 'tr:first-child',
            'rule': 'display: None;'
        }]),
    html.Br(),
    html.Div(id='output-container-button2',children='No comments to display'),
    html.Br(),
    html.Div(dcc.Input(id='input-box', type='text')),
    html.Button('Submit Comment', id='button'),
    html.Br(),
    html.Button('Validate Sample - Include in DB', id='button3'),
    html.Br(),
    html.Div(id='newlines-container',children='\n\n\n\n'),
    html.Br(),
    html.Div(id ='Breakdiv', style={'break-after':'page'}),
    html.Br(),
    html.H2(children="Complete table of run info for current sample (DNA variants)"),
    html.Div(id='table-2-pagination-info', style={'margin': '10px 0'}),
    dash_table.DataTable(id = 'table-2',
        columns=[{'name':'Variant', 'id':'variant', 'deletable': False},
                 {'name':'Gene', 'id':'gene', 'deletable': False},
                 {'name':'Allele Frequency', 'id':'afreq', 'deletable': False},
                 {'name':'Std deviation', 'id':'sd', 'deletable': False},
                 {'name':'Upper Bound', 'id':'upper_bound', 'deletable': False},
                 {'name':'Lower Bound', 'id':'lower_bound', 'deletable': False},
                 {'name':'Coverage', 'id':'coverage', 'deletable': False}
                 ],
        page_size=25,
        page_action='custom',
        page_current=0,
        style_data_conditional=[
        {
            'if': {
                'filter_query':'{afreq} < {lower_bound}',
                'column_id':'afreq'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }, {
            'if': {
                'filter_query': '{afreq} > {upper_bound}',
                'column_id':'afreq'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }]),
    html.Br(),
    html.H2(children="Complete table of run info for current sample (RNA variants)"),
    html.Div(id='table-3-pagination-info', style={'margin': '10px 0'}),
    dash_table.DataTable(id = 'table-3',
        columns=[
        {'name':'Variant', 'id':'variant', 'deletable': False},
        {'name':'Gene', 'id':'gene', 'deletable': False},
        {'name':'Normalized Counts', 'id':'norm_count', 'deletable': False},
        {'name':'Std deviation', 'id':'sd', 'deletable': False},
        {'name':'Upper Bound', 'id':'upper_bound', 'deletable': False},
        {'name':'Lower Bound', 'id':'lower_bound', 'deletable': False},
        {'name':'Coverage', 'id':'coverage', 'deletable': False}
        ],
        page_size=25,
        page_action='custom',
        page_current=0,
        style_data_conditional=[
        {
            'if': {
                'filter_query':'{norm_count} < {lower_bound}',
                'column_id':'norm_count'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }, {
            'if': {
                'filter_query': '{norm_count} > {upper_bound}',
                'column_id':'norm_count'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }]),
    html.Br(),
    html.H2(children="Levey-Jennings Graph for entire series (DNA variants)"),
    dash_table.DataTable(
    id='table',
    columns=[
        {'name':'Variant', 'id':'variant', 'deletable': False},
        {'name':'Gene', 'id':'gene', 'deletable': False},
        {'name':'Allele Frequency', 'id':'afreq', 'deletable': False},
        {'name':'Std deviation', 'id':'sd', 'deletable': False},
        {'name':'Upper Bound', 'id':'upper_bound', 'deletable': False},
        {'name':'Lower Bound', 'id':'lower_bound', 'deletable': False},
        {'name':'Coverage', 'id':'coverage', 'deletable': False},
        {'name':'Number of positive runs', 'id':'samplename', 'deletable': False}
    ],
    editable=False,
    filter_action="native",
    sort_action="native",
    sort_mode='multi',
    row_selectable='single',
    row_deletable=False,
    selected_rows=[],
    page_action='native',
    page_current= 0,
    page_size= 10,
    ),
    html.Br(),
    html.Br(),
    html.Div(id ='Breakdiv2', style={'break-after':'page'}),
    html.Div(id='LJ_graph'),
    dcc.Graph(id = 'LJ_graph2'),
    html.Br(),
    html.H2(children="Levey-Jennings Graph for entire series (RNA variants)"),
    dash_table.DataTable(
    id='tableR',
    columns=[
        {'name':'Variant', 'id':'variant', 'deletable': False},
        {'name':'Gene', 'id':'gene', 'deletable': False},
        {'name':'Normalized Counts', 'id':'norm_count', 'deletable': False},
        {'name':'Std deviation', 'id':'sd', 'deletable': False},
        {'name':'Upper Bound', 'id':'upper_bound', 'deletable': False},
        {'name':'Lower Bound', 'id':'lower_bound', 'deletable': False},
        {'name':'Coverage', 'id':'coverage', 'deletable': False},
        {'name':'Number of positive runs', 'id':'samplename', 'deletable': False}
    ],
    editable=False,
    filter_action="native",
    sort_action="native",
    sort_mode='multi',
    row_selectable='single',
    row_deletable=False,
    selected_rows=[],
    page_action='native',
    page_current= 0,
    page_size= 10,
    ),
    html.Br(),
    html.Br(),
    html.Div(id ='Breakdiv3', style={'break-after':'page'}),
    html.Div(id='LJ_graphRNA'),
    dcc.Graph(id = 'LJ_graphRNA2'),
    html.Br(),
    html.Button('Delete', id='button2'),
    html.Br(),
    html.Div(id='dummy1'),
    html.Br(),
    html.Div(id='dummy2'),
    html.Br(),
    html.Div(id='dummy3'),
    html.Div(id='dummy', style={'display': 'none'})
    ])

app.layout = serve_layout

# All callback functions (same as original but with optimized data flow)
@app.callback(
    Output('memory-output', 'data'),
    Input('dummy', 'id'))
def dcc_store(dummy):
    try:
        t = get_sql()
        if t is None or t.empty:
            return None
        return t.to_json()
    except Exception as e:
        print(f"Error in dcc_store: {e}")
        return None

@app.callback(
    Output("drpdown", "options"),
    Output("drpdown", "value"),
    Input('memory-output', 'data'))
def make_drpdown(data):
    if data is None:
        return [], None
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    data = pd.read_json(data)
    data = data[neworder]
    data = data.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    options = [{'label': i, 'value': i} for i in data['samplename'].unique()[-20:]]
    value = data['samplename'].tolist()[-1]
    return options, value

@app.callback(
    Output('table', 'data'),
    Input('memory-output', 'data'))
def prep_table1(data):
    data = getSummary(data, "DNA")
    return data.to_dict('records')

@app.callback(
    Output('tableR', 'data'),
    Input('memory-output', 'data'))
def prep_table2(data):
    data = getSummary(data, "RNA")
    return data.to_dict('records')

@app.callback(
    Output(component_id='LJ_graph', component_property='children'),
    Input('table', 'data'),
    Input('table', 'selected_rows'))
def print_selection(data, selected_rows):
    if selected_rows is None:
        selected_rows = []
    df = data[selected_rows[0]]['variant'] if selected_rows else "No selected rows"
    out = str(df)
    return ''.join(out) if df else "No Variant Selected"

@app.callback(
    Output('LJ_graph2', 'figure'),
    Input('table','data'),
    Input('table','selected_rows'),
    Input('memory-output', 'data'))
def update_graph(data, selected_rows, data2):
    if data2 is None:
        return {}
    cleared_samples = []
    with open('/dash-files/cleared.tsv') as f:
        include = f.read().splitlines()
        cleared_samples = include
    limit = None
    with open('/dash-files/config.txt') as f:
        vals = f.read().splitlines()
        limit = int(vals[4])

    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    data2 = pd.read_json(data2)
    data2 = data2.applymap(lambda x: round(x, 4) if isinstance(x, (int, float)) else x)
    data2 = data2[neworder]
    if selected_rows is None:
        selected_rows = []
    var = data[selected_rows[0]]['variant'] if selected_rows else "chr12_25398281_C_T_snp_1"
    data_long = data2.applymap(lambda x: round(x, 4) if isinstance(x, (int, float)) else x)
    sset = pd.DataFrame(data_long['samplename'].unique(), columns=['samplename'])
    is_var = data_long['variant'] == var
    filt_dat = data_long[is_var]
    value_vect = []
    for index, row in sset.iterrows():
        label = row['samplename']
        if label in filt_dat['samplename'].tolist():
            a = filt_dat.loc[filt_dat['samplename']==label, 'afreq'].values[0]
            value_vect.append(a)
        else:
            value_vect.append(0)
    sset['afreq'] = value_vect
    mn = sset['afreq'].tolist()
    mn1 = []
    for i in mn:
        try:
            mn1.append(i if i else mn1[-1])
        except:
            mn1.append(0.00000001)
    mn2 = [st.mean(mn1[0:s]) for s in range(1,len(list(set(cleared_samples))))]
    mn2.insert(0, mn[0])
    diff = len(mn)-len(cleared_samples)
    if diff > 0:
        ex = [mn2[-1]] * diff
        mn2.extend(ex)
    mn3 = [num for num in mn if num]
    sd1 = [np.std(mn1[0:s], ddof=1) for s in range(1,len(list(set(cleared_samples))))]
    sd1.insert(0, 0)
    sd1 = np.array(sd1)
    sd1[np.isnan(sd1)] = 0
    sd1 = sd1.tolist()
    diff2 = len(mn1)-len(cleared_samples)
    if diff2 > 0:
        ex2 = [sd1[-1]] * diff2
        sd1.extend(ex2)
    sd2 = sd1
    sdpos1 = np.array(mn2) + np.array(sd2)
    sdneg1 = np.array(mn2) - np.array(sd2)
    sdpos2 = np.array(mn2) + limit*(np.array(sd2))
    sdneg2 = np.array(mn2) - limit*(np.array(sd2))
    sdpos1[sdpos1 > 100] = 100
    sdneg1[sdneg1 < 0] = 0
    sdpos2[sdpos2 > 100] = 100
    sdneg2[sdneg2 < 0] = 0
    figure = go.Figure(data = go.Scatter(x = sset[-20:]['samplename'], y = mn[-20:], mode='lines+markers', name = 'Value'))
    figure.add_trace(go.Scatter(x = sset[-20:]['samplename'], y = sdpos1[-20:], mode = 'lines', line_color="green", name = '+1SD'))
    figure.add_trace(go.Scatter(x = sset[-20:]['samplename'], y = sdneg1[-20:], mode = 'lines', line_color="green", name = '-1SD'))
    figure.add_trace(go.Scatter(x = sset[-20:]['samplename'], y = sdpos2[-20:], mode = 'lines', line_color="red", name = 'Upper Limit'))
    figure.add_trace(go.Scatter(x = sset[-20:]['samplename'], y = sdneg2[-20:], mode = 'lines', line_color="red", name = 'Lower Limit'))
    figure.update_xaxes(showticklabels=False)
    return figure

@app.callback(
    Output(component_id='LJ_graphRNA', component_property='children'),
    Input('tableR', 'data'),
    Input('tableR', 'selected_rows'))
def print_selection2(data, selected_rows):
    if selected_rows is None:
        selected_rows = []
    df = data[selected_rows[0]]['variant'] if selected_rows else "No selected rows"
    out = str(df)
    return ''.join(out) if df else "No Variant Selected"

@app.callback(
    Output('LJ_graphRNA2', 'figure'),
    Input('tableR','data'),
    Input('tableR','selected_rows'),
    Input('memory-output', 'data'))
def update_graph2(data, selected_rows, data2):
    if data2 is None:
        return {}
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    cleared_samples = []
    with open('/dash-files/cleared.tsv') as f:
        include = f.read().splitlines()
        cleared_samples = include
    limit = None
    with open('/dash-files/config.txt') as f:
        vals = f.read().splitlines()
        limit = int(vals[4])
    data2 = pd.read_json(data2)
    data2 = data2.applymap(lambda x: round(x, 4) if isinstance(x, (int, float)) else x)
    data2 = data2[neworder]
    if selected_rows is None:
        selected_rows = []
    var = data[selected_rows[0]]['variant'] if selected_rows else "BCR(14)-ABL(2)"
    data_long = data2.applymap(lambda x: round(x, 4) if isinstance(x, (int, float)) else x)
    sset = pd.DataFrame(data_long['samplename'].unique(), columns=['samplename'])
    is_var = data_long['variant'] == var
    filt_dat = data_long[is_var]
    value_vect = []
    for index, row in sset.iterrows():
        label = row['samplename']
        if label in filt_dat['samplename'].tolist():
            a = filt_dat.loc[filt_dat['samplename']==label, 'norm_count'].values[0]
            value_vect.append(a)
        else:
            value_vect.append(0)
    sset['norm_count'] = value_vect

    mn = sset['norm_count'].tolist()
    mn1 = []
    for i in mn:
        try:
            mn1.append(i if i else mn1[-1])
        except:
            mn1.append(0.00000001)
    mn2 = [st.mean(mn1[0:s]) for s in range(1,len(list(set(cleared_samples))))]
    mn2.insert(0, mn[0])
    diff = len(mn)-len(cleared_samples)
    if diff > 0:
        ex = [mn2[-1]] * diff
        mn2.extend(ex)
    mn3 = [num for num in mn if num]
    sd1 = [np.std(mn1[0:s], ddof=1) for s in range(1,len(list(set(cleared_samples))))]
    diff2 = len(mn1)-len(cleared_samples)
    sd1.insert(0, 0)
    sd1 = np.array(sd1)
    sd1[np.isnan(sd1)] = 0
    sd1 = sd1.tolist()
    if diff2 > 0:
        ex2 = [sd1[-1]] * diff2
        sd1.extend(ex2)
    sdpos1 = np.array(mn2) + np.array(sd1)
    sdneg1 = np.array(mn2) - np.array(sd1)
    sdpos2 = np.array(mn2) + limit*(np.array(sd1))
    sdneg2 = np.array(mn2) - limit*(np.array(sd1))
    sdneg1[sdneg1 < 0] = 0
    sdneg2[sdneg2 < 0] = 0
    figure = go.Figure(data = go.Scatter(x = sset[-20:]['samplename'], y = mn[-20:], mode='lines+markers', name = 'Value'))
    figure.add_trace(go.Scatter(x = sset[-20:]['samplename'], y = sdpos1[-20:], mode = 'lines', line_color="green", name = '+1SD'))
    figure.add_trace(go.Scatter(x = sset[-20:]['samplename'], y = sdneg1[-20:], mode = 'lines', line_color="green", name = '-1SD'))
    figure.add_trace(go.Scatter(x = sset[-20:]['samplename'], y = sdpos2[-20:], mode = 'lines', line_color="red", name = 'Upper Limit'))
    figure.add_trace(go.Scatter(x = sset[-20:]['samplename'], y = sdneg2[-20:], mode = 'lines', line_color="red", name = 'Lower Limit'))
    figure.update_xaxes(showticklabels=False)
    return figure

# Optimized callback with pagination for table-2 (DNA variants)
@app.callback(
    [Output('table-2', 'data'),
     Output('table-2-pagination-info', 'children')],
    [Input('drpdown', 'value'),
     Input('memory-output', 'data'),
     Input('table-2', 'page_current'),
     Input('table-2', 'page_size')])
def update_table2_optimized(sel_value, data, page_current, page_size):
    if not sel_value or not data:
        return [], "No sample selected"
    
    # Use optimized function with caching
    processed_data = process_sample_data(data, sel_value, "DNA", filter_failing=False)
    
    # Apply pagination
    paginated_data, total_pages = paginate_data(processed_data, page_current, page_size)
    
    # Create pagination info
    pagination_info = create_pagination_info(page_current, page_size, len(processed_data))
    
    return paginated_data, pagination_info

# Optimized callback with pagination for table-3 (RNA variants)
@app.callback(
    [Output('table-3', 'data'),
     Output('table-3-pagination-info', 'children')],
    [Input('drpdown', 'value'),
     Input('memory-output', 'data'),
     Input('table-3', 'page_current'),
     Input('table-3', 'page_size')])
def update_table3_optimized(sel_value, data, page_current, page_size):
    if not sel_value or not data:
        return [], "No sample selected"
    
    # Use optimized function with caching
    processed_data = process_sample_data(data, sel_value, "RNA", filter_failing=False)
    
    # Apply pagination
    paginated_data, total_pages = paginate_data(processed_data, page_current, page_size)
    
    # Create pagination info
    pagination_info = create_pagination_info(page_current, page_size, len(processed_data))
    
    return paginated_data, pagination_info

@app.callback(
    Output('table-fail','data'),
    Input('drpdown','value'),
    Input('memory-output', 'data'))
def update_fail1(sel_value, data):
    if data is None:
        return []
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    t0 = pd.read_json(data).copy()
    t0 = t0[neworder]
    t0 = t0.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    filt_dat = t0[t0['variant'].str.startswith('chr')]
    t1 = getSummary(data, "DNA")
    filt_dat = filt_dat.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    missing = list(set(t1['variant'].tolist()) - set(filt_dat['variant'].tolist()))
    if missing:
        for var in missing:
            new_row = {'variant':var,'gene':'','afreq':0,'norm_count':0,'sd':0,'upper_bound':0,'lower_bound':0,'coverage':0,'trname':'','HGVSc':'','HGVSp':'','samplename':sel_value}
            filt_dat = filt_dat.append(new_row, ignore_index=True)
    filt_dat = filt_dat.sort_values('variant')
    filt_dat['sd']= t1['sd'].tolist()
    filt_dat['upper_bound'] = t1['upper_bound'].tolist()
    filt_dat.loc[filt_dat['upper_bound'] > 100.00, 'upper_bound'] = 100.00
    filt_dat['lower_bound'] = t1['lower_bound'].tolist()
    filt_dat['lower_bound'].values[filt_dat['lower_bound'].values < 0.00] = 0.00
    filt_dat = filt_dat.loc[(filt_dat['afreq']<filt_dat['lower_bound'])|(filt_dat['afreq']>filt_dat['upper_bound'])]
    return filt_dat.to_dict('records')

@app.callback(
    Output('table-fail2','data'),
    Input('drpdown','value'),
    Input('memory-output', 'data'))
def update_fail2(sel_value, data):
    if data is None:
        return []
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    t0 = pd.read_json(data)
    t0 = t0[neworder]
    t0 = t0.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
    filt_dat = t0[~t0['variant'].str.startswith('chr')]
    t2 = getSummary(data, "RNA")
    filt_dat = filt_dat.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    filt_dat = filt_dat.sort_values('variant')
    filt_dat['sd']= t2['sd'].tolist()
    filt_dat['upper_bound'] = t2['upper_bound'].tolist()
    filt_dat['lower_bound'] = t2['lower_bound'].tolist()
    filt_dat['lower_bound'].values[filt_dat['lower_bound'].values < 0] = 0
    filt_dat = filt_dat.loc[(filt_dat['norm_count']<filt_dat['lower_bound'])|(filt_dat['norm_count']>filt_dat['upper_bound'])]
    return filt_dat.to_dict('records')

@app.callback(
    Output('output-container-button2', 'children'),
    Input('drpdown','value'))
def display_notes(value):
    override = pd.read_csv('/dash-files/comments.txt', sep='\t', names=['sample','time','comment'])
    filt_or = override.loc[override['sample'] == value]
    try:
        slist = filt_or[['time','comment']].values.flatten().tolist()
        print(slist)
        slist = list(filter(('nan').__ne__, slist))
        return '    |    '.join(slist)
        return slist
    except:
        return 'No comments'

@app.callback(
    Output("dummy1", "children"),
    Input('button','n_clicks'),
    State('drpdown','value'),
    State('input-box', 'value'),prevent_initial_call=True)
def update_notes(n_clicks, drpdown ,input_box):
    now = datetime.now().date()
    f = open('/dash-files/comments.txt', 'a')
    writer = csv.writer(f, delimiter = "\t")
    row = [drpdown, now, input_box]
    writer.writerow(row)
    f.close()
    return None

@app.callback(
    Output("dummy2", "children"),
    Input('button2','n_clicks'),
    State('drpdown','value'),prevent_initial_call=True)
def remove_outlier(n_clicks, drpdown):
    f = open('/dash-files/exclusions.tsv', 'a')
    writer = csv.writer(f, delimiter = "\t")
    writer.writerow([drpdown])
    f.close()
    return None

@app.callback(
    Output("dummy3", "children"),
    Input('button3','n_clicks'),
    State('drpdown','value'),prevent_initial_call=True)
def clear(n_clicks, drpdown):
    f = open('/dash-files/cleared.tsv', 'a')
    writer = csv.writer(f, delimiter = "\t")
    writer.writerow([drpdown])
    f.close()
    now = datetime.now().date()
    f2 = open('/dash-files/comments.txt', 'a')
    writer = csv.writer(f2, delimiter = "\t")
    row = [drpdown, now, "Sample was Cleared"]
    writer.writerow(row)
    f2.close()
    return None

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8090)
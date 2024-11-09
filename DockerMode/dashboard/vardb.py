#!/usr/bin/env python3

#works OK updates seem to be linked to the DB wen pressing refresh button. 


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


#read the data from the mysql database with the hd200 samples
def get_sql():
    start =time.time()
    #Use MySQL Connector for establishing link to DB in function, so that we may update live to the user
    mydb = mysql.connector.connect(host='db', database = 'vardb',user="usr", passwd='usrpass')
    exclusions = []
    with open('/dash-files/exclusions.tsv') as f:
        exclude = f.read().splitlines()
        exclusions = exclude
    print(exclusions)
    query = "SELECT CallData.pass_filter,  CallData.afreq,  CallData.coverage,  CallData.norm_count,  CallData.sample, VarData.name, RunInfo.IonWF_version, RunInfo.name, RunInfo.filedate, Transcripts.name , HGVS.transcript, HGVS.HGVSc, HGVS.HGVSp, Genes.name FROM VarData LEFT JOIN HGVS ON HGVS.id = VarData.hgvs LEFT JOIN CallData ON VarData.id = CallData.variant LEFT JOIN RunInfo ON CallData.sample = RunInfo.id LEFT JOIN Transcripts ON Transcripts.id = HGVS.transcript LEFT JOIN Genes ON VarData.gene = Genes.id;"
    df = pd.read_sql(query,mydb)
    mydb.close()

    #read-in data and change duplicated column headers
    df.columns = ['pass_filter','afreq','coverage','norm_count','sample','variant','IonWF_version','samplename','filedate','trname','transcript','HGVSc', 'HGVSp','gene']

    #get only HD200 and seracare samples
    df = df[~df['samplename'].isin(exclusions)]
    #Get the variants of interest
    regions = []
    with open('/dash-files/regions.txt') as f:
        region = f.read().splitlines()
        regions = region
    #print(regions)

    ####needs to be read in from a BED file if possible
    df = df[df['variant'].isin(regions)]
    #with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #    print(df)
    #Change fusion gene names to something more interpretable
    #Getting precise coordinates and SQL variant names can be done by using the following command in bash:

    #mysql -u eallain -p -e "USE HD200_database; SELECT  CallData.genotype,  CallData.geno_qual,  CallData.pass_filter,  CallData.afreq,  CallData.coverage,  CallData.norm_count,  CallData.sample, VarData.name, RunInfo.IonWF_version FROM  CallData  JOIN VarData ON VarData.id = CallData.variant JOIN RunInfo ON RunInfo.id = CallData.sample;" > dash_variant_data.txt

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

    #You can isolate specifiic workflows
    #df = df.loc[df['IonWF_version'] == 1]

    #Sort by date
    df = df.sort_values(["filedate","variant"])
    df = df.reset_index(drop=True)

    limit = None

    with open('/dash-files/config.txt') as f: # get the cleared samples
        vals = f.read().splitlines()
        limit = int(vals[4])

    #Drop uninformative columns, add stdev for numerical values and group the entire table by variant. means and modes are used, except the samples names, which are the sum of unique names. 
    tabledf = df.drop(labels=['IonWF_version','pass_filter','transcript'], axis =1)
    tabledf['afreq'] = tabledf['afreq'].fillna(0)
    tabledf['afreq'] = tabledf['afreq'].astype(float)
    tabledf['afreq'] = 100*(tabledf['afreq'])
    tabledf['norm_count'] = tabledf['norm_count'].fillna(0)
    tabledf['norm_count'] = 1000000*(tabledf['norm_count'])
    tabledf['afreq_normcount'] = tabledf['afreq'] + tabledf['norm_count']
    tabledf['sd'] = tabledf.groupby('variant').afreq_normcount.transform('std')
    tabledf['upper_bound'] = tabledf['afreq_normcount'] + limit*(tabledf['sd']) #This sets your hard reject limits based on the integer in the config files 5th line.
    tabledf['lower_bound'] = tabledf['afreq_normcount'] - limit*(tabledf['sd'])
    tabledf = tabledf.drop('afreq_normcount', axis=1)
    print(time.time()-start)
    return(tabledf)

#initial call for the database query
#DB = get_sql()

def getSummary(data, bioMolecule): #function to summarize statistics on cleared samples
    cleared_samples = []
    with open('/dash-files/cleared.tsv') as f: # get the cleared samples
        include = f.read().splitlines()
        cleared_samples = include
    limit = None
    with open('/dash-files/config.txt') as f: # get the cleared samples
        vals = f.read().splitlines()
        limit = int(vals[4])
    if bioMolecule == "DNA":
        neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        #data = data[neworder]
        t0 = pd.read_json(data)
        t0 = t0[neworder]
        t0 = t0.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
        #get only data with cleared samples
        summarizedData = t0[t0['samplename'].isin(cleared_samples)]
        #recalculate means, sd and limits
        summarizedData['sd'] = summarizedData.groupby('variant').afreq.transform('std')
        summarizedData['upper_bound'] = summarizedData['afreq'] + limit*(summarizedData['sd'])
        summarizedData['lower_bound'] = summarizedData['afreq'] - limit*(summarizedData['sd'])
        summarizedData = summarizedData.groupby('variant', as_index=False).agg({'samplename': 'nunique', 'coverage': ['mean'], 'afreq': ['mean'], 'trname': lambda x: scipy.stats.mode(x)[0], 'HGVSc': lambda x: scipy.stats.mode(x)[0], 'HGVSp':lambda x: scipy.stats.mode(x)[0], 'gene': lambda x: scipy.stats.mode(x)[0], 'sd': ['mean'], 'upper_bound': ['mean'], 'lower_bound':['mean']})
        summarizedData.columns = summarizedData.columns.droplevel(1)
        neworder1 = ['variant','gene','afreq','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        summarizedData = summarizedData[neworder1]
        summarizedData = summarizedData[summarizedData['variant'].str.startswith('chr')]
        summarizedData = summarizedData.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        ######
        summarizedData.loc[summarizedData['upper_bound'] > 100.00, 'upper_bound'] = 100.00 # AF cant be higher than 100
        summarizedData['lower_bound'].values[summarizedData['lower_bound'].values < 0.00] = 0.00 #AF cant be lower than 0
        return(summarizedData)
    if bioMolecule == "RNA":
        neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        #data = data[neworder]
        t0 = pd.read_json(data)
        t0 = t0[neworder]
        t0 = t0.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
        #get only data with cleared samples
        summarizedData = t0[t0['samplename'].isin(cleared_samples)]
        #recalculate means, sd and limits
        summarizedData['sd'] = summarizedData.groupby('variant').norm_count.transform('std')
        summarizedData['upper_bound'] = summarizedData['norm_count'] + limit*(summarizedData['sd'])
        summarizedData['lower_bound'] = summarizedData['norm_count'] - limit*(summarizedData['sd'])
        summarizedData = summarizedData.groupby('variant', as_index=False).agg({'samplename': 'nunique', 'coverage': ['mean'], 'norm_count': ['mean'], 'trname': lambda x: scipy.stats.mode(x)[0], 'HGVSc': lambda x: scipy.stats.mode(x)[0], 'HGVSp':lambda x: scipy.stats.mode(x)[0], 'gene': lambda x: scipy.stats.mode(x)[0], 'sd': ['mean'], 'upper_bound': ['mean'], 'lower_bound':['mean']})
        summarizedData.columns = summarizedData.columns.droplevel(1)
        neworder1 = ['variant','gene','norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
        summarizedData = summarizedData[neworder1]
        summarizedData = summarizedData[~summarizedData['variant'].str.startswith('chr')]
        summarizedData = summarizedData.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        ######
        summarizedData['lower_bound'].values[summarizedData['lower_bound'].values < 0] = 0
        return(summarizedData)



#create the app layout
app = dash.Dash(__name__)
server = app.server

######################
#VALID_USERNAME_PASSWORD_PAIRS = { # login credentials
#    'ABC': 'XYZ'
#}

#auth = dash_auth.BasicAuth(
#    app,
#    VALID_USERNAME_PASSWORD_PAIRS
#)
#Avoid global variables, instead store in empty divs


#defining the layout
def serve_layout():
    #Customizable thresholds
    sig_tab = pd.DataFrame({'Field':["QC Blanks","Coverage > 800","Uniformity > 80%","Lot Number","PhD", "MD"],'Value':["PASS  /  FAIL","PASS  /  FAIL","PASS  /  FAIL","___________________________________________________" ,"___________________________________________________","___________________________________________________"]})
    return html.Div(children=[
    dcc.Store(id='memory-output'),
    #First is a title 
    #Then a datatable with selectable rows for later graphs with callback
    html.H1(children="MGDB control monitoring"),
    html.Br(),
    dcc.Dropdown(id = 'drpdown'), # options = [{'label': i, 'value': i} for i in t0['samplename'].unique()[-20:]], value = t0['samplename'].tolist()[-1]), # dropdown menu to pick sample for analysis
    html.H2(children="DNA Variants not passing QC verification:"),
    dash_table.DataTable(id = 'table-fail', # table for small variants not passing QC
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
    dash_table.DataTable(id = 'table-fail2', #this is the RNA-based summary of only variants not passing QC
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
    dash_table.DataTable(id = 'table-signature', data=sig_tab.to_dict('records'), css=[{ # table with signature lines, etc. for printing. 
            'selector': 'tr:first-child',
            'rule':'''
                    display: None;
            '''
        }]),
    html.Br(),
    # add the conditionnal styling to allele frequencies that are out-of-bounds (3SD)
    html.Div(id='output-container-button2',children='No comments to display'),
    html.Br(),
    html.Div(dcc.Input(id='input-box', type='text')), #input box for comments
    html.Button('Submit Comment', id='button'),
    html.Br(),
    html.Button('Validate Sample - Include in DB', id='button3'),
    html.Br(),
    html.Div(id='newlines-container',children='\n\n\n\n'),
    html.Br(),
    html.Div(id ='Breakdiv', style={'break-after':'page'}),
    html.Br(),
    html.H2(children="Complete table of run info for current sample (DNA variants)"),
    dash_table.DataTable(id = 'table-2',
        columns=[{'name':'Variant', 'id':'variant', 'deletable': False},
                 {'name':'Gene', 'id':'gene', 'deletable': False},
                 {'name':'Allele Frequency', 'id':'afreq', 'deletable': False},
                 {'name':'Std deviation', 'id':'sd', 'deletable': False},
                 {'name':'Upper Bound', 'id':'upper_bound', 'deletable': False},
                 {'name':'Lower Bound', 'id':'lower_bound', 'deletable': False},
                 {'name':'Coverage', 'id':'coverage', 'deletable': False}
                 ],
        page_size=10,
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
    dash_table.DataTable(id = 'table-3', # for RNA
        columns=[
        {'name':'Variant', 'id':'variant', 'deletable': False},
        {'name':'Gene', 'id':'gene', 'deletable': False},
        {'name':'Normalized Counts', 'id':'norm_count', 'deletable': False},
        {'name':'Std deviation', 'id':'sd', 'deletable': False},
        {'name':'Upper Bound', 'id':'upper_bound', 'deletable': False},
        {'name':'Lower Bound', 'id':'lower_bound', 'deletable': False},
        {'name':'Coverage', 'id':'coverage', 'deletable': False}
        ],
        page_size=5,
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
    #dcc.Graph(id = 'subplot-div', style={'width': '250vh'}),
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
    #This to_dict function adds a level to column headers, making them tuples if not dropped after using groupby. See above.
    #data=t1.to_dict('records'),
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
    #This to_dict function adds a level to column headers, making them tuples if not dropped after using groupby. See above.
    #data=t2.to_dict('records'),
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
    html.Button('Delete', id='button2'), # Delete will add to a list of exclusions that filters out any unwanted data when reading in from SQL
    html.Br(),
    html.Div(id='dummy1'),
    html.Br(),
    html.Div(id='dummy2'),
    html.Br(),
    html.Div(id='dummy3'),
    html.Div(id='dummy', style={'display': 'none'})
    ])

app.layout = serve_layout




#Callbacks and functions

#Store the data in a dummy div
@app.callback(
    ServersideOutput('memory-output', 'data'),
    Input('dummy', 'id'))

def dcc_store(dummy):
    t = get_sql()
    return t.to_json()

#Make the dropdown menu

@app.callback(
    Output("drpdown", "options"),
    Output("drpdown", "value"),
    Input('memory-output', 'data'))

def make_drpdown(data):
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    data = pd.read_json(data)
    data = data[neworder]
    data = data.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    options = [{'label': i, 'value': i} for i in data['samplename'].unique()[-20:]]
    value = data['samplename'].tolist()[-1]
    return options, value

# Make the tables with all data from validated samples

@app.callback(
    Output('table', 'data'),
    Input('memory-output', 'data'))

def prep_table1(data):
    data = getSummary(data, "DNA")
    return data.to_dict('records')

#Same, but for RNA

@app.callback(
    Output('tableR', 'data'),
    Input('memory-output', 'data'))

def prep_table2(data):
    data = getSummary(data, "RNA")
    return data.to_dict('records')


#Function for printing the active variant on the screen
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

#now for the first LJ graph

@app.callback(
    Output('LJ_graph2', 'figure'), #outputs to plotly figure
    Input('table','data'), # gets data from the table
    Input('table','selected_rows'), # gets the seleccted active row
    Input('memory-output', 'data')) #Gets the stored empty-div dataframe

def update_graph(data, selected_rows, data2):
    cleared_samples = []
    with open('/dash-files/cleared.tsv') as f: # get the cleared samples
        include = f.read().splitlines()
        cleared_samples = include
    limit = None
    with open('/dash-files/config.txt') as f: # get the cleared samples
        vals = f.read().splitlines()
        limit = int(vals[4])

    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    data2 = pd.read_json(data2)
    data2 = data2.applymap(lambda x: round(x, 4) if isinstance(x, (int, float)) else x)
    data2 = data2[neworder]
    if selected_rows is None:
        selected_rows = []
    var = data[selected_rows[0]]['variant'] if selected_rows else "chr12_25398281_C_T_snp_1" #default selection
    data_long = data2.applymap(lambda x: round(x, 4) if isinstance(x, (int, float)) else x)
    sset = pd.DataFrame(data_long['samplename'].unique(), columns=['samplename']) # required to get null value samples
    is_var = data_long['variant'] == var #get only the active variant
    filt_dat = data_long[is_var]
    value_vect = [] # stores the sample-wise values for Afreq to check if missing samples.
    for index, row in sset.iterrows(): #find only the non-null AFs
        label = row['samplename']
        if label in filt_dat['samplename'].tolist():
            a = filt_dat.loc[filt_dat['samplename']==label, 'afreq'].values[0]
            value_vect.append(a)
        else:
            value_vect.append(0)
    sset['afreq'] = value_vect
    mn = sset['afreq'].tolist() # convert the AFs to a list
    mn1 = []
    for i in mn: #need this try to catch instances of first-samples being zero AF runs...
        try:
            mn1.append(i if i else mn1[-1])
        except: # if is the case, then use veryvery small number in lieu of 0
            mn1.append(0.00000001)
    mn2 = [st.mean(mn1[0:s]) for s in range(1,len(list(set(cleared_samples))))] # calculate the rolling average
    mn2.insert(0, mn[0])
    diff = len(mn)-len(cleared_samples)
    if diff > 0:
        ex = [mn2[-1]] * diff
        mn2.extend(ex)
    mn3 = [num for num in mn if num]
    sd1 = [np.std(mn1[0:s], ddof=1) for s in range(1,len(list(set(cleared_samples))))] # get the upper and lower limits for the graph (ommiting the last value and instead adding the n-1th value twice)
    sd1.insert(0, 0)
    sd1 = np.array(sd1)
    sd1[np.isnan(sd1)] = 0
    sd1 = sd1.tolist()
    diff2 = len(mn1)-len(cleared_samples)
    if diff2 > 0:
        ex2 = [sd1[-1]] * diff2
        sd1.extend(ex2)
    ############
    sd2 = sd1 #Need this to calculate the correct SD while plotting zeroes without having our 3SD intervals stop prematurely
    sdpos1 = np.array(mn2) + np.array(sd2) # calculate limits for rolling average and dynamic SDs
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

#Function for printing the active variant on the screen for RNA
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

#Second graph

@app.callback(
    Output('LJ_graphRNA2', 'figure'), #outputs to plotly figure
    Input('tableR','data'), # gets data from the table
    Input('tableR','selected_rows'), # gets the seleccted active row
    Input('memory-output', 'data')) #Gets the stored empty-div dataframe

def update_graph2(data, selected_rows, data2):
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    cleared_samples = []
    with open('/dash-files/cleared.tsv') as f: # get the cleared samples
        include = f.read().splitlines()
        cleared_samples = include
    limit = None
    with open('/dash-files/config.txt') as f: # get the cleared samples
        vals = f.read().splitlines()
        limit = int(vals[4])
    data2 = pd.read_json(data2)
    data2 = data2.applymap(lambda x: round(x, 4) if isinstance(x, (int, float)) else x)
    data2 = data2[neworder]
    if selected_rows is None:
        selected_rows = []
    var = data[selected_rows[0]]['variant'] if selected_rows else "BCR(14)-ABL(2)" #default selection
    data_long = data2.applymap(lambda x: round(x, 4) if isinstance(x, (int, float)) else x)
    sset = pd.DataFrame(data_long['samplename'].unique(), columns=['samplename']) # required to get null value samples
    is_var = data_long['variant'] == var #get only the active variant
    filt_dat = data_long[is_var]
    value_vect = [] # stores the sample-wise values for Afreq to check if missing samples.
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
    for i in mn: #need this try to catch instances of first-samples being zero AF runs...
        try:
            mn1.append(i if i else mn1[-1])
        except: # if is the case, then use veryvery small number in lieu of 0
            mn1.append(0.00000001)
    mn2 = [st.mean(mn1[0:s]) for s in range(1,len(list(set(cleared_samples))))]
    mn2.insert(0, mn[0])
    diff = len(mn)-len(cleared_samples)
    if diff > 0:
        ex = [mn2[-1]] * diff
        mn2.extend(ex)
    mn3 = [num for num in mn if num]
    sd1 = [np.std(mn1[0:s], ddof=1) for s in range(1,len(list(set(cleared_samples))))] # get the upper and lower limits for the graph (ommiting the last value and instead adding the n-1th value twice)
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


#The table describing all DNA variants for a selected run below the sample failures description 

@app.callback(
    Output('table-2','data'), #plot table
    Input('drpdown','value'), #get active sample from dropdown
    Input('memory-output', 'data')) # get table 2 from dummy div

def update_table2(sel_value, data):
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    t0 = pd.read_json(data).copy()
    t0 = t0[neworder]
    t0 = t0.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
    filt_dat = t0[t0['variant'].str.startswith('chr')]
    t1 = getSummary(data, "DNA")
    filt_dat = filt_dat.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    missing = list(set(t1['variant'].tolist()) - set(filt_dat['variant'].tolist()))
    if missing:
        for var in missing:
            new_row = {'variant':var,'gene':'','afreq':0,'norm_count':0,'sd':0,'upper_bound':0,'lower_bound':0,'coverage':0,'trname':'','HGVSc':'','HGVSp':'','samplename':sel_value}
            filt_dat = filt_dat.append(new_row, ignore_index=True)
    filt_dat['sd']= t1['sd'].tolist()
    filt_dat = filt_dat.sort_values('variant')
    filt_dat['upper_bound'] = t1['upper_bound'].tolist()
    filt_dat.loc[filt_dat['upper_bound'] > 100.00, 'upper_bound'] = 100.00 # AF cant be higher than 100
    filt_dat['lower_bound'] = t1['lower_bound'].tolist()
    filt_dat['lower_bound'].values[filt_dat['lower_bound'].values < 0.00] = 0.00 #AF cant be lower than 0
    return filt_dat.to_dict('records')

#The table describing all RNA variants for a selected run below the sample failures description

@app.callback(
    Output('table-3','data'), #plot table
    Input('drpdown','value'), #get active sample from dropdown
    Input('memory-output', 'data')) #get data from dummy div

def update_table3(sel_value, data):  #too slow and need a store for the raw sql call - this needs the same SD tweaks as the fail1 table
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    #data = data[neworder]
    t0 = pd.read_json(data)
    t0 = t0[neworder]
    t0 = t0.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
    filt_dat = t0[~t0['variant'].str.startswith('chr')]
    t2 = getSummary(data, "RNA")
    filt_dat = filt_dat.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    filt_dat = filt_dat.sort_values('variant')
    filt_dat['sd']= t2['sd'].tolist()
    filt_dat['upper_bound'] = t2['upper_bound'].tolist()
    filt_dat['lower_bound'] = t2['lower_bound'].tolist()
    filt_dat['lower_bound'].values[filt_dat['lower_bound'].values < 0] = 0 #counts cant be lower than 0
    return filt_dat.to_dict('records')



#For the summary tables at top that show sample failure

@app.callback(
    Output('table-fail','data'), #plot table
    Input('drpdown','value'), #get active sample from dropdown
    Input('memory-output', 'data')) #get data from dummy div


def update_fail1(sel_value, data): ##### Table at the very top showing failures in current sample. Defaults to most recent sample.
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    t0 = pd.read_json(data).copy()
    t0 = t0[neworder]
    t0 = t0.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
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
    filt_dat.loc[filt_dat['upper_bound'] > 100.00, 'upper_bound'] = 100.00 # AF cant be higher than 100
    filt_dat['lower_bound'] = t1['lower_bound'].tolist()
    filt_dat['lower_bound'].values[filt_dat['lower_bound'].values < 0.00] = 0.00 #AF cant be lower than 0
    filt_dat = filt_dat.loc[(filt_dat['afreq']<filt_dat['lower_bound'])|(filt_dat['afreq']>filt_dat['upper_bound'])]
    return filt_dat.to_dict('records')

@app.callback(
    Output('table-fail2','data'), #plot table
    Input('drpdown','value'), #get active sample from dropdown
    Input('memory-output', 'data')) #get data from dummy div


def update_fail2(sel_value, data): # table at top for RNA
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename']
    #data = data[neworder]
    t0 = pd.read_json(data)
    t0 = t0[neworder]
    t0 = t0.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
    filt_dat = t0[~t0['variant'].str.startswith('chr')]
    t2 = getSummary(data, "RNA")
    filt_dat = filt_dat.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    filt_dat = filt_dat.sort_values('variant')
    filt_dat['sd']= t2['sd'].tolist()
    filt_dat['upper_bound'] = t2['upper_bound'].tolist()
    filt_dat['lower_bound'] = t2['lower_bound'].tolist()
    filt_dat['lower_bound'].values[filt_dat['lower_bound'].values < 0] = 0 #counts cant be lower than 0
    filt_dat = filt_dat.loc[(filt_dat['norm_count']<filt_dat['lower_bound'])|(filt_dat['norm_count']>filt_dat['upper_bound'])]
    return filt_dat.to_dict('records')





#Read the comments file and display the notes for a given sample

@app.callback(
    Output('output-container-button2', 'children'),
    Input('drpdown','value')) #this comment manager takes the dropdown value as input. 

def display_notes(value):
    override = pd.read_csv('/dash-files/comments.txt', sep='\t', names=['sample','time','comment']) #read the comments file to obtain any current comments on the sample.
    filt_or = override.loc[override['sample'] == value] #find the selected dropdown value in the frame
    try:
        slist = filt_or[['time','comment']].values.flatten().tolist()
        print(slist)
        slist = list(filter(('nan').__ne__, slist))
        return '    |    '.join(slist) #print comments
        return slist
    except:
        return 'No comments'

#Write comments in the comment box and submit them to save the notes for the current sample in dropdown

@app.callback(
    Output("dummy1", "children"), #needed for function, output really does to text file
    Input('button','n_clicks'),
    State('drpdown','value'), #see above, comment manager takes dropdown as input
    State('input-box', 'value'),prevent_initial_call=True)

def update_notes(n_clicks, drpdown ,input_box):
    now = datetime.now().date()
    f = open('/dash-files/comments.txt', 'a') # file to add comments to
    writer = csv.writer(f, delimiter = "\t")
    row = [drpdown, now, input_box] #row has the sample ID, the date and comments. 
    writer.writerow(row)
    f.close()
    return None

#DELETE button on screen will remove the selected dropdown sample from consideration in calculating statistics, refresh page to update graphs. 

@app.callback(
    Output("dummy2", "children"), #needed for function, output really does to text file
    Input('button2','n_clicks'),
    State('drpdown','value'),prevent_initial_call=True) #see above, comment manager takes dropdown as input

def remove_outlier(n_clicks, drpdown):
    #insert function to delete and refresh here
    f = open('/dash-files/exclusions.tsv', 'a')
    writer = csv.writer(f, delimiter = "\t")
    writer.writerow([drpdown])
    f.close()
    return None

#The Calidate button will validate the current sample, and if not already in the list of cleared samples will now be included in statistics, thus adjusting SDs and Means


@app.callback(
    Output("dummy3", "children"), #needed for function, output really does to text file
    Input('button3','n_clicks'),
    State('drpdown','value'),prevent_initial_call=True) #see above, comment manager takes dropdown as input

def clear(n_clicks, drpdown):
    #insert function to delete and refresh here
    f = open('/dash-files/cleared.tsv', 'a')
    writer = csv.writer(f, delimiter = "\t")
    writer.writerow([drpdown])
    f.close()
    now = datetime.now().date()
    f2 = open('/dash-files/comments.txt', 'a') # file to add comments to
    writer = csv.writer(f2, delimiter = "\t")
    row = [drpdown, now, "Sample was Cleared"] #row has the sample ID, the date and comments.
    #print(row)
    writer.writerow(row)
    f2.close()
    return None

#run on this server with IP

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8090)

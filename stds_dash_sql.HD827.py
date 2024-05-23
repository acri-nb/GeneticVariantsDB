#!/usr/bin/env python3

#works OK updates seem to be linked to the DB wen pressing refresh button. 


#Dependencies
import dash
import dash_auth
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash import dcc
from dash import html
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import plotly.express as px
import statistics as st
import mysql.connector
import time
from datetime import datetime
import csv




#read the data from the mysql database with the hd200 samples
def get_sql():
    #Use MySQL Connector for establishing link to DB in function, so that we may update live to the user
    mydb = mysql.connector.connect(host="localhost", database = 'HD827',user="####", passwd="####")
    with open('exclusions.tsv') as f:
        exclusions = f.readlines()
    query = "SELECT CallData.pass_filter,  CallData.afreq,  CallData.coverage,  CallData.norm_count,  CallData.sample, VarData.name, RunInfo.IonWF_version, RunInfo.name, RunInfo.filedate, Transcripts.name , HGVS.transcript, HGVS.HGVSc, HGVS.HGVSp, Genes.name FROM VarData LEFT JOIN HGVS ON HGVS.id = VarData.hgvs LEFT JOIN CallData ON VarData.id = CallData.variant LEFT JOIN RunInfo ON CallData.sample = RunInfo.id LEFT JOIN Transcripts ON Transcripts.id = HGVS.transcript LEFT JOIN Genes ON VarData.gene = Genes.id;"
    df = pd.read_sql(query,mydb)
    mydb.close()

    #read-in data and change duplicated column headers
    df.columns = ['pass_filter','afreq','coverage','norm_count','sample','variant','IonWF_version','samplename','filedate','trname','transcript','HGVSc', 'HGVSp','gene']

    #get only HD200 and seracare samples
    df = df[df['samplename'].str.contains("HD827_SSEQ|HD832_SSEQ", na=False)]
    df = df[~df['samplename'].isin(exclusions)]
    #Get the variants of interest

    df = df[df['variant'].isin(["chr1_115256530_G_T_snp_1",\
    "chr1_11181327_C_T_snp_1",\
    "chr1_17359676_C_A_snp_1",\
    "chr1_27056285_G_A_snp_1",\
    "chr1_27100181_C_T_snp_1",\
    "chr1_46738433_C_A_snp_1",\
    "chr1_65310489_T_C_snp_1",\
    "chr1_65312342_G_A_snp_1",\
    "chr1_65321388_G_A_snp_1",\
    "chr1_65325970_C_T_snp_1",\
    "chr1_115256530_G_T_snp_1",\
    "chr1_120458004_A_T_snp_1",\
    "chr1_120471800_G_A_snp_1",\
    "chr1_120477998_C_A_snp_1",\
    "chr1_156846233_G_A_snp_1",\
    "chr1_156846307_GC_G_del_1",\
    "chr1_156848995_C_T_snp_1",\
    "chr2_25469502_C_T_snp_1",\
    "chr2_25469913_C_T_snp_1",\
    "chr2_29416326_G_A_snp_1",\
    "chr2_29416366_G_C_snp_1",\
    "chr2_47601106_T_C_snp_1",\
    "chr2_47656801_G_A_snp_1",\
    "chr2_47693959_G_A_snp_1",\
    "chr2_48018030_A_G_snp_1",\
    "chr2_48018236_G_T_snp_1",\
    "chr2_48027921_T_C_snp_1",\
    "chr2_178095900_A_G_snp_1",\
    "chr2_215632255_CA_TG_mnp_2",\
    "chr2_215645464_C_G_snp_1",\
    "chr2_215645545_C_G_snp_1",\
    "chr3_10138019_G_A_snp_1",\
    "chr3_37056000_C_A_snp_1",\
    "chr3_41266101_C_A_snp_1",\
    "chr3_41266133_CCTT_C_del_3",\
    "chr3_128200806_G_A_snp_1",\
    "chr3_142277575_A_T_snp_1",\
    "chr3_178936091_G_A_snp_1",\
    "chr3_178947865_G_A_snp_1",\
    "chr3_178952085_A_G_snp_1",\
    "chr4_55138600_G_A_snp_1",\
    "chr4_55152040_C_T_snp_1",\
    "chr4_55599321_A_T_snp_1",\
    "chr4_55602765_G_C_snp_1",\
    "chr4_55604693_C_A_snp_1",\
    "chr4_106182946_C_A_snp_1",\
    "chr4_153244155_TC_T_del_1",\
    "chr4_153332500_C_T_snp_1",\
    "chr5_1254594_C_T_snp_1",\
    "chr5_1260515_G_A_snp_1",\
    "chr5_67522722_C_T_snp_1",\
    "chr5_79970914_CA_C_del_1",\
    "chr5_80168937_G_A_snp_1",\
    "chr5_112162854_T_C_snp_1",\
    "chr5_112164561_G_A_snp_1",\
    "chr5_112175770_G_A_snp_1",\
    "chr5_112176325_G_A_snp_1",\
    "chr5_112176559_T_G_snp_1",\
    "chr5_112176756_T_A_snp_1",\
    "chr5_112177171_G_A_snp_1",\
    "chr5_112179431_C_T_snp_1",\
    "chr5_149504348_C_T_snp_1",\
    "chr6_35420267_C_T_snp_1",\
    "chr6_41903782_A_C_snp_1",\
    "chr7_2953038_C_T_snp_1",\
    "chr7_6022626_C_T_snp_1",\
    "chr7_6026988_G_A_snp_1",\
    "chr7_55241707_G_A_snp_1",\
    "chr7_55249063_G_A_snp_1",\
    "chr7_55259515_T_G_snp_1",\
    "chr7_106508978_A_G_snp_1",\
    "chr7_116339847_GT_G_del_1",\
    "chr7_116436022_G_A_snp_1",\
    "chr7_140449150_T_C_snp_1",\
    "chr7_140453136_A_T_snp_1",\
    "chr8_26217856_A_C_snp_1",\
    "chr8_38275434_C_A_snp_1",\
    "chr8_90993061_A_G_snp_1",\
    "chr8_145737514_G_A_snp_1",\
    "chr8_145741130_C_T_snp_1",\
    "chr8_145741765_G_A_snp_1",\
    "chr8_145742514_A_G_snp_1",\
    "chr9_5050706_C_T_snp_1",\
    "chr9_35074917_T_C_snp_1",\
    "chr9_98209594_G_A_snp_1",\
    "chr9_98211548_TG_T_del_1",\
    "chr9_98278975_C_T_snp_1",\
    "chr9_135802659_C_T_snp_1",\
    "chr9_139391636_G_A_snp_1",\
    "chr9_139396746_C_T_snp_1",\
    "chr9_139397707_G_A_snp_1",\
    "chr9_139407932_A_G_snp_1",\
    "chr9_139409754_G_A_snp_1",\
    "chr9_139418260_A_G_snp_1",\
    "chr10_8100647_C_T_snp_1",\
    "chr10_8111409_C_T_snp_1",\
    "chr10_43613843_G_T_snp_1",\
    "chr11_533328_C_T_snp_1",\
    "chr11_69462910_G_A_snp_1",\
    "chr11_69625385_C_T_snp_1",\
    "chr11_69633633_C_A_snp_1",\
    "chr11_94212048_C_T_snp_1",\
    "chr11_94225920_C_T_snp_1",\
    "chr11_128333503_T_C_snp_1",\
    "chr12_4553332_A_G_snp_1",\
    "chr12_4553383_A_G_snp_1",\
    "chr12_25362777_A_G_snp_1",\
    "chr12_25398281_C_T_snp_1",\
    "chr12_25398284_C_T_snp_1",\
    "chr12_121416622_C_G_snp_1",\
    "chr12_121416650_A_C_snp_1",\
    "chr12_121437114_G_A_snp_1",\
    "chr12_121437221_T_C_snp_1",\
    "chr13_28578214_GGA_G_del_2",\
    "chr13_32911888_A_G_snp_1",\
    "chr13_32912299_T_C_snp_1",\
    "chr13_32912750_G_T_snp_1",\
    "chr13_32913558_CA_C_del_1",\
    "chr13_32913836_CA_C_del_1",\
    "chr13_32936646_T_C_snp_1",\
    "chr13_48916887_A_G_snp_1",\
    "chr13_49051481_T_A_snp_1",\
    "chr14_45645974_A_G_snp_1",\
    "chr14_68290372_T_G_snp_1",\
    "chr14_105241378_C_T_snp_1",\
    "chr15_66727451_A_C_snp_1",\
    "chr15_66729147_C_T_snp_1",\
    "chr15_89849327_G_A_snp_1",\
    "chr15_91312313_G_A_snp_1",\
    "chr15_91337479_G_A_snp_1",\
    "chr15_91346923_C_A_snp_1",\
    "chr15_91354505_C_T_snp_1",\
    "chr16_2120402_T_C_snp_1",\
    "chr16_2134450_G_A_snp_1",\
    "chr16_3658433_C_A_snp_1",\
    "chr16_14041958_T_C_snp_1",\
    "chr16_68771372_C_T_snp_1",\
    "chr16_89805914_T_C_snp_1",\
    "chr16_89807233_C_G_snp_1",\
    "chr16_89815152_G_A_snp_1",\
    "chr16_89816314_A_G_snp_1",\
    "chr16_89816333_C_T_snp_1",\
    "chr16_89825065_G_A_snp_1",\
    "chr16_89828437_A_G_snp_1",\
    "chr16_89839766_G_C_snp_1",\
    "chr16_89857935_G_A_snp_1",\
    "chr16_89857964_T_C_snp_1",\
    "chr16_89858417_C_A_snp_1",\
    "chr16_89862434_T_C_snp_1",\
    "chr16_89877269_T_C_snp_1",\
    "chr17_7579472_G_C_snp_1",\
    "chr17_29553485_G_A_snp_1",\
    "chr17_37650892_C_T_snp_1",\
    "chr17_37879588_A_G_snp_1",\
    "chr17_41234451_G_A_snp_1",\
    "chr17_41251931_G_A_snp_1",\
    "chr17_62007498_A_G_snp_1",\
    "chr19_1222012_G_C_snp_1",\
    "chr19_4101062_G_T_snp_1",\
    "chr19_15278222_C_T_snp_1",\
    "chr19_15300069_T_C_snp_1",\
    "chr19_15302905_C_T_snp_1",\
    "chr19_17952185_G_T_snp_1",\
    "chr19_30314666_C_T_snp_1",\
    "chr19_45868309_T_G_snp_1",\
    "chr19_45872036_C_T_snp_1",\
    "chr19_45912406_G_A_snp_1",\
    "chr22_41536164_C_T_snp_1",\
    "chr22_41551039_T_A_snp_1",\
    "chr22_41564708_C_A_snp_1",\
    "chr22_41566524_CA_C_del_1",\
    "chr22_41568480_T_C_snp_1",\
    "chr1_154142876_C_C[chr1:156844363[_Fusion_None",\
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
    "chr10_32306071_C_C[chr10:43609928[_Fusion_None"])]
    #Change fusion gene names to something more interpretable
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
    "chr10_32306071_C_C[chr10:43609928[_Fusion_None"],["TPM3(7) - NTRK1(10)",\
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
    "KIF5B(24) - RET(11)"], inplace = True)

    #Get only workflow 5.16
    df = df.loc[df['IonWF_version'] == 1]
    #Sort by date
    df = df.sort_values(["filedate","variant"])
    df = df.reset_index(drop=True)

    #Drop uninformative columns, add stdev for numerical values and group the entire table by variant. means and modes are used, except the samples names, which are the sum of unique names. 
    tabledf = df.drop(labels=['IonWF_version','pass_filter','transcript'], axis =1)
    tabledf['afreq'] = tabledf['afreq'].fillna(0)
    tabledf['afreq'] = tabledf['afreq'].astype(float)
    tabledf['afreq'] = 100*(tabledf['afreq'])
    tabledf['norm_count'] = tabledf['norm_count'].fillna(0)
    tabledf['norm_count'] = 1000000*(tabledf['norm_count'])
    tabledf['afreq_normcount'] = tabledf['afreq'] + tabledf['norm_count']
    tabledf['sd'] = tabledf.groupby('variant').afreq_normcount.transform('std')
    tabledf['upper_bound (3SD)'] = tabledf['afreq_normcount'] + 3*(tabledf['sd'])
    tabledf['lower_bound (3SD)'] = tabledf['afreq_normcount'] - 3*(tabledf['sd'])
    tabledf = tabledf.drop('afreq_normcount', axis=1)
    return(tabledf)

#initial call for the database query

def make_table(): # this needs to create 3 tables: one with the complete output from SQL, one aggregated to have means and SD calculated for small variants, and one similar but for RNA
    tabledf = get_sql()
    tabledf1 = tabledf.groupby('variant', as_index=False).agg({'samplename': 'nunique', 'coverage': ['mean'], 'afreq': ['mean'], 'trname': pd.Series.mode, 'HGVSc': pd.Series.mode, 'HGVSp':pd.Series.mode, 'filedate': ['max'], 'gene': pd.Series.mode, 'sd': ['mean'], 'upper_bound (3SD)': ['mean'], 'lower_bound (3SD)':['mean']})
    tabledf1.columns = tabledf1.columns.droplevel(1)
    tabledf2 = tabledf.groupby('variant', as_index=False).agg({'samplename': 'nunique', 'coverage': ['mean'], 'norm_count': ['mean'], 'trname': pd.Series.mode, 'HGVSc': pd.Series.mode, 'HGVSp':pd.Series.mode, 'filedate': ['max'], 'gene': pd.Series.mode, 'sd': ['mean'], 'upper_bound (3SD)': ['mean'], 'lower_bound (3SD)':['mean']})
    tabledf2.columns = tabledf2.columns.droplevel(1)
    neworder = ['variant','gene','afreq', 'norm_count','sd', 'upper_bound (3SD)', 'lower_bound (3SD)','coverage','trname','HGVSc','HGVSp','samplename']
    neworder1 = ['variant','gene','afreq','sd', 'upper_bound (3SD)', 'lower_bound (3SD)','coverage','trname','HGVSc','HGVSp','samplename']
    neworder2 = ['variant','gene','norm_count','sd', 'upper_bound (3SD)', 'lower_bound (3SD)','coverage','trname','HGVSc','HGVSp','samplename']
    tabledf = tabledf[neworder]
    tabledf1 = tabledf1[neworder1]
    tabledf2 = tabledf2[neworder2]
    tabledf1 = tabledf1[tabledf1['variant'].str.startswith('chr')]
    tabledf2 = tabledf2[~tabledf2['variant'].str.startswith('chr')]
    tabledf = tabledf.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    tabledf1 = tabledf1.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    tabledf2 = tabledf2.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
    # Needs to be jsonized to store in an empty div to gain speed, otherwise you are stuck building the dataframes 0 and 1 in each callback, which is expensive.
    return tabledf.to_json(double_precision = 4), tabledf1.to_json(double_precision = 2), tabledf2.to_json(double_precision = 0)


#create the app layout
app = dash.Dash(__name__)

VALID_USERNAME_PASSWORD_PAIRS = { # login credentials
    'EAllain': 'Vitalite1',
    'NCrapoulet': 'Vitalite2',
    'PPRobichaud': 'Vitalite3',
    'ROuellette': 'Vitalite4'
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
#Avoid global variables, instead store in empty divs

#defining the layout
def serve_layout():
    tab0, tab1, tab2 = make_table()
    t0 = pd.read_json(tab0)
    t1 = pd.read_json(tab1)
    t2 = pd.read_json(tab2)
    t0 = t0.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    t1 = t1.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    t2 = t2.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
    sig_tab = pd.DataFrame({'Field':["CQ Blancs","Couverture > 800","Uniformité","PhD \#1", "PhD \#2", "MD Conseil"],'Value':["PASS  /  FAIL","PASS  /  FAIL","PASS  /  FAIL","___________________________________________________","___________________________________________________","___________________________________________________"]})
    return html.Div(children=[
    #First is a title and a refresh button
    #Then a datatable with selectable rows for later graphs with callback
    html.Div([html.Button('Refresh', id='apply-button', n_clicks=0),
              html.Div(id='output-container-button', children='Click the button to update.')]),
    html.H1(children="HD827 / SeraCare controls"),
    html.Br(),
    dcc.Dropdown(id = 'drpdown', options = [{'label': i, 'value': i} for i in t0['samplename'].unique()[-50:]], value = t0['samplename'].tolist()[-1]), # dropdown menu to pick sample for analysis
    html.H2(children="Variants n'ayant pas passé vérification CQ:"),
    dash_table.DataTable(id = 'table-fail', # table for small variants not passing QC
        columns=[{'name':i, 'id':i, 'deletable': False} for i in t0.columns if i not in ['id', 'afreqsd','normcountsd']],
        page_size=25,
        style_data_conditional=[
        {
            'if': {
                'filter_query':'{afreq} < {lower_bound (3SD)}',
                'column_id':'afreq'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }, {
            'if': {
                'filter_query': '{afreq} > {upper_bound (3SD)}',
                'column_id':'afreq'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }]),
    html.Br(),
    dash_table.DataTable(id = 'table-fail2', #this is the RNA-based summary of only variants not passing QC
        columns=[{'name':i, 'id':i, 'deletable': False} for i in t0.columns if i not in ['id', 'afreqsd','normcountsd']],
        page_size=10,
        style_data_conditional=[
        {
            'if': {
                'filter_query':'{norm_count} < {lower_bound (3SD)}',
                'column_id':'norm_count'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }, {
            'if': {
                'filter_query': '{norm_count} > {upper_bound (3SD)}',
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
    html.H2(children="Tableaux Complets des variants"),
    dash_table.DataTable(id = 'table-2',
        columns=[{'name':i, 'id':i, 'deletable': False} for i in t0.columns if i not in ['id', 'afreqsd','normcountsd']],
        page_size=10,
        style_data_conditional=[
        {
            'if': {
                'filter_query':'{afreq} < {lower_bound (3SD)}',
                'column_id':'afreq'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }, {
            'if': {
                'filter_query': '{afreq} > {upper_bound (3SD)}',
                'column_id':'afreq'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }]),
    html.Br(),
    dash_table.DataTable(id = 'table-3', # for RNA
        columns=[{'name':i, 'id':i, 'deletable': False} for i in t0.columns if i not in ['id', 'afreqsd','normcountsd']],
        page_size=5,
        style_data_conditional=[
        {
            'if': {
                'filter_query':'{norm_count} < {lower_bound (3SD)}',
                'column_id':'norm_count'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }, {
            'if': {
                'filter_query': '{norm_count} > {upper_bound (3SD)}',
                'column_id':'norm_count'
            },
            'backgroundColor': '#85144b',
            'color':'white'
        }]),
    html.Br(),
    #dcc.Graph(id = 'subplot-div', style={'width': '250vh'}),
    html.Div(dcc.Input(id='input-box', type='text')), #input box for comments
    html.Button('Submit', id='button'),
    html.Br(),
    html.Div(id='newlines-container',children='\n\n\n\n'),
    html.Br(),
    html.Br(),
    html.Button('Delete', id='button2'), # Delete will add to a list of exclusions that filters out any unwanted data when reading in from SQL
    html.Br(),
    html.H2(children="Graphiques Levey-Jennings"),
    dash_table.DataTable(
    id='table',
    columns=[
        {'name': i, 'id': i, 'deletable': False} for i in t1.columns
        # omit the id column
        if i != 'id'
    ],
    #This to_dict function adds a level to column headers, making them tuples if not dropped after using groupby. See above.
    data=t1.to_dict('records'),
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
    html.Div(id='LJ_graph'),
    dcc.Graph(id = 'LJ_graph2'),
    html.Br(),
    dash_table.DataTable(
    id='tableR',
    columns=[
        {'name': i, 'id': i, 'deletable': False} for i in t2.columns
        # omit the id column
        if i != 'id'
    ],
    #This to_dict function adds a level to column headers, making them tuples if not dropped after using groupby. See above.
    data=t2.to_dict('records'),
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
    html.Div(id='LJ_graphRNA'),
    dcc.Graph(id = 'LJ_graphRNA2'),
    html.Br(),
    html.Div(id='dummy1'),
    html.Br(),
    html.Div(id='dummy2'),
    html.Div(id = 'store1',style={'display': 'none'}, children = tab0), #empty divs allow us to only compute / load the expensive database filtering upon initialization, rather than in each callback
    html.Div(id = 'store2',style={'display': 'none'}, children = tab1),
    html.Div(id = 'store3',style={'display': 'none'}, children = tab2)
    ])

app.layout = serve_layout

#Callbacks and functions


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

#now for the first graph

@app.callback(
    Output('LJ_graph2', 'figure'), #outputs to plotly figure
    Input('table','data'), # gets data from the table
    Input('table','selected_rows'), # gets the seleccted active row
    Input('store1', 'children')) #Gets the stored empty-div dataframe

def update_graph(data, selected_rows, tab0):
    if selected_rows is None:
        selected_rows = []
    var = data[selected_rows[0]]['variant'] if selected_rows else "chr1_11181327_C_T_snp_1" #default selection
    data_long = pd.read_json(tab0).copy() #read the json
    #print(data_long)
    sset = pd.DataFrame(data_long['samplename'].unique(), columns=['samplename']) # required to get null value samples
    is_var = data_long['variant'] == var #get only the active variant
    filt_dat = data_long[is_var]
    value_vect = [] # stores the sample-wise values for Afreq to check if missing samples. 
    #print(sset)
    for index, row in sset.iterrows():
        #print(row['samplename'])
        label = row['samplename']
        if label in filt_dat['samplename'].tolist():
            a = filt_dat.loc[filt_dat['samplename']==label, 'afreq'].values[0]
            value_vect.append(a)
        else:
            value_vect.append(0)
    sset['afreq'] = value_vect
    #print(sset)
    mn = sset['afreq'].tolist()
    #print(mn)
    mn1 = [num for num in mn if num]
    if len(filt_dat.index) >50: # if more than 50 samples, get the latest 50 (df is sorted by date)
        filt_dat = filt_dat[-50:]
    sdpos1 = st.median(mn1) + np.std(mn1)
    sdneg1 = st.median(mn1) -(np.std(mn1))
    sdpos2 = st.median(mn1) + 3*(np.std(mn1))
    sdneg2 = st.median(mn1) - 3*(np.std(mn1))
    figure = go.Figure(data = go.Scatter(x = sset['samplename'], y = mn[-50:], mode='lines+markers', name = 'Value'))
    figure.add_hline(y = sdpos1, line_width=2, line_color="green", name = '+1SD')
    figure.add_hline(y = sdneg1, line_width=2, line_color="green", name = '-1SD')
    figure.add_hline(y = sdpos2, line_width=2, line_color="red", name = '+3SD')
    figure.add_hline(y = sdneg2, line_width=2, line_color="red", name = '-3SD')
    figure.update_xaxes(showticklabels=False)
    return figure

#Function for printing the active variant on the screen
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

#now for the first graph

@app.callback(
    Output('LJ_graphRNA2', 'figure'), #outputs to plotly figure
    Input('tableR','data'), # gets data from the table
    Input('tableR','selected_rows'), # gets the seleccted active row
    Input('store1', 'children')) #Gets the stored empty-div dataframe

def update_graph2(data, selected_rows, tab0):
    if selected_rows is None:
        selected_rows = []
    var = data[selected_rows[0]]['variant'] if selected_rows else "LMNA(2) - NTRK1(11)" #default selection
    data_long = pd.read_json(tab0).copy() #read the json
    sset = pd.DataFrame(data_long['samplename'].unique(), columns=['samplename']) # required to get null value samples
    is_var = data_long['variant'] == var #get only the active variant
    filt_dat = data_long[is_var]
    value_vect = [] # stores the sample-wise values for Afreq to check if missing samples.
    for index, row in sset.iterrows():
        #print(row['samplename'])
        label = row['samplename']
        if label in filt_dat['samplename'].tolist():
            a = filt_dat.loc[filt_dat['samplename']==label, 'norm_count'].values[0]
            value_vect.append(a)
        else:
            value_vect.append(0)
    sset['norm_count'] = value_vect
    #print(sset)
    mn = sset['norm_count'].tolist()
    #print(mn)
    mn1 = [num for num in mn if num]
    if len(filt_dat.index) >50: # if more than 50 samples, get the latest 50 (df is sorted by date)
        filt_dat = filt_dat[-50:]
    sdpos1 = st.median(mn1) + np.std(mn1)
    sdneg1 = st.median(mn1) -(np.std(mn1))
    sdpos2 = st.median(mn1) + 3*(np.std(mn1))
    sdneg2 = st.median(mn1) - 3*(np.std(mn1))
    figure = go.Figure(data = go.Scatter(x = sset['samplename'], y = mn[-50:], mode='lines+markers', name = 'Value'))
    figure.add_hline(y = sdpos1, line_width=2, line_color="green", name = '+1SD')
    figure.add_hline(y = sdneg1, line_width=2, line_color="green", name = '-1SD')
    figure.add_hline(y = sdpos2, line_width=2, line_color="red", name = '+3SD')
    figure.add_hline(y = sdneg2, line_width=2, line_color="red", name = '-3SD')
    figure.update_xaxes(showticklabels=False)
    return figure


#The second sample-wise graphs

@app.callback(
    Output('table-2','data'), #plot table
    Input('drpdown','value'), #get active sample from dropdown
    Input('store1', 'children'), #get data from dummy div
    Input('store2', 'children')) # get table 2 from dummy div

def update_table2(sel_value, tab0, tab1):
    t0 = pd.read_json(tab0).copy()
    t0 = t0.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
    t1 = pd.read_json(tab1)
    t1 = t1.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    filt_dat = t0[t0['variant'].str.startswith('chr')]
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    missing = list(set(t1['variant'].tolist()) - set(filt_dat['variant'].tolist()))
    if missing:
        for var in missing:
            new_row = {'variant':var,'gene':'','afreq':0,'norm_count':0,'sd':0,'upper_bound (3SD)':0,'lower_bound (3SD)':0,'coverage':0,'trname':'','HGVSc':'','HGVSp':'','samplename':sel_value}
            filt_dat = filt_dat.append(new_row, ignore_index=True)
    filt_dat = filt_dat.sort_values('variant')
    #print(filt_dat['variant'].tolist())
    #print(t1['variant'].tolist())
    filt_dat['upper_bound (3SD)'] = t1['upper_bound (3SD)'].tolist()
    filt_dat['lower_bound (3SD)'] = t1['lower_bound (3SD)'].tolist()
    return filt_dat.to_dict('records')

@app.callback(
    Output('table-3','data'), #plot table
    Input('drpdown','value'), #get active sample from dropdown
    Input('store1', 'children'), #get data from dummy div
    Input('store3', 'children')) # get table 3 from dummy div

def update_table3(sel_value, tab0, tab2):
    t0 = pd.read_json(tab0)
    t0 = t0.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
    t2 = pd.read_json(tab2)
    t2 = t2.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
    filt_dat = t0[~t0['variant'].str.startswith('chr')]
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    filt_dat['upper_bound (3SD)'] = t2['upper_bound (3SD)'].tolist()
    filt_dat['lower_bound (3SD)'] = t2['lower_bound (3SD)'].tolist()
    return filt_dat.to_dict('records')



#For the summary tables at top

@app.callback(
    Output('table-fail','data'), #plot table
    Input('drpdown','value'), #get active sample from dropdown
    Input('store1', 'children'), #get data from dummy div
    Input('store2', 'children')) # get table 2 from dummy div

def update_fail1(sel_value, tab0, tab1):
    t0 = pd.read_json(tab0).copy()
    t0 = t0.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
    t1 = pd.read_json(tab1)
    t1 = t1.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
    filt_dat = t0[t0['variant'].str.startswith('chr')]
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    missing = list(set(t1['variant'].tolist()) - set(filt_dat['variant'].tolist()))
    if missing:
        for var in missing:
            idx = t1.index[t1['variant']==var].tolist()
            label = t1.loc[idx,'gene']
            new_row = {'variant':var,'gene':label,'afreq':0,'norm_count':0,'sd':0,'upper_bound (3SD)':0,'lower_bound (3SD)':0,'coverage':0,'trname':'','HGVSc':'','HGVSp':'','samplename':sel_value}
            filt_dat = filt_dat.append(new_row, ignore_index=True)
    filt_dat = filt_dat.sort_values('variant')
    filt_dat['upper_bound (3SD)'] = t1['upper_bound (3SD)'].tolist()
    filt_dat['lower_bound (3SD)'] = t1['lower_bound (3SD)'].tolist()
    filt_dat = filt_dat.loc[(filt_dat['afreq']<=filt_dat['lower_bound (3SD)'])|(filt_dat['afreq']>=filt_dat['upper_bound (3SD)'])]
    return filt_dat.to_dict('records')

@app.callback(
    Output('table-fail2','data'), #plot table
    Input('drpdown','value'), #get active sample from dropdown
    Input('store1', 'children'), #get data from dummy div
    Input('store3', 'children')) # get table 3 from dummy div

def update_fail2(sel_value, tab0, tab2):
    t0 = pd.read_json(tab0)
    t0 = t0.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x) #when reading from json, floats are 15 decimal points long for some reason.... need to round
    t2 = pd.read_json(tab2)
    t2 = t2.applymap(lambda x: round(x, 0) if isinstance(x, (int, float)) else x)
    filt_dat = t0[~t0['variant'].str.startswith('chr')]
    filt_dat = filt_dat[filt_dat['samplename'] == sel_value].copy()
    filt_dat['upper_bound (3SD)'] = t2['upper_bound (3SD)'].tolist()
    filt_dat['lower_bound (3SD)'] = t2['lower_bound (3SD)'].tolist()
    filt_dat = filt_dat.loc[(filt_dat['norm_count']<=filt_dat['lower_bound (3SD)'])|(filt_dat['norm_count']>=filt_dat['upper_bound (3SD)'])]
    return filt_dat.to_dict('records')











#Refresh button
@app.callback(
    Output('output-container-button', 'children'), #refresh button calls serve_layout.. can also hit refresh on browser... 
    Input('apply-button', 'n_clicks'))

def refresh(n_clicks):
    if not n_clicks:
        return dash.no_update
    else:
        app.layout = serve_layout #not 100% sure this works

#dotplots

#@app.callback(
#        Output('subplot-div','figure'),
#        Input('drpdown','value'),
#        Input('store1','children'))


#def make_dotplots(value, tab0): # needs to be changed to a per-variant graph
#    data_dot = pd.read_json(tab0).copy()
#    data_dot.loc[data_dot.samplename != value, 'samplename'] = "Group"
#    data_dot.loc[data_dot.samplename == value, 'samplename'] = "Current Sample"
#    figure = px.box(data_dot, x = "variant", y = "afreq_normcount",color="samplename", facet_col="variant")
#    figure.update_yaxes(matches=None, showticklabels=False)
#    figure.update_xaxes(matches=None, tickangle=45, title="")
#    figure.for_each_annotation(lambda a: a.update(text=""))
#    return figure



@app.callback(
    Output('output-container-button2', 'children'),
    Input('drpdown','value')) #this comment manager takes the dropdown value as input. 

def display_notes(value):
    override = pd.read_csv('comments.txt', sep='\t', names=['sample','time','comment']) #read the comments file to obtain any current comments on the sample.
    filt_or = override.loc[override['sample'] == value] #find the selected dropdown value in the frame
    try:
        slist = filt_or['comment'].tolist()
        slist = [str(i) for i in slist]
        print(slist)
        slist = list(filter(('nan').__ne__, slist))
        return '\n'.join(slist) #print comments
    except:
        return 'No comments'

@app.callback(
    Output("dummy1", "children"), #needed for function, output really does to text file
    Input('button','n_clicks'),
    State('drpdown','value'), #see above, comment manager takes dropdown as input
    State('input-box', 'value'),prevent_initial_call=True)

def update_notes(n_clicks, drpdown ,input_box):
    now = datetime.now().date()
    f = open('comments.txt', 'a') # file to add comments to
    writer = csv.writer(f, delimiter = "\t")
    row = [drpdown, now, input_box] #row has the sample ID, the date and comments. 
    print(row)
    writer.writerow(row)
    f.close()
    return None

@app.callback(
    Output("dummy2", "children"), #needed for function, output really does to text file
    Input('button2','n_clicks'),
    State('drpdown','value'),prevent_initial_call=True) #see above, comment manager takes dropdown as input

def remove_outlier(n_clicks, drpdown):
    #insert function to delete and refresh here
    f = open('exclusions.tsv', 'a')
    writer = csv.writer(f, delimiter = "\t")
    writer.writerow([drpdown])
    f.close()
    return None

#run on this server with IP

if __name__ == '__main__':
    app.run_server(debug=False, host='10.XXX.XXX.XXX', port=8060)

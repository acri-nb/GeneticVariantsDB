#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 13:19:44 2021
This script is used to fix errors in the clinical Ion Torrent VCF headers, creates a file-like object with the new header,
Reads the VCF with PyVCF and inserts the values into the corresponding SQL database. 
It can be used at the command line with the -i and -db arguments to specify vcf file and database of choice. 
Usage: python3 ../Add_to_DB_v2.py -i input.vcf -db database.sql
@author: Eric
"""


#DEPENDENCIES
import mysql.connector
import os
import re
import numpy
import pandas
import vcf
import sqlite3
from io import StringIO
import argparse


#FOR IMPLEMENTATION

#find . -name '*:*' -type f -print0 | perl -0ne ' rename $_, s{[^/]+$}{$& =~ y/:/-/r}res or warn "rename $_: $!"'
#python3 ../DB_init_v2.py     !!! ONLY THE 1st TIME
#for i in $(ls *.vcf); do python3 Add_to_DB_v2.py -i $i; done


#Function to fix several bugs in the VCF header.
def change_header(old_vcf):
    meta = []
    data_list = []
    for ln in open(old_vcf,'r'): #open the input file
        if ln.startswith("##"): #strip the header
            meta.append(ln.rstrip())
        else:
            data_list.append(ln.rstrip()) #strip the data
    try:
        id = meta.index('##INFO=<ID=NORM_COUNT_WITHIN_GENE,Number=1,Type=Float,String,Description="Normalized read count of this assay to all the other assays for the same gene ">') #find the corresponding index for this string
        meta[id] = meta[id].replace(',String','') #replace erroneous substring
        #meta.remove('##INFO=<ID=FR,Number=.,Type=String,Description="Filter Reason. Can be one or more of (READ_COUNT, PERCENT_NONZERO_AMPLICONS, PERCENT_ALIGNED_READS, SEVERE_GRADIENT, LOCAL_AVERAGE_SIGNAL_VARIATION, DIFFERENT_MEAN_SIGNAL).">')
    except:
        pass
    try:
        id = meta.index('##INFO=<ID=RATIO_TO_WILD_TYPE,Number=1,Type=Float,String,Description="Ratio between read count of this assay and oormalized count of wild type assay ">')
        meta[id] = meta[id].replace(',String','')
        #meta.remove('##FILTER=<ID=NOCALL,Description="Generic filter. Filtering details stored in FR info tag.">')
        #meta.remove('##FILTER=<ID=GAIN,Description="Filter is marked as GAIN when Amplification threshold criteria are satisfied using focal_amplification v1>')
    except:
        pass
    try:
        id = meta.index('##FILTER=<ID=GAIN,Description="Filter is marked as GAIN when Amplification threshold criteria are satisfied using focal_amplification v1>')
        meta[id] = meta[id].replace('focal_amplification v1>','focal_amplification v1">')
    except:
        pass
    try:
        meta.remove('##INFO=<ID=SD,Number=1,Type=Float,Description="The standard deviation of the values used to calculate the CN estimate.">') #some strings could not be replaced, if they are not critical, remove them
    except:
        pass
    try:
        id = meta.index('##INFO=<ID=IMBALANCE_PVAL,Number=1,Type=Float,Description="p-value for the expression imbalance between the 3p and 5p markers of the driver gene based on the exon tiling assays">')
        meta[id] = meta[id].replace('Float','String')
    except:
        pass
    final_list = meta + data_list # concatenate the new header to the data
    return(final_list)

#function used for writing new file during testing rather than using file-like objects, ignore.
def write_fix_file(title, new_file):
    with open(title, 'w') as fl:
        fl.write('\n'.join(new_file))

#function for creating a file-like object with correct header from the original file
def make_vcf_object(vcf_f):
    res = '\n'.join(change_header(vcf_f)) # join rows with newline
    ex = StringIO(res)
    ex_vcf = vcf.Reader(ex) # read with PyVCF
    return(ex_vcf)


#Function for storing tool versions and workflow information in the corresponding database tables.
def ToolVerSanityCheck(conn, vcf_f):#takes two arguments, the connector object and the VCF
    cur = conn.cursor()
    vcf_obj = make_vcf_object(vcf_f)
    #get basic metadata from the vcf
    AV = vcf_obj.metadata['OncomineVariantAnnotationToolVersion'][0]
    try:
        BCV = vcf_obj.metadata['basecallerVersion'][0].replace('"','')
    except:
        BCV = None
    WF = vcf_obj.metadata['IonReporterWorkflowName'][0]
    WFV = vcf_obj.metadata['IonReporterWorkflowVersion'][0]
    REF = vcf_obj.metadata['reference']
    #get the disease type, if it can be found
    try:
        DT = vcf.obj.metadata['sampleDiseaseType']
    except:
        DT = 'QC'

    q1 = '''
    INSERT IGNORE INTO AnnotationVersion (name)
        VALUES (%s)'''
    q2 = '''
    INSERT IGNORE INTO BaseCallVer (name)
        VALUES (%s)'''
    q3 = '''
    INSERT IGNORE INTO WorkFlowName (name)
        VALUES (%s)'''
    q4 = '''
    INSERT IGNORE INTO WorkFlowVer (name)
        VALUES (%s)'''
    q5 = '''
    INSERT IGNORE INTO ref_genome (name)
        VALUES (%s)'''
    q6 = '''
    INSERT IGNORE INTO DisType (name)
        VALUES (%s)'''
    #add the contigs into the appropriate table
    val1 = (AV,)
    val2 = (BCV,)
    val3 = (WF,)
    val4 = (WFV,)
    val5 = (REF,)
    val6 = (DT,)
    cur.execute(q1, val1)
    cur.execute(q2, val2)
    cur.execute(q3, val3)
    cur.execute(q4, val4)
    cur.execute(q5, val5)
    cur.execute(q6, val6)
    contigs = list(vcf_obj.contigs.keys())
    for item in contigs:
        q ='''
        INSERT IGNORE INTO Chromosomes (name)
            VALUES (%s)'''
        val = (item,)
        cur.execute(q, val)
    conn.commit()


#Function for storing run / sample information
def insert_Run_info(conn, vcf_f):
    cur = conn.cursor()
    vcf_obj = make_vcf_object(vcf_f)
    #Retrieveing some required info
    AV = vcf_obj.metadata['OncomineVariantAnnotationToolVersion'][0]
    try:
        BCV = vcf_obj.metadata['basecallerVersion'][0].replace('"','')
    except:
        BCV = None
    WF = vcf_obj.metadata['IonReporterWorkflowName'][0]
    WFV = vcf_obj.metadata['IonReporterWorkflowVersion'][0]
    REF = vcf_obj.metadata['reference']
    #get the disease type, if it can be found
    try:
        DT = vcf.obj.metadata['sampleDiseaseType']
    except:
        DT = 'QC'
    #fetching values for insertion into appropriate Run table

    NAME = vcf_obj.metadata['IonReporterAnalysisName'][0]
    SEX = vcf_obj.metadata['sampleGender'][0]
    FORMAT = vcf_obj.metadata['fileformat']
    DATE = int(vcf_obj.metadata['fileDate'].replace("/",""))

    #find the right internal sql identifiers by searching the name in the other tables and establishing the correct foreign keys
    q1 = 'SELECT id FROM ref_genome WHERE name = %s'
    val1 = (REF,)
    cur.execute(q1, val1)
    REFERENCE = cur.fetchone()[0]
    q2 = 'SELECT id FROM AnnotationVersion WHERE name = %s'
    val2 = (AV,)
    cur.execute(q2, val2)
    OMAV = cur.fetchone()[0]
    q3 = 'SELECT id FROM WorkFlowName WHERE name = %s'
    val3 = (WF,)
    cur.execute(q3, val3)
    IONWF = cur.fetchone()[0]
    q4 = 'SELECT id FROM WorkFlowVer WHERE name = %s'
    val4 = (WFV,)
    cur.execute(q4, val4)
    IONWFVER = cur.fetchone()[0]
    try:
        CELL = float(vcf_obj.metadata['CellularityAsAFractionBetween0-1'][0])
    except:
        CELL = None
    try:
        FUSIONOC = vcf_obj.metadata['FusionSampleOverallCall'][0][0:8]
        FUSIONQC = vcf_obj.metadata['FusionSampleQC'][0][0:4]
        FUSIONRD = int(vcf_obj.metadata['TotalMappedFusionPanelReads'][0])
    except:
        FUSIONOC = None
        FUSIONQC = None
        FUSIONRD = None
    if BCV == None:
        BCVer = None
    else:
        q5 = 'SELECT id FROM BaseCallVer WHERE name = %s'
        val5 = (BCV,)
        cur.execute(q5, val5)
        BCVer = cur.fetchone()[0]
    try:
        PERMAP = float(vcf_obj.metadata['percent_aligned_reads'][0])
    except:
        PERMAP = None
    q6 = 'SELECT id FROM DisType WHERE name = %s'
    val6 = (DT,)
    cur.execute(q6, val6)
    PHENO = cur.fetchone()[0]

    #insert values into tables
    q7 = '''
    INSERT IGNORE INTO RunInfo (name, pheno, sex, fileformat, filedate, reference, OM_anno_version, IonWF, IonWF_version, Cellularity, fusionOC, fusionQC, fusionReads, basecall_ver, perc_mapped)
        VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )'''
    values = (NAME, PHENO, SEX, FORMAT, DATE, REFERENCE, OMAV, IONWF, IONWFVER, CELL, FUSIONOC, FUSIONQC, FUSIONRD, BCVer, PERMAP)
    cur.execute(q7, values)
    conn.commit()

#define the types of variants in the VarType table
def insert_Var_types(conn,vcf_f):
    cur = conn.cursor()
    vcf_obj = make_vcf_object(vcf_f)
    #This first Chunk checks if there are any novel variant types in the VarType table, and adds them if necessary
    genes = []
    types = []
    for record in vcf_obj:
        try:
            M = '\'\'\'' + ''.join(record.INFO['FUNC']) + '\'\'\''
            A = M.split("\'gene\':\'")
            B = A[1].split("\'")
            genes.append(B[0])
        except:
            genes.append(None)
        try:
            if isinstance(record.INFO['TYPE'], list):
                ty = record.INFO['TYPE'][0]
                types.append(ty)
            else:
                types.append(record.INFO['TYPE'])
        except:
            if isinstance(record.INFO['SVTYPE'], list):
                ty = record.INFO['SVTYPE'][0]
                types.append(ty)
            else:
                types.append(record.INFO['SVTYPE'])
    #print(types)
    setOfTypes=set(types)
    ls=(list(setOfTypes)) #make the set of variant types a list
    for item in ls:
        q = "INSERT IGNORE INTO VarType (name) VALUES (%s)"
        val = (item,)
        cur.execute(q, val)
    setOfGenes=set(genes)
    gls=(list(setOfGenes))#make the set of gene identifiers
    for item in gls:
        q = "INSERT IGNORE INTO Genes (name) VALUES (%s)"
        val = (item,)
        cur.execute(q, val)
    conn.commit()


#Insert the HGVS annotation for wasy tracking and stardardiizatino of 3' shifted variants
def insert_HGVS(conn, vcf_f):
    cur = conn.cursor()
    vcf_obj = make_vcf_object(vcf_f)
    for record in vcf_obj:
        try:
            hgvs_ann = record.INFO['ANN']
            ALTS = [str(e) for e in record.ALT]
            idxs = []
            for j in range(len(ALTS)):
                alt_allele = [ALTS[j], "|"]
                alt_new = ''.join(alt_allele)
                reorder = [hgvs_ann.index(n) for n in hgvs_ann if hgvs_ann[hgvs_ann.index(n)].startswith(alt_new)]
                idxs.append(reorder[0])
            for i in idxs:
                m = record.INFO['ANN'][i]
                ms = m.split("|")
                idx = [3,6,9,10]
                ms = [ms[b] for b in idx]
                q1 = 'SELECT id FROM Genes WHERE name = %s'
                val1 = (ms[0], )
                cur.execute(q1,val1)
                GN = cur.fetchone()[0]
                q2 = 'INSERT IGNORE INTO Transcripts (name) VALUES (%s)'
                val2 = (ms[1], )
                cur.execute(q2, val2)
                q3 = 'SELECT id FROM Transcripts WHERE name = %s'
                cur.execute(q3, val2)
                TR = cur.fetchone()[0]
                q4 = 'INSERT IGNORE INTO HGVS (transcript, gene, HGVSc, HGVSp) VALUES ( %s, %s, %s, %s )'
                vals = (TR, GN, ms[2], ms[3])
                cur.execute(q4, vals)
        except:
            continue
    conn.commit()

#insert unique variants into the VarData table.
def insert_Var_info(conn,vcf_f):
    cur = conn.cursor()
    vcf_obj = make_vcf_object(vcf_f)
    #Generate a list which contains all the values to be added into each row of the variant table
    for record in vcf_obj:
        #print(record)
        for i in range(len(record.ALT)):
            VAR = []
            VAR.append(record.CHROM)
            VAR.append(record.POS)
            VAR.append(record.REF) # append ref allele
            VAR.append(str(record.ALT[i])) #append alt alleles
            try: # catch perticularities in vcf related to CNV, fusions, splicing or other SVs
                VAR.append(record.INFO['TYPE'][i])
                VAR.append(str(record.INFO['LEN'][i]))
            except:
                if isinstance(record.INFO['SVTYPE'], list):
                    if record.INFO['SVTYPE'][0] == 'CNV':
                        VAR.append(record.INFO['SVTYPE'][0])
                        VAR.append(str(record.INFO['LEN'][0]))
                    else:
                        VAR.append(record.INFO['SVTYPE'][0])
                        VAR.append(None)
                else:
                    if record.INFO['SVTYPE'] == 'CNV':
                        VAR.append(record.INFO['SVTYPE'])
                        VAR.append(str(record.INFO['LEN']))
                    else:
                        VAR.append(record.INFO['SVTYPE'])
                        VAR.append(None)
            NAME = '_'.join(str(e) for e in VAR) #unique name which is just the concatenation of the PARAMS list into a string
            NAME = NAME.replace('>','')
            NAME = NAME.replace('<','') #remove problematic characters
            VAR.append(NAME)
            q1 = 'SELECT id FROM Chromosomes WHERE name = %s' # get Chromosome IDs
            val1 = (VAR[0],)
            cur.execute(q1, val1)
            CHR = cur.fetchone()[0]
            VAR[0] = CHR
            q2 = 'SELECT id FROM VarType WHERE name = %s' # get VarType IDs
            val2 = (VAR[4],)
            cur.execute(q2, val2)
            TY = cur.fetchone()[0]
            VAR[4] = TY
            if record.ID is None or len(record.ID.split(";")) != len(record.ALT): #some alt alleles have only partial annotations, I chose to handle these by checking if all alt alleles are annotated, if so add them to the db, if not skip.
                VAR.append(None)
            else:
                Anno_splitter = record.ID.split(";") #split the annotations prior to adding them, this way they can have a common index with alt alleles in a list.
                VAR.append(Anno_splitter[i])
            try:
                M = '\'\'\'' + ''.join(record.INFO['FUNC']) + '\'\'\'' #some formatiing to fetch the gene name.
                A = M.split("\'gene\':\'")
                B = A[1].split("\'")
                q3 = 'SELECT id FROM Genes WHERE name = %s'
                val3 = (B[0],)
                cur.execute(q3, val3)
                GN = cur.fetchone()[0]
                VAR.append(GN)
            except:
                GN = None
                VAR.append(GN)
            try:
                idxs = []
                hgvs_ann = record.INFO['ANN']
                alt = str(record.ALT[i])
                alt_allele = [alt, "|"]
                alt_new = ''.join(alt_allele)
                newidx = [hgvs_ann.index(n) for n in hgvs_ann if hgvs_ann[hgvs_ann.index(n)].startswith(alt_new)]
                idxs.append(newidx[0])
                for x in idxs:
                    m = record.INFO['ANN'][x]
                    ms = m.split("|")
                    idx = [6,9]
                    ms = [ms[b] for b in idx]
                    q1 = 'SELECT id FROM Transcripts WHERE name = %s'
                    val1 = (ms[0], )
                    cur.execute(q1, val1)
                    TR = cur.fetchone()[0]
                    q2 = 'SELECT id FROM HGVS WHERE transcript = %s AND HGVSc = %s'
                    val2 = (TR, ms[1], )
                    cur.execute(q2,val2)
                    HG = cur.fetchone()[0]
                    VAR.append(HG)
            except:
                VAR.append(None)
            q4 = '''INSERT IGNORE INTO VarData (name, chr, start, len, ref, alt, type, annotation, gene, hgvs)
                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )'''
            values = (VAR[6], VAR[0], VAR[1], VAR[5], VAR[2], VAR[3], VAR[4], VAR[7], VAR[8], VAR[9])
            cur.execute(q4, values)
    conn.commit()


#Function to insert call info for a patient. This is the largest table, and contains genotype info, metrics such as depth for each individual. Each row is referenced by a foreign key to a unique variant. 
def insert_Call_info(conn, vcf_f):
    cur = conn.cursor()
    vcf_obj = make_vcf_object(vcf_f)
    SMPL = vcf_obj.metadata['IonReporterAnalysisName'][0]
    q1 = "SELECT id FROM RunInfo WHERE name = %s"
    val1 = (SMPL,)
    cur.execute(q1, val1)
    SMPLID = cur.fetchone()[0]
    for record in vcf_obj:
        print(record)
        print(record.INFO)
        for i in range(len(record.ALT)):
            PARAMS = []
            PARAMS.append(record.CHROM)
            PARAMS.append(record.POS)
            PARAMS.append(record.REF) # append ref allele
            PARAMS.append(str(record.ALT[i])) #append alt alleles
            try: # catch perticularities in vcf related to CNV, fusions, splicing or other SVs
                PARAMS.append(record.INFO['TYPE'][i])
                PARAMS.append(str(record.INFO['LEN'][i]))
            except:
                if isinstance(record.INFO['SVTYPE'], list):
                    if record.INFO['SVTYPE'][0] == 'CNV':
                        PARAMS.append(record.INFO['SVTYPE'][0])
                        PARAMS.append(str(record.INFO['LEN'][0]))
                    else:
                        PARAMS.append(record.INFO['SVTYPE'][0])
                        PARAMS.append(None)
                else:
                    if record.INFO['SVTYPE'] == 'CNV':
                        PARAMS.append(record.INFO['SVTYPE'])
                        PARAMS.append(str(record.INFO['LEN']))
                    else:
                        PARAMS.append(record.INFO['SVTYPE'])
                        PARAMS.append(None)
            NAME = '_'.join(str(e) for e in PARAMS) #unique name which is just the concatenation of the PARAMS list into a string
            NAME = NAME.replace('>','')
            NAME = NAME.replace('<','')
            # format data for insertion into table
            if NAME in ['chr21_36231771_T_T]chr8:93029591]_Fusion_None', 'chr9_5073770_G_T_snp_1', 'chr15_90631838_C_T_snp_1', 'chr17_7577559_G_A_snp_1']:
                print(record)
                print(record.INFO)
            # add runID, varID, genotype, depth, obsRef, obsAlt, AF, filter, copynumber, normCount. insert NULL where appropriate
            q2 = 'SELECT id FROM VarData WHERE name = %s' # get Var ID
            val2 = (NAME,)
            cur.execute(q2, val2)
            VARID = cur.fetchone()[0]
            try:
                COLNAME = record.samples[0].sample
                GT = record.genotype(COLNAME)['GT']
                GQ = record.genotype(COLNAME)['GQ']
            except:
                GT = None
                GQ = None
            if PARAMS[4] == 'CNV': #this if statement adds different info based on the variant of structural variant type. For example, CNVs have no alt allele. 
                CN =  record.genotype(COLNAME)['CN']
                if not record.FILTER:
                    FL = 'PASS'
                else:
                    FL = record.FILTER[0]
                q3 = '''INSERT IGNORE INTO CallData (sample, variant, genotype, geno_qual, coverage, ref_count, alt_count, norm_count, afreq, pass_filter, cn) 
                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )'''
                values = (SMPLID, VARID, GT, GQ, None, None, None, None, None, FL, CN)
                cur.execute(q3, values)
            elif PARAMS[4] == 'Fusion' or PARAMS[4] == 'RNAExonVariant' or PARAMS[4] == 'ExprControl': #these are all treated like fusions in the db
                try:
                    if not record.FILTER:
                        record.FILTER = ['PASS']
                    if record.FILTER[0] == 'PASS':
                        NC = record.INFO['NORM_COUNT']
                        DP = int(record.INFO['READ_COUNT'][0])
                        FL = record.FILTER[0]
                        q3 = '''INSERT IGNORE INTO CallData (sample, variant, genotype, geno_qual, coverage, ref_count, alt_count, norm_count, afreq, pass_filter, cn)
                        VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )'''
                        values = (SMPLID, VARID, GT, GQ, DP, None, None, NC, None, FL,None)
                        cur.execute(q3, values)
                except:
                    continue
            elif PARAMS[4] == '5p3pAssays': # The important metric here is 5p3pAssays, which is the imbalance score, added into the cn field
                DP = int(record.INFO['READ_COUNT'][0])
                CN = float(record.INFO['5P_3P_ASSAYS'])
                if not record.FILTER:
                    FL = 'PASS'
                else:
                    FL = record.FILTER[0]
                q3 = '''INSERT IGNORE INTO CallData (sample, variant, genotype, geno_qual, coverage, ref_count, alt_count, norm_count, afreq, pass_filter, cn) 
                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )'''
                values = (SMPLID, VARID, GT, GQ, DP, None, None, None, None,FL, CN)
                cur.execute(q3, values)
            elif PARAMS[4] == 'GeneExpression':
                DP = int(record.INFO['READ_COUNT'][0])
                #CN = float(record.INFO['5P_3P_ASSAYS'])
                if not record.FILTER:
                    FL = 'PASS'
                else:
                    FL = record.FILTER[0]
                q3 = '''INSERT IGNORE INTO CallData (sample, variant, genotype, geno_qual, coverage, ref_count, alt_count, norm_count, afreq, pass_filter, cn)
                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )'''
                values = (SMPLID, VARID, GT, GQ, DP, None, None, None, None,FL, None)
                cur.execute(q3, values)

            elif PARAMS[4] == 'RNAExonTiles': # As with 5p-3p assays, the imbalance score is added into the cn field and p-value is added to norm count field
                try:
                    NC = float(record.INFO['IMBALANCE_PVAL'])
                except:
                    NC = 1.00
                CN = float(record.INFO['IMBALANCE_SCORE'])
                if not record.FILTER:
                    FL = 'PASS'
                else:
                    FL = record.FILTER[0]
                q3 = '''INSERT IGNORE INTO CallData (sample, variant, genotype, geno_qual, coverage, ref_count, alt_count, norm_count, afreq, pass_filter, cn)
                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )'''
                values = (SMPLID, VARID, GT, GQ, None, None, None, NC, None,FL, CN)
                cur.execute(q3, values)
            else:
                DP = record.INFO['DP']
                RO = record.INFO['RO']
                AO = record.INFO['AO'][i]
                AF = str(record.INFO['AF'][i])
                if not record.FILTER:
                    FL = 'PASS'
                else:
                    FL = record.FILTER[0]
                q3 = '''INSERT IGNORE INTO CallData (sample, variant, genotype, geno_qual, coverage, ref_count, alt_count, norm_count, afreq, pass_filter, cn) 
                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )'''
                values = (SMPLID, VARID, GT, GQ, DP, RO, AO, None, AF, FL,None)
                cur.execute(q3, values)
    conn.commit()


#parser to define arguments
def _parse_args():
    """Parse command line arguments
    Returns
    ----------
    argparse.Namespace
        Contains parsed command line arguments
    """

    parser = argparse.ArgumentParser(
        description="\n=========Read and add VCF data to custom SQL db=========\n"
        "Usage: python3 ../Add_to_DB_v2.py -i input.vcf"
        "\n",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-i",
        "--input",
        default="None",
        required=True,
        help="input vcf file",
    )

    args = parser.parse_args()
    return args


# Main function
def main():
    #password_file = '/secrets/db-password'
    args = _parse_args()
    #pf = open(password_file, 'r')
    conn = mysql.connector.connect(host='db',user='usr',password='usrpass',database='vardb', port = 3306)
    ToolVerSanityCheck(conn, args.input)
    insert_Run_info(conn, args.input)
    insert_Var_types(conn, args.input)
    insert_HGVS(conn, args.input)
    insert_Var_info(conn, args.input)
    insert_Call_info(conn, args.input)
    conn.close()



if __name__ == "__main__":
    main()

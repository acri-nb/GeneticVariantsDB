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
        
        # Read exclusions
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
        
        # read-in data and change duplicated column headers
        df.columns = ['pass_filter','afreq','coverage','norm_count','sample','variant','IonWF_version','samplename','filedate','trname','transcript','HGVSc', 'HGVSp','gene']
        
        # get only HD200 and seracare samples (exclude unwanted samples)
        df = df[~df['samplename'].isin(exclusions)]
        
        # Get the variants of interest
        regions = []
        with open('/dash-files/regions.txt') as f:
            region = f.read().splitlines()
            regions = region
        
        # Filter by regions of interest
        df = df[df['variant'].isin(regions)]
        
        # Replace fusion gene names with readable names
        df.replace(["chr1_154142876_C_C[chr1:156844363[_Fusion_None",
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
        "chr19_1619110_C_C[chr1:164761731[_Fusion_None"],["TPM3(7) - NTRK1(10)",
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
        "TCF3(16)-PBX1(3)"], inplace = True)
        
        # Sort by date
        df = df.sort_values(["filedate","variant"])
        df = df.reset_index(drop=True)
        
        # Get limit from config
        limit = None
        with open('/dash-files/config.txt') as f:
            vals = f.read().splitlines()
            limit = int(vals[4])
        
        # Drop uninformative columns, add stdev for numerical values and group the entire table by variant
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
        import traceback
        traceback.print_exc()
        # Return empty DataFrame with correct columns to prevent crashes
        return pd.DataFrame(columns=['variant','gene','afreq', 'norm_count','sd', 'upper_bound', 'lower_bound','coverage','trname','HGVSc','HGVSp','samplename'])
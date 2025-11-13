-- Phase 2: Pre-aggregated views to optimize dashboard performance
-- These views pre-calculate statistics to avoid repeated computations

-- 1. View for basic statistics by variant and sample
CREATE OR REPLACE VIEW vw_variant_stats AS
SELECT 
    v.id as variant_id,
    v.name as variant_name,
    g.name as gene_name,
    c.sample,
    r.name as sample_name,
    r.filedate,
    r.IonWF_version,
    AVG(c.afreq) as avg_afreq,
    STDDEV(c.afreq) as stddev_afreq,
    AVG(c.coverage) as avg_coverage,
    COUNT(*) as total_calls,
    SUM(CASE WHEN c.pass_filter = 1 THEN 1 ELSE 0 END) as pass_count,
    SUM(CASE WHEN c.pass_filter = 0 THEN 1 ELSE 0 END) as fail_count,
    MIN(c.afreq) as min_afreq,
    MAX(c.afreq) as max_afreq,
    -- Detection of variant type (DNA vs RNA)
    CASE 
        WHEN v.name REGEXP 'c\\.' THEN 'DNA'
        ELSE 'RNA'
    END as biomolecule_type
FROM CallData c
INNER JOIN VarData v ON v.id = c.variant
INNER JOIN RunInfo r ON r.id = c.sample
LEFT JOIN Genes g ON g.id = v.gene
GROUP BY v.id, v.name, g.name, c.sample, r.name, r.filedate, r.IonWF_version;

-- 2. View for Levey-Jennings statistics (moving averages)
CREATE OR REPLACE VIEW vw_levey_jennings_stats AS
SELECT 
    vs.variant_id,
    vs.variant_name,
    vs.gene_name,
    vs.sample,
    vs.sample_name,
    vs.filedate,
    vs.biomolecule_type,
    vs.avg_afreq,
    vs.stddev_afreq,
    vs.avg_coverage,
    -- Calculate moving averages over 20 previous samples
    AVG(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as rolling_mean_afreq,
    STDDEV(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as rolling_stddev_afreq,
    -- Calculate control limits (±2σ and ±3σ)
    AVG(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) + 2 * STDDEV(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as ucl_2sigma,
    AVG(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) - 2 * STDDEV(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as lcl_2sigma,
    AVG(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) + 3 * STDDEV(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as ucl_3sigma,
    AVG(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) - 3 * STDDEV(vs.avg_afreq) OVER (
        PARTITION BY vs.variant_id 
        ORDER BY vs.filedate 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as lcl_3sigma,
    -- Flag for out-of-limit values
    CASE 
        WHEN vs.avg_afreq > (
            AVG(vs.avg_afreq) OVER (
                PARTITION BY vs.variant_id 
                ORDER BY vs.filedate 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) + 3 * STDDEV(vs.avg_afreq) OVER (
                PARTITION BY vs.variant_id 
                ORDER BY vs.filedate 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            )
        ) OR vs.avg_afreq < (
            AVG(vs.avg_afreq) OVER (
                PARTITION BY vs.variant_id 
                ORDER BY vs.filedate 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) - 3 * STDDEV(vs.avg_afreq) OVER (
                PARTITION BY vs.variant_id 
                ORDER BY vs.filedate 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            )
        ) THEN 'OUT_OF_CONTROL'
        WHEN vs.avg_afreq > (
            AVG(vs.avg_afreq) OVER (
                PARTITION BY vs.variant_id 
                ORDER BY vs.filedate 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) + 2 * STDDEV(vs.avg_afreq) OVER (
                PARTITION BY vs.variant_id 
                ORDER BY vs.filedate 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            )
        ) OR vs.avg_afreq < (
            AVG(vs.avg_afreq) OVER (
                PARTITION BY vs.variant_id 
                ORDER BY vs.filedate 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) - 2 * STDDEV(vs.avg_afreq) OVER (
                PARTITION BY vs.variant_id 
                ORDER BY vs.filedate 
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            )
        ) THEN 'WARNING'
        ELSE 'IN_CONTROL'
    END as control_status
FROM vw_variant_stats vs;

-- 3. View for summary by biomolecular type and QC status
CREATE OR REPLACE VIEW vw_summary_by_biomolecule AS
SELECT 
    biomolecule_type,
    COUNT(DISTINCT variant_id) as total_variants,
    COUNT(DISTINCT sample) as total_samples,
    AVG(avg_afreq) as overall_avg_afreq,
    STDDEV(avg_afreq) as overall_stddev_afreq,
    SUM(pass_count) as total_pass,
    SUM(fail_count) as total_fail,
    SUM(pass_count) / (SUM(pass_count) + SUM(fail_count)) * 100 as pass_rate_percent,
    COUNT(CASE WHEN avg_afreq = 0 THEN 1 END) as zero_afreq_count
FROM vw_variant_stats
GROUP BY biomolecule_type;

-- 4. View for recent samples (dashboard dropdown)
CREATE OR REPLACE VIEW vw_recent_samples AS
SELECT DISTINCT
    r.id as sample_id,
    r.name as sample_name,
    r.filedate,
    r.IonWF_version,
    COUNT(DISTINCT c.variant) as variant_count,
    AVG(c.afreq) as avg_afreq,
    AVG(c.coverage) as avg_coverage,
    SUM(CASE WHEN c.pass_filter = 1 THEN 1 ELSE 0 END) as pass_count,
    SUM(CASE WHEN c.pass_filter = 0 THEN 1 ELSE 0 END) as fail_count
FROM RunInfo r
INNER JOIN CallData c ON r.id = c.sample
GROUP BY r.id, r.name, r.filedate, r.IonWF_version
ORDER BY r.filedate DESC
LIMIT 50;

-- 5. View for detailed QC failures
CREATE OR REPLACE VIEW vw_qc_failures AS
SELECT 
    v.name as variant_name,
    g.name as gene_name,
    r.name as sample_name,
    r.filedate,
    c.afreq,
    c.coverage,
    c.norm_count,
    c.pass_filter,
    h.HGVSc,
    h.HGVSp,
    t.name as transcript_name,
    CASE 
        WHEN v.name REGEXP 'c\\.' THEN 'DNA'
        ELSE 'RNA'
    END as biomolecule_type,
    CASE 
        WHEN c.pass_filter = 0 THEN 'FILTER_FAIL'
        WHEN c.afreq = 0 THEN 'ZERO_AFREQ'
        ELSE 'OTHER'
    END as failure_reason
FROM CallData c
INNER JOIN VarData v ON v.id = c.variant
INNER JOIN RunInfo r ON r.id = c.sample
LEFT JOIN HGVS h ON h.id = v.hgvs
LEFT JOIN Transcripts t ON t.id = h.transcript
LEFT JOIN Genes g ON g.id = v.gene
WHERE c.pass_filter = 0 OR c.afreq = 0;

-- Indexes to optimize view performance (MySQL 5.7 compatible)
CREATE INDEX idx_runinfo_filedate ON RunInfo(filedate);
CREATE INDEX idx_vardata_name_pattern ON VarData(name(20));
CREATE INDEX idx_calldata_afreq ON CallData(afreq);
CREATE INDEX idx_calldata_pass_filter ON CallData(pass_filter);

-- Statistics for MySQL optimizer
ANALYZE TABLE CallData, VarData, RunInfo, Genes, HGVS, Transcripts;
-- Performance Optimization Indexes for VarDB
-- These indexes will significantly improve query performance for the dashboard

-- Index for CallData table (most queried)
CREATE INDEX IF NOT EXISTS idx_calldata_sample ON CallData(sample);
CREATE INDEX IF NOT EXISTS idx_calldata_variant ON CallData(variant);
CREATE INDEX IF NOT EXISTS idx_calldata_variant_sample ON CallData(variant, sample);

-- Index for VarData table
CREATE INDEX IF NOT EXISTS idx_vardata_gene ON VarData(gene);
CREATE INDEX IF NOT EXISTS idx_vardata_name ON VarData(name);
CREATE INDEX IF NOT EXISTS idx_vardata_hgvs ON VarData(hgvs);

-- Index for RunInfo table (used for filtering by date)
CREATE INDEX IF NOT EXISTS idx_runinfo_filedate ON RunInfo(filedate);
CREATE INDEX IF NOT EXISTS idx_runinfo_name ON RunInfo(name);

-- Index for HGVS table
CREATE INDEX IF NOT EXISTS idx_hgvs_transcript ON HGVS(transcript);
CREATE INDEX IF NOT EXISTS idx_hgvs_gene ON HGVS(gene);

-- Index for Genes table
CREATE INDEX IF NOT EXISTS idx_genes_name ON Genes(name);

-- Index for Transcripts table
CREATE INDEX IF NOT EXISTS idx_transcripts_name ON Transcripts(name);

-- Show index creation status
SHOW INDEX FROM CallData;
SHOW INDEX FROM VarData;
SHOW INDEX FROM RunInfo;
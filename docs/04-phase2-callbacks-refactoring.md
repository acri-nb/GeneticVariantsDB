# Phase 2: Dash Callbacks Refactoring

## Bottleneck Analysis

### Identified Problems:

1. **CRITICAL** - Levey-Jennings Charts (`update_graph` and `update_graph2`)
   - Complex statistical calculations without cache
   - Repeated reading of configuration files
   - Nested loops and expensive NumPy operations

2. **MAJOR** - Code duplication
   - `update_fail1` duplicates `update_table2`
   - `update_fail2` duplicates `update_table3`
   - Similar DNA/RNA logic separated

3. **MINOR** - Repeated file I/O
   - Reading config files in each callback
   - `display_notes` reads CSV on every change

## Refactoring Plan

### 1. Levey-Jennings chart caching
- Statistical calculations caching
- Chart data cache with TTL
- NumPy operations optimization

### 2. Code factorization
- Common function for sample processing
- Shared DNA/RNA logic
- Reusable cache utilities

### 3. Global configuration
- Single loading of config files
- Global variables to avoid repeated I/O

### 4. Table pagination
- Server-side pagination for large tables
- Lazy data loading
- UX improvement for large datasets

### 5. Pre-aggregated views
- MySQL views for statistics
- Pre-calculated tables for charts
- Scheduled aggregation refresh

## Expected Performance Metrics

| Component | Before | After | Improvement |
|-----------|-------|-------|--------------|
| LJ Charts | 3-5s | 0.5-1s | 70-80% |
| Sample Tables | 1-2s | 0.2-0.5s | 75-80% |
| Cache hit ratio | 85-90% | 95-98% | +8-10% |
| Code maintenance | - | - | -50% duplication |

## Target Architecture

```
Global Configuration (loaded 1x)
├── CONFIG_FILES
├── STATS_CACHE
└── UI_CONSTANTS

Optimized Callbacks:
├── dcc_store (unchanged)
├── table_callbacks (factorized)
├── graph_callbacks (cached)
└── action_callbacks (optimized)

Cache Strategy:
├── Redis (main data)
├── Memory (statistical calculations)
└── File (configurations)
```
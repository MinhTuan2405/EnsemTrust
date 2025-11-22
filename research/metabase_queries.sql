-- ============================================================================
-- METABASE SQL QUERIES FOR ENSEMTRUST - FAKE NEWS DETECTION
-- ============================================================================
-- These queries are designed to work with Trino query engine
-- Catalog: delta (Delta Lake tables in MinIO/S3)
-- Schema: gold
-- Table: news_dataset
-- ============================================================================

-- ============================================================================
-- 1. OVERVIEW & KPI QUERIES
-- ============================================================================

-- 1.1 Overall Statistics Dashboard
-- Purpose: High-level metrics for executive dashboard
SELECT 
    COUNT(*) as total_articles,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_news_count,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real_news_count,
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as fake_percentage,
    ROUND(100.0 * SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as real_percentage,
    COUNT(DISTINCT subject) as unique_subjects,
    COUNT(DISTINCT year) as year_span,
    ROUND(AVG(text_length), 2) as avg_text_length,
    ROUND(AVG(title_length), 2) as avg_title_length
FROM delta.gold.news_dataset;


-- 1.2 Label Distribution (for pie charts)
-- Purpose: Simple label distribution visualization
SELECT 
    CASE 
        WHEN label = 0 THEN 'Fake News'
        WHEN label = 1 THEN 'Real News'
        ELSE 'Unknown'
    END as news_type,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM delta.gold.news_dataset
GROUP BY label
ORDER BY label;


-- 1.3 Daily Statistics Summary
-- Purpose: Quick daily metrics
SELECT 
    CURRENT_DATE as report_date,
    COUNT(*) as total_records,
    COUNT(DISTINCT subject) as active_subjects,
    ROUND(AVG(text_length), 0) as avg_article_length,
    MAX(text_length) as longest_article,
    MIN(text_length) as shortest_article
FROM delta.gold.news_dataset;


-- ============================================================================
-- 2. SUBJECT ANALYSIS QUERIES
-- ============================================================================

-- 2.1 Subject Distribution Overview
-- Purpose: Articles count by subject with percentage
SELECT 
    subject,
    COUNT(*) as article_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_count,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real_count
FROM delta.gold.news_dataset
GROUP BY subject
ORDER BY article_count DESC;


-- 2.2 Subject vs Label Analysis
-- Purpose: Cross-tabulation of subjects and labels
SELECT 
    subject,
    COUNT(*) as total,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_news,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real_news,
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as fake_percentage,
    ROUND(100.0 * SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as real_percentage
FROM delta.gold.news_dataset
GROUP BY subject
ORDER BY total DESC;


-- 2.3 Top Subjects by Fake News
-- Purpose: Identify subjects with highest fake news concentration
SELECT 
    subject,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_count,
    COUNT(*) as total_count,
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as fake_rate
FROM delta.gold.news_dataset
GROUP BY subject
HAVING COUNT(*) >= 10  -- Filter subjects with at least 10 articles
ORDER BY fake_rate DESC
LIMIT 10;


-- 2.4 Subject Performance Comparison
-- Purpose: Compare metrics across subjects
SELECT 
    subject,
    COUNT(*) as total_articles,
    ROUND(AVG(text_length), 0) as avg_text_length,
    ROUND(AVG(title_length), 0) as avg_title_length,
    MIN(text_length) as min_text_length,
    MAX(text_length) as max_text_length,
    ROUND(STDDEV(text_length), 0) as stddev_text_length
FROM delta.gold.news_dataset
GROUP BY subject
ORDER BY total_articles DESC;


-- ============================================================================
-- 3. TEMPORAL ANALYSIS QUERIES
-- ============================================================================

-- 3.1 Year-wise Distribution
-- Purpose: Trend analysis by year
SELECT 
    year,
    COUNT(*) as total_articles,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_news,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real_news,
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as fake_percentage
FROM delta.gold.news_dataset
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;


-- 3.2 Month-wise Distribution (All Years Combined)
-- Purpose: Seasonal patterns analysis
SELECT 
    month,
    COUNT(*) as total_articles,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_news,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real_news,
    ROUND(AVG(text_length), 0) as avg_text_length
FROM delta.gold.news_dataset
WHERE month IS NOT NULL
GROUP BY month
ORDER BY 
    CASE month
        WHEN 'January' THEN 1
        WHEN 'February' THEN 2
        WHEN 'March' THEN 3
        WHEN 'April' THEN 4
        WHEN 'May' THEN 5
        WHEN 'June' THEN 6
        WHEN 'July' THEN 7
        WHEN 'August' THEN 8
        WHEN 'September' THEN 9
        WHEN 'October' THEN 10
        WHEN 'November' THEN 11
        WHEN 'December' THEN 12
    END;


-- 3.3 Year-Month Time Series
-- Purpose: Detailed time series for trend charts
SELECT 
    year_month,
    COUNT(*) as total_articles,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_news,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real_news,
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as fake_rate
FROM delta.gold.news_dataset
WHERE year_month IS NOT NULL
GROUP BY year_month
ORDER BY year_month;


-- 3.4 Recent Trends (Last 12 Months by Year-Month)
-- Purpose: Focus on recent activity
SELECT 
    year_month,
    COUNT(*) as articles,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real
FROM delta.gold.news_dataset
WHERE year_month IS NOT NULL
GROUP BY year_month
ORDER BY year_month DESC
LIMIT 12;


-- 3.5 Yearly Growth Analysis
-- Purpose: YoY comparison
SELECT 
    year,
    COUNT(*) as articles_count,
    LAG(COUNT(*)) OVER (ORDER BY year) as prev_year_count,
    COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY year) as growth,
    ROUND(100.0 * (COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY year)) / 
          NULLIF(LAG(COUNT(*)) OVER (ORDER BY year), 0), 2) as growth_percentage
FROM delta.gold.news_dataset
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;


-- ============================================================================
-- 4. TEXT LENGTH ANALYSIS QUERIES
-- ============================================================================

-- 4.1 Text Length Distribution by Label
-- Purpose: Compare article lengths between fake and real news
SELECT 
    CASE 
        WHEN label = 0 THEN 'Fake News'
        WHEN label = 1 THEN 'Real News'
    END as news_type,
    COUNT(*) as count,
    ROUND(AVG(text_length), 0) as avg_length,
    ROUND(AVG(title_length), 0) as avg_title_length,
    MIN(text_length) as min_length,
    MAX(text_length) as max_length,
    ROUND(STDDEV(text_length), 0) as stddev_length,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY text_length) as median_length
FROM delta.gold.news_dataset
GROUP BY label
ORDER BY label;


-- 4.2 Text Length Buckets
-- Purpose: Categorize articles by length for histogram
SELECT 
    CASE 
        WHEN text_length < 500 THEN '0-500'
        WHEN text_length < 1000 THEN '500-1000'
        WHEN text_length < 2000 THEN '1000-2000'
        WHEN text_length < 3000 THEN '2000-3000'
        WHEN text_length < 5000 THEN '3000-5000'
        ELSE '5000+'
    END as length_bucket,
    COUNT(*) as count,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_count,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real_count
FROM delta.gold.news_dataset
GROUP BY 
    CASE 
        WHEN text_length < 500 THEN '0-500'
        WHEN text_length < 1000 THEN '500-1000'
        WHEN text_length < 2000 THEN '1000-2000'
        WHEN text_length < 3000 THEN '2000-3000'
        WHEN text_length < 5000 THEN '3000-5000'
        ELSE '5000+'
    END
ORDER BY 
    CASE 
        WHEN text_length < 500 THEN 1
        WHEN text_length < 1000 THEN 2
        WHEN text_length < 2000 THEN 3
        WHEN text_length < 3000 THEN 4
        WHEN text_length < 5000 THEN 5
        ELSE 6
    END;


-- 4.3 Title Length Analysis
-- Purpose: Analyze title characteristics
SELECT 
    CASE 
        WHEN label = 0 THEN 'Fake News'
        WHEN label = 1 THEN 'Real News'
    END as news_type,
    ROUND(AVG(title_length), 2) as avg_title_length,
    MIN(title_length) as min_title_length,
    MAX(title_length) as max_title_length,
    ROUND(STDDEV(title_length), 2) as stddev_title_length,
    COUNT(CASE WHEN title_length < 50 THEN 1 END) as short_titles,
    COUNT(CASE WHEN title_length BETWEEN 50 AND 100 THEN 1 END) as medium_titles,
    COUNT(CASE WHEN title_length > 100 THEN 1 END) as long_titles
FROM delta.gold.news_dataset
GROUP BY label
ORDER BY label;


-- 4.4 Outlier Detection - Very Long Articles
-- Purpose: Identify unusually long articles
SELECT 
    CASE WHEN label = 0 THEN 'Fake' ELSE 'Real' END as type,
    subject,
    title,
    text_length,
    year_month
FROM delta.gold.news_dataset
WHERE text_length > (SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY text_length) FROM delta.gold.news_dataset)
ORDER BY text_length DESC
LIMIT 50;


-- 4.5 Outlier Detection - Very Short Articles
-- Purpose: Identify unusually short articles
SELECT 
    CASE WHEN label = 0 THEN 'Fake' ELSE 'Real' END as type,
    subject,
    title,
    text_length,
    year_month
FROM delta.gold.news_dataset
WHERE text_length < (SELECT PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY text_length) FROM delta.gold.news_dataset)
    AND text_length > 0
ORDER BY text_length ASC
LIMIT 50;


-- ============================================================================
-- 5. ADVANCED ANALYTICS QUERIES
-- ============================================================================

-- 5.1 Subject-Year Matrix
-- Purpose: Heatmap data for subject activity over time
SELECT 
    subject,
    year,
    COUNT(*) as article_count,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_count,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real_count
FROM delta.gold.news_dataset
WHERE year IS NOT NULL
GROUP BY subject, year
ORDER BY subject, year;


-- 5.2 Fake News Concentration by Period
-- Purpose: Identify time periods with high fake news activity
SELECT 
    year_month,
    COUNT(*) as total,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_count,
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as fake_rate,
    CASE 
        WHEN ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) > 60 THEN 'High Risk'
        WHEN ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) > 40 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END as risk_level
FROM delta.gold.news_dataset
WHERE year_month IS NOT NULL
GROUP BY year_month
HAVING COUNT(*) >= 10
ORDER BY fake_rate DESC;


-- 5.3 Subject Diversity by Label
-- Purpose: Understand which label has more diverse subjects
SELECT 
    CASE WHEN label = 0 THEN 'Fake News' ELSE 'Real News' END as news_type,
    COUNT(DISTINCT subject) as unique_subjects,
    COUNT(*) as total_articles,
    ROUND(1.0 * COUNT(*) / COUNT(DISTINCT subject), 2) as articles_per_subject
FROM delta.gold.news_dataset
GROUP BY label;


-- 5.4 Correlation: Text Length vs Label
-- Purpose: Statistical relationship analysis
SELECT 
    CASE 
        WHEN text_length < 1000 THEN 'Short'
        WHEN text_length < 3000 THEN 'Medium'
        ELSE 'Long'
    END as length_category,
    COUNT(*) as total,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake,
    SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real,
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as fake_percentage
FROM delta.gold.news_dataset
GROUP BY 
    CASE 
        WHEN text_length < 1000 THEN 'Short'
        WHEN text_length < 3000 THEN 'Medium'
        ELSE 'Long'
    END
ORDER BY fake_percentage DESC;


-- 5.5 Top N Analysis - Longest Fake vs Real Articles
-- Purpose: Compare extreme cases
WITH ranked_articles AS (
    SELECT 
        CASE WHEN label = 0 THEN 'Fake' ELSE 'Real' END as type,
        subject,
        title,
        text_length,
        year,
        ROW_NUMBER() OVER (PARTITION BY label ORDER BY text_length DESC) as rank
    FROM delta.gold.news_dataset
)
SELECT 
    type,
    subject,
    LEFT(title, 100) as title_preview,
    text_length,
    year,
    rank
FROM ranked_articles
WHERE rank <= 10
ORDER BY type, rank;


-- ============================================================================
-- 6. DATA QUALITY & MONITORING QUERIES
-- ============================================================================

-- 6.1 Data Completeness Check
-- Purpose: Monitor data quality
SELECT 
    COUNT(*) as total_records,
    SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) as missing_title,
    SUM(CASE WHEN text IS NULL OR text = '' THEN 1 ELSE 0 END) as missing_text,
    SUM(CASE WHEN subject IS NULL OR subject = '' THEN 1 ELSE 0 END) as missing_subject,
    SUM(CASE WHEN year IS NULL OR year = '' THEN 1 ELSE 0 END) as missing_year,
    SUM(CASE WHEN month IS NULL OR month = '' THEN 1 ELSE 0 END) as missing_month,
    SUM(CASE WHEN text_length = 0 THEN 1 ELSE 0 END) as zero_length_text,
    ROUND(100.0 * SUM(CASE WHEN title IS NOT NULL AND title != '' 
                          AND text IS NOT NULL AND text != ''
                          AND subject IS NOT NULL AND subject != '' THEN 1 ELSE 0 END) / COUNT(*), 2) as data_completeness_pct
FROM delta.gold.news_dataset;


-- 6.2 Record Count by Date Range
-- Purpose: Data ingestion monitoring
SELECT 
    year,
    COUNT(*) as record_count,
    MIN(text_length) as min_length,
    MAX(text_length) as max_length,
    ROUND(AVG(text_length), 0) as avg_length
FROM delta.gold.news_dataset
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year DESC;


-- 6.3 Label Distribution Quality Check
-- Purpose: Ensure balanced dataset
SELECT 
    label,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
    CASE 
        WHEN ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) BETWEEN 40 AND 60 THEN 'Balanced'
        WHEN ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) > 60 THEN 'Over-represented'
        ELSE 'Under-represented'
    END as status
FROM delta.gold.news_dataset
GROUP BY label
ORDER BY label;


-- 6.4 Anomaly Detection - Duplicate Titles
-- Purpose: Find potential data quality issues
SELECT 
    title,
    COUNT(*) as occurrence,
    COUNT(DISTINCT label) as different_labels,
    STRING_AGG(DISTINCT CAST(label AS VARCHAR), ', ') as labels,
    STRING_AGG(DISTINCT subject, ', ') as subjects
FROM delta.gold.news_dataset
GROUP BY title
HAVING COUNT(*) > 1
ORDER BY occurrence DESC
LIMIT 20;


-- ============================================================================
-- 7. DASHBOARD-SPECIFIC QUERIES
-- ============================================================================

-- 7.1 Executive Summary Card
-- Purpose: Single-row summary for dashboard header
SELECT 
    CAST(COUNT(*) AS VARCHAR) || ' Total Articles' as metric1,
    CAST(SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) AS VARCHAR) || ' Fake (' || 
        CAST(ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS VARCHAR) || '%)' as metric2,
    CAST(COUNT(DISTINCT subject) AS VARCHAR) || ' Subjects' as metric3,
    CAST(COUNT(DISTINCT year) AS VARCHAR) || ' Years' as metric4
FROM delta.gold.news_dataset;


-- 7.2 Gauge Chart - Fake News Rate
-- Purpose: Single value for gauge visualization
SELECT 
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as fake_news_percentage
FROM delta.gold.news_dataset;


-- 7.3 Trending Subjects (Last Year)
-- Purpose: Popular subjects in recent period
SELECT 
    subject,
    COUNT(*) as article_count,
    SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake_count
FROM delta.gold.news_dataset
WHERE year = (SELECT MAX(year) FROM delta.gold.news_dataset WHERE year IS NOT NULL)
GROUP BY subject
ORDER BY article_count DESC
LIMIT 10;


-- 7.4 Weekly Snapshot (for consistent monitoring)
-- Purpose: Standard weekly report metrics
SELECT 
    'Week of ' || CAST(CURRENT_DATE AS VARCHAR) as period,
    COUNT(*) as total_articles,
    ROUND(100.0 * SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as fake_rate,
    COUNT(DISTINCT subject) as subjects_covered,
    ROUND(AVG(text_length), 0) as avg_article_length,
    COUNT(DISTINCT year_month) as active_periods
FROM delta.gold.news_dataset;


-- ============================================================================
-- 8. PARAMETERIZED QUERIES (Use with Metabase Variables)
-- ============================================================================

-- 8.1 Filter by Subject (Use {{subject}} variable in Metabase)
-- SELECT * FROM delta.gold.news_dataset WHERE subject = {{subject}};


-- 8.2 Filter by Year (Use {{year}} variable)
-- SELECT * FROM delta.gold.news_dataset WHERE year = {{year}};


-- 8.3 Filter by Label (Use {{label}} variable: 0 for Fake, 1 for Real)
-- SELECT * FROM delta.gold.news_dataset WHERE label = {{label}};


-- 8.4 Date Range Filter (Use {{start_year}} and {{end_year}})
-- SELECT * FROM delta.gold.news_dataset 
-- WHERE year BETWEEN {{start_year}} AND {{end_year}};


-- 8.5 Combined Filters
-- SELECT 
--     subject,
--     year_month,
--     COUNT(*) as count,
--     SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) as fake,
--     SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) as real
-- FROM delta.gold.news_dataset
-- WHERE 1=1
--     [[AND subject = {{subject}}]]
--     [[AND year = {{year}}]]
--     [[AND label = {{label}}]]
-- GROUP BY subject, year_month
-- ORDER BY year_month DESC;


-- ============================================================================
-- NOTES FOR METABASE USAGE:
-- ============================================================================
-- 1. Connection: Use Trino connector in Metabase
-- 2. Host: trino (or localhost:8090 if external)
-- 3. Catalog: delta
-- 4. Schema: gold
-- 5. Table: news_dataset
--
-- VISUALIZATION RECOMMENDATIONS:
-- - Query 1.1, 1.2: Use for Overview Dashboard
-- - Query 2.1, 2.2: Bar charts for Subject Analysis
-- - Query 3.1, 3.2, 3.3: Line charts for Time Series
-- - Query 4.2: Histogram for Length Distribution
-- - Query 5.2: Table with conditional formatting for Risk Levels
-- - Query 7.2: Gauge chart for Fake News Rate
--
-- PERFORMANCE TIPS:
-- - Add LIMIT clauses for large result sets
-- - Use aggregations instead of raw data when possible
-- - Create materialized views for frequently-used complex queries
-- - Add WHERE clauses to filter unnecessary data
-- ============================================================================

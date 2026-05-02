

### 1. Introduction and Workplace Description
I completed my professional internship at the Unified Situational Center (CPCP), serving as a Data Analyst Intern. The Situational Center is the core municipal entity responsible for processing, categorizing, and assigning citizen appeals regarding various infrastructure, transportation, and public utility issues. During my internship, I worked closely with the technical and operational teams to leverage data analytics for improving the speed and efficiency of municipal services.

### 2. Problem Statement and Objectives
A significant operational bottleneck at the center was the manual tracking of citizen complaints, which made it highly challenging to identify delayed tasks. Each department operates under a strict Service Level Agreement (SLA) that dictates the maximum allowable days to resolve an issue. 

The main objective of my internship was to design and implement an automated data pipeline that could autonomously calculate SLA violations, analyze processing times, and visualize the performance of various municipal departments through an interactive dashboard.

*Note on Data Privacy (NDA): Due to strict Non-Disclosure Agreements, the use of real citizen data was prohibited. To proceed with the technical demonstration, I engineered a mathematically accurate synthetic dataset comprising 10,000 records that flawlessly mimics the production environment's statistical distributions.*

### 3. Technical Contributions & Implementation

#### 3.1. Relational Database Design & SQL Aggregation
Instead of relying on flat CSV files, I designed a localized relational database using SQLite to simulate the real-world infrastructure of the Situational Center. The schema consists of three normalized tables: `citizens`, `departments`, and `appeals` (fact table). I wrote optimized SQL queries incorporating `JOIN` operations to merge these tables and calculate SLA breaches directly at the database level.

```sql
/* SQL snippet demonstrating the extraction of SLA breaches */
SELECT 
    d.dept_name,
    COUNT(a.appeal_id) as total_appeals,
    AVG(JULIANDAY(a.closed_at) - JULIANDAY(a.created_at)) as avg_processing_days,
    SUM(CASE WHEN (JULIANDAY(a.closed_at) - JULIANDAY(a.created_at)) > d.sla_days_limit THEN 1 ELSE 0 END) as sla_breaches
FROM appeals a
JOIN departments d ON a.dept_id = d.dept_id
WHERE a.status = 'Closed'
GROUP BY d.dept_name;
```

#### 3.2. Data Preprocessing and Feature Engineering (Pandas)
After data extraction, I utilized the Python `pandas` library to perform Extract, Transform, and Load (ETL) operations. I engineered several new features required for deep analytics, such as precisely calculating processing times in days and identifying peak submission hours.

```python
# Python/Pandas snippet for feature engineering
df['created_at'] = pd.to_datetime(df['created_at'])
df['closed_at'] = pd.to_datetime(df['closed_at'])

df['processing_time_days'] = (df['closed_at'] - df['created_at']).dt.total_seconds() / 86400
df['is_sla_breached'] = df['processing_time_days'] > df['sla_days_limit']
df['day_of_week'] = df['created_at'].dt.day_name()
```

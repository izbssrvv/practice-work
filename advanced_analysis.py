import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta, datetime
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# ШАГ 1: Создание реляционной БД и генерация данных (Имитация DWH)
# ==========================================
print("1. Инициализация базы данных SQLite и генерация данных...")
conn = sqlite3.connect('situational_center.db')
cursor = conn.cursor()

# Создаем таблицы
cursor.executescript('''
    DROP TABLE IF EXISTS appeals;
    DROP TABLE IF EXISTS departments;
    DROP TABLE IF EXISTS citizens;

    CREATE TABLE departments (
        dept_id INTEGER PRIMARY KEY,
        dept_name TEXT,
        sla_days_limit INTEGER
    );

    CREATE TABLE citizens (
        citizen_id INTEGER PRIMARY KEY,
        region TEXT,
        registration_date DATE
    );

    CREATE TABLE appeals (
        appeal_id TEXT PRIMARY KEY,
        citizen_id INTEGER,
        dept_id INTEGER,
        category TEXT,
        priority TEXT,
        description_length INTEGER,
        created_at TIMESTAMP,
        closed_at TIMESTAMP,
        status TEXT,
        FOREIGN KEY(citizen_id) REFERENCES citizens(citizen_id),
        FOREIGN KEY(dept_id) REFERENCES departments(dept_id)
    );
''')

# Заполняем справочники
np.random.seed(100)
depts = [
    (1, 'Dept of Transportation', 14),
    (2, 'Housing Administration', 21),
    (3, 'Healthcare Board', 7),
    (4, 'Education Ministry', 10),
    (5, 'Public Utilities', 5)
]
cursor.executemany("INSERT INTO departments VALUES (?, ?, ?)", depts)

regions = ['Astana', 'Almaty', 'Shymkent', 'Karaganda', 'Aktobe']
citizens = [(i, np.random.choice(regions, p=[0.3, 0.35, 0.15, 0.1, 0.1]), 
             f"202{np.random.randint(0, 5)}-{np.random.randint(1, 13):02d}-01") for i in range(1, 5001)]
cursor.executemany("INSERT INTO citizens VALUES (?, ?, ?)", citizens)

# Генерируем 10,000 сложных обращений
n_appeals = 10000
categories = ['Infrastructure', 'Service Quality', 'Financial Support', 'Information Request']
priorities = ['High', 'Medium', 'Low']

start_date = pd.to_datetime('2025-10-01')
created_dates = start_date + pd.to_timedelta(np.random.randint(0, 180, n_appeals), unit='D') \
                + pd.to_timedelta(np.random.randint(0, 24, n_appeals), unit='h')

data_appeals = []
for i in range(n_appeals):
    created = created_dates[i]
    status = np.random.choice(['Closed', 'In Progress'], p=[0.85, 0.15])
    priority = np.random.choice(priorities, p=[0.2, 0.5, 0.3])
    dept_id = np.random.randint(1, 6)
    
    # Сложность жалобы (длина текста) влияет на время решения
    desc_len = int(np.random.normal(200, 50)) if priority == 'High' else int(np.random.normal(100, 30))
    desc_len = max(20, desc_len)
    
    if status == 'Closed':
        # Базовое время + задержка от длины текста и приоритета
        base_days = 2 if priority == 'High' else (5 if priority == 'Medium' else 10)
        processing_time = base_days + (desc_len / 50) + np.random.normal(0, 3)
        closed = created + pd.to_timedelta(max(1, processing_time), unit='D')
    else:
        closed = None
        
    data_appeals.append((f"APP-{20000+i}", np.random.randint(1, 5001), dept_id, 
                         np.random.choice(categories), priority, desc_len, 
                         created.strftime('%Y-%m-%d %H:%M:%S'), 
                         closed.strftime('%Y-%m-%d %H:%M:%S') if closed else None, 
                         status))

cursor.executemany("INSERT INTO appeals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data_appeals)
conn.commit()

# ==========================================
# ШАГ 2: Сложный SQL-запрос (Неделя 4 по плану)
# ==========================================
print("\n2. Выявление департаментов-аутсайдеров с помощью SQL (JOIN & Aggregation)...")
sql_query = """
SELECT 
    d.dept_name,
    COUNT(a.appeal_id) as total_appeals,
    AVG(JULIANDAY(a.closed_at) - JULIANDAY(a.created_at)) as avg_processing_days,
    SUM(CASE WHEN (JULIANDAY(a.closed_at) - JULIANDAY(a.created_at)) > d.sla_days_limit THEN 1 ELSE 0 END) as sla_breaches
FROM appeals a
JOIN departments d ON a.dept_id = d.dept_id
WHERE a.status = 'Closed'
GROUP BY d.dept_name
ORDER BY sla_breaches DESC;
"""
sql_results = pd.read_sql(sql_query, conn)
print(sql_results.to_string())

# ==========================================
# ШАГ 3: Preprocessing & Advanced Pandas (Недели 3-5)
# ==========================================
# Выгружаем полный датасет для анализа
full_query = """
SELECT a.appeal_id, c.region, d.dept_name, d.sla_days_limit, a.category, a.priority, 
       a.description_length, a.created_at, a.closed_at, a.status
FROM appeals a
JOIN citizens c ON a.citizen_id = c.citizen_id
JOIN departments d ON a.dept_id = d.dept_id
"""
df = pd.read_sql(full_query, conn)
df['created_at'] = pd.to_datetime(df['created_at'])
df['closed_at'] = pd.to_datetime(df['closed_at'])

# Feature Engineering
df['processing_time_days'] = (df['closed_at'] - df['created_at']).dt.total_seconds() / 86400
df['is_sla_breached'] = df['processing_time_days'] > df['sla_days_limit']
df['day_of_week'] = df['created_at'].dt.day_name()
df['hour_of_day'] = df['created_at'].dt.hour

# Сохраняем расширенный датасет для Power BI
df.to_csv('advanced_appeals_data.csv', index=False)
print("\n3. Расширенный датасет 'advanced_appeals_data.csv' сохранен со 10 000 записей.")

# ==========================================
# ШАГ 4: Сложная визуализация (Неделя 6)
# ==========================================
print("4. Генерация аналитических графиков...")
sns.set_theme(style="darkgrid", context="talk")

# График 1: Тепловая карта загруженности (День недели vs Час дня)
plt.figure(figsize=(12, 6))
heatmap_data = df.groupby(['day_of_week', 'hour_of_day']).size().unstack(fill_value=0)
order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = heatmap_data.reindex(order)
sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=.5)
plt.title('Heatmap of Appeal Volumes (Day of Week vs Hour of Day)', pad=20)
plt.xlabel('Hour of Day')
plt.ylabel('Day of Week')
plt.tight_layout()
plt.savefig('heatmap_volume.png')

# График 2: Корреляция длины текста (сложности) и времени решения
plt.figure(figsize=(10, 6))
closed_df = df[df['status'] == 'Closed'].copy()
sns.scatterplot(data=closed_df, x='description_length', y='processing_time_days', 
                hue='priority', alpha=0.6, palette='deep')
# Добавим линию тренда
sns.regplot(data=closed_df, x='description_length', y='processing_time_days', 
            scatter=False, color='black', line_kws={"linestyle": "--"})
plt.title('Correlation: Problem Complexity vs Resolution Time')
plt.xlabel('Length of Appeal Description (characters)')
plt.ylabel('Resolution Time (Days)')
plt.tight_layout()
plt.savefig('complexity_correlation.png')

# График 3: Нарушения SLA (Service Level Agreement) по департаментам
plt.figure(figsize=(12, 6))
sla_data = df[df['status'] == 'Closed'].groupby('dept_name')['is_sla_breached'].mean() * 100
sla_data = sla_data.sort_values(ascending=False).reset_index()
sns.barplot(data=sla_data, x='is_sla_breached', y='dept_name', palette='Reds_r')
plt.title('SLA Violation Rate by Department (%)')
plt.xlabel('Percentage of Overdue Appeals (%)')
plt.ylabel('Department')
for i, v in enumerate(sla_data['is_sla_breached']):
    plt.text(v + 0.5, i, f"{v:.1f}%", color='black', va='center')
plt.tight_layout()
plt.savefig('sla_violations.png')

print("Анализ завершен успешно! База и графики сохранены.")
conn.close()
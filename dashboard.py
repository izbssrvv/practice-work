import streamlit as st
import pandas as pd
import plotly.express as px

# Настройка страницы
st.set_page_config(page_title="USC Executive Dashboard", layout="wide", page_icon="📊")

@st.cache_data
def load_data():
    df = pd.read_csv('advanced_appeals_data.csv')
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Файл 'advanced_appeals_data.csv' не найден. Сначала запустите advanced_analysis.py")
    st.stop()

# Заголовок
st.title("📊 Unified Situational Center - Monitor")
st.markdown("Интерактивный дашборд для мониторинга обращений граждан и контроля SLA.")

# --- БОКОВАЯ ПАНЕЛЬ (ФИЛЬТРЫ) ---
st.sidebar.header("Параметры фильтрации")
dept_filter = st.sidebar.multiselect(
    "Департамент:", 
    options=df['dept_name'].unique(), 
    default=df['dept_name'].unique()
)

priority_filter = st.sidebar.multiselect(
    "Приоритет:", 
    options=df['priority'].unique(), 
    default=df['priority'].unique()
)

# Применяем фильтры
filtered_df = df[(df['dept_name'].isin(dept_filter)) & (df['priority'].isin(priority_filter))]

st.sidebar.markdown("---")

# --- КАРТОЧКИ (KPIs) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего обращений", f"{len(filtered_df):,}")

if not filtered_df.empty:
    avg_days = filtered_df['processing_time_days'].dropna().mean()
    col2.metric("Среднее время решения", f"{avg_days:.1f} дней")
    
    sla_breaches = filtered_df['is_sla_breached'].sum()
    col3.metric("Нарушения сроков (SLA)", f"{int(sla_breaches):,}")
    
    sla_rate = (sla_breaches / len(filtered_df)) * 100
    col4.metric("Доля нарушений", f"{sla_rate:.1f}%")

st.markdown("---")

# --- ГРАФИКИ ---
c1, c2 = st.columns(2)

with c1:
    # Кольцевая диаграмма (Donut Chart) по категориям
    fig_pie = px.pie(
        filtered_df, 
        names='category', 
        title='Распределение обращений по категориям',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    # Столбчатая диаграмма нарушений SLA
    sla_dept = filtered_df[filtered_df['is_sla_breached'] == True].groupby('dept_name').size().reset_index(name='Breaches')
    fig_bar = px.bar(
        sla_dept, 
        x='dept_name', 
        y='Breaches', 
        title='Количество нарушений SLA по департаментам',
        color='dept_name',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_bar.update_layout(xaxis_title="Департамент", yaxis_title="Количество просрочек")
    st.plotly_chart(fig_bar, use_container_width=True)

# График временного ряда (Динамика)
st.subheader("Динамика поступления новых обращений")
daily_data = filtered_df.groupby(filtered_df['created_at'].dt.date).size().reset_index(name='Поступило жалоб')
fig_line = px.line(
        daily_data, 
        x='created_at', 
        y='Поступило жалоб',
        markers=True,
        line_shape='spline'
    )
fig_line.update_layout(xaxis_title="Дата", yaxis_title="Объем")
st.plotly_chart(fig_line, use_container_width=True)

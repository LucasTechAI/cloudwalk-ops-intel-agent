import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import json

# Adicionar o diretório raiz ao path
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

from src.utils.sqlite_manager import SqliteManager

# ========== CONFIGURAÇÕES GLOBAIS ==========
DB_START_DATE = '2025-01-01'
DB_END_DATE = '2025-03-31'

# Configuração da página
st.set_page_config(
    page_title="CloudWalk Operations Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS APRIMORADO ==========
st.markdown("""
    <style>
    /* Paleta de cores */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ecc71;
        --danger-color: #e74c3c;
        --warning-color: #f39c12;
        --bg-card: #ffffff;
        --bg-light: #f8f9fa;
        --text-primary: #2c3e50;
        --text-secondary: #7f8c8d;
    }
    
    /* Cards com efeitos */
    .stMetric {
        background: var(--bg-card);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .stMetric:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    
    /* Números grandes mais legíveis */
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    .stMetric [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    /* Tabs melhoradas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: var(--bg-light);
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(31, 119, 180, 0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    
    /* Botões */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 2rem;
        transition: all 0.2s ease;
        border: none;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Alertas */
    .alert-card {
        padding: 1.25rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        border-left: 5px solid;
        animation: slideIn 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .alert-critical {
        background: linear-gradient(135deg, #e74c3c15 0%, #e74c3c05 100%);
        border-left-color: #e74c3c;
    }
    
    .alert-high {
        background: linear-gradient(135deg, #f39c1215 0%, #f39c1205 100%);
        border-left-color: #f39c12;
    }
    
    .alert-medium {
        background: linear-gradient(135deg, #f1c40f15 0%, #f1c40f05 100%);
        border-left-color: #f1c40f;
    }
    
    /* Gráficos */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
    }
    
    h2 {
        font-size: 1.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid var(--primary-color);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        border-radius: 8px;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Data frames */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Tooltips */
    .tooltip-icon {
        cursor: help;
        color: var(--text-secondary);
        font-size: 0.875rem;
        margin-left: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# ========== FUNÇÕES AUXILIARES ==========

def apply_chart_theme(fig, title="", height=400):
    """Aplica tema consistente aos gráficos Plotly"""
    fig.update_layout(
        title={
            'text': title,
            'font': {'size': 18, 'color': '#2c3e50', 'family': 'Arial, sans-serif'},
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial, sans-serif", size=12, color='#2c3e50'),
        hovermode='closest',
        margin=dict(l=60, r=60, t=80, b=60),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        height=height
    )
    
    # Grade sutil
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(0,0,0,0.08)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.2)'
    )
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(0,0,0,0.08)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.2)'
    )
    
    return fig

def metric_with_sparkline(label, value, trend_data=None, delta=None, help_text=None):
    """Cria métrica com mini gráfico de tendência"""
    cols = st.columns([3, 1]) if trend_data is not None else [st.container()]
    
    with cols[0]:
        st.metric(label=label, value=value, delta=delta, help=help_text)
    
    if trend_data is not None and len(trend_data) > 0:
        with cols[1]:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=trend_data,
                mode='lines',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            ))
            fig.update_layout(
                height=60,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def alert_card(level, title, message, metric_value=None):
    """Cria card de alerta estilizado"""
    icons = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢'
    }
    
    classes = {
        'CRITICAL': 'alert-critical',
        'HIGH': 'alert-high',
        'MEDIUM': 'alert-medium',
        'LOW': 'alert-low'
    }
    
    metric_html = f'<div style="margin-top: 8px; font-size: 1.2rem; font-weight: 700; color: #2c3e50;">R$ {metric_value:,.2f}</div>' if metric_value else ''
    
    st.markdown(f"""
        <div class="alert-card {classes.get(level, 'alert-medium')}">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 1.5rem;">{icons.get(level, '⚪')}</span>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 1rem; margin-bottom: 4px; color: #2c3e50;">
                        {level}: {title}
                    </div>
                    <div style="color: #7f8c8d; font-size: 0.875rem;">
                        {message}
                    </div>
                    {metric_html}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ========== INICIALIZAÇÃO ==========

@st.cache_resource
def init_db():
    """Inicializa e retorna o gerenciador de banco de dados thread-safe"""
    db_manager = SqliteManager()
    return db_manager

# ========== FUNÇÕES DE CARREGAMENTO DE DADOS ==========

@st.cache_data(ttl=300)
def load_overall_kpis(_db_manager):
    """Carrega KPIs gerais usando a view v_kpi"""
    query = """
    SELECT 
        SUM(tpv) as total_tpv,
        SUM(total_transactions) as total_transactions,
        SUM(total_merchants) as total_merchants,
        AVG(average_ticket) as avg_ticket,
        MAX(day) as last_update
    FROM v_kpi
    """
    return _db_manager.select_query(query)

@st.cache_data(ttl=300)
def load_daily_trends(_db_manager, days=90):
    """Carrega tendências diárias com variações"""
    query = f"""
    SELECT 
        day,
        SUM(tpv) as tpv,
        SUM(total_transactions) as transactions,
        AVG(avg_ticket) as avg_ticket,
        AVG(var_d7_pct) as var_d7_pct,
        AVG(avg_7d) as moving_avg_7d
    FROM v_daily_kpis
    WHERE day >= date('{DB_END_DATE}', '-{days} days')
      AND day <= '{DB_END_DATE}'
    GROUP BY day
    ORDER BY day
    """
    return _db_manager.select_query(query)

@st.cache_data(ttl=300)
def load_product_comparison(_db_manager):
    """Carrega comparação entre produtos"""
    query = """
    SELECT 
        product,
        entity,
        tpv,
        total_transactions,
        avg_ticket,
        tpv_pct_of_total,
        days_active
    FROM v_product_comparison
    ORDER BY tpv DESC
    """
    return _db_manager.select_query(query)

@st.cache_data(ttl=300)
def load_weekday_analysis(_db_manager):
    """Carrega análise por dia da semana"""
    query = """
    SELECT 
        weekday,
        weekday_num,
        SUM(tpv) as tpv,
        SUM(total_transactions) as transactions,
        AVG(avg_ticket) as avg_ticket,
        AVG(avg_daily_tpv) as avg_daily_tpv
    FROM v_weekday_analysis
    GROUP BY weekday, weekday_num
    ORDER BY weekday_num
    """
    return _db_manager.select_query(query)

@st.cache_data(ttl=300)
def load_alerts(_db_manager, days=90):
    """Carrega alertas críticos e importantes"""
    query = f"""
    SELECT 
        day,
        entity,
        product,
        payment_method,
        tpv,
        alert_level,
        alert_message,
        severity_score,
        var_d7_pct,
        var_vs_14d_pct
    FROM v_alerts
    WHERE day >= date('{DB_END_DATE}', '-{days} days')
      AND day <= '{DB_END_DATE}'
    ORDER BY severity_score DESC, day DESC
    LIMIT 20
    """
    return _db_manager.select_query(query)

@st.cache_data(ttl=300)
def load_segmentation(_db_manager):
    """Carrega análise de segmentação"""
    query = """
    SELECT 
        entity,
        product,
        payment_method,
        tpv,
        total_transactions,
        avg_ticket,
        tpv_pct_of_total
    FROM v_segmentation
    ORDER BY tpv DESC
    LIMIT 15
    """
    return _db_manager.select_query(query)

@st.cache_data(ttl=300)
def load_anticipation_analysis(_db_manager):
    """Carrega análise de métodos de antecipação"""
    query = """
    SELECT 
        entity,
        anticipation_method,
        tpv,
        total_transactions,
        tpv_pct_by_entity,
        transactions_pct_by_entity
    FROM v_anticipation_analysis
    ORDER BY entity, tpv DESC
    """
    return _db_manager.select_query(query)

@st.cache_data(ttl=300)
def load_installments_analysis(_db_manager):
    """Carrega análise de parcelamento"""
    query = """
    SELECT 
        installments,
        SUM(tpv) as tpv,
        SUM(total_transactions) as transactions,
        AVG(avg_ticket) as avg_ticket,
        AVG(tpv_pct) as tpv_pct
    FROM v_installments_analysis
    GROUP BY installments
    ORDER BY installments
    """
    return _db_manager.select_query(query)

# ========== FUNÇÕES DE IA ==========

def generate_sql_with_ai(user_question, db_manager):
    """Gera uma query SQL usando IA com base na pergunta do usuário"""
    try:
        from src.agents.agent_invoker import AgentInvoker
        from src.agents.utils.prompt_tool_loader import AgentResourceLoader

        loader = AgentResourceLoader(prompts_dir="agents/prompts", tools_dir="agents/tools")
        agent = AgentInvoker(model_name="llama3.1", temperature=0, max_retries=3)

        system_prompt = loader.load_prompt("answers_questions.txt")
        tool_definition = loader.load_tools("answers_questions.json")

        user_question = (
            "You MUST call the generate_sql_and_visualization tool to answer.\n\n"
            f"Question: {user_question}\n\n"
            "IMPORTANT: Call the tool with all required parameters only. "
            "You MUST provide ALL required fields with meaningful content: "
            "querySQL, plotSuggestion, explanation, title, x-axis, y-axis"
        )

        response = agent.invoke_with_tools(
            system_prompt=system_prompt,
            user_message=user_question,
            tools=tool_definition,
            tool_choice="required"
        )

        return response

    except Exception as e:
        return f"Erro ao gerar SQL: {str(e)}"

def generate_insights_with_ai(user_question, data_df, response):
    """Gera insights usando IA a partir dos dados"""
    try:
        from src.agents.agent_invoker import AgentInvoker
        from src.agents.utils.prompt_tool_loader import AgentResourceLoader

        loader = AgentResourceLoader(prompts_dir="agents/prompts", tools_dir="agents/tools")
        agent = AgentInvoker(model_name="llama3.1", temperature=0.7, max_retries=3)

        system_prompt = loader.load_prompt("generate_insights.txt")
        tool_definition = loader.load_tools("generate_insights.json")

        user_message = (
            "Based on the data returned from the SQL query and the user's original question, "
            "generate detailed insights and analysis.\n\n"
            f"User Question: {user_question}\n\n"
            f"SQL Query: {response.get('querySQL', '')}\n\n"
            f"Data:\n{data_df.to_json(orient='records')}\n\n"
            "Provide insights in a clear and structured manner."
        )

        insights_response = agent.invoke_with_tools(
            system_prompt=system_prompt,
            user_message=user_message,
            tools=tool_definition,
            tool_choice="required"
        )

        return insights_response
    
    except Exception as e:
        return f"Erro ao gerar insights: {str(e)}"

def auto_visualize(df, suggestion):
    """Gera visualização automática baseada na sugestão da IA"""
    plot_type = suggestion.get("plotSuggestion", None)
    title = suggestion.get("title", "Auto-generated Visualization")
    x_axis = suggestion.get("x-axis", None)
    y_axis = suggestion.get("y-axis", None)

    # Identificar colunas
    numeric_cols = df.select_dtypes(include=["float", "int"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    # Fallback automático
    if not x_axis:
        if date_cols:
            x_axis = date_cols[0]
        elif categorical_cols:
            x_axis = categorical_cols[0]
        elif numeric_cols:
            x_axis = numeric_cols[0]

    if not y_axis:
        if numeric_cols and x_axis not in numeric_cols:
            y_axis = numeric_cols[0]
        elif len(numeric_cols) > 1:
            y_axis = numeric_cols[1]

    # Criar gráfico baseado no tipo
    if plot_type == "bar":
        fig = px.bar(df, x=x_axis, y=y_axis, title=title)
    elif plot_type == "barh":
        fig = px.bar(df, x=y_axis, y=x_axis, orientation="h", title=title)
    elif plot_type == "line":
        fig = px.line(df, x=x_axis, y=y_axis, markers=True, title=title)
    elif plot_type == "boxplot":
        fig = px.box(df, x=x_axis, y=y_axis, title=title)
    elif plot_type == "hist":
        fig = px.histogram(df, x=x_axis, title=title)
    elif plot_type == "scatter":
        size_col = numeric_cols[2] if len(numeric_cols) > 2 else None
        fig = px.scatter(df, x=x_axis, y=y_axis, size=size_col, title=title)
    elif plot_type == "table":
        st.dataframe(df, use_container_width=True)
        return
    elif plot_type == "number":
        if numeric_cols:
            metric = df[numeric_cols[0]].sum()
            st.metric(label=title, value=f"{metric:,.2f}")
            return
        else:
            st.warning("Nenhuma coluna numérica disponível.")
            return
    else:
        # Fallback automático
        if numeric_cols and categorical_cols:
            fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0], title="Auto Bar Chart")
        elif len(numeric_cols) >= 2:
            fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title="Auto Scatter")
        else:
            st.dataframe(df, use_container_width=True)
            return

    # Aplicar tema
    fig = apply_chart_theme(fig, title)
    st.plotly_chart(fig, use_container_width=True)

# ========== APLICAÇÃO PRINCIPAL ==========

def main():
    # Inicializar recursos
    db_manager = init_db()
    
    # Verificar primeira visita
    if 'first_visit' not in st.session_state:
        st.session_state.first_visit = True
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Onboarding
        if st.session_state.first_visit:
            st.info("""
            👋 **Welcome!**
            
            This dashboard provides comprehensive analytics for CloudWalk operations.
            
            Use the filters below to customize your analysis.
            """)
            
            if st.button("✓ Got it!", type="primary"):
                st.session_state.first_visit = False
                st.rerun()
        
        st.markdown("---")
        
        # Filtros em expander
        with st.expander("🔍 **Filters**", expanded=True):
            st.markdown("##### 📅 Time Period")
            
            # Info do período de dados
            st.caption(f"📊 Available: {DB_START_DATE} to {DB_END_DATE}")
            
            days_filter = st.select_slider(
                "Days to analyze (from Mar 31):",
                options=[7, 15, 30, 60, 90],
                value=90,
                help="Retroactive analysis from March 31, 2025"
            )
            
        
        st.markdown("---")
        
        # Informações do sistema
        with st.expander("ℹ️ **About**"):
            st.markdown("""
            **CloudWalk Operations Intelligence**
            
            📊 Real-time analytics platform for transaction monitoring and business intelligence.
            
            **Features:**
            - Live KPI tracking
            - Trend analysis
            - AI-powered insights
            - Custom queries
            
            **Tech Stack:**  
            🎨 Streamlit • 📈 Plotly  
            🐼 Pandas • 🗄️ SQLite
            
            ---
            
            **Data Period:** Q1 2025  
            **Version:** 2.0.0  
            **Created by:** Lucas Mendes Barbosa
            """)
        
        # Refresh button
        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # ========== CABEÇALHO ==========
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        st.title("📊 CloudWalk Operations Intelligence")
        st.markdown("*Real-time Analytics Dashboard • Q1 2025*")
    
    with col_header2:
        st.markdown("###  ")
        st.info(f"**Analysis Period**  \n📅 Last {days_filter} days")
    
    st.markdown("---")
    
    # ========== TABS PRINCIPAIS ==========
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", 
        "📈 Trends & Analysis", 
        "🔍 Deep Dive", 
        "💬 AI Assistant"
    ])
    
    # ==================== TAB 1: OVERVIEW ====================
    with tab1:
        st.header("Key Performance Indicators")
        
        try:
            kpis = load_overall_kpis(db_manager)
            daily_trends = load_daily_trends(db_manager, days=days_filter)
            
            if not kpis.empty:
                # KPIs principais com sparklines
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    trend_data = daily_trends['tpv'].tail(30).tolist() if not daily_trends.empty else None
                    metric_with_sparkline(
                        label="💰 Total TPV",
                        value=f"R$ {kpis['total_tpv'].iloc[0]:,.0f}",
                        trend_data=trend_data,
                        help_text="Total Payment Volume - Sum of all transactions"
                    )
                
                with col2:
                    trend_data = daily_trends['transactions'].tail(30).tolist() if not daily_trends.empty else None
                    metric_with_sparkline(
                        label="🔄 Transactions",
                        value=f"{kpis['total_transactions'].iloc[0]:,.0f}",
                        trend_data=trend_data,
                        help_text="Total number of processed transactions"
                    )
                
                with col3:
                    metric_with_sparkline(
                        label="🏪 Active Merchants",
                        value=f"{kpis['total_merchants'].iloc[0]:,.0f}",
                        help_text="Number of unique active merchants"
                    )
                
                with col4:
                    trend_data = daily_trends['avg_ticket'].tail(30).tolist() if not daily_trends.empty else None
                    metric_with_sparkline(
                        label="🎫 Avg Ticket",
                        value=f"R$ {kpis['avg_ticket'].iloc[0]:,.2f}",
                        trend_data=trend_data,
                        help_text="Average transaction value"
                    )
                
                st.markdown("---")
                
                # Alertas críticos
                st.subheader(f"🚨 Critical Alerts - Last {days_filter} Days")
                
                alerts = load_alerts(db_manager, days=days_filter)
                critical_alerts = alerts[alerts['severity_score'] >= 4] if not alerts.empty else pd.DataFrame()
                
                if not critical_alerts.empty:
                    for _, alert in critical_alerts.head(5).iterrows():
                        alert_card(
                            level=alert['alert_level'],
                            title=f"{alert['product']} • {alert['entity']}",
                            message=alert['alert_message'],
                            metric_value=alert['tpv']
                        )
                else:
                    st.success("✅ No critical alerts in this period!")
                
                st.markdown("---")
                
                # Quick stats do período
                st.subheader(f"📊 Period Summary - Last {days_filter} Days")
                
                if not daily_trends.empty:
                    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                    
                    total_tpv = daily_trends['tpv'].sum()
                    total_trans = daily_trends['transactions'].sum()
                    avg_ticket_period = total_tpv / total_trans if total_trans > 0 else 0
                    last_var = daily_trends['var_d7_pct'].iloc[-1]
                    
                    with col_stats1:
                        st.metric(
                            "Period TPV",
                            f"R$ {total_tpv:,.0f}",
                            help=f"Total TPV in last {days_filter} days"
                        )
                    
                    with col_stats2:
                        st.metric(
                            "Period Transactions",
                            f"{total_trans:,.0f}",
                            help=f"Transactions in last {days_filter} days"
                        )
                    
                    with col_stats3:
                        st.metric(
                            "Period Avg Ticket",
                            f"R$ {avg_ticket_period:,.2f}",
                            help=f"Average ticket in last {days_filter} days"
                        )
                    
                    with col_stats4:
                        delta_color = "normal" if last_var >= 0 else "inverse"
                        st.metric(
                            "Last D-7 Var",
                            f"{last_var:+.2f}%",
                            delta=f"{last_var:.2f}%",
                            help="Latest 7-day variation"
                        )
        
        except Exception as e:
            st.error(f"❌ Error loading overview data: {str(e)}")
    
    # ==================== TAB 2: TRENDS & ANALYSIS ====================
    with tab2:
        st.header("📈 Trends & Performance Analysis")
        
        try:
            daily_trends = load_daily_trends(db_manager, days=days_filter)
            
            if not daily_trends.empty:
                # Row 1: TPV e Variação
                col_t1, col_t2 = st.columns(2)
                
                with col_t1:
                    st.subheader("💰 TPV Evolution")
                    
                    fig_tpv = go.Figure()
                    fig_tpv.add_trace(go.Scatter(
                        x=daily_trends['day'],
                        y=daily_trends['tpv'],
                        mode='lines+markers',
                        name='Daily TPV',
                        line=dict(color='#1f77b4', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(31, 119, 180, 0.2)',
                        marker=dict(size=6)
                    ))
                    fig_tpv.add_trace(go.Scatter(
                        x=daily_trends['day'],
                        y=daily_trends['moving_avg_7d'],
                        mode='lines',
                        name='7-day Moving Avg',
                        line=dict(color='#ff7f0e', width=2, dash='dash')
                    ))
                    
                    fig_tpv = apply_chart_theme(fig_tpv, "")
                    fig_tpv.update_xaxes(title="Date")
                    fig_tpv.update_yaxes(title="TPV (R$)")
                    
                    st.plotly_chart(fig_tpv, use_container_width=True)
                
                with col_t2:
                    st.subheader("📊 D-7 Variation (%)")
                    
                    colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in daily_trends['var_d7_pct']]
                    
                    fig_var = go.Figure()
                    fig_var.add_trace(go.Bar(
                        x=daily_trends['day'],
                        y=daily_trends['var_d7_pct'],
                        marker_color=colors,
                        name='D-7 Variation',
                        hovertemplate='<b>%{x}</b><br>Variation: %{y:.2f}%<extra></extra>'
                    ))
                    fig_var.add_hline(y=0, line_dash="dash", line_color="gray", line_width=2)
                    
                    fig_var = apply_chart_theme(fig_var, "")
                    fig_var.update_xaxes(title="Date")
                    fig_var.update_yaxes(title="Variation (%)")
                    
                    st.plotly_chart(fig_var, use_container_width=True)
                
                st.markdown("---")
                
                # Row 2: Análises comparativas
                col_t3, col_t4 = st.columns(2)
                
                with col_t3:
                    st.subheader("📦 Product Performance")
                    
                    product_comp = load_product_comparison(db_manager)
                    
                    if not product_comp.empty:
                        fig_prod = px.bar(
                            product_comp.head(10),
                            x='product',
                            y='tpv',
                            color='entity',
                            title='',
                            labels={'tpv': 'TPV (R$)', 'product': 'Product', 'entity': 'Entity'},
                            color_discrete_map={'individual': '#3498db', 'business': '#e74c3c'}
                        )
                        fig_prod = apply_chart_theme(fig_prod, "")
                        st.plotly_chart(fig_prod, use_container_width=True)
                
                with col_t4:
                    st.subheader("📅 Weekday Performance")
                    
                    weekday_analysis = load_weekday_analysis(db_manager)
                    
                    if not weekday_analysis.empty:
                        fig_week = px.line(
                            weekday_analysis,
                            x='weekday',
                            y='avg_daily_tpv',
                            markers=True,
                            title='',
                            labels={'avg_daily_tpv': 'Daily Avg TPV (R$)', 'weekday': 'Weekday'}
                        )
                        fig_week.update_traces(
                            line=dict(width=3, color='#9b59b6'),
                            marker=dict(size=10)
                        )
                        fig_week = apply_chart_theme(fig_week, "")
                        st.plotly_chart(fig_week, use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Error loading trends: {str(e)}")
    
    # ==================== TAB 3: DEEP DIVE ====================
    with tab3:
        st.header("🔍 Deep Dive Analysis")
        
        # Subtabs para organizar
        subtab1, subtab2, subtab3 = st.tabs(["💳 Payment Methods", "📊 Segmentation", "📈 Installments"])
        
        with subtab1:
            st.subheader("Anticipation Methods Distribution")
            
            try:
                anticipation = load_anticipation_analysis(db_manager)
                
                if not anticipation.empty:
                    col_ant1, col_ant2 = st.columns([2, 1])
                    
                    with col_ant1:
                        fig_sun = px.sunburst(
                            anticipation,
                            path=['entity', 'anticipation_method'],
                            values='tpv',
                            title='',
                            color='tpv',
                            color_continuous_scale='Blues'
                        )
                        fig_sun.update_traces(
                            hovertemplate='<b>%{label}</b><br>' +
                                        'TPV: R$ %{value:,.2f}<br>' +
                                        'Share: %{percentParent:.2%}<br>' +
                                        '<extra></extra>'
                        )
                        fig_sun = apply_chart_theme(fig_sun, "", height=500)
                        st.plotly_chart(fig_sun, use_container_width=True)
                    
                    with col_ant2:
                        st.markdown("##### 📊 Summary by Entity")
                        
                        summary = anticipation.groupby('entity').agg({
                            'tpv': 'sum',
                            'total_transactions': 'sum'
                        }).reset_index()
                        
                        for _, row in summary.iterrows():
                            st.metric(
                                label=f"{row['entity'].title()}",
                                value=f"R$ {row['tpv']:,.0f}",
                                delta=f"{row['total_transactions']:,.0f} trans"
                            )
            
            except Exception as e:
                st.error(f"❌ Error loading anticipation data: {str(e)}")
        
        with subtab2:
            st.subheader("Transaction Segmentation")
            
            try:
                segmentation = load_segmentation(db_manager)
                
                if not segmentation.empty:
                    # Treemap
                    fig_tree = px.treemap(
                        segmentation,
                        path=['entity', 'product', 'payment_method'],
                        values='tpv',
                        title='',
                        color='tpv_pct_of_total',
                        color_continuous_scale='Viridis'
                    )
                    fig_tree = apply_chart_theme(fig_tree, "", height=600)
                    st.plotly_chart(fig_tree, use_container_width=True)
                    
                    # Tabela detalhada
                    st.markdown("##### 📋 Detailed Breakdown")
                    st.dataframe(
                        segmentation.style.format({
                            'tpv': 'R$ {:,.2f}',
                            'total_transactions': '{:,.0f}',
                            'avg_ticket': 'R$ {:,.2f}',
                            'tpv_pct_of_total': '{:.2f}%'
                        }),
                        use_container_width=True,
                        height=400
                    )
            
            except Exception as e:
                st.error(f"❌ Error loading segmentation: {str(e)}")
        
        with subtab3:
            st.subheader("Installments Analysis")
            
            try:
                installments = load_installments_analysis(db_manager)
                
                if not installments.empty:
                    # Gráfico combinado
                    fig_inst = go.Figure()
                    
                    fig_inst.add_trace(go.Bar(
                        x=installments['installments'],
                        y=installments['tpv'],
                        name='TPV',
                        yaxis='y',
                        marker_color='#3498db',
                        hovertemplate='<b>%{x}x</b><br>TPV: R$ %{y:,.2f}<extra></extra>'
                    ))
                    
                    fig_inst.add_trace(go.Scatter(
                        x=installments['installments'],
                        y=installments['avg_ticket'],
                        name='Avg Ticket',
                        yaxis='y2',
                        mode='lines+markers',
                        line=dict(color='#e74c3c', width=3),
                        marker=dict(size=10),
                        hovertemplate='<b>%{x}x</b><br>Avg: R$ %{y:,.2f}<extra></extra>'
                    ))
                    
                    fig_inst = apply_chart_theme(fig_inst, "", height=500)
                    fig_inst.update_layout(
                        xaxis=dict(title="Number of Installments"),
                        yaxis=dict(title="TPV (R$)", side='left'),
                        yaxis2=dict(
                            title="Avg Ticket (R$)",
                            overlaying='y',
                            side='right'
                        )
                    )
                    
                    st.plotly_chart(fig_inst, use_container_width=True)
                    
                    # Stats rápidos
                    col_inst1, col_inst2, col_inst3 = st.columns(3)
                    
                    with col_inst1:
                        most_used = installments.loc[installments['transactions'].idxmax()]
                        st.metric(
                            "Most Used",
                            f"{int(most_used['installments'])}x",
                            f"{most_used['transactions']:,.0f} trans"
                        )
                    
                    with col_inst2:
                        highest_tpv = installments.loc[installments['tpv'].idxmax()]
                        st.metric(
                            "Highest TPV",
                            f"{int(highest_tpv['installments'])}x",
                            f"R$ {highest_tpv['tpv']:,.0f}"
                        )
                    
                    with col_inst3:
                        highest_ticket = installments.loc[installments['avg_ticket'].idxmax()]
                        st.metric(
                            "Highest Avg Ticket",
                            f"{int(highest_ticket['installments'])}x",
                            f"R$ {highest_ticket['avg_ticket']:,.2f}"
                        )
            
            except Exception as e:
                st.error(f"❌ Error loading installments: {str(e)}")
    
    # ==================== TAB 4: AI ASSISTANT ====================
    with tab4:
        st.header("💬 AI-Powered Custom Analysis")
        
        st.markdown("""
        Ask questions about your data and the AI will automatically:
        - 🔍 Generate optimized SQL queries
        - 📊 Create appropriate visualizations
        - 💡 Provide actionable insights
        """)
        
        # Estado da sessão
        if 'query_result' not in st.session_state:
            st.session_state.query_result = None
        if 'generated_sql' not in st.session_state:
            st.session_state.generated_sql = None
        if 'insights' not in st.session_state:
            st.session_state.insights = None
        if 'user_question' not in st.session_state:
            st.session_state.user_question = ""
        if 'response' not in st.session_state:
            st.session_state.response = None
        
        # Exemplos de perguntas
        with st.expander("💡 **Example Questions**", expanded=False):
            st.markdown("""
            **Performance Analysis:**
            - Which product has the highest TPV?
            - What's the trend of transactions over the last 30 days?
            
            **Comparative Analysis:**
            - How do weekdays compare in terms of TPV?
            - Which segment has the highest average ticket?
            
            **Behavioral Insights:**
            - Which anticipation method is most used by individuals vs businesses?
            - What's the distribution of installment preferences?
            
            **Anomaly Detection:**
            - Are there any unusual patterns in the last week?
            - Which products show the highest variation?
            """)
        
        st.markdown("---")
        
        # Input de pergunta
        user_question = st.text_area(
            "**Your Question:**",
            placeholder="Example: Which products have the highest TPV in March 2025?",
            height=100,
            value=st.session_state.user_question,
            help="Ask any question about the data and AI will analyze it for you"
        )
        
        # Botões de ação
        col_ai1, col_ai2, col_ai3, col_ai4 = st.columns([3, 2, 2, 1])
        
        with col_ai1:
            submit_button = st.button(
                "🔍 Analyze Question", 
                type="primary", 
                use_container_width=True,
                disabled=not user_question.strip()
            )
        
        with col_ai2:
            insights_button = st.button(
                "✨ Generate Insights", 
                use_container_width=True,
                disabled=(st.session_state.query_result is None)
            )
        
        with col_ai3:
            export_button = st.button(
                "📥 Export Results",
                use_container_width=True,
                disabled=(st.session_state.query_result is None)
            )
        
        with col_ai4:
            clear_button = st.button(
                "🗑️",
                use_container_width=True,
                help="Clear all results"
            )
        
        # Processar pergunta
        if submit_button and user_question:
            st.session_state.user_question = user_question
            
            with st.spinner("🤖 AI is analyzing your question..."):
                try:
                    progress_bar = st.progress(0)
                    status = st.empty()
                    
                    status.text("🔍 Generating SQL query...")
                    progress_bar.progress(33)
                    
                    results = generate_sql_with_ai(user_question, db_manager)
                    sql_query = results.get("querySQL", "")
                    explanation = results.get("explanation", "")
                    
                    if sql_query:
                        status.text("⚡ Executing query...")
                        progress_bar.progress(66)
                        
                        result_df = db_manager.select_query(sql_query)
                        
                        if not result_df.empty:
                            status.text("✅ Query completed!")
                            progress_bar.progress(100)
                            
                            st.session_state.query_result = result_df
                            st.session_state.generated_sql = sql_query
                            st.session_state.response = results
                            st.session_state.insights = None
                            
                            # Limpar progress
                            progress_bar.empty()
                            status.empty()
                            
                            st.success(f"✅ Analysis complete! Found {len(result_df)} records.")
                            
                            if explanation:
                                st.info(f"**AI Explanation:** {explanation}")
                            
                            st.rerun()
                        else:
                            progress_bar.empty()
                            status.empty()
                            st.warning("⚠️ Query returned no results. Try rephrasing your question.")
                    else:
                        progress_bar.empty()
                        status.empty()
                        st.error("❌ Could not generate SQL for your question. Please try rephrasing.")
                
                except Exception as e:
                    st.error(f"❌ Error processing question: {str(e)}")
        
        # Gerar insights
        if insights_button and st.session_state.query_result is not None:
            with st.spinner("🤖 Generating insights from data..."):
                try:
                    insights = generate_insights_with_ai(
                        st.session_state.user_question,
                        st.session_state.query_result,
                        st.session_state.response
                    )
                    
                    st.session_state.insights = insights
                    st.success("✅ Insights generated successfully!")
                    
                    conclusion = insights.get("conclusion", "")
                    if conclusion:
                        st.info(f"**Key Insight:** {conclusion}")
                
                except Exception as e:
                    st.error(f"❌ Error generating insights: {str(e)}")
        
        # Exportar resultados
        if export_button and st.session_state.query_result is not None:
            csv_data = st.session_state.query_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=f'analysis_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
                use_container_width=True
            )
        
        # Limpar
        if clear_button:
            st.session_state.query_result = None
            st.session_state.generated_sql = None
            st.session_state.insights = None
            st.session_state.response = None
            st.session_state.user_question = ""
            st.rerun()
        
        # Exibir resultados
        if st.session_state.query_result is not None:
            st.markdown("---")
            
            # Insights
            if st.session_state.insights:
                st.markdown("### 💡 AI-Generated Insights")
                
                with st.container():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 2rem; border-radius: 12px; color: white; 
                                box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                        {st.session_state.insights.get('conclusion', '')}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
            
            # Visualização
            st.markdown("### 📊 Visualization")
            
            if st.session_state.response:
                auto_visualize(st.session_state.query_result, st.session_state.response)
            
            st.markdown("---")
            
            # Dados brutos em tabs
            result_tab1, result_tab2 = st.tabs(["📋 Data Table", "💻 SQL Query"])
            
            with result_tab1:
                st.dataframe(
                    st.session_state.query_result,
                    use_container_width=True,
                    height=400
                )
                
                # Estatísticas rápidas
                st.markdown("##### Quick Stats")
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("Rows", f"{len(st.session_state.query_result):,}")
                
                with col_stat2:
                    st.metric("Columns", f"{len(st.session_state.query_result.columns):,}")
                
                with col_stat3:
                    memory = st.session_state.query_result.memory_usage(deep=True).sum() / 1024
                    st.metric("Memory", f"{memory:.2f} KB")
            
            with result_tab2:
                if st.session_state.generated_sql:
                    st.code(st.session_state.generated_sql, language='sql')
                    
                    if st.button("📋 Copy SQL", use_container_width=True):
                        st.toast("✅ SQL copied to clipboard!")

if __name__ == "__main__":
    main()
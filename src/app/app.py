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
print(root_path)
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

# CSS customizado
st.markdown("""
    <style>
    .big-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 1rem;
        color: #666;
    }
    .stButton>button {
        width: 100%;
    }
    .alert-critical {
        background-color: #ffebee;
        padding: 10px;
        border-left: 4px solid #f44336;
        margin: 5px 0;
    }
    .alert-high {
        background-color: #fff3e0;
        padding: 10px;
        border-left: 4px solid #ff9800;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar conexão com banco de dados - THREAD-SAFE
@st.cache_resource
def init_db():
    """
    Inicializa e retorna o gerenciador de banco de dados thread-safe.
    O SqliteManager agora cria conexões específicas por thread automaticamente.
    """
    db_manager = SqliteManager()
    return db_manager

# ========== FUNÇÕES DE CARREGAMENTO DE DADOS ==========

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

# ========== FUNÇÃO PARA GERAR SQL COM IA ==========
def generate_sql_with_ai(user_question, db_manager):
    """Gera uma query SQL usando IA com base na pergunta do usuário."""
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
            "You MUST provide ALL required fields with meaningful content: ",
            "- querySQL",
            "- plotSuggestion",
            "- explanation",
            "- title",
            "- x-axis",
            "- y-axis",
        )

        response = agent.invoke_with_tools(
            system_prompt=system_prompt,
            user_message=user_question,
            tools=tool_definition,
            tool_choice="required"
        )

        print("Generated SQL Response:", response)
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
            f"Data :\n{data_df.to_json(orient='records')}\n\n"
            "Provide insights in a clear and structured manner."
        )

        insights_response = agent.invoke_with_tools(
            system_prompt=system_prompt,
            user_message=user_message,
            tools=tool_definition,
            tool_choice="required"
        )

        print("Generated Insights Response:", insights_response)
        return insights_response
    
    except Exception as e:
        return f"Erro ao gerar insights: {str(e)}"

# ========== APLICAÇÃO PRINCIPAL ==========

def auto_visualize(df, suggestion):
    print("Visualization Suggestion:", suggestion)
    plot_type = suggestion.get("plotSuggestion", None)
    title = suggestion.get("title", "Auto-generated Visualization")
    x_axis = suggestion.get("x-axis", None)
    y_axis = suggestion.get("y-axis", None)

    # Identificar colunas
    numeric_cols = df.select_dtypes(include=["float", "int"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    # Fallback automático se o modelo não enviou eixos
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

    # ----------------------------
    #     TIPOS DE GRÁFICO
    # ----------------------------

    # BAR -----------------------------------------------------
    if plot_type == "bar":
        fig = px.bar(df, x=x_axis, y=y_axis, title=title)

    # BARH (bar orientation horizontal)
    elif plot_type == "barh":
        fig = px.bar(df, x=y_axis, y=x_axis, orientation="h", title=title)

    # LINE ----------------------------------------------------
    elif plot_type == "line":
        fig = px.line(df, x=x_axis, y=y_axis, markers=True, title=title)

    # BOXPLOT -------------------------------------------------
    elif plot_type == "boxplot":
        fig = px.box(df, x=x_axis, y=y_axis, title=title)

    # HIST ----------------------------------------------------
    elif plot_type == "hist":
        fig = px.histogram(df, x=x_axis, title=title)

    # SCATTER -------------------------------------------------
    elif plot_type == "scatter":
        size_col = numeric_cols[2] if len(numeric_cols) > 2 else None
        fig = px.scatter(df, x=x_axis, y=y_axis, size=size_col, title=title)

    # TABLE ---------------------------------------------------
    elif plot_type == "table":
        st.dataframe(df)
        return  # sem gráfico

    # NUMBER (métrica única) ---------------------------------
    elif plot_type == "number":
        if numeric_cols:
            metric = df[numeric_cols[0]].sum()
            st.metric(label=title, value=f"{metric:,.2f}")
            return
        else:
            st.warning("Nenhuma coluna numérica disponível para exibir número.")
            return

    # FALLBACK AUTOMÁTICO ------------------------------------
    else:
        if numeric_cols and categorical_cols:
            fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0], title="Auto Bar Chart")
        elif len(numeric_cols) >= 2:
            fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title="Auto Scatter")
        else:
            st.dataframe(df)
            return

    st.plotly_chart(fig, width='content')


def main():
    # Inicializar recursos com thread-safety
    db_manager = init_db()
    
    # Sidebar com filtros
    with st.sidebar:
        st.title("⚙️ Settings")
        
        st.markdown("---")
        st.markdown("### 📅 Database Period")
        
        st.info(f"""
        **Available Data:**
        - 📅 Start: 01/01/2025
        - 📅 End: 31/03/2025
        - 📊 Total: 90 days (Q1 2025)
        """)
        
        st.markdown("### 🔍 Analysis Filter")
        days_filter = st.selectbox(
            "Last N days (from 03/31):",
            options=[7, 15, 30, 60, 90],
            index=4,
            help="Retroactive analysis from March 31, 2025"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("""
        **CloudWalk Operations Intelligence**

        📊 Real-time analytics dashboard for transaction monitoring, KPIs tracking, and operational alerts.

        **Tech Stack:**  
        - 🎨 Streamlit • 📈 Plotly • 🐼 Pandas • 🗄️ SQLite

        **Data Period:**  
        Q1 2025 (Jan-Mar)

        **Created by:** Lucas Mendes Barbosa  
        **Version:** 1.1.0 (Thread-Safe)
        """)
    
    # Título principal
    st.title("CloudWalk - Operations Intelligence")
    st.markdown("*Operations Analytics Dashboard - Q1 2025*")
    st.markdown(f"**Data Period:** Jan 01, 2025 to Mar 31, 2025 | **Analysis Filter:** Last {days_filter} days")
    st.markdown("---")
    
    # ========== SEÇÃO 1: BIG NUMBERS / KPIs ==========
    st.header("Key Performance Indicators")
    
    try:
        kpis = load_overall_kpis(db_manager)
        
        if not kpis.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total TPV",
                    value=f"R$ {kpis['total_tpv'].iloc[0]:,.2f}",
                    help="Total Payment Volume - Total processed volume (Q1 2025)"
                )
            
            with col2:
                st.metric(
                    label="Transactions",
                    value=f"{kpis['total_transactions'].iloc[0]:,.0f}",
                    help="Total number of processed transactions"
                )
            
            with col3:
                st.metric(
                    label="Merchants",
                    value=f"{kpis['total_merchants'].iloc[0]:,.0f}",
                    help="Number of active merchants"
                )
            
            with col4:
                st.metric(
                    label="Avg Ticket",
                    value=f"R$ {kpis['avg_ticket'].iloc[0]:,.2f}",
                    help="Average value per transaction"
                )
    except Exception as e:
        st.error(f"Error loading KPIs: {str(e)}")
    
    # Alertas críticos
    try:
        alerts = load_alerts(db_manager, days=days_filter)
        critical_alerts = alerts[alerts['severity_score'] >= 4] if not alerts.empty else pd.DataFrame()
        
        if not critical_alerts.empty:
            st.markdown("---")
            st.subheader(f"Critical Alerts (Last {days_filter} days)")
            
            for _, alert in critical_alerts.head(3).iterrows():
                col1, col2, col3 = st.columns([2, 3, 2])
                with col1:
                    st.markdown(f"**{alert['alert_level']}**")
                with col2:
                    st.markdown(f"{alert['product']} - {alert['entity']}")
                with col3:
                    st.markdown(f"*{alert['alert_message']}*")
    except Exception as e:
        st.warning(f"Could not load alerts: {str(e)}")
    
    st.markdown("---")

    
    # ========== SEÇÃO 2: PRINCIPAIS GRÁFICOS ==========
    # Key metrics overview
    st.header(f"Key Metrics Overview - Last {days_filter} Days")
    try:
        daily_trends = load_daily_trends(db_manager, days=days_filter)
        if not daily_trends.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_tpv = daily_trends['tpv'].sum()
                st.metric(
                    label="Total TPV",
                    value=f"R$ {total_tpv:,.2f}",
                    help=f"Total Payment Volume in last {days_filter} days"
                )
            with col2:
                total_transactions = daily_trends['transactions'].sum()
                st.metric(
                    label="Transactions",
                    value=f"{total_transactions:,.0f}",
                    help=f"Total Transactions in last {days_filter} days"
                )
            with col3:
                avg_ticket = (total_tpv / total_transactions) if total_transactions > 0 else 0
                st.metric(
                    label="Avg Ticket",
                    value=f"R$ {avg_ticket:,.2f}",
                    help=f"Average Ticket in last {days_filter} days"
                )
            with col4:
                last_var_d7 = daily_trends['var_d7_pct'].iloc[-1]
                st.metric(
                    label="D-7 Variation",
                    value=f"{last_var_d7:.2f}%",
                    help=f"Variation compared to D-7 in last {days_filter} days"
                )
    except Exception as e:
        st.error(f"Error loading daily trends: {str(e)}")
    
    # Linha 1: Tendências temporais
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"TPV Over Time - Last")
        
        try:
            daily_trends = load_daily_trends(db_manager, days=days_filter)
            if not daily_trends.empty:
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(
                    x=daily_trends['day'],
                    y=daily_trends['tpv'],
                    mode='lines+markers',
                    name='TPV',
                    line=dict(color='#1f77b4', width=2),
                    fill='tozeroy'
                ))
                fig1.add_trace(go.Scatter(
                    x=daily_trends['day'],
                    y=daily_trends['moving_avg_7d'],
                    mode='lines',
                    name=f'{days_filter}-day Moving Avg',
                    line=dict(color='#ff7f0e', width=2, dash='dash')
                ))
                fig1.update_layout(
                    xaxis_title="Date",
                    yaxis_title="TPV (R$)",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig1, width='stretch')
        except Exception as e:
            st.error(f"Error loading TPV trend: {str(e)}")
    
    with col2:
        st.subheader(f"D-{days_filter} Variation (%)")
        try:
            if not daily_trends.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=daily_trends['day'],
                    y=daily_trends['var_d7_pct'],
                    marker_color=daily_trends['var_d7_pct'].apply(
                        lambda x: '#2ecc71' if x > 0 else '#e74c3c'
                    ),
                    name='Variation vs D-7'
                ))
                fig2.add_hline(y=0, line_dash="dash", line_color="gray")
                fig2.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Variation (%)",
                    height=400
                )
                st.plotly_chart(fig2, width='stretch')
        except Exception as e:
            st.error(f"Error loading variation chart: {str(e)}")
    
    # Linha 2: Análises comparativas
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Product Comparison")
        try:
            product_comp = load_product_comparison(db_manager)
            
            if not product_comp.empty:
                fig3 = px.bar(
                    product_comp.head(10),
                    x='product',
                    y='tpv',
                    color='entity',
                    title='',
                    labels={'tpv': 'TPV (R$)', 'product': 'Product', 'entity': 'Type'}
                )
                fig3.update_layout(height=400)
                st.plotly_chart(fig3, width='stretch')
        except Exception as e:
            st.error(f"Error loading product comparison: {str(e)}")
    
    with col4:
        st.subheader("Performance by Weekday")
        try:
            weekday_analysis = load_weekday_analysis(db_manager)
            
            if not weekday_analysis.empty:
                fig4 = px.line(
                    weekday_analysis,
                    x='weekday',
                    y='avg_daily_tpv',
                    markers=True,
                    title='',
                    labels={'avg_daily_tpv': 'Daily Avg TPV (R$)', 'weekday': 'Weekday'}
                )
                fig4.update_layout(height=400)
                st.plotly_chart(fig4, width='stretch')
        except Exception as e:
            st.error(f"Error loading weekday analysis: {str(e)}")
    
    # Linha 3: Análises adicionais
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("Anticipation Methods")
        try:
            anticipation = load_anticipation_analysis(db_manager)
            
            if not anticipation.empty:
                fig5 = px.sunburst(
                    anticipation,
                    path=['entity', 'anticipation_method'],
                    values='tpv',
                    title=''
                )
                
                # Configurar hover com porcentagem
                fig5.update_traces(
                    hovertemplate='<b>%{label}</b><br>' +
                                'TPV: R$ %{value:,.2f}<br>' +
                                'Porcentagem: %{percentParent:.2%}<br>' +
                                '<extra></extra>'
                )
                
                fig5.update_layout(height=400)
                st.plotly_chart(fig5, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading anticipation analysis: {str(e)}")
    
    with col6:
        st.subheader("Installments Analysis")
        try:
            installments = load_installments_analysis(db_manager)
            
            if not installments.empty:
                fig6 = go.Figure()
                fig6.add_trace(go.Bar(
                    x=installments['installments'],
                    y=installments['tpv'],
                    name='TPV',
                    yaxis='y'
                ))
                fig6.add_trace(go.Scatter(
                    x=installments['installments'],
                    y=installments['avg_ticket'],
                    name='Avg Ticket',
                    yaxis='y2',
                    mode='lines+markers',
                    line=dict(color='red')
                ))
                fig6.update_layout(
                    xaxis_title="Number of Installments",
                    yaxis=dict(title="TPV (R$)"),
                    yaxis2=dict(title="Avg Ticket (R$)", overlaying='y', side='right'),
                    height=400
                )
                st.plotly_chart(fig6, width='stretch')
        except Exception as e:
            st.error(f"Error loading installments analysis: {str(e)}")
    
    st.markdown("---")
    
    # ========== SEÇÃO 3: CHAT PARA PERGUNTAS ==========
    st.header("💬 Custom Analysis with AI")
    st.markdown("Ask questions about the data and AI will automatically generate SQL to answer.")
    
    # Estado da sessão
    if 'query_result' not in st.session_state:
        st.session_state.query_result = None
    if 'generated_sql' not in st.session_state:
        st.session_state.generated_sql = None
    if 'insights' not in st.session_state:
        st.session_state.insights = None
    if 'user_question' not in st.session_state:
        st.session_state.user_question = ""
    
    # Input e botões
    ## MOSTRAR EXPANDER PERGUNTAS EXEMPLO
    with st.expander("**Most frequent questions examples**"):
        st.markdown("""
        - Which product has the highest TPV?
        - How do weekdays influence TPV?
        - Which segment has the highest average TPV? And the highest Average Ticket?
        - Which anticipation method is most used by individuals and by businesses?
        """)

    user_question = st.text_area(
        "Your question:",
        placeholder="Ex: Which products have the highest TPV in March 2025?",
        height=100,
        value=st.session_state.user_question
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
    
    with col_btn1:
        submit_button = st.button("🔍 Submit Question", type="primary", width='stretch')
    
    with col_btn2:
        insights_button = st.button(
            "✨ Generate Insights", 
            width='stretch', 
            disabled=(st.session_state.query_result is None)
        )
    
    with col_btn3:
        clear_button = st.button("🗑️ Clear", width='stretch')
    
    if clear_button:
        st.session_state.query_result = None
        st.session_state.generated_sql = None
        st.session_state.insights = None
        st.session_state.response = None
        st.session_state.user_question = ""
        st.rerun()
    
    if submit_button and user_question:
        
        st.session_state.user_question = user_question
        
        with st.spinner("🤖 Generating SQL and executing query..."):
            try:
                results = generate_sql_with_ai(user_question, db_manager)

                sql_query = results.get("querySQL", "")
                explanation = results.get("explanation", "")
                
                if sql_query:
                    result_df = db_manager.select_query(sql_query)
                    
                    if not result_df.empty:
                        st.session_state.query_result = result_df
                        st.session_state.generated_sql = sql_query
                        st.session_state.response = results
                        st.session_state.insights = None
                        st.rerun()
                        st.success(f"✅ Query executed successfully! {len(result_df)} records found.")
                        st.info(f"**Explanation:** {explanation}")
                    else:
                        st.warning("⚠️ Query returned no results.")
                else:
                    st.error("❌ Could not generate SQL for your question.")
            
            except Exception as e:
                st.error(f"❌ Error processing question: {str(e)}")

    # Processar geração de insights
    if insights_button and st.session_state.query_result is not None:
        with st.spinner("🤖 Analyzing data and generating insights..."):
            try:
                insights = generate_insights_with_ai(
                    st.session_state.user_question,
                    st.session_state.query_result,
                    st.session_state.response
                )
                conclusion = insights.get("conclusion", "")

                st.session_state.insights = insights
                insights_request = insights.get("insights_request", "")
                st.success("✅ Insights generated successfully!")
                st.info(f"**Conclusion:** {conclusion}")
                st.info(f"**Insights Request:** {insights_request}")
                
            except Exception as e:
                st.error(f"❌ Error generating insights: {str(e)}")
    
    # Exibir insights
    if st.session_state.insights:
        st.markdown("---")
        st.markdown("### 💡 Insights and Detailed Analysis")
        st.markdown(st.session_state.insights)

    # Exibir resultados
    if st.session_state.query_result is not None and not st.session_state.query_result.empty:
        st.markdown("### 📈 Visualization")

        df = st.session_state.query_result
        suggestion = st.session_state.response

        auto_visualize(df, suggestion)

    #exibir SQL gerado e expandir
    if st.session_state.generated_sql:
        with st.expander("Generated SQL Query"):
            st.code(st.session_state.generated_sql, language='sql')
    
    # mostrar table de dados brutos
    if st.session_state.query_result is not None and not st.session_state.query_result.empty:
        st.markdown("### 📋 Raw Data")
        st.dataframe(st.session_state.query_result)
    
    #opcao de download dos dados
    if st.session_state.query_result is not None and not st.session_state.query_result.empty:
        csv_data = st.session_state.query_result.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv_data,
            file_name='query_results.csv',
            mime='text/csv'
        )
    
    

if __name__ == "__main__":
    main()
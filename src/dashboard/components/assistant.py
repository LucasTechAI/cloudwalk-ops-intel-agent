from streamlit import (
    session_state,
    header,
    markdown,
    columns,
    button,
    text_area,
    expander,
    spinner,
    progress,
    empty,
    success,
    info,
    warning,
    error,
    download_button,
    code,
    metric,
    tabs,
    rerun,
    toast,
    dataframe,
)
from logging import Logger, basicConfig, getLogger, INFO
from datetime import datetime
from pathlib import Path
from sys import path


basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))

from src.dashboard.utils.ai_service import (
    generate_sql_with_ai,
    generate_insights_with_ai,
    auto_visualize,
)
from src.utils.sqlite_manager import SqliteManager


def render_assistant_page(db_manager: SqliteManager) -> None:
    """Renders the AI-Powered Assistant page"""
    logger.info("Rendering Assistant Page")
    header("💬 AI-Powered Custom Analysis")

    markdown(
        """
    Ask questions about your data and the AI will automatically:
    - 🔍 Generate optimized SQL queries
    - 📊 Create appropriate visualizations
    - 💡 Provide actionable insights
    """
    )

    if "query_result" not in session_state:
        session_state.query_result = None
    if "generated_sql" not in session_state:
        session_state.generated_sql = None
    if "insights" not in session_state:
        session_state.insights = None
    if "user_question" not in session_state:
        session_state.user_question = ""
    if "response" not in session_state:
        session_state.response = None

    with expander("💡 **Example Questions**", expanded=False):
        markdown(
            """
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
        """
        )

    markdown("---")

    user_question = text_area(
        "**Your Question:**",
        placeholder="Example: Which products have the highest TPV in March 2025?",
        height=100,
        value=session_state.user_question,
        help="Ask any question about the data and AI will analyze it for you",
    )

    col_ai1, col_ai2, col_ai3, col_ai4 = columns([3, 2, 2, 1])

    with col_ai1:
        logger.info("User question input received")
        submit_button = button(
            "🔍 Analyze Question",
            type="primary",
            width="stretch",
            disabled=not user_question.strip(),
        )

    with col_ai2:
        logger.info("Preparing to generate insights button")
        insights_button = button(
            "✨ Generate Insights",
            width="stretch",
            disabled=(session_state.query_result is None),
        )

    with col_ai3:
        logger.info("Preparing to export results button")
        export_button = button(
            "📥 Export Results",
            width="stretch",
            disabled=(session_state.query_result is None),
        )

    with col_ai4:
        logger.info("Preparing to clear results button")
        clear_button = button("🗑️", width="stretch", help="Clear all results")

    if submit_button and user_question:
        logger.info("Submitting user question for analysis")
        session_state.user_question = user_question

        with spinner("AI is analyzing your question..."):
            try:
                logger.info("Generating SQL with AI")
                progress_bar = progress(0)
                status = empty()

                status.text("🔍 Generating SQL query...")
                progress_bar.progress(33)

                results = generate_sql_with_ai(user_question, db_manager)
                sql_query = results.get("querySQL", "")
                explanation = results.get("explanation", "")

                if sql_query:
                    logger.info("Executing generated SQL query")
                    status.text("⚡ Executing query...")
                    progress_bar.progress(66)

                    result_df = db_manager.select_query(sql_query)

                    if not result_df.empty:
                        logger.info("Query executed successfully with results")
                        status.text("✅ Query completed!")
                        progress_bar.progress(100)

                        session_state.query_result = result_df
                        session_state.generated_sql = sql_query
                        session_state.response = results
                        session_state.insights = None

                        progress_bar.empty()
                        status.empty()

                        success(
                            f"✅ Analysis complete! Found {len(result_df)} records."
                        )

                        if explanation:
                            info(f"**AI Explanation:** {explanation}")

                        rerun()
                    else:
                        logger.warning("Query executed but returned no results")
                        progress_bar.empty()
                        status.empty()
                        warning(
                            "⚠️ Query returned no results. Try rephrasing your question."
                        )
                else:
                    logger.error("Failed to generate SQL from AI")
                    progress_bar.empty()
                    status.empty()
                    error(
                        "❌ Could not generate SQL for your question. Please try rephrasing."
                    )

            except Exception as e:
                logger.error(f"Exception during AI analysis: {e}")
                error(f"❌ Error processing question: {str(e)}")

    if insights_button and session_state.query_result is not None:
        logger.info("Generating insights from data")
        with spinner("Generating insights from data..."):
            try:
                insights = generate_insights_with_ai(
                    session_state.user_question,
                    session_state.query_result,
                    session_state.response,
                )

                session_state.insights = insights
                success("✅ Insights generated successfully!")

                conclusion = insights.get("conclusion", "")
                if conclusion:
                    logger.info("Displaying key insight conclusion")
                    info(f"**Key Insight:** {conclusion}")

            except Exception as e:
                logger.error(f"Exception during insights generation: {e}")
                error(f"❌ Error generating insights: {str(e)}")

    if export_button and session_state.query_result is not None:
        logger.info("Exporting query results as CSV")
        csv_data = session_state.query_result.to_csv(index=False).encode("utf-8")
        download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f'analysis_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime="text/csv",
            width="stretch",
        )

    if clear_button:
        logger.info("Clearing all session results")
        session_state.query_result = None
        session_state.generated_sql = None
        session_state.insights = None
        session_state.response = None
        session_state.user_question = ""
        rerun()

    if session_state.query_result is not None:
        markdown("---")

        if session_state.insights:
            markdown("### 💡 AI-Generated Insights")

            conclusion = session_state.insights.get("conclusion", "")
            insights_request = session_state.insights.get("insightsRequest", "")
            next_steps = session_state.insights.get("nextSteps", "")

            markdown(
                """
                <style>
                .insight-card {
                    background: ##ffffff;
                    padding: 2rem;
                    border-radius: 8px;
                    color: black;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                    border-left: 10px solid #ffc800;
                }

                .insight-title {
                    font-size: 2rem;
                    font-weight: 600;
                    margin-bottom: 1.5rem;
                    letter-spacing: -0.02em;
                }

                .insight-section-title {
                    font-size: 1.5rem;
                    font-weight: 600;
                    margin-top: 1.5rem;
                    margin-bottom: 0.75rem;
                    opacity: 0.95;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    font-size: 0.9rem;
                }

                .insight-text0 {
                    font-size: 1.2rem;
                    line-height: 1.6;
                    opacity: 0.9;
                    font-weight: 400;
                }
                .insight-text1 {
                    font-size: 0.95rem;
                    line-height: 1.6;
                    opacity: 0.92;
                    font-weight: 400;
                }
                        
                </style>
                """,
                unsafe_allow_html=True,
            )

            markdown(
                f"""
            <div class="insight-card">
                <div class="insight-title"><b>Executive Summary</b></div>
                <div class="insight-text0">{conclusion}</div>
                <div class="insight-section-title"><b>Key Findings</b></div>
                <div class="insight-text1">{insights_request}</div>
                <div class="insight-section-title"><b>Recommended Actions</b></div>
                <div class="insight-text1">{next_steps}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            markdown("---")

        markdown("### 📊 Visualization")

        if session_state.response:
            logger.info("Auto-generating visualization from AI suggestion")
            auto_visualize(session_state.query_result, session_state.response)

        markdown("---")

        result_tab1, result_tab2 = tabs(["📋 Data Table", "💻 SQL Query"])

        with result_tab1:
            dataframe(session_state.query_result, width="stretch", height=400)

            markdown("##### Quick Stats")
            col_stat1, col_stat2, col_stat3 = columns(3)

            with col_stat1:
                metric("Rows", f"{len(session_state.query_result):,}")

            with col_stat2:
                metric("Columns", f"{len(session_state.query_result.columns):,}")

            with col_stat3:
                memory = session_state.query_result.memory_usage(deep=True).sum() / 1024
                metric("Memory", f"{memory:.2f} KB")

        with result_tab2:
            if session_state.generated_sql:
                code(session_state.generated_sql, language="sql")

                if button("📋 Copy SQL", width="stretch"):
                    toast("✅ SQL copied to clipboard!")

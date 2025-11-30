from streamlit import warning, metric, dataframe, plotly_chart
from plotly.express import bar, line, box, histogram, scatter
from logging import Logger, basicConfig, getLogger, INFO
from pandas import DataFrame
from pathlib import Path
from sys import path

basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


root_path = Path(__file__).parent.parent.parent
path.append(str(root_path))

from src.dashboard.utils.charts import apply_chart_theme
from src.agents.agent_invoker import AgentInvoker
from src.agents.utils.prompt_tool_loader import AgentResourceLoader
from src.utils.sqlite_manager import SqliteManager

global loader, agent
loader = AgentResourceLoader(prompts_dir="agents/prompts", tools_dir="agents/tools")
agent = AgentInvoker(model_name="llama3.1", temperature=0, max_retries=3)


def generate_sql_with_ai(user_question: str, db_manager: SqliteManager) -> dict:
    """Generation of a SQL query using AI based on the user's question"""
    try:
        logger.info("Generating SQL with AI")
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
            tool_choice="required",
        )

        return response

    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        return f"Erro ao gerar SQL: {str(e)}"


def generate_insights_with_ai(
    user_question: str, data_df: DataFrame, response: dict
) -> dict:
    """Generate insights using AI based on the data"""
    try:
        logger.info("Generating insights with AI")
        system_prompt = loader.load_prompt("generate_insights.txt")
        tool_definition = loader.load_tools("generate_insights.json")

        user_message = (
            "Based on the data returned from the SQL query and the user's original question, "
            "generate detailed insights and analysis.\n\n"
            f"User Question: {user_question}\n\n"
            f"SQL Query: {response.get('querySQL', '')}\n\n"
            f"Data:\n{data_df.to_json(orient='records')}\n\n"
            "Provide insights in a clear and structured manner."
            " YOU MUST return a JSON with the following fields: "
            "insightsRequest, conclusion, nextSteps"
        )

        insights_response = agent.invoke_with_tools(
            system_prompt=system_prompt,
            user_message=user_message,
            tools=tool_definition,
            tool_choice="required",
        )

        return insights_response

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return f"Erro ao gerar insights: {str(e)}"


def auto_visualize(df: DataFrame, suggestion: dict) -> None:
    """Generate automatic visualization based on AI suggestion"""
    logger.info("Generating automatic visualization")
    plot_type = suggestion.get("plotSuggestion", None)
    title = suggestion.get("title", "Auto-generated Visualization")
    x_axis = suggestion.get("x-axis", None)
    y_axis = suggestion.get("y-axis", None)

    numeric_cols = df.select_dtypes(include=["float", "int"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

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

    if plot_type == "bar":
        fig = bar(df, x=x_axis, y=y_axis, title=title)
    elif plot_type == "barh":
        fig = bar(df, x=y_axis, y=x_axis, orientation="h", title=title)
    elif plot_type == "line":
        fig = line(df, x=x_axis, y=y_axis, markers=True, title=title)
    elif plot_type == "boxplot":
        fig = box(df, x=x_axis, y=y_axis, title=title)
    elif plot_type == "hist":
        fig = histogram(df, x=x_axis, title=title)
    elif plot_type == "scatter":
        size_col = numeric_cols[2] if len(numeric_cols) > 2 else None
        fig = scatter(df, x=x_axis, y=y_axis, size=size_col, title=title)
    elif plot_type == "table":
        dataframe(df, width="stretch")
        return
    elif plot_type == "number":
        if numeric_cols:
            metric = df[numeric_cols[0]].sum()
            metric(label=title, value=f"{metric:,.2f}")
            return
        else:
            warning("Nenhuma coluna numérica disponível.")
            return
    else:
        if numeric_cols and categorical_cols:
            fig = bar(
                df, x=categorical_cols[0], y=numeric_cols[0], title="Auto Bar Chart"
            )
        elif len(numeric_cols) >= 2:
            fig = scatter(
                df, x=numeric_cols[0], y=numeric_cols[1], title="Auto Scatter"
            )
        else:
            dataframe(df, width="stretch")
            return

    fig = apply_chart_theme(fig, title)
    plotly_chart(fig, width="stretch")
    logger.info("Visualization generated successfully")

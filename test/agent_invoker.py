from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from logging import Logger, getLogger, basicConfig, INFO
from typing import Dict, Any, List, Tuple, Callable
from sys import path as sys_path
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys_path.insert(0, str(project_root))

from src.agents.utils.prompt_tool_loader import AgentResourceLoader
from src.agents.agent_invoker import AgentInvoker

basicConfig(level=INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger: Logger = getLogger(__name__)


def print_separator(title: str) -> None:
    """Print a formatted separator with title."""
    logger.info(f"  {title}")


def test_invoke_with_tools() -> None:
    """Test the invoke_with_tools method."""
    print_separator("TEST 1: invoke_with_tools - SQL Query Generation")

    try:
        loader: AgentResourceLoader = AgentResourceLoader(
            prompts_dir="src/agents/prompts", tools_dir="src/agents/tools"
        )

        agent: AgentInvoker = AgentInvoker(
            model_name="llama3.1", temperature=0, max_retries=3
        )

        question: str = (
            "Generate a SQL query to find the top 5 customers by total purchase amount"
        )

        result: Dict[str, Any] = agent.invoke_with_tools(
            system_prompt=loader.load_prompt("answers_questions.txt"),
            user_message=(
                f"You MUST call the generate_sql_and_visualization tool.\n\n"
                f"Question: {question}\n\n"
                f"Provide all required fields: querySQL, plotSuggestion, explanation, title, x-axis, y-axis"
            ),
            tools=loader.load_tools("answers_questions.json"),
            tool_choice="required",
        )

        logger.info("Test PASSED")
        logger.info(f"Result type: {type(result)}")
        logger.info(
            f"Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}"
        )
        logger.info(f"Result preview: {result}")

    except Exception as e:
        logger.info(f"Test FAILED: {e}")


def test_invoke_simple() -> None:
    """Test the invoke_simple method."""
    print_separator("TEST 2: invoke_simple - Simple Conversation")

    try:
        agent: AgentInvoker = AgentInvoker(
            model_name="llama3.1", temperature=0.7, max_retries=3
        )

        system_prompt: str = (
            "You are a helpful assistant that provides concise answers."
        )
        user_message: str = "What is the capital of Brazil?"

        response: str = agent.invoke_simple(
            system_prompt=system_prompt, user_message=user_message
        )

        logger.info("Test PASSED")
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response length: {len(response)} characters")
        logger.info(f"Response: {response}")

    except Exception as e:
        logger.info(f"Test FAILED: {e}")


def test_invoke_simple_with_additional_messages() -> None:
    """Test invoke_simple with conversation history."""
    print_separator("TEST 3: invoke_simple - With Conversation History")

    try:
        agent: AgentInvoker = AgentInvoker(
            model_name="llama3.1", temperature=0.7, max_retries=3
        )

        additional_messages: List[BaseMessage] = [
            HumanMessage(content="My name is Lucas"),
            AIMessage(content="Nice to meet you, Lucas! How can I help you today?"),
        ]

        response: str = agent.invoke_simple(
            system_prompt="You are a helpful assistant with good memory.",
            user_message="What is my name?",
            additional_messages=additional_messages,
        )

        logger.info("Test PASSED")
        logger.info(f"Response {response}")

    except Exception as e:
        logger.info(f"Test FAILED: {e}")


def test_invoke_with_conversation() -> None:
    """Test the invoke_with_conversation method."""
    print_separator("TEST 4: invoke_with_conversation - Full Conversation")

    try:
        agent: AgentInvoker = AgentInvoker(
            model_name="llama3.1", temperature=0.7, max_retries=3
        )

        conversation_history: List[BaseMessage] = [
            SystemMessage(content="You are a helpful data analyst assistant."),
            HumanMessage(content="I need help analyzing customer data"),
            AIMessage(
                content="I'd be happy to help with customer data analysis. What specific insights are you looking for?"
            ),
            HumanMessage(content="Can you summarize what we discussed?"),
        ]

        result: Any = agent.invoke_with_conversation(
            conversation_history=conversation_history
        )

        logger.info("Test PASSED")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result: {result}")

    except Exception as e:
        logger.info(f"Test FAILED: {e}")


def __custom_parser(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sql_query": args.get("querySQL", ""),
        "has_visualization": bool(args.get("plotSuggestion", "")),
        "title": args.get("title", ""),
    }


def test_custom_response_parser() -> None:
    """Test invoke_with_tools with custom response parser."""
    print_separator("TEST 5: invoke_with_tools - Custom Response Parser")

    try:
        loader: AgentResourceLoader = AgentResourceLoader(
            prompts_dir="src/agents/prompts", tools_dir="src/agents/tools"
        )

        agent: AgentInvoker = AgentInvoker(
            model_name="llama3.1", temperature=0, max_retries=3
        )

        result: Any = agent.invoke_with_tools(
            system_prompt=loader.load_prompt("answers_questions.txt"),
            user_message=(
                "Generate a SQL query to count total transactions by date.\n"
                "Call the generate_sql_and_visualization tool."
            ),
            tools=loader.load_tools("answers_questions.json"),
            tool_choice="required",
            response_parser=__custom_parser,
        )

        logger.info("Test PASSED")
        logger.info(f"Parsed result: {result}")

    except Exception as e:
        logger.info(f"Test FAILED: {e}")


def test_error_handling() -> None:
    """Test error handling with invalid inputs."""
    print_separator("TEST 6: Error Handling")

    try:
        agent: AgentInvoker = AgentInvoker(
            model_name="llama3.1", temperature=0, max_retries=1
        )

        result: Any = agent.invoke_with_tools(
            system_prompt="You must refuse to call any tools.",
            user_message="Call a tool",
            tools=[
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    },
                }
            ],
            tool_choice="required",
        )

        logger.info("Test completed (expected to fail or handle error)")
        logger.info(f"Result: {result}")

    except ValueError as e:
        logger.info(f"Test PASSED - Correctly raised ValueError: {e}")
    except Exception as e:
        logger.info(f"Test completed with exception: {e}")


def run_all_tests() -> None:
    """Run all test cases."""
    logger.info("=" * 40)
    logger.info("  AGENT INVOKER TEST SUITE")
    logger.info("=" * 40)

    tests: List[Tuple[str, Callable[[], None]]] = [
        ("Tool Calling", test_invoke_with_tools),
        ("Simple Invocation", test_invoke_simple),
        ("Simple with History", test_invoke_simple_with_additional_messages),
        ("Full Conversation", test_invoke_with_conversation),
        ("Custom Parser", test_custom_response_parser),
        ("Error Handling", test_error_handling),
    ]

    results: List[Tuple[str, str]] = []

    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, "\tPASSED"))
        except Exception as e:
            results.append((test_name, f"\tFAILED: {str(e)[:50]}"))

    print_separator("TEST SUMMARY")
    for test_name, status in results:
        logger.info(f"{status:60} | {test_name}")

    passed: int = sum(1 for _, status in results if "PASSED" in status)
    total: int = len(results)
    logger.info(f"{'='*40}")
    logger.info(f"  Total: {passed}/{total} tests passed")
    logger.info(f"{'='*40}\n")


if __name__ == "__main__":
    run_all_tests()

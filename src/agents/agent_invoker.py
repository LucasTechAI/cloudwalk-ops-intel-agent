from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from logging import Logger, basicConfig, getLogger, INFO
from typing import Dict, Any, List, Optional, Callable
from langchain_ollama import ChatOllama
from json import loads


basicConfig(
    level=INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)
logger: Logger = getLogger(__name__)


class AgentInvoker:
    """
    Generic class for invoking LLM agents with tool calling capabilities.

    Attributes:
        model_name (str): Name of the Ollama model to use.
        temperature (float): Temperature for model generation.
        max_retries (int): Maximum number of retries for tool calling.
    """

    def __init__(
        self, model_name: str = "llama3.1", temperature: float = 0, max_retries: int = 3
    ) -> None:
        """
        Initialize the AgentInvoker.

        Args:
            model_name: Name of the Ollama model.
            temperature: Temperature parameter for generation.
            max_retries: Maximum retry attempts for tool calling.
        """
        logger.info(f"AgentInvoker initialized with model: {model_name}")
        self.model_name: str = model_name
        self.temperature: float = temperature
        self.max_retries: int = max_retries
        self.model: ChatOllama = ChatOllama(
            model=self.model_name, temperature=self.temperature
        )

    def invoke_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        additional_messages: Optional[List[BaseMessage]] = None,
        response_parser: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke the model with tool calling capability.

        Args:
            system_prompt: System prompt for the agent.
            user_message: User's input message.
            tools: List of tool definitions (JSON schemas).
            tool_choice: Tool choice mode ("required", "auto", or specific tool name).
            additional_messages: Optional additional messages to include in conversation.
            response_parser: Optional custom parser for the response.

        Returns:
            Dict containing the tool call arguments or parsed response.

        Raises:
            ValueError: If model fails to call tools after all retries.
        """
        logger.info("Binding tools to the model...")
        model_with_tools: ChatOllama = self.model.bind_tools(
            tools, tool_choice=tool_choice
        )

        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
        if additional_messages:
            messages.extend(additional_messages)

        messages.append(HumanMessage(content=user_message))

        logger.info("Starting invocation with tool calling...")
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Attempt {attempt}/{self.max_retries} — invoking model...")

            try:
                response: BaseMessage = model_with_tools.invoke(messages)
                logger.info(f"RAW RESPONSE: {response}")
                logger.info("Model response received.")

                tool_calls: Optional[List[Dict[str, Any]]] = getattr(
                    response, "tool_calls", None
                )
                if tool_calls:
                    logger.info(f"Tool call detected: {tool_calls[0]['name']}")

                    args: Dict[str, Any] = tool_calls[0].get("args", {})
                    if not isinstance(args, dict):
                        logger.warning(
                            "Tool arguments not parsed as dict. Attempting recovery..."
                        )
                        try:
                            args = loads(tool_calls[0]["args"])
                        except Exception as e:
                            raise ValueError(f"Failed to parse tool args: {e}")

                    if response_parser:
                        return response_parser(args)

                    return args

                if tool_choice == "auto" and hasattr(response, "content"):
                    logger.info("No tool call, but text response received.")
                    return {"response": response.content}

                logger.warning(
                    f"No tool call detected on attempt {attempt}. Retrying..."
                )

            except Exception as e:
                logger.error(f"Error during invocation attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    raise

        raise ValueError("Model failed to call the required tool after all retries.")

    def invoke_simple(
        self,
        system_prompt: str,
        user_message: str,
        additional_messages: Optional[List[BaseMessage]] = None,
    ) -> str:
        """
        Simple invocation without tool calling.

        Args:
            system_prompt: System prompt for the agent.
            user_message: User's input message.
            additional_messages: Optional additional messages.

        Returns:
            String response from the model.
        """
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]

        if additional_messages:
            messages.extend(additional_messages)

        messages.append(HumanMessage(content=user_message))

        logger.info("Invoking model (simple mode)...")
        response: BaseMessage = self.model.invoke(messages)

        return response.content

    def invoke_with_conversation(
        self,
        conversation_history: List[BaseMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        """
        Invoke model with full conversation history.

        Args:
            conversation_history: List of messages representing the conversation.
            tools: Optional list of tool definitions.
            tool_choice: Tool choice mode.

        Returns:
            Dict containing response or tool call arguments.
        """
        if tools:
            model_with_tools: ChatOllama = self.model.bind_tools(
                tools, tool_choice=tool_choice
            )
            response: BaseMessage = model_with_tools.invoke(conversation_history)

            tool_calls: Optional[List[Dict[str, Any]]] = getattr(
                response, "tool_calls", None
            )
            if tool_calls:
                return tool_calls[0].get("args", {})
        else:
            response: BaseMessage = self.model.invoke(conversation_history)

        return {"response": response.content}


if __name__ == "__main__":
    from pathlib import Path
    from sys import path as sys_path

    # Add project root to Python path
    project_root = Path(__file__).resolve().parent.parent.parent
    sys_path.insert(0, str(project_root))

    from src.agents.utils.prompt_tool_loader import AgentResourceLoader

    loader = AgentResourceLoader(prompts_dir="agents/prompts", tools_dir="agents/tools")

    question = "Generate a SQL query to find the top 5 customers by total purchase amount and provide a bar chart visualization."

    max_retries = 3

    agent = AgentInvoker(model_name="llama3.1", temperature=0, max_retries=max_retries)

    result = agent.invoke_with_tools(
        system_prompt=loader.load_prompt("answers_questions.txt"),
        user_message=(
            "You MUST call the generate_sql_and_visualization tool to answer.\n\n"
            f"Question: {question}\n\n"
            "IMPORTANT: Call the tool with all required parameters only. "
            "You MUST provide ALL required fields with meaningful content: ",
            "- querySQL",
            "- plotSuggestion",
            "- explanation",
            "- title",
            "- x-axis",
            "- y-axis",
        ),
        tools=loader.load_tools("answers_questions.json"),
        tool_choice="required",
    )

    print("=== FINAL RESULT ===")
    print(result)

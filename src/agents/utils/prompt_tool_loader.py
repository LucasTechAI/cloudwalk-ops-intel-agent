from logging import Logger, getLogger, basicConfig, INFO
from typing import Dict, Any, Optional, List
from json import JSONDecodeError, load
from contextlib import contextmanager
from pathlib import Path


basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: Logger = getLogger(__name__)



PATH_ROOT: Path = Path(__file__).resolve().parents[2]
DEFAULT_PROMPTS_DIR: str = "agents/prompts"
DEFAULT_TOOLS_DIR: str = "agents/tools"
DEFAULT_ENCODING: str = "utf-8"


class ResourceNotFoundError(Exception):
    """
    Exception raised when a requested resource is not found.
    """
    pass


class PromptLoader:
    """
    Load and manage prompts from text files.
    """
    
    def __init__(self, prompts_dir: str = DEFAULT_PROMPTS_DIR) -> None:
        """
        Initialize the prompt loader.
        Args:
            prompts_dir: Caminho relativo ao diretório de prompts.
        """
        self.prompts_dir: Path = PATH_ROOT / prompts_dir
        self._prompts_cache: Dict[str, str] = {}
        self._validate_directory()
    
    def _validate_directory(self) -> None:
        """
        Validates if the prompts directory exists.
        """
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            self.prompts_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created: {self.prompts_dir}")
    
    def load(self, filename: str, use_cache: bool = True) -> str:
        """
        Load a prompt from a file.
        Args:
            filename: Name of the prompt file (e.g., 'answers_questions.txt').
            use_cache: If True, use cache. If False, force reload.
            
        Returns:
            Prompt content.
            ResourceNotFoundError: If the file is not found.
        """
        if use_cache and filename in self._prompts_cache:
            logger.debug(f"Prompt '{filename}' loaded from cache")
            return self._prompts_cache[filename]
        
        filepath = self.prompts_dir / filename
        
        if not filepath.exists():
            raise ResourceNotFoundError(
                f"Prompt file not found: {filepath}"
            )
        
        try:
            logger.info(f"Loading prompt: {filepath}")
            with open(filepath, "r", encoding=DEFAULT_ENCODING) as f:
                content: str = f.read().strip()
            
            if not content:
                logger.warning(f"Empty prompt: {filename}")
            
            self._prompts_cache[filename] = content
            return content
            
        except Exception as e:
            logger.error(f"Error loading prompt '{filename}': {e}")
            raise
    
    def format(self, filename: str, **kwargs) -> str:
        """
        Load and format a prompt with variables.
        Args:
            filename: Name of the prompt file.
            **kwargs: Variables for formatting.
        Returns:
            Prompt formatado.
        Raises:
            KeyError: Se variáveis obrigatórias estiverem faltando.
        """
        prompt = self.load(filename)
        
        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            logger.error(f"Variável faltando no prompt '{filename}': {e}")
            raise ValueError(
                f"Variável {e} não fornecida para o prompt '{filename}'"
            ) from e
    
    def reload(self, filename: Optional[str] = None) -> None:
        """
        Load prompts from disk (clear cache).
        Args:
            filename: Specific file to reload, or None for all.
        """
        if filename:
            if filename in self._prompts_cache:
                del self._prompts_cache[filename]
                logger.info(f"Prompt reloaded: {filename}")
            else:
                logger.warning(f"Prompt was not in cache: {filename}")
        else:
            count = len(self._prompts_cache)
            self._prompts_cache.clear()
            logger.info(f"Prompt cache cleared ({count} prompts removed)")
    
    def list_prompts(self) -> List[str]:
        """
        List all available prompt files.
        Returns:
            List of file names.
        """
        if not self.prompts_dir.exists():
            return []
        return sorted([f.name for f in self.prompts_dir.glob("*.txt")])
    
    def exists(self, filename: str) -> bool:
        """
        Check if a prompt exists.
        Args:
            filename: Name of the file.
        Returns:
            True if the file exists, False otherwise.
        """
        return (self.prompts_dir / filename).exists()
    
    @property
    def cache_size(self) -> int:
        """Returns the number of prompts in cache."""
        return len(self._prompts_cache)


class ToolsLoader:
    """
    Loads and manages tools from JSON files.
    Attributes:
        tools_dir (Path): Path to the tools directory.
        _tools_cache (Dict[str, Any]): Internal cache of loaded tools.
    """
    
    def __init__(self, tools_dir: str = DEFAULT_TOOLS_DIR) -> None:
        """
        Initializes the tools loader.
        Args:
            tools_dir: Relative path to the tools directory.
        """
        self.tools_dir: Path = PATH_ROOT / tools_dir
        self._tools_cache: Dict[str, Any] = {}
        self._validate_directory()
    
    def _validate_directory(self) -> None:
        """Validates if the tools directory exists."""
        if not self.tools_dir.exists():
            logger.warning(f"Tools directory not found: {self.tools_dir}")
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created: {self.tools_dir}")
    
    def load(self, filename: str, use_cache: bool = True) -> Any:
        """
        Loads tools from a JSON file.
        Args:
            filename: Name of the tools file (e.g., 'sql_tools.json').
            use_cache: If True, use cache. If False, force reload.  
        Returns:
            Parsed JSON content of the tools.
        Raises:
            ResourceNotFoundError: If the file is not found.
            JSONDecodeError: If the file contains invalid JSON.
        """
        if use_cache and filename in self._tools_cache:
            logger.debug(f"Ferramentas '{filename}' carregadas do cache")
            return self._tools_cache[filename]
        
        filepath: Path = self.tools_dir / filename
        
        if not filepath.exists():
            raise ResourceNotFoundError(
                f"Tools file not found: {filepath}"
            )
        
        try:
            logger.info(f"Loading tools: {filepath}")
            with open(filepath, "r", encoding=DEFAULT_ENCODING) as f:
                content: Any = load(f)
            
            self._tools_cache[filename] = content
            return content
            
        except JSONDecodeError as e:
            logger.error(f"Invalid JSON in '{filename}': {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading tools '{filename}': {e}")
            raise
    
    def reload(self, filename: Optional[str] = None) -> None:
        """
        Reloads tools from disk (clears cache).
        
        Args:
            filename: Specific file to reload, or None for all.
        """
        if filename:
            if filename in self._tools_cache:
                del self._tools_cache[filename]
                logger.info(f"Tools reloaded: {filename}")
            else:
                logger.warning(f"Tools were not in cache: {filename}")
        else:
            count = len(self._tools_cache)
            self._tools_cache.clear()
            logger.info(f"Tools cache cleared ({count} files removed)")
    
    def list_tools(self) -> List[str]:
        """
        Lists all available tools files.
        
        Returns:
            List of filenames.
        """
        if not self.tools_dir.exists():
            return []
        return sorted([f.name for f in self.tools_dir.glob("*.json")])
    
    def get_tool(self, filename: str, tool_name: str) -> Optional[Dict]:
        """
        Gets a specific tool by name.
        
        Args:
            filename: Name of the tools file.
            tool_name: Name of the tool to retrieve.
            
        Returns:
            Tool definition or None if not found.
        """
        tools: Any = self.load(filename)
        
        if isinstance(tools, list):
            for tool in tools:
                if isinstance(tool, dict) and tool.get("name") == tool_name:
                    return tool
            logger.warning(f"Tool '{tool_name}' not found in '{filename}'")
        
        elif isinstance(tools, dict):
            if tool_name in tools:
                return tools[tool_name]
            logger.warning(f"Tool '{tool_name}' not found in '{filename}'")
        
        return None
    
    def exists(self, filename: str) -> bool:
        """
        Checks if a tools file exists.
        
        Args:
            filename: Name of the file.
            
        Returns:
            True if the file exists, False otherwise.
        """
        return (self.tools_dir / filename).exists()
    
    @property
    def cache_size(self) -> int:
        """Returns the number of tools files in cache."""
        return len(self._tools_cache)


class AgentResourceLoader:
    """
    Combined loader for prompts and tools.
    
    Provides a unified interface for loading agent resources.
    
    Attributes:
        prompts (PromptLoader): Loader de prompts.
        tools (ToolsLoader): Loader de ferramentas.
    """
    
    def __init__(
        self,
        prompts_dir: str = DEFAULT_PROMPTS_DIR,
        tools_dir: str = DEFAULT_TOOLS_DIR
    ) -> None:
        """
        Initializes the agent resource loader.
        
        Args:
            prompts_dir: Diretório de prompts.
            tools_dir: Diretório de ferramentas.
        """
        self.prompts: PromptLoader = PromptLoader(prompts_dir)
        self.tools: ToolsLoader = ToolsLoader(tools_dir)
        logger.info("AgentResourceLoader initialized")
    
    def reload_all(self) -> None:
        """Reloads all resources (prompts and tools)."""
        self.prompts.reload()
        self.tools.reload()
        logger.info("All resources reloaded")
    
    def info(self) -> Dict[str, Any]:
        """
        Gets information about loaded resources.
        
        Returns:
            Dictionary with statistics and lists of resources.
        """
        return {
            "prompts": {
                "available": self.prompts.list_prompts(),
                "cached": self.prompts.cache_size,
                "directory": str(self.prompts.prompts_dir)
            },
            "tools": {
                "available": self.tools.list_tools(),
                "cached": self.tools.cache_size,
                "directory": str(self.tools.tools_dir)
            }
        }
    
    def load_prompt(self, filename: str, use_cache: bool = True) -> str:
        """
        Loads a specific prompt.
        
        Args:
            filename: Name of the prompt file.
            use_cache: Whether to use cache.
            
        Returns:
            Prompt content.
        """
        return self.prompts.load(filename, use_cache)
    
    def load_tools(self, filename: str, use_cache: bool = True) -> Any:
        """
        Loads a specific tools file.
        
        Args:
            filename: Name of the tools file.
            use_cache: Whether to use cache.
            
        Returns:
            JSON content of the tools.
        """
        return self.tools.load(filename, use_cache)
    
    def format_prompt(self, filename: str, **kwargs) -> str:
        """
        Loads and formats a prompt with variables.
        
        Args:
            filename: Name of the prompt file.
            **kwargs: Variables for formatting.
            
        Returns:
            Formatted prompt.
        """
        return self.prompts.format(filename, **kwargs)
    
    @contextmanager
    def batch_load(self):
        """
        Context manager for batch loading.
        
        Useful for efficiently loading multiple resources.
        
        Example:
            >>> loader = AgentResourceLoader()
            >>> with loader.batch_load():
            ...     prompt1 = loader.load_prompt("prompt1.txt")
            ...     prompt2 = loader.load_prompt("prompt2.txt")
        """
        logger.debug("Iniciando carregamento em lote")
        try:
            yield self
        finally:
            logger.debug("Carregamento em lote concluído")
    
    def __repr__(self) -> str:
        """String representation of the loader."""
        return (
            f"AgentResourceLoader("
            f"prompts={self.prompts.cache_size}, "
            f"tools={self.tools.cache_size})"
        )


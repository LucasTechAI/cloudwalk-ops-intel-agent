from unittest import TestCase,TextTestResult, TestLoader, TestSuite, TextTestRunner
from logging import Logger, getLogger, basicConfig, INFO
from json import dump, JSONDecodeError
from unittest.mock import patch
from datetime import datetime
from tempfile import mkdtemp
from sys import path, exit
from shutil import rmtree
from pathlib import Path
from typing import Any

path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.utils.prompt_tool_loader import (
    PromptLoader,
    ToolsLoader,
    AgentResourceLoader,
    ResourceNotFoundError
)


basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: Logger = getLogger(__name__)


class TestPromptLoader(TestCase):
    """
    Test cases for the PromptLoader class.
    """
    def setUp(self) -> None:
        """Set up test environment"""
        self.test_dir: str = mkdtemp()
        self.prompts_dir: Path = Path(self.test_dir) / "agents" / "prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_prompt_file: Path = self.prompts_dir / "test_prompt.txt"
        self.test_prompt_content: str = "Hello {name}, welcome to {place}!"
        with open(self.test_prompt_file, "w", encoding="utf-8") as f:
            f.write(self.test_prompt_content)
        
        self.empty_file: Path = self.prompts_dir / "empty.txt"
        with open(self.empty_file, "w", encoding="utf-8") as f:
            f.write("")
        
        self.patcher: Any = patch('src.agents.utils.prompt_tool_loader.PATH_ROOT', Path(self.test_dir))
        self.patcher.start()
        
        self.loader: PromptLoader = PromptLoader()
    
    def tearDown(self) -> None:
        """Clean up test environment"""
        self.patcher.stop()
        rmtree(self.test_dir)
    
    def test_load_prompt_success(self) -> None:
        """Test successful prompt loading"""
        content: str = self.loader.load("test_prompt.txt")
        self.assertEqual(content, self.test_prompt_content)
    
    def test_load_prompt_not_found(self) -> None:
        """Test error when loading nonexistent prompt"""
        with self.assertRaises(ResourceNotFoundError):
            self.loader.load("nonexistent.txt")
    
    def test_load_prompt_cache(self) -> None:
        """Test cache functionality"""
        content1: str = self.loader.load("test_prompt.txt")
        self.assertEqual(self.loader.cache_size, 1)
        
        content2: str = self.loader.load("test_prompt.txt")
        self.assertEqual(content1, content2)
        self.assertEqual(self.loader.cache_size, 1)
    
    def test_load_without_cache(self) -> None:
        """Test loading without using cache"""
        self.loader.load("test_prompt.txt")
        
        new_content: str = "Modified content"
        with open(self.test_prompt_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        content: str = self.loader.load("test_prompt.txt", use_cache=False)
        self.assertEqual(content, new_content)
    
    def test_format_prompt(self) -> None:
        """Test prompt formatting with variables"""
        formatted: str = self.loader.format(
            "test_prompt.txt",
            name="Alice",
            place="Wonderland"
        )
        self.assertEqual(formatted, "Hello Alice, welcome to Wonderland!")
    
    def test_format_missing_variable(self) -> None:
        """Test error when formatting with missing variable"""
        with self.assertRaises(ValueError):
            self.loader.format("test_prompt.txt", name="Alice")
    
    def test_reload_specific_prompt(self) -> None:
        """Test reloading a specific prompt"""
        self.loader.load("test_prompt.txt")
        self.assertEqual(self.loader.cache_size, 1)
        
        self.loader.reload("test_prompt.txt")
        self.assertEqual(self.loader.cache_size, 0)
    
    def test_reload_all_prompts(self) -> None:
        """Test reloading all prompts"""
        self.loader.load("test_prompt.txt")
        self.loader.load("empty.txt")
        self.assertEqual(self.loader.cache_size, 2)
        
        self.loader.reload()
        self.assertEqual(self.loader.cache_size, 0)
    
    def test_list_prompts(self) -> None:
        """Test listing available prompts"""
        prompts: list[str] = self.loader.list_prompts()
        self.assertIn("test_prompt.txt", prompts)
        self.assertIn("empty.txt", prompts)
        self.assertEqual(len(prompts), 2)
    
    def test_exists(self) -> None:
        """Test existence check for prompts"""
        self.assertTrue(self.loader.exists("test_prompt.txt"))
        self.assertFalse(self.loader.exists("nonexistent.txt"))
    
    def test_empty_prompt_warning(self) -> None:
        """Test warning when loading empty prompt"""
        content: str = self.loader.load("empty.txt")
        self.assertEqual(content, "")


class TestToolsLoader(TestCase):
    """Tests for the ToolsLoader class"""
    
    def setUp(self) -> None:
        """Set up test environment"""
        self.test_dir: str = mkdtemp()
        self.tools_dir: Path = Path(self.test_dir) / "agents" / "tools"
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_tools_list: list[dict[str, object]] = [
            {
                "name": "search_tool",
                "description": "Search for information",
                "parameters": {"query": "string"}
            },
            {
                "name": "calc_tool",
                "description": "Calculate numbers",
                "parameters": {"expression": "string"}
            }
        ]
        self.test_tools_file: Path = self.tools_dir / "test_tools.json"
        with open(self.test_tools_file, "w", encoding="utf-8") as f:
            dump(self.test_tools_list, f)
        
        self.test_tools_dict: dict[str, dict[str, str]] = {
            "search": {"description": "Search tool"},
            "calc": {"description": "Calculator tool"}
        }
        self.test_tools_dict_file: Path = self.tools_dir / "tools_dict.json"
        with open(self.test_tools_dict_file, "w", encoding="utf-8") as f:
            dump(self.test_tools_dict, f)
        
        self.invalid_json_file: Path = self.tools_dir / "invalid.json"
        with open(self.invalid_json_file, "w", encoding="utf-8") as f:
            f.write("{invalid json")
        
        self.patcher: Any = patch('src.agents.utils.prompt_tool_loader.PATH_ROOT', Path(self.test_dir))
        self.patcher.start()
        
        self.loader: ToolsLoader = ToolsLoader()
    
    def tearDown(self) -> None:
        """Clean up test environment"""
        self.patcher.stop()
        rmtree(self.test_dir)
    
    def test_load_tools_success(self) -> None:
        """Test successful loading of tools"""
        tools: list[dict[str, object]] = self.loader.load("test_tools.json")
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0]["name"], "search_tool")
    
    def test_load_tools_not_found(self) -> None:
        """Test error when loading nonexistent tools"""
        with self.assertRaises(ResourceNotFoundError):
            self.loader.load("nonexistent.json")
    
    def test_load_invalid_json(self) -> None:
        """Test error when loading invalid JSON"""
        with self.assertRaises(JSONDecodeError):
            self.loader.load("invalid.json")
    
    def test_load_tools_cache(self) -> None:
        """Test cache functionality"""
        tools1: list[dict[str, object]] = self.loader.load("test_tools.json")
        self.assertEqual(self.loader.cache_size, 1)
        
        tools2: list[dict[str, object]] = self.loader.load("test_tools.json")
        self.assertEqual(tools1, tools2)
        self.assertEqual(self.loader.cache_size, 1)
    
    def test_get_tool_from_list(self) -> None:
        """Test getting specific tool from list"""
        tool: dict[str, object] | None = self.loader.get_tool("test_tools.json", "search_tool")
        self.assertIsNotNone(tool)
        self.assertEqual(tool["name"], "search_tool")
    
    def test_get_tool_from_dict(self) -> None:
        """Test getting specific tool from dictionary"""
        tool: dict[str, object] | None = self.loader.get_tool("tools_dict.json", "search")
        self.assertIsNotNone(tool)
        self.assertEqual(tool["description"], "Search tool")
    
    def test_get_nonexistent_tool(self) -> None:
        """Test getting nonexistent tool"""
        tool: dict[str, object] | None = self.loader.get_tool("test_tools.json", "nonexistent")
        self.assertIsNone(tool)
    
    def test_reload_specific_tools(self) -> None:
        """Test reloading specific tools"""
        self.loader.load("test_tools.json")
        self.assertEqual(self.loader.cache_size, 1)
        
        self.loader.reload("test_tools.json")
        self.assertEqual(self.loader.cache_size, 0)
    
    def test_reload_all_tools(self) -> None:
        """Test reloading all tools"""
        self.loader.load("test_tools.json")
        self.loader.load("tools_dict.json")
        self.assertEqual(self.loader.cache_size, 2)
        
        self.loader.reload()
        self.assertEqual(self.loader.cache_size, 0)
    
    def test_list_tools(self) -> None:
        """Test listing available tools"""
        tools = self.loader.list_tools()
        self.assertIn("test_tools.json", tools)
        self.assertIn("tools_dict.json", tools)
        self.assertIn("invalid.json", tools)
    
    def test_exists(self) -> None:
        """Test checking existence of tools"""
        self.assertTrue(self.loader.exists("test_tools.json"))
        self.assertFalse(self.loader.exists("nonexistent.json"))


class TestAgentResourceLoader(TestCase):
    """Tests for the AgentResourceLoader class"""
    
    def setUp(self) -> None:
        """Set up test environment"""
        self.test_dir: str = mkdtemp()
        self.prompts_dir: Path = Path(self.test_dir) / "agents" / "prompts"
        self.tools_dir: Path = Path(self.test_dir) / "agents" / "tools"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_prompt: Path = self.prompts_dir / "test.txt"
        with open(self.test_prompt, "w", encoding="utf-8") as f:
            f.write("Test prompt")
        
        self.test_tools: Path = self.tools_dir / "test.json"
        with open(self.test_tools, "w", encoding="utf-8") as f:
            dump([{"name": "test_tool"}], f)
        
        self.patcher: Any = patch('src.agents.utils.prompt_tool_loader.PATH_ROOT', Path(self.test_dir))
        self.patcher.start()
        
        self.loader = AgentResourceLoader()
    
    def tearDown(self) -> None:
        """Clean up test environment"""
        self.patcher.stop()
        rmtree(self.test_dir)
    
    def test_load_prompt(self) -> None:
        """Test loading prompt via AgentResourceLoader"""
        prompt: str = self.loader.load_prompt("test.txt")
        self.assertEqual(prompt, "Test prompt")
    
    def test_load_tools(self) -> None:
        """Test loading tools via AgentResourceLoader"""
        tools: list[dict[str, object]] = self.loader.load_tools("test.json")
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "test_tool")
    
    def test_format_prompt(self) -> None:
        """Test formatting prompt via AgentResourceLoader"""
        formatted_prompt: Path = self.prompts_dir / "formatted.txt"
        with open(formatted_prompt, "w", encoding="utf-8") as f:
            f.write("Hello {name}!")
        
        result: str = self.loader.format_prompt("formatted.txt", name="World")
        self.assertEqual(result, "Hello World!")
    
    def test_reload_all(self) -> None:
        """Test reloading all resources"""
        self.loader.load_prompt("test.txt")
        self.loader.load_tools("test.json")
        
        self.assertEqual(self.loader.prompts.cache_size, 1)
        self.assertEqual(self.loader.tools.cache_size, 1)
        
        self.loader.reload_all()
        
        self.assertEqual(self.loader.prompts.cache_size, 0)
        self.assertEqual(self.loader.tools.cache_size, 0)
    
    def test_info(self) -> None:
        """Test info method"""
        info: dict[str, dict[str, object]] = self.loader.info()
        
        self.assertIn("prompts", info)
        self.assertIn("tools", info)
        self.assertIn("available", info["prompts"])
        self.assertIn("cached", info["prompts"])
        self.assertIn("directory", info["prompts"])
        self.assertIn("test.txt", info["prompts"]["available"])
        self.assertIn("test.json", info["tools"]["available"])
    
    def test_batch_load_context_manager(self) -> None:
        """Test batch load context manager"""
        with self.loader.batch_load() as loader:
            prompt: str = loader.load_prompt("test.txt")
            tools: list[dict[str, object]] = loader.load_tools("test.json")
            
            self.assertEqual(prompt, "Test prompt")
            self.assertEqual(len(tools), 1)
    
    def test_repr(self) -> None:
        """Test string representation of the loader"""
        self.loader.load_prompt("test.txt")
        self.loader.load_tools("test.json")
        
        repr_str: str = repr(self.loader)
        self.assertIn("AgentResourceLoader", repr_str)
        self.assertIn("prompts=1", repr_str)
        self.assertIn("tools=1", repr_str)


class TestIntegration(TestCase):
    """Integration tests for AgentResourceLoader"""
    
    def setUp(self) -> None:
        """Set up test environment"""
        self.test_dir: str = mkdtemp()
        self.prompts_dir: Path = Path(self.test_dir) / "prompts"
        self.tools_dir: Path = Path(self.test_dir) / "tools"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self) -> None:
        """Clean up test environment"""
        rmtree(self.test_dir)
    
    def test_full_workflow(self) -> None:
        """Test full usage workflow"""
        prompt_file: Path = self.prompts_dir / "workflow.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write("Agent: {agent_name}, Task: {task}")
        
        tools_file: Path = self.tools_dir / "workflow.json"
        with open(tools_file, "w", encoding="utf-8") as f:
            dump([
                {"name": "tool1", "description": "First tool"},
                {"name": "tool2", "description": "Second tool"}
            ], f)
        
        loader: AgentResourceLoader = AgentResourceLoader(
            prompts_dir=self.prompts_dir,
            tools_dir=self.tools_dir
        )
        
        prompt: str = loader.format_prompt(
            "workflow.txt",
            agent_name="TestAgent",
            task="analyze data"
        )
        self.assertEqual(prompt, "Agent: TestAgent, Task: analyze data")
        
        tools: list[dict[str, object]] = loader.load_tools("workflow.json")
        self.assertEqual(len(tools), 2)
        
        info: dict[str, dict[str, object]] = loader.info()
        self.assertEqual(info["prompts"]["cached"], 1)
        self.assertEqual(info["tools"]["cached"], 1)


class TestResultCollector(TextTestResult):
    """Custom test result collector with detailed reporting"""
    
    def __init__(self, *args, **kwargs) -> None:
        """Initializes the test result collector"""
        super().__init__(*args, **kwargs)
        self.test_results = []
    
    def addSuccess(self, test) -> None:
        """Records a successful test"""
        super().addSuccess(test)
        self.test_results.append({
            'test': test.id(),
            'status': '✓ PASS',
            'message': ''
        })
    
    def addError(self, test, err):
        """Records a test that resulted in an error"""
        super().addError(test, err)
        self.test_results.append({
            'test': test.id(),
            'status': '✗ ERROR',
            'message': str(err[1])
        })
    
    def addFailure(self, test, err):
        """Records a failed test"""
        super().addFailure(test, err)
        self.test_results.append({
            'test': test.id(),
            'status': '✗ FAIL',
            'message': str(err[1])
        })
    
    def addSkip(self, test, reason):
        """Records a skipped test"""
        super().addSkip(test, reason)
        self.test_results.append({
            'test': test.id(),
            'status': '⊘ SKIP',
            'message': reason
        })


def print_test_report(result) -> None:
    """Prints a detailed test report"""
    logger.info("\n" + "="*80)
    logger.info("TEST REPORT")
    logger.info("="*80)
    logger.info(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors) - len(result.skipped)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    
    logger.info(f"\n📊 GENERAL STATISTICS:")
    logger.info(f"   Tests Total: {total}")
    logger.info(f"   ✓ Success : {passed} ({passed/total*100:.1f}%)")
    logger.info(f"   ✗ Fail: {failed} ({failed/total*100:.1f}%)")
    logger.info(f"   ✗ Error: {errors} ({errors/total*100:.1f}%)")
    logger.info(f"   ⊘ Ignore: {skipped} ({skipped/total*100:.1f}%)")
    
    results_by_class = {}
    for test_result in result.test_results:
        test_id = test_result['test']
        class_name = '.'.join(test_id.split('.')[:-1])
        test_name = test_id.split('.')[-1]
        
        if class_name not in results_by_class:
            results_by_class[class_name] = []
        
        results_by_class[class_name].append({
            'name': test_name,
            'status': test_result['status'],
            'message': test_result['message']
        })
    
        
    logger.info("\n" + "="*80)
    logger.info("DETAILED RESULTS BY TEST CLASS")
    logger.info("="*80)
    
    for class_name, tests in sorted(results_by_class.items()):
        class_total = len(tests)
        class_passed = sum(1 for t in tests if '✓' in t['status'])
        
        logger.info(f"\n📦 {class_name}")
        logger.info(f"   Tests: {class_total} | Successes: {class_passed}/{class_total}")
        logger.info("   " + "-"*76)
        
        for test in tests:
            status_icon = test['status'].split()[0]
            logger.info(f"   {status_icon} {test['name']}")
            if test['message']:
                msg = test['message'][:100] + "..." if len(test['message']) > 100 else test['message']
                logger.info(f"      └─ {msg}")
    
    logger.info("\n" + "="*80)
    logger.info("FINAL SUMMARY")
    logger.info("="*80)
    
    if result.wasSuccessful():
        logger.info("✓ All tests passed successfully!")
    else:
        logger.info(f" {failed + errors} tests failed or had errors.")
    
    logger.info("="*80 + "\n")


def run_tests() -> TestResultCollector:
    """Runs all test cases and prints a detailed report"""
    loader = TestLoader()
    suite = TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestPromptLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestToolsLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentResourceLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = TextTestRunner(resultclass=TestResultCollector, verbosity=2)
    result = runner.run(suite)
    
    print_test_report(result)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    exit(0 if result.wasSuccessful() else 1)
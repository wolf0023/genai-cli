import logging

from genai_cli.command.handler import CommandHandler
from genai_cli.command.base import BaseCommand
from genai_cli.command.registry import CommandRegistry

class MockSubCommand1(BaseCommand):
    name = "test1"
    description = "A mock subcommand for testing."
    usage = "mock test test1 [arg]"
    subcommands = {}
    def execute(self, argc: int, argv: list[str]) -> str:
        return f"Mock subcommand 1 executed with args: {argv}"
    def _register_all_subcommands(self):
        pass

class MockSubCommand2(BaseCommand):
    name = "test2"
    description = "A mock subcommand for testing."
    usage = "mock test test2 [arg]"
    subcommands = {}
    def execute(self, argc: int, argv: list[str]) -> str:
        return f"Mock subcommand 2 executed with args: {argv}"
    def _register_all_subcommands(self):
        pass

class MockSubCommand(BaseCommand):
    name = "test"
    description = "A mock subcommand for testing."
    usage = "mock test [arg]"
    def __init__(self):
        super().__init__()

    def execute(self, argc: int, argv: list[str]) -> str:
        return f"Mock subcommand executed with args: {argv}"

    def _register_all_subcommands(self):
        try:
            self.register_subcommand(MockSubCommand1())
            self.register_subcommand(MockSubCommand2())
        except ValueError as e:
            raise

class MockDebugSubCommand(BaseCommand):
    name = "debug"
    description = "A mock debug subcommand for testing."
    usage = "mock debug [arg]"
    def __init__(self):
        super().__init__()

    def execute(self, argc: int, argv: list[str]) -> str:
        return f"Mock debug subcommand executed with args: {argv}"

    def _register_all_subcommands(self):
        try:
            self.register_subcommand(MockSubCommand1())
            self.register_subcommand(MockSubCommand2())
        except ValueError as e:
            raise

class MockCommand(BaseCommand):
    name = "mock"
    description = "A mock command for testing."
    usage = "mock [test|debug] [test1|test2] [arg]"
    def __init__(self):
        super().__init__()

    def execute(self, argc: int, argv: list[str]) -> str:
        return f"Mock command executed with args: {argv}"

    def _register_all_subcommands(self):
        try:
            self.register_subcommand(MockSubCommand())
            self.register_subcommand(MockDebugSubCommand())

        except ValueError as e:
            raise

class MockCommandRegistry(CommandRegistry):
    def __init__(self, logger: logging.Logger):
        super().__init__(logger)

class MockCommandHandler(CommandHandler):
    def __init__(self, logger: logging.Logger, command_registry: CommandRegistry):
        super().__init__(logger, command_registry)

def test_command_handler():
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    registry = MockCommandRegistry(logger)
    registry.register(MockCommand())

    handler = MockCommandHandler(logger, registry)

    test_command: str = "/mock debug test2 arg1"
    test_command1: str = "/mock test test1 arg1"

    # Test is_command
    assert handler.is_command("/mock") == True

    # Test parse_command
    argc, argv = handler.parse_command(test_command)
    assert argc == 4
    assert argv == ["mock", "debug", "test2", "arg1"]

    # Test execute_command
    result = handler.handle_command(argc, argv)
    logger.debug(f"Result of executing command: {result}")

    # Test parse_command for another command
    argc1, argv1 = handler.parse_command(test_command1)
    assert argc1 == 4
    assert argv1 == ["mock", "test", "test1", "arg1"]

    # Test execute_command for another command
    result1 = handler.handle_command(argc1, argv1)
    logger.debug(f"Result of executing command: {result1}")


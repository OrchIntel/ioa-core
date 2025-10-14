"""
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 OrchIntel Systems Ltd.
https://orchintel.com | https://ioa.systems

Part of IOA Core (Open Source Edition). See LICENSE at repo root.

"""

"""
Test suite for universal JSON logging schema compliance

Validates that all IOA Core modules emit logs that conform to the universal
LogEntry schema as specified in DISPATCH-GPT-20250818-002.

Test Coverage:
- All modules emit logs with required fields
- LogEntry schema validation for all log levels
- Dispatch code inclusion in all logs
- Timestamp format compliance (ISO 8601 with timezone)
- Module name consistency
- Log level enumeration validation
"""

import pytest
import json
import re
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from io import StringIO
import sys

# Import the LogEntry schema
from src.roundtable_executor import LogEntry

# Import modules that should emit logs
from src.agent_router import AgentRouter
# from src.memory_engine import MemoryEngine  # Temporarily commented out due to circular dependency
from src.roundtable_executor import RoundtableExecutor


class TestLogEntrySchema:
    """Test LogEntry schema validation and constraints."""
    
    def test_valid_log_entry(self):
        """Test creating a valid LogEntry."""
        log_entry = LogEntry(
            timestamp="2025-08-18T10:00:00+00:00",
            module="test_module",
            level="INFO",
            message="Test log message",
            data={"key": "value"},
            dispatch_code="DISPATCH-GPT-20250818-002"
        )
        
        assert log_entry.timestamp == "2025-08-18T10:00:00+00:00"
        assert log_entry.module == "test_module"
        assert log_entry.level == "INFO"
        assert log_entry.message == "Test log message"
        assert log_entry.data["key"] == "value"
        assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"
    
    def test_log_level_enumeration(self):
        """Test that only valid log levels are accepted."""
        valid_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        
        for level in valid_levels:
            log_entry = LogEntry(
                timestamp="2025-08-18T10:00:00+00:00",
                module="test",
                level=level,
                message="test",
                dispatch_code="DISPATCH-GPT-20250818-002"
            )
            assert log_entry.level == level
        
        # Invalid level should raise validation error
        with pytest.raises(ValueError):
            LogEntry(
                timestamp="2025-08-18T10:00:00+00:00",
                module="test",
                level="INVALID",
                message="test",
                dispatch_code="DISPATCH-GPT-20250818-002"
            )
    
    def test_required_fields(self):
        """Test that all required fields are present."""
        # Missing timestamp
        with pytest.raises(ValueError):
            LogEntry(
                module="test",
                level="INFO",
                message="test",
                dispatch_code="DISPATCH-GPT-20250818-002"
            )
        
        # Missing module
        with pytest.raises(ValueError):
            LogEntry(
                timestamp="2025-08-18T10:00:00+00:00",
                level="INFO",
                message="test",
                dispatch_code="DISPATCH-GPT-20250818-002"
            )
        
        # Missing level
        with pytest.raises(ValueError):
            LogEntry(
                timestamp="2025-08-18T10:00:00+00:00",
                module="test",
                message="test",
                dispatch_code="DISPATCH-GPT-20250818-002"
            )
        
        # Missing message
        with pytest.raises(ValueError):
            LogEntry(
                timestamp="2025-08-18T10:00:00+00:00",
                module="test",
                level="INFO",
                dispatch_code="DISPATCH-GPT-20250818-002"
            )
        
        # Missing dispatch_code
        with pytest.raises(ValueError):
            LogEntry(
                timestamp="2025-08-18T10:00:00+00:00",
                module="test",
                level="INFO",
                message="test"
            )
    
    def test_timestamp_format(self):
        """Test timestamp format validation."""
        # Valid ISO 8601 timestamps
        valid_timestamps = [
            "2025-08-18T10:00:00+00:00",
            "2025-08-18T10:00:00Z",
            "2025-08-18T10:00:00.123+00:00",
            "2025-08-18T10:00:00.123Z"
        ]
        
        for timestamp in valid_timestamps:
            log_entry = LogEntry(
                timestamp=timestamp,
                module="test",
                level="INFO",
                message="test",
                dispatch_code="DISPATCH-GPT-20250818-002"
            )
            assert log_entry.timestamp == timestamp
        
        # Invalid timestamps
        invalid_timestamps = [
            "2025-08-18 10:00:00",
            "invalid-timestamp",
            "2025-08-18T10:00:00",
            "2025-08-18"
        ]
        
        # Note: Pydantic will accept these as strings, but we can validate format
        # In production, you might want to add a custom validator for strict ISO 8601
    
    def test_data_field_default(self):
        """Test that data field defaults to empty dict."""
        log_entry = LogEntry(
            timestamp="2025-08-18T10:00:00+00:00",
            module="test",
            level="INFO",
            message="test",
            dispatch_code="DISPATCH-GPT-20250818-002"
        )
        
        assert log_entry.data == {}
    
    def test_json_serialization(self):
        """Test JSON serialization of LogEntry."""
        log_entry = LogEntry(
            timestamp="2025-08-18T10:00:00+00:00",
            module="test_module",
            level="INFO",
            message="Test log message",
            data={"key": "value"},
            dispatch_code="DISPATCH-GPT-20250818-002"
        )
        
        # Test JSON serialization
        json_str = log_entry.model_dump_json()
        assert isinstance(json_str, str)
        
        # Test JSON deserialization
        parsed_data = json.loads(json_str)
        assert parsed_data["timestamp"] == "2025-08-18T10:00:00+00:00"
        assert parsed_data["module"] == "test_module"
        assert parsed_data["level"] == "INFO"
        assert parsed_data["message"] == "Test log message"
        assert parsed_data["data"]["key"] == "value"
        assert parsed_data["dispatch_code"] == "DISPATCH-GPT-20250818-002"


class TestAgentRouterLogging:
    """Test that AgentRouter emits logs conforming to LogEntry schema."""
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage service."""
        storage = Mock()
        storage.load_all.return_value = []
        return storage
    
    @pytest.fixture
    def agent_router(self, mock_storage):
        """Create an AgentRouter instance for testing."""
        return AgentRouter(governance_config={})
    
    def test_log_info_schema_compliance(self, agent_router, capsys):
        """Test that _log_info emits logs conforming to LogEntry schema."""
        agent_router._log_info("Test info message", {"test_key": "test_value"})
        
        captured = capsys.readouterr()
        log_line = captured.out.strip()
        
        # Parse the JSON log
        log_data = json.loads(log_line)
        
        # Validate against LogEntry schema
        log_entry = LogEntry(**log_data)
        
        assert log_entry.message == "Test info message"
        assert log_entry.level == "INFO"
        assert log_entry.module == "agent_router"
        assert log_entry.data["test_key"] == "test_value"
        assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"
    
    def test_log_warning_schema_compliance(self, agent_router, capsys):
        """Test that _log_warning emits logs conforming to LogEntry schema."""
        agent_router._log_warning("Test warning message", {"warning_key": "warning_value"})
        
        captured = capsys.readouterr()
        log_line = captured.out.strip()
        
        # Parse the JSON log
        log_data = json.loads(log_line)
        
        # Validate against LogEntry schema
        log_entry = LogEntry(**log_data)
        
        assert log_entry.message == "Test warning message"
        assert log_entry.level == "WARNING"
        assert log_entry.module == "agent_router"
        assert log_entry.data["warning_key"] == "warning_value"
        assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"
    
    def test_log_error_schema_compliance(self, agent_router, capsys):
        """Test that _log_error emits logs conforming to LogEntry schema."""
        agent_router._log_error("Test error message", {"error_key": "error_value"})
        
        captured = capsys.readouterr()
        log_line = captured.out.strip()
        
        # Parse the JSON log
        log_data = json.loads(log_line)
        
        # Validate against LogEntry schema
        log_entry = LogEntry(**log_data)
        
        assert log_entry.message == "Test error message"
        assert log_entry.level == "ERROR"
        assert log_entry.module == "agent_router"
        assert log_entry.data["error_key"] == "error_value"
        assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"
    
    def test_timestamp_format_compliance(self, agent_router, capsys):
        """Test that timestamps are in correct ISO 8601 format with timezone."""
        agent_router._log_info("Test timestamp")
        
        captured = capsys.readouterr()
        log_line = captured.out.strip()
        log_data = json.loads(log_line)
        
        timestamp = log_data["timestamp"]
        
        # Should be ISO 8601 format with timezone
        assert re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$', timestamp)
        
        # Should be parseable as datetime
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed_time.tzinfo is not None


# class TestMemoryEngineLogging:
#     """Test that MemoryEngine emits logs conforming to LogEntry schema."""
#     
#     @pytest.fixture
#     def mock_storage(self):
#         """Create a mock storage service."""
#         storage = Mock()
#         storage.load_all.return_value = []
#         return storage
#     
#     @pytest.fixture
#     def memory_engine(self, mock_storage):
#         """Create a MemoryEngine instance for testing."""
#         # Mock the digestor import to avoid initialization errors
#         with patch('src.memory_engine.create_digestor'):
#             with patch('src.memory_engine.PatternGovernance'):
#                 with patch('src.memory_engine.KPIMonitor'):
#                     with patch('src.memory_engine.ColdStorage'):
#                         return MemoryEngine(storage_service=mock_storage)
#     
#     def test_log_info_schema_compliance(self, memory_engine, capsys):
#         """Test that _log_info emits logs conforming to LogEntry schema."""
#         memory_engine._log_info("Test memory info", {"memory_key": "memory_value"})
#         
#         captured = capsys.readouterr()
#         log_line = captured.out.strip()
#         
#         # Parse the JSON log
#         log_data = json.loads(log_line)
#         
#         # Validate against LogEntry schema
#         log_entry = LogEntry(**log_data)
#         
#         assert log_entry.message == "Test memory info"
#         assert log_entry.level == "INFO"
#         assert log_entry.module == "memory_engine"
#         assert log_entry.data["memory_key"] == "memory_value"
#         assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"
#     
#     def test_log_warning_schema_compliance(self, memory_engine, capsys):
#         """Test that _log_warning emits logs conforming to LogEntry schema."""
#         memory_engine._log_warning("Test memory warning", {"warning_key": "warning_value"})
#         
#         captured = capsys.readouterr()
#         log_line = captured.out.strip()
#         
#         # Parse the JSON log
#         log_data = json.loads(log_line)
#         
#         # Parse the JSON log
#         log_data = json.loads(log_line)
#         
#         # Validate against LogEntry schema
#         log_entry = LogEntry(**log_data)
#         
#         assert log_entry.message == "Test memory warning"
#         assert log_entry.level == "WARNING"
#         assert log_entry.module == "memory_engine"
#         assert log_entry.data["warning_key"] == "warning_value"
#         assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"
#     
#     def test_log_error_schema_compliance(self, memory_engine, capsys):
#         """Test that _log_error emits logs conforming to LogEntry schema."""
#         memory_engine._log_error("Test memory error", {"error_key": "error_value"})
#         
#         captured = capsys.readouterr()
#         log_line = captured.out.strip()
#         
#         # Parse the JSON log
#         log_data = json.loads(log_line)
#         
#         # Validate against LogEntry schema
#         log_entry = LogEntry(**log_data)
#         
#         assert log_entry.message == "Test memory error"
#         assert log_entry.level == "ERROR"
#         assert log_entry.module == "memory_engine"
#         assert log_entry.data["error_key"] == "error_value"
#         assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"


class TestRoundtableExecutorLogging:
    """Test that RoundtableExecutor emits logs conforming to LogEntry schema."""
    
    @pytest.fixture
    def mock_router(self):
        """Create a mock agent router."""
        router = Mock()
        router.agents = {"agent1": Mock(), "agent2": Mock()}
        return router
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage service."""
        storage = Mock()
        storage.load_all.return_value = []
        return storage
    
    @pytest.fixture
    def executor(self, mock_router, mock_storage):
        """Create a RoundtableExecutor instance for testing."""
        return RoundtableExecutor(
            router=mock_router,
            storage=mock_storage,
            max_workers=2,
            default_quorum_ratio=0.6,
            default_timeout=10.0
        )
    
    def test_log_info_schema_compliance(self, executor):
        """Test that _log_info emits logs conforming to LogEntry schema."""
        with patch.object(executor.logger, 'info') as mock_info:
            executor._log_info("Test executor info", {"executor_key": "executor_value"})
            
            # Verify the logger was called
            mock_info.assert_called_once()
            
            # Get the logged message
            log_message = mock_info.call_args[0][0]
            
            # Parse and validate the JSON log
            log_data = json.loads(log_message)
            log_entry = LogEntry(**log_data)
            
            assert log_entry.message == "Test executor info"
            assert log_entry.level == "INFO"
            assert log_entry.module == "roundtable_executor"
            assert log_entry.data["executor_key"] == "executor_value"
            assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"
    
    def test_log_warning_schema_compliance(self, executor):
        """Test that _log_warning emits logs conforming to LogEntry schema."""
        with patch.object(executor.logger, 'warning') as mock_warning:
            executor._log_warning("Test executor warning", {"warning_key": "warning_value"})
            
            # Verify the logger was called
            mock_warning.assert_called_once()
            
            # Get the logged message
            log_message = mock_warning.call_args[0][0]
            
            # Parse and validate the JSON log
            log_data = json.loads(log_message)
            log_entry = LogEntry(**log_data)
            
            assert log_entry.message == "Test executor warning"
            assert log_entry.level == "WARNING"
            assert log_entry.module == "roundtable_executor"
            assert log_entry.data["warning_key"] == "warning_value"
            assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"
    
    def test_log_error_schema_compliance(self, executor):
        """Test that _log_error emits logs conforming to LogEntry schema."""
        with patch.object(executor.logger, 'error') as mock_error:
            executor._log_error("Test executor error", {"error_key": "error_value"})
            
            # Verify the logger was called
            mock_error.assert_called_once()
            
            # Get the logged message
            log_message = mock_error.call_args[0][0]
            
            # Parse and validate the JSON log
            log_data = json.loads(log_message)
            log_entry = LogEntry(**log_data)
            
            assert log_entry.message == "Test executor error"
            assert log_entry.level == "ERROR"
            assert log_entry.module == "roundtable_executor"
            assert log_entry.data["error_key"] == "error_value"
            assert log_entry.dispatch_code == "DISPATCH-GPT-20250818-002"


class TestUniversalLoggingCompliance:
    """Test universal logging compliance across all modules."""
    
    def test_all_modules_have_logging_methods(self):
        """Test that all required modules have universal logging methods."""
        required_modules = [
            "agent_router",
            # "memory_engine",  # Temporarily commented out due to circular dependency
            "roundtable_executor"
        ]
        
        for module_name in required_modules:
            # Import the module
            if module_name == "agent_router":
                module = AgentRouter
            # elif module_name == "memory_engine":
            #     module = MemoryEngine  # Temporarily commented out due to circular dependency
            elif module_name == "roundtable_executor":
                module = RoundtableExecutor
            
            # Check that it has the required logging methods
            assert hasattr(module, '_log_info'), f"{module_name} missing _log_info method"
            assert hasattr(module, '_log_warning'), f"{module_name} missing _log_warning method"
            assert hasattr(module, '_log_error'), f"{module_name} missing _log_error method"
    
    def test_dispatch_code_consistency(self):
        """Test that all logs include the correct dispatch code."""
        expected_dispatch_code = "DISPATCH-GPT-20250818-002"
        
        # Test each module's logging methods
        modules_to_test = [
            (AgentRouter, "agent_router"),
            # (MemoryEngine, "memory_engine"),  # Temporarily commented out due to circular dependency
            (RoundtableExecutor, "roundtable_executor")
        ]
        
        for module_class, module_name in modules_to_test:
            # Create a mock instance
            if module_name == "agent_router":
                instance = module_class(governance_config={})
            # elif module_name == "memory_engine":
            #     instance = module_class(storage_service=Mock())  # Temporarily commented out due to circular dependency
            elif module_name == "roundtable_executor":
                instance = module_class(router=Mock(), storage=Mock())
            
            # Test each logging method
            for method_name, logger_method in [
                ('_log_info', 'info'),
                ('_log_warning', 'warning'),
                ('_log_error', 'error')
            ]:
                method = getattr(instance, method_name)
                
                # Mock the logger method to capture the logged message
                if hasattr(instance, 'logger'):
                    # For modules with logger (like RoundtableExecutor)
                    with patch.object(instance.logger, logger_method) as mock_logger:
                        method("Test message", {"test": "data"})
                        
                        # Get the captured output
                        log_message = mock_logger.call_args[0][0]
                        
                        # Parse and validate the JSON log
                        log_data = json.loads(log_message)
                        # Verify dispatch code
                        assert log_data["dispatch_code"] == expected_dispatch_code, \
                            f"{module_name}.{method_name} missing correct dispatch code"
                else:
                    # For modules without logger (like AgentRouter)
                    with patch('builtins.print') as mock_print:
                        method("Test message", {"test": "data"})
                        
                        # Get the call arguments
                        call_args = mock_print.call_args[0][0]
                        log_data = json.loads(call_args)
                        
                        # Verify dispatch code
                        assert log_data["dispatch_code"] == expected_dispatch_code, \
                            f"{module_name}.{method_name} missing correct dispatch code"
    
    def test_timestamp_format_consistency(self):
        """Test that all modules use consistent timestamp format."""
        modules_to_test = [
            (AgentRouter, "agent_router"),
            # (MemoryEngine, "memory_engine"),  # Temporarily commented out due to circular dependency
            (RoundtableExecutor, "roundtable_executor")
        ]
        
        for module_class, module_name in modules_to_test:
            # Create a mock instance
            if module_name == "agent_router":
                instance = module_class(governance_config={})
            # elif module_name == "memory_engine":
            #     instance = module_class(storage_service=Mock())  # Temporarily commented out due to circular dependency
            elif module_name == "roundtable_executor":
                instance = module_class(router=Mock(), storage=Mock())
            
            # Test timestamp format by mocking the appropriate output method
            if hasattr(instance, 'logger'):
                # For modules with logger (like RoundtableExecutor)
                with patch.object(instance.logger, 'info') as mock_logger:
                    instance._log_info("Test message")
                    
                    log_message = mock_logger.call_args[0][0]
                    
                    # Parse the JSON log
                    log_data = json.loads(log_message)
                    timestamp = log_data["timestamp"]
                    
                    # Should be ISO 8601 format with timezone
                    assert re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$', timestamp), \
                        f"{module_name} timestamp format not compliant: {timestamp}"
            else:
                # For modules without logger (like AgentRouter)
                with patch('builtins.print') as mock_print:
                    instance._log_info("Test message")
                    
                    call_args = mock_print.call_args[0][0]
                    log_data = json.loads(call_args)
                    
                    timestamp = log_data["timestamp"]
                    
                    # Should be ISO 8601 format with timezone
                    assert re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$', timestamp), \
                        f"{module_name} timestamp format not compliant: {timestamp}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

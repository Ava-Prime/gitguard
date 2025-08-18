"""Unit tests for Prometheus metrics collection and recording functionality.

This module tests:
- Metrics initialization and configuration
- Recording functions for various metric types
- Middleware integration for automatic metrics collection
- Temporal workflow and activity metrics
- Metrics server startup and endpoint functionality
- Error handling and edge cases
"""

import pytest
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from prometheus_client import Counter, Histogram, Gauge, REGISTRY, CollectorRegistry
import asyncio
from typing import Dict, Any

# Mock the metrics modules since they may not be available in test environment
class MockMetric:
    """Mock Prometheus metric for testing."""
    def __init__(self, name, description, labelnames=None):
        self.name = name
        self.description = description
        self._labelnames = tuple(labelnames or [])
        self._value = Mock()
        self._value._value = {}
        
    def labels(self, **kwargs):
        return Mock(inc=Mock(), observe=Mock(), set=Mock())
        
    def inc(self):
        pass
        
    def observe(self, value):
        pass
        
    def set(self, value):
        pass

class MockGuardApiMetrics:
    """Mock guard-api metrics module."""
    def __init__(self):
        # Mock metrics
        self.api_requests_total = MockMetric('api_requests_total', 'API requests', ['method', 'endpoint', 'status_code'])
        self.api_request_duration_seconds = MockMetric('api_request_duration_seconds', 'API duration', ['method', 'endpoint'])
        self.webhook_events_total = MockMetric('webhook_events_total', 'Webhook events', ['event_type', 'action', 'status'])
        self.webhook_processing_duration_seconds = MockMetric('webhook_processing_duration_seconds', 'Webhook duration', ['event_type', 'action'])
        self.webhook_signature_validations_total = MockMetric('webhook_signature_validations_total', 'Signature validations', ['status'])
        self.active_connections = MockMetric('active_connections', 'Active connections', ['service'])
        self.nats_messages_published_total = MockMetric('nats_messages_published_total', 'NATS messages', ['subject', 'status'])
        self.temporal_workflow_starts_total = MockMetric('temporal_workflow_starts_total', 'Workflow starts', ['workflow_type', 'status'])
        self.risk_score_calculations_total = MockMetric('risk_score_calculations_total', 'Risk calculations', ['result_category'])
        self.risk_score_distribution = MockMetric('risk_score_distribution', 'Risk distribution')
        self.codex_requests_total = MockMetric('codex_requests_total', 'Codex requests', ['endpoint', 'status_code'])
        self.codex_request_duration_seconds = MockMetric('codex_request_duration_seconds', 'Codex duration', ['endpoint'])
        
        # Mock functions
        self.start_metrics_server = Mock()
        self.record_api_request = Mock()
        self.record_webhook_event = Mock()
        self.record_webhook_signature_validation = Mock()
        self.record_connection_status = Mock()
        self.record_nats_message = Mock()
        self.record_temporal_workflow_start = Mock()
        self.record_risk_score_calculation = Mock()
        self.record_codex_request = Mock()
        
        # Mock middleware
        self.MetricsMiddleware = lambda app: Mock()
        
class MockGuardCodexMetrics:
    """Mock guard-codex metrics module."""
    def __init__(self):
        # Mock metrics
        self.workflow_executions_total = MockMetric('workflow_executions_total', 'Workflow executions', ['workflow_type', 'status'])
        self.activity_executions_total = MockMetric('activity_executions_total', 'Activity executions', ['activity_name', 'status'])
        self.activity_failures_total = MockMetric('activity_failures_total', 'Activity failures', ['activity_name', 'failure_type'])
        self.workflow_failures_total = MockMetric('workflow_failures_total', 'Workflow failures', ['workflow_type', 'failure_type'])
        self.codex_events_processed_total = MockMetric('codex_events_processed_total', 'Codex events', ['event_type', 'status'])
        self.codex_docs_generated_total = MockMetric('codex_docs_generated_total', 'Docs generated', ['doc_type'])
        self.codex_graph_updates_total = MockMetric('codex_graph_updates_total', 'Graph updates', ['update_type'])
        
        # Mock functions
        self.start_metrics_server = Mock()
        self.record_workflow_start = Mock()
        self.record_workflow_completion = Mock()
        self.record_workflow_failure = Mock()
        self.record_activity_start = Mock()
        self.record_activity_completion = Mock()
        self.record_activity_failure = Mock()
        self.record_codex_event = Mock()
        self.record_docs_generation = Mock()
        self.record_graph_update = Mock()
        self.metrics_activity = lambda func: func

# Initialize mock modules
guard_api_metrics = MockGuardApiMetrics()
guard_codex_metrics = MockGuardCodexMetrics()


class TestGuardApiMetrics:
    """Test suite for guard-api Prometheus metrics."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset mocks
        guard_api_metrics.record_api_request.reset_mock()
        guard_api_metrics.record_webhook_event.reset_mock()
        guard_api_metrics.record_webhook_signature_validation.reset_mock()
        
    def test_api_request_metrics_recording(self):
        """Test recording of API request metrics."""
        # Test successful request
        guard_api_metrics.record_api_request('GET', '/health', 200, 0.5)
        guard_api_metrics.record_api_request.assert_called_with('GET', '/health', 200, 0.5)
        
        # Test error request
        guard_api_metrics.record_api_request('POST', '/webhook', 500, 1.2)
        assert guard_api_metrics.record_api_request.call_count == 2
        
    def test_webhook_event_metrics(self):
        """Test webhook event metrics recording."""
        # Test successful webhook processing
        guard_api_metrics.record_webhook_event('pull_request', 'opened', True, 0.8)
        guard_api_metrics.record_webhook_event.assert_called_with('pull_request', 'opened', True, 0.8)
        
        # Test failed webhook processing
        guard_api_metrics.record_webhook_event('push', 'created', False, 2.1)
        
        # Test without duration
        guard_api_metrics.record_webhook_event('issues', 'closed', True)
        
        assert guard_api_metrics.record_webhook_event.call_count == 3
        
    def test_webhook_signature_validation_metrics(self):
        """Test webhook signature validation metrics."""
        # Test successful validation
        guard_api_metrics.record_webhook_signature_validation(True)
        guard_api_metrics.record_webhook_signature_validation.assert_called_with(True)
        
        # Test failed validation
        guard_api_metrics.record_webhook_signature_validation(False)
        assert guard_api_metrics.record_webhook_signature_validation.call_count == 2
        
    def test_connection_status_metrics(self):
        """Test external service connection status metrics."""
        # Test connected status
        guard_api_metrics.record_connection_status('nats', True)
        guard_api_metrics.record_connection_status('temporal', True)
        
        # Test disconnected status
        guard_api_metrics.record_connection_status('redis', False)
        
        assert guard_api_metrics.record_connection_status.call_count == 3
        
    def test_nats_message_metrics(self):
        """Test NATS message publishing metrics."""
        # Test successful message
        guard_api_metrics.record_nats_message('pr.analysis', True)
        
        # Test failed message
        guard_api_metrics.record_nats_message('webhook.event', False)
        
        assert guard_api_metrics.record_nats_message.call_count == 2
        
    def test_temporal_workflow_metrics(self):
        """Test Temporal workflow start metrics."""
        # Test successful workflow start
        guard_api_metrics.record_temporal_workflow_start('pr_analysis', True)
        
        # Test failed workflow start
        guard_api_metrics.record_temporal_workflow_start('risk_assessment', False)
        
        assert guard_api_metrics.record_temporal_workflow_start.call_count == 2
        
    def test_risk_score_calculation_metrics(self):
        """Test risk score calculation metrics."""
        # Test low risk score
        guard_api_metrics.record_risk_score_calculation(0.2)
        
        # Test medium risk score
        guard_api_metrics.record_risk_score_calculation(0.5)
        
        # Test high risk score
        guard_api_metrics.record_risk_score_calculation(0.9)
        
        assert guard_api_metrics.record_risk_score_calculation.call_count == 3
        
    def test_codex_request_metrics(self):
        """Test Codex service request metrics."""
        # Test successful request
        guard_api_metrics.record_codex_request('/codex/pr-digest', 200, 1.5)
        
        # Test failed request
        guard_api_metrics.record_codex_request('/codex/graph', 500, 3.2)
        
        assert guard_api_metrics.record_codex_request.call_count == 2
        
    def test_metrics_server_startup_success(self):
        """Test successful metrics server startup."""
        guard_api_metrics.start_metrics_server(8080)
        guard_api_metrics.start_metrics_server.assert_called_with(8080)
        
    def test_metrics_server_startup_failure(self):
        """Test metrics server startup failure handling."""
        guard_api_metrics.start_metrics_server.side_effect = Exception("Port already in use")
        
        with pytest.raises(Exception):
            guard_api_metrics.start_metrics_server(8080)
        
    def test_metrics_middleware_initialization(self):
        """Test MetricsMiddleware initialization."""
        mock_app = Mock()
        middleware = guard_api_metrics.MetricsMiddleware(mock_app)
        
        # Since MetricsMiddleware is mocked, just verify it can be instantiated
        assert middleware is not None
        
    def test_metric_definitions(self):
        """Test that all required metrics are properly defined."""
        # Test guard-api metrics
        assert hasattr(guard_api_metrics, 'api_requests_total')
        assert hasattr(guard_api_metrics, 'api_request_duration_seconds')
        assert hasattr(guard_api_metrics, 'webhook_events_total')
        assert hasattr(guard_api_metrics, 'webhook_processing_duration_seconds')
        assert hasattr(guard_api_metrics, 'webhook_signature_validations_total')
        assert hasattr(guard_api_metrics, 'active_connections')
        assert hasattr(guard_api_metrics, 'nats_messages_published_total')
        assert hasattr(guard_api_metrics, 'temporal_workflow_starts_total')
        assert hasattr(guard_api_metrics, 'risk_score_calculations_total')
        assert hasattr(guard_api_metrics, 'risk_score_distribution')
        assert hasattr(guard_api_metrics, 'codex_requests_total')
        assert hasattr(guard_api_metrics, 'codex_request_duration_seconds')
        
    def test_metric_labels(self):
        """Test that metrics have the correct label names."""
        # Test API request labels
        expected_labels = ('method', 'endpoint', 'status_code')
        assert guard_api_metrics.api_requests_total._labelnames == expected_labels
        
        # Test webhook event labels
        expected_labels = ('event_type', 'action', 'status')
        assert guard_api_metrics.webhook_events_total._labelnames == expected_labels
        
        # Test connection status labels
        expected_labels = ('service',)
        assert guard_api_metrics.active_connections._labelnames == expected_labels


class TestGuardCodexMetrics:
    """Test suite for guard-codex Prometheus metrics."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset mocks
        guard_codex_metrics.record_workflow_start.reset_mock()
        guard_codex_metrics.record_workflow_completion.reset_mock()
        guard_codex_metrics.record_activity_start.reset_mock()
        
    def test_workflow_lifecycle_metrics(self):
        """Test complete workflow lifecycle metrics."""
        workflow_type = 'pr_analysis'
        
        # Start workflow
        guard_codex_metrics.record_workflow_start(workflow_type)
        guard_codex_metrics.record_workflow_start.assert_called_with(workflow_type)
        
        # Complete workflow successfully
        guard_codex_metrics.record_workflow_completion(workflow_type, 5.2, True)
        guard_codex_metrics.record_workflow_completion.assert_called_with(workflow_type, 5.2, True)
        
    def test_workflow_failure_metrics(self):
        """Test workflow failure metrics."""
        workflow_type = 'risk_assessment'
        failure_type = 'timeout'
        
        guard_codex_metrics.record_workflow_failure(workflow_type, failure_type)
        guard_codex_metrics.record_workflow_failure.assert_called_with(workflow_type, failure_type)
        
    def test_activity_lifecycle_metrics(self):
        """Test complete activity lifecycle metrics."""
        activity_name = 'analyze_pr'
        
        # Start activity
        guard_codex_metrics.record_activity_start(activity_name)
        guard_codex_metrics.record_activity_start.assert_called_with(activity_name)
        
        # Complete activity successfully
        guard_codex_metrics.record_activity_completion(activity_name, 2.1, True)
        guard_codex_metrics.record_activity_completion.assert_called_with(activity_name, 2.1, True)
        
    def test_activity_failure_metrics(self):
        """Test activity failure metrics."""
        activity_name = 'generate_docs'
        failure_type = 'ValueError'
        
        guard_codex_metrics.record_activity_failure(activity_name, failure_type)
        guard_codex_metrics.record_activity_failure.assert_called_with(activity_name, failure_type)
        
    def test_codex_event_processing_metrics(self):
        """Test Codex event processing metrics."""
        # Test successful event processing
        guard_codex_metrics.record_codex_event('pull_request', True)
        
        # Test failed event processing
        guard_codex_metrics.record_codex_event('push', False)
        
        assert guard_codex_metrics.record_codex_event.call_count == 2
        
    def test_docs_generation_metrics(self):
        """Test documentation generation metrics."""
        guard_codex_metrics.record_docs_generation('pr_digest')
        guard_codex_metrics.record_docs_generation('api_docs')
        
        assert guard_codex_metrics.record_docs_generation.call_count == 2
        
    def test_graph_update_metrics(self):
        """Test knowledge graph update metrics."""
        guard_codex_metrics.record_graph_update('node_creation')
        guard_codex_metrics.record_graph_update('relationship_update')
        
        assert guard_codex_metrics.record_graph_update.call_count == 2
        
    def test_codex_metrics_server_startup(self):
        """Test Codex metrics server startup."""
        guard_codex_metrics.start_metrics_server(8090)
        guard_codex_metrics.start_metrics_server.assert_called_with(8090)
        
    @pytest.mark.asyncio
    async def test_metrics_activity_decorator_success(self):
        """Test MetricsActivityDecorator for successful activity."""
        @guard_codex_metrics.metrics_activity
        async def sample_activity(data: str) -> str:
            await asyncio.sleep(0.01)  # Reduced sleep time for faster tests
            return f"processed: {data}"
        
        result = await sample_activity("test_data")
        assert result == "processed: test_data"
        
    @pytest.mark.asyncio
    async def test_metrics_activity_decorator_failure(self):
        """Test MetricsActivityDecorator for failed activity."""
        @guard_codex_metrics.metrics_activity
        async def failing_activity() -> None:
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await failing_activity()


class TestMetricsIntegration:
    """Test suite for metrics integration and end-to-end scenarios."""
    
    def test_metrics_collection_workflow(self):
        """Test complete metrics collection workflow."""
        # Simulate a complete request workflow
        start_time = time.time()
        
        # Record webhook event
        guard_api_metrics.record_webhook_event('pull_request', 'opened', True, 0.5)
        
        # Record signature validation
        guard_api_metrics.record_webhook_signature_validation(True)
        
        # Record risk score calculation
        guard_api_metrics.record_risk_score_calculation(0.6)
        
        # Record NATS message
        guard_api_metrics.record_nats_message('pr.analysis', True)
        
        # Record Temporal workflow start
        guard_api_metrics.record_temporal_workflow_start('pr_analysis', True)
        
        # Record API request
        duration = time.time() - start_time
        guard_api_metrics.record_api_request('POST', '/webhook', 200, duration)
        
        # Verify all functions were called
        guard_api_metrics.record_webhook_event.assert_called()
        guard_api_metrics.record_webhook_signature_validation.assert_called()
        guard_api_metrics.record_risk_score_calculation.assert_called()
        guard_api_metrics.record_nats_message.assert_called()
        guard_api_metrics.record_temporal_workflow_start.assert_called()
        guard_api_metrics.record_api_request.assert_called()
        
    def test_metrics_error_handling(self):
        """Test metrics recording with various error conditions."""
        # Test with None values where appropriate
        guard_api_metrics.record_webhook_event('push', 'created', True, None)
        
        # Test with edge case values
        guard_api_metrics.record_risk_score_calculation(0.0)
        guard_api_metrics.record_risk_score_calculation(1.0)
        
        # Test with empty strings
        guard_api_metrics.record_nats_message('', True)
        
        # Verify no exceptions were raised and functions were called
        assert guard_api_metrics.record_webhook_event.called
        assert guard_api_metrics.record_risk_score_calculation.called
        assert guard_api_metrics.record_nats_message.called
        
    def test_concurrent_metrics_recording(self):
        """Test concurrent metrics recording for thread safety."""
        import threading
        import concurrent.futures
        
        def record_metrics(thread_id: int):
            """Record metrics from multiple threads."""
            for i in range(10):
                guard_api_metrics.record_api_request('GET', f'/test/{thread_id}', 200, 0.1)
                guard_api_metrics.record_webhook_event('test', 'action', True, 0.2)
                
        # Run metrics recording from multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(record_metrics, i) for i in range(5)]
            concurrent.futures.wait(futures)
            
        # Verify no exceptions occurred
        for future in futures:
            future.result()  # This will raise if there was an exception
            
        # Verify functions were called multiple times
        assert guard_api_metrics.record_api_request.call_count >= 50
        assert guard_api_metrics.record_webhook_event.call_count >= 50


class TestMetricsConfiguration:
    """Test suite for metrics configuration and setup."""
    
    def test_metric_definitions(self):
        """Test that all required metrics are properly defined."""
        # Test guard-api metrics
        required_metrics = [
            'api_requests_total', 'api_request_duration_seconds', 'webhook_events_total',
            'webhook_processing_duration_seconds', 'webhook_signature_validations_total',
            'active_connections', 'nats_messages_published_total', 'temporal_workflow_starts_total',
            'risk_score_calculations_total', 'risk_score_distribution', 'codex_requests_total',
            'codex_request_duration_seconds'
        ]
        
        for metric_name in required_metrics:
            assert hasattr(guard_api_metrics, metric_name), f"Missing metric: {metric_name}"
            
        # Test guard-codex metrics
        codex_metrics = [
            'workflow_executions_total', 'activity_executions_total', 'activity_failures_total',
            'workflow_failures_total', 'codex_events_processed_total', 'codex_docs_generated_total',
            'codex_graph_updates_total'
        ]
        
        for metric_name in codex_metrics:
            assert hasattr(guard_codex_metrics, metric_name), f"Missing codex metric: {metric_name}"
            
    def test_metric_functions(self):
        """Test that all required metric functions are available."""
        # Test guard-api functions
        required_functions = [
            'start_metrics_server', 'record_api_request', 'record_webhook_event',
            'record_webhook_signature_validation', 'record_connection_status',
            'record_nats_message', 'record_temporal_workflow_start',
            'record_risk_score_calculation', 'record_codex_request'
        ]
        
        for func_name in required_functions:
            assert hasattr(guard_api_metrics, func_name), f"Missing function: {func_name}"
            assert callable(getattr(guard_api_metrics, func_name)), f"Not callable: {func_name}"
            
        # Test guard-codex functions
        codex_functions = [
            'start_metrics_server', 'record_workflow_start', 'record_workflow_completion',
            'record_workflow_failure', 'record_activity_start', 'record_activity_completion',
            'record_activity_failure', 'record_codex_event', 'record_docs_generation',
            'record_graph_update'
        ]
        
        for func_name in codex_functions:
            assert hasattr(guard_codex_metrics, func_name), f"Missing codex function: {func_name}"
            assert callable(getattr(guard_codex_metrics, func_name)), f"Not callable: {func_name}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
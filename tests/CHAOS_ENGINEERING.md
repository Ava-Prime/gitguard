# GitGuard Org-Brain Chaos Engineering Drills

This directory contains chaos engineering tests designed to validate the resilience and fault tolerance of the GitGuard system, including the org-brain features. These tests simulate various failure scenarios to ensure the system behaves correctly under adverse conditions.

## 🌪️ Overview

Chaos engineering is the practice of experimenting on a system to build confidence in its capability to withstand turbulent conditions in production. Our chaos drills focus on:

- **Idempotency Testing**: Ensuring duplicate events are handled correctly
- **Fault Injection**: Simulating failures and testing recovery mechanisms
- **Network Partitions**: Testing behavior during connectivity issues
- **High Load**: Validating performance under stress
- **Graph API Resilience**: Testing Graph API endpoint fault tolerance
- **Policy Transparency**: Validating policy evaluation under failure conditions
- **Mermaid Graph Generation**: Testing graph rendering resilience
- **Owners Index**: Validating owners data consistency during failures
- **SLO Monitoring**: Testing SLO compliance during chaos scenarios

## 📁 Files

### Core Test Files

- **`chaos_drills.py`**: Main chaos engineering test suite
- **`fault_injection.py`**: Fault injection framework and utilities
- **`guard_codex_fault_integration.py`**: Example integration with guard-codex service
- **`CHAOS_ENGINEERING.md`**: This documentation file

### Test Categories

#### A) Duplicate Flood (Idempotency Proof)
```python
# Sends 50 identical events and expects:
# - Only 1 workflow execution
# - 49 duplicate acknowledgments in logs/metrics
async def test_duplicate_flood_idempotency()
```

#### B) Crash Mid-Publish (Retry/Backoff)
```python
# Simulates crashes during publish and verifies:
# - JetStream redelivery mechanisms
# - Eventual successful processing
# - Proper retry/backoff behavior
async def test_crash_mid_publish_retry()
```

#### C) Network Partition Simulation
```python
# Tests system behavior during network connectivity issues
async def test_network_partition_simulation()
```

#### D) High Load Stress Test
```python
# Tests system behavior under high concurrent load
async def test_high_load_stress()
```

#### E) Graph API Fault Tolerance
```python
# Tests Graph API resilience during failures
async def test_graph_api_fault_tolerance()
```

#### F) Policy Transparency Resilience
```python
# Tests policy evaluation during service disruptions
async def test_policy_transparency_resilience()
```

#### G) Mermaid Graph Generation Chaos
```python
# Tests Mermaid graph rendering under failure conditions
async def test_mermaid_generation_chaos()
```

#### H) Owners Index Consistency
```python
# Tests owners index data consistency during failures
async def test_owners_index_consistency()
```

#### I) SLO Monitoring Chaos
```python
# Tests SLO monitoring accuracy during chaos scenarios
async def test_slo_monitoring_chaos()
```

## 🚀 Quick Start

### Prerequisites

1. **GitGuard Stack Running**:
   ```bash
   make codex.up
   make codex.schema
   ```

2. **Dependencies Installed**:
   ```bash
   pip install -r requirements-dev.txt
   pip install psycopg-binary nats-py
   ```

### Running Chaos Drills

```bash
# Run all chaos engineering tests
make test.chaos

# Run specific test
pytest tests/chaos_drills.py::test_duplicate_flood_idempotency -v

# Run with custom configuration
NATS_URL=nats://localhost:4222 pytest tests/chaos_drills.py -v
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `NATS_URL` | NATS server connection string | `nats://localhost:4222` |
| `FAULT_ONCE_DELIVERY_ID` | Delivery ID to inject fault for | None |
| `DATABASE_URL` | PostgreSQL connection string | From compose |
| `GRAPH_API_URL` | Graph API endpoint URL | `http://localhost:8080/api/v1/graph` |
| `POLICY_TRANSPARENCY_ENABLED` | Enable policy transparency chaos tests | `true` |
| `MERMAID_GENERATION_ENABLED` | Enable Mermaid graph chaos tests | `true` |
| `OWNERS_INDEX_ENABLED` | Enable owners index chaos tests | `true` |
| `SLO_MONITORING_ENABLED` | Enable SLO monitoring chaos tests | `true` |

### Test Configuration

```python
class ChaosTestConfig:
    NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
    DUPLICATE_COUNT = 50
    TIMEOUT_SECONDS = 30
    FAULT_ONCE_DELIVERY_ID = os.getenv("FAULT_ONCE_DELIVERY_ID")
    
    # Org-Brain Feature Configuration
    GRAPH_API_URL = os.getenv("GRAPH_API_URL", "http://localhost:8080/api/v1/graph")
    POLICY_TRANSPARENCY_ENABLED = os.getenv("POLICY_TRANSPARENCY_ENABLED", "true").lower() == "true"
    MERMAID_GENERATION_ENABLED = os.getenv("MERMAID_GENERATION_ENABLED", "true").lower() == "true"
    OWNERS_INDEX_ENABLED = os.getenv("OWNERS_INDEX_ENABLED", "true").lower() == "true"
    SLO_MONITORING_ENABLED = os.getenv("SLO_MONITORING_ENABLED", "true").lower() == "true"
    
    # Chaos Test Thresholds
    GRAPH_API_TIMEOUT = 5.0
    POLICY_EVAL_TIMEOUT = 10.0
    MERMAID_RENDER_TIMEOUT = 15.0
    OWNERS_INDEX_SYNC_TIMEOUT = 8.0
    SLO_COMPLIANCE_THRESHOLD = 0.99
```

## 🛠️ Fault Injection Framework

### Basic Usage

```python
from fault_injection import with_fault_injection, FaultInjectionError

@with_fault_injection
async def publish_portal(delivery_id: str, event_data: dict):
    # Your publish logic here
    # Will raise FaultInjectionError if FAULT_ONCE_DELIVERY_ID matches
    pass
```

### Manual Fault Injection

```python
from fault_injection import inject_publish_fault

# Manually trigger fault for specific delivery_id
try:
    inject_publish_fault("test-delivery-123")
except FaultInjectionError as e:
    print(f"Fault injected: {e}")
```

### Integration with Guard-Codex

To integrate fault injection into the actual guard-codex service:

1. **Import the fault injection decorator**:
   ```python
   from tests.fault_injection import with_fault_injection
   ```

2. **Decorate your publish methods**:
   ```python
   @with_fault_injection
   async def publish_portal(self, delivery_id: str, event_data: dict):
       # Existing publish logic
       pass
   ```

3. **Handle fault injection errors**:
   ```python
   try:
       await self.publish_portal(delivery_id, event_data)
   except FaultInjectionError as e:
       logger.warning(f"Chaos engineering fault: {e}")
       # Trigger retry mechanisms
   ```

## 📊 Expected Behaviors

### Duplicate Flood Test

**Expected Results**:
- ✅ 1 successful workflow execution
- ✅ 49 duplicate events acknowledged and ignored
- ✅ Idempotency maintained across all duplicates
- ✅ No data corruption or inconsistencies

**Monitoring Points**:
- Check NATS JetStream consumer metrics
- Verify database contains only one record per unique event
- Monitor application logs for deduplication messages

### Crash Mid-Publish Test

**Expected Results**:
- ✅ First publish attempt fails (simulated crash)
- ✅ JetStream handles redelivery automatically
- ✅ Second attempt succeeds
- ✅ Event is eventually processed successfully

**Monitoring Points**:
- NATS JetStream redelivery counters
- Application retry/backoff logs
- End-to-end processing confirmation

### Graph API Fault Tolerance Test

**Expected Results**:
- ✅ Circuit breaker activates on repeated failures
- ✅ Fallback to cached data when upstream unavailable
- ✅ Graceful degradation of Graph API features
- ✅ Automatic recovery when service restored

**Monitoring Points**:
- Graph API endpoint response times
- Circuit breaker state transitions
- Cache hit rates during failures
- Recovery time measurements

### Policy Transparency Resilience Test

**Expected Results**:
- ✅ Policy evaluation continues with cached policies
- ✅ OPA timeouts handled gracefully
- ✅ Transparency rendering degrades gracefully
- ✅ Policy decisions remain consistent

**Monitoring Points**:
- Policy evaluation latency
- Cache effectiveness metrics
- OPA service health
- Policy decision accuracy

### Mermaid Graph Generation Chaos Test

**Expected Results**:
- ✅ Graph generation failures don't block PR processing
- ✅ Fallback to text-based policy representation
- ✅ Graph rendering timeouts handled properly
- ✅ Cache prevents repeated generation attempts

**Monitoring Points**:
- Graph generation success rates
- Rendering timeout frequency
- Cache utilization
- Fallback activation rates

### Owners Index Consistency Test

**Expected Results**:
- ✅ Index remains consistent during partial failures
- ✅ Synchronization resumes after connectivity restored
- ✅ Stale data is properly invalidated
- ✅ Query performance maintained during sync

**Monitoring Points**:
- Index synchronization lag
- Data consistency checks
- Query response times
- Conflict resolution events

### SLO Monitoring Chaos Test

**Expected Results**:
- ✅ SLO violations are accurately detected
- ✅ Error budget calculations remain correct
- ✅ Alerting continues during monitoring failures
- ✅ Historical data integrity maintained

**Monitoring Points**:
- SLO compliance accuracy
- Error budget consumption rates
- Alert delivery success
- Data retention compliance

## 🔍 Monitoring and Observability

### Key Metrics to Monitor

1. **NATS JetStream Metrics**:
   - Message delivery attempts
   - Redelivery counts
   - Consumer lag
   - Acknowledgment rates

2. **Application Metrics**:
   - Event processing rates
   - Error rates by type
   - Duplicate detection rates
   - Processing latency

3. **Database Metrics**:
   - Connection pool usage
   - Query performance
   - Transaction success rates

4. **Graph API Metrics**:
   - Endpoint response times
   - Circuit breaker state
   - Fallback activation rates
   - Cache hit/miss ratios

5. **Policy Transparency Metrics**:
   - Policy evaluation latency
   - Policy cache effectiveness
   - Transparency rendering success rates
   - OPA evaluation performance

6. **Mermaid Graph Metrics**:
   - Graph generation time
   - Rendering success rates
   - Graph complexity metrics
   - Cache utilization

7. **Owners Index Metrics**:
   - Index synchronization latency
   - Data consistency checks
   - Update propagation time
   - Query performance

8. **SLO Monitoring Metrics**:
   - SLO compliance percentages
   - Error budget consumption
   - Alert firing rates
   - Recovery time objectives

### Log Analysis

Look for these log patterns during chaos tests:

```bash
# Successful deduplication
grep "Duplicate event detected" logs/guard-codex.log

# Fault injection triggers
grep "FAULT INJECTION" logs/guard-codex.log

# Retry attempts
grep "retry" logs/guard-codex.log

# Processing confirmations
grep "Successfully published" logs/guard-codex.log

# Graph API chaos events
grep "Graph API" logs/guard-brain.log
grep "circuit breaker" logs/guard-brain.log
grep "fallback mode" logs/guard-brain.log

# Policy transparency chaos
grep "policy evaluation" logs/guard-brain.log
grep "OPA timeout" logs/guard-brain.log
grep "policy cache" logs/guard-brain.log

# Mermaid graph chaos
grep "mermaid generation" logs/guard-brain.log
grep "graph rendering" logs/guard-brain.log

# Owners index chaos
grep "owners index" logs/guard-brain.log
grep "index sync" logs/guard-brain.log

# SLO monitoring chaos
grep "SLO violation" logs/guard-brain.log
grep "error budget" logs/guard-brain.log
```

## 🧪 Advanced Testing Scenarios

### Custom Chaos Scenarios

Create custom chaos tests by extending the base framework:

```python
@pytest.mark.asyncio
async def test_custom_chaos_scenario():
    """Custom chaos engineering test"""
    # Your custom chaos logic here
    pass
```

### Load Testing Integration

Combine chaos engineering with load testing:

```python
# Run chaos drills under load
NATS_URL=nats://localhost:4222 \
FAULT_ONCE_DELIVERY_ID=load-test-123 \
pytest tests/chaos_drills.py::test_high_load_stress -v
```

## 🚨 Safety Considerations

### Production Safety

⚠️ **WARNING**: These chaos tests are designed for development and staging environments. Do not run against production systems without proper safeguards.

### Safe Testing Practices

1. **Isolated Environment**: Run tests in isolated development/staging environments
2. **Data Backup**: Ensure test data can be easily restored
3. **Monitoring**: Have comprehensive monitoring in place
4. **Rollback Plan**: Prepare rollback procedures
5. **Team Coordination**: Coordinate with team before running disruptive tests

### Test Data Management

```python
# Use test-specific delivery IDs
delivery_id = f"chaos-test-{uuid.uuid4()}"

# Clean up test data after tests
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    yield
    # Cleanup logic here
```

## 🐛 Troubleshooting

### Common Issues

#### NATS Connection Errors
```bash
# Check NATS server status
docker compose -f ops/compose.yml ps nats

# Check NATS logs
docker compose -f ops/compose.yml logs nats
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker compose -f ops/compose.yml ps postgres

# Verify database schema
make codex.schema
```

#### Test Timeouts
```python
# Increase timeout for slow environments
class ChaosTestConfig:
    TIMEOUT_SECONDS = 60  # Increase from default 30
```

### Debug Mode

Run tests with verbose logging:

```bash
# Enable debug logging
LOG_LEVEL=DEBUG pytest tests/chaos_drills.py -v -s
```

## 📈 Continuous Integration

### CI/CD Integration

Add chaos tests to your CI pipeline:

```yaml
# .github/workflows/chaos-tests.yml
name: Chaos Engineering Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Run nightly
  workflow_dispatch:

jobs:
  chaos-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup GitGuard Stack
        run: |
          make codex.up
          make codex.schema
      - name: Run Chaos Drills
        run: make test.chaos
```

### Scheduled Testing

Run chaos tests on a regular schedule:

```bash
# Add to crontab for nightly chaos testing
0 2 * * * cd /path/to/gitguard && make test.chaos
```

## 🤝 Contributing

### Adding New Chaos Tests

1. **Create test function** in `chaos_drills.py`
2. **Follow naming convention**: `test_<scenario>_<expected_behavior>`
3. **Add comprehensive logging** for observability
4. **Document expected behaviors** in this README
5. **Include cleanup logic** to avoid test pollution

### Best Practices

- Use descriptive test names and docstrings
- Include both positive and negative test cases
- Add appropriate timeouts and error handling
- Log important events for debugging
- Clean up test data after execution

## 📚 References

- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [NATS JetStream Documentation](https://docs.nats.io/jetstream)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [GitGuard Architecture Documentation](../ARCHITECTURE.md)

---

**Happy Chaos Engineering! 🌪️**

Remember: The goal is not to break things, but to build confidence in our system's ability to handle the unexpected.
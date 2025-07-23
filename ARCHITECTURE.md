# Architecture Documentation

## Overview

The Healthcare Cost Navigator MVP is built using a clean, layered architecture that prioritizes maintainability, testability, and performance. The application follows modern Python best practices with async-first design patterns.

## Architecture Layers

### 1. API Layer (`app/api/`)
- **FastAPI Routers**: Handle HTTP requests and responses
- **Request/Response Models**: Pydantic models for validation
- **Dependency Injection**: Database sessions and services
- **Error Handling**: Centralized exception handling

### 2. Service Layer (`app/services/`)
- **Business Logic**: Core application logic separated from API concerns
- **ProviderService**: Hospital search and filtering operations
- **AIService**: Natural language processing and SQL generation
- **Class-based Design**: Promotes testability and reusability

### 3. Data Layer (`app/models/`, `app/db/`)
- **SQLAlchemy Models**: Async ORM with declarative base
- **Database Session Management**: Async session factory
- **Connection Pooling**: Efficient database connection handling

### 4. Configuration (`app/config/`)
- **Environment Management**: Pydantic settings for configuration
- **Type Safety**: Strongly typed configuration values
- **Validation**: Automatic validation of environment variables

## Design Patterns

### Service-Repository Pattern

**Why Class-based Services?**
- **Testability**: Easy to mock and test in isolation
- **Dependency Injection**: Services can be injected and swapped
- **Reusability**: Services can be used across different API endpoints
- **Maintainability**: Clear separation of concerns

**Implementation:**
```python
class ProviderService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def search_providers(self, drg: Optional[int] = None, ...):
        # Business logic here
```

### Repository Pattern (Implicit)
- SQLAlchemy models act as repositories
- Database operations are encapsulated in services
- Clear data access abstraction

## Database Design Decisions

### Normalized Schema
**Why Separate Tables?**
- **Data Integrity**: Foreign key constraints prevent orphaned records
- **Flexibility**: Hospitals can have multiple procedures and ratings
- **Performance**: Efficient indexing on specific columns
- **Maintainability**: Easier to modify individual entities

### Index Strategy
```sql
-- Hospitals table
CREATE INDEX idx_hospital_zip ON hospitals(provider_zip_code);
CREATE INDEX idx_hospital_state ON hospitals(provider_state);

-- Procedures table  
CREATE INDEX idx_procedure_drg ON procedures(ms_drg_code);
CREATE INDEX idx_procedure_charges ON procedures(average_covered_charges);

-- Ratings table
CREATE INDEX idx_rating_provider ON ratings(provider_id);
CREATE INDEX idx_rating_value ON ratings(rating);
```

### Async SQLAlchemy Benefits
- **Non-blocking I/O**: Database operations don't block the event loop
- **Connection Pooling**: Efficient resource utilization
- **Scalability**: Better performance under concurrent load
- **Modern Python**: Leverages Python 3.11 async features

## OpenAI Integration Architecture

### Two-Stage Processing
1. **SQL Generation**: Convert natural language to SQL queries
2. **Answer Generation**: Create human-readable responses from results

### Safety Measures
```python
# SQL Injection Prevention
dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER']
if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
    raise ValueError("Generated SQL contains dangerous operations")

# Fallback Mechanism
try:
    results = await self._execute_sql_query(sql_query, params)
except Exception:
    results = await self._fallback_search(params)
```

### Trade-offs Analysis

**Pros of OpenAI for SQL Generation:**
- **Natural Language Understanding**: Handles complex, varied queries
- **Flexible Query Generation**: Can create complex JOINs and aggregations
- **Human-like Responses**: Generates conversational answers
- **Rapid Development**: No need to build custom NLP pipeline

**Cons and Mitigations:**
- **API Dependency**: Single point of failure
  - *Mitigation*: Service layer fallback
- **Cost**: Per-request pricing
  - *Mitigation*: Query caching, rate limiting
- **Latency**: External API calls
  - *Mitigation*: Async processing, timeout handling
- **Potential Errors**: Incorrect SQL generation
  - *Mitigation*: SQL validation, fallback to service methods

## Performance Considerations

### Database Optimization
- **Indexed Queries**: All common search patterns are indexed
- **Efficient JOINs**: Proper foreign key relationships
- **Query Optimization**: Minimal data transfer

### Async Architecture Benefits
- **Concurrent Processing**: Multiple requests handled simultaneously
- **Resource Efficiency**: Non-blocking I/O operations
- **Scalability**: Better resource utilization

### Caching Strategy (Future)
- **Query Results**: Cache frequent searches
- **AI Responses**: Cache similar questions
- **Database Connections**: Connection pooling

## Security Architecture

### Input Validation
- **Pydantic Models**: Automatic request validation
- **Type Safety**: Strong typing throughout the stack
- **SQL Injection Prevention**: Parameterized queries and validation

### Error Handling
- **Graceful Degradation**: Fallback mechanisms for failures
- **Information Leakage Prevention**: Generic error messages
- **Logging**: Structured logging for debugging

### Environment Security
- **Configuration Management**: Environment variables for secrets
- **Docker Security**: Non-root user in containers
- **Network Security**: CORS configuration

## Testing Strategy

### Test Architecture
- **Unit Tests**: Service layer testing with mocked dependencies
- **Integration Tests**: API endpoint testing with test database
- **Async Testing**: Proper async test fixtures and patterns

### Test Data Management
- **Fixtures**: Reusable test data setup
- **Isolation**: Each test runs in isolation
- **Cleanup**: Automatic test data cleanup

## Deployment Architecture

### Docker Strategy
- **Multi-stage Builds**: Optimized container images
- **Health Checks**: Application health monitoring
- **Non-root User**: Security best practices

### Docker Compose Benefits
- **Service Orchestration**: Coordinated startup of services
- **Environment Management**: Centralized configuration
- **Development/Production Parity**: Same environment across stages

## Scalability Considerations

### Horizontal Scaling
- **Stateless Design**: Services can be scaled horizontally
- **Database Connection Pooling**: Efficient connection management
- **Load Balancing**: Ready for load balancer integration

### Vertical Scaling
- **Async Processing**: Better CPU utilization
- **Memory Efficiency**: Minimal memory footprint
- **Resource Optimization**: Efficient resource usage

## Monitoring and Observability

### Health Checks
- **Application Health**: `/health` endpoint
- **Database Connectivity**: Connection pool monitoring
- **External Dependencies**: OpenAI API health monitoring

### Logging Strategy
- **Structured Logging**: JSON-formatted logs
- **Request Tracing**: Request/response logging
- **Error Tracking**: Comprehensive error logging

## Future Architecture Enhancements

### Microservices Evolution
- **Service Decomposition**: Split into focused services
- **API Gateway**: Centralized routing and authentication
- **Event-Driven Architecture**: Async communication between services

### Data Architecture
- **Read Replicas**: Database read scaling
- **Caching Layer**: Redis for performance optimization
- **Data Warehousing**: Analytics and reporting capabilities

### AI/ML Integration
- **Model Serving**: Dedicated ML model serving
- **Feature Store**: Centralized feature management
- **A/B Testing**: Experimentation framework

## Conclusion

The Healthcare Cost Navigator MVP architecture prioritizes:

1. **Maintainability**: Clean separation of concerns and modular design
2. **Testability**: Comprehensive testing strategy with proper abstractions
3. **Performance**: Async-first design with optimized database operations
4. **Security**: Multiple layers of security and validation
5. **Scalability**: Architecture ready for growth and scaling

The architecture provides a solid foundation for future enhancements while maintaining simplicity and clarity for the current MVP requirements. 
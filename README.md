# Healthcare Cost Navigator MVP

A comprehensive healthcare cost comparison platform with a FastAPI backend and React frontend that enables patients to search for hospitals offering MS-DRG procedures, view estimated prices & quality ratings, and interact with an AI assistant for natural language queries.

## Features

- **Hospital Search**: Search hospitals by MS-DRG code, ZIP code, and radius
- **Cost Comparison**: View and compare hospital charges and payments
- **Quality Ratings**: Access hospital star ratings (1-10 scale)
- **AI Assistant**: Natural language interface for healthcare queries
- **Fuzzy Search**: Text-based search for procedures and hospitals
- **Modern Web Interface**: React-based frontend with responsive design
- **Async Architecture**: High-performance async SQLAlchemy and FastAPI

## Tech Stack

### Backend
- **Python 3.11** with Poetry for dependency management
- **FastAPI** for REST API framework
- **Async SQLAlchemy** for database ORM
- **PostgreSQL** for data storage
- **OpenAI GPT-4o** for natural language processing
- **Docker & Docker Compose** for containerization
- **Pytest** for testing

### Frontend
- **React 18** with **TypeScript** for type-safe development
- **TailwindCSS** for modern, responsive styling
- **Axios** for API communication
- **Docker** for containerization

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (optional - app works without it using fallback methods)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd healthcare-cost-navigator
   ```

2. **Set environment variables (optional)**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   # Note: The app will work without OpenAI API key using fallback methods
   ```

3. **Download [sample data](https://catalog.data.gov/dataset/medicare-inpatient-hospitals-by-provider-and-service-9af02/resource/e51cf14c-615a-4efe-ba6b-3a3ef15dcfb0)**
   ```bash
   # Download the CMS sample data (15k Alabama records)
   # Place it as sample_prices_ny.csv in the project root
   # Note: Despite the filename, this contains Alabama hospital data
   ```

4. **Start the application**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - **Frontend**: http://localhost:3000 (Modern web interface)
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

6. **Test the API**
   ```bash
   # Test basic search
   curl "http://localhost:8000/providers?drg=023"
   
   # Test AI assistant
   curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "Who is cheapest for DRG 023 near 36301?"}'
   ```

## API Endpoints

### GET /providers
Search for hospitals offering MS-DRG procedures.

**Parameters:**
- `drg` (optional): MS-DRG code (e.g., 023, 024, 025, 038)
- `zip_code` (optional): ZIP code for location search
- `radius_km` (optional): Search radius in kilometers
- `sort_by` (optional): Sort by "cost" or "rating" (default: "cost")

**Example:**
```bash
# Search for heart failure procedures (DRG 291) near ZIP 36301
curl "http://localhost:8000/providers/?drg=291&zip_code=36301&radius_km=25&sort_by=cost"

# Search for pneumonia procedures without location filter
curl "http://localhost:8000/providers/?drg=193&sort_by=rating"
```

### GET /providers/search
Text-based search for procedures and hospitals.

**Parameters:**
- `q` (required): Search text
- `zip_code` (optional): ZIP code for location search
- `radius_km` (optional): Search radius in kilometers

**Example:**
```bash
# Search for heart failure procedures
curl "http://localhost:8000/providers/search?q=heart%20failure&zip_code=36301"

# Search for hospitals by name
curl "http://localhost:8000/providers/search?q=Southeast%20Health"
```

### POST /ask
Natural language interface for healthcare queries.

**Request Body:**
```json
{
  "question": "Who is cheapest for DRG 291 within 25 miles of 36301?"
}
```

**Example:**
```bash
# Ask about heart failure procedures
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is cheapest for DRG 291 within 25 miles of 36301?"}'

# Ask about hospital ratings
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What hospitals have the best ratings for DRG 193 near 36401?"}'
```

## AI Assistant Examples

The AI assistant can handle various types of healthcare-related questions:

### Cost Queries
1. **"Who is cheapest for DRG 291 within 25 miles of 36301?"**
   - Finds the most affordable hospitals for heart failure procedures near Dothan, AL

2. **"What's the cheapest hospital for DRG 193 near 36401?"**
   - Searches for pneumonia procedures with cost-based sorting

3. **"What hospital has the lowest total payments for DRG 280 near 36301?"**
   - Compares total payment amounts for heart attack procedures

### Quality Queries
4. **"Who has the best ratings for DRG 291 near 36301?"**
   - Finds top-rated hospitals for heart failure procedures

5. **"Show me top 3 hospitals by rating for DRG 193 within 50 km of 36401"**
   - Lists highest-rated hospitals for pneumonia procedures in the area

### Out-of-Scope Handling
6. **"What's the weather today?"**
   - Returns: "I can only help with hospital pricing and quality information. Please ask about medical procedures, costs, or hospital ratings."

## Sample Data Coverage

The application uses a sample dataset containing **15,000+ hospital procedure records** from Alabama hospitals. The data includes:

- **Geographic Coverage**: Alabama hospitals (ZIP codes starting with 36xxx)
- **Procedure Types**: Neurological, surgical, and medical procedures
- **Time Period**: Recent CMS hospital pricing data
- **Data Quality**: Clean, validated hospital and procedure information

### Common DRG Codes in Sample Data:
- **291**: Heart Failure and Shock with MCC
- **193**: Simple Pneumonia and Pleurisy with MCC
- **280**: Acute Myocardial Infarction, Discharged Alive with MCC
- **247**: Percutaneous Cardiovascular Procedures with Drug-Eluting Stent without MCC
- **871**: Septicemia or Severe Sepsis without MV >96 Hours with MCC
- **552**: Medical Back Problems without MCC
- **603**: Cellulitis without MCC
- **682**: Renal Failure with MCC

## Database Schema

### Hospitals Table
- `provider_id` (PK): CMS provider identifier
- `provider_name`: Hospital name
- `provider_city`: City
- `provider_state`: State (2-letter code)
- `provider_zip_code`: ZIP code

### Procedures Table
- `id` (PK): Auto-incrementing ID
- `provider_id` (FK): Reference to hospitals table
- `ms_drg_code`: MS-DRG procedure code
- `ms_drg_definition`: Procedure description
- `total_discharges`: Number of procedures performed
- `average_covered_charges`: Average hospital charges
- `average_total_payments`: Average total payments
- `average_medicare_payments`: Average Medicare payments

### Ratings Table
- `id` (PK): Auto-incrementing ID
- `provider_id` (FK): Reference to hospitals table
- `rating`: Star rating (1-10 scale)

## ETL Process

The ETL script (`app/etl.py`) performs the following operations:

1. **Data Loading**: Reads `sample_prices_ny.csv` asynchronously (Alabama hospital data)
2. **Data Cleaning**: Maps CSV column names to database schema and trims whitespace
3. **DRG Processing**: Uses MS-DRG codes directly from the CSV (023, 024, 025, 038, etc.)
4. **Data Population**: Creates hospital, procedure, and rating records
5. **Rating Generation**: Creates mock star ratings (1-10) for each provider

**Available DRG Codes in Sample Data:**
- **023**: Craniotomy with Major Device Implant or Acute Complex CNS Principal Diagnosis with MCC
- **024**: Craniotomy with Major Device Implant or Acute Complex CNS Principal Diagnosis without MCC
- **025**: Craniotomy and Endovascular Intracranial Procedures with MCC
- **038**: Extracranial Procedures with CC
- And many more neurological and surgical procedures

## Development

### Local Development Setup

1. **Install Poetry**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

4. **Run database migrations**
   ```bash
   poetry run python -m app.etl
   ```

5. **Start development server**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_api.py
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy app/
```

## Architecture Decisions

### Service Layer Pattern
- **ProviderService**: Handles hospital search and filtering logic
- **AIService**: Manages natural language processing and SQL generation
- **Benefits**: Separation of concerns, testability, reusability

### Async SQLAlchemy
- **Performance**: Non-blocking database operations
- **Scalability**: Better resource utilization under load
- **Modern Python**: Leverages Python 3.11 async features

### OpenAI Integration
- **SQL Generation**: Converts natural language to SQL queries
- **Answer Generation**: Creates human-readable responses
- **Safety**: Validates generated SQL to prevent injection attacks
- **Fallback**: Service layer fallback if AI generation fails

### Database Design
- **Normalized Schema**: Separate tables for hospitals, procedures, and ratings
- **Indexes**: Optimized for common query patterns
- **Foreign Keys**: Maintains data integrity
- **Flexibility**: Supports various search and filtering scenarios

## Trade-offs

### OpenAI for SQL Generation
**Pros:**
- Natural language understanding
- Flexible query generation
- Human-like responses

**Cons:**
- API dependency and costs
- Potential for incorrect SQL
- Latency from external API calls

**Mitigation:**
- SQL validation and sanitization
- Service layer fallback
- Caching for repeated queries

### Simplified Geospatial Search
**Current Implementation:**
- ZIP code prefix matching (first 3 digits)
- Simplified radius calculations
- Sample data covers Alabama area (ZIP codes starting with 36xxx)

**Production Considerations:**
- Implement proper geospatial indexes
- Use PostGIS for accurate distance calculations
- Integrate with geocoding services
- Expand to nationwide hospital data

### Mock Ratings
**Current Implementation:**
- Random rating generation
- Realistic distribution (favoring higher ratings)

**Production Considerations:**
- Integrate with Medicare star ratings
- Use actual quality metrics
- Implement rating aggregation logic

## Performance Considerations

- **Database Indexes**: Optimized for common query patterns
- **Connection Pooling**: Efficient database connection management
- **Async Operations**: Non-blocking I/O throughout the stack
- **Query Optimization**: Efficient JOINs and filtering
- **Caching**: Consider Redis for frequently accessed data

## Security Considerations

- **SQL Injection Prevention**: Parameterized queries and validation
- **Input Validation**: Pydantic models for request validation
- **Error Handling**: Graceful error responses without information leakage
- **API Rate Limiting**: Consider implementing rate limiting for production
- **Environment Variables**: Secure configuration management

## Future Enhancements

1. **Real Geospatial Search**: Implement PostGIS for accurate distance calculations
2. **Actual Quality Data**: Integrate with Medicare star ratings and quality metrics
3. **Caching Layer**: Add Redis for performance optimization
4. **Authentication**: Implement user authentication and authorization
5. **Advanced Analytics**: Add cost trend analysis and quality comparisons
6. **Mobile App**: Develop companion mobile application
7. **Insurance Integration**: Add insurance-specific pricing and coverage
8. **Provider Portal**: Allow hospitals to update their information

## Testing Examples

Here are real working examples you can test with the application:

### Basic Provider Search
```bash
# Search for all craniotomy procedures (DRG 023)
curl "http://localhost:8000/providers?drg=023"

# Search for procedures near Dothan, AL
curl "http://localhost:8000/providers?drg=024&zip_code=36301&radius_km=50"

# Search by rating
curl "http://localhost:8000/providers?drg=025&sort_by=rating"
```

### Text Search
```bash
# Search for craniotomy procedures
curl "http://localhost:8000/providers/search?q=craniotomy"

# Search for specific hospital
curl "http://localhost:8000/providers/search?q=Southeast Health"
```

### AI Assistant Queries
```bash
# Cost comparison
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the cheapest hospital for DRG 023 near 36301?"}'

# Quality comparison
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Which hospitals have the best ratings for DRG 024?"}'

# General procedure search
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me hospitals that perform DRG 038 procedures"}'

# Out-of-scope question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the weather today?"}'
```

### Expected Responses
- **Provider Search**: Returns JSON array of hospitals with procedure details, costs, and ratings
- **AI Assistant**: Returns natural language answers with supporting data
- **Out-of-Scope**: Returns message explaining the assistant only handles healthcare queries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

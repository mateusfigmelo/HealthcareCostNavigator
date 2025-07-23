# Sample API Queries for Healthcare Cost Navigator

## Setup Instructions

1. **Start the application:**
   ```bash
   docker-compose up --build
   ```

2. **Wait for the application to be ready** (check logs for "Starting FastAPI application...")

3. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

## Provider Search Examples

### 1. Search by DRG Code (Heart Failure)
```bash
curl "http://localhost:8000/providers/?drg=291&sort_by=cost"
```

### 2. Search by DRG and Location (Alabama)
```bash
curl "http://localhost:8000/providers/?drg=291&zip_code=36301&radius_km=25&sort_by=cost"
```

### 3. Search by DRG and Sort by Rating
```bash
curl "http://localhost:8000/providers/?drg=193&zip_code=36401&radius_km=25&sort_by=rating"
```

### 4. Text-based Search
```bash
curl "http://localhost:8000/providers/search?q=heart%20failure&zip_code=36301"
```

### 5. Search for Pneumonia Procedures
```bash
curl "http://localhost:8000/providers/search?q=pneumonia&zip_code=36401"
```

## AI Assistant Examples

### 1. Cost-based Queries
```bash
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is cheapest for DRG 291 within 25 miles of 36301?"}'
```

### 2. Quality-based Queries
```bash
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who has the best ratings for DRG 193 near 36401?"}'
```

### 3. Complex Queries
```bash
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me top 3 hospitals by rating for DRG 291 within 50 km of 36301"}'
```

### 4. Average Cost Queries
```bash
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the average cost of heart failure treatment in Alabama?"}'
```

### 5. Payment Comparison
```bash
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What hospital has the lowest total payments for DRG 193 near 36401?"}'
```

### 6. Out-of-Scope Query (Should be rejected)
```bash
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the weather today?"}'
```

## Health Check

```bash
curl "http://localhost:8000/health"
```

## API Documentation

Access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Actual Test Results

### Example 1: Heart Failure Search
**Query:** `"Show me top 3 hospitals by rating for DRG 291 within 50 km of 36301"`

**Response:**
```json
{
  "answer": "In the area around the 36301 zip code, the top-rated hospital for DRG 291 is Southeast Health Medical Center. It's located right in Dothan, Alabama, and boasts a solid rating of 6.0. Unfortunately, we don't have more hospitals within a 50 km range to compare, but Southeast Health Medical Center seems to be a reliable choice. If you need more options or details on costs, let me know, and I can help with additional information!",
  "results": [
    {
      "provider_id": "010001",
      "provider_name": "SOUTHEAST HEALTH MEDICAL CENTER",
      "provider_city": "DOTHAN",
      "provider_state": "AL",
      "provider_zip_code": "36301",
      "rating": 6.0
    }
  ],
  "out_of_scope": false,
  "sql_query": "SELECT hospitals.provider_id, hospitals.provider_name, hospitals.provider_city, hospitals.provider_state, hospitals.provider_zip_code, ratings.rating FROM hospitals JOIN procedures ON hospitals.provider_id = procedures.provider_id JOIN ratings ON hospitals.provider_id = ratings.provider_id WHERE procedures.ms_drg_code = '291' AND hospitals.provider_zip_code = '36301' ORDER BY ratings.rating DESC LIMIT 3",
  "error": null
}
```

### Example 2: Cost Analysis Query
**Query:** `"What is the average cost of heart failure treatment in Alabama?"`

**Response:**
```json
{
  "answer": "If you're looking at the cost of heart failure treatment in Alabama, the prices can vary quite a bit. For instance, at Southeast Health Medical Center in Dothan, the average coverage charge is about $35,102, with an overall rating of 6.0. Meanwhile, Evergreen Medical Center charges around $10,505, with a rating of 7.0. These costs reflect the average covered charges, and you might pay less depending on your insurance. It's always good to consider both cost and hospital ratings when making your decision!",
  "results": [
    {
      "provider_name": "SOUTHEAST HEALTH MEDICAL CENTER",
      "provider_city": "DOTHAN",
      "provider_state": "AL",
      "provider_zip_code": "36301",
      "ms_drg_definition": "HEART FAILURE AND SHOCK WITH MCC",
      "average_covered_charges": 35102.4,
      "average_total_payments": 9223.56,
      "average_medicare_payments": 7517.81,
      "rating": 6.0
    },
    {
      "provider_name": "EVERGREEN MEDICAL CENTER",
      "provider_city": "EVERGREEN",
      "provider_state": "AL",
      "provider_zip_code": "36401",
      "ms_drg_definition": "HEART FAILURE AND SHOCK WITH MCC",
      "average_covered_charges": 10505.03,
      "average_total_payments": 8382.32,
      "average_medicare_payments": 6848.13,
      "rating": 7.0
    }
  ],
  "out_of_scope": false,
  "sql_query": "SELECT h.provider_name, h.provider_city, h.provider_state, h.provider_zip_code, p.ms_drg_definition, p.average_covered_charges, p.average_total_payments, p.average_medicare_payments, r.rating FROM hospitals h JOIN procedures p ON h.provider_id = p.provider_id LEFT JOIN ratings r ON h.provider_id = r.provider_id WHERE p.ms_drg_code = '291' AND h.provider_state = 'AL' ORDER BY p.average_covered_charges DESC LIMIT 10;",
  "error": null
}
```

### Example 3: Out-of-Scope Query
**Query:** `"What is the weather today?"`

**Response:**
```json
{
  "answer": "I can only help with hospital pricing and quality information. Please ask about medical procedures, costs, or hospital ratings.",
  "results": [],
  "out_of_scope": true,
  "sql_query": null,
  "error": null
}
```

## Expected Responses

### Provider Search Response
```json
[
  {
    "provider_id": "010001",
    "provider_name": "SOUTHEAST HEALTH MEDICAL CENTER",
    "provider_city": "DOTHAN",
    "provider_state": "AL",
    "provider_zip_code": "36301",
    "ms_drg_code": "291",
    "ms_drg_definition": "HEART FAILURE AND SHOCK WITH MCC",
    "total_discharges": 237,
    "average_covered_charges": 35102.4,
    "average_total_payments": 9223.56,
    "average_medicare_payments": 7517.81,
    "average_rating": 6.0
  }
]
```

### AI Assistant Response
```json
{
  "answer": "In the area around the 36301 zip code, the top-rated hospital for DRG 291 is Southeast Health Medical Center. It's located right in Dothan, Alabama, and boasts a solid rating of 6.0. Unfortunately, we don't have more hospitals within a 50 km range to compare, but Southeast Health Medical Center seems to be a reliable choice. If you need more options or details on costs, let me know, and I can help with additional information!",
  "results": [
    {
      "provider_id": "010001",
      "provider_name": "SOUTHEAST HEALTH MEDICAL CENTER",
      "provider_city": "DOTHAN",
      "provider_state": "AL",
      "provider_zip_code": "36301",
      "rating": 6.0
    }
  ],
  "out_of_scope": false,
  "sql_query": "SELECT hospitals.provider_id, hospitals.provider_name, hospitals.provider_city, hospitals.provider_state, hospitals.provider_zip_code, ratings.rating FROM hospitals JOIN procedures ON hospitals.provider_id = procedures.provider_id JOIN ratings ON hospitals.provider_id = ratings.provider_id WHERE procedures.ms_drg_code = '291' AND hospitals.provider_zip_code = '36301' ORDER BY ratings.rating DESC LIMIT 3",
  "error": null
}
```

### Out-of-Scope Response
```json
{
  "answer": "I can only help with hospital pricing and quality information. Please ask about medical procedures, costs, or hospital ratings.",
  "results": [],
  "out_of_scope": true,
  "sql_query": null,
  "error": null
}
```

## Testing Tips

1. **Start with simple queries** to verify the API is working
2. **Test both endpoints** (/providers and /ask)
3. **Try different DRG codes** (291, 193, 280, 247 are common in the data)
4. **Test location filtering** with different ZIP codes (36301, 36401, 35209, 21204)
5. **Verify sorting** works for both cost and rating
6. **Check error handling** with invalid parameters
7. **Test out-of-scope queries** to ensure proper filtering

## Common DRG Codes in Sample Data

- **291**: Heart Failure and Shock with MCC
- **193**: Simple Pneumonia and Pleurisy with MCC
- **280**: Acute Myocardial Infarction, Discharged Alive with MCC
- **247**: Percutaneous Cardiovascular Procedures with Drug-Eluting Stent without MCC
- **871**: Septicemia or Severe Sepsis without MV >96 Hours with MCC
- **552**: Medical Back Problems without MCC
- **603**: Cellulitis without MCC

## Geographic Coverage in Sample Data

- **Alabama (AL)**: ZIP codes starting with 36xxx (Dothan, Birmingham, Mobile, Evergreen)
- **Maryland (MD)**: ZIP codes starting with 21xxx (Baltimore, Columbia)
- **Oregon (OR)**: ZIP codes starting with 97xxx (Medford, Springfield, Hillsboro)

## Troubleshooting

1. **Database connection issues**: Check if PostgreSQL is running
2. **OpenAI API errors**: Verify your API key is set correctly
3. **No results**: Try broader search criteria or different ZIP codes from the sample data
4. **Slow responses**: The AI assistant may take a few seconds for complex queries 

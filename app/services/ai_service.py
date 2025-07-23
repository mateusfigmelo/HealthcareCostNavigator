"""AI service for natural language to SQL conversion."""

import re
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.provider_service import ProviderService


class AIService:
    """Service for AI-powered natural language queries."""

    client: AsyncOpenAI | None

    def __init__(self, session: AsyncSession):
        self.session = session
        self.provider_service = ProviderService(session)

        # Initialize OpenAI client only if API key is available
        if (
            hasattr(settings, "openai_api_key")
            and settings.openai_api_key
            and settings.openai_api_key != "your-openai-api-key-here"
        ):
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None

    def _is_healthcare_related(self, question: str) -> bool:
        """Check if the question is healthcare-related."""
        healthcare_keywords = [
            "hospital",
            "doctor",
            "medical",
            "procedure",
            "surgery",
            "cost",
            "price",
            "drg",
            "rating",
            "quality",
            "cheapest",
            "best",
            "near",
            "zip",
            "miles",
            "knee",
            "heart",
            "joint",
            "replacement",
            "bypass",
            "cardiac",
            "orthopedic",
        ]

        question_lower = question.lower()
        return any(keyword in question_lower for keyword in healthcare_keywords)

    def _extract_parameters(self, question: str) -> dict[str, Any]:
        """Extract parameters from natural language question."""
        params: dict[str, Any] = {}

        # Extract DRG code
        drg_match = re.search(r"drg\s+(\d+)", question.lower())
        if drg_match:
            params["drg"] = str(drg_match.group(1))  # Keep as string for SQL

        # Extract ZIP code
        zip_match = re.search(r"(\d{5})", question)
        if zip_match:
            params["zip_code"] = zip_match.group(1)

        # Extract radius/distance
        radius_match = re.search(r"(\d+)\s*(?:miles?|km)", question.lower())
        if radius_match:
            radius_value = int(radius_match.group(1))
            # Convert miles to km if needed
            if "miles" in question.lower():
                radius_value = int(radius_value * 1.60934)
            params["radius_km"] = radius_value

        # Extract sort preference
        if "cheapest" in question.lower() or "lowest cost" in question.lower():
            params["sort_by"] = "cost"
        elif "best rating" in question.lower() or "highest rating" in question.lower():
            params["sort_by"] = "rating"

        return params

    async def _generate_sql_query(self, question: str) -> str:
        """Generate SQL query from natural language using OpenAI."""

        if not self.client:
            # Fallback to parameter extraction without SQL generation
            raise ValueError("OpenAI client not available")

        system_prompt = """
        You are a SQL expert for a healthcare database. Generate a safe SQL query based on the user's question.

        Database schema:
        - hospitals: provider_id (PK), provider_name, provider_city, provider_state, provider_zip_code
        - procedures: id (PK), provider_id (FK), ms_drg_code (VARCHAR), ms_drg_definition, total_discharges, average_covered_charges, average_total_payments, average_medicare_payments
        - ratings: id (PK), provider_id (FK), rating (1-10 scale)

        Rules:
        1. Only generate SELECT queries
        2. Use proper JOINs to connect tables
        3. Include WHERE clauses for filtering
        4. Use ORDER BY for sorting
        5. Limit results to 10 rows
        6. Never use INSERT, UPDATE, DELETE, or DROP
        7. Use parameterized queries with placeholders like :drg, :zip_code
        8. Always include provider information and ratings when available
        9. Return ONLY the raw SQL query - NO markdown formatting, NO code blocks, NO explanations
        10. IMPORTANT: ms_drg_code is VARCHAR - always use quotes around DRG codes (e.g., ms_drg_code = '470')
        11. IMPORTANT: provider_zip_code is VARCHAR - always use quotes around ZIP codes (e.g., provider_zip_code = '10001')

        IMPORTANT: Return the SQL query as plain text without any markdown formatting or code blocks.
        """

        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned empty response")
        sql_query = content.strip()

        # Clean up markdown formatting if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]  # Remove ```sql
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]  # Remove ```
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]  # Remove trailing ```

        sql_query = sql_query.strip()

        # Basic SQL injection prevention
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "INSERT",
            "UPDATE",
            "CREATE",
            "ALTER",
            "EXEC",
            "EXECUTE",
        ]
        if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
            raise ValueError("Generated SQL contains dangerous operations")

        return sql_query

    async def _execute_sql_query(
        self, sql_query: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute the generated SQL query safely."""
        try:
            # Replace placeholders with actual values
            for key, value in params.items():
                sql_query = sql_query.replace(f":{key}", str(value))

            result = await self.session.execute(text(sql_query))
            rows = result.fetchall()

            # Convert to list of dicts
            columns = result.keys()
            return [dict(zip(columns, row, strict=False)) for row in rows]

        except Exception:
            # Rollback the transaction on error
            await self.session.rollback()
            # Fallback to service method if SQL execution fails
            return await self._fallback_search(params)

    async def _fallback_search(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Fallback search using the provider service."""
        return await self.provider_service.search_providers(
            drg=params.get("drg"),
            zip_code=params.get("zip_code"),
            radius_km=params.get("radius_km"),
            sort_by=params.get("sort_by", "cost"),
        )

    async def process_question(self, question: str) -> dict[str, Any]:
        """Process a natural language question and return results."""

        # Check if question is healthcare-related
        if not self._is_healthcare_related(question):
            return {
                "answer": "I can only help with hospital pricing and quality information. Please ask about medical procedures, costs, or hospital ratings.",
                "results": [],
                "out_of_scope": True,
            }

        try:
            # Extract parameters from question
            params = self._extract_parameters(question)

            # Try to generate SQL query (may fail if OpenAI is not available)
            sql_query = None
            results = []
            try:
                sql_query = await self._generate_sql_query(question)
                # Execute query
                results = await self._execute_sql_query(sql_query, params)
            except Exception:
                # Fallback to service method if SQL generation fails
                results = await self._fallback_search(params)

            # Generate natural language answer
            answer = await self._generate_answer(question, results)

            return {
                "answer": answer,
                "results": results,
                "sql_query": sql_query,
                "error": None,
                "out_of_scope": False,
            }

        except Exception as e:
            # Final fallback
            params = self._extract_parameters(question)
            results = await self._fallback_search(params)
            answer = await self._generate_answer(question, results)

            return {
                "answer": answer,
                "results": results,
                "error": str(e) if e else "Unknown error occurred",
                "out_of_scope": False,
            }

    async def _generate_answer(
        self, question: str, results: list[dict[str, Any]]
    ) -> str:
        """Generate a natural language answer from results."""

        if not results:
            return "I couldn't find any hospitals matching your criteria. Please try different search terms or a broader location."

        # If OpenAI is not available, generate a simple answer
        if not self.client:
            if len(results) == 1:
                result = results[0]
                return f"I found {result['provider_name']} in {result['provider_city']}, {result['provider_state']}. The average covered charges for {result['ms_drg_definition']} is ${result['average_covered_charges']:,.2f}."
            else:
                top_result = results[0]
                return f"I found {len(results)} hospitals. The most affordable option is {top_result['provider_name']} in {top_result['provider_city']} with average charges of ${top_result['average_covered_charges']:,.2f}."

        # Generate answer using OpenAI
        system_prompt = """
        You are a helpful healthcare assistant. Generate a concise, natural language answer based on the database results.
        Focus on the most relevant information: hospital names, costs, ratings, and locations.
        Keep the answer under 200 words and be conversational.
        """

        results_text = "\n".join(
            [str(result) for result in results[:5]]
        )  # Limit to top 5 results

        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nResults: {results_text}",
                },
            ],
            temperature=0.7,
            max_tokens=300,
        )

        content = response.choices[0].message.content
        if content is None:
            return (
                "I couldn't generate a response. Please try rephrasing your question."
            )
        return content.strip()

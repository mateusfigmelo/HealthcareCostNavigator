"""ETL script for loading CMS hospital data."""

import asyncio
import csv
import random
import re
from typing import Any

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models import Hospital, Procedure, Rating


def extract_drg_code(drg_definition: str) -> str:
    """Extract DRG code from definition string."""
    if not drg_definition:
        return ""

    # Look for pattern like "470 – Major Joint Replacement w/o MCC"
    match = re.match(r"(\d+)\s*[–-]\s*(.+)", drg_definition.strip())
    if match:
        return match.group(1)

    # Fallback: look for any 3-digit number at the start
    match = re.match(r"(\d{3})", drg_definition.strip())
    if match:
        return match.group(1)

    return ""


def clean_string(value: str) -> str:
    """Clean and normalize string values."""
    if not value:
        return ""
    return value.strip().upper()


def parse_float(value: str) -> float:
    """Parse float value safely."""
    if not value:
        return 0.0
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return 0.0


def parse_int(value: str) -> int:
    """Parse integer value safely."""
    if not value:
        return 0
    try:
        return int(value.replace(",", ""))
    except ValueError:
        return 0


async def load_csv_data(file_path: str) -> list[dict[str, Any]]:
    """Load and parse CSV data asynchronously."""
    data = []

    # Try different encodings
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    content = None

    for encoding in encodings:
        try:
            async with aiofiles.open(file_path, mode="r", encoding=encoding) as file:
                content = await file.read()
                print(f"✓ Successfully read file with {encoding} encoding")
                break
        except UnicodeDecodeError:
            print(f"✗ Failed to read with {encoding} encoding, trying next...")
            continue
        except FileNotFoundError:
            print(f"✗ File {file_path} not found!")
            return []

    if content is None:
        print("✗ Could not read file with any encoding")
        return []

    # Parse CSV content
    reader = csv.DictReader(content.splitlines())

    for row in reader:
        # Map CSV column names to expected field names
        drg_code = clean_string(row.get("DRG_Cd", ""))
        drg_definition = clean_string(row.get("DRG_Desc", ""))

        # Skip rows with invalid data
        if not drg_code or not clean_string(row.get("Rndrng_Prvdr_CCN", "")):
            continue

        data.append(
            {
                "provider_id": clean_string(row.get("Rndrng_Prvdr_CCN", "")),
                "provider_name": clean_string(row.get("Rndrng_Prvdr_Org_Name", "")),
                "provider_city": clean_string(row.get("Rndrng_Prvdr_City", "")),
                "provider_state": clean_string(
                    row.get("Rndrng_Prvdr_State_Abrvtn", "")
                ),
                "provider_zip_code": clean_string(row.get("Rndrng_Prvdr_Zip5", "")),
                "ms_drg_code": drg_code,
                "ms_drg_definition": drg_definition,
                "total_discharges": parse_int(row.get("Tot_Dschrgs", "0")),
                "average_covered_charges": parse_float(
                    row.get("Avg_Submtd_Cvrd_Chrg", "0")
                ),
                "average_total_payments": parse_float(row.get("Avg_Tot_Pymt_Amt", "0")),
                "average_medicare_payments": parse_float(
                    row.get("Avg_Mdcr_Pymt_Amt", "0")
                ),
            }
        )

    return data


async def create_hospitals(
    session: AsyncSession, data: list[dict[str, Any]]
) -> dict[str, Hospital]:
    """Create hospital records and return mapping of provider_id to hospital."""
    hospitals = {}

    for row in data:
        provider_id = row["provider_id"]
        if provider_id and provider_id not in hospitals:
            hospital = Hospital(
                provider_id=provider_id,
                provider_name=row["provider_name"],
                provider_city=row["provider_city"],
                provider_state=row["provider_state"],
                provider_zip_code=row["provider_zip_code"],
            )
            hospitals[provider_id] = hospital
            session.add(hospital)

    await session.commit()
    return hospitals


async def create_procedures(session: AsyncSession, data: list[dict[str, Any]]) -> None:
    """Create procedure records."""
    for row in data:
        if row["provider_id"] and row["ms_drg_code"]:
            procedure = Procedure(
                provider_id=row["provider_id"],
                ms_drg_code=row["ms_drg_code"],
                ms_drg_definition=row["ms_drg_definition"],
                total_discharges=row["total_discharges"],
                average_covered_charges=row["average_covered_charges"],
                average_total_payments=row["average_total_payments"],
                average_medicare_payments=row["average_medicare_payments"],
            )
            session.add(procedure)

    await session.commit()


async def create_ratings(session: AsyncSession, provider_ids: list[str]) -> None:
    """Create random star ratings for each provider."""
    for provider_id in provider_ids:
        # Generate random rating between 1-10 with some distribution
        # Favor higher ratings (more realistic)
        rating = random.choices(
            range(1, 11),
            weights=[1, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # Higher weights for better ratings
        )[0]

        rating_record = Rating(provider_id=provider_id, rating=float(rating))
        session.add(rating_record)

    await session.commit()


async def main() -> None:
    """Main ETL function."""
    print("Starting ETL process...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load CSV data
    csv_file = "sample_prices_ny.csv"
    print(f"Loading data from {csv_file}...")
    data = await load_csv_data(csv_file)

    # If no data loaded, create sample data
    if not data:
        print("No CSV data found, creating sample data...")
        data = create_sample_data()
        print(f"Created {len(data)} sample records")
    else:
        print(f"Loaded {len(data)} records from CSV")

    # Process data in database session
    async with AsyncSessionLocal() as session:
        # Create hospitals
        print("Creating hospitals...")
        hospitals = await create_hospitals(session, data)
        print(f"Created {len(hospitals)} hospitals")

        # Create procedures
        print("Creating procedures...")
        await create_procedures(session, data)
        print(f"Created {len(data)} procedures")

        # Create ratings
        print("Creating ratings...")
        provider_ids = list(hospitals.keys())
        await create_ratings(session, provider_ids)
        print(f"Created ratings for {len(provider_ids)} providers")

    print("ETL process completed successfully!")


def create_sample_data() -> list[dict[str, Any]]:
    """Create sample data for testing when CSV is not available."""
    return [
        {
            "provider_id": "330123",
            "provider_name": "MOUNT SINAI HOSPITAL",
            "provider_city": "NEW YORK",
            "provider_state": "NY",
            "provider_zip_code": "10029",
            "ms_drg_code": "470",
            "ms_drg_definition": "470 – MAJOR JOINT REPLACEMENT W/O MCC",
            "total_discharges": 150,
            "average_covered_charges": 85000.0,
            "average_total_payments": 25000.0,
            "average_medicare_payments": 20000.0,
        },
        {
            "provider_id": "330124",
            "provider_name": "NYU LANGONE HOSPITAL",
            "provider_city": "NEW YORK",
            "provider_state": "NY",
            "provider_zip_code": "10016",
            "ms_drg_code": "470",
            "ms_drg_definition": "470 – MAJOR JOINT REPLACEMENT W/O MCC",
            "total_discharges": 120,
            "average_covered_charges": 92000.0,
            "average_total_payments": 28000.0,
            "average_medicare_payments": 22000.0,
        },
        {
            "provider_id": "330125",
            "provider_name": "LENOX HILL HOSPITAL",
            "provider_city": "NEW YORK",
            "provider_state": "NY",
            "provider_zip_code": "10021",
            "ms_drg_code": "470",
            "ms_drg_definition": "470 – MAJOR JOINT REPLACEMENT W/O MCC",
            "total_discharges": 80,
            "average_covered_charges": 78000.0,
            "average_total_payments": 22000.0,
            "average_medicare_payments": 18000.0,
        },
        {
            "provider_id": "330126",
            "provider_name": "BROOKLYN HOSPITAL CENTER",
            "provider_city": "BROOKLYN",
            "provider_state": "NY",
            "provider_zip_code": "11201",
            "ms_drg_code": "470",
            "ms_drg_definition": "470 – MAJOR JOINT REPLACEMENT W/O MCC",
            "total_discharges": 60,
            "average_covered_charges": 65000.0,
            "average_total_payments": 18000.0,
            "average_medicare_payments": 15000.0,
        },
        {
            "provider_id": "330127",
            "provider_name": "MONTEFIORE MEDICAL CENTER",
            "provider_city": "BRONX",
            "provider_state": "NY",
            "provider_zip_code": "10467",
            "ms_drg_code": "470",
            "ms_drg_definition": "470 – MAJOR JOINT REPLACEMENT W/O MCC",
            "total_discharges": 90,
            "average_covered_charges": 72000.0,
            "average_total_payments": 20000.0,
            "average_medicare_payments": 17000.0,
        },
        # Add some heart procedures
        {
            "provider_id": "330123",
            "provider_name": "MOUNT SINAI HOSPITAL",
            "provider_city": "NEW YORK",
            "provider_state": "NY",
            "provider_zip_code": "10029",
            "ms_drg_code": "291",
            "ms_drg_definition": "291 – HEART FAILURE AND SHOCK W/O MCC",
            "total_discharges": 200,
            "average_covered_charges": 45000.0,
            "average_total_payments": 15000.0,
            "average_medicare_payments": 12000.0,
        },
        {
            "provider_id": "330124",
            "provider_name": "NYU LANGONE HOSPITAL",
            "provider_city": "NEW YORK",
            "provider_state": "NY",
            "provider_zip_code": "10016",
            "ms_drg_code": "291",
            "ms_drg_definition": "291 – HEART FAILURE AND SHOCK W/O MCC",
            "total_discharges": 180,
            "average_covered_charges": 48000.0,
            "average_total_payments": 16000.0,
            "average_medicare_payments": 13000.0,
        },
    ]


if __name__ == "__main__":
    asyncio.run(main())

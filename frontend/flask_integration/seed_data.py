#!/usr/bin/env python3
"""
MERIT Data Seeder
=================
Load your existing nonprofit data into the MERIT database.

Usage:
    # From CSV
    python flask_integration/seed_data.py --source data/my_orgs.csv --format csv

    # From JSON
    python flask_integration/seed_data.py --source data/my_orgs.json --format json

    # From existing database table
    python flask_integration/seed_data.py --from-table old_orgs_table

CSV Format Expected:
    id,name,ein,city,state,category,subcategory,merit_score,revenue,assets,
    employees,founded,mission,programs,leadership,board_size,revenue_trend,
    program_efficiency,fundraising_ratio,operating_reserve,transparency_score

Programs/Leadership/Revenue Trend columns can be JSON strings or comma-separated.
"""

import os
import sys
import csv
import json
import argparse
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///data/merit.db')
engine = create_engine(DATABASE_URL)


def parse_json_field(value, default=None):
    """Try to parse a field as JSON, fall back to other formats."""
    if not value:
        return default if default is not None else []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        # Try comma-separated
        return [v.strip() for v in str(value).split(',') if v.strip()]


def seed_from_csv(filepath):
    """Load data from a CSV file."""
    with engine.connect() as conn:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    conn.execute(text("""
                        INSERT OR REPLACE INTO organizations
                        (id, name, ein, city, state, category, subcategory, merit_score,
                         revenue, assets, employees, founded, mission, programs, leadership,
                         board_size, revenue_trend, program_efficiency, fundraising_ratio,
                         operating_reserve, transparency_score, created_at, updated_at)
                        VALUES (:id, :name, :ein, :city, :state, :category, :subcategory,
                                :merit_score, :revenue, :assets, :employees, :founded,
                                :mission, :programs, :leadership, :board_size, :revenue_trend,
                                :program_efficiency, :fundraising_ratio, :operating_reserve,
                                :transparency_score, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """), {
                        "id": row.get('id', str(count)),
                        "name": row.get('name', ''),
                        "ein": row.get('ein', ''),
                        "city": row.get('city', ''),
                        "state": row.get('state', ''),
                        "category": row.get('category', ''),
                        "subcategory": row.get('subcategory', row.get('category', '')),
                        "merit_score": int(row['merit_score']) if row.get('merit_score') else 0,
                        "revenue": int(float(row['revenue'])) if row.get('revenue') else 0,
                        "assets": int(float(row['assets'])) if row.get('assets') else 0,
                        "employees": int(row['employees']) if row.get('employees') else 0,
                        "founded": int(row['founded']) if row.get('founded') else 0,
                        "mission": row.get('mission', ''),
                        "programs": json.dumps(parse_json_field(row.get('programs'))),
                        "leadership": json.dumps(parse_json_field(row.get('leadership'))),
                        "board_size": int(row['board_size']) if row.get('board_size') else 0,
                        "revenue_trend": json.dumps(parse_json_field(row.get('revenue_trend'))),
                        "program_efficiency": int(row['program_efficiency']) if row.get('program_efficiency') else 0,
                        "fundraising_ratio": int(row['fundraising_ratio']) if row.get('fundraising_ratio') else 0,
                        "operating_reserve": float(row['operating_reserve']) if row.get('operating_reserve') else 0,
                        "transparency_score": int(row['transparency_score']) if row.get('transparency_score') else 0,
                    })
                    count += 1
                    if count % 100 == 0:
                        print(f"  Inserted {count} records...")
                except Exception as e:
                    print(f"  Error on row {count}: {e}")
                    continue

        conn.commit()
    print(f"Loaded {count} organizations from {filepath}")


def seed_from_json(filepath):
    """Load data from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    organizations = data if isinstance(data, list) else data.get('organizations', [])

    with engine.connect() as conn:
        count = 0
        for org in organizations:
            try:
                conn.execute(text("""
                    INSERT OR REPLACE INTO organizations
                    (id, name, ein, city, state, category, subcategory, merit_score,
                     revenue, assets, employees, founded, mission, programs, leadership,
                     board_size, revenue_trend, program_efficiency, fundraising_ratio,
                     operating_reserve, transparency_score, created_at, updated_at)
                    VALUES (:id, :name, :ein, :city, :state, :category, :subcategory,
                            :merit_score, :revenue, :assets, :employees, :founded,
                            :mission, :programs, :leadership, :board_size, :revenue_trend,
                            :program_efficiency, :fundraising_ratio, :operating_reserve,
                            :transparency_score, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), {
                    "id": str(org.get('id', count)),
                    "name": org.get('name', ''),
                    "ein": org.get('ein', ''),
                    "city": org.get('city', ''),
                    "state": org.get('state', ''),
                    "category": org.get('category', ''),
                    "subcategory": org.get('subcategory', org.get('category', '')),
                    "merit_score": org.get('merit_score', 0),
                    "revenue": org.get('revenue', 0),
                    "assets": org.get('assets', 0),
                    "employees": org.get('employees', 0),
                    "founded": org.get('founded', 0),
                    "mission": org.get('mission', ''),
                    "programs": json.dumps(org.get('programs', [])),
                    "leadership": json.dumps(org.get('leadership', [])),
                    "board_size": org.get('board_size', 0),
                    "revenue_trend": json.dumps(org.get('revenue_trend', [])),
                    "program_efficiency": org.get('program_efficiency', 0),
                    "fundraising_ratio": org.get('fundraising_ratio', 0),
                    "operating_reserve": org.get('operating_reserve', 0),
                    "transparency_score": org.get('transparency_score', 0),
                })
                count += 1
            except Exception as e:
                print(f"  Error on org {org.get('name', count)}: {e}")
                continue

        conn.commit()
    print(f"Loaded {count} organizations from {filepath}")


def seed_from_table(table_name):
    """Migrate data from an existing table in the same database."""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table_name}"))
        count = 0
        for row in result.mappings():
            try:
                row_dict = dict(row)
                # Map common column name variations
                field_map = {
                    'org_id': 'id',
                    'org_name': 'name',
                    'employer_id': 'ein',
                    'ntee_code': 'category',
                    'score': 'merit_score',
                }
                for old, new in field_map.items():
                    if old in row_dict and new not in row_dict:
                        row_dict[new] = row_dict.pop(old)

                conn.execute(text("""
                    INSERT OR REPLACE INTO organizations
                    (id, name, ein, city, state, category, subcategory, merit_score,
                     revenue, assets, employees, founded, mission, created_at, updated_at)
                    VALUES (:id, :name, :ein, :city, :state, :category, :subcategory,
                            :merit_score, :revenue, :assets, :employees, :founded,
                            :mission, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), row_dict)
                count += 1
            except Exception as e:
                print(f"  Error on row {count}: {e}")
                continue

        conn.commit()
    print(f"Migrated {count} organizations from table `{table_name}`")


def seed_sample_data():
    """Insert 18 sample organizations for testing."""
    sample_orgs = [
        {"id": "1", "name": "United Way Worldwide", "ein": "13-1635294", "city": "Alexandria", "state": "VA", "category": "human-services", "subcategory": "Human Services", "merit_score": 94, "revenue": 4800000000, "assets": 4200000000, "employees": 3200, "founded": 1887, "mission": "To improve lives by mobilizing the caring power of communities around the world to advance the common good.", "programs": ["Education", "Financial Stability", "Health", "Disaster Response"], "leadership": [{"name": "Angela F. Williams", "title": "President & CEO", "initials": "AW"}], "board_size": 18, "revenue_trend": [{"year": 2020, "amount": 4100000000}, {"year": 2021, "amount": 4500000000}, {"year": 2022, "amount": 4700000000}, {"year": 2023, "amount": 4800000000}, {"year": 2024, "amount": 4900000000}], "program_efficiency": 91, "fundraising_ratio": 8, "operating_reserve": 11.2, "transparency_score": 96},
        {"id": "2", "name": "Teach For America", "ein": "13-1624016", "city": "New York", "state": "NY", "category": "education", "subcategory": "Education", "merit_score": 92, "revenue": 350000000, "assets": 450000000, "employees": 2500, "founded": 1989, "mission": "Teach For America finds, develops, and supports a diverse network of leaders who expand opportunity for children from classrooms, schools, and every sector that shapes the broader systems in which schools operate.", "programs": ["Teacher Corps", "Alumni Leadership", "Policy & Advocacy"], "leadership": [{"name": "Elisa Villanueva Beard", "title": "CEO", "initials": "EV"}], "board_size": 22, "revenue_trend": [{"year": 2020, "amount": 310000000}, {"year": 2021, "amount": 330000000}, {"year": 2022, "amount": 340000000}, {"year": 2023, "amount": 350000000}, {"year": 2024, "amount": 355000000}], "program_efficiency": 88, "fundraising_ratio": 10, "operating_reserve": 9.8, "transparency_score": 94},
        {"id": "3", "name": "The Nature Conservancy", "ein": "23-7923164", "city": "Arlington", "state": "VA", "category": "environment", "subcategory": "Environment", "merit_score": 95, "revenue": 1200000000, "assets": 8900000000, "employees": 4800, "founded": 1951, "mission": "To conserve the lands and waters on which all life depends.", "programs": ["Climate Change", "Water Conservation", "Land Protection", "Ocean Health"], "leadership": [{"name": "Jennifer Morris", "title": "CEO", "initials": "JM"}], "board_size": 19, "revenue_trend": [{"year": 2020, "amount": 950000000}, {"year": 2021, "amount": 1050000000}, {"year": 2022, "amount": 1120000000}, {"year": 2023, "amount": 1200000000}, {"year": 2024, "amount": 1250000000}], "program_efficiency": 87, "fundraising_ratio": 9, "operating_reserve": 14.6, "transparency_score": 95},
        {"id": "4", "name": "Metropolitan Museum of Art", "ein": "13-1624082", "city": "New York", "state": "NY", "category": "arts", "subcategory": "Arts & Culture", "merit_score": 89, "revenue": 420000000, "assets": 3100000000, "employees": 2200, "founded": 1870, "mission": "To connect people to creativity, knowledge, and ideas.", "programs": ["Exhibitions", "Education", "Conservation", "Digital Initiatives"], "leadership": [{"name": "Max Hollein", "title": "Director & CEO", "initials": "MH"}], "board_size": 41, "revenue_trend": [{"year": 2020, "amount": 280000000}, {"year": 2021, "amount": 340000000}, {"year": 2022, "amount": 380000000}, {"year": 2023, "amount": 420000000}, {"year": 2024, "amount": 445000000}], "program_efficiency": 82, "fundraising_ratio": 14, "operating_reserve": 18.3, "transparency_score": 91},
        {"id": "5", "name": "Doctors Without Borders", "ein": "13-1623456", "city": "New York", "state": "NY", "category": "health", "subcategory": "Health & Research", "merit_score": 97, "revenue": 580000000, "assets": 320000000, "employees": 45000, "founded": 1971, "mission": "To provide impartial medical relief to the victims of war, disease, and natural or man-made disaster, without regard to race, religion, or political affiliation.", "programs": ["Emergency Response", "Vaccination Campaigns", "Mental Health", "Surgery"], "leadership": [{"name": "Avril Benoit", "title": "Executive Director", "initials": "AB"}], "board_size": 12, "revenue_trend": [{"year": 2020, "amount": 420000000}, {"year": 2021, "amount": 510000000}, {"year": 2022, "amount": 540000000}, {"year": 2023, "amount": 580000000}, {"year": 2024, "amount": 600000000}], "program_efficiency": 94, "fundraising_ratio": 6, "operating_reserve": 7.4, "transparency_score": 98},
        {"id": "8", "name": "St. Jude Children's Research Hospital", "ein": "13-1625469", "city": "Memphis", "state": "TN", "category": "health", "subcategory": "Health & Research", "merit_score": 98, "revenue": 2100000000, "assets": 6500000000, "employees": 4800, "founded": 1962, "mission": "Finding cures. Saving children.", "programs": ["Pediatric Cancer Research", "Patient Care", "Global Outreach", "Research Publications"], "leadership": [{"name": "James R. Downing", "title": "President & CEO", "initials": "JD"}], "board_size": 23, "revenue_trend": [{"year": 2020, "amount": 1800000000}, {"year": 2021, "amount": 1950000000}, {"year": 2022, "amount": 2050000000}, {"year": 2023, "amount": 2100000000}, {"year": 2024, "amount": 2200000000}], "program_efficiency": 92, "fundraising_ratio": 7, "operating_reserve": 22.1, "transparency_score": 99},
        {"id": "9", "name": "Khan Academy", "ein": "26-1544963", "city": "Mountain View", "state": "CA", "category": "education", "subcategory": "Education", "merit_score": 96, "revenue": 85000000, "assets": 120000000, "employees": 180, "founded": 2006, "mission": "To provide a free, world-class education for anyone, anywhere.", "programs": ["K-12 Curriculum", "Test Preparation", "Computer Science", "Language Learning"], "leadership": [{"name": "Sal Khan", "title": "Founder & CEO", "initials": "SK"}], "board_size": 9, "revenue_trend": [{"year": 2020, "amount": 52000000}, {"year": 2021, "amount": 68000000}, {"year": 2022, "amount": 75000000}, {"year": 2023, "amount": 85000000}, {"year": 2024, "amount": 92000000}], "program_efficiency": 96, "fundraising_ratio": 4, "operating_reserve": 16.8, "transparency_score": 97},
        {"id": "12", "name": "Feeding America", "ein": "13-1625537", "city": "Chicago", "state": "IL", "category": "human-services", "subcategory": "Human Services", "merit_score": 93, "revenue": 4200000000, "assets": 280000000, "employees": 350, "founded": 1979, "mission": "To feed America's hungry through a nationwide network of member food banks and engage our country in the fight to end hunger.", "programs": ["Food Distribution", "Advocacy", "Research", "Disaster Response"], "leadership": [{"name": "Claire Babineaux-Fontenot", "title": "CEO", "initials": "CB"}], "board_size": 17, "revenue_trend": [{"year": 2020, "amount": 3800000000}, {"year": 2021, "amount": 4100000000}, {"year": 2022, "amount": 4200000000}, {"year": 2023, "amount": 4200000000}, {"year": 2024, "amount": 4300000000}], "program_efficiency": 98, "fundraising_ratio": 3, "operating_reserve": 3.2, "transparency_score": 95},
        {"id": "13", "name": "American Red Cross", "ein": "53-0196605", "city": "Washington", "state": "DC", "category": "human-services", "subcategory": "Human Services", "merit_score": 90, "revenue": 3800000000, "assets": 4600000000, "employees": 22000, "founded": 1881, "mission": "To prevent and alleviate human suffering in the face of emergencies by mobilizing the power of volunteers and the generosity of donors.", "programs": ["Disaster Relief", "Blood Services", "Training & Certification", "International Services"], "leadership": [{"name": "Gail J. McGovern", "title": "President & CEO", "initials": "GM"}], "board_size": 25, "revenue_trend": [{"year": 2020, "amount": 3200000000}, {"year": 2021, "amount": 3500000000}, {"year": 2022, "amount": 3600000000}, {"year": 2023, "amount": 3800000000}, {"year": 2024, "amount": 3900000000}], "program_efficiency": 89, "fundraising_ratio": 9, "operating_reserve": 10.5, "transparency_score": 92},
    ]

    with engine.connect() as conn:
        for org in sample_orgs:
            conn.execute(text("""
                INSERT OR REPLACE INTO organizations
                (id, name, ein, city, state, category, subcategory, merit_score,
                 revenue, assets, employees, founded, mission, programs, leadership,
                 board_size, revenue_trend, program_efficiency, fundraising_ratio,
                 operating_reserve, transparency_score, created_at, updated_at)
                VALUES (:id, :name, :ein, :city, :state, :category, :subcategory,
                        :merit_score, :revenue, :assets, :employees, :founded,
                        :mission, :programs, :leadership, :board_size, :revenue_trend,
                        :program_efficiency, :fundraising_ratio, :operating_reserve,
                        :transparency_score, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {
                **org,
                "programs": json.dumps(org["programs"]),
                "leadership": json.dumps(org["leadership"]),
                "revenue_trend": json.dumps(org["revenue_trend"]),
            })
        conn.commit()

    print(f"Inserted {len(sample_orgs)} sample organizations")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed MERIT database with nonprofit data')
    parser.add_argument('--source', help='Path to data file (CSV or JSON)')
    parser.add_argument('--format', choices=['csv', 'json'], help='Data format')
    parser.add_argument('--from-table', help='Migrate from existing table name')
    parser.add_argument('--sample', action='store_true', help='Load sample data for testing')
    args = parser.parse_args()

    if args.source:
        fmt = args.format or ('json' if args.source.endswith('.json') else 'csv')
        if fmt == 'csv':
            seed_from_csv(args.source)
        else:
            seed_from_json(args.source)
    elif args.from_table:
        seed_from_table(args.from_table)
    elif args.sample:
        seed_sample_data()
    else:
        print("Usage:")
        print("  python seed_data.py --source data.csv --format csv")
        print("  python seed_data.py --source data.json")
        print("  python seed_data.py --from-table old_orgs")
        print("  python seed_data.py --sample")

import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

DEFAULT_DB_PATH = Path("data/database/aml_transactions.db")

def init_database(db_path: Path = DEFAULT_DB_PATH):
    """Initializes and seeds the mock banking database with realistic AML patterns."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop existing tables for fresh seed
    cursor.execute("DROP TABLE IF EXISTS transactions;")
    cursor.execute("DROP TABLE IF EXISTS accounts;")
    cursor.execute("DROP TABLE IF EXISTS entities;")
    cursor.execute("DROP TABLE IF EXISTS sanctions_list;")

    # 1. Accounts Table
    cursor.execute("""
    CREATE TABLE accounts (
        account_id TEXT PRIMARY KEY,
        account_name TEXT NOT NULL,
        account_type TEXT NOT NULL,
        country TEXT NOT NULL,
        risk_rating TEXT NOT NULL,
        balance REAL NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Transactions Table
    cursor.execute("""
    CREATE TABLE transactions (
        transaction_id TEXT PRIMARY KEY,
        source_account TEXT NOT NULL,
        dest_account TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        is_flagged INTEGER DEFAULT 0,
        flag_reason TEXT,
        FOREIGN KEY (source_account) REFERENCES accounts (account_id),
        FOREIGN KEY (dest_account) REFERENCES accounts (account_id)
    );
    """)

    # 3. Entities Table (Graph Links / UBOs)
    cursor.execute("""
    CREATE TABLE entities (
        entity_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        associated_accounts TEXT NOT NULL,
        jurisdiction TEXT NOT NULL,
        ultimate_beneficial_owner TEXT,
        phone_number TEXT,
        address TEXT
    );
    """)

    # 4. Sanctions Watchlist Table
    cursor.execute("""
    CREATE TABLE sanctions_list (
        sanction_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        aliases TEXT,
        country TEXT NOT NULL,
        program TEXT NOT NULL,
        listing_date TEXT NOT NULL,
        notes TEXT
    );
    """)

    # --- SEED DATA ---
    now = datetime.now()

    # Seed Accounts
    accounts_data = [
        # Suspect 1: Structuring / Smurfing Subject
        ("ACC-883910", "Derrick Sterling / Apex Horizon LLC", "BUSINESS_CHECKING", "USA", "HIGH", 1450.00, (now - timedelta(days=120)).isoformat()),
        ("ACC-110294", "First National Cash Vault", "INTERNAL_TRANSIT", "USA", "LOW", 9999999.00, (now - timedelta(days=500)).isoformat()),
        ("ACC-992014", "Bluecrest Maritime Holdings Ltd", "OFFSHORE_CORP", "CYPRUS", "HIGH", 420000.00, (now - timedelta(days=45)).isoformat()),
        
        # Suspect 2: Layering Ring
        ("ACC-449102", "Elena Rostova Import-Export", "BUSINESS_CHECKING", "USA", "HIGH", 8500.00, (now - timedelta(days=200)).isoformat()),
        ("ACC-552109", "Vanguard Logistics FZE", "CORPORATE", "UAE", "HIGH", 610000.00, (now - timedelta(days=90)).isoformat()),
        
        # Legitimate Baseline Account
        ("ACC-100001", "Acme Retail Store Inc", "COMMERCIAL", "USA", "LOW", 45000.00, (now - timedelta(days=1000)).isoformat()),
        ("ACC-100002", "Standard Supplier Co", "COMMERCIAL", "USA", "LOW", 12000.00, (now - timedelta(days=800)).isoformat()),
    ]
    cursor.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?);", accounts_data)

    # Seed Suspicious Transactions (Structuring: 4 cash deposits below $10,000 threshold within 48h, then offshore wire)
    tx_data = [
        # Structuring pattern into ACC-883910
        ("TX-9901", "ACC-110294", "ACC-883910", 9400.00, "USD", "CASH_DEPOSIT", (now - timedelta(hours=46)).strftime("%Y-%m-%d %H:%M:%S"), 1, "Pattern: Cash deposit just below $10,000 CTR reporting threshold"),
        ("TX-9902", "ACC-110294", "ACC-883910", 9850.00, "USD", "CASH_DEPOSIT", (now - timedelta(hours=34)).strftime("%Y-%m-%d %H:%M:%S"), 1, "Pattern: Cash deposit just below $10,000 CTR reporting threshold"),
        ("TX-9903", "ACC-110294", "ACC-883910", 9200.00, "USD", "CASH_DEPOSIT", (now - timedelta(hours=22)).strftime("%Y-%m-%d %H:%M:%S"), 1, "Pattern: Cash deposit just below $10,000 CTR reporting threshold"),
        ("TX-9904", "ACC-110294", "ACC-883910", 9750.00, "USD", "CASH_DEPOSIT", (now - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S"), 1, "Pattern: Cash deposit just below $10,000 CTR reporting threshold"),
        # Immediate outbound wire to Cyprus offshore entity
        ("TX-9905", "ACC-883910", "ACC-992014", 37500.00, "USD", "WIRE_OUTBOUND", (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"), 1, "Rapid movement of structured funds to high-risk offshore jurisdiction"),
        
        # Layering transactions for Suspect 2
        ("TX-7701", "ACC-449102", "ACC-552109", 150000.00, "USD", "WIRE_OUTBOUND", (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), 1, "Large round dollar international wire to high-risk free-zone entity"),
        
        # Normal baseline transactions
        ("TX-1001", "ACC-100001", "ACC-100002", 3420.50, "USD", "ACH_PAYMENT", (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"), 0, None),
        ("TX-1002", "ACC-100001", "ACC-100002", 4810.00, "USD", "ACH_PAYMENT", (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), 0, None),
    ]
    cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", tx_data)

    # Seed Entities & Graph linkages
    entities_data = [
        ("ENT-001", "Derrick Sterling", "INDIVIDUAL", "ACC-883910", "USA", "Derrick Sterling", "+1-212-555-0199", "742 Evergreen Terrace, New York, NY"),
        ("ENT-002", "Apex Horizon LLC", "SHELL_CORP", "ACC-883910", "DELAWARE, USA", "Derrick Sterling", "+1-212-555-0199", "1209 Orange St, Wilmington, DE"),
        ("ENT-003", "Bluecrest Maritime Holdings Ltd", "OFFSHORE_CORP", "ACC-992014", "CYPRUS", "Viktor Krumov", "+357-22-123456", "Spyrou Kyprianou Ave, Limassol, Cyprus"),
        ("ENT-004", "Elena Rostova", "INDIVIDUAL", "ACC-449102", "USA", "Elena Rostova", "+1-305-555-0144", "100 Biscayne Blvd, Miami, FL"),
        ("ENT-005", "Vanguard Logistics FZE", "CORPORATE", "ACC-552109", "UAE", "Elena Rostova", "+971-4-8812345", "Jebel Ali Free Zone, Dubai, UAE")
    ]
    cursor.executemany("INSERT INTO entities VALUES (?, ?, ?, ?, ?, ?, ?, ?);", entities_data)

    # Seed Sanctions Watchlist (OFAC SDN mock)
    sanctions_data = [
        ("SANC-001", "Viktor Krumov", "Victor Krumoff, V. Krumov", "RUSSIA/CYPRUS", "OFAC-RUSSIA-EO14024", "2023-04-12", "Designated for maritime evasion of oil price caps and shell company networks."),
        ("SANC-002", "PetroTrans Global Corp", "PTG Limited", "IRAN/PANAMA", "OFAC-IRAN-EO13846", "2022-09-15", "Front company facilitating illicit petroleum shipments."),
        ("SANC-003", "Al-Baraka Money Exchange", "Baraka Hawala", "SOMALIA", "UN-SOMALIA-RES751", "2021-11-20", "Informal value transfer system associated with illicit financing.")
    ]
    cursor.executemany("INSERT INTO sanctions_list VALUES (?, ?, ?, ?, ?, ?, ?);", sanctions_data)

    conn.commit()
    conn.close()
    print(f"Mock AML database initialized successfully at: {db_path.resolve()}")

if __name__ == "__main__":
    init_database()

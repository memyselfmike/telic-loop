#!/usr/bin/env python3
"""
Verification: Database layer - schema creation, idempotency, foreign keys
PRD Reference: Section 2 (Database Schema)
Vision Goal: Trust the Data - all data persists, FK integrity enforced
Category: unit
"""
import sys
import os
import tempfile
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

print("=== Unit: Database Layer ===")

SPRINT_DIR = os.path.join(os.path.dirname(__file__), '..', '..')

# Add backend to path
backend_dir = os.path.join(SPRINT_DIR, 'backend')
sys.path.insert(0, os.path.dirname(SPRINT_DIR))
sys.path.insert(0, SPRINT_DIR)

try:
    from backend.database import init_db, get_db_path
    print("PASS: database module imports successfully")
except ImportError as e:
    print(f"FAIL: Cannot import backend.database: {e}")
    sys.exit(1)

# Test 1: init_db creates tables
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    test_db = f.name

try:
    os.unlink(test_db)  # Remove so init_db creates it fresh
except FileNotFoundError:
    pass

try:
    init_db(test_db)
    print("PASS: init_db() runs without error")
except Exception as e:
    print(f"FAIL: init_db() raised: {e}")
    sys.exit(1)

# Test 2: Both tables exist with correct columns
conn = sqlite3.connect(test_db)
try:
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    
    if 'projects' not in tables:
        print(f"FAIL: 'projects' table missing. Found: {tables}")
        sys.exit(1)
    print("PASS: projects table exists")
    
    if 'time_entries' not in tables:
        print(f"FAIL: 'time_entries' table missing. Found: {tables}")
        sys.exit(1)
    print("PASS: time_entries table exists")

    # Test 3: projects table columns
    cursor = conn.execute("PRAGMA table_info(projects)")
    cols = {row[1] for row in cursor.fetchall()}
    required_cols = {'id', 'name', 'client_name', 'hourly_rate', 'color', 'archived', 'created_at', 'updated_at'}
    missing = required_cols - cols
    if missing:
        print(f"FAIL: projects missing columns: {missing}")
        sys.exit(1)
    print(f"PASS: projects table has all required columns: {required_cols}")

    # Test 4: time_entries table columns
    cursor = conn.execute("PRAGMA table_info(time_entries)")
    cols = {row[1] for row in cursor.fetchall()}
    required_cols = {'id', 'project_id', 'description', 'start_time', 'end_time', 'duration_seconds', 'created_at', 'updated_at'}
    missing = required_cols - cols
    if missing:
        print(f"FAIL: time_entries missing columns: {missing}")
        sys.exit(1)
    print(f"PASS: time_entries table has all required columns: {required_cols}")

    # Test 5: Foreign key on time_entries.project_id
    cursor = conn.execute("PRAGMA foreign_key_list(time_entries)")
    fks = cursor.fetchall()
    if not fks:
        print("FAIL: time_entries has no foreign keys defined")
        sys.exit(1)
    fk_tables = {row[2] for row in fks}
    if 'projects' not in fk_tables:
        print(f"FAIL: time_entries FK does not reference projects. Found: {fks}")
        sys.exit(1)
    print("PASS: time_entries has foreign key referencing projects")

    # Test 6: Foreign keys enforced
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("INSERT INTO time_entries (project_id, start_time) VALUES (999, '2026-02-17T10:00:00')")
        conn.commit()
        print("FAIL: FK not enforced - inserted time_entry with non-existent project_id")
        sys.exit(1)
    except sqlite3.IntegrityError:
        print("PASS: Foreign key constraint enforced")

finally:
    conn.close()

# Test 7: Idempotency - calling init_db twice does not error
try:
    init_db(test_db)
    init_db(test_db)
    print("PASS: init_db() is idempotent (can be called multiple times)")
except Exception as e:
    print(f"FAIL: init_db() not idempotent: {e}")
    sys.exit(1)
finally:
    try:
        os.unlink(test_db)
    except FileNotFoundError:
        pass

# Test 8: data/ directory auto-created
data_dir = os.path.join(SPRINT_DIR, 'data')
if not os.path.isdir(data_dir):
    print(f"FAIL: data/ directory not auto-created at {data_dir}")
    sys.exit(1)
print("PASS: data/ directory exists")

print("\n=== ALL DATABASE UNIT TESTS PASSED ===")
sys.exit(0)

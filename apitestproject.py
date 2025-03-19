import requests
import pytest
import logging
import json
import sqlite3
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='api_test.log', filemode='w')

# Updated API URL
BASE_URL = "https://reqres.in/api"

# Sample endpoints to test
ENDPOINTS = {
    "users": "/users",
    "unknown": "/unknown",
    "register": "/register"
}

# Database setup
db_connection = sqlite3.connect("api_test.db")
db_cursor = db_connection.cursor()
db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        status_code INTEGER,
        response TEXT
    )
""")
db_connection.commit()

def log_response(response):
    """Log API responses for debugging and store them in the database."""
    logging.info(f"Request URL: {response.url}")
    logging.info(f"Status Code: {response.status_code}")
    logging.info(f"Response: {json.dumps(response.json(), indent=2)[:500]}")  # Log first 500 chars
    
    db_cursor.execute("INSERT INTO api_logs (url, status_code, response) VALUES (?, ?, ?)",
                      (response.url, response.status_code, json.dumps(response.json())[:500]))
    db_connection.commit()

def retrieve_logged_responses():
    """Retrieve stored API logs from the database."""
    db_cursor.execute("SELECT * FROM api_logs")
    logs = db_cursor.fetchall()
    return logs

def analyze_response_statuses():
    """Analyze stored API responses to find trends in status codes."""
    db_cursor.execute("SELECT status_code FROM api_logs")
    status_codes = [row[0] for row in db_cursor.fetchall()]
    status_distribution = Counter(status_codes)
    print("Status Code Distribution:")
    for code, count in status_distribution.items():
        print(f"Status {code}: {count} occurrences")

@pytest.mark.parametrize("endpoint", ENDPOINTS.values())
def test_api_response_status(endpoint):
    """Test if API endpoints return a successful response."""
    response = requests.get(BASE_URL + endpoint)
    log_response(response)
    assert response.status_code == 200, f"Failed at {endpoint}, Status Code: {response.status_code}"

@pytest.mark.parametrize("endpoint", ENDPOINTS.values())
def test_api_json_format(endpoint):
    """Test if API responses are in JSON format."""
    response = requests.get(BASE_URL + endpoint)
    log_response(response)
    assert response.headers["Content-Type"].startswith("application/json"), "Response is not JSON"
    assert isinstance(response.json(), dict), "Response JSON format is incorrect"

def test_create_user():
    """Test creating a new user."""
    new_user = {
        "name": "John Doe",
        "job": "Software Engineer"
    }
    response = requests.post(f"{BASE_URL}/users", json=new_user)
    log_response(response)
    assert response.status_code == 201, "User creation failed"
    data = response.json()
    assert data["name"] == new_user["name"], "Name mismatch"
    assert data["job"] == new_user["job"], "Job mismatch"

def test_database_logging():
    """Verify that database logging is working correctly."""
    db_cursor.execute("SELECT COUNT(*) FROM api_logs")
    count = db_cursor.fetchone()[0]
    assert count > 0, "Database log should not be empty"

def test_retrieve_logged_responses():
    """Test retrieval of logged API responses from the database."""
    logs = retrieve_logged_responses()
    assert len(logs) > 0, "No logs found in the database"
    for log in logs:
        print(log)

def test_analyze_response_statuses():
    """Test the response status analysis function."""
    analyze_response_statuses()

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])
    analyze_response_statuses()
    
    # Close database connection
    db_connection.close()

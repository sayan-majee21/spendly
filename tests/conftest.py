import os
import pytest

# SET THIS BEFORE ANY OTHER IMPORTS
os.environ["DB_NAME"] = "test_spendly.db"

from app import app
from database.db import init_db

@pytest.fixture
def client():
    """Provides a test client with a fresh database for each test function."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    
    # Ensure a fresh database for each test
    if os.path.exists("test_spendly.db"):
        os.remove("test_spendly.db")
    
    with app.app_context():
        init_db()
    
    with app.test_client() as client:
        yield client
    
    # Cleanup
    if os.path.exists("test_spendly.db"):
        os.remove("test_spendly.db")

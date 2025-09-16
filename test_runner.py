"""
Simple test runner for the database functionality.
"""

import sys
import os
import tempfile
import subprocess

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_tests():
    """Run the database tests."""
    print("Running database tests...")

    # Run pytest
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        'tests/database/',
        '-v',
        '--tb=short',
        '--color=yes'
    ], capture_output=True, text=True)

    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")

    return result.returncode == 0

def test_basic_functionality():
    """Test basic database functionality without pytest."""
    print("Testing basic database functionality...")

    try:
        # Import our modules
        from src.email_priority_manager.database.schema import DatabaseSchema
        from src.email_priority_manager.database.search import EmailSearch
        from src.email_priority_manager.database.indexes import DatabaseIndexManager
        from src.email_priority_manager.database.queries import EmailQueries
        from src.email_priority_manager.database.connections import DatabaseManager

        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            db_path = temp_db.name

        try:
            # Test schema initialization
            print("1. Testing schema initialization...")
            schema = DatabaseSchema(db_path)
            schema.initialize_database()
            print("   ✓ Schema initialized successfully")

            # Test database manager
            print("2. Testing database manager...")
            db_manager = DatabaseManager()
            db_manager.config.db_path = db_path
            db_manager.initialize_database()
            print("   ✓ Database manager initialized successfully")

            # Test search functionality
            print("3. Testing search functionality...")
            search = EmailSearch(db_path)
            results = search.search("test")
            print(f"   ✓ Search functionality works (found {len(results)} results)")

            # Test index manager
            print("4. Testing index manager...")
            index_manager = DatabaseIndexManager(db_path)
            index_manager.create_all_indexes()
            stats = index_manager.get_index_stats()
            print(f"   ✓ Index manager works (created {stats['total_indexes']} indexes)")

            # Test queries
            print("5. Testing queries...")
            queries = EmailQueries(db_path)
            stats = queries.get_email_statistics()
            print(f"   ✓ Queries work (retrieved statistics for {stats['total_emails']} emails)")

            print("\n✅ All basic functionality tests passed!")
            return True

        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Email Priority Manager - Database Tests")
    print("=" * 50)

    # Test basic functionality first
    if not test_basic_functionality():
        sys.exit(1)

    # If basic tests pass, run full test suite
    print("\n" + "=" * 50)
    if run_tests():
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
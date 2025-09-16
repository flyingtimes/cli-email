"""
Simple test for database functionality.
"""

import sys
import os
import tempfile

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database():
    """Test basic database functionality."""
    print("Testing database functionality...")

    try:
        # Import our modules directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'email_priority_manager', 'database'))

        from schema import DatabaseSchema
        from search import EmailSearch
        from indexes import DatabaseIndexManager
        from queries import EmailQueries
        from connections import DatabaseManager

        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            db_path = temp_db.name

        try:
            # Test schema initialization
            print("1. Testing schema initialization...")
            schema = DatabaseSchema(db_path)
            schema.initialize_database()
            print("   OK: Schema initialized successfully")

            # Test database manager
            print("2. Testing database manager...")
            db_manager = DatabaseManager()
            db_manager.config.db_path = db_path
            db_manager.initialize_database()
            print("   OK: Database manager initialized successfully")

            # Test search functionality
            print("3. Testing search functionality...")
            search = EmailSearch(db_path)
            results = search.search("test")
            print(f"   OK: Search functionality works (found {len(results)} results)")

            # Test index manager
            print("4. Testing index manager...")
            index_manager = DatabaseIndexManager(db_path)
            index_manager.create_all_indexes()
            stats = index_manager.get_index_stats()
            print(f"   OK: Index manager works (created {stats['total_indexes']} indexes)")

            # Test queries
            print("5. Testing queries...")
            queries = EmailQueries(db_path)
            stats = queries.get_email_statistics()
            print(f"   OK: Queries work (retrieved statistics for {stats['total_emails']} emails)")

            print("\nAll basic functionality tests passed!")
            return True

        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database()
    if success:
        print("\nSUCCESS: Database functionality verified!")
    else:
        print("\nFAILED: Database functionality test failed!")
        sys.exit(1)
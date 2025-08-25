from backend.database import engine, Base
from backend.models import User, OnboardingData

def init_database():
    """Initialize the database with all tables"""
    try:
        # Drop all existing tables (be careful with this in production!)
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("Database tables created successfully!")
        
        # Print table info
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"- {table_name}")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    init_database()
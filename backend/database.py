from sqlmodel import SQLModel, create_engine, Session
import os

# Database file path
DATABASE_URL = "sqlite:///./eyetracker.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)
    # Run migrations
    migrate_database()


def migrate_database():
    """Migrate database schema by adding new columns if they don't exist"""
    from sqlalchemy import inspect, text
    
    try:
        inspector = inspect(engine)
        
        # Check if users table exists
        if 'users' in inspector.get_table_names():
            # Get existing columns
            existing_columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Add new columns if they don't exist
            with engine.begin() as conn:
                if 'gender' not in existing_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN gender VARCHAR(50)"))
                    print("Added 'gender' column to users table")
                
                if 'age' not in existing_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN age INTEGER"))
                    print("Added 'age' column to users table")
                
                if 'voice' not in existing_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN voice VARCHAR(100)"))
                    print("Added 'voice' column to users table")
    except Exception as e:
        print(f"Migration error (this is OK if columns already exist): {e}")


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session


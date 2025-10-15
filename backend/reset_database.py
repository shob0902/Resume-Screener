import os
from database import Base, engine

# Delete old database
db_path = "resumes.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✓ Deleted old database: {db_path}")

# Create new database with updated schema
Base.metadata.create_all(bind=engine)
print("✓ Created new database with updated schema")
print("✓ Database reset complete!")
print("\nNew columns added:")
print("  - job_match_percentage (Integer)")
print("  - match_reasoning (Text)")
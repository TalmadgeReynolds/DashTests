#!/usr/bin/env python3
from sqlalchemy import create_engine, text

# Define connection string
connection_string = 'postgresql://lipsync:PYQUw4VwDi36Jz9@lipsync.c9qesoeo0b50.us-east-1.rds.amazonaws.com:5432/postgres'

# Create engine
engine = create_engine(connection_string)

# Create alembic_version table if it doesn't exist
with engine.connect() as conn:
    conn.execute(text('CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))'))
    
    # Check if initial migration version exists to avoid duplicate key errors
    result = conn.execute(text("SELECT count(*) FROM alembic_version WHERE version_num = '896fe07d8f9e'"))
    count = result.scalar()
    
    if count == 0:
        # Mark initial migration as completed
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('896fe07d8f9e')"))
        print("Initial migration marked as completed")
    else:
        print("Initial migration was already marked as completed")
    
    # Check if screenplay migration version exists
    result = conn.execute(text("SELECT count(*) FROM alembic_version WHERE version_num = 'b7f9e1d8c2a1'"))
    count = result.scalar()
    
    if count == 0:
        # Mark screenplay migration as completed
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('b7f9e1d8c2a1')"))
        print("Screenplay migration marked as completed")
    else:
        print("Screenplay migration was already marked as completed")
    
    # Commit the transaction
    conn.commit()

print("Done!")
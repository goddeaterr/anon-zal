from app import db, Post
import uuid

# Add the new 'uuid' column to the 'Post' table if it doesn't already exist
with db.engine.connect() as connection:
    # Check if 'uuid' column exists
    result = connection.execute("PRAGMA table_info(post);")
    columns = [row[1] for row in result]
    if 'uuid' not in columns:
        connection.execute('ALTER TABLE post ADD COLUMN uuid VARCHAR(36)')

# Populate the 'uuid' column with unique UUIDs
posts = Post.query.all()
for post in posts:
    if not post.uuid:
        post.uuid = str(uuid.uuid4())
        db.session.add(post)

db.session.commit()

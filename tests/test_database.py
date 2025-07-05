
import pytest
from note_app import database

def test_create_user(app):
    """
    Tests that a user can be created successfully.
    """
    with app.app_context():
        user_id = database.create_user("testuser", "test@example.com", "password123")
        assert user_id is not None
        
        user = database.get_user_by_username("testuser")
        assert user is not None
        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"

def test_add_and_get_note(app):
    """
    Tests that a note can be added and retrieved for a specific user.
    """
    with app.app_context():
        user_id = database.create_user("testuser", "test@example.com", "password123")
        assert user_id is not None # Ensure user was created

        note_id = database.add_note("Test Title", "Test Content", "Test Category", "tag1, tag2", user_id)
        
        assert note_id is not None
        
        note = database.get_note(note_id, user_id)
        assert note is not None
        assert note['title'] == "Test Title"
        assert note['content'] == "Test Content"
        assert note['category'] == "Test Category"
        assert "tag1" in note['tags']
        assert "tag2" in note['tags']

def test_note_isolation(app):
    """
    Tests that a user cannot see another user's notes.
    This is a critical security test.
    """
    with app.app_context():
        # Create two users
        user1_id = database.create_user("user1", "user1@example.com", "password123")
        user2_id = database.create_user("user2", "user2@example.com", "password123")
        
        # User 1 creates a note
        note1_id = database.add_note("User 1's Note", "Content", None, None, user1_id)
        
        # Verify User 1 can see their note
        assert database.get_note(note1_id, user1_id) is not None
        
        # CRITICAL: Verify User 2 CANNOT see User 1's note
        assert database.get_note(note1_id, user2_id) is None
        
        # Verify listing notes also respects isolation
        user1_notes = database.list_notes(user1_id)
        user2_notes = database.list_notes(user2_id)
        
        assert len(user1_notes) == 1
        assert user1_notes[0]['title'] == "User 1's Note"
        assert len(user2_notes) == 0

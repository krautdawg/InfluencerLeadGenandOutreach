import pytest
from main import deduplicate_profiles

def test_deduplicate_profiles_basic():
    """Test basic deduplication functionality"""
    profiles = [
        {'hashtag': 'fitness', 'username': 'user1'},
        {'hashtag': 'fitness', 'username': 'user2'},
        {'hashtag': 'fitness', 'username': 'user1'},  # Duplicate
        {'hashtag': 'travel', 'username': 'user1'},   # Different hashtag, same user
    ]
    
    unique_profiles, duplicates = deduplicate_profiles(profiles)
    
    assert len(unique_profiles) == 3
    assert 'user1' in duplicates
    assert len(duplicates) == 1

def test_deduplicate_profiles_empty():
    """Test deduplication with empty input"""
    profiles = []
    unique_profiles, duplicates = deduplicate_profiles(profiles)
    
    assert len(unique_profiles) == 0
    assert len(duplicates) == 0

def test_deduplicate_profiles_no_duplicates():
    """Test deduplication with no duplicates"""
    profiles = [
        {'hashtag': 'fitness', 'username': 'user1'},
        {'hashtag': 'fitness', 'username': 'user2'},
        {'hashtag': 'travel', 'username': 'user3'},
    ]
    
    unique_profiles, duplicates = deduplicate_profiles(profiles)
    
    assert len(unique_profiles) == 3
    assert len(duplicates) == 0

def test_deduplicate_profiles_missing_fields():
    """Test deduplication with missing hashtag or username"""
    profiles = [
        {'hashtag': 'fitness', 'username': 'user1'},
        {'hashtag': '', 'username': 'user2'},
        {'hashtag': 'fitness', 'username': ''},
        {'hashtag': '', 'username': ''},
        {'hashtag': '', 'username': ''},  # Duplicate empty
    ]
    
    unique_profiles, duplicates = deduplicate_profiles(profiles)
    
    assert len(unique_profiles) == 4
    assert '' in duplicates  # Empty username marked as duplicate

def test_deduplicate_profiles_multiple_duplicates():
    """Test deduplication with multiple duplicates"""
    profiles = [
        {'hashtag': 'fitness', 'username': 'user1'},
        {'hashtag': 'fitness', 'username': 'user2'},
        {'hashtag': 'fitness', 'username': 'user1'},  # Duplicate
        {'hashtag': 'fitness', 'username': 'user2'},  # Duplicate
        {'hashtag': 'fitness', 'username': 'user1'},  # Another duplicate
    ]
    
    unique_profiles, duplicates = deduplicate_profiles(profiles)
    
    assert len(unique_profiles) == 2
    assert 'user1' in duplicates
    assert 'user2' in duplicates
    assert len(duplicates) == 2

if __name__ == '__main__':
    pytest.main([__file__])

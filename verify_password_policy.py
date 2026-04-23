from security import is_password_strong, verify_password, hash_password
from auth import login_user
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

def test_password_strength():
    print("Testing Password Strength...")
    tests = [
        ("short", False),
        ("NoNumbersOrSymbols", False),
        ("NoSymbols123", False),
        ("lowercase1!234", False),
        ("UPPERCASE1!234", False),
        ("ValidPassword1!", True),
        ("AnotherValid#2024", True),
    ]
    for pwd, expected in tests:
        valid, msg = is_password_strong(pwd)
        print(f"  '{pwd}': {valid} ({msg if not valid else 'OK'})")
        assert valid == expected

def test_lockout_logic():
    print("\nTesting Lockout Logic...")
    # Mock database functions
    with patch('auth.get_user_by_username') as mock_get, \
         patch('auth.update_user_lockout') as mock_update, \
         patch('auth.verify_password') as mock_verify:
        
        username = "testuser"
        hashed = "hashed_pw"
        
        # 1. Normal failure
        mock_get.return_value = (1, "E001", username, hashed, 0, None)
        mock_verify.return_value = False
        res = login_user(username, "wrong")
        print(f"  First failure: {res['error']}")
        mock_update.assert_called_with(username, 1, None)
        
        # 2. Lockout after 5 attempts
        mock_get.return_value = (1, "E001", username, hashed, 4, None)
        res = login_user(username, "wrong")
        print(f"  Fifth failure: {res['error']}")
        # Check if it locked (locked_until should be roughly now + 15 min)
        args, kwargs = mock_update.call_args
        assert args[1] == 5
        assert args[2] is not None
        
        # 3. Locked account
        future_lock = datetime.now() + timedelta(minutes=10)
        mock_get.return_value = (1, "E001", username, hashed, 5, future_lock)
        res = login_user(username, "any")
        print(f"  Locked attempt: {res['error']}")
        assert "Account locked" in res['error']

if __name__ == "__main__":
    try:
        test_password_strength()
        test_lockout_logic()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")

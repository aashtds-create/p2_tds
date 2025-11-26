"""
Authentication utilities
"""
import os
import secrets

SECRET = os.getenv("SECRET", "")


def verify_secret(provided_secret: str) -> bool:
    """
    Verify that the provided secret matches the configured secret
    
    Args:
        provided_secret: Secret from request
        
    Returns:
        True if secret matches, False otherwise
    """
    # Re-fetch secret to ensure we get latest env var
    secret = os.getenv("SECRET", "")
    
    if not secret:
        return False
        
    return secrets.compare_digest(provided_secret, secret)


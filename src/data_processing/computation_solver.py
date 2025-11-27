"""
Computational solver for math/algorithm puzzles
"""
import logging
import hashlib
import re
from typing import Optional

logger = logging.getLogger(__name__)

class ComputationSolver:
    """
    Solves computational puzzles that require code execution
    (e.g., alphametic puzzles, hash calculations, formulas)
    """
    
    async def solve_alphametic(self, content: str, email: str, previous_answer: str = None) -> Optional[str]:
        """
        Solve alphametic puzzles with computational formulas
        
        Args:
            content: The puzzle content
            email: The user's email for personalized puzzles
            previous_answer: Previous answer (for chained puzzles)
            
        Returns:
            The computed answer as a string
        """
        try:
            logger.info(f"Solving computational puzzle for email: {email}")
            
            # SHA1-based formulas (check FIRST - more specific)
            if "SHA1" in content and "emailNumber" in content:
                return await self._solve_sha1_formula(content, email)
            
            # SHA256 checksum puzzles (check AFTER SHA1)
            elif "SHA256" in content or "checksum" in content.lower():
                return await self._solve_sha256_checksum(content, previous_answer)
            
            # Add more alphametic types here as needed
            logger.warning("Unknown computational puzzle type")
            return None
            
        except Exception as e:
            logger.error(f"Error solving computation: {e}")
            return None
    
    async def _solve_sha256_checksum(self, content: str, previous_answer: str) -> Optional[str]:
        """
        Solve SHA256 checksum puzzles
        
        Example:
        - Take key from previous puzzle (e.g., '87266151')
        - Append blob (e.g., '8b1f4c3a2d')
        - Compute SHA256(key + blob)
        - Return first N hex characters
        """
        try:
            logger.info("Solving SHA256 checksum puzzle")
            
            # Extract the key (from previous answer or content)
            key = previous_answer
            if not key:
                # Try to extract from content
                key_match = re.search(r'8-digit key.*?(\d{8})', content)
                if key_match:
                    key = key_match.group(1)
                else:
                    logger.error("Could not find key for SHA256 checksum")
                    return None
            
            logger.info(f"Using key: {key}")
            
            # Extract the blob to append
            blob_match = re.search(r"append.*?['\"]([a-f0-9]+)['\"]", content, re.IGNORECASE)
            if not blob_match:
                blob_match = re.search(r"blob.*?['\"]([a-f0-9]+)['\"]", content, re.IGNORECASE)
            
            if not blob_match:
                logger.error("Could not find blob in content")
                return None
            
            blob = blob_match.group(1)
            logger.info(f"Blob to append: {blob}")
            
            # Compute SHA256
            combined = key + blob
            sha256_hash = hashlib.sha256(combined.encode()).hexdigest()
            logger.info(f"SHA256({combined}) = {sha256_hash}")
            
            # Extract how many hex characters to return
            hex_count_match = re.search(r'first\s+(\d+)\s+hex', content, re.IGNORECASE)
            if hex_count_match:
                hex_count = int(hex_count_match.group(1))
            else:
                hex_count = 12  # Default to 12
            
            result = sha256_hash[:hex_count]
            logger.info(f"Returning first {hex_count} hex chars: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in SHA256 checksum solving: {e}")
            return None
    
    async def _solve_sha1_formula(self, content: str, email: str) -> Optional[str]:
        """
        Solve alphametic puzzles that use SHA1-based formulas
        
        Example: 
        - emailNumber = first 4 hex of SHA1(email) as integer
        - Key = ((emailNumber * 7919 + 12345) mod 1e8)
        """
        try:
            # Step 1: Calculate SHA1 of email
            sha1_hash = hashlib.sha1(email.encode()).hexdigest()
            logger.info(f"SHA1({email}) = {sha1_hash}")
            
            # Step 2: Extract first 4 hex characters and convert to integer
            first_4_hex = sha1_hash[:4]
            email_number = int(first_4_hex, 16)
            logger.info(f"emailNumber (first 4 hex as int) = {email_number}")
            
            # Step 3: Extract formula from content
            # Look for patterns like: ((emailNumber * X + Y) mod Z)
            formula_match = re.search(r'\(\(emailNumber\s*\*\s*(\d+)\s*\+\s*(\d+)\)\s*mod\s*(\w+)\)', content)
            
            if formula_match:
                multiplier = int(formula_match.group(1))
                addend = int(formula_match.group(2))
                modulus_str = formula_match.group(3)
                
                # Parse modulus (could be "1e8" or "100000000")
                if 'e' in modulus_str.lower():
                    modulus = int(float(modulus_str))
                else:
                    modulus = int(modulus_str)
                
                logger.info(f"Formula: (({email_number} * {multiplier} + {addend}) mod {modulus})")
                
                # Step 4: Calculate the key
                key = ((email_number * multiplier) + addend) % modulus
                logger.info(f"Calculated key: {key}")
                
                # Step 5: Format as 8-digit string (pad with zeros if needed)
                key_str = str(key).zfill(8)
                logger.info(f"8-digit key: {key_str}")
                
                return key_str
            else:
                logger.error("Could not extract formula from content")
                return None
                
        except Exception as e:
            logger.error(f"Error in SHA1 formula solving: {e}")
            return None


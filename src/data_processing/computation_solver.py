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
    
    async def solve_alphametic(self, content: str, email: str) -> Optional[str]:
        """
        Solve alphametic puzzles with computational formulas
        
        Args:
            content: The puzzle content
            email: The user's email for personalized puzzles
            
        Returns:
            The computed answer as a string
        """
        try:
            logger.info(f"Solving alphametic puzzle for email: {email}")
            
            # Check if this is the FORK+LIME type puzzle
            if "SHA1" in content and "emailNumber" in content:
                return await self._solve_sha1_formula(content, email)
            
            # Add more alphametic types here as needed
            logger.warning("Unknown alphametic type")
            return None
            
        except Exception as e:
            logger.error(f"Error solving alphametic: {e}")
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


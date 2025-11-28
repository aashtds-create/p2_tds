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
            
            # MD5 hash puzzles
            elif "MD5" in content:
                return await self._solve_md5_puzzle(content, email, previous_answer)
            
            # Fibonacci sequence
            elif "fibonacci" in content.lower():
                return await self._solve_fibonacci(content)
            
            # Prime number problems
            elif "prime" in content.lower() and any(word in content.lower() for word in ["factor", "number"]):
                return await self._solve_prime_problem(content)
            
            # Base64 encoding/decoding
            elif "base64" in content.lower():
                return await self._solve_base64_problem(content, previous_answer)
            
            # Simple arithmetic
            elif re.search(r'\d+\s*[+\-*/]\s*\d+', content):
                return await self._solve_arithmetic(content)
            
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
            logger.info(f"Content length: {len(content)} chars")
            logger.info(f"Content preview: {content[:300]}")
            
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
            
            # Extract the blob to append - try multiple patterns
            blob = None
            
            # Pattern 1: blob 'xxx' or blob "xxx"
            blob_match = re.search(r"blob\s*['\"]([a-f0-9]+)['\"]", content, re.IGNORECASE)
            if blob_match:
                blob = blob_match.group(1)
            
            # Pattern 2: append 'xxx' or append "xxx"
            if not blob:
                blob_match = re.search(r"append.*?['\"]([a-f0-9]+)['\"]", content, re.IGNORECASE)
                if blob_match:
                    blob = blob_match.group(1)
            
            # Pattern 3: Just any hex string after "blob" or "append"
            if not blob:
                blob_match = re.search(r"(?:blob|append).*?([a-f0-9]{8,})", content, re.IGNORECASE)
                if blob_match:
                    blob = blob_match.group(1)
            
            # Pattern 4: Look for any standalone hex string (risky but fallback)
            if not blob:
                # Find hex strings that look like blobs (8+ chars)
                hex_strings = re.findall(r'\b([a-f0-9]{8,})\b', content, re.IGNORECASE)
                # Filter out the key itself
                hex_strings = [h for h in hex_strings if h != key]
                if hex_strings:
                    blob = hex_strings[0]
            
            if not blob:
                logger.error(f"Could not find blob in content. Content: {content[:200]}")
                return None
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
    
    async def _solve_md5_puzzle(self, content: str, email: str, previous_answer: str) -> Optional[str]:
        """Solve MD5 hash puzzles"""
        try:
            logger.info("Solving MD5 puzzle")
            md5_hash = hashlib.md5(email.encode()).hexdigest()
            logger.info(f"MD5({email}) = {md5_hash}")
            
            # Extract how many characters to return
            char_match = re.search(r'first\s+(\d+)', content, re.IGNORECASE)
            if char_match:
                num_chars = int(char_match.group(1))
                return md5_hash[:num_chars]
            
            return md5_hash
        except Exception as e:
            logger.error(f"Error in MD5 solving: {e}")
            return None
    
    async def _solve_fibonacci(self, content: str) -> Optional[str]:
        """Solve Fibonacci sequence problems"""
        try:
            logger.info("Solving Fibonacci puzzle")
            
            # Extract which Fibonacci number is requested
            n_match = re.search(r'fibonacci.*?(\d+)', content, re.IGNORECASE)
            if not n_match:
                n_match = re.search(r'(\d+).*?fibonacci', content, re.IGNORECASE)
            
            if n_match:
                n = int(n_match.group(1))
                logger.info(f"Computing Fibonacci({n})")
                
                # Compute nth Fibonacci number
                if n <= 1:
                    return str(n)
                
                a, b = 0, 1
                for _ in range(2, n + 1):
                    a, b = b, a + b
                
                logger.info(f"Fibonacci({n}) = {b}")
                return str(b)
            
            return None
        except Exception as e:
            logger.error(f"Error in Fibonacci solving: {e}")
            return None
    
    async def _solve_prime_problem(self, content: str) -> Optional[str]:
        """Solve prime number problems (factorization, nth prime, etc.)"""
        try:
            logger.info("Solving prime number puzzle")
            
            # Check if it's prime factorization
            if "factor" in content.lower():
                # Extract number to factorize
                num_match = re.search(r'factor.*?(\d+)', content, re.IGNORECASE)
                if not num_match:
                    num_match = re.search(r'(\d+).*?factor', content, re.IGNORECASE)
                
                if num_match:
                    n = int(num_match.group(1))
                    logger.info(f"Finding prime factors of {n}")
                    
                    factors = []
                    d = 2
                    while d * d <= n:
                        while n % d == 0:
                            factors.append(d)
                            n //= d
                        d += 1
                    if n > 1:
                        factors.append(n)
                    
                    logger.info(f"Prime factors: {factors}")
                    return str(factors)
            
            return None
        except Exception as e:
            logger.error(f"Error in prime solving: {e}")
            return None
    
    async def _solve_base64_problem(self, content: str, previous_answer: str) -> Optional[str]:
        """Solve base64 encoding/decoding problems"""
        try:
            logger.info("Solving base64 puzzle")
            import base64 as b64
            
            # Check if encoding or decoding
            if "encode" in content.lower():
                # Encode previous answer or extract text
                text = previous_answer or content
                encoded = b64.b64encode(text.encode()).decode()
                logger.info(f"Base64 encoded: {encoded}")
                return encoded
            
            elif "decode" in content.lower():
                # Find base64 string to decode
                b64_match = re.search(r'([A-Za-z0-9+/]+=*)', content)
                if b64_match:
                    encoded = b64_match.group(1)
                    decoded = b64.b64decode(encoded).decode()
                    logger.info(f"Base64 decoded: {decoded}")
                    return decoded
            
            return None
        except Exception as e:
            logger.error(f"Error in base64 solving: {e}")
            return None
    
    async def _solve_arithmetic(self, content: str) -> Optional[str]:
        """Solve simple arithmetic expressions"""
        try:
            logger.info("Solving arithmetic puzzle")
            
            # Extract expression like "123 + 456" or "50 * 20"
            expr_match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', content)
            if expr_match:
                a = int(expr_match.group(1))
                op = expr_match.group(2)
                b = int(expr_match.group(3))
                
                result = None
                if op == '+':
                    result = a + b
                elif op == '-':
                    result = a - b
                elif op == '*':
                    result = a * b
                elif op == '/':
                    result = a // b if b != 0 else None
                
                if result is not None:
                    logger.info(f"{a} {op} {b} = {result}")
                    return str(result)
            
            return None
        except Exception as e:
            logger.error(f"Error in arithmetic solving: {e}")
            return None


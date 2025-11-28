"""
Game solver for interactive game-based puzzles
Handles Tic-Tac-Toe, word games, logic puzzles, and novel games
"""
import logging
import json
import re
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class GameSolver:
    """
    Solves game-based puzzles using strategies and LLM assistance
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def solve_game(self, content: str, game_type: str = None) -> Optional[str]:
        """
        Main entry point for game solving
        
        Args:
            content: The game description/state
            game_type: Type of game (auto-detect if None)
            
        Returns:
            The move/answer to make
        """
        try:
            # Auto-detect game type if not provided
            if not game_type:
                game_type = self._detect_game_type(content)
            
            logger.info(f"Solving {game_type} game")
            
            # Route to appropriate solver
            if game_type == "tictactoe":
                return await self._solve_tictactoe(content)
            elif game_type == "wordle":
                return await self._solve_wordle(content)
            elif game_type == "sudoku":
                return await self._solve_sudoku(content)
            elif game_type == "chess":
                return await self._solve_chess_puzzle(content)
            elif game_type == "word_game":
                return await self._solve_word_game(content)
            else:
                # Unknown game - use LLM to generate strategy
                return await self._solve_novel_game(content)
                
        except Exception as e:
            logger.error(f"Error solving game: {e}")
            return None
    
    def _detect_game_type(self, content: str) -> str:
        """Detect what type of game this is"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["tic-tac-toe", "tictactoe", "noughts", "crosses"]):
            return "tictactoe"
        elif any(word in content_lower for word in ["wordle", "guess the word", "5 letter"]):
            return "wordle"
        elif any(word in content_lower for word in ["sudoku", "9x9 grid"]):
            return "sudoku"
        elif any(word in content_lower for word in ["chess", "checkmate", "knight", "bishop"]):
            return "chess"
        elif any(word in content_lower for word in ["scribble", "word", "letter", "anagram"]):
            return "word_game"
        else:
            return "unknown"
    
    async def _solve_tictactoe(self, content: str) -> Optional[str]:
        """
        Solve Tic-Tac-Toe using minimax algorithm
        """
        logger.info("Solving Tic-Tac-Toe puzzle")
        
        # Extract board state
        board = self._extract_tictactoe_board(content)
        if not board:
            logger.error("Could not extract Tic-Tac-Toe board")
            return None
        
        logger.info(f"Board state: {board}")
        
        # Determine who we are (X or O)
        our_symbol = self._determine_player(content, board)
        logger.info(f"Playing as: {our_symbol}")
        
        # Find optimal move using minimax
        best_move = self._minimax_tictactoe(board, our_symbol)
        
        if best_move:
            logger.info(f"Optimal move: position {best_move}")
            return self._format_tictactoe_move(best_move, content)
        
        return None
    
    def _extract_tictactoe_board(self, content: str) -> Optional[List[str]]:
        """
        Extract Tic-Tac-Toe board from various formats
        
        Expected: 9 positions [0-8] with X, O, or empty
        """
        # Try to find board representation
        # Format 1: "Board: X O _ / _ X _ / O _ X"
        board_match = re.search(r'board[:\s]*([XO_|/ ]+)', content, re.IGNORECASE)
        if board_match:
            board_str = board_match.group(1).upper()
            # Remove separators
            board_str = board_str.replace('/', '').replace('|', '').replace(' ', '')
            if len(board_str) == 9:
                return list(board_str.replace('_', ' '))
        
        # Format 2: List of positions
        positions = re.findall(r'position\s*(\d):\s*([XO])', content, re.IGNORECASE)
        if positions:
            board = [' '] * 9
            for pos, symbol in positions:
                board[int(pos)] = symbol.upper()
            return board
        
        # Format 3: JSON-like
        try:
            json_match = re.search(r'\{[^}]*"board"[^}]*\}', content)
            if json_match:
                data = json.loads(json_match.group(0))
                if 'board' in data:
                    return list(data['board'])
        except:
            pass
        
        return None
    
    def _determine_player(self, content: str, board: List[str]) -> str:
        """Determine which symbol we're playing (X or O)"""
        # Check explicit mention
        if "you are x" in content.lower() or "play as x" in content.lower():
            return 'X'
        if "you are o" in content.lower() or "play as o" in content.lower():
            return 'O'
        
        # Infer from board state (who has fewer pieces goes next)
        x_count = board.count('X')
        o_count = board.count('O')
        
        if x_count <= o_count:
            return 'X'
        else:
            return 'O'
    
    def _minimax_tictactoe(self, board: List[str], player: str) -> Optional[int]:
        """
        Use minimax algorithm to find optimal Tic-Tac-Toe move
        """
        opponent = 'O' if player == 'X' else 'X'
        
        # Check for winning move
        for i in range(9):
            if board[i] == ' ':
                board[i] = player
                if self._check_winner(board, player):
                    board[i] = ' '
                    return i
                board[i] = ' '
        
        # Check for blocking move
        for i in range(9):
            if board[i] == ' ':
                board[i] = opponent
                if self._check_winner(board, opponent):
                    board[i] = ' '
                    return i
                board[i] = ' '
        
        # Take center if available
        if board[4] == ' ':
            return 4
        
        # Take corners
        corners = [0, 2, 6, 8]
        for corner in corners:
            if board[corner] == ' ':
                return corner
        
        # Take any side
        sides = [1, 3, 5, 7]
        for side in sides:
            if board[side] == ' ':
                return side
        
        return None
    
    def _check_winner(self, board: List[str], player: str) -> bool:
        """Check if player has won"""
        wins = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        return any(all(board[i] == player for i in win) for win in wins)
    
    def _format_tictactoe_move(self, position: int, content: str) -> str:
        """Format move according to expected format"""
        # Check what format is expected
        if "position" in content.lower():
            return str(position)
        elif "row" in content.lower() and "col" in content.lower():
            row = position // 3
            col = position % 3
            return f"{row},{col}"
        else:
            return str(position)
    
    async def _solve_wordle(self, content: str) -> Optional[str]:
        """
        Solve Wordle-style word guessing games
        """
        logger.info("Solving Wordle puzzle")
        
        # Extract clues (green/yellow/gray)
        previous_guesses = self._extract_wordle_clues(content)
        
        # Use LLM to generate next guess based on clues
        prompt = f"""
You are playing Wordle (5-letter word game).

Previous guesses and feedback:
{json.dumps(previous_guesses, indent=2)}

Green = correct letter in correct position
Yellow = correct letter in wrong position
Gray = letter not in word

Generate the optimal next guess (common 5-letter word that fits the clues).
Return ONLY the word, nothing else.
"""
        
        guess = await self.llm_client.chat_completion([
            {"role": "system", "content": "You are a Wordle expert."},
            {"role": "user", "content": prompt}
        ])
        
        if guess:
            guess = guess.strip().upper()[:5]
            logger.info(f"Wordle guess: {guess}")
            return guess
        
        return None
    
    def _extract_wordle_clues(self, content: str) -> List[Dict]:
        """Extract previous Wordle guesses and feedback"""
        # Parse formats like "GUESS: CRANE - G_Y_G" (Green, Gray, Yellow, Gray, Green)
        guesses = []
        patterns = re.findall(r'([A-Z]{5})\s*[-:]\s*([GYB_]{5})', content, re.IGNORECASE)
        
        for word, feedback in patterns:
            guesses.append({
                "word": word.upper(),
                "feedback": feedback.upper()
            })
        
        return guesses
    
    async def _solve_sudoku(self, content: str) -> Optional[str]:
        """
        Solve Sudoku puzzles
        """
        logger.info("Solving Sudoku puzzle")
        
        # Extract 9x9 grid
        grid = self._extract_sudoku_grid(content)
        if not grid:
            return None
        
        # Solve using backtracking
        if self._solve_sudoku_backtrack(grid):
            logger.info("Sudoku solved!")
            return self._format_sudoku_solution(grid, content)
        
        return None
    
    def _extract_sudoku_grid(self, content: str) -> Optional[List[List[int]]]:
        """Extract Sudoku grid from content"""
        # Look for 9x9 grid of numbers
        lines = content.split('\n')
        grid = []
        
        for line in lines:
            # Extract numbers from line
            numbers = re.findall(r'\d', line)
            if len(numbers) == 9:
                grid.append([int(n) if n != '0' else 0 for n in numbers])
        
        if len(grid) == 9:
            return grid
        
        return None
    
    def _solve_sudoku_backtrack(self, grid: List[List[int]]) -> bool:
        """Backtracking algorithm for Sudoku"""
        # Find empty cell
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 0:
                    # Try numbers 1-9
                    for num in range(1, 10):
                        if self._is_valid_sudoku(grid, i, j, num):
                            grid[i][j] = num
                            
                            if self._solve_sudoku_backtrack(grid):
                                return True
                            
                            grid[i][j] = 0
                    
                    return False
        
        return True
    
    def _is_valid_sudoku(self, grid: List[List[int]], row: int, col: int, num: int) -> bool:
        """Check if number is valid in Sudoku position"""
        # Check row
        if num in grid[row]:
            return False
        
        # Check column
        if num in [grid[i][col] for i in range(9)]:
            return False
        
        # Check 3x3 box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if grid[i][j] == num:
                    return False
        
        return True
    
    def _format_sudoku_solution(self, grid: List[List[int]], content: str) -> str:
        """Format Sudoku solution"""
        # Return as JSON or string based on expected format
        if "json" in content.lower():
            return json.dumps(grid)
        else:
            return '\n'.join([' '.join(map(str, row)) for row in grid])
    
    async def _solve_chess_puzzle(self, content: str) -> Optional[str]:
        """
        Solve chess puzzles (mate in N, best move, etc.)
        """
        logger.info("Solving chess puzzle")
        
        # Use LLM with chess knowledge
        prompt = f"""
You are a chess master. Solve this chess puzzle:

{content}

Return the best move in standard chess notation (e.g., "Qh5+" or "Nf3").
Return ONLY the move, nothing else.
"""
        
        move = await self.llm_client.chat_completion([
            {"role": "system", "content": "You are a chess expert."},
            {"role": "user", "content": prompt}
        ])
        
        if move:
            logger.info(f"Chess move: {move.strip()}")
            return move.strip()
        
        return None
    
    async def _solve_word_game(self, content: str) -> Optional[str]:
        """
        Solve word-based games (anagrams, Scrabble, etc.)
        """
        logger.info("Solving word game")
        
        # Use LLM for word games
        prompt = f"""
Solve this word game puzzle:

{content}

Analyze the clues and constraints carefully.
Return ONLY the answer (word or phrase), nothing else.
"""
        
        answer = await self.llm_client.chat_completion([
            {"role": "system", "content": "You are an expert at word games and puzzles."},
            {"role": "user", "content": prompt}
        ])
        
        if answer:
            logger.info(f"Word game answer: {answer.strip()}")
            return answer.strip()
        
        return None
    
    async def _solve_novel_game(self, content: str) -> Optional[str]:
        """
        Solve completely unknown games using LLM
        
        Strategy:
        1. Ask LLM to understand the rules
        2. Ask LLM to generate optimal strategy
        3. Execute strategy
        """
        logger.info("Solving novel/unknown game")
        
        # First, understand the game
        understanding_prompt = f"""
Analyze this game description and explain:
1. What are the rules?
2. What is the objective?
3. What move/answer should I make?

Game description:
{content}

Think step by step, then provide your answer.
"""
        
        response = await self.llm_client.chat_completion([
            {"role": "system", "content": "You are a game strategy expert. Analyze games and provide optimal moves."},
            {"role": "user", "content": understanding_prompt}
        ])
        
        if response:
            logger.info(f"LLM game analysis: {response[:200]}...")
            
            # Extract the answer/move from response
            # Look for explicit answer indication
            answer_match = re.search(r'(?:answer|move|play|choose)[:\s]*([^\n.]+)', response, re.IGNORECASE)
            if answer_match:
                answer = answer_match.group(1).strip()
                logger.info(f"Extracted answer: {answer}")
                return answer
            
            # Otherwise return the full response (LLM will have put answer at end)
            lines = response.strip().split('\n')
            return lines[-1].strip()
        
        return None


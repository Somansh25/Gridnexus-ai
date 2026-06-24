import random

# ==========================================
# 1. CORE LOGIC CONSTANTS & HELPERS
# ==========================================

WIN_LINES_3X3 = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8], # Columns
    [0, 4, 8], [2, 4, 6]             # Diagonals
]

def check_3x3_winner(board):
    """Detects winner in any 3x3 layout (works for micro grids and macro status)."""
    for line in WIN_LINES_3X3:
        if board[line[0]] != "" and board[line[0]] == board[line[1]] == board[line[2]]:
            if board[line[0]] in ["X", "O"]:
                return board[line[0]]
                
    # Check for draw: no empty spots and no winner
    # Micro grids use "", macro-status uses None for empty
    if all(cell is not None and cell != "" for cell in board):
        return "Draw"
    return None

def get_legal_moves(macro_board, active_index, macro_status):
    """Identifies all valid (sub_board, slot) coordinate pairs based on active targeting rules."""
    # Forced target scenario
    if active_index is not None and 0 <= active_index < 9:
        if macro_status[active_index] is None:
            moves = [(active_index, s) for s, v in enumerate(macro_board[active_index]) if v == ""]
            if moves: return moves
            
    # Free move scenario: Player can play in any unresolved board
    moves = []
    for b_idx in range(9):
        if macro_status[b_idx] is None:
            for s_idx, val in enumerate(macro_board[b_idx]):
                if val == "": moves.append((b_idx, s_idx))
    return moves

# ==========================================
# 2. HEURISTIC POSITION ANALYSIS
# ==========================================

def evaluate_ultimate_state(macro_board, macro_status):
    """Scores the board from the perspective of AI ('O') on macro and micro layers."""
    score = 0
    
    # Layer 1: Macro Win Path Building
    for line in WIN_LINES_3X3:
        marks = [macro_status[i] for i in line]
        ai_won = marks.count("O")
        hu_won = marks.count("X")
        none = marks.count(None)
        
        if ai_won == 2 and none == 1: score += 150
        elif ai_won == 1 and none == 2: score += 30
        
        if hu_won == 2 and none == 1: score -= 200
        elif hu_won == 1 and none == 2: score -= 40

    # Layer 2: Local Control & Strategic Centers
    for i in range(9):
        if macro_status[i] == "O":
            score += 45 if i == 4 else 20
        elif macro_status[i] == "X":
            score -= 55 if i == 4 else 25
        elif macro_status[i] is None:
            for slot, mark in enumerate(macro_board[i]):
                if mark == "O": score += 5 if slot == 4 else 1
                elif mark == "X": score -= 6 if slot == 4 else -1
    return score

# ==========================================
# 3. ULTIMATE ADVERSARIAL ENGINE
# ==========================================

def minimax_ultimate(macro_board, active_index, depth, is_maximizing, alpha, beta, max_depth):
    """Recursive depth-limited engine for the nested 9x9 matrix."""
    macro_status = [check_3x3_winner(sb) for sb in macro_board]
    global_winner = check_3x3_winner(macro_status)
    
    if global_winner == "O": return 10000 - depth
    if global_winner == "X": return -10000 + depth
    if depth >= max_depth: return evaluate_ultimate_state(macro_board, macro_status)
    
    moves = get_legal_moves(macro_board, active_index, macro_status)
    if not moves: return 0

    if is_maximizing:
        best = float('-inf')
        for sub, slot in moves:
            macro_board[sub][slot] = "O"
            sub_res = check_3x3_winner(macro_board[sub])
            # Determine if next move is forced to a specific sector
            res = minimax_ultimate(macro_board, slot if sub_res is None else None, depth + 1, False, alpha, beta, max_depth)
            macro_board[sub][slot] = ""
            best = max(best, res)
            alpha = max(alpha, res)
            if beta <= alpha: break
        return best
    else:
        best = float('inf')
        for sub, slot in moves:
            macro_board[sub][slot] = "X"
            sub_res = check_3x3_winner(macro_board[sub])
            res = minimax_ultimate(macro_board, slot if sub_res is None else None, depth + 1, True, alpha, beta, max_depth)
            macro_board[sub][slot] = ""
            best = min(best, res)
            beta = min(beta, res)
            if beta <= alpha: break
        return best

# ==========================================
# 4. AI ENTRY POINT
# ==========================================

def get_ultimate_move(macro_board, active_board_index, difficulty):
    """Calculates the optimized next move for 9x9 Ultimate play based on game state and difficulty."""
    macro_status = [check_3x3_winner(sb) for sb in macro_board]
    valid_moves = get_legal_moves(macro_board, active_board_index, macro_status)
    
    if not valid_moves: return {"sub_board": 0, "slot": 0}

    # Blunder Injection
    if difficulty == "easy" and random.random() < 0.85:
        m = random.choice(valid_moves)
        return {"sub_board": m[0], "slot": m[1]}
    if difficulty == "medium" and random.random() < 0.35:
        m = random.choice(valid_moves)
        return {"sub_board": m[0], "slot": m[1]}

    search_depth = 3
    best_score = float('-inf')
    best_move = valid_moves[0]
    alpha, beta = float('-inf'), float('inf')
    
    random.shuffle(valid_moves) # Diverse gameplay

    for sub_idx, slot_idx in valid_moves:
        macro_board[sub_idx][slot_idx] = "O"
        sub_res = check_3x3_winner(macro_board[sub_idx])
        next_active = slot_idx if sub_res is None else None
        
        score = minimax_ultimate(macro_board, next_active, 0, False, alpha, beta, search_depth)
        macro_board[sub_idx][slot_idx] = ""
        
        if score > best_score:
            best_score = score
            best_move = (sub_idx, slot_idx)
        alpha = max(alpha, score)

    return {"sub_board": best_move[0], "slot": best_move[1]}
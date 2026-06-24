import random

# ==========================================
# 1. CONSTANTS & UTILITIES
# ==========================================

def get_win_condition(size):
    #3x3 requires 3 in a row. 5x5 requires 4 in a row.
    return 3 if size == 3 else 4

def get_winning_lines(size, win_streak):
    #Pre-calculates all indices for possible winning streaks to boost performance.
    lines = []
    # Rows
    for r in range(size):
        for c in range(size - win_streak + 1):
            lines.append([r * size + c + i for i in range(win_streak)])
    # Columns
    for c in range(size):
        for r in range(size - win_streak + 1):
            lines.append([(r + i) * size + c for i in range(win_streak)])
    # Diagonals (Top-Left to Bottom-Right)
    for r in range(size - win_streak + 1):
        for c in range(size - win_streak + 1):
            lines.append([(r + i) * size + (c + i) for i in range(win_streak)])
    # Diagonals (Top-Right to Bottom-Left)
    for r in range(size - win_streak + 1):
        for c in range(win_streak - 1, size):
            lines.append([(r + i) * size + (c - i) for i in range(win_streak)])
    return lines

# ==========================================
# 2. STATE EVALUATION ENGINES
# ==========================================

def check_winner(board, lines):
    #Scans pre-calculated lines to find any completed win sequences.
    for line in lines:
        first = board[line[0]]
        if first != "" and all(board[idx] == first for idx in line):
            return first
    return None

def evaluate_heuristic(board, lines, win_streak):
    #Scores non-terminal states based on potential for winning alignments.
    score = 0
    for line in lines:
        ai_count = sum(1 for i in line if board[i] == "O")
        hu_count = sum(1 for i in line if board[i] == "X")
        empty = sum(1 for i in line if board[i] == "")

        if ai_count > 0 and hu_count == 0:
            if ai_count == win_streak - 1: score += 50
            elif ai_count == win_streak - 2: score += 10
        elif hu_count > 0 and ai_count == 0:
            if hu_count == win_streak - 1: score -= 85
            elif hu_count == win_streak - 2: score -= 15
    return score

# ==========================================
# 3. MINIMAX WITH ALPHA-BETA PRUNING
# ==========================================

def minimax(board, lines, win_streak, depth, is_maximizing, alpha, beta, max_depth):
    #Depth-limited adversarial search with pruning.
    winner = check_winner(board, lines)
    if winner == "O": return 1000 - depth
    if winner == "X": return -1000 + depth
    if "" not in board: return 0

    if depth >= max_depth:
        return evaluate_heuristic(board, lines, win_streak)

    available = [i for i, spot in enumerate(board) if spot == ""]

    if is_maximizing:
        best_eval = float('-inf')
        for move in available:
            board[move] = "O"
            res = minimax(board, lines, win_streak, depth + 1, False, alpha, beta, max_depth)
            board[move] = ""
            best_eval = max(best_eval, res)
            alpha = max(alpha, res)
            if beta <= alpha: break
        return best_eval
    else:
        best_eval = float('inf')
        for move in available:
            board[move] = "X"
            res = minimax(board, lines, win_streak, depth + 1, True, alpha, beta, max_depth)
            board[move] = ""
            best_eval = min(best_eval, res)
            beta = min(beta, res)
            if beta <= alpha: break
        return best_eval

# ==========================================
# 4. PRIMARY API ENTRY POINT
# ==========================================

def get_classic_move(board, size, difficulty):
    #Orchestrates AI decision making based on game size, difficulty and current state.
    available = [i for i, spot in enumerate(board) if spot == ""]
    if not available: return None

    # DIFFICULTY BLUNDER INJECTION
    if difficulty == "easy" and random.random() < 0.85:
        return random.choice(available)
    if difficulty == "medium" and random.random() < 0.35:
        return random.choice(available)

    # Strategy: Grab center immediately if it's the very first move
    if len(available) == (size * size):
        return 4 if size == 3 else 12

    win_streak = get_win_condition(size)
    lines = get_winning_lines(size, win_streak)
    max_depth = 100 if size == 3 else 4

    best_score = float('-inf')
    best_move = available[0]
    
    # Introduce shuffle for varied gameplay on equal branch scores
    random.shuffle(available)

    for move in available:
        board[move] = "O"
        score = minimax(board, lines, win_streak, 0, False, float('-inf'), float('inf'), max_depth)
        board[move] = ""
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move
import os
import re
import json
import math
import random
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import certifi
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environmental variables explicitly before initializing the application
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Strict configuration retrieval
SECRET_KEY = os.environ.get('SECRET_KEY')
MONGO_URI = os.environ.get('MONGO_URI')

if not SECRET_KEY or not MONGO_URI:
    raise RuntimeError("CRITICAL ERROR: Environment variables 'SECRET_KEY' and 'MONGO_URI' must be set.")

app.secret_key = SECRET_KEY

# ==========================================================================
# 1. DATABASE INITIALIZATION
# ==========================================================================
db = None
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
        db = client.get_database()
        print("Successfully connected to MongoDB Atlas infrastructure.")
    except Exception as e:
        print(f"Database connection warning: {e}")
else:
    print("Warning: MONGO_URI not found in environment variables. Running in local fallback mode.")

# ==========================================================================
# 2. CORE GAME LOGIC HELPERS
# ==========================================================================
def check_winner_3x3(b):
    #Checks for a winner in a 3x3 grid (Classic or Micro-grid).
    lines = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
    for l in lines:
        if b[l[0]] != "" and b[l[0]] == b[l[1]] == b[l[2]]:
            return b[l[0]]
    return "Draw" if "" not in b else None

def get_lines_5x5():
    #Pre-calculates all winning 4-in-a-row lines for a 5x5 grid.
    lines = []
    for r in range(5):
        for c in range(2):
            lines.append([r*5+c, r*5+c+1, r*5+c+2, r*5+c+3]) # Rows
            lines.append([c*5+r, (c+1)*5+r, (c+2)*5+r, (c+3)*5+r]) # Cols
    for r in range(2):
        for c in range(2):
            lines.append([r*5+c, (r+1)*5+(c+1), (r+2)*5+(c+2), (r+3)*5+(c+3)]) # Diag TL-BR
        for c in range(3, 5):
            lines.append([r*5+c, (r+1)*5+(c-1), (r+2)*5+(c-2), (r+3)*5+(c-3)]) # Diag TR-BL
    return lines

LINES_5x5 = get_lines_5x5()

def check_winner_5x5(b):
    #Checks for 4-in-a-row in a 5x5 grid.
    for l in LINES_5x5:
        if b[l[0]] != "" and b[l[0]] == b[l[1]] == b[l[2]] == b[l[3]]:
            return b[l[0]]
    return "Draw" if "" not in b else None

# ==========================================================================
# 3. AI ENGINES (MINIMAX & HEURISTICS)
# ==========================================================================

# --- CLASSIC ENGINE ---
def minimax_3x3(board, depth, is_maximizing, alpha, beta):
    status = check_winner_3x3(board)
    if status == "O": return 10 - depth
    if status == "X": return depth - 10
    if status == "Draw": return 0

    open_slots = [i for i, cell in enumerate(board) if cell == ""]
    if is_maximizing:
        max_eval = -math.inf
        for move in open_slots:
            board[move] = "O"
            evaluation = minimax_3x3(board, depth + 1, False, alpha, beta)
            board[move] = ""
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha: break
        return max_eval
    else:
        min_eval = math.inf
        for move in open_slots:
            board[move] = "X"
            evaluation = minimax_3x3(board, depth + 1, True, alpha, beta)
            board[move] = ""
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha: break
        return min_eval

def heuristic_evaluate_5x5(board):
    score = 0
    for line in LINES_5x5:
        tokens = [board[idx] for idx in line]
        o_count, x_count = tokens.count("O"), tokens.count("X")
        if o_count > 0 and x_count == 0:
            if o_count == 3: score += 50
            elif o_count == 2: score += 10
            elif o_count == 1: score += 1
        elif x_count > 0 and o_count == 0:
            if x_count == 3: score -= 45
            elif x_count == 2: score -= 8
            elif x_count == 1: score -= 1
    return score

def alphabeta_5x5(board, depth, is_maximizing, alpha, beta):
    status = check_winner_5x5(board)
    if status == "O": return 1000 + depth
    if status == "X": return -1000 - depth
    if status == "Draw": return 0
    if depth == 0: return heuristic_evaluate_5x5(board)

    open_slots = [i for i, cell in enumerate(board) if cell == ""]
    if is_maximizing:
        max_eval = -math.inf
        for move in open_slots:
            board[move] = "O"
            evaluation = alphabeta_5x5(board, depth - 1, False, alpha, beta)
            board[move] = ""
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha: break
        return max_eval
    else:
        min_eval = math.inf
        for move in open_slots:
            board[move] = "X"
            evaluation = alphabeta_5x5(board, depth - 1, True, alpha, beta)
            board[move] = ""
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha: break
        return min_eval

def run_classic_search(board, size):
    open_slots = [i for i, cell in enumerate(board) if cell == ""]
    if not open_slots: return None
    
    best_score = -math.inf
    best_move = open_slots[0]
    
    if size == 3:
        for move in open_slots:
            board[move] = "O"
            score = minimax_3x3(board, 0, False, -math.inf, math.inf)
            board[move] = ""
            if score > best_score:
                best_score, best_move = score, move
    else:
        depth_limit = 3
        for move in open_slots:
            board[move] = "O"
            score = alphabeta_5x5(board, depth_limit - 1, False, -math.inf, math.inf)
            board[move] = ""
            if score > best_score:
                best_score, best_move = score, move
    return best_move

# --- ULTIMATE ENGINE ---
def evaluate_ultimate_board(macro_board, macro_status):
    global_winner = check_winner_3x3(macro_status)
    if global_winner == "O": return 10000
    if global_winner == "X": return -10000
    if global_winner == "Draw": return 0

    score = 0
    macro_weights = [1.2, 1.0, 1.2, 1.0, 1.5, 1.0, 1.2, 1.0, 1.2]
    lines_3x3 = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]

    for line in lines_3x3:
        tokens = [macro_status[idx] for idx in line]
        o_mac, x_mac = tokens.count("O"), tokens.count("X")
        if o_mac > 0 and x_mac == 0:
            score += 300 if o_mac == 2 else 30
        elif x_mac > 0 and o_mac == 0:
            score -= 280 if x_mac == 2 else 25

    for i in range(9):
        if macro_status[i] == "O":
            score += 100 * macro_weights[i]
        elif macro_status[i] == "X":
            score -= 100 * macro_weights[i]
        elif macro_status[i] is None:
            sub_score = 0
            for line in lines_3x3:
                tokens = [macro_board[i][idx] for idx in line]
                o_mic, x_mic = tokens.count("O"), tokens.count("X")
                if o_mic > 0 and x_mic == 0: sub_score += (o_mic * 2)
                elif x_mic > 0 and o_mic == 0: sub_score -= (x_mic * 2)
            score += sub_score * macro_weights[i]
    return score

def calculate_best_ultimate_move(macro_board, macro_status, legal_moves):
    best_score = -math.inf
    best_move = legal_moves[0]
    for move in legal_moves:
        sub, slot = move['sub_board'], move['slot']
        macro_board[sub][slot] = "O"
        prev_status = macro_status[sub]
        macro_status[sub] = check_winner_3x3(macro_board[sub])
        score = evaluate_ultimate_board(macro_board, macro_status)
        macro_board[sub][slot] = ""
        macro_status[sub] = prev_status
        if score > best_score:
            best_score, best_move = score, move
    return best_move

# ==========================================================================
# 4. APPLICATION ROUTES
# ==========================================================================

@app.route('/')
def index():
    #Serves the main application interface.
    return render_template('index.html')

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    if db is None: return jsonify({'success': False, 'message': 'DB offline'}), 503
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = re.sub('<[^<]+?>', '', data.get('name', '').strip())

    if not all([email, password, name]):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400

    if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        return jsonify({'success': False, 'message': 'Password too weak'}), 400

    if db['users'].find_one({'email': email}):
        return jsonify({'success': False, 'message': 'Email exists'}), 409

    user_id = db['users'].insert_one({
        'email': email,
        'name': name,
        'password': generate_password_hash(password),
        'x_wins': 0,
        'o_wins': 0,
        'ties': 0,
        'achievements': []
    }).inserted_id

    session['user_id'] = str(user_id)
    session['nickname'] = name
    session['x_wins'] = 0
    session['o_wins'] = 0
    session['ties'] = 0
    session['achievements'] = []
    return jsonify({'success': True, 'name': name, 'scores': {'X': 0, 'O': 0, 'ties': 0}, 'achievements': []}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    if db is None: return jsonify({'success': False, 'message': 'DB offline'}), 503
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = db['users'].find_one({'email': email})
    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        session['nickname'] = user.get('name', 'Player')
        session['x_wins'] = user.get('x_wins', 0)
        session['o_wins'] = user.get('o_wins', 0)
        session['ties'] = user.get('ties', 0)
        session['achievements'] = user.get('achievements', [])
        return jsonify({'success': True, 'name': session['nickname'], 'scores': {
            'X': session['x_wins'],
            'O': session['o_wins'],
            'ties': session['ties']
        }, 'achievements': session['achievements']}), 200
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True}), 200

@app.route('/api/auth/status', methods=['GET'])
def status():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'name': session.get('nickname', 'Player'), 'scores': {
            'X': session.get('x_wins', 0),
            'O': session.get('o_wins', 0),
            'ties': session.get('ties', 0),
        }, 'achievements': session.get('achievements', [])}), 200
    
    return jsonify({'logged_in': False}), 200

@app.route('/api/sync-profile', methods=['POST'])
def sync_profile():
    data = request.get_json() or {}
    nickname = re.sub('<[^<]+?>', '', data.get('nickname', '').strip())
    if not nickname: return jsonify({"success": False}), 400
    
    session['nickname'] = nickname
    if db is not None and 'user_id' in session:
        try:
            db['users'].update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'name': nickname}})
        except Exception:
            pass
    return jsonify({"success": True, "nickname": nickname})

@app.route('/api/update-scores', methods=['POST'])
def update_scores():
    if db is None: return jsonify({'success': False, 'message': 'DB offline'}), 503
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.get_json()
    x_wins = data.get('X', 0)
    o_wins = data.get('O', 0)
    ties = data.get('ties', 0)

    db['users'].update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'x_wins': x_wins, 'o_wins': o_wins, 'ties': ties}}
    )
    session['x_wins'] = x_wins
    session['o_wins'] = o_wins
    session['ties'] = ties
    return jsonify({'success': True}), 200

@app.route('/api/update-achievements', methods=['POST'])
def update_achievements():
    if db is None: return jsonify({'success': False, 'message': 'DB offline'}), 503
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.get_json()
    badges = data.get('badges', [])

    db['users'].update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'achievements': badges}}
    )
    session['achievements'] = badges
    return jsonify({'success': True}), 200

@app.route('/api/clear-scores', methods=['POST'])
def clear_scores():
    if db is None: return jsonify({'success': False, 'message': 'DB offline'}), 503
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    db['users'].update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'x_wins': 0, 'o_wins': 0, 'ties': 0, 'achievements': []}}
    )
    session['x_wins'] = session['o_wins'] = session['ties'] = 0; session['achievements'] = []
    return jsonify({'success': True}), 200


@app.route('/api/classic-move', methods=['POST'])
def classic_move():
    #Calculates the best move for 3x3 or 5x5 classic games.
    data = request.get_json()
    if not data or 'board' not in data:
        return jsonify({"success": False, "message": "Missing board data"}), 400
        
    board = data.get('board')
    size = int(data.get('size', 3))
    difficulty = data.get('difficulty', 'hard').lower()
    
    try:
        open_slots = [i for i, cell in enumerate(board) if cell == ""]
        if not open_slots:
            return jsonify({"success": False, "message": "No moves available"}), 400

        if difficulty == 'easy':
            ai_index = random.choice(open_slots)
        elif difficulty == 'medium' and random.random() < 0.5:
            ai_index = random.choice(open_slots)
        else:
            ai_index = run_classic_search(board, size)

        return jsonify({"success": True, "move": ai_index})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/ultimate-move', methods=['POST'])
def ultimate_move():
    #Calculates the best move for 9x9 Ultimate Tic-Tac-Toe.
    data = request.get_json()
    if not data or 'macro_board' not in data:
        return jsonify({"success": False, "message": "Missing macro_board data"}), 400
        
    macro_board = data.get('macro_board')
    active_board_index = data.get('active_board_index')
    difficulty = data.get('difficulty', 'hard').lower()
    
    try:
        macro_status = [check_winner_3x3(subgrid) for subgrid in macro_board]
        legal_moves = []
        
        if active_board_index is not None and macro_status[active_board_index] is None:
            for idx, cell in enumerate(macro_board[active_board_index]):
                if cell == "": legal_moves.append({'sub_board': active_board_index, 'slot': idx})
        
        if not legal_moves:
            for s_idx, subgrid in enumerate(macro_board):
                if macro_status[s_idx] is None:
                    for c_idx, cell in enumerate(subgrid):
                        if cell == "": legal_moves.append({'sub_board': s_idx, 'slot': c_idx})

        if not legal_moves:
            return jsonify({"success": False, "message": "No valid moves"}), 400

        if difficulty == 'easy':
            pick = random.choice(legal_moves)
        elif difficulty == 'medium' and random.random() < 0.4:
            pick = random.choice(legal_moves)
        else:
            pick = calculate_best_ultimate_move(macro_board, macro_status, legal_moves)

        return jsonify({"success": True, "sub_board": pick['sub_board'], "slot": pick['slot']})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==========================================================================
# 5. SERVER ENTRY POINT
# ==========================================================================
if __name__ == '__main__':
    app.run(debug=True)
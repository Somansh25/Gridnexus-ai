# Tic-Tac-Toe AI: Ultimate Edition

A modern, feature-rich Tic-Tac-Toe platform featuring classic and advanced game variants, integrated AI, and a sleek neon-inspired UI.

##  Features

*   **Multiple Game Modes:**
    *   **Classic (3x3):** The traditional experience.
    *   **Expanded (5x5):** A larger field for deeper strategy.
    *   **Ultimate (9x9):** A nested macro-grid challenge where every move dictates the opponent's next sector.
*   **Advanced AI:** Play against an intelligent opponent with multiple difficulty levels.
*   **Achievement System:** Unlock badges and track your progress as you master the game.
*   **Responsive Design:** Fully optimized for desktop, tablets, and mobile devices.
*   **Modern UI/UX:** Features a "Glassmorphism" aesthetic with neon accents, smooth transitions, and real-time score tracking.

##  Tech Stack

*   **Frontend:** HTML5, CSS3 (using CSS Variables and Grid/Flexbox), JavaScript (ES6+).
*   **Styling:** Custom CSS system with a dedicated color palette and adaptive breakpoints.

##  Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/tic-tac-toe-ai.git
    ```
2.  **Navigate to the project directory:**
    ```bash
    cd tic-tac-toe-ai
    ```
3.  **Run the application:**
    ```bash
    python app.py
    ```
4.  **Access in Browser:**
    Open `http://localhost:5000` in your web browser.

##  How to Play

1.  **Select a Mode:** Choose between 3x3, 5x5, or Ultimate from the dashboard.
2.  **Configure Match:** Set your difficulty level and toggle AI assistance if needed.
3.  **Ultimate Rules:** In the 9x9 mode, the square you pick in a local 3x3 grid determines which 3x3 grid your opponent must play in next. Win three local grids in a row to win the game!

##  Project Structure

```text
├── index.html          # Main entry point
├── css/                # Stylesheets (Color system, Grids, Components)
├── js/                 # Game logic, AI (Minimax), and UI controllers
├── assets/             # Icons, logos, and badge images
└── README.md
```

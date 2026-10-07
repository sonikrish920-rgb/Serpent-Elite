# 🐍 Serpent Elite — Advanced Snake Game
### Software Engineering Mini Project (Python + Pygame)

---

# 📌 Project Overview

**Serpent Elite** is a modern and advanced version of the classic Snake Game developed using **Python** and **Pygame**.

This project demonstrates:
- Object Oriented Programming (OOP)
- Software Engineering Principles
- SDLC Phases
- Game Loop Architecture
- Event Handling
- Collision Detection
- File Handling
- UI Design
- Modular Programming

The game includes:
- Multiple difficulty levels
- Animated UI
- Power-Ups
- Obstacles
- High Score Saving
- Pause System
- Mouse Clickable Menu
- Neon Styled Graphics

---

# ⚡ Features

## 🎮 Gameplay Features
- Smooth snake movement
- Dynamic speed increase
- Score & Level system
- Game Over screen
- Pause / Resume support
- Restart support

---

## 🍎 Food System

Three different food types:

| Food Type | Score | Effect |
|-----------|------|---------|
| Normal Food | +1 | Grow snake |
| Bonus Food | +5 | Large growth |
| Poison Food | -2 | Shrinks snake |

---

## ⚡ Power-Up System

The game includes special gameplay mechanics:
- Bonus food
- Poison food
- Speed progression
- Level-based challenge system

---

## 🔥 UI Features
- Mouse-clickable menu
- Animated buttons
- Sidebar HUD
- Neon glow effects
- Smooth rendering
- Modern dark theme

---

## 🧱 Obstacles
- Random obstacle generation
- Difficulty-based obstacle spawning
- Collision detection

---

# 🏗️ Software Engineering Concepts Used

## SDLC Phases Implemented

| SDLC Phase | Implementation |
|------------|---------------|
| Requirement Analysis | Feature planning |
| System Design | OOP class structure |
| Implementation | Modular Python code |
| Testing | Manual gameplay verification |
| Maintenance | Config-based editable values |

---

# 🧩 OOP Architecture

```text
Game (Main Controller)
│
├── Snake
├── Food
├── Obstacle
├── ScoreManager
├── Renderer
└── InputHandler
```

---

# 📂 Project Structure

```text
Serpent-Elite/
│
├── snake_game.py
├── snake_game.spec
├── README.md
├── requirements.txt
└── assets/
    └── game_demo.mp4
```

---

# ⚙️ Requirements

## Python Version
- Python 3.10 or above

## Required Library
- pygame-ce (Pygame Community Edition, using the `pygame` import)

---

# 📥 Installation

## Step 1 — Install Python

Download Python from:

https://www.python.org/downloads/

⚠️ IMPORTANT:

While installing Python, enable:

```text
☑ Add Python to PATH
```

---

## Step 2 — Install Pygame

Open terminal / CMD:

```bash
python -m pip install -r requirements.txt
```

---

# ▶️ Run the Game

Open terminal inside project folder:

```bash
python snake_game.py
```

---

# 🎮 Controls

| Key | Action |
|-----|--------|
| ↑ ↓ ← → | Move Snake |
| W A S D | Move Snake |
| P | Pause / Resume |
| R | Restart |
| ENTER | Start Game |
| ESC | Quit |

---

# 🎯 Difficulty Levels

| Difficulty | Speed | Obstacles | Wall Wrap |
|------------|------|------------|-----------|
| Easy | Slow | No | Yes |
| Medium | Medium | Yes | No |
| Hard | Fast | Yes | No |

---

# 💾 High Score System

The game automatically saves the highest score using:

```text
serpent_highscore.json
```

This file is created automatically after playing.

---

# 🖥️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Core Programming |
| Pygame | Game Development |
| JSON | High Score Saving |
| OOP | Architecture Design |

---

# 🧠 Concepts Used

- Event Driven Programming
- Game Loop
- Collision Detection
- Rendering Engine
- State Machine
- File Handling
- Timers
- Animations
- Grid Movement Logic

---

# 🔄 Game State Machine

```text
MENU
  │
  ▼
PLAYING
  │
  ├──► PAUSED
  │
  ▼
GAME OVER
  │
  ▼
RESTART
```

---

# 🚀 Future Improvements

Possible future upgrades:
- Multiplayer Mode
- Online Scoreboard
- AI Snake Opponent
- Mobile APK Version
- More Power-Ups
- Custom Themes
- Controller Support

---

# 🧪 Testing

No automated test suite is included. Run the game using the instructions above
to verify gameplay, collision, food, pause/restart, and high-score behavior.

---

# 📚 Learning Outcomes

Through this project, the following concepts were learned:
- Python game development
- OOP implementation
- SDLC practical usage
- Event handling
- Real-time rendering
- Game optimization
- UI/UX basics

---

# 👨‍💻 Author

**Krish Soni**
B.Tech Computer Science Engineering

---

# 📜 License

This project is created for educational and academic purposes only.

---

# ❤️ Thank You

Thank you for checking out **Serpent Elite** 🐍
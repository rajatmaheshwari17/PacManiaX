
# PacManiaX


This project implements an advanced AI for a multi-agent capture-the-flag variant of the Pac-Man game. The primary goal is to design offensive and defensive agents capable of working collaboratively to maximize team performance. The project involves heuristic decision-making, dynamic role switching, and effective pathfinding to address the challenges posed by this adversarial game environment.

## Features
- **Fully Observable Game State**: Agents have access to real-time positions of all players.
- **Offensive and Defensive Strategies**: Separate roles for agents, allowing specialization in attacking or defending.
- **Dynamic Role Switching**: Adaptive strategies that adjust based on the current game state.
- **Efficient Pathfinding**: A* search algorithm for optimized movement through the maze.
- **Patrol Logic for Defense**: The defensive agent patrols border points to secure the team’s territory.
- **Food Hunting for Offense**: The offensive agent prioritizes collecting food while avoiding ghosts.




## Agent Implementation
### Defensive Agent
The DefensiveAgent secures the team’s territory by:
- Patrolling border points to prevent opponents from stealing food.
- Chasing visible invaders using safe movement strategies.
- Prioritizing invader interception while ensuring safe positioning.

Key Functions:
- `getFullBorderPatrolPoints`: Identifies patrol points along the border.
- `moveTowardsSafely`: Moves towards a target while avoiding dangerous positions.
- `chaseSafely`: Pursues invaders within the team’s territory.
- `patrolBorder`: Cycles through patrol points for consistent defense.

### Offensive Agent
The OffensiveAgent focuses on food collection in the opponent’s territory by:
- Prioritizing food collection while avoiding nearby ghosts.
- Escaping from dangerous ghost positions.
- Evaluating food targets based on proximity and safety.

Key Functions:
- `getVisibleGhosts`: Identifies ghosts and their scared status.
- `escapeGhost`: Calculates the safest move to avoid ghosts.
- `huntFood`: Identifies and moves towards the most favorable food target.

## Strategies
### Classic Strategy
- One agent focuses on offense while the other focuses on defense.

### Dual-Offense Strategy
- Both agents prioritize attacking the opponent’s territory to maximize food collection.

### Adaptive Strategy
- Agents dynamically switch between offense and defense based on the game state.

## Usage
### Setting Up the Environment
1. Clone the repository:
   ```bash
   git clone git@github.com:rajatmaheshwari17/PacManiaX.git
   cd PacManiaX
   ```
2. Install dependencies (if applicable):
   ```bash
   pip install -r requirements.txt
   ```

## Evaluation
- **Win Rate**: Assessed against baseline agents.
- **Score Differential**: Measured as the difference in scores between our team and opponents.
- **Adaptability**: Evaluated through performance across dynamic scenarios.

## Lessons Learned
1. Dynamic role adaptation enhances performance in multi-agent settings.
2. Balancing offensive and defensive strategies is crucial for success.
3. Coordination between agents significantly improves overall effectiveness.

#
_This README is a part of the PacManiaX Project by Rajat Maheshwari._

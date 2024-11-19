import os
import random

def run_games(num_games=1000):
    wins = 0
    losses = 0
    ties = 0

    for i in range(num_games):
        # Generate a random seed for each game.
        seed = random.randint(1, 10000)
        print(f"Running game {i + 1} with seed {seed}...")

        # Run the game using the generated seed.
        result = os.system(
            f"python3 -m pacai.bin.capture --layout RANDOM{seed} --null-graphics "
        )

        # Check result (assuming non-zero exit codes indicate loss).
        if result == 0:
            wins += 1
        elif result == 1:
            losses += 1
        else:
            ties += 1

    # Calculate statistics.
    win_percentage = (wins / num_games) * 100
    loss_percentage = (losses / num_games) * 100
    tie_percentage = (ties / num_games) * 100

    # Print the summary.
    print("\n--- Game Summary ---")
    print(f"Total Games: {num_games}")
    print(f"Wins: {wins} ({win_percentage:.2f}%)")
    print(f"Losses: {losses} ({loss_percentage:.2f}%)")
    print(f"Ties: {ties} ({tie_percentage:.2f}%)")

# Run the simulation.
if __name__ == "__main__":
    run_games()


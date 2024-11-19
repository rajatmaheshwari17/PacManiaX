def calculateMemoryPoints(memory):
    total_points = 0
    cumulative_sum = 0

    # Calculate cumulative sum in the given input order, treating negatives as positive
    for chapter in memory:
        cumulative_sum += abs(chapter)  # Use absolute value of chapter's memory
        total_points += cumulative_sum  # Add cumulative sum to total points

    return total_points

# Example usage:
n = int(input())  # Size of the memory array (n)
memory = [int(input()) for _ in range(n)]  # Memory values from input

# Calculate and print the total memory points
print(calculateMemoryPoints(memory))

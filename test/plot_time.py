import matplotlib.pyplot as plt
import numpy as np


# Read transfer times from the log file
def read_transfer_times(filename="transfer_times.txt"):
    transfer_times = []

    try:
        with open(filename, "r") as file:
            for line in file:
                parts = line.strip().split(": ")
                if len(parts) == 2:
                    time_taken = float(parts[1].replace(" seconds", "").strip())
                    transfer_times.append(time_taken)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []

    return transfer_times


# Plot the data with average and standard deviation
def plot_transfer_times():
    transfer_times = read_transfer_times()

    if not transfer_times:
        print("No data to plot.")
        return

    x_values = range(1, len(transfer_times) + 1)
    avg_time = np.mean(transfer_times)
    std_dev = np.std(transfer_times)

    plt.figure(figsize=(10, 5))
    plt.plot(
        x_values,
        transfer_times,
        marker="o",
        linestyle="-",
        color="blue",
        alpha=0.7,
        label="Download Time",
    )
    plt.axhline(
        y=avg_time, color="red", linestyle="--", label=f"Avg: {avg_time:.4f} sec"
    )
    plt.axhline(
        y=avg_time + std_dev,
        color="green",
        linestyle="--",
        label=f"+1σ: {avg_time + std_dev:.4f} sec",
    )
    plt.axhline(
        y=avg_time - std_dev,
        color="green",
        linestyle="--",
        label=f"-1σ: {avg_time - std_dev:.4f} sec",
    )

    plt.xlabel("Image Sequence Number")
    plt.ylabel("Download Time (seconds)")
    plt.title("03/08/25 Server v1 Performance for 1000, 12MP(36MB) Images")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    plt.show()


# Execute the function
plot_transfer_times()
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter


# Seed for reproducibility
np.random.seed(0)

# Generate data
x = np.linspace(0, 10, 1000)
y = np.concatenate([np.ones(200) * 5, np.linspace(5, 20, 50), np.ones(750) * 20])
y += np.random.normal(scale=0.1, size=y.size)

# Calculate the first derivative of the data
dy = np.diff(y) / np.diff(x)

# Smooth the derivative to reduce noise
dy_smoothed = gaussian_filter(dy, sigma=5)

# Find the start and end of the ramp
# Threshold for the derivative could be determined by looking at the smoothed derivative plot
threshold = 10
ramp_start = np.where(dy_smoothed > threshold)[0][0] + 1  # +1 to correct index after diff
ramp_end = np.where(dy_smoothed > threshold)[0][-1] + 1

# Plot the results
plt.figure(figsize=(12, 6))
plt.subplot(211)
plt.plot(x, y, label='Data')
plt.axvline(x[ramp_start], color='r', linestyle='--', label='Ramp Start')
plt.axvline(x[ramp_end], color='g', linestyle='--', label='Ramp End')
plt.legend()

plt.subplot(212)
plt.plot(x[:-1], dy_smoothed, label='Smoothed Derivative')
plt.axhline(threshold, color='black', linestyle='--', label='Threshold')
plt.axvline(x[ramp_start], color='r', linestyle='--')
plt.axvline(x[ramp_end], color='g', linestyle='--')
plt.legend()

plt.show()
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from LogReader import LogReader
from Event import Event, Channel, get_channel


# Get data
reader = LogReader()
reader.read_events("logs/example1.xz")
for e in reader.events[::-1]:
    if e.event_type == Event.DEPRESSURIZE:
        event = e
        break

y = get_channel(event, Channel.HI_PRE_SAMPLE)
x = range(len(y))

# Calculate the first derivative of the data
dy = np.diff(y) / np.diff(x)
dy_smoothed = gaussian_filter(dy, sigma=5)

# Find the start and end of the ramp
if event.event_type == Event.PRESSURIZE:
    threshold = 0.4 * max(dy_smoothed)
    ramp_start = np.where(dy_smoothed > threshold)[0][0] + 1  # +1 to correct index after diff
    ramp_end = np.where(dy_smoothed > threshold)[0][-1] + 1
elif event.event_type == Event.DEPRESSURIZE:
    threshold = 0.4 * min(dy_smoothed)
    ramp_start = np.where(dy_smoothed < threshold)[0][0] + 1  # +1 to correct index after diff
    ramp_end = np.where(dy_smoothed < threshold)[0][-1] + 1

print(threshold)

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
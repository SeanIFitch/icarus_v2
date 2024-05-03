import numpy as np
o = np.ones(10)
i = [0,2,4,9]
step_sums = np.add.reduceat(o, i)
print(step_sums)

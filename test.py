import array

# Create an array of integers
my_array = array.array('i', [1, 2, 3, 4, 5])

# Create a memoryview from the array
my_view = memoryview(my_array)

# Access a slice without copying
my_slice = my_view[1:4]

# Modify the slice
for i in range(len(my_slice)):
    my_slice[i] += 10

# Print the original array
print(my_array)
print(type(my_view))
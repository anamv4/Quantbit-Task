# Reverse a string without using built-in methods.

s="hello"
reverse= " "
for i in range(len(s) - 1, -1, -1):
    reverse += s[i]
print(reverse)  

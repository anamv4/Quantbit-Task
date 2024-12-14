# Validate user input as an integer.

while True:  
    user = input()
    is_number = True

    for char in user:  
        if char < '0' or char > '9':  
            print("Invalid input. Please enter a number.") 
            is_number = False
            break
    
    if is_number:
        print(f"You entered: {user}")
        break  
          

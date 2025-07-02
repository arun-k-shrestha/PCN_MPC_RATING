# Yao's Millionaires' Protocol Implementation
#source: https://www.youtube.com/watch?v=gf4BawfCY1A

# Example usage
import random
import math

# Shared transformation used by both parties
def sharedFunction(x):
    return (x * 7 + 42) % 997  # Simple linear transformation

# Encodes a number by dividing with the shared randomNum1
def Inverse(x, r):
    return x / r

# Reverses the encoded number by multiplying with randomNum1
def reverseInverse(x, r):
    return r * x

# Simulated Yao's Millionaires' Protocol 
def Yao_Millionaires_Protocol(Intermediate_Node, Sender, Highest, randomNum, randomNum1=random.randint(1, 500)):
    # Mask the sender's value using an inverse transformation
    masked_value = Inverse(randomNum, randomNum1) - Sender
    encoded_values = []

    # Generate hidden values from 0 to Highest
    for i in range(0, Highest):
        hidden = reverseInverse(masked_value + i, randomNum1)
        transform = sharedFunction(hidden)
        encoded_values.append(transform)

    # Add +1 to values starting from Intermediate_Node to Highest
    lowerBound = round(Intermediate_Node)
    for i in range(lowerBound, Highest):
        encoded_values[i] += 1

    # Compute the comparison value (check if it's among the encoded values)
    checker = sharedFunction(randomNum) + 1

    # Use safe float comparison
    if any(math.isclose(val, checker, rel_tol=1e-9) for val in encoded_values): # because when x = 0.1 + 0.2 the print(x == 0.3) -> False but print(math.isclose(x, 0.3)) ->  True
        return True  # Sender is richer than Intermediate_Node
    else:
        return False  # Sender is not richer


# Run multiple times with the same parameters
# for i in range(10):
#     result = Yao_Millionaires_Protocol(
#         Intermediate_Node=40,
#         Sender=90,
#         Highest=90,
#         randomNum=90,
#     )
#     print(result)




# import random
# randomNum1 = random.randint(1,10) #radomNum1 should be less than half of the highest value
# randomNum2 = random.randint(1,10)


# def Inverse(x):
#     return x/randomNum1
# def sharedFunction(x):
#     return x/300

# # Alice -> amount d  -> Bob
# def reverseInverse(x):
#     return randomNum1*x

# def Yao_Millionaires_Protocol(Intermediate_Node, Sender, Highest, randomNum):
#     InverseRandomNum = Inverse(randomNum)
#     masked_value = InverseRandomNum - Sender
#     encoded_values= []

#     for i in range(0,Highest):
#         hidden =reverseInverse(masked_value+i) 
#         transform = sharedFunction(hidden)
#         encoded_values.append(transform)

#     lowerBound = round(Intermediate_Node)
# # 
#     for i in range(lowerBound ,Highest):
#         encoded_values[i] = encoded_values[i]+1

#     checker = sharedFunction(randomNum) +1
#     if checker in encoded_values:
#         #print("Sender is richer")
#         return True
#     else:
#         return False
# print(Yao_Millionaires_Protocol(400, 90, 1000, 10))

# https://www.youtube.com/watch?v=gf4BawfCY1A


# Alice = 90
# Bob = 5
# Highest = 100000
# randomNum = 250

# def Eb(x):
#     return x/2
# def sharedFunction(x):
#     return x/3

# c = Eb(randomNum)
# d = c -Alice

# # Alice -> amount d  -> Bob
# def Db(x):
#     return 2*x

# lis = []

# for i in range(0,Highest):
#     a =Db(d+i)
#     b = sharedFunction(a)
#     lis.append(b)

# lowerBound = round(Bob)
# # 
# for i in range(lowerBound,Highest):
#     lis[i] = lis[i]+1

# print(lis)

# def finalChecker(x):
#     a = sharedFunction(randomNum) +1
#     if a in lis:
#         print("Alice is rlicher")
#     else:
#         print("no")

# finalChecker(randomNum)

# # https://www.youtube.com/watch?v=gf4BawfCY1A


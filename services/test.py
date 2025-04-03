a="My name is Sanjeev Kumar"

smallstring=0
capitalstring=0
for i in a:
    if i.islower():
        smallstring+=1
    elif i.isupper():
        capitalstring+=1
print(f"Total smallstring is {smallstring} and Total capitalstring is {capitalstring}")
    

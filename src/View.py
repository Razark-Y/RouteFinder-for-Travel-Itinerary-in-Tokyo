import pickle
pickleFile = open("../graph.pkl","rb")
personInfo = pickle.load(open("../graph.pkl", "rb"))
print (personInfo)
from models import *

print("-----------")
# On supprime tous les appels et les opérateurs déjà enregistrés dans Redis 
Call.destroy_all()
Operator.destroy_all()


# Création d'un appel et d'un opérateur")
appel = Call("0607080910")
operateur = Operator("Alexis","Dbn")

# Afficher les données d'un appel 
print("data appel :",appel.data())
print("data operator",operateur.data())

coordinator = Coordinator()
coordinator.assign_all()

appel.description = "test"

appel.end()

# Faire une fonction qui met fin à l'appel :
#     operateur : status = 0 
#     operateur : call_id = 0
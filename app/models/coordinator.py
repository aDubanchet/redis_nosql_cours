from webbrowser import Opera
from .operator import *
from .call import *


class Coordinator:
    @staticmethod
    def assign_all():
        appels = Call.list()
        operateurs = Operator.list()
        for appel in appels:
            if appel['status'] == '0':
                for operateur in operateurs:
                    if operateur['status'] == "0":
                        # On récupère les objets
                        appel_instance = Call.get_instance_by_id(appel['id'])
                        operateur_instance = Operator.get_instance_by_id(operateur['id'])
                        
                        # On change les attributs
                        appel_instance.status = 1
                        operateur_instance.call_id = appel['id']
                        operateur_instance.status = 1
                        print(f"Appel {appel['id']} assigné à l'opérateur {operateur['id']}")
                        break
                else:
                    print(f"Aucun opérateur disponible pour l'appel {appel['id']}")
            else:
                print(f"L'appel {appel['id']} est déjà en cours")

        return

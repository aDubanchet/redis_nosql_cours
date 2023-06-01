from datetime import datetime
from dataclasses import dataclass
from queue import Empty
import redis 

redis_connexion = redis.Redis(host="localhost",port=6379)

@dataclass 
class Operator():
    def __init__(self,firstname,surname,id=0):
        self._id = id
        self._firstname = firstname
        self._surname = surname
        self._status = 0 
        self._call_id = 0

        self.__post_init__()

    def __post_init__(self):
        # méthode appelée après la création de l'objet 
        # permettant d'enregistrer l'objet dans Redis


        # ------------------------------
        ## Générer l'identifiant 
        # ------------------------------
        if self._id == 0 : 
            # on récupère l'identifiant du dernier appel 
            identifiants_operateurs = redis_connexion.smembers("identifiants_operateurs") 

            if len(identifiants_operateurs) != 0 : 
                # Conversion des valeurs en entiers
                valeurs_entiers = [int(valeur) for valeur in identifiants_operateurs]

                identifiant_max = max(valeurs_entiers)

                # le nouvel appel aura l'id le plus élevé de identifiants_appels_entrants + 1
                self._id = identifiant_max + 1
            else :
                self._id = 1 
            # ------------------------------
            ## Enregistrer dans Redis
            # ------------------------------
            # On vérifie avant que l'objet n'est pas déjà dans Redis : 
            identifiant_operateur = redis_connexion.smembers("identifiants_operateurs")
        
            # on décode le set 
            identifiant_operateur = {element.decode() for element in identifiant_operateur}
            
            if self._id not in identifiant_operateur:

                # On enregistre l'identifiant de l'appel 
                redis_connexion.sadd("identifiants_operateurs",repr(self._id).encode('utf-8'))

                # Première méthode : utilisant hset 


                redis_connexion.hset(
                    "operateur :{}".format(repr(self._id).encode('utf-8')),
                    "firstname",self._firstname.encode()
                )

                redis_connexion.hset(
                    "operateur :{}".format(repr(self._id).encode('utf-8')),
                    "surname",self._surname.encode()
                ) 

                print("Enregistré dans Redis")

        return self
        

    # ------------------------------
    # Propriétés de classe personnalisés
    # ------------------------------
    @property
    def status(self):
        # 0 quand l'operateur n'a pas d'appels, 1 quand il est déjà au téléphone
        return self._status 

    @status.setter
    def status(self,value):
        # Pour assigner un opérateur à un Call 
        self._status = value
        redis_connexion.hset(
            "operateur :{}".format(repr(self._id).encode('utf-8')),
            "status",value
        )

        return self

    @property
    def call_id(self):
        return self._call_id

    @call_id.setter
    def call_id(self,id_call):
        # Pour assigner un status à un Call 


        # Si status = 0, càd que l'opérateur n'a pas d'appels 
        if self.status == 0 :
        # Si call_id == 0 : ça que l'opérateur n'a pas d'appels
            if self.call_id == 0 :
                # Si le call n'a pas d'opérateurs
                # cad si call.status == 0 

                # On récupère la liste des appels entrants pour un identifiant donné 
                details_appel = redis_connexion.hgetall("appels_entrants :{}".format(id_call)) 
                
                # On vérifie si l'appel existe bien 
                if not details_appel :
                    raise Exception("L'appel n'a pas été trouvé")

                # Si aucun operateur ou si le status de l'appel n'a pas été défini 
                if details_appel['operator_id'] == 0 and details_appel['status'] == 0 :

                    # on attribute l'appel à l'opérateur 
                    self._call_id = id_call
                    redis_connexion.hset(
                        "operateur :{}".format(repr(self._id).encode('utf-8')),
                        "call_id",id_call
                    )

                    # On attribue ensuite l'opérateur à l'appel 
                    # TODO 

                else :
                    raise Exception("L'appel a déjà un opérateur d'affecté.")
            else :
                raise Exception("L'opérateur a déjà un appel.")
        else :
            raise Exception("L'opérateur n'est pas disponible.")


        return self
        
    # ------------------------------
    # Méthodes de l'objet
    # ------------------------------

    def data(self):
        """
        Retourne les caractéristiques de l'appel
        """

        details_operateur = redis_connexion.hgetall("operateur :{}".format(repr(self._id).encode('utf-8')))

        details_operateur['id'] = self._id # on ajoute l'identifiant au dictionnaire 

        return details_operateur

    def destroy(self):
        """
        Supprime un appel 
        """
        # supprimer l'élément id du set redis 
        result = redis_connexion.srem("identifiants_operateurs",self._id)

        # supprimer le hachage Redis contenant les caractéristiques de l'appel 
        redis_connexion.delete("operateur :{}".format(self._id))
        del self 

    # ------------------------------
    # Méthodes statiques
    # ------------------------------
    @staticmethod
    def list():
        """
        Liste tous les opérateurs ainsi que leurs descriptions, 
        enregistrés dans le hash Redis operateur + id 
        """
        operateurs = []
        identifiants_operateurs= redis_connexion.smembers("identifiants_operateurs")
        for identifiant in identifiants_operateurs:
            details_operateur = redis_connexion.hgetall("operateur :{}".format(identifiant))   
            details_operateur["id"] = identifiant # on ajoute l'identifiant au dictionnaire
            operateurs.append(details_operateur) 

        return operateurs

    @staticmethod
    def get_instance_by_id(identifiant):
        """
        Retourne un objet Operateur pour un identifiant donné
        """
        identifiant_operateur= redis_connexion.smembers("identifiants_operateurs")
        if identifiant in identifiant_operateur:

            details_operateur = redis_connexion.hgetall("operateur :{}".format(identifiant))
            firstname = details_operateur.get(b"firstname", b"").decode()
            surname = details_operateur.get(b"surname", b"").decode()

            # Créer une nouvelle instance d'opérateur avec les informations récupérées
            instance = Operator(firstname, surname,id=identifiant)

            # Récupérer et assigner les autres attributs de l'opérateur (status, call_id, etc.)
            instance._status = int(details_operateur.get(b"status", 0))
            instance._call_id = int(details_operateur.get(b"call_id", 0))

            return instance

        raise Exception("L'opérateur n'existe pas. ")


if __name__ == '__main__' : 
    operateur = Operator("Alexis","Dubanchet")
    operateur.call_id = 1
    operateur.status = 1
    for operateur in (Operator.list()) : 
        print(operateur)


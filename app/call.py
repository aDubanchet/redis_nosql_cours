from datetime import datetime
from dataclasses import dataclass
import redis 

redis_connexion = redis.Redis(host="localhost",port=6379)

@dataclass 
class Call():
    """
    Attributs de classe :
        - id : Initialisé à la création : privé 
        - creation_time : Initialisé à la création : privé
        - phone_number : Initialisé à la création : privé 
        - status : Initialisé à la création : Public 
        - duree : Uniquement en lecture, n'est pas écrit dans redis 
        - operator_id : Initialisé au cours de l'appel : Public
        - description : Initialisé au cours de l'appel : Public
    
    Setters publics de la classe : 
        - operator_id
        - description
        - status
            0 pour en Attente
            1 pour Pris 
            2 pour Terminé 

    Méthodes publiques de la classe : 
        Propres à une instance :
            - data(self)
            - destroy(self)

        Propres à Call : 
            - list_id()
            - list()
            - destroy_all()

    Limites de la classe :
        - Ne gère pas encore les erreurs si l'objet n'a pas réussi à être sauvegardé dans Redis 
        - la méthode durée ne peut pas s'utiliser sur les données de Redis, uniquement sur les objets 
        - Décoder en string le listing 
        - Ne gère pas les appels attendant depuis longtemps
    """

    def __init__(self,phone_number,id=0):
        self._id = id 
        self._creation_time = datetime.now() # _ pour dire que ce sont des attributs privés
        self._phone_number = phone_number
        self._status = 0
        self._description = ""

        self.__post_init__()

    def __post_init__(self):
        # méthode appelée après la création de l'objet 
        # permettant d'enregistrer l'objet dans Redis

        # ------------------------------
        ## Générer l'identifiant 
        # ------------------------------
        if self._id == 0 :
            # on récupère l'identifiant du dernier appel 
            identifiants_appels_entrants = redis_connexion.smembers("identifiants_appels_entrants") 

            if len(identifiants_appels_entrants) != 0 : 
                # Conversion des valeurs en entiers
                valeurs_entiers = [int(valeur) for valeur in identifiants_appels_entrants]

                identifiant_max = max(valeurs_entiers)

                # le nouvel appel aura l'id le plus élevé de identifiants_appels_entrants + 1
                self._id = identifiant_max + 1
            else :
                self._id = 1

            # ------------------------------
            ## Enregistrer dans Redis
            # ------------------------------
            
            # On vérifie avant que l'objet n'est pas déjà dans Redis : 
            identifiants_appels = redis_connexion.smembers("identifiants_appels_entrants")
            
            # on décode le set 
            identifiants_appels = {element.decode() for element in identifiants_appels}

            if self._id not in identifiants_appels : 
                # On enregistre l'identifiant de l'appel 
                redis_connexion.sadd("identifiants_appels_entrants",repr(self._id).encode('utf-8'))

                # Première méthode : utilisant hset 
                redis_connexion.hset(
                    "appels_entrants :{}".format(repr(self._id).encode('utf-8')),
                    "creation_time",self._creation_time.strftime("%m/%d/%Y, %H:%M:%S").encode()
                )
                redis_connexion.hset(
                    "appels_entrants :{}".format(repr(self._id).encode('utf-8')),
                    "phone_number",self._phone_number.encode()
                )

                print("Enregistré dans Redis")
        return self

    # ------------------------------
    # Propriétés de classe personnalisés
    # ------------------------------
    @property
    def operator_id(self):
        return self.operator_id 

    @operator_id.setter
    def operator_id(self,value):
        # Pour assigner un opérateur à un Call 
        redis_connexion.hset(
            "appels_entrants :{}".format(repr(self._id).encode('utf-8')),
            "operator_id",value
        )

        return self

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self,value):
        # Pour assigner un status à un Call 

        self._status = value

        redis_connexion.hset(
            "appels_entrants :{}".format(repr(self._id).encode('utf-8')),
            "status",value
        )
        return self

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self,value):
        # Pour assigner une description à un Call 

        self._description = value

        redis_connexion.hset(
            "appels_entrants :{}".format(repr(self._id).encode('utf-8')),
            "description",value
        )
        return self

    @property
    def duree(self):
        # une méthode calculant la durée à chaque fois qu'il est appelé
        current_time = datetime.now()
        datetime_creation_time = datetime.strptime(self._creation_time, "%m/%d/%Y, %H:%M:%S")
        duration = current_time - datetime_creation_time 
        return duration.total_seconds()
    
    # ------------------------------
    # Méthodes de l'objet
    # ------------------------------

    def data(self):
        """
        Retourne les caractéristiques de l'appel
        """
        

        details_appel = redis_connexion.hgetall("appels_entrants :{}".format(repr(self._id).encode('utf-8')))

        details_appel['id'] = self._id # on ajoute l'identifiant au dictionnaire 

        details_appel['duree'] = self.duree # on ajoute la durée au dictionnaire 

        return details_appel

    def destroy(self):
        """
        Supprime un appel 
        """
        # supprimer l'élément id du set redis 
        redis_connexion.srem("identifiants_appels_entrants",repr(self._id).encode('utf-8'))

        # supprimer le hachage Redis contenant les caractéristiques de l'appel 
        redis_connexion.delete("appels_entrants :{}".format(self._id))
        del self 

    # ------------------------------
    # Méthodes statiques
    # ------------------------------
    @staticmethod
    def list_id():
        """
        Liste tous les identifiants des appels enregistrés dans Redis,
        enregistrés dans le set identifiants_appels_entrants
        """
        return redis_connexion.smembers("identifiants_appels_entrants")

    @staticmethod
    def list():
        """
        Liste tous les appels ainsi que leurs descriptions, 
        enregistrés dans le hash Redis appels_entrants + id 
        """
        appels = []
        identifiants_appels_entrants = redis_connexion.smembers("identifiants_appels_entrants")
        for identifiant in identifiants_appels_entrants:
            details_appel = redis_connexion.hgetall("appels_entrants :{}".format(identifiant))   
            details_appel["id"] = identifiant # on ajoute l'identifiant au dictionnaire 
            appels.append(details_appel)

        return appels

    @staticmethod
    def destroy_all():
        """
        Supprime tous les appels : 
        - Dans le set identifiants_appels_entrants contenant les id 
        - Dans le hash appels_entrants contenant les détails des appels 
        """
        # On récupère tous les identifiants enregistrés 
        all_keys = Call.list_id()

        # Parcourir les clés et supprimer les hachages redis 
        for key in all_keys:
            # on supprime l'identifiant du set contenant les identifiants 
            redis_connexion.srem("identifiants_appels_entrants",key)

            # on supprime les éléments du hash contenant les détails de l'appel 
            redis_connexion.delete("appels_entrants :{}".format(key))

        all_keys = Call.list_id()

    @staticmethod
    def get_instance_by_id(identifiant):
        """
        Retourne un objet Call pour un identifiant donné
        """
        identifiants_appels_entrants = redis_connexion.smembers("identifiants_appels_entrants")

        if identifiant in identifiants_appels_entrants:
            details_appel = redis_connexion.hgetall("appels_entrants :{}".format(identifiant))
            phone_number = details_appel.get(b"phone_number", b"").decode()

            # Créer une nouvelle instance d'appel avec les informations récupérées
            instance = Call(phone_number,id=identifiant)

            # Récupérer et assigner les autres attributs de l'appel (status, operator_id, description)
            instance._status = int(details_appel.get(b"status", 0))
            instance._phone_number = int(details_appel.get(b"phone_number", 0))
            instance._description = details_appel.get(b"description", b"").decode()
            instance._creation_time = details_appel.get(b"creation_time", b"").decode()
            
            return instance

        raise Exception("L'appel n'existe pas.")

    @staticmethod
    def list_entring_call():
        """
        Liste les appels entrants
        """
        pass

if __name__ == '__main__' : 
    
    for x in Call.list():
        appel = Call.get_instance_by_id(x['id'])
        appel.destroy()
    Call.list()
    
    #Call.destroy_all()
    
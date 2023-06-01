import unittest
from datetime import datetime
from dataclasses import dataclass
import redis

from call import *

@dataclass
class CallTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def setUp(self):
        # Initialiser la connexion Redis pour les tests
        self.redis_connexion = redis.Redis(host="localhost", port=6379)
        self.redis_connexion.flushdb()

    def tearDown(self):
        # Vider la base de données Redis après les tests
        self.redis_connexion.flushdb()

    def test_call_creation(self):
        # Teste la création d'un appel avec les attributs attendus
        phone_number = "0678675532"
        call = Call(phone_number)

        self.assertEqual(call.phone_number, phone_number)
        self.assertIsInstance(call.creation_time, datetime)
        self.assertEqual(call.status, "")

        # Vérifier que l'appel a été enregistré dans Redis
        identifiants_appels_entrants = self.redis_connexion.smembers("identifiants_appels_entrants")
        self.assertEqual(len(identifiants_appels_entrants), 1)

        call_details = self.redis_connexion.hgetall(f"appels_entrants :{call.id}")
        self.assertEqual(call_details[b"phone_number"].decode(), phone_number)

    def test_call_properties(self):
        # Teste la modification des propriétés personnalisées d'un appel
        phone_number = "0678675532"
        call = Call(phone_number)

        # Teste la propriété `operator_id`
        operator_id = "123"
        call.operator_id = operator_id
        call_details = self.redis_connexion.hgetall(f"appels_entrants :{call.id}")
        self.assertEqual(call_details[b"operator_id"].decode(), operator_id)

        # Teste la propriété `description`
        description = "Bonjour, je m'appelle Alexis"
        call.description = description
        call_details = self.redis_connexion.hgetall(f"appels_entrants :{call.id}")
        self.assertEqual(call_details[b"description"].decode(), description)

    def test_call_destroy(self):
        # Teste la suppression d'un appel
        phone_number = "0678675532"
        call = Call(phone_number)

        # Vérifier que l'appel est présent dans Redis
        self.assertIn(call.id.encode(), self.redis_connexion.smembers("identifiants_appels_entrants"))
        self.assertTrue(self.redis_connexion.exists(f"appels_entrants :{call.id}"))

        # Supprimer l'appel
        call.destroy()

        # Vérifier que l'appel a été supprimé de Redis
        self.assertNotIn(call.id.encode(), self.redis_connexion.smembers("identifiants_appels_entrants"))
        self.assertFalse(self.redis_connexion.exists(f"appels_entrants :{call.id}"))

    def test_call_list(self):
        # Teste la méthode statique `list()` pour récupérer la liste des appels
        phone_number1 = "0628728192"
        call1 = Call(phone_number1)
        call1.description = "Test 1"

        phone_number2 = "0712345678"
        call2 = Call(phone_number2)
        call2.description = "Test 2"

        # Récupérer la liste des appels
        calls = Call.list()

        # Vérifier que les détails des appels sont corrects
        self.assertEqual(len(calls), 2)

        call1_details = self.redis_connexion.hgetall(f"appels_entrants :{call1.id}")
        self.assertIn(call1_details, calls)

        call2_details = self.redis_connexion.hgetall(f"appels_entrants :{call2.id}")
        self.assertIn(call2_details, calls)


if __name__ == "__main__":
    unittest.main()

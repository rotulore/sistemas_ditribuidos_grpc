import grpc
from concurrent import futures
from datetime import datetime, timezone
from google.protobuf.timestamp_pb2 import Timestamp

import trainer_pb2
import trainer_pb2_grpc

from TrainerRepository.trainer_repository import TrainerRepository
import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_CONNECTION_STRING", "mongodb://admin:password@mongodb:27017")
DB_NAME  = os.getenv("MONGO_DB_NAME", "pokedex")
COL_NAME = os.getenv("MONGO_COLLECTION", "Trainers")

client = MongoClient(MONGO_URI)
db     = client[DB_NAME]
collection = db[COL_NAME]

repo = TrainerRepository(collection)

class TrainerServiceServicer(trainer_pb2_grpc.TrainerServiceServicer):
    def GetTrainer(self, request, context):
        doc = repo.get_by_id(request.id)
        if not doc:
            context.abort(grpc.StatusCode.NOT_FOUND, "Trainer no encontrado")
        # mapear doc a TrainerResponse
        resp = trainer_pb2.TrainerResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            age=doc["age"],
            birthdate=Timestamp(seconds=int(doc["birthdate"].timestamp())),
            medals=[trainer_pb2.Medals(region=m["region"], type=m["type"]) for m in doc.get("medals", [])],
            created_at=Timestamp(seconds=int(doc["created_at"].timestamp()))
        )
        return resp

    def CreateTrainer(self, request, context):
        data = {
            "name": request.name,
            "age":  request.age,
            "birthdate": datetime.fromtimestamp(request.birthdate.seconds, tz=timezone.utc),
            "medals": [{"region": m.region, "type": m.type} for m in request.medals],
        }
        created = repo.create(data)
        return trainer_pb2.TrainerResponse(
        id=str(created["_id"]),
        name=created["name"],
        age=created["age"],
        birthdate=Timestamp(seconds=int(created["birthdate"].timestamp())),
        medals=[trainer_pb2.Medals(region=m["region"], type=m["type"]) for m in created.get("medals", [])],
        created_at=Timestamp(seconds=int(created["created_at"].timestamp()))
        )
    
    def CreateManyTrainers(self, request_iterator, context):
        responses = []
        for req in request_iterator:
            data = {
                "name": req.name,
                "age":  req.age,
                "birthdate": datetime.fromtimestamp(req.birthdate.seconds, tz=timezone.utc),
                "medals": [{"region": m.region, "type": m.type} for m in req.medals],
            }
            created = repo.create(data)
            responses.append(trainer_pb2.TrainerResponse(
                id=str(created["_id"]),
                name=created["name"],
                age=created["age"],
                birthdate=Timestamp(seconds=int(created["birthdate"].timestamp())),
                medals=[trainer_pb2.Medals(region=m["region"], type=m["type"]) for m in created.get("medals", [])],
                created_at=Timestamp(seconds=int(created["created_at"].timestamp()))
        ))

        return trainer_pb2.CreateManyResponse(
            created_count=len(responses),
            trainers=responses
    )

    def GetTrainersByName(self, request, context):
        docs = repo.get_by_name(request.name)
        for doc in docs:
            ts_birth   = Timestamp();   ts_birth.FromDatetime(doc["birthdate"])
            ts_created = Timestamp();   ts_created.FromDatetime(doc["created_at"])
            yield trainer_pb2.TrainerResponse(
                id=str(doc["_id"]),
                name=doc["name"],
                age=doc["age"],
                birthdate=ts_birth,
                medals=[trainer_pb2.Medals(region=m["region"], type=m["type"]) for m in doc.get("medals", [])],
                created_at=ts_created
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    trainer_pb2_grpc.add_TrainerServiceServicer_to_server(TrainerServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC iniciado en el puerto 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
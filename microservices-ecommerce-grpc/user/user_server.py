#python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. user.proto
import grpc
from concurrent import futures 
import io
import os
from passlib.hash import sha256_crypt
import user_pb2
import user_pb2_grpc
from app import app, db, User

# UserService implementation
class UserService(user_pb2_grpc.UserServiceServicer):

    def GetUserById(self, request, context):
        with app.app_context():
            user = User.query.filter_by(id=request.id).first()
            if user:
                p=user_pb2.User()
                p.id = user.id
                p.first_name = user.first_name
                p.last_name = user.last_name
                p.username = user.username
                p.email = user.email
                p.photo = user.photo
                p.is_admin = user.is_admin
                p.api_key = user.api_key               
                return p
            return user_pb2.EmptyUser()

    def CreateUser(self, request, context):
        with app.app_context():
            # Create user logic
            first_name = request.first_name
            last_name = request.last_name
            email = request.email
            username = request.username

            password = sha256_crypt.hash(request.password)

            user = User()
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.password = password
            user.username = username
            user.authenticated = True
            user.photo = request.photo

            db.session.add(user)
            db.session.commit()

            p=user_pb2.User()
            p.id = user.id
            p.first_name = user.first_name
            p.last_name = user.last_name
            p.username = user.username
            p.email = user.email
            p.photo = user.photo
            p.is_admin = user.is_admin              
            return p

    def LoginUser(self, request, context):
        with app.app_context():
            user = User.query.filter_by(username=request.username).first()
            if user:
                if sha256_crypt.verify(request.password, user.password):
                    user.encode_api_key()
                    db.session.commit()
                    #login_user(user)
                    p=user_pb2.User()
                    p.id = user.id
                    p.first_name = user.first_name
                    p.last_name = user.last_name
                    p.username = user.username
                    p.email = user.email
                    p.photo = user.photo
                    p.is_admin = user.is_admin
                    p.api_key = user.api_key               
                    return p
            return user_pb2.EmptyUser()


    def CheckUsername(self, request, context):
        with app.app_context():
            # Check username logic
            item = User.query.filter_by(username=request.username).first()
            u= user_pb2.UsernameResponse()
            if item is not None:
                u.result=True                
            else:
                u.result=False
            return u

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50054')
    server.start()
    print("gRPC server started on port 50054")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()  
#python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. product.proto
import grpc
from concurrent import futures 
import io
import os
import product_pb2
import product_pb2_grpc
from app import app, db, Product

class ProductService(product_pb2_grpc.ProductServiceServicer):

    def GetProducts(self, request, context):
        with app.app_context():
            products = Product.query.all()

            product_list = product_pb2.ProductList()
            for product in products:
                p = product_pb2.Product()
                p.id = product.id
                p.name = product.name
                p.description = product.description
                p.slug = product.slug
                p.price = product.price
                p.image = product.image
                product_list.products.append(p)

            return product_list

    def GetProduct(self, request, context):
        with app.app_context():
            product = Product.query.filter_by(slug=request.slug).first()
            if not product:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Product not found')
                return product_pb2.Product()
            p = product_pb2.Product()
            p.id = product.id
            p.name = product.name
            p.description = product.description
            p.slug = product.slug
            p.price = product.price
            p.image = product.image
            return p
    
    def GetProductWithID(self, request, context):
        with app.app_context():
            product = Product.query.filter_by(id=request.id).first()
            if not product:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Product not found')
                return product_pb2.Product()
            p = product_pb2.Product()
            p.id = product.id
            p.name = product.name
            p.description = product.description
            p.slug = product.slug
            p.price = product.price
            p.image = product.image
            return p

    def CreateProduct(self, request, context):
        with app.app_context():
            product = Product()
            product.name = request.name
            product.description = request.description
            product.slug = request.slug
            product.price = request.price
            product.image = request.image
            db.session.add(product)
            db.session.commit()
            p = product_pb2.Product()
            p.id = product.id
            p.name = product.name
            p.description = product.description
            p.slug = product.slug
            p.price = product.price
            p.image = product.image
            p.date_added = product.date_added.strftime("%b %d, %Y")
            return p

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server started on port 50051")
    server.wait_for_termination()


if __name__ == '__main__':
     serve()
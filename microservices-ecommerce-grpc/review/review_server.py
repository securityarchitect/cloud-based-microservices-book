#python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. review.proto
import grpc
from concurrent import futures 
import io
import os
import review_pb2
import review_pb2_grpc
from app import app, db, Review



class ReviewService(review_pb2_grpc.ReviewServiceServicer):
    def GetReviews(self, request, context):
        with app.app_context():
            reviews = Review.query.filter_by(product_id=request.product_id)
            reviews_list = review_pb2.ReviewsList()
            for review in reviews:
                p = review_pb2.Review()
                p.id = review.id
                p.user_id = review.user_id
                p.product_id = review.product_id
                p.rating = review.rating
                p.description = review.description
                p.date_added = review.date_added.strftime("%b %d, %Y")
                reviews_list.reviews.append(p)
            return reviews_list

    def AddReview(self, request, context):
        with app.app_context():
            review = Review()
            review.user_id = request.user_id
            review.product_id = request.product_id
            review.rating = request.rating
            review.description = request.description
            db.session.add(review)
            db.session.commit()
            #print(review.id, review.user_id, review.product_id, review.rating, review.description, review.date_added)
            p = review_pb2.Review()
            p.id = review.id
            p.user_id = review.user_id
            p.product_id = review.product_id
            p.rating = review.rating
            p.description = review.description
            p.date_added = review.date_added.strftime("%b %d, %Y")
            return p

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    review_pb2_grpc.add_ReviewServiceServicer_to_server(ReviewService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("gRPC server started on port 50052")
    server.wait_for_termination()


if __name__ == '__main__':
     serve()



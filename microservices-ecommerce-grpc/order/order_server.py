
#python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. order.proto
import os
import json
import grpc
from concurrent import futures
import order_pb2
import order_pb2_grpc
from app import app, db, Order, OrderItem

# Implementation of gRPC service
class OrderService(order_pb2_grpc.OrderServiceServicer):

  def AddItem(self, request, context):
    with app.app_context():
        user_id = request.user_id
        product_id = request.product_id
        qty = request.qty
        price = request.price
        
        known_order = Order.query.filter_by(user_id=user_id, is_open=1).first()

        if known_order is None:
            known_order = Order()
            known_order.is_open = True
            known_order.user_id = user_id

            order_item = OrderItem(product_id, qty, price)
            known_order.items.append(order_item)
        else:
            found = False

            for item in known_order.items:
                if item.product_id == product_id:
                    found = True
                    item.quantity += qty

            if found is False:
                order_item = OrderItem(product_id, qty, price)
                known_order.items.append(order_item)

        db.session.add(known_order)
        db.session.commit()
        orderjson=known_order.to_json()
        p = order_pb2.OrderResponse()
        p.id = orderjson['id']
        p.items = json.dumps(orderjson['items'])
        p.is_open = orderjson['is_open']
        p.user_id = orderjson['user_id'] 
        p.date_added = orderjson['date_added']
        p.amount = orderjson['amount']
        return p
  
  def GetOrder(self, request, context):
    with app.app_context():
        open_order = Order.query.filter_by(user_id=request.user_id, is_open=1).first()
        if open_order is not None:
            orderjson=open_order.to_json()
            p = order_pb2.OrderResponse()
            p.id = orderjson['id']
            p.items = json.dumps(orderjson['items'])
            p.is_open = orderjson['is_open']
            p.user_id = orderjson['user_id'] 
            p.date_added = orderjson['date_added']
            p.amount = orderjson['amount']
            return p
        else:
            return order_pb2.OrderResponse()

  def Checkout(self, request, context):
    with app.app_context():
        order_model = Order.query.filter_by(user_id=request.user_id, is_open=1).first()
        order_model.is_open = 0

        db.session.add(order_model)
        db.session.commit()

        orderjson=order_model.to_json()
        p = order_pb2.OrderResponse()
        p.id = orderjson['id']
        p.items = json.dumps(orderjson['items'])
        p.is_open = orderjson['is_open']
        p.user_id = orderjson['user_id'] 
        p.date_added = orderjson['date_added']
        p.amount = orderjson['amount']
        return p

  def GetCart(self, request, context):
    with app.app_context():
        open_order = Order.query.filter_by(user_id=request.user_id, is_open=1).first()

        items=[]
        if open_order is not None:
            for item in open_order.items:
                items.append(item.to_json())

        p=order_pb2.GetCartResponse()
        p.items=json.dumps(items)
        return p

  def GetOrders(self, request, context):
    with app.app_context():
        orders = Order.query.filter_by(user_id=request.user_id, is_open=0)

        orders_list = order_pb2.GetOrdersResponse()
        for order in orders:
            p = order_pb2.OrderResponse()
            orderjson=order.to_json()
            print(orderjson)
            p.id = orderjson['id']
            p.items = json.dumps(orderjson['items'])
            p.is_open = orderjson['is_open']
            p.user_id = orderjson['user_id'] 
            p.date_added = orderjson['date_added']
            p.amount = orderjson['amount']

            orders_list.orders.append(p) 
            
        return orders_list
        

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderService(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    print("gRPC server started on port 50053")
    server.wait_for_termination()


if __name__ == '__main__':
     serve()



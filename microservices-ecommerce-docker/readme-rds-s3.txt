docker build -f Dockerfile -t ecomfrontend:v6 .
docker tag ecomfrontend:v6 asbind/ecomfrontend:v6
docker push asbind/ecomfrontend:v6

docker build -f Dockerfile -t ecomuser:v6 .
docker tag ecomuser:v6 asbind/ecomuser:v6
docker push asbind/ecomuser:v6

docker build -f Dockerfile -t ecomproduct:v6 .
docker tag ecomproduct:v6 asbind/ecomproduct:v6
docker push asbind/ecomproduct:v6

docker build -f Dockerfile -t ecomorder:v6 .
docker tag ecomorder:v6 asbind/ecomorder:v6
docker push asbind/ecomorder:v6

docker build -f Dockerfile -t ecomreview:v6 .
docker tag ecomreview:v6 asbind/ecomreview:v6
docker push asbind/ecomreview:v6

docker network ls
docker network create --driver bridge ecom_network
docker run -p 5000:5000 --detach --name frontend-service --net=ecom_network ecomfrontend:v6
docker run -p 5001:5000 --detach --name user-service --net=ecom_network ecomuser:v6
docker run -p 5002:5000 --detach --name product-service --net=ecom_network ecomproduct:v6
docker run -p 5003:5000 --detach --name order-service --net=ecom_network ecomorder:v6
docker run -p 5004:5000 --detach --name review-service --net=ecom_network ecomreview:v6

docker ps -a

#Cleanup by removing all containers
docker rm -f $(docker ps -aq)

-----------


docker tag ecomfrontend:v6 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomfrontend_v6
docker tag ecomuser:v6 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomuser_v6
docker tag ecomproduct:v6 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomproduct_v6
docker tag ecomorder:v4 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomorder_v4
docker tag ecomreview:v6 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomreview_v6

docker push 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomfrontend_v6
docker push 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomuser_v6
docker push 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomproduct_v6
docker push 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomorder_v4
docker push 497612612079.dkr.ecr.us-west-2.amazonaws.com/microservices:ecomreview_v6
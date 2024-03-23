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
------

#Run MySQL

mkdir -p ~/mysql/database

docker run \
  --detach \
  --name database \
  -e MYSQL_ROOT_PASSWORD=c1Zl6tC93AuTfKC \
  -p 3306:3306 \
  -v ~/mysql/database/mysql-data:/var/lib/mysql \
  mysql

docker exec -it database mysql -u root -p

SHOW DATABASES;
CREATE DATABASE userdb;
CREATE DATABASE orderdb;
CREATE DATABASE productdb;
CREATE DATABASE reviewdb;

---------
#Run Minio

mkdir -p ~/minio/data

docker run \
  --detach \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio1 \
  -v ~/minio/data:/data \
  -e "MINIO_ROOT_USER=AKIAIOSFODNN7EXAMPLE" \
  -e "MINIO_ROOT_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" \
  quay.io/minio/minio server /data --console-address ":9001"

-----
#Run DB migrations

docker exec -it user-container /bin/bash
rm -rf migrations/
flask db init
flask db migrate
flask db upgrade

docker exec -it order-container /bin/bash
rm -rf migrations/
flask db init
flask db migrate
flask db upgrade

docker exec -it product-container /bin/bash
rm -rf migrations/
flask db init
flask db migrate
flask db upgrade

docker exec -it review-container /bin/bash
rm -rf migrations/
flask db init
flask db migrate
flask db upgrade

-----

#Run docker-compose
docker-compose -f docker-compose-mysql-minio up

#Create product
curl -X POST -F "name=Mug" -F "slug=mug-1" -F "description=This is a mug" -F "price=49.99" -F "image=@mug.jpg" http://localhost:5002/api/product/create


#Cleanup by removing all containers:
docker rm -f $(docker ps -aq)
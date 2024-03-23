FROM python:3.11.6-slim
RUN mkdir /app
WORKDIR /app
ADD . /app/
RUN apt-get update
RUN apt install -y libcairo-5c-dev
RUN apt install -y mariadb-client-core
RUN pip3 install -r requirements.txt
EXPOSE 5000

#ENV SECRET_KEY=DoWgTDq87Kmne3TsCjNFabP
#ENV WTF_CSRF_SECRET_KEY=sEWQkE9oYBiF5fVJnm278i7
#ENV BUCKET_NAME=microservices-ecommerce-app
#ENV CLOUDFRONT_URL=https://dn2aztcn1xe1u.cloudfront.net
#ENV AWS_ACCESS_KEY=AKIATHISISANEXAMPLEKEY
#ENV AWS_SECRET_KEY=APthisisanexamplesecretkey
#ENV MYSQL_RDS_ENDPOINT=database-1.czqnyxmkvtxg.us-west-2.rds.amazonaws.com
#ENV MYSQL_RDS_PASSWORD=S9c1Zl6tC93AuTfKCLLV
#ENV USER_SERVICE_URL=http://user-service:5000
#ENV PRODUCT_SERVICE_URL=http://product-service:5000
#ENV ORDER_SERVICE_URL=http://order-service:5000
#ENV REVIEW_SERVICE_URL=http://review-service:5000

#CMD ["python", "/app/app.py"]
CMD ["gunicorn", "wsgi:app", "-c", "/app/gunicorn.py"]

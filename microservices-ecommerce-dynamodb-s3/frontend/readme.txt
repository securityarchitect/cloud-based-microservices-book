#Install the required packages 
sudo apt update
sudo apt install python3-pip python3-dev nginx supervisor
sudo apt install libcairo-5c-dev
sudo apt install mysql-client-core-8.0

#Install the python packages
sudo pip3 install -r requirements.txt

#Connect to RDS MySQL Database
mysql --host=database-1.czqnyxmkvtxg.us-west-2.rds.amazonaws.com --port=3306 --user=admin --password=S9c1Zl6tC93AuTfKCLLV
#--Run within mysql shell---
    #Create Database
    CREATE DATABASE user;
    CREATE DATABASE product;
    CREATE DATABASE orderdb;
    CREATE DATABASE review;
    #Show Databases
    SHOW DATABASES;
    #Exit mysql shell
    exit

#Setup the DB
flask db init
flask db migrate
flask db upgrade

#Run the app
python3 app.py 

#Setup Nginx
sudo cp nginx-flask.conf /etc/nginx/sites-available/
cd /etc/nginx/sites-enabled/
sudo ln -s ../sites-available/nginx-flask.conf .
sudo service nginx restart

#Setup Supervisor
sudo cp frontend-supervisor.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

#Getting SSL Certificate
sudo apt install certbot
sudo service nginx stop
sudo certbot certonly --standalone -d app.study411.com

#Create products (replace localhost with private IP of product service)

curl -X POST -F "name=Coffee Mug" -F "slug=mug-1" -F "description=This is product 1" -F "price=49.99" -F "image=@mug.jpg" http://localhost:5000/api/product/create

curl -X POST -F "name=Clock" -F "slug=clock-1" -F "description=This is product 2" -F "price=14.99" -F "image=@clock.jpg" http://localhost:5002/api/product/create

#Test create and login user
curl -X POST -F "first_name=Alan" -F "last_name=Bob" -F "email=alan@example.com" -F "username=alan" -F "password=mypass123" http://localhost:5000/api/user/create

curl -X POST -F "username=alan" -F "password=mypass123" http://localhost:5000/api/user/login
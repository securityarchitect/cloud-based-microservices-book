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

curl -X POST -F "name=Coffee Mug" -F "slug=mug-1" -F "description=These premium quality coffee mugs are crafted from durable, dishwasher-safe ceramic and feature stunning, unique designs that add a touch of style to your morning routine. With a generous 300ml capacity and comfortable, ergonomic handle, you can enjoy more of your favorite hot beverage with each sip. The mugs have a glossy finish that looks elegant and feels smooth to the touch. Microwave safe for convenient reheating, they make for thoughtful, personalized gifts for birthdays, holidays, anniversaries, or to show appreciation for someone special. Arriving beautifully packaged in a secure box, these eye-catching mugs are ready to delight any recipient." -F "price=9.99" -F "image=@mug.jpg" http://172.31.16.52:5000/api/product/create
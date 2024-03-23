#Product

curl -X POST -H "Content-Type: application/json" -d '{"name": "Coffee Mug2","slug":"mug-1c", "description":"This is a mug","price":"10", "filename":"mug.jpg", "image" : "'"$( base64 ~/Pictures/mug.jpg)"'"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/product/create

curl https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/product/getall

curl https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/product/get/mug-1b

--

#User

curl -X POST -H "Content-Type: application/json" -d '{"given_name": "Charles", "family_name": "Bob", "picture": "https://dn2aztcn1xe1u.cloudfront.net/photos/mug.jpg", "username":"charles3", "email":"charles@example.com", "password":"Charles@2024"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/user/create

curl -X POST -H "Content-Type: application/json" -d '{"username":"charles4", "password":"Charles@2024"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/user/login

--

#Review

curl -X POST -H "Content-Type: application/json" -d '{"username":"charles4", "description": "Very good", "rating": "4", "product_slug": "mug-1"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/review/create

curl https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/review/get/mug-1

--

#Order

curl -X POST -H "Content-Type: application/json" -d '{"username":"charles4", "qty": "1", "price": "29", "product_slug": "mug-1", "image": "https://dn2aztcn1xe1u.cloudfront.net/photos/mug.jpg", "name": "Mug"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/additem

curl -X POST -H "Content-Type: application/json" -d '{"username":"charles4"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/getall

curl -X POST -H "authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImNoYXJsZXM0IiwiZXhwIjoxNzA3MTA4OTQxfQ.uD-mgX6YQjpcHX_cyp7uU6TVXxaU_HcTQNjWWic8DI0" -H "Content-Type: application/json" -d '{"username":"charles4"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/getcart

curl -X POST -H "Content-Type: application/json" -d '{"username":"charles4"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/getcart

curl -X POST -H "Content-Type: application/json" -d '{"username":"charles4"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/checkout

curl -X POST -H "Content-Type: application/json" -d '{"username":"charles4"}' https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/get

--
#Install Python 3.9 on Amazon Linux 2 instance
sudo yum update -y
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel
cd /opt
sudo wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tgz
sudo tar xzf Python-3.9.0.tgz
cd Python-3.9.0
sudo ./configure --enable-optimizations
sudo make altinstall

#Create folder structure for python packages
cd ~/
mkdir -p mylayer/aws-layer/aws-layer/python/lib/python3.9/site-packages

#Install python packages at the created path
cd ~/mylayer
pip3.9 install cairosvg --target aws-layer/python/lib/python3.9/site-packages
pip3.9 install cffi --target aws-layer/python/lib/python3.9/site-packages
pip3.9 install avinit[png] --target aws-layer/python/lib/python3.9/site-packages
pip3.9 install PyJWT --target aws-layer/python/lib/python3.9/site-packages

#Install required libraries
sudo yum install cairo cairo-dev

#Copy required libraries along with the dependencies
cd ~/mylayer/aws-layer/aws-layer/python/lib/
sudo cp -r /usr/lib64/libcairo* .
sudo cp -r /usr/lib64/libX* .
sudo cp -r /usr/lib64/libglvnd* .
sudo cp -r /usr/lib64/libgl* .
sudo cp -r /usr/lib64/libx* .
sudo cp -r /usr/lib64/libpng* .
sudo cp -r /usr/lib64/libpixman* .
sudo cp -r /usr/lib64/libway* .
sudo cp -r /usr/lib64/libEGL* .
sudo cp -r /usr/lib64/libGL* .
sudo cp -r /usr/lib64/libgbm* .
sudo cp -r /usr/lib64/libgl* .
sudo cp -r /usr/lib64/libxshmfence* .

#Create zip of layer
cd ~/mylayer/aws-layer/
zip -r9 lambda-layer.zip .

#Configure AWS CLI
aws configure

#Upload layer zip to AWS
aws lambda publish-layer-version --layer-name Avinit12 --description "My Python layer" --zip-file fileb://lambda-layer.zip     --compatible-runtimes python3.9

#In Lambda function > Configuration > Environment Variables, set:
LD_LIBRARY_PATH=/opt/python/lib

#Add the uploaded layer to lambda function
-------


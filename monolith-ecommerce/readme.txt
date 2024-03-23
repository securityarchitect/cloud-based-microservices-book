#Setup the DB
flask db init
flask db migrate
flask db upgrade

#Run the app
python3 app.py 

#Create products

curl -X POST -F "name=Coffee Mug" -F "slug=mug-1" -F "description=These premium quality coffee mugs are crafted from durable, dishwasher-safe ceramic and feature stunning, unique designs that add a touch of style to your morning routine. With a generous 300ml capacity and comfortable, ergonomic handle, you can enjoy more of your favorite hot beverage with each sip. The mugs have a glossy finish that looks elegant and feels smooth to the touch. Microwave safe for convenient reheating, they make for thoughtful, personalized gifts for birthdays, holidays, anniversaries, or to show appreciation for someone special. Arriving beautifully packaged in a secure box, these eye-catching mugs are ready to delight any recipient." -F "price=9.99" -F "image=@mug.jpg" http://localhost:5000/api/product/create

curl -X POST -F "name=Rechargeable Table Lamp" -F "slug=lamp-1" -F "description=The rechargeable black table lamp is designed for tabletop use during reading or work. It has compact dimensions and is lightweight and portable. The lamp is powered by a 20000mAh lithium-ion battery that takes 6 hours to fully recharge via the included USB cable. It provides up to 120 minutes of light on the highest setting or longer on lower settings. The LED bulb is energy efficient, rated for 60,000 hours of use, and provides a milky white light. The lamp has a 3-stage dimming feature to adjust brightness as needed. It uses a touch sensor switch for operation. The flexible gooseneck allows the light to be adjusted to any angle, providing 360 degrees of directable lighting. The lamp has a foldable, compact design that makes it easy to transport and use anywhere like a bedroom, living room, study, or library." -F "price=14.99" -F "image=@lamp.jpg" http://localhost:5000/api/product/create

curl -X POST -F "name=Wooden Wall Clock" -F "slug=clock-1" -F "description=variety of décor styles. Measuring 10 inches in diameter, the clock face has a thin black frame and large easy-to-read numerals marking each hour position. The frame is constructed from durable MDF wood in an attractive distressed finish that emulates a natural wood grain texture. The white clock face and black numbers offer high contrast for optimal visibility. With its affordable price point, neutral hues, sturdy construction and easy-to-read design, this modern wall clock is a versatile accent piece for any space. Its simple yet elegant aesthetics allow it to blend in anywhere you need an attractive and reliable timepiece." -F "price=20" -F "image=@clock.jpg" http://localhost:5000/api/product/create


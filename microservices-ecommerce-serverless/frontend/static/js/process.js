function clearSession() {
    sessionStorage.clear();
    location.href = 'login.html';
};

$.urlParam = function (name) {
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    return results[1] || 0;
}

function processLogin() {
    var username = $("#username").val();
    var password = $("#password").val();

    var datadir = {
        username: username,
        password: password
    };

    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/user/login',
        type: 'POST',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        success: function (data) {
            //var result = JSON.parse(data.body);
            console.log(data);
            if (data.result) {
                sessionStorage.setItem('username', data.userdata.username);
                sessionStorage.setItem('name', data.userdata.given_name + ' ' + data.userdata.family_name);
                sessionStorage.setItem('token', data.userdata.token);
                sessionStorage.setItem('userphoto', data.userdata.picture);
                location.href = 'index.html';
            } else {
                $("#message").html(data.message);
            }

            console.log(data);
        },
        error: function (data) {
            console.log(data);
            console.log("Failed");
        },
        data: JSON.stringify(datadir)
    });
}


function processSignup() {
    var username = $("#username").val();
    var password = $("#password").val();
    var given_name = $("#given_name").val();
    var family_name = $("#family_name").val();
    var email = $("#email").val();

    var datadir = {
        username: username,
        password: password,
        given_name: given_name,
        family_name: family_name,
        email: email
    };

    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/user/create',
        type: 'POST',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        success: function (data) {
            console.log(data);
            $("#message").html("Thanks for signing up. Please login.");
            $("#signupform").hide();
        },
        error: function () {
            console.log("Failed");
        },
        data: JSON.stringify(datadir)
    });
}


function checkIfLoggedIn() {
    var token = sessionStorage.getItem('token');
    var username = sessionStorage.getItem('username');
    if (token == null || username == null) {
        return false;
    } else {
        return true;
    }
}

function loadNavbar() {
    $("#navbar-container").html('<li class="nav-item"><a class="nav-link text-white mr-3" href="cart.html">Cart <span class="badge" id="cartcount"></span></a></li><li class="nav-item"><a class="nav-link text-white mr-3" href="orders.html">Orders</a></li><li class="nav-item"><a class="nav-link text-white mr-3" href="#" id="logoutlink">Logout</a></li><span style="margin-top:8px;margin-left: 20px;color:#fff">' + sessionStorage.getItem('name') + '</span><img src="' + sessionStorage.getItem('userphoto') + '" class="mr-3 rounded-circle" style="width:30px;height:30px;margin-top:5px;margin-left: 20px;">');
}


function updateCartCount() {
    var datadir = {
        username: sessionStorage.getItem('username')
    };

    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/getcart',
        type: 'POST',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        headers: {
            'authorization': sessionStorage.getItem('token')
        },
        success: function (data) {
            console.log(data);
            var cartcount = 0;
            if (data.totalamount > 0) {
                var resultsjson = JSON.parse(data.result);
                $.each(resultsjson, function (index, value) {
                    cartcount = cartcount + 1;
                });
            }
            $('#cartcount').html(cartcount);
        },
        error: function () {
            console.log("Failed");
        },
        data: JSON.stringify(datadir)
    });
}

function loadHomePage() {
    loggedin = checkIfLoggedIn();
    if (loggedin) {
        loadNavbar();
        updateCartCount();
    } else {
        $("#navbar-container").html('<li class="nav-item"><a class="nav-link text-white mr-3" href="/login.html">Login</a></li><li class="nav-item"><a class="nav-link text-white mr-3" href="/register.html">Register</a></li>');
    }

    var htmlstr = "";
    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/product/getall',
        type: 'GET',
        crossDomain: true,
        contentType: "application/json",
        success: function (data) {
            console.log(data);
            $.each(data.results, function (index, value) {
                htmlstr = htmlstr + '<div class="col-md-4"><div class="card mb-4"><a href="product.html?slug=' + value.slug + '"><img src="' + value.image + '" class="card-img-top"></a><div class="card-body"><a href="product.html?slug=' + value.slug + '"><h5 class="card-title">' + value.name + '</h5></a><p class="card-text">Price: $' + value.price + '</p></div></div></div>';
            });
            console.log(htmlstr);
            $('#products-container').html(htmlstr);
        },
        error: function () {
            console.log("Failed");
        }
    });
}

function loadCartPage() {
    loggedin = checkIfLoggedIn();
    if (loggedin) {
        loadNavbar();
        updateCartCount();
    } else {
        location.href = "login.html"
    }

    var htmlstr = "";
    var datadir = {
        username: sessionStorage.getItem('username')
    };

    var htmlstr = '<div class="container mt-5"><h2>Shopping Cart</h2><table class="table"><thead><tr><th>Product</th><th>Price</th><th>Quantity</th><th>Amount</th></tr></thead><tbody>';
    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/getcart',
        type: 'POST',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        headers: {
            'authorization': sessionStorage.getItem('token')
        },
        success: function (data) {
            console.log(data);
            if (data.totalamount > 0) {
                var resultsjson = JSON.parse(data.result);
                $.each(resultsjson, function (index, value) {
                    htmlstr = htmlstr + '<tr><td><img src="' + value.image + '" style="max-width: 80px;">' + value.name + '</td><td>' + value.price + '</td><td>' + value.quantity + '</td><td>' + value.price + '</td></tr>';
                });
                htmlstr = htmlstr + '</tbody></table><strong>Total Amount: $' + data.totalamount + '</strong><br><br><button class="btn btn-primary" id="checkoutlink">Checkout</button>    </div>';
            } else {
                htmlstr = htmlstr + '<tr><td colspan="4">Your cart is empty</td></tr></tbody></table>';
            }
            $('#cart-container').html(htmlstr);
        },
        error: function () {
            console.log("Failed");
        },
        data: JSON.stringify(datadir)
    });
}

function checkoutOrder() {
    loggedin = checkIfLoggedIn();
    if (loggedin) {

    } else {
        location.href = "login.html"
    }

    var datadir = {
        username: sessionStorage.getItem('username')
    };

    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/checkout',
        type: 'POST',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        headers: {
            'authorization': sessionStorage.getItem('token')
        },
        success: function (data) {
            console.log(data);
            location.href = "thanks.html"
        },
        error: function () {
            console.log("Failed");
        },
        data: JSON.stringify(datadir)
    });
}

function loadThanksPage() {
    loggedin = checkIfLoggedIn();
    if (loggedin) {
        loadNavbar();
        updateCartCount();
    } else {
        location.href = "login.html"
    }

}

function formattedDate(datetime) {
    var date = new Date(datetime);

    var formatted = date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });

    return formatted;

}

function loadOrdersPage() {
    loggedin = checkIfLoggedIn();
    if (loggedin) {
        loadNavbar();
        updateCartCount();
    } else {
        location.href = "login.html"
    }

    var htmlstr = "";
    var datadir = {
        username: sessionStorage.getItem('username')
    };

    var htmlstr = '<div class="container mt-5"><h2>Orders</h2><table class="table"><thead><tr><th>Order ID</th><th>Date</th><th>Items</th><th>Total Amount</th></tr></thead><tbody>';
    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/getall',
        type: 'POST',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        headers: {
            'authorization': sessionStorage.getItem('token')
        },
        success: function (data) {
            console.log(data);
            if (data.message == "Order found") {
                var totalamount = 0
                $.each(data.result, function (index, value) {
                    htmlstr = htmlstr + '<tr><td>' + value.order_id + '</td><td>' + formattedDate(value.date_added) + '</td><td>';
                    $.each(JSON.parse(value.items), function (index1, value1) {
                        htmlstr = htmlstr + '<img src="' + value1.image + '" style="max-width: 50px;">';
                        totalamount = totalamount + value1.price;
                    });
                    htmlstr = htmlstr + '</td><td>$' + totalamount + '</td></tr>';
                });
                //htmlstr = htmlstr + '<strong>Total Amount: $' + data.totalamount + '</strong>';
            } else {
                htmlstr = htmlstr + '<tr><td colspan="4">No orders found</td></tr></tbody></table>';
            }
            $('#orders-container').html(htmlstr);
        },
        error: function () {
            console.log("Failed");
        },
        data: JSON.stringify(datadir)
    });
}


function loadProductPage() {
    loggedin = checkIfLoggedIn();
    if (loggedin) {
        loadNavbar();
        updateCartCount();
    } else {
        location.href = "login.html"
    }

    var htmlstr = "";
    console.log(window.location.href);
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    const slug = urlParams.get('slug')
    console.log(slug);
    $("#reviewformproductslug").val(slug);

    var htmlstr = '';
    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/product/get/' + slug,
        type: 'GET',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        headers: {
            'authorization': sessionStorage.getItem('token')
        },
        success: function (data) {
            console.log(data);
            htmlstr = htmlstr + '<div class="row"><div class="col-md-6"><img src="' + data.result.image + '" width="100%" alt="Product Image"></div><div class="col-md-6"><h2>' + data.result.name + '</h2><p>' + data.result.description + '</p><h4>Price: $' + data.result.price + '</h4><br><input type="hidden" name="cartproductslug" id="cartproductslug" value="' + data.result.slug + '"><input type="hidden" name="cartproductqty" id="cartproductqty" value="1"><input type="hidden" name="cartproductprice" id="cartproductprice" value="' + data.result.price + '"><input type="hidden" name="cartproductname" id="cartproductname" value="' + data.result.name + '"><input type="hidden" name="cartproductimage" id="cartproductimage" value="' + data.result.image + '"><button type="submit" class="btn btn-primary" id="addtocartbtn">Add To Cart</button></div></div>';
            $('#product-container').html(htmlstr);
        },
        error: function () {
            console.log("Failed");
        }
    });


    var htmlstr1 = '';
    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/review/get/' + slug,
        type: 'GET',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        headers: {
            'authorization': sessionStorage.getItem('token')
        },
        success: function (data) {
            console.log(data);
            htmlstr1 = htmlstr1 + '<h3>Reviews</h3>';

            $.each(data.results, function (index, value) {
                htmlstr1 = htmlstr1 + '<div class="media mb-3">     <img src="' + value.userphoto + '" class="mr-3 rounded-circle" width="50">     <div class="media-body">       <h5 class="mt-0">' + value.fullname + ' - <small><i> ' + formattedDate(value.date_added) + '</i></small></h5>        <input required class="rating" type="number" value="' + value.rating + '" title=""  >  ' + value.description + '</div>   </div>';

            });

            $('#review-container').html(htmlstr1);
            $(".rating").rating({min:0, max:5, step:0.5, size:'xs', theme: 'krajee-fas', displayOnly: true, 'showClear': false, 'showCaption': false});
        },
        error: function () {
            console.log("Failed");
        }
    });
}

function processPostReview() {
    var datadir = {
        username: sessionStorage.getItem('username'),
        userphoto: sessionStorage.getItem('userphoto'),
        fullname: sessionStorage.getItem('name'),
        product_slug: $("#reviewformproductslug").val(),
        rating: $("#ratinginput").val(),
        description: $("#reviewinput").val()
    };

    console.log(datadir);

    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/review/create',
        type: 'POST',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        headers: {
            'authorization': sessionStorage.getItem('token')
        },
        success: function (data) {
            console.log(data);
            location.reload();
        },
        error: function () {
            console.log("Failed");
        },
        data: JSON.stringify(datadir)
    });
}

function processAddToCart() {
    var datadir = {
        username: sessionStorage.getItem('username'),
        //userphoto: sessionStorage.getItem('userphoto'),
        fullname: sessionStorage.getItem('name'),
        product_slug: $("#cartproductslug").val(),
        name: $("#cartproductname").val(),
        qty: $("#cartproductqty").val(),
        price: $("#cartproductprice").val(),
        image: $("#cartproductimage").val()
    };

    console.log(datadir);

    $.ajax({
        url: 'https://kzji4guyfg.execute-api.us-west-2.amazonaws.com/dev/order/additem',
        type: 'POST',
        crossDomain: true,
        dataType: 'json',
        contentType: "application/json",
        headers: {
            'authorization': sessionStorage.getItem('token')
        },
        success: function (data) {
            console.log(data);
            updateCartCount();
        },
        error: function () {
            console.log("Failed");
        },
        data: JSON.stringify(datadir)
    });
}

$(document).ready(function () {
    $("#loginform").submit(function (event) {
        processLogin();
        event.preventDefault();
    });

    $("#signupform").submit(function (event) {
        processSignup();
        event.preventDefault();
    });

    $("#reviewform").submit(function (event) {
        processPostReview();
        event.preventDefault();
    });



    $('body').on('click', '#addtocartbtn', function (event) {
        processAddToCart();
        event.preventDefault();
    });


    var pathname = window.location.pathname;
    console.log(pathname);

    if (pathname == '/index.html') {
        loadHomePage();
    } else if (pathname == '/cart.html') {
        loadCartPage();
    } else if (pathname == "/orders.html") {
        loadOrdersPage();
    } else if (pathname == "/product.html") {
        loadProductPage();
    } else if (pathname == "/thanks.html") {
        loadThanksPage();
    }


    $('body').on('click', '#checkoutlink', function (event) {
        checkoutOrder();
        event.preventDefault();
    });


    $("#logoutlink").click(function (event) {
        clearSession();
        event.preventDefault();
    });


});
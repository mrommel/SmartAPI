/** assumes jquery is loaded **/

function handleLoginClicked() {
    var formData = {
        username: $("#login_email").val(),
        password: $("#login_password").val(),
    };

    $.ajax({
        type:"POST",
        url: "/api/auth/login",
        contentType: "application/json",
        data: JSON.stringify(formData),
        dataType: "json",
        success: function(response) {
            console.log('success: ' + JSON.stringify(response));
            document.getElementById('login_form').style.display='none';
            setTimeout(function() {
                window.location.reload();
            }, 3);
        },
        error: function(xhr, textStatus, exception) {
            handleError(xhr, textStatus, exception);
        }
    });
}

function handleSignupClicked() {
    var formData = {
        email: $("#signup_email").val(),
        name: $("#signup_name").val(),
        photo: 'default.png',
        password: $("#signup_password").val(),
        passwordConfirm: $("#signup_repeat_password").val()
    };

    $.ajax({
        type:"POST",
        url: "/api/auth/signup",
        contentType: "application/json",
        data: JSON.stringify(formData),
        dataType: "json",
        success: function(response) {
            console.log('success: ' + JSON.stringify(response));
            document.getElementById('signup_form').style.display='none';
            window.location.href = window.location.href;
        },
        error: function(xhr, textStatus, exception) {
            handleError(xhr, textStatus, exception);
        }
    });
}

function handleLogoutClicked() {
    $.ajax({
        type:"GET",
        url: "/api/auth/logout",
        success: function(response) {
            console.log('success: ' + JSON.stringify(response));
            window.location.href = window.location.href;
        },
        error: function(xhr, textStatus, exception) {
            handleError(xhr, textStatus, exception);
        }
    });
}

function handleError(xhr, textStatus, exception) {

    if (xhr.status === 0) {
        console.log('Not connect.\n Verify Network.');
    } else if (xhr.status == 404) {
        // 404 page error
        console.log('Requested page not found. [404]');
    } else if (xhr.status == 500) {
        // 500 Internal Server error
        console.log('Internal Server Error [500].');
    } else if (exception === 'parsererror') {
        // Requested JSON parse
        console.log('Requested JSON parse failed.');
    } else if (exception === 'timeout') {
        // Time out error
        console.log('Time out error.');
    } else if (exception === 'abort') {
        // request aborted
        console.log('Ajax request aborted.');
    } else {
        console.log('Uncaught Error.\n' + xhr.responseText);
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            // Est-ce que ce cookie stocke notre token CSRF ?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function form_to_json(id_form, url_api, func=null) {
    var form = document.querySelector(id_form);
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        var formData = new FormData(form);
        var object = {};
        formData.forEach(function(value, key){
            if (value instanceof File) {
                var reader = new FileReader();
                reader.onloadend = function() {
                    object[key] = reader.result;
                    sendJson(object, url_api, func);
                }
                reader.readAsDataURL(value);
            } else {
                object[key] = value;
            }
        });
        if (!object.hasOwnProperty('image')) {
            sendJson(object, url_api, func);
        }
    });
}

function sendJson(object, url_api, func=null) {
    var json = JSON.stringify(object);
    console.log(json);
    fetch(url_api, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Assurez-vous d'inclure un jeton CSRF pour la sécurité
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: json
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    }).then(data => {
        if (data.message) {
            Swal.fire({
                title: 'Success!',
                text: data.message,
                icon: 'success',
                confirmButtonText: 'OK'
            }).then((result) => {
                console.log(result);
                if (result.isConfirmed) {
                    console.log('ok');
                    console.log(func);
                    if (func) {
                        func();
                    }
                }
            });
        }
        else {
            Swal.fire({
                title: 'Error!',
                text: data.error,
                icon: 'error',
                confirmButtonText: 'OK'
            }).then((result) => {
                if (result.isConfirmed) {
                    if (func) {
                        func();
                    }
                }
            });
        }
    })
    .catch(error => { console.error(error); });
}

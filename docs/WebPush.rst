At a high-level, the key steps for implementing web push notifications after installing django-push-notifications[WP] are:
 - Configure the VAPID keys, a private and public key for signing your push requests.
 - Add client side logic to ask the user for permission to send push notifications and then sending returned client identifier information to a django view to create a WebPushDevice.
 - Use a service worker to receive messages that have been pushed to the device and displaying them as notifications.

These are in addition to the instalation steps for django-push-notifications[WP]

Configure the VAPID keys
------------------------------
- Install:

.. code-block:: python

	pip install py-vapid  (Only for generating key)

- Generate public and private keys:

.. code-block:: bash

	vapid --gen

	Generating private_key.pem
	Generating public_key.pem


The private key generated is the file to use with the setting ``WP_PRIVATE_KEY``
The public key will be used in your client side javascript, but first it must be formated as an Application Server Key

- Generate client public key (applicationServerKey)

.. code-block:: bash

	vapid --applicationServerKey

	Application Server Key = <Your Public Key>



Client Side logic to ask user for permission and subscribe to WebPush
------------------------------
The example subscribeUser function is best called in response to a user action, such as a button click. Some browsers will deny the request otherwise.

.. code-block:: javascript

	// Utils functions:

	function urlBase64ToUint8Array (base64String) {
	  var padding = '='.repeat((4 - base64String.length % 4) % 4)
	  var base64 = (base64String + padding)
	    .replace(/\-/g, '+')
	    .replace(/_/g, '/')

	  var rawData = window.atob(base64)
	  var outputArray = new Uint8Array(rawData.length)

	  for (var i = 0; i < rawData.length; ++i) {
	    outputArray[i] = rawData.charCodeAt(i)
	  }
	  return outputArray;
	}

	var applicationServerKey = '<Your Public Key>';

	function subscribeUser() {
	  if ('Notification' in window && 'serviceWorker' in navigator) {
	    navigator.serviceWorker.ready.then(function (reg) {
	      reg.pushManager
	        .subscribe({
	          userVisibleOnly: true,
	          applicationServerKey: urlBase64ToUint8Array(
	            applicationServerKey
	          ),
	        })
	        .then(function (sub) {
	          var registration_id = sub.endpoint;
	          var data = {
	            p256dh: btoa(
	              String.fromCharCode.apply(
	                null,
	                new Uint8Array(sub.getKey('p256dh'))
	              )
	            ),
	            auth: btoa(
	              String.fromCharCode.apply(
	                null,
	                new Uint8Array(sub.getKey('auth'))
	              )
	            ),
	            registration_id: registration_id,
	          }
	          requestPOSTToServer(data)
	        })
	        .catch(function (e) {
	          if (Notification.permission === 'denied') {
	            console.warn('Permission for notifications was denied')
	          } else {
	            console.error('Unable to subscribe to push', e)
	          }
	        })
	    })
	  }
	}

	// Send the subscription data to your server
	function requestPOSTToServer (data) {
	  const headers = new Headers();
	  headers.set('Content-Type', 'application/json');
	  const requestOptions = {
	    method: 'POST',
	    headers,
	    body: JSON.stringify(data),
	  };

	  return (
	    fetch(
	      '<your endpoint url>',
	      requestOptions
	    )
	  ).then((response) => response.json())
	}

Server Side logic to create webpush
------------------------------
It is up to you how to add a view in your django application that can handle a POST of p256dh, auth, registration_id and create a WebPushDevice with those values assoicated with the appropriate user.
For example you could use rest_framework

.. code-block:: python

	from rest_framework.routers import SimpleRouter
	from push_notifications.api.rest_framework import WebPushDeviceViewSet
	....
	api_router = SimpleRouter()
	api_router.register(r'push/web', WebPushDeviceViewSet, basename='web_push')
	...
	urlpatterns += [
		# Api
		re_path('api/v1/', include(api_router.urls)),
		...
	]

Or a generic function view (add your own boilerplate for errors and protections)

.. code-block:: python

	import json
	from push_notifications.models import WebPushDevice
	def register_webpush(request):
		data = json.loads(request.body)
		WebPushDevice.objects.create(
			user=request.user,
			**data
		)


Service Worker to show messages
------------------------------
You will need a service worker registered with your web app that can handle the notfications, for example

.. code-block:: javascript

	// Example navigatorPush.service.js file

	var getTitle = function (title) {
	  if (title === "") {
	    title = "TITLE DEFAULT";
	  }
	  return title;
	};
	var getNotificationOptions = function (message, message_tag) {
	  var options = {
	    body: message,
	    icon: '/img/icon_120.png',
	    tag: message_tag,
	    vibrate: [200, 100, 200, 100, 200, 100, 200]
	  };
	  return options;
	};

	self.addEventListener('install', function (event) {
	  self.skipWaiting();
	});

	self.addEventListener('push', function(event) {
	  try {
	    // Push is a JSON
	    var response_json = event.data.json();
	    var title = response_json.title;
	    var message = response_json.message;
	    var message_tag = response_json.tag;
	  } catch (err) {
	    // Push is a simple text
	    var title = "";
	    var message = event.data.text();
	    var message_tag = "";
	  }
	  self.registration.showNotification(getTitle(title), getNotificationOptions(message, message_tag));
	  // Optional: Comunicating with our js application. Send a signal
	  self.clients.matchAll({includeUncontrolled: true, type: 'window'}).then(function (clients) {
	    clients.forEach(function (client) {
	      client.postMessage({
	        "data": message_tag,
	        "data_title": title,
	        "data_body": message});
	      });
	  });
	});

	// Optional: Added to that the browser opens when you click on the notification push web.
	self.addEventListener('notificationclick', function(event) {
	  // Android doesn't close the notification when you click it
	  // See http://crbug.com/463146
	  event.notification.close();
	  // Check if there's already a tab open with this URL.
	  // If yes: focus on the tab.
	  // If no: open a tab with the URL.
	  event.waitUntil(clients.matchAll({type: 'window', includeUncontrolled: true}).then(function(windowClients) {
	      for (var i = 0; i < windowClients.length; i++) {
	        var client = windowClients[i];
	        if ('focus' in client) {
	          return client.focus();
	        }
	      }
	    })
	  );
	});

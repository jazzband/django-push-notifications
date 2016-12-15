These are the main big items that still need to be done:

## General

* Use third party libraries to implement APNS and GCM.
* Clean up the tests accordingly. If APNS/GCM etc functionality is being tested
  in an upstream project, those tests don't need to be duplicated here.
  Django Push Notifications should be testing the integration of those backends.
* Review the impact of #260 and merge it. This can bring in a 2.0 release.

## Backends

* WebPush (#276)
* FCM (#302)

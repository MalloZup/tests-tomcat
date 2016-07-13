# Tests-Tomcat

Susetest testsuite for tomcat.

Testsuite dev and Maintainer:
Dario Maiocchi


## Tests-Coverage of testsuite

### Server-SIDE
* install tomcat

* start/stop tests for tomcat.
* tests tomcat listening socket for http and tomcat process. ( not very coherent with systemd for moment)


- Use https/ssl tomcat
* run differents instances of tomcat on same server ( on development)

###  Webtesting from Client Side
* get the homepage from tomcat-server on the client-side (wget)
  * and check the welcome greatings.

* tests docs, hello world apllication, all the standard pages docs.
* tests with web-crawling this pages.


* check the documentation/applet

* test return code, response from web-server , when  differents admins/user try to managing tomcat.

TOMCAT USERS in the testsuite :
user:               pwd

tomcat 		    opensuse
admin	            ~~~  ---> 
manager		    ~~~

  <user username="tomcat" password="opensuse" roles="tomcat"/>
  <user username="manager" password="opensuse" roles="manager-gui,manager-script,manager-jmx,manager-status"/>
  <user username="admin" password="opensuse" roles="admin-gui"/>



## Other possible not defined tests-cases


## Need research:


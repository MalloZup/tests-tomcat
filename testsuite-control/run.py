#! /usr/bin/python

import sys
import traceback
import twopence
import susetest
#from susetest_api import assertions
import suselog
from lib import tomcat
import re

journal = None
suite = "/var/lib/slenkins/tests-tomcat"
client = None
server = None

def setup():
    global client, server, journal

    config = susetest.Config("tests-tomcat")
    journal = config.journal

    client = config.target("client")
    server = config.target("server")

### Helper Functions ##
def assert_equal(node, command, expected):
	''' this function catch the output of sucesseful command and expect a result string
 	it check that a command success with something as string.'''
        journal.beginTest("for successful cmd: \"{}\" ASSERT_OUTPUT:  \"{}\" ".format(command, expected))
	
	status = node.run(command)
        if not (status):
                journal.failure("FAILURE: something unexpected!!{}".format(command))
                return False
	# check code exit of command.
        if (status.code != 0):
		journal.failure("COMMAND returned \"{}\" EXPECTED 0".format(str(status.code)) )
        # check output of  command.
        s = str(status.stdout)
	s = s.rstrip()
        if  (expected in s):
        	journal.success("ASSERT_TEST_EQUAL to {} PASS! OK".format(command))
		return True
	else :
           journal.failure("GOT Output:\"{}\",  EXPECTED\"{}\"".format(s, expected))
	   return False

def assert_fail_equal(node, command, expected, code):
	''' this function catch the output of failed command and expect a result string
 	it check that a command fail with something as string.'''
        journal.beginTest("For failed command \"{}\" is expected \"{}\" ".format(command, expected))
	
	status = node.run(command)
        if (status):
                journal.failure("COMMAND SHOULD FAIL but is not! !!{}".format(command))
                return False
	# check code exit of command.
        if (status.code != code):
		journal.failure("COMMAND returned \"{}\" EXPECTED \"{}\"".format(str(status.code), str(code)) )
        # check output of failed command.
        s = str(status.stdout)
        if  (expected in s):
        	journal.success("ASSERT_TEST_FAILURE_EQUAL for {} PASS! OK".format(command))
		return True
	else :
           journal.failure("GOT \"{}\",  EXPECTED\"{}\"".format(s, expected))
	   return False

def run_command(node, command, msg_fail, msg_success):
        journal.beginTest("Command executed %s" % command  )
        if not node.run(command, timeout = 8000):
                journal.failure(msg_fail)
		return False
        journal.success(msg_success)
        return True

def run_command_no_log(node, command, msg_fail, msg_success):
        if not node.run(command, timeout = 8000):
        	journal.beginTest("Command FAIL{}".format(command)  )
	        journal.failure(msg_fail)
		return False
def run_command_timeout(node, command, msg_fail, msg_success, timeout, testname):
        journal.beginTest(testname)
        if not node.run(command, timeout = timeout):
                journal.failure(msg_fail)
		return False
        journal.success(msg_success)
        return True


#####################################
## server functions and tests only on the SERVER-SIDE ##
####################################
def get_tomcat(server):
    journal.beginTest("Install tomcat on the server")

    packages = "tomcat tomcat-webapps tomcat-admin-webapps tomcat-docs-webapp"

    if server.run("zypper -n in {}".format(packages), timeout=300):
        journal.success("Tomcat Installation OK!")
    else:
        journal.failure("Tomcat Installation FAIL!")

def setup_tomcat(server):
    conf_tomcat= "/etc/tomcat"
    data = "/var/lib/slenkins/tests-tomcat/tests-server/data"
 
    journal.beginGroup("Start the tomcat server and configure it")
    run_command(server, "mv  {}/tomcat-users.xml {}/tomcat-users.xml".format(data, conf_tomcat), "TOMCAT SET USER FAIL!", "TOMCAT SET USER OK!")
    run_command(server, "systemctl start tomcat; systemctl status tomcat", "TOMCAT CONF FAIL!", "TOMCAT CONF OK!")


def start_stop_tests_server(server):
    run_command(server, "systemctl restart tomcat; systemctl status tomcat; systemctl stop tomcat; systemctl start tomcat; systemctl status tomcat", "RESTART/STOP TEST FAIL!", "RESTART/STOP TEST OK!")

def find_html_sites(host_dir):
    ''' find html pages in specific directory on server, give a string, that need a split for wget :) '''
    status = server.run("cd {}; find  -name \"*.html\" | sed 's/^..//'".format(host_dir))
    if not (status):
               journal.failure("something wrong with find command!")
               return None
    return str(status.stdout)

def multiple_tomcat(number_webServer):
    ''' this test enable running multiples tomcats web-server on same server
         number_istances = 1 will add one instance more additionaly. so (1 + number_istances)'''
    # this variable is only for begin. after we should have this a in iterator on for loop with number_instances ! :)
    journal.beginGroup("Configure {} instances of TOMCAT on same server !".format(number_webServer))
    number_webServer = number_webServer + 1

    for num in range(1, number_webServer):
        run_command(server, "cp -a /etc/tomcat /etc/tomcat{0}/; cp -a /usr/share/tomcat /usr/share/tomcat{0};".format(num), "fail to configure multiples machines", "multiple machine conf ok!")
	one = str(9500 + num)
	two = str (8080 + num)
        tree = str (8443 + num)
        four = str (8009 + num)
        configure_port = '''  sed -i 's/port="8005" shutdown="SHUTDOWN"/port="{1}" shutdown="SHUTDOWN"/' /etc/tomcat{0}/server.xml ;
	                      sed -i 's/port="8080" protocol="HTTP\/1.1"/port="{2}" protocol="HTTP\/1.1"/' /etc/tomcat{0}/server.xml;
			      sed -i 's/redirectPort="8443"/redirectPort="{3}"/g' /etc/tomcat{0}/server.xml ;
  			      sed -i 's/<Connector port="8009" protocol="AJP/<Connector port="{4}" protocol="AJP/' /etc/tomcat{0}/server.xml '''.format(num, one, two , tree , four )
 
        run_command_no_log(server, configure_port, "fail to configure tomcat instance_num: {0} machines", "multiple instance num:{0} ok!".format(num))

	# systemd service copy and conf.
        systemd_conf = "cp /usr/lib/systemd/system/tomcat.service /usr/lib/systemd/system/tomcat{0}.service;".format(num)
	service_modify = " sed -i 's/\/etc\/tomcat\/tomcat.conf/\/etc\/tomcat{0}\/tomcat.conf/' /usr/lib/systemd/system/tomcat{0}.service".format(num)	
        run_command_no_log(server, systemd_conf + service_modify , "fail to conf systemd for instance num {0}", "multiple machine, instance num {0} OK!".format(num))
	# /usr/share/tomcat and soft link stuff.
	# rm soft links

 	rm_soft_link = "cd /usr/share/tomcat{0} ; rm conf lib logs temp webapps work;  cd;".format(num)
	create_dir = ''' cp -a /var/log/tomcat /var/log/tomcat{0}; cp -a /usr/share/java/tomcat/ /usr/share/java/tomcat{0};
			 cp -a /var/cache/tomcat /var/cache/tomcat{0}; cp -a /srv/tomcat /srv/tomcat{0};'''.format(num)
     
        new_soft_link = ''' cd /usr/share/tomcat{0}; ln -s /etc/tomcat{0}/ conf; ln -s /var/log/tomcat{0}/ logs;
			    ln -s /var/cache/tomcat{0}/temp/ temp ; ln -s /srv/tomcat{0}/webapps/ webapps;
			    ln -s /var/cache/tomcat{0}/work/ work ;  ln -s /usr/share/java/tomcat{0}/ lib; cd; '''.format(num)

	# tomcat.conf stuff
	tomcat_conf = ''' cd /etc/tomcat{0}/; sed -i 's/\/usr\/share\/tomcat/\/usr\/share\/tomcat{0}/' tomcat.conf;
         		  sed -i 's/\/var\/cache\/tomcat\/temp/\/var\/cache\/tomcat{0}\/temp/' tomcat.conf; cd'''.format(num)

        run_command_no_log(server, rm_soft_link + create_dir + new_soft_link  , "FAIL to config main tomcat folder for instance{0}".format(num), "tomcat main folder conf instance num {0} OK!".format(num))

        run_command_no_log(server, tomcat_conf  , "FAIL to config main tomcat folder for instance{0}".format(num), "tomcat main folder conf instance num {0} OK!".format(num))
	# start the services !

	run_command(server, "systemctl start tomcat{0}; systemctl status tomcat{0}".format(num), "fail to start tomcat service numb {}".format(num), "tomcat instance {0} started!{0}".format(num))         
	#  test wgetting home page    
        run_command(client, "wget {0}:{1}".format(server.ipaddr, two), "fail to download index TOMCAT instance {0} PAGE!".format(num), "homepage tomcat{} wget OK!".format(num))
    #overall status from tomcats servers...
    run_command(server, "systemctl status tomcat*", "fail to display status of servers", "status server ok")
    

def test_tomcat_cmd(server):
	journal.beginGroup("testing various cmd for tomcat server""")
	#https://bugzilla.redhat.com/show_bug.cgi?id=1240279
	run_command(server, "tomcat-digest" , "fail to execute tomcat-digest. FAIL!", "tomcat digest ok!")         



def test_tomcat_user(server):
	''' testing commands as tomcat user'''
	journal.beginGroup("User tomcat for server tests")
	assert_equal(server, "su tomcat -c \"whoami\"", "tomcat")
	assert_equal(server, "su tomcat -c \"umask\"", "0022")
	assert_equal(server, "su tomcat -c \"cd;pwd\"", "/usr/share/tomcat") # for each instance create a user ?


def ssl_tomcat(server):
        ''' setup ssl tomcat server'''

        keystore_path = '/tmp/'
        genkey = '''cd ;
        keytool -genkey -noprompt  -alias alias1  -dname "CN=mqttserver.ibm.com, OU=ID, O=IBM, L=Hursley, S=Hants, C=GB"  -keystore keystore  -storepass password  -keypass password
        $JAVA_HOME/bin/keytool -genkey -noprompt  -alias tomcat  -dname \"CN=foo, OU=ID, O=Gino, L=Hursley, S=Hants, C=DE\"  -keystore {0}keystore \\
         -storepass password  -keypass password '''.format(keystore_path)

        run_command(server, genkey, "fail genkey", "genkey OK!")

        tomcat_server_xml = "/etc/tomcat/server.xml"
        tmp_config =  ''' cat > /tmp/ssl_temp.conf <<EOF
         <Connector SSLEnabled=\"true\" acceptCount=\"100\" clientAuth=\"false\"
         disableUploadTimeout=\"true\" enableLookups=\"false\" maxThreads=\"25\"
         port=\"8443\" keystoreFile=\"{0}keystore\" keystorePass=\"password\"
         protocol=\"org.apache.coyote.http11.Http11NioProtocol\" scheme=\"https\"
         secure=\"true\" sslProtocol=\"TLS\" />\nEOF
        '''.format(keystore_path)

        find_line = "grep \'clientAuth=\"false\" sslProtocol=\"TLS\" />\' /etc/tomcat/server.xml -no | cut -d\':\' -f1"
        status = server.run(find_line)
        line = int(status.stdout)
        line = line + 2
        port = 8443
        run_command(server, tmp_config, "fail to append ssl config!", "append ssl-config ok!")
        run_command(server, "sed -i '{0}r/tmp/ssl_temp.conf' {1}".format(line, tomcat_server_xml), "fail ssl-config", "ssl-config OK!")
        run_command(server, "systemctl restart tomcat", "restart tomcat fail!", "restart tomcat OK!")

        listen_test = "until ss -ltp | grep https && ps -ef | grep tomcat; do echo \"+++TOMCAT not LISTENING/READY!++++\"; sleep 2; done"
        test_title = "verify that tomcat server is listening. socket and process verification!"
        run_command_timeout(server, listen_test,  "TOMCAT not LISTENING AT ALL!! FAIL", "TOMCAT SERVER LISTENING!!OK", 120, test_title)
        run_command(server, "wget --no-check-certificate https://{0}:{1}".format(server.ipaddr,port) , "fail to append ssl config!", "append ssl-config ok!")


##########################################
## client functions and tests ##
##########################################
## WEB-testing fro tomcat. 
##########################################
def user_page_test(node, user, pwd, page, expect, code):
	 assert_fail_equal(node, "wget --user {} --password {} http://{}:8080/{}".format(user, pwd, server.ipaddr, page), expect, code)

# get a file from tomcat
def wget_files(client, server):
    ''' web-pages tests for tomcat'''
    # wget exit:  6 = Username/password authentication failure.  
    #             8 = Server issued an error response. 

    listen_test = "until ss -ltp | grep http-alt && ps -ef | grep tomcat; do echo \"+++TOMCAT not LISTENING/READY!++++\"; sleep 2; done"
    # http responses.
    file_401 = "401 Unauthorized"
    file_403 = "403 Forbidden"
    congrat = "grep \"If you're seeing this, you've successfully installed Tomcat. Congratulations\" index.html; mv index.html homepage.html"
    
    journal.beginGroup("Download index files from client to test the Web-server")
    
    # before running wget, verify that server tomcat is listening and running.
    test_title = "verify that tomcat server is listening. socket and process verification!"
    run_command_timeout(server, listen_test,  "TOMCAT not LISTENING AT ALL!! FAIL", "TOMCAT SERVER LISTENING!!OK", 120, test_title)


    # ** HOME-PAGE web-TESTS **
    run_command(client, "wget {}:8080".format(server.ipaddr), "fail to download index TOMCAT PAGE!", "index homepage TEST OK!")
    run_command(client, congrat,  "HOMEPAGE Welcom string not found FAIL!", "HOMEPAGE TEST OK!")
    # ** SAMPLE_PAGE web-TESTS **
    run_command(client, "wget {}:8080/sample/hello".format(server.ipaddr), "fail to download index TOMCAT SAMPLE!", "index SAMPLE TEST OK!")

    # ** HOST_MANAGER web-TESTS**
    run_command(client, "wget --user admin --password opensuse http://{}:8080/host-manager".format(server.ipaddr), "WEB-TEST-wget host-manager FAIL", "web-TEST-wget hostmanager OK!")
    user_page_test(client, "ADMIN", "opensuse", "host-manager", file_401, 6)
    user_page_test(client, "tomcat", "opensuse", "host-manager", file_403, 8)
    user_page_test(client, "manager", "opensuse", "host-manager", file_403, 8)
    
    # ** tomcat/page MANAGER TESTS**
    run_command(client, "wget --user manager --password opensuse http://{}:8080/manager/status".format(server.ipaddr), "WEB-TEST-wget manager FAIL", "web-TEST-wget manager OK!")
    user_page_test(client, "MaNaGer", "opensuse", "manager/status", file_401, 6)
    user_page_test(client, "tomcat", "opensuse", "manager/status", file_403, 8)
    user_page_test(client, "admin", "opensuse", "manager/status", file_403, 8)
    
    # ** DOCS TESTS **
    docs = find_html_sites("/usr/share/tomcat/webapps/docs")
    for web in docs.split() :
   	 run_command(client, "wget http://{}:8080/docs/{}".format(server.ipaddr, web), "WEB-TEST-wget docs-pages FAIL", "web-TEST-wget {} OK!".format(web))
   
    # ** EXAMPLES tests **
    examples = find_html_sites("/usr/share/tomcat/webapps/examples")
    journal.beginGroup("Test examples web-pages")
    for web_ex in examples.split() :
   	 run_command(client, "wget http://{}:8080/example/{}".format(server.ipaddr, web_ex), "WEB-TEST-wget examples-pages FAIL", "web-TEST-wget {} OK!".format(web_ex))
    
def multiple_web_test(client,server, instances):
    journal.beginGroup("testing all tomcat instances, web-homepage")
    webserver_max = 8081 + instances
    for port in range(8081, webserver_max):
	    run_command(client, "wget {0}:{1}".format(server.ipaddr,port), "fail to download index TOMCAT PAGE!", "index homepage TEST OK!")

def check_log(server):
	check_SEVERE_log = "grep SEVERE  /var/log/tomcat/catalina*.log "
        journal.beginTest("checking catalina logs-file!")
              
        status = server.run(check_SEVERE_log)
        if not (status):
                journal.failure("FAILURE: something unexpected!!{}".format(command))
                return False
        # if grep return 0, it means we found some errors !
        if (status.code == 0):
                journal.failure("SEVERE ERRORS found in catalina!".format(str(status.code)))
        else :
           journal.succes("CHECKING LOG CATALINA OK! no SEVERE ERRORS FOUND")
           return True

######################
##              
#   MAIN
##
######################

setup()
tomcat_instances = 20

try:
    get_tomcat(server)
    setup_tomcat(server)
    test_tomcat_cmd(server)
    wget_files(client, server)
    start_stop_tests_server(server)
    test_tomcat_user(server)
    ssl_tomcat(server)
    multiple_tomcat(tomcat_instances)
    multiple_web_test(client, server, tomcat_instances)
    check_log(server)

except:
    print "Unexpected error"
    journal.info(traceback.format_exc(None))
    raise

susetest.finish(journal)

# docker-nagios-retriever

This component is used to retrieve regular statuses from a nagios server and ingest these into a rabbitmq exchange for further processing by other components.

The component is autobuilt into the docker image mmaschenk/nagios-retriever

The docker image requires the following environment variables to be defined:

<dl>
<dt>MQRABBIT_USER</dt>
<dd>The username for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_PASSWORD</dt>
<dd>The password for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_USER</dt>
<dd>The username for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_HOST</dt>
<dd>The hostname for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_VHOST</dt>
<dd>The virtual hostname for connecting to the rabbitmq server. Defaults to /</dd>

<dt>MQRABBIT_PORT</dt>
<dd>The port for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_EXCHANGE</dt>
<dd>The name of the rabbitmq exchange that the messages will be ingested into</dd>

<dt>NAGIOS_URL</dt>
<dd>The url to the nagios json output producing the service list. This is usually of the form https://&lt;hostname>/nagios/cgi-bin/statusjson.cgi?query=&lt;your query></dd>

<dt>NAGIOS_USER</dt>
<dd>The username for accessing the nagios server</dd>

<dt>NAGIOS_PASSWORD</dt>
<dd>The password for accessing the nagios server</dd>

</dl>

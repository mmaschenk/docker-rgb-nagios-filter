# docker-rgb-nagios-filter

This component is used to retrieve nagios satuses from a rabbitmq and ingest these into a rabbitmq exchange for further processing by other components.

The component is autobuilt into the docker image mmaschenk/nagios-retriever

The docker image requires the following environment variables to be defined:

<dl>
<dt>MQRABBIT_USER</dt>
<dd>The username for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_PASSWORD</dt>
<dd>The password for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_HOST</dt>
<dd>The hostname for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_VHOST</dt>
<dd>The virtual hostname for connecting to the rabbitmq server. Defaults to /</dd>

<dt>MQRABBIT_PORT</dt>
<dd>The port for connecting to the rabbitmq server</dd>

<dt>MQRABBIT_EXCHANGE</dt>
<dd>The name of the rabbitmq exchange that the messages will be read from</dd>

<dt>MQRABBIT_DESTINATION</dt>
<dd>The routing key of the rabbitmq queue that the rgb display messages will be ingested into</dd>

</dl>

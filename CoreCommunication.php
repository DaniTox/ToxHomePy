<?php
error_reporting(E_ALL);

/* Get the port for the WWW service. */
$service_port = 1717;

/* Get the IP address for the target host. */
$address = 'localhost';

/* Create a TCP/IP socket. */
$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
if ($socket === false) {
    echo "socket_create() failed: reason: " . 
         socket_strerror(socket_last_error()) . "\n";
}

echo "Attempting to connect to '$address' on port '$service_port'...";
$result = socket_connect($socket, $address, $service_port);
if ($result === false) {
    echo "socket_connect() failed.\nReason: ($result) " . 
          socket_strerror(socket_last_error($socket)) . "\n";
}

$json_string = ''; //TODO: create a json string and add it to variable
$out = '';

echo "Sending json string...";
socket_write($socket, $json_string, strlen($json_string));
echo "OK.\n";

echo "Reading response:\n\n";
while ($out = socket_read($socket, 2048)) {
    echo $out;
}

socket_close($socket);
?>
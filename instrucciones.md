El programa ```create_docker_compose.py``` crea un archivo copiando ```docker-compose-dev.yaml```, y segun el numero recibido por parametro, escribe en el archivo la cantidad de clientes deseada, y finalmente, reemplaza el archivo.

Para ejecutar, correr la siguiente instruccion por linea de comandos:  
``` python3 create-docker-compose.py X ```  
Siendo X el numero de clientes a declarar

## Ejercicio 2
Para comprobar el funcionamiento del volumen, una vez que corro `make docker-compose-up`, modifico los valores de puerto de los archivos `config.ini` para el server, y `config.yaml` para los clientes, luego, cuando vuelvo a ver los logs con `make docker-compose-logs`, veo que los clientes pudieron comunicarse con el server ambos utilizando el nuevo puerto.

## Ejercicio 3
Dentro de la carpeta `server_test`, ejecutar `./test.sh`para ejecutar el script, esto creara un archivo llamado `test.txt`, el cual contendra el resultado del comando nc y la debajo la respuesta recibida por parte del servidor.

## Ejercicio 4
Se añadieron handlers de `SIGTERM` en ambos server y client. Los cuales funcionan dela siguiente manera:
#### Server
Al principio de la funcion de loop del server andes de empezar el loop, declaro,  usando la libreria signal, cual va a ser la funcion a ejecutar una vez recibida la signal `SIGTERM`. En este caso, lo que realiza la funcion la cual llame `handle_sigterm` es setear el campo `running` del servidor en `False` y cerrar todos los sockets de clientes activos y por ultimo, cerrar el socket del server.

#### Cliente
De la misma forma que en el server, se declara un canal por el cual entrara la señal `SIGTERM`, lo que significa que, en caso de que se escriba algo por ese canal, significa que el programa recibio la signal.
Luego, dentro del loop principal, se evaluan dos opciones: caso de timeout, que no nos interesa en este caso y caso `sigchan`, donde se procedera a cerrar la conexion del cliente y salir de la funcion.

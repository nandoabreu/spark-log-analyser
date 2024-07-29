## Create mocked data

To start mocking data to log files and publishing them to Spark, once the dev env is set,
call the following commands. They are bash calls, packed as make commands. Calling the make targets
is the same as copying the commands from the [Makefile](../Makefile).


### Note about this project's Makefile

This project's [Makefile](../Makefile) holds necessary commands to run the instructions os this page,
but it starts from dynamically creating and updating a .env file in the root of this repo
with variables and values loaded from the [env.toml](../env.toml) file.

In case Makefile's commands are triggered manually, remember to create and update the .env
file so that the expected variables are loaded, or include them to the command, as in:

```shell
PYTHONPATH=src BIND_PORT=9021 poetry run python -m app
```

### Note about containers in this project

Podman is a community option for docker, and is used in this project. We recommend
[installing podman](https://podman.io/docs/installation), but docker can be used instead.
The Makefile targets must be updated or their commands altered on the command line.

### Start a temporary Spark service (optional)

In case there is no Spark service available to work with, the following command will create a local one.
It will create a Kafka broker service in a podman container, from [Apache](https://hub.docker.com/u/apache).

```shell
make test-start-kafka
```

### Set up a Kafka UI service (optional)

A web interface can be set to check and manage Kafka services. The following command will spin a
podman container with [Kafka UI, by Provectus](https://github.com/provectus/kafka-ui).

```shell
test-start-kafka-ui
```

### Create mocked http and app logs

From the Makefile target, 97-99 logs will be created per run:
```shell
make test-publish-mocked-logs
```

### Publish logs to Kafka

From the Makefile target, run:
```shell
make test-publish-mocked-logs
```

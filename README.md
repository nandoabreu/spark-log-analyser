# spark-log-analyser

Spark log analyser, merging Apache with Application logs to analyse users' request to Apache and response from App.

This project delivers an end-to-end solution to merge logs from Apache and an web App to compare requests and
responses. This project's main goal is to analyse streaming data from Kafka, using Spark.


## Requisites

To analyse streaming data, a Kafka service is expected to be running and having Apache and App logs delivered to it.
This solution has a test scenario to mock data, in case the environment isn't already set.

The logic here considers patterns in Apache and App logs that will probably differ from a production environment,
so some minimal Python coding may be required to tune how the streaming data is parsed.

### Environment settings

All settings needed for this solution to run are in the [env.toml](env.toml) file at the root of this project.
`make` commands are responsible for updating the dynamically created [.env](.env) on every [Makefile](Makefile)
run.

### Publish logs to Kafka

Once this project's goal is about processing data already in Kafka, there will be no support for publishing
data to Kafka, however, the test environment for this project has scripts that can be used to process
and publish production logs to Kafka.

### Set the test environment

The following commands will enable a test environment with:

- A Kafka service running locally on a Podman container
  - To install Podman, [check this link](https://podman.io/docs/installation#installing-on-linux)
- Mocked Apache and App logs, created locally with scripts
- Apache and App logs stream publishing to Kafka

```shell
make setup-dev
make test-start-kafka
make test-create-mocked-logs
```
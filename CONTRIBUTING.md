# Guide to Contributing
## Requirements
See the `README.md` for requirements.

## Technology Overview
### GNU Make
GNU make is used to build, deploy, redeploy, and clean up services. The `Makefile` describes
how this is done. The different `make` targets are described later.

### Docker
Docker is used to containerise each service. Services should be written in Python 3.13 unless
discussed prior. The `Dockerfile` in each service directory describes how the service
container should be built, here's an annotated example:

```Dockerfile
# use python 3.13.1, container based on Alpine - a very slim Linux distro
FROM python:3.13.1-alpine

# install uv, the package manager we are using
COPY --from=ghcr.io/astral-sh/uv:0.5.30 /uv /uvx /bin/

# set up working directory, copying over service files
WORKDIR /app
# .venv should be ignored in the .dockerignore
COPY . .

# don't touch this, it speeds up build times
ENV CASS_DRIVER_NO_EXTENSIONS=1

# install external requirements
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# install shared library
RUN uv pip install -e shared/

# create a new unprivileged user
RUN addgroup -S group1 && adduser -S user1 -G group1
# set it to own the /app directory
RUN chown -R user1:group1 /app
# use new user
USER user1:group1

# run the service
CMD ["uv", "run", "main.py"]
```

There is also a `.dockerignore` which specifies files and directories
to ignore in each service build context.

Services need to be containerised to allow us to deploy them using Kubernetes.

### Kubernetes (K8s)
K8s is a container orchestration system. Essentially, it is in charge of deploying
containers, networking them, etc. This is done by declaring the state of the system
you'd like to achieve in `.yaml` files, K8s will then attempt to bring the actual
state of the system in line with that configuration.

You shouldn't need to know much K8s to contribute your sub-system, but the
[Kubernetes docs](https://kubernetes.io/docs/home/) are a good place to learn a little
about what it does and understand the terminology to better communicate with the
team.

We use `minikube` to run a K8s cluster locally as typically K8s clusters
are run on cloud infrastructure.

### RabbitMQ
We are using a microservices architecture, this means that each service should have
essentially one task. Each service must not be coupled with another service until
runtime. What this means is that a service should not depend on code from another
service. Code reuse is done through the shared library (see Directory Structure section).

To only couple services at runtime, we use RabbitMQ to allow inter-process communication.
The idea is that a service (the client) will communicate with another (the server) by sending
a message to a message queue. The server will then "consume" said message queue to receive
messsages and process them.

Each service should have it's own RabbitMQ credentials, with the minimum possible credentials
needed for what it has to do. These credentials are randomly generated.

The key RabbitMQ components that we use are:
- Exchanges - where the client can publish messages to, which route messages to specific queues.
- Queues - a message queue that the client publishes it's message to (via the exchange), and the
           server consumes.

### ScyllaDB
ScyllaDB is our database solution. It uses Cassandra Query Language (CQL) which is very
similar to SQL. Check out the [documentation](https://docs.datastax.com/en/cql-oss/3.3/cql/cqlIntro.html)
for more information.

In our case, each subsystem should have it's own ScyllaDB credentials, and a [keyspace](https://university.scylladb.com/courses/data-modeling/lessons/basic-data-modeling-2/topic/keyspace/)
for which it has permissions to use. A subsystem should only have permissions for it's
own keyspace.

Keyspace names are encoded for some technical reasons, see the shared library for
encoding implementation.

### Valkey
TODO.

## Directory Structure
The base repository directory (the one that contains `.git/`) contains documentation markdown files
like `README.md` and this file. It also contains the `Makefile`, which is a type of script to build
and deploy all services in a local Kubernetes cluster.

```
.
├── k8s
│   └── crds
├── src
│   ├── operators
│   │   └── scylla-auth-operator
│   ├── shared
│   │   └── rpcs
│   └── template
│       ├── example-service
│       ├── example-service-2
│       └── k8s
│           ├── rabbitmq
│           └── scylla
└── tests
    └── integration
        └── template
```

`src/` contains directories, which each (with the exception of `src/shared` and `src/operators`)
represent a subsystem. Within each subsystem directory, there are more directories which each
(with the exception of `src/{subsystem}/k8s`) represent services.


`src/shared` contains a Python library that all services can use, it provides abstractions
over creating ScyllaDB sessions and RabbitMQ connections. `src/shared/rpcs` is the RPC submodule,
which defines base classes for RPC clients and services, see the RPC section for more information
on RPCs.

`src/operators` contains custom Kubernetes operators, you shouldn't need to touch these
when developing your own subsystems.

`src/{subsystem}/k8s` should contain subsystem specific Kubernetes configuration, including
a `namespace.yaml` which defines a Kubernetes namespace for each subsystem's resources.

`src/{subsystem}/k8s/rabbitmq` contains Kubernetes configuration for required RabbitMQ exchanges
and queues for RPC calls within each subsystem, you may have to manually edit these configuration
files.

`src/{subsystem}/k8s/scylla` contains Kubernetes configuration for a subsystems ScyllaDB credentials,
keyspace, and permissions.

`k8s` contains "global" Kubernetes configurations for our infrastructure, you shouldn't need to touch
any of this when developing your own subsystems. To be clear: do not touch any "global" Kubernetes config
without asking [@peterc-s](https://github.com/peterc-s/) or [@wjgr2004](https://github.com/wjgr2004/)

`tests` contains a testing library (`tests/lib.py`), integration (`tests/integration/`), and end-to-end
tests (will go in `tests/e2e/` when we have them). 

## Creating Subsystems
To create a subsystem, use the `create-subsystem.sh` script (`./create-subsystem.sh` for usage).
For example, if we run `./create-subsystem.sh example` we get the following:
```
src
└── example
    └── k8s
        ├── namespace.yaml
        └── scylla
            └── example-scylla-perms.yaml
```

As you can see, the script will create an example subsystem, it's ScyllaDB credentials
K8s configuration, and it's K8s namespace (this file also configures a network policy

## Creating Services
Once you've created a subsystem with `create-subsystem.sh`, you can create services
using `create-service.sh` (`./create-service` for usage). For example, if we run
`./create-service example example-service "An example service."` we get:
```
src
└── example
    ├── example-service
    │   ├── Dockerfile
    │   ├── .dockerignore
    │   ├── example-service.yaml
    │   ├── main.py
    │   ├── pyproject.toml
    │   ├── README.md
    │   └── uv.lock
    └── k8s
        ├── namespace.yaml
        └── scylla
            └── example-scylla-perms.yaml

You can see it has generated files for the service within it's subsystem. This
includes:
- The `Dockerfile` and `.dockerignore` as mentioned earlier.
- The base service K8s configuration (`example-service.yaml` in this case).
- A `pyproject.toml` with the required dependencies and the given service description.
- An empty `README.md` to write API documentation in.
- `uv.lock`, generated using `uv sync`, which should also create a Python virtual environment
  with only the required dependencies.

## Creating RPCs
Normally, to call a function we just define it and call it. However, when doing distributed
systems we want to call a function (procedure) on another remote system. To do this, we use
a Remote Procedure Call (RPC).

We use RabbitMQ to perform RPCs.

First, we define our call and response exchanges, along with the call queue in the 
`src/{subsystem}/k8s/rabbitmq/{rpc-name}.yaml`, which looks like this:
```yaml
# call exchange
apiVersion: rabbitmq.com/v1beta1
kind: Exchange
metadata:
  name: ping-rpc-call-exc
spec:
  name: ping-rpc-call-exc
  autoDelete: false
  durable: true
  rabbitmqClusterReference:
    name: rabbitmq
    namespace: rabbitmq

---

# response exchange
apiVersion: rabbitmq.com/v1beta1
kind: Exchange
metadata:
  name: ping-rpc-resp-exc
spec:
  name: ping-rpc-resp-exc
  autoDelete: false
  durable: true
  rabbitmqClusterReference:
    name: rabbitmq
    namespace: rabbitmq

---

# call queue
apiVersion: rabbitmq.com/v1beta1
kind: Queue
metadata:
  name: ping-rpc-call-q
spec:
  name: ping-rpc-call-q
  autoDelete: false
  durable: true
  rabbitmqClusterReference:
    name: rabbitmq
    namespace: rabbitmq
```

The call exchange means that the client can send a message and get it routed to the
call queue. The response exchange means that the server can send it's response to
a response queue (when the client declares it).

We also need to bind the call queue to the call exchange, so that the call exchange
can actually route messages to the call queue, we do this by adding this to the `.yaml`:
```yaml
---

# ping-rpc-call-exc -> ping-rpc-call-q
apiVersion: rabbitmq.com/v1beta1
kind: Binding
metadata:
  name: ping-rpc-call-bind
spec:
  source: ping-rpc-call-exc
  destination: ping-rpc-call-q
  routingKey: "ping-rpc-call-q"
  destinationType: queue
  rabbitmqClusterReference:
    name: rabbitmq
    namespace: rabbitmq
```

Due to the nature of Kubernetes, we can have multiple clients calling the same type of
RPC on multiple different servers, so each server needs to know how to route it's response
back to the client properly. This is why the client will (in code, not configuration) declare
a unique queue for responses to be sent back over, bound to the response exchange.

The `shared.rpcs` sub-module defines abstract base classes for RPC servers and clients. Luckily,
all of the details for declaring response queues, binding them to exchanges, and ensuring
that the RPC server replies over the correct queue, etc. are all abstracted out, so you
shouldn't have to worry about these details.

If you haven't noticed already, there is a naming convention for RPCs, which is as follows:
- {rpc-prefix}-resp-q-{UUID} - name of the queue an RPC server should
                               respond to, declared by the RPC client.
- {rpc-prefix}-resp-exc - name of the response exchange for the RPC server
                          to send it's response to, declared by k8s yaml
                          in src/{subsystem}/rabbitmq/{rpc-prefix}.yaml.
- {rpc-prefix}-call-q - name of the queue to send a call to, declared
                        by k8s yaml in {sub-system}/rabbitmq/{rpc-prefix}.yaml, consumed
                        by an RPC server.
- {rpc-prefix}-call-exc - name of the exchange to send a call to, declared
                          by k8s yaml in {subsystem}/rabbitmq/{rpc-prefix}.yaml.

The {rpc-prefix} is essentially the name of the RPC, and should be kept consistent across the
server and client. Note the {UUID} in the response queue, this is that unique queue identifier
to properly route responses.

### Writing an RPC
The `template` subsystem implements a very rudimentary `ping` RPC, which simply responds to
`Ping!` with `Pong!` and anything else with `That's not a ping!`.

#### Clients
To define the client, we create a new Python file in the `src/shared/rpcs` directory, it should
be the same as your {rpc-prefix}, but with any hyphens replaced with underscores. It's placed
in the shared library because many different services may want to call the same RPC.

Here's the example from the `ping-rpc` RPC:
```Python
"""
Example implementation of an extremely
simple "ping - pong" RPC client.
"""


from shared.rpcs import RPCClient


class PingRPCClient(RPCClient):
    """
    Sub-class of RPC client which just
    sends "Ping!".
    """

    def call(self, *args, **kwargs):
        """
        Send "Ping!" to server.
        """
        return self._call(body="Ping!")
```

When you implement a client, it must be a subclass of `RPCClient`, and it must implement
`self.call(self, *args, **kwargs)`, which must return `self._call(body)`.

`self._call()` is an internal method which actually performs the RPC call and waits on a response,
we propagate it's value as that is the response from the server. In reality, you should be encoding
your requests and responses as json (the example does not do this as it is just for illustrative
purposes).

#### Servers
Server code is written within the `main.py` of the service which serves the RPC. This
is so that no other service could possibly attempt to serve the RPC.

As an example, from the `template`:
```python
from shared import rpcs


class PingRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which
    simply returns "Pong!" no matter
    what.
    """

    def process(self, body, *args, **kwargs):
        """
        Respond with "Pong!", unless message
        isn't "Ping!".
        """
        if body.decode() == "Ping!":
            return "Pong!"
        return "That's not a ping!"
```

When you implement a server, it must be a subclass of `RPCServer`, and it must implement
`self.process(self, body, *args, **kwargs)` which must return the response for a given
message (passed in through `body`). Again, this should be done using json.

The server must always assume a message it receives is malicious - do not blindly
trust potentially user supplied data. Ensure you securely de-serialise any json.

### Using an RPC
Once you've written the configuration and code for a certain RPC, we need to set up permissions
for service users to access the RPC queues and exchanges, and then write the logic to actually
use the code.

#### Setting up Permissions
In the RPC server service directory, we must modify the services `.yaml` K8s configuration
to allow it to write to the RPC response exchange, and read from the call queue.

In the `template` example, the permissions in `src/template/example-service/example-service.yaml`
are given as follows:
```yaml
apiVersion: rabbitmq.com/v1beta1
kind: Permission
metadata:
  name: example-service-rabbitmq-permission
  namespace: template
spec:
  vhost: "/"
  userReference:
    name: "example-service-rabbitmq-user"
  permissions:
    write: "ping-rpc-resp-exc" # give write access to response exchange
    configure: ""
    read: "ping-rpc-call-q" # give read access to call queue
  rabbitmqClusterReference:
    name: rabbitmq
    namespace: rabbitmq
```

The client's permissions are a bit more complicated. A client needs to be able to:
- Read from the response queue and exchange.
- Write to the call exchange and it's unique response queue.
- Configure the response exchange and it's unique response queue.

Luckily (or unluckily), permissions are done with regex, so the above translates to:
```yaml
apiVersion: rabbitmq.com/v1beta1
kind: Permission
metadata:
  name: example-service-2-rabbitmq-permission
  namespace: template
spec:
  vhost: "/"
  userReference:
    name: "example-service-2-rabbitmq-user"
  permissions:
    write: "ping-rpc-(call-exc|resp-q-.*)" # write to call exchange and unique response queue
    configure: "ping-rpc-resp-(exc|q-.*)" # configure response exchange and unique response queue
    read: "ping-rpc-resp-(exc|q-.*)" # write to call exchange and unique response queue
  rabbitmqClusterReference:
    name: rabbitmq
    namespace: rabbitmq
```

#### In Code
The code for using the RPC is pretty simple. To start serving the `ping-rpc` we can do
the following in the server service:
```python
rpc_server = PingRPCServer(
    os.environ["RABBITMQ_USERNAME"],
    os.environ["RABBITMQ_PASSWORD"],
    "ping-rpc",
)

rpc_server.channel.start_consuming()
```

And to send a ping every second, we can import the `PingRPCClient` and write the following
in the client service:
```python
    ping_rpc = PingRPCClient(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
        "ping-rpc",
    )

    while True:
        response = ping_rpc.call()
        time.sleep(1)
```

### Documenting an RPC
You should document the expected json requests and responses in the server's `README.md`.

The client and server code should be simple enough that the API is clear just from reading it.

## Creating a Test
To create an integration test (which should test that an RPC API works correctly) you will need
to make a new testing file.

The `tests` directory tree looks like this:
```
tests
├── copy-secret.sh
├── Dockerfile
├── .dockerignore
├── __init__.py
├── integration
│   ├── __init__.py
│   └── template
│       ├── __init__.py
│       └── test_ping_rpc.py
├── lib.py
├── main.py
├── print-logs.sh
├── pyproject.toml
├── .python-version
├── README.md
├── testing.yaml
├── test-job.yaml
├── test-result.sh
└── uv.lock
```

You can ignore many of the files here, as they don't need touching to create new tests.
If your subsystem was the `example` subsystem, you would create a new directory `tests/integration/example`.
You should then create an empty file called `__init__.py` in that directory, this is so that
the main testing script can properly discover your test cases.

Then, you can create a test file, its name must start with `test` or else it won't be
discovered. Here's an example test file:
```Python
"""
Integration tests for the ping RPC.
"""

import os

from lib import AutocleanTestCase
from shared.rpcs.ping_rpc import PingRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class PingRPCTest(AutocleanTestCase):
    """
    Integration tests for the ping RPC.
    """

    def test_send_ping(self):
        """
        Test expected "Ping!" for a
        "Pong!" response.
        """
        client = PingRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        response = client.call()

        self.assertEqual(response, b"Pong!")

    def test_send_nothing(self):
        """
        Tests the case where the ping RPC isn't sent the
        correct request.
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        response = client.call("")

        self.assertNotEqual(response, b"Pong")
        self.assertEqual(response, b"That's not a ping!")
```

You should use our `AutocleanTestCase` rather than the default `unittest.TestCase`, this is
so that the test environment gets properly cleaned between test cases.

## Using GNU Make
You should not need to modify the `Makefile`, but you should know what some of the
useful targets do. To use make run `make <target>` in the same directory as the `Makefile`.

The main targets are:
- `deploy` - will try and get the system in it's fully deployed state.
- `build` - builds all service containers in the `minikube` context.
- `redeploy-unchecked` - will stop and redeploy our own services without checking if RabbitMQ, ScyllaDB, and Valkey are running.
- `redeploy` - will stop redeploy our own services, checking that infra is running, and deploying it if it isn't.
- `clean-all` - will stop `minikube`, and delete any persistent storage it had, essentially wiping the slate clean.

You can also set your own Docker runtime and Minikube driver in a file
named `.build_config.mk` (gitignored), for example:
```
DOCKER_RUNTIME:=docker
MINIKUBE_DRIVER:=virtualbox
```

For all other make targets (there are many), check the `Makefile` for comments.

## Rules
There are some rules so we can keep the codebase clean:
1. Create a new branch for each major feature you're adding, the branch name should be descriptive enough and doesn't need to include a name.
2. Attach feature branches to GitHub issues.
3. Keep the GitHub project up to date.
4. Before merging to main, you must pass the `pylint` action, CodeQL mustn't complain, and your changes must be reviewed by *at least* one other team member.
5. You must document well, use the example service and shared library as a reference point. Do not over-comment, your code **in most cases** should explain itself.
6. Document service APIs in the `README.md` (NOTE: no reference for this yet).
7. Your service APIs must be authenticated properly and tested.
8. UI must abide by the UI style guide.
9. Do not add any dependencies without prior discussion, dependencies can be liabilities.

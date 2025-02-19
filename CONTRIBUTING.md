# Guide to Contributing
## Requirements
See the `README.md` for requirements.

## Directory Structure
The base repository directory (the one that contains `.git/`) contains documentation markdown files
like `README.md` and this file. It also contains the `Makefile`, which is a type of script to build
and deploy all services in a local Kubernetes cluster.

```
.
├── k8s
└── src
    ├── shared
    └── template
        ├── example-service
        └── example-service-2
```

`src/` contains directories. With the exception of `src/shared/`, each directory represents a
sub-system, for example `src/template/` represents the `template` sub-system. Each directory
within a sub-system represents a service, for example `src/template/example-service/` represents
the `example-service` service.

`src/shared` contains a shared Python library to abstract away some boilerplate when creating
a service.

`k8s/` contains `.yaml` configuration files for Kubernetes objects, each service within a sub-system
should have it's own `.yaml` configuration file.

## Technology Overview
### GNU Make
GNU make is used to build, deploy, redeploy, and clean up services. The `Makefile` describes
how this is done. The different make targets are described later.

### Docker
Docker is used to containerise each service, services should be written in Python 3.13 unless
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

# run the service
CMD ["uv", "run", "main.py"]
```

Services need to be containerised to deploy on Kubernetes.

### Kubernetes (K8s)
K8s is a container orchestration system. Essentially, it is in charge of deploying
containers, networking them, etc.

You shouldn't need to know much K8s to contribute your sub-system, but the
[Kubernetes docs](https://kubernetes.io/docs/home/) are a good place to learn a little
about what it does.

We use `minikube` to run a K8s cluster locally.

## Creating a New Subsystem
The `src/template/` sub-system is meant to be a template of a very basic sub-system.

```
.
├── example-service
│   ├── Dockerfile
│   ├── main.py
│   ├── pyproject.toml
│   ├── README.md
│   └── uv.lock
└── example-service-2
    ├── Dockerfile
    ├── main.py
    ├── pyproject.toml
    ├── README.md
    └── uv.lock
```

### New Sub-system
To create a new sub-system, simply copy the template sub-system. Make sure you're
in `src/`, then run `cp -r template <new-sub-system>`, replacing `<new-sub-system>`
with the name of your sub-system.

Change directory to your new sub-system's. You should rename the example services with
`mv example-service <new-service-name>`, and `mv example-service-2 <new-service-name>`.

You should edit the `pyproject.toml` in each service to reflect their new names and
purposes.

In this state, the new services won't be deployed to K8s. You must also create copies of
`k8s/example-service.yaml` for each service, with the name reflecting the name of your
service. Within your new K8s `.yaml` config for your new services, you should replace
all occurrences of `example-service` with the name of your new service.

You will also need to make modifications to the code in `main.py` for the service
to actually be useful. Have a look at the code for each of the example services
to understand how services should be implemented.

### New Service
To create a new service, just create a copy of the `example-service` directory
with `cp -r example-service <new-service>`. You should then follow the steps above
from "You should edit the ..." to make sure your new service will be deployed.

Services must have a `Dockerfile`, as this is how the `Makefile` identifies
them.

## Using GNU Make
(NOTE: Valkey targets not currently present as it isn't ready yet)

You should not need to modify the `Makefile`, but you should know what some of the
useful targets do. To use make run `make <target>` in the same directory as the `Makefile`.

The targets provided in the main `Makefile` are:
- `all` - the default target used when `make` is called with no arguments, in this case it will try to reach the `deploy` target.
- `minikube` - will start up a Minikube VM.
- `minikube-clean` - will stop the Minikube VM.
- `minikube-restart` - will stop then start the Minikube VM.
- `minikube-clean-full` - will stop then delete the Minikube VM.
- `minikube-reset` - will stop and delete the Minikube VM, then start up a new one.
- `build` - will build all service containers in the Minikube context (will start Minikube if it isn't already running).
- `deploy` - will do what `build` does, deploy extra K8s objects for ScyllaDB, RabbitMQ, and Valkey, and then deploy the built service containers using configs in `k8s/`.
- `deploy-unchecked` - does what `deploy` does, but doesn't check if ScyllaDB, RabbitMQ, and Valkey are running, faster if you know those services are running.
- `deploy-clean` - will 'un-deploy' our services (but not ScyllaDB, RabbitMQ, etc.)
- `redeploy` - runs `deploy-clean` then `deploy`.
- `redeploy-unchecked` - runs `deploy-clean` then `deploy-unchecked`.
- `clean` - currently just `deploy-clean`.
- `clean-all` - currently just `minikube-clean-full`.

There are also targets specific to RabbitMQ, ScyllaDB, and Valkey. Though the
main useful one is `scylladb-clean` which will delete all databases, the
`deploy` target should create new databases. Some others include:
- `rabbitmq-creds` - prints credentials to log into the RabbitMQ management portal.
- `rabbitmq-manage` - start serving and open the RabbitMQ management portal.
- `print-services` - print all services the `Makefile` has identified.
- `check-docker` - checks if docker is running.

You can also set your own Docker runtime and Minikube driver in a file
named `.build_config.mk` (gitignored), for example:
```
DOCKER_RUNTIME:=docker
MINIKUBE_DRIVER:=virtualbox
```

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

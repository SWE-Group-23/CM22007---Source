##
# Vars
##

# include personal build options
-include .build_config.mk

# set docker runtime and minikube driver if not already in .build_config.mk
DOCKER_RUNTIME ?= docker
MINIKUBE_DRIVER ?= docker

# paths to Dockerfiles for each service
SERVICES=$(wildcard src/*/*/Dockerfile)
# names of services
SERVICE_NAMES=$(notdir $(patsubst %/Dockerfile, %, $(SERVICES)))

all: deploy

##
# Util
##

rabbitmq-manage:
	@kubectl rabbitmq manage rabbitmq

rabbitmq-creds:
	@echo Username:
	@kubectl get secret rabbitmq-default-user -o jsonpath='{.data.username}' | base64 --decode 
	@echo
	@echo Password:
	@kubectl get secret rabbitmq-default-user -o jsonpath='{.data.password}' | base64 --decode
	@echo

# print all the services in SERVICES and the path to their Dockerfile
print-services:
	@for service in $(SERVICES); do \
		name=$$(basename $$(dirname $$service)); \
		echo "$$name : $$service"; \
	done

# check if docker is running
check-docker:
	@if ! $(DOCKER_RUNTIME) info > /dev/null 2>&1; then \
		echo "Docker isn't running, please start the docker daemon (using systemd: \`sudo systemctl start $(DOCKER_RUNTIME)\`)."; \
		exit 1; \
	fi

##
# Build + Deployment
##

# build all services within minikube
build: minikube check-docker
	@echo "Building docker images inside Minikube..."
	@for service in $(SERVICES); do \
		name=$$(basename $$(dirname $$service)); \
		echo "Building $$name..."; \
		( \
			cd $$(dirname $$service); \
			uv lock; \
			minikube image build -t $$name .; \
		); \
		echo "Done!"; \
	done

rabbitmq-setup: minikube
	@echo "Installing rabbitMQ cluster operator..."
	@kubectl rabbitmq install-cluster-operator
	@echo "Getting rabbitMQ resource definitions..."
	@kubectl get customresourcedefinitions.apiextensions.k8s.io

# apply all k8s configs in the k8s/ directory
deploy: build rabbitmq-setup minikube
	@echo "Deploying services to K8s..."
	@kubectl apply -f k8s/
	@echo "Done!"

# delete all deployments in SERVICE_NAMES
deploy-clean:
	@echo "Deleting deployments..."
	@-for service in $(SERVICE_NAMES); do \
		echo "Deleting $$service..."; \
		kubectl delete deployments.apps "$$service"; \
	done
	@echo "Done!"

# delete all deployments, then rebuild and deploy
redeploy: deploy-clean | deploy

##
# Infra
##

# start minikube if it isn't already running
minikube: check-docker
	@echo "Starting minikube with $(MINIKUBE_DRIVER) driver..."
	@if minikube status | grep -q "host: Running"; then \
		echo "Minikube already running."; \
	else \
		minikube start --driver=$(MINIKUBE_DRIVER); \
		echo "Done!"; \
	fi

# stop minikube
minikube-clean:
	@echo "Stopping minikube..."
	@-minikube stop
	@echo "Done!"

# restart minikube
minikube-restart: minikube-clean | minikube

# delete minikube vm
minikube-clean-full: minikube-clean
	@echo "Deleting minikube..."
	@-minikube delete
	@echo "Done!"

# delete minikube vm then start up a new one
minikube-reset: minikube-clean-full | minikube

# just deletes deployments for now
clean: deploy-clean

# deletes minikube and deletes deployments
clean-all: minikube-clean-full deploy-clean

.PHONY: rabbitmq-setup rabbitmq-creds all print-services check-docker build deploy deploy-clean redeploy minikube minikube-clean minikube-restart minikube-clean-full minikube-reset clean clean-all

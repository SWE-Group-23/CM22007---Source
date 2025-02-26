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

# service k8s configs
K8S_CFGS=$(wildcard src/*/*/*.yaml)

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

scylla-creds:
	@echo Username:
	@kubectl get secret dev-db-superuser -o jsonpath='{.data.username}' | base64 --decode 
	@echo
	@echo Password:
	@kubectl get secret dev-db-superuser -o jsonpath='{.data.password}' | base64 --decode
	@echo

pylint:
	@echo "Running pylint..."
	@if ! uv tool run pylint $(shell git ls-files '*.py'); then \
		echo "FAIL WORKFLOW."; \
	else \
		echo "PASS WORKFLOW."; \
	fi

# print all the services in SERVICES and the path to their Dockerfile
print-services:
	@for service in $(SERVICES); do \
		name=$$(basename $$(dirname $$service)); \
		echo "$$name : $$service"; \
	done

print-k8s-cfgs:
	@echo "Service k8s + queues:"
	@for config in $(K8S_CFGS); do \
		name=$$(basename $$(dirname $$config)); \
		echo "$$name : $$config"; \
	done

	@printf "\n\n"
	@echo "Global k8s:"
	@for config in $(wildcard k8s/*); do \
		echo "$$config"; \
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
	@set -e; for service in $(SERVICES); do \
		name=$$(basename $$(dirname $$service)); \
		echo "Building $$name..."; \
		( \
			cd $$(dirname $$service); \
			cp -r ../../shared .; \
			uv lock; \
			minikube image build -t $$name .; \
			rm -r shared/; \
		); \
		echo "Done!"; \
	done

cert-manager:
	@echo "Install cert-manager..."
	@# check if cert manager is already installed
	@if ! kubectl get crd certificates.cert-manager.io &>/dev/null || ! kubectl get deployment -n cert-manager | grep -q 'cert-manager'; then \
		echo "Cert-manager is not fully installed. Installing..."; \
		kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.3.1/cert-manager.yaml; \
	else \
		echo "Cert-manager is already installed. Skipping installation."; \
	fi
	@echo "Waiting for cert-manager to start..."
	@kubectl wait --for condition=established crd/certificates.cert-manager.io crd/issuers.cert-manager.io
	@kubectl -n cert-manager rollout status --timeout=5m deployment.apps/cert-manager-webhook
	@kubectl -n cert-manager rollout status --timeout=5m deployment.apps/cert-manager-cainjector

scylladb-setup: minikube cert-manager
	@# @echo "Installing Prometheus Operator..."
	@#kubectl apply --server-side -f=https://github.com/prometheus-operator/prometheus-operator/releases/latest/download/bundle.yaml
	@echo "Installing Scylla operator..."
	kubectl -n=scylla-operator apply --server-side -f=https://raw.githubusercontent.com/scylladb/scylla-operator/refs/heads/v1.15/deploy/operator.yaml
	@echo "Done!"

scylladb-clean: deploy-clean
	@echo "Deleting ScyllaDB clusters..."
	kubectl delete --namespace=scylla --all scyllaclusters.scylla.scylladb.com
	@echo "Deleting ScyllaDB creds..."
	@# TODO: properly namespace secrets
	kubectl delete secrets dev-db-superuser
	kubectl delete secrets template-user-scylla-creds
	@echo "Done!"

scylladb-clean-full: scylladb-clean
	@echo "Deleting ScyllaDB operators..."
	kubectl delete --namespace=scylla-operator --all deployment
	@echo "Done!"

# installs rabbitmq cluster operator, cert-manager, rabbitmq topology operator, then deploys rabbitmq
rabbitmq-setup: minikube cert-manager
	@echo "Checking rabbitMQ cluster operator..."
	@if ! kubectl get deployment -n rabbitmq-system | grep -q 'rabbitmq-cluster-operator'; then \
		echo "Cluster operator not found. Installing..."; \
		kubectl rabbitmq install-cluster-operator; \
		echo "Done!"; \
	else \
		echo "Cluster operator found!"; \
	fi

	@echo "Checking RabbitMQ resource definitions..."
	@if ! kubectl get crd | grep -q 'rabbitmqclusters.rabbitmq.com'; then \
		echo "CRDs not found. Exiting..."; \
		exit 1; \
	else \
		echo "CRDs found!"; \
	fi

	@echo "Checking RabbitMQ topology operator..."
	@if ! kubectl get deployment -n rabbitmq-system | grep -q 'messaging-topology-operator'; then \
		echo "Topology operator not found. Installing..."; \
		kubectl apply -f https://github.com/rabbitmq/messaging-topology-operator/releases/latest/download/messaging-topology-operator-with-certmanager.yaml; \
		echo "Done!"; \
	else \
		echo "Topology operator found!"; \
	fi
	
	@echo "Deploying rabbitMQ..."
	@kubectl apply -f k8s/rabbit-mq.yaml
	@echo "Done!"

# delete all deployments made in rabbitmq-setup
rabbitmq-clean: deploy-clean
	@echo "Deleting rabbitmq deployments..."
	@kubectl delete -f k8s/rabbit-mq.yaml
	@kubectl delete --namespace=rabbitmq-system --all deployment
	@echo "Deleting cert-manager deployments..."
	@kubectl delete --namespace=cert-manager --all deployment

# sets up valkey if it isn't already installed
valkey-setup: minikube
	@echo "Checking for Valkey operator..."
	@if kubectl get deployment -n valkey-operator-system | grep -q 'valkey-operator-controller-manager'; then \
		echo "Valkey operator found!"; \
	else \
		echo "Installing Valkey operator..."; \
		kubectl apply -f https://github.com/hyperspike/valkey-operator/releases/download/v0.0.57/install.yaml; \
		echo "Done!"; \
	fi

# deletes valkey deployment
valkey-clean:
	@echo "Deleting Valkey operator deployment..."
	@kubectl delete --namespace=valkey-operator-system --all deployment
	@echo "Done!"

# deploys dependencies in parallel
deploy-dependencies: cert-manager
	$(MAKE) -j 4 _deploy-scylladb _deploy-rabbitmq _deploy-valkey _build

_deploy-scylladb:
	$(MAKE) scylladb-setup

_deploy-rabbitmq:
	$(MAKE) rabbitmq-setup

_deploy-valkey:
	$(MAKE) valkey-setup

_build:
	$(MAKE) build

# deploys the database pod
deploy-database: deploy-dependencies
	@echo "Waiting for ScyllaDB to start..."
	@kubectl wait --for condition=established crd/scyllaclusters.scylla.scylladb.com
	@kubectl wait --for condition=established crd/scyllaoperatorconfigs.scylla.scylladb.com
	@kubectl wait --for condition=established crd/nodeconfigs.scylla.scylladb.com
	@kubectl -n scylla-operator rollout status --timeout=5m deployments.apps/scylla-operator
	@kubectl -n scylla-operator rollout status --timeout=5m deployments.apps/webhook-server
	@echo "Deploying database..."
	@kubectl apply -f k8s/scylladb-config.yaml
	@echo "Done!"

# waits for rabbitmq, valkey, and scylladb to start
wait-ready: deploy-dependencies deploy-database
	@printf "Waiting for rabbitMQ to start"
	@until kubectl rabbitmq list | grep -q -E "rabbitmq +True"; do sleep 1; printf "."; done; printf "\n"
	@echo "Waiting for ScyllaDB cluster to start..."
	@kubectl -n scylla wait pod/dev-db-dev-1-dev-1a-0 --for=condition=PodReadyToStartContainers --timeout=5m
	@kubectl -n scylla wait pod/dev-db-dev-1-dev-1a-0 --for=condition=Ready --timeout=10m
	@echo "Waiting for Valkey to start..."
	@kubectl -n valkey-operator-system rollout status --timeout=5m deployments.apps/valkey-operator-controller-manager
	@echo "Done!"

# apply all k8s configs in the k8s/ directory
deploy: minikube | wait-ready
	@echo "Deploying CRDs..."
	@kubectl apply -f k8s/crds/
	@echo "Deploying global configs..."
	@kubectl apply -f k8s/
	@echo "Deploying services to K8s..."
	@-for config in $(K8S_CFGS); do \
		echo "Deploying $$config..."; \
		kubectl apply -f "$$config"; \
	done
	@echo "Done!"

# apply all k8s configs in the k8s/ directory
deploy-unchecked: minikube | build
	@echo "WARNING: You should only use this target if you know all other services are running."
	@echo "Deploying CRDs..."
	@kubectl apply -f k8s/crds/
	@echo "Deploying global configs..."
	@kubectl apply -f k8s/
	@echo "Deploying services to K8s..."
	@-for config in $(K8S_CFGS); do \
		echo "Deploying $$config..."; \
		kubectl apply -f "$$config"; \
	done
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
redeploy-unchecked: deploy-clean | deploy-unchecked

##
# Infra
##

# start minikube if it isn't already running
minikube: check-docker
	@echo "Starting minikube with $(MINIKUBE_DRIVER) driver..."
	@if minikube status | grep -q "host: Running"; then \
		echo "Minikube already running."; \
	else \
		minikube start --driver=$(MINIKUBE_DRIVER) --cpus 2; \
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

# deletes minikube (which should delete all deployments)
clean-all: minikube-clean-full

.PHONY: valkey-clean valkey-setup print-k8s-cfgs scylladb-creds scylladb-clean-full scylladb-clean wait-ready redeploy-unchecked deploy-unchecked scylladb-setup cert-manager rabbitmq-clean rabbitmq-setup rabbitmq-creds all print-services check-docker build deploy deploy-clean redeploy minikube minikube-clean minikube-restart minikube-clean-full minikube-reset clean clean-all

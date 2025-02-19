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
	@kubectl get secret example-db-superuser -o jsonpath='{.data.username}' | base64 --decode 
	@echo
	@echo Password:
	@kubectl get secret example-db-superuser -o jsonpath='{.data.password}' | base64 --decode
	@echo

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
	# TODO: check if it's installed already and skip if it is
	@kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.3.1/cert-manager.yaml

scylladb-setup: minikube cert-manager
	# @echo "Installing Prometheus Operator..."
	#kubectl apply --server-side -f=https://github.com/prometheus-operator/prometheus-operator/releases/latest/download/bundle.yaml
	@echo "Installing Scylla operator..."
	kubectl -n=scylla-operator apply --server-side -f=https://raw.githubusercontent.com/scylladb/scylla-operator/refs/heads/v1.15/deploy/operator.yaml
	@echo "Done!"

scylladb-clean: deploy-clean
	@echo "Deleting ScyllaDB clusters..."
	kubectl delete --namespace=scylla --all scyllaclusters.scylla.scylladb.com
	@echo "Done!"

scylladb-clean-full: scylladb-clean
	@echo "Deleting ScyllaDB operators..."
	kubectl delete --namespace=scylla-operator --all deployment
	@echo "Done!"

# installs rabbitmq cluster operator, cert-manager, rabbitmq topology operator, then deploys rabbitmq
rabbitmq-setup: minikube cert-manager
	@echo "Installing rabbitMQ cluster operator..."
	# TODO: check if it's installed already and skip if it is
	@kubectl rabbitmq install-cluster-operator
	@echo "Getting rabbitMQ resource definitions..."
	# TODO: check if this is already done and skip if it is
	@kubectl get customresourcedefinitions.apiextensions.k8s.io
	@printf "Waiting for cert-manager"
	# TODO: make this not use dry run if possible
	@until kubectl --dry-run=server apply -f https://github.com/rabbitmq/messaging-topology-operator/releases/latest/download/messaging-topology-operator-with-certmanager.yaml &> /dev/null; do sleep 1; printf "."; done; printf "\n"
	@echo "Installing rabbitMQ Topology operator..."
	# TODO: check if it's installed already and skip if it is
	@kubectl apply -f https://github.com/rabbitmq/messaging-topology-operator/releases/latest/download/messaging-topology-operator-with-certmanager.yaml
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

wait-ready: rabbitmq-setup scylladb-setup
	@printf "Waiting for rabbitMQ to start"
	@until kubectl rabbitmq list | grep -q -E "rabbitmq +True"; do sleep 1; printf "."; done; printf "\n"

# apply all k8s configs in the k8s/ directory
deploy: minikube | build wait-ready
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

.PHONY: print-k8s-cfgs scylladb-creds scylladb-clean-full scylladb-clean wait-ready redeploy-unchecked deploy-unchecked scylladb-setup cert-manager rabbitmq-clean rabbitmq-setup rabbitmq-creds all print-services check-docker build deploy deploy-clean redeploy minikube minikube-clean minikube-restart minikube-clean-full minikube-reset clean clean-all

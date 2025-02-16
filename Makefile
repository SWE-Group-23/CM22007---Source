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
			docker build -t localhost:`(minikube addons enable registry | grep "uses port" | awk '{print $$9} END {exit $$9 == ""}' || echo 5000)`/$$name .; \
			docker push localhost:`(minikube addons enable registry | grep "uses port 2" | awk '{print $$9} END {exit $$9 == ""}' || echo 5000)`/$$name; \
		); \
		echo "Done!"; \
	done

cert-manager:
	@echo "Install cert-manager..."
	# TODO: check if it's installed already and skip if it is
	@kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.3.1/cert-manager.yaml

scylladb-setup: minikube cert-manager
	@echo "Installing Prometheus Operator..."
	#kubectl apply --server-side -f=https://github.com/prometheus-operator/prometheus-operator/releases/latest/download/bundle.yaml
	kubectl -n=scylla-operator apply --server-side -f=https://raw.githubusercontent.com/scylladb/scylla-operator/refs/heads/v1.15/deploy/operator.yaml

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
	@printf "Waiting for rabbitMQ to start"
	@until kubectl rabbitmq list | grep -q -E "rabbitmq +True"; do sleep 1; printf "."; done; printf "\n"
	@echo "Done!"

# delete all deployments made in rabbitmq-setup
rabbitmq-clean: deploy-clean
	@echo "Deleting rabbitmq deployments..."
	@kubectl delete -f k8s/rabbit-mq.yaml
	@kubectl delete --namespace=rabbitmq-system --all deployment
	@echo "Deleting cert-manager deployments..."
	@kubectl delete --namespace=cert-manager --all deployment

# apply all k8s configs in the k8s/ directory
deploy: minikube | build rabbitmq-setup scylladb-setup
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
		minikube start --driver=$(MINIKUBE_DRIVER) --cpus 2 --memory 2G; \
		minikube addons enable registry; \
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

.PHONY: scylladb-setup cert-manager rabbitmq-clean rabbitmq-setup rabbitmq-creds all print-services check-docker build deploy deploy-clean redeploy minikube minikube-clean minikube-restart minikube-clean-full minikube-reset clean clean-all

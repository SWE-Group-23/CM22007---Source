DOCKER_RUNTIME=docker

SERVICES=$(wildcard src/*/*/Dockerfile)
SERVICE_NAMES=$(notdir $(patsubst %/Dockerfile, %, $(SERVICES)))

all: deploy

##
# Util
##

print-services:
	@for service in $(SERVICES); do \
		name=$$(basename $$(dirname $$service)); \
		echo "$$name : $$service"; \
	done

check-docker:
	@if ! $(DOCKER_RUNTIME) info > /dev/null 2>&1; then \
		echo "Docker isn't running, please start the docker daemon (using systemd: \`sudo systemctl start $(DOCKER_RUNTIME)\`)."; \
		exit 1; \
	fi

##
# Build + Deployment
##

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

deploy: build minikube
	@echo "Deploying services to K8s..."
	@kubectl apply -f k8s/
	@echo "Done!"

deploy-clean:
	@echo "Deleting deployments..."
	@-for service in $(SERVICE_NAMES); do \
		echo "Deleting $$service..."; \
		kubectl delete deployments.apps "$$service"; \
	done
	@echo "Done!"

redeploy: deploy-clean | deploy

##
# Infra
##

minikube: check-docker
	@echo "Starting minikube..."
	@if minikube status | grep -q "host: Running"; then \
		echo "Minikube already running."; \
	else \
		minikube start --driver=virtualbox; \
		echo "Done!"; \
	fi

minikube-clean:
	@echo "Stopping minikube..."
	@-minikube stop
	@echo "Done!"

minikube-restart: minikube-clean | minikube

minikube-clean-full: minikube-clean
	@echo "Deleting minikube..."
	@-minikube delete
	@echo "Done!"

minikube-reset: minikube-clean-full | minikube

clean: deploy-clean

clean-all: minikube-clean-full deploy-clean

.PHONY: all print-services check-docker build deploy deploy-clean redeploy minikube minikube-clean minikube-restart minikube-clean-full minikube-reset clean clean-all

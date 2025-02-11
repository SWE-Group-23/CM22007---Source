REGISTRY=localhost:5000

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

##
# Build + Deployment
##

build: registry minikube
	@echo "Building docker images for services..."
	@for service in $(SERVICES); do \
		name=$$(basename $$(dirname $$service)); \
		echo "Building and pushing $$name to local registry..."; \
		(cd $$(dirname $$service); echo "Building..."; docker build -t $(REGISTRY)/$$name .; echo "Pushing..."; docker push $(REGISTRY)/$$name; echo "Loading to minikube..."; minikube image load $(REGISTRY)/$$name;); \
		echo "Done!"; \
	done

deploy: build registry minikube
	@echo "Deploying services to K8s..."
	@kubectl apply -f k8s/
	@echo "Done!"

deploy-clean:
	@echo "Deleting deployments..."
	-@for service in $(SERVICE_NAMES); do \
		echo "Deleting $$service..."; \
		kubectl delete deployments.apps "$$service"; \
	done
	@echo "Done!"

##
# Infra
##

minikube: registry
	@echo "Starting minikube..."
	@if minikube status | grep -q "host: Running"; then \
		echo "Minikube already running."; \
	else \
		minikube start; \
		echo "Done!"; \
	fi

minikube-clean:
	@echo "Stopping minikube..."
	@minikube stop
	@echo "Done!"

registry:
	@if docker ps --filter "name=registry" | grep -q registry; then \
		echo "Local docker registry already running."; \
	else \
		echo "Starting local docker registry at $(REGISTRY)..."; \
		(docker start registry && echo "Restarted registry...") || (docker run -d -p 5000:5000 --name registry registry:2.8.3 && echo "Started new registry..."); \
		echo "Done!"; \
	fi

registry-clean:
	@echo "Killing registry container..."
	@-docker kill registry
	@echo "Done!"

registry-clean-full: registry-clean
	@echo "Removing registry container..."
	@docker container rm registry
	@echo "Done!"

clean: deploy-clean registry-clean

clean-all: registry-clean-full deploy-clean minikube-clean

.PHONY: clean registry-clean minikube-clean deploy-clean minikube registry build deploy print-services all

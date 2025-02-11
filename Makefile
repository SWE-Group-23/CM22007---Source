#
# Subsystems
##

## Template
example-service: registry
	(cd src/template/example-service/; docker build -t localhost:5000/example-service:1.0.0 .; docker push localhost:5000/example-service:1.0.0)

##
# Infra
##
minikube: registry
	minikube start

minikube-clean:
	minikube stop

registry:
	docker run -d -p 5000:5000 --name registry registry:2.8.3

registry-clean:
	docker kill registry
	docker container rm registry

clean: minikube-clean registry-clean

.PHONY: registry cleanup minikube minikube-cleanup registry-cleanup

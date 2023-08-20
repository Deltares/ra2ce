#!/usr/bin/bash

sudo dnf install -y https://storage.googleapis.com/minikube/releases/latest/minikube-latest.x86_64.rpm
minikube start --kubernetes-version=v1.27.4

# Enable ingress in minikube

minikube addons enable ingress

# Enable and configure metallb 

minikube addons enable metallb
echo "The IP address of this minikube node is: $(minikube ip)"
kubectl apply -f /usr/share/doc/metallb/config.yaml

exit

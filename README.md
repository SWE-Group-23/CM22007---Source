# CM22007---Source
Source code for the project. CI/CD

## Requirements
You will need to run this on a Linux machine as GNU make is a requirement.
- `make`
- `uv`
- `minikube`
- `kubectl`
    - Recommended to add completions to `.bashrc`, `.zshrc`, etc. depending on shell:
    - For example, with `zsh`: `echo "source <(kubectl completion zsh)" >> .zshrc`
- `docker`
- `docker-buildx`
- docker runtime (e.g. `docker`, `colima`)
- `krew`
    - Requires adding something to `PATH`.
    - For example, with `zsh`: `echo "export PATH=\"\${KREW_ROOT:-\$HOME/.krew}/bin:\$PATH\"" >> .zshrc`
- rabbitmq krew plugin
    - To install: `kubectl krew install rabbitmq`
- wait-job krew plugin
    - To install: `kubectl krew install wait-job`

## Recommended Tools
For managing and viewing the status of Kubernetes objects, `k9s` is a great tool.
`k9s` can be installed using `brew` on mac and `wget https://github.com/derailed/k9s/releases/download/v0.40.5/k9s_linux_amd64.deb; sudo apt install ./k9s_linux_amd64.deb; rm k9s_linux_amd64.deb` on ubuntu

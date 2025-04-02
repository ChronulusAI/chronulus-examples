#!/bin/bash

mkdir -p /tmp/pip

CODEARTIFACT_AUTH_TOKEN=`aws codeartifact get-authorization-token --profile Artifacts --domain ${CA_DOMAIN_NAME} --domain-owner ${CA_AWS_ACCOUNT_ID}  --region ${AWS_REGION} --query authorizationToken --output text`

echo "[global]
index-url = https://aws:${CODEARTIFACT_AUTH_TOKEN}@${CA_DOMAIN_NAME}-${CA_AWS_ACCOUNT_ID}.d.codeartifact.${AWS_REGION}.amazonaws.com/pypi/${CA_REPOSITORY_NAME}/simple/
extra-index-url = https://pypi.org/simple/
" > $PIP_CONFIG_FILE
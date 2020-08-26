

#!/bin/bash
mkdir -p netpalm/backend/core/security/cert/tls
openssl genrsa -out netpalm/backend/core/security/cert/tls/ca.key 4096
openssl req \
     -x509 -new -nodes -sha256 \
     -key netpalm/backend/core/security/cert/tls/ca.key \
     -days 3650 \
     -subj '/O=Redis Test/CN=Certificate Authority' \
     -out netpalm/backend/core/security/cert/tls/ca.crt
 openssl genrsa -out netpalm/backend/core/security/cert/tls/redis.key 2048
 openssl req \
     -new -sha256 \
     -key netpalm/backend/core/security/cert/tls/redis.key \
    -subj '/O=Redis Test/CN=Server' | \
     openssl x509 \
         -req -sha256 \
         -CA netpalm/backend/core/security/cert/tls/ca.crt \
         -CAkey netpalm/backend/core/security/cert/tls/ca.key \
         -CAserial netpalm/backend/core/security/cert/tls/ca.txt \
         -CAcreateserial \
         -days 365 \
         -out netpalm/backend/core/security/cert/tls/redis.crt
 openssl dhparam -out netpalm/backend/core/security/cert/tls/redis.dh 2048
#!/usr/bin/env bash
set -euo pipefail

output_dir="${1:-.local/worker/pki}"
umask 077
mkdir -p "$output_dir"

for command_name in openssl; do
  command -v "$command_name" >/dev/null || { printf '%s is required\n' "$command_name" >&2; exit 1; }
done

openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$output_dir/ca.key"
openssl req -x509 -new -sha256 -days 365 -key "$output_dir/ca.key" \
  -subj "/CN=assessment-worker-development-ca" -out "$output_dir/ca.pem"

openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$output_dir/server.key"
openssl req -new -sha256 -key "$output_dir/server.key" -subj "/CN=127.0.0.1" -out "$output_dir/server.csr"
printf '%s\n' 'subjectAltName=IP:127.0.0.1' 'extendedKeyUsage=serverAuth' > "$output_dir/server.ext"
openssl x509 -req -sha256 -days 90 -in "$output_dir/server.csr" -CA "$output_dir/ca.pem" \
  -CAkey "$output_dir/ca.key" -CAcreateserial -extfile "$output_dir/server.ext" -out "$output_dir/server.pem"

openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$output_dir/client.key"
openssl req -new -sha256 -key "$output_dir/client.key" -subj "/CN=assessment-api" -out "$output_dir/client.csr"
printf '%s\n' 'extendedKeyUsage=clientAuth' > "$output_dir/client.ext"
openssl x509 -req -sha256 -days 90 -in "$output_dir/client.csr" -CA "$output_dir/ca.pem" \
  -CAkey "$output_dir/ca.key" -CAcreateserial -extfile "$output_dir/client.ext" -out "$output_dir/client.pem"

rm -f "$output_dir/server.csr" "$output_dir/client.csr" "$output_dir/server.ext" "$output_dir/client.ext" "$output_dir/ca.srl"
chmod 0600 "$output_dir"/*.key
chmod 0644 "$output_dir"/*.pem
printf 'Development certificates written to %s; keep private keys outside source control.\n' "$output_dir"

#!/usr/bin/env bash
# Fetch the Debezium Postgres connector plugin from Maven Central and verify Maven's published SHA-1.
# The plugin is mounted into a stock apache/kafka Connect worker (compose.yaml); nothing is committed.
set -euo pipefail
VERSION="${DEBEZIUM_VERSION:-3.2.0.Final}"
SHA1="${DEBEZIUM_SHA1:-93b66536fa223280ecd8ddee132be0b4d7acc06b}"
URL="https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/${VERSION}/debezium-connector-postgres-${VERSION}-plugin.tar.gz"
cd "$(dirname "$0")"
mkdir -p plugins
curl -fsSL "$URL" -o plugins/debezium.tgz
echo "${SHA1}  plugins/debezium.tgz" | sha1sum -c -
tar xzf plugins/debezium.tgz -C plugins && rm plugins/debezium.tgz
echo "debezium-connector-postgres ${VERSION} in $(pwd)/plugins"

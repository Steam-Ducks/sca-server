#!/bin/sh
set -e
sed \
  -e "s|\${GF_CLOUD_METRICS_URL}|${GF_CLOUD_METRICS_URL}|g" \
  -e "s|\${GF_CLOUD_METRICS_USER}|${GF_CLOUD_METRICS_USER}|g" \
  -e "s|\${GF_CLOUD_METRICS_API_KEY}|${GF_CLOUD_METRICS_API_KEY}|g" \
  /etc/prometheus/prometheus.prod.tmpl > /tmp/prometheus.runtime.yml
exec /bin/prometheus "$@"

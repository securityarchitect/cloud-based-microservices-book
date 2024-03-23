docker run -p 9090:9090 --network=host -v /mnt/arshdeep/WORK/arshdeep/MyCoding/microservices-book/microservices-ecommerce-dynamodb-s3-prometheus-grafana/frontend/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

docker volume create grafana-storage
docker run -p 3000:3000 -d --network=host --name=grafana --volume grafana-storage:/var/lib/grafana  grafana/grafana

rate(request_count_total[5m])
rate(add_to_cart_total[5m])
histogram_quantile(0.95, rate(request_latency_seconds_bucket[5m]))
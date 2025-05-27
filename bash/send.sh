#!/bin/bash

ORG="WIE"
BUCKET="omvormer_bucket"
TOKEN="2hMjwsBQ8KZFOJhswwCkY3y4sGWyiJLpZSMWNgO07MJ-pU5sljMBLqsLKZM8WQVrfYizasKpNtZHUJ1I-nq9tA=="
URL="https://eu-central-1-1.aws.cloud2.influxdata.com/api/v2/write?org=$ORG&bucket=$BUCKET&precision=s"

# Add all measurement names
FIELDS=("vac-middle" "vac-bottom" "amp-top" "amp-middle" "amp-bottom" "kw-top" "kw-middle" "kw-bottom" "temp" "amp-input" "dc-voltage")

while true; do
    DATA=""

    for FIELD in "${FIELDS[@]}"; do
        case $FIELD in
            vac-*) VALUE=$((RANDOM % 20 + 970)) ;;  # 970–989
            amp-*) VALUE=$((RANDOM % 50 + 200)) ;;  # 200–249
            kw-*) VALUE=$(awk -v min=195 -v max=205 'BEGIN{srand(); printf "%.1f", min+rand()*(max-min)}') ;; # 195.0–205.0
            temp) VALUE=$((RANDOM % 100 + 1)) ;;    # 1–100
            amp-input) VALUE=$(awk 'BEGIN{srand(); printf "%.2f", 0.2 + rand() * (10.0 - 0.2)}') ;; # 0.2–10.0
            dc-voltage) VALUE=$(awk 'BEGIN{srand(); printf "%.2f", 4.9 + rand() * (5.3 - 4.9)}') ;; # 4.9–5.3
            *) VALUE=0 ;;
        esac
        DATA+="omvormer,name=$FIELD value=$VALUE\n"
    done

    # Random ON/OFF status string
    STATUS_VALUE=$( ((RANDOM % 2)) && echo "ON" || echo "OFF" )
    DATA+="status,name=status value=\"$STATUS_VALUE\"\n"

    # Send to InfluxDB
    echo -e "$DATA" | curl -s -XPOST "$URL" \
      -H "Authorization: Token $TOKEN" \
      -H "Content-Type: text/plain" \
      --data-binary @-

    echo "✅ Sent data at $(date)"
    sleep 2
done


#!/bin/sh

tasks=(
    awral_sim
    catchment_deciles
    catchment_extraction
    day_deciles
    day_to_month
    latest_multi_month
    month_deciles
    month_to_date_deciles
    month_to_year
    reg_user_products
    rootzone_soil_moisture
    scale_soil_moisture
    update_climate
    update_website_prod
    update_wind
    year_deciles
    year_to_date_deciles
)
outfile=gen-suite-runtime.rc

echo '[runtime]' > $outfile

for i in "${tasks[@]}"; do
cat <<EOF >> $outfile
    [[${i}]]
        script = "sleep 5; echo running ${i}..."
EOF
done


set -euo pipefail
IFS=$'\n\t'



DUMP_DIR="dump-data"
APPS=("measurements" "submeasurements" "flags" "fp_tables" "sites" "asns")
DATE=`date +%Y-%m-%d`
mkdir $DUMP_DIR/$DATE
DUMP_LOCATION=$DUMP_DIR/$DATE

for app in "${APPS[@]}"; do
    python manage.py dumpdata $app > $DUMP_LOCATION/dump-$app.json
done
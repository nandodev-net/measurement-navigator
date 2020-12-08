-- This query can update the previous_counter for dns submeasurements
WITH resolvers AS (
    SELECT 
        dns.id AS dns_id, 
        cast(rms.test_keys->>'client_resolver' AS inet) AS client_resolver
    FROM submeasurements_dns dns 
        JOIN measurements_measurement ms ON dns.measurement_id=ms.id
        JOIN measurements_rawmeasurement rms ON rms.id=ms.raw_measurement_id
)
UPDATE submeasurements_dns dns
SET client_resolver = resolvers.client_resolver
FROM resolvers
WHERE dns.id = resolvers.dns_id


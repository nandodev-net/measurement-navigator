We tried to make the database model for the ooni fast path based on
the given model from Federico:
https://github.com/ooni/pipeline/blob/master/af/oometa/018-fastpath.install.sql
but it turns out that this is not possible since such data doesn't comes with 
the format specified in that link. So we adapted our table so it matches with the actual response
given by the ooni api which is:
anomaly: bool
confirmed: bool
failure: bool
input: string
measurement_id: string
measurement_start_time: datetime
measurement_url: url field
probe_asn: string
probe_cc: 2 chars string
report_id: a veri long id
scores: a json
test_name: a string (contained in an enum)
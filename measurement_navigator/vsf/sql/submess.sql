SELECT  
                submeasurements_dns.id,  
                previous_counter,  
                rms.measurement_start_time,  
                dense_rank() OVER (order by rms.input) as group_id  

                FROM  
                submeasurements_dns JOIN measurements_measurement ms ON ms.id = submeasurements_dns.measurement_id  
                                        JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id  
                                        JOIN flags_flag f ON f.id = submeasurements_dns.flag_id  
                WHERE  
                f.flag<>'ok'  
                ORDER BY rms.input, rms.measurement_start_time, previous_counter; 
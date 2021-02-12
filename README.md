# Fast Path navigator

This measurement navigator version will periodically search for measurements in the ooni api. These measurements may or may not be complete, so there's a measurement collector for
incomplete measurement. You can see details for every complete measurement, filter them and searching for patterns.  

The system allows for quickly checking measurements that are available in the ooni fastpath, so you can find information really fast even if it's not still complete.

## Exampes
### Main Menu
![Main Menu](./images/fp_navigator1.png?raw=true "Main Menu")

### Filtering by input
![Filter by input](./images/fp_navigator2.png?raw=true "Input filter")

### Details
![Details](./images/fp_navigator3.png?raw=true "Measurement Details")

## Asynchronous process:
Our current setup implements asynchronous process through Celery, you can find a full installation guide for this project [here](https://github.com/VEinteligente/measurement-navigator/wiki/Measurement-Navigator-Installation-on-Server)



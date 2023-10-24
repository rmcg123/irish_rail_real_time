## Irish Rail Realtime Train Visualisation

A small project to visualise train movements over a specified time window.

The data for this project is principally obtained within the script from the Irish Rail
API.

This data is supplemented with two GeoJSON files from Ordnance Survey Ireland:
1. Rail Network GeoJSON available [here](https://data-osi.opendata.arcgis.com/datasets/cef400fb8edb496886e3dab535ef1344_0/about)
2. Rail Stations GeoJSON available [here](https://data.gov.ie/dataset/railway-stations-osi-national-250k-map-of-ireland4?package_type=dataset)

If you wish to run this yourself then you should download these and save them
into a `railway_network` folder within the `data` folder.

For this project I have used an anaconda environment running python `3.11`.
The project requirements are in the `requirements.in` file, to install these
run: `pip install -r requirements.in`. I have used the root of the directory as
the project working directory.
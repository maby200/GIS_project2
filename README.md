# Project 2
> The final tool

This project involves the creation of a python script for ArcGIS PRO. This tool allows the user to load a CSV file with the points to be sampled. The raster to be sampled needs to be a DEM. In this tool, this elevation model is the `USGS/3DEP/10m`, an elevation model that cover all the United States including Alaska and Hawaii.

## Methodology
1. Before creating the script tool, the smapling points csv file was inspected. It was found that the coordinates were in meters. Also, according to the data description given by the course instructor these points' coordinates were taken from the same DEM model previously mentioned, i.e. the coordinates have the same reference system, which Well Known ID (WKID) is `32119` with name: `NAD83 / North Carolina`.
2. The Earth ENgine (`ee`) package was used to create a list of points. Then the `ee.FeatureCOllection` function was used to use these points.
![Sample points](/img/sampling_points_raw.png "EE-readable converted points")
3. Using the previous points, the elevation was sampled from the DEM.

- Before sampling the elevation
```python
    {'type': 'FeatureCollection',
    'columns': {'system:index': 'String'},
    'features': [{'type': 'Feature',
    'geometry': {'crs': {'type': 'name', 'properties': {'name': 'EPSG:32119'}},
        'type': 'Point',
        'coordinates': [699102.8877924071, 186780.4458126684]},
    'id': '0',
    'properties': {}},
    {...}
    ]
    }
```
- After sampling elevation. NOTICE THE NEW VALUE AT `elevation`.
```python
    {'type': 'FeatureCollection',
    'columns': {},
    'properties': {'band_order': ['elevation']},
    'features': [{'type': 'Feature',
    'geometry': {'geodesic': False,
        'type': 'Point',
        'coordinates': [-78.01426489169957, 35.429736096570515]},
    'id': '0_0',
    'properties': {'elevation': 22.24553871154785}},
    {...}
    ]
    }
```

Nonetheless, these values are not ready to be used in ArcGIS or QGIS yet. These have to be converted to shapefile, and for that different tools can be used. In this project, the `arcpy` package was used.

4. For this step, the `arcpy.management.CreateFeatureClass()` function was used to create an empty shapefile.
![Creatingempty shapefile](/img/arcgis_shp_raw.png "Empty shapefile created")
5. The `arcpy.management.AddField` was used to insert the fields (headers) to the shapefile
![Inserting fields](/img/arcgis_shp_fieldElevation.png "Inserting fields to shapefile")
6. Finally, the `arcpy.da.InsertCursor` was used to insert both the point and its sampled elevation.
![Inserting elevation values](/img/arcgis_shp_elevationValues.png "Inserting elevation values")

### Using the Script Through the GUI in ArcGIS Pro
![ArcGIS GUI Script tool](/img/arcgisGUI.png "Using ArcGIS Pro GUI")

### The code

```python
import arcpy
import pandas as pd
import ee
import os

def getElevation(workspace, csv_file_name, output_name, output_subfolder='', x_name='X', y_name='Y', spatial_reference=4326, scale=10):
    fullpath_csv_file       = os.path.join(workspace,csv_file_name)
    boundary_table          = pd.read_csv(fullpath_csv_file)
    dem                     = ee.Image('USGS/3DEP/10m')
    geometries              = [ee.Geometry.Point([x, y], f'EPSG:{spatial_reference}') for x, y in zip(boundary_table[x_name], boundary_table[y_name])]
    boundary_fc             = ee.FeatureCollection(geometries)
    boundary_origin_info    = boundary_fc.getInfo()
    sampled_boundary_fc     = dem.sampleRegions(collection=boundary_fc,scale=scale, geometries=True)
    sampled_info            = sampled_boundary_fc.getInfo()
    output_path_subfolder   = os.path.join(workspace,output_subfolder)
    boundary_fc_name        = os.path.join(workspace, output_subfolder, output_name)
    
    for idx, item in enumerate(boundary_origin_info['features']):
        item['properties']  = sampled_info['features'][idx]['properties']
    
    if arcpy.Exists(boundary_fc_name):
        arcpy.management.Delete(boundary_fc_name)
        
    # create Feature class (layer for the points wth elevation info)
    arcpy.management.CreateFeatureclass(output_path_subfolder, output_name, geometry_type='POINT', spatial_reference=spatial_reference)
    # add new field to this feature class
    arcpy.management.AddField(boundary_fc_name, 'Elevation', field_type='FLOAT')
    
    with arcpy.da.InsertCursor(boundary_fc_name, ['SHAPE@','Elevation']) as cursor:
        for ft in boundary_origin_info['features']:
            coordinates = ft['geometry']['coordinates']
            point       = arcpy.PointGeometry(arcpy.Point(coordinates[0], coordinates[1]),spatial_reference=spatial_reference)
            elevation   = ft['properties']['elevation']
            cursor.insertRow([point,elevation])

def main():
    try:
        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()
        
    workspace           = r'C:\Users\mgavil3\Box\CursosLSU\GISProgramming4057\Projects\P2'
    csv_file            = 'boundary.csv'
    output_name         = 'point_elev.shp'
    output_subfolder    = 'output'
    spatial_reference   = 32119
    
    getElevation(workspace, csv_file, output_name, output_subfolder,spatial_reference=spatial_reference)

if __name__ == "__main__":
    main()
```
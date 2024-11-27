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
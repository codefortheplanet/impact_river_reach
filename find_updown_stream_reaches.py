# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 10:16:17 2020

@author: FY
"""

#Loop through the gauge points and check their attributes 
import arcpy
import os
import numpy as np
import csv
import argparse
arcpy.env.overwriteOutput = True

def search_reach1(upstreamID,reachlength1,upstreamarea,reachfeaturefile):
    upID=[]
    upstreamarea=[upstreamarea,upstreamarea]
    while reachlength1<=10 and (upstreamarea[-1]>=upstreamarea[-2]*0.5) and len(upstreamID)!=0:
        uplength1,uplandarea1,upreachid1,selectedid1=up_search(reachfeaturefile,upstreamID,upstreamarea)
        if uplength1==[]:
            reachlength1+=0
        else:
            reachlength1+=uplength1            
        upstreamarea.append(uplandarea1)
        upID.append(selectedid1)
        upstreamID=upreachid1
    return (upID)

def search_reach2(downstreamID,reachlength2,upstreamarea,reachfeaturefile):
    downID=[]
    downlength2,uplandarea2,downreachid2,selectedid2=down_search(reachfeaturefile,downstreamID)
    upstreamarea=[upstreamarea,uplandarea2]

    while reachlength2<=10 and (upstreamarea[-1]<=upstreamarea[-2]*1.5) and len(downstreamID)!=0 and downstreamID!=[0]:
        downlength2,uplandarea2,downreachid2,selectedid2=down_search(reachfeaturefile,downstreamID)
        if downlength2==[]:
            reachlength2+=0
        else:
            reachlength2+=downlength2
        upstreamarea.append(uplandarea2)
        downID.append(selectedid2)
        downstreamID=[downreachid2]
    return (downID)
    
        
def up_search(reachfeaturefile,upstreamID,upstreamarea):         
    uplength=[]
    uplandarea=[]
    upreachid=[]
    compare=[]
    upreachid_str=[]
    if len(upstreamID)!=0:
        arcpy.MakeFeatureLayer_management(reachfeaturefile,"reach_lyr")
        field = arcpy.AddFieldDelimiters("reach_lyr", "NOID")
        for i in upstreamID:
            selectionup = '{field} = {val}'.format(field=field, val=i)
            up=arcpy.SelectLayerByAttribute_management("reach_lyr", "NEW_SELECTION", selectionup)
            with arcpy.da.SearchCursor(up, ['LENGTH_KM','UPLAND_SKM','NUOID']) as cursor:
                for row in cursor:
                    uplength.append(row[0])
                    uplandarea.append(row[1])
                    upreachid.append(row[2]) 
        if uplength!=[]:
            for j in uplandarea:
                compare.append(abs(j-upstreamarea[-1]))
            index = [i for i, j in enumerate(compare) if j == min(compare)][0]
            uplength=uplength[index]
            uplandarea=uplandarea[index]
            upreachid=upreachid[index]
            selectedid=upstreamID[index]
            upreachid_str=upreachid.split("_")
        if len(upreachid_str)>1:
            upreachid_int=[int(i) for i in upreachid_str]
        else:
            upreachid_int=[]
            selectedid=[]
    else:
        selectedid=[]
    arcpy.Delete_management("reach_lyr")
    return (uplength,uplandarea,upreachid_int,selectedid)

def down_search(reachfeaturefile,downstreamID):         
    downlength=[]
    uplandarea=[]
    downreachid=[]
    if len(downstreamID)!=0:
        arcpy.MakeFeatureLayer_management(reachfeaturefile,"reach_lyr")
        field = arcpy.AddFieldDelimiters("reach_lyr", "NOID")
        selectiondown = '{field} = {val}'.format(field=field, val=downstreamID[0])
        
        down=arcpy.SelectLayerByAttribute_management("reach_lyr", "NEW_SELECTION", selectiondown)
        with arcpy.da.SearchCursor(down, ['LENGTH_KM','UPLAND_SKM','NDOID']) as cursor:
            for row in cursor:
                downlength=row[0]
                uplandarea=row[1]
                downreachid=row[2]
        selectedid=downstreamID[0]
    else:
        selectedid=[]
    arcpy.Delete_management("reach_lyr")
    return (downlength,uplandarea,downreachid,selectedid)

def proclines(OID,currentreach,pointpath,reachfeaturefile,upreaches,downreaches,centerlinepath):
    arcpy.MakeFeatureLayer_management(reachfeaturefile,"reach_lyr")
    upreaches = list(filter(None, upreaches))
    downreaches = list(filter(None, downreaches))    
    upreaches.extend(downreaches)
    upreaches.append(currentreach)
    field = arcpy.AddFieldDelimiters("reach_lyr", "NOID")
    unsplitfile=os.path.join("in_memory","unsplit_"+os.path.basename(reachfeaturefile)+str(OID).zfill(4))
    outpointfile_unsort=os.path.join("in_memory","unsort_"+os.path.basename(reachfeaturefile)+str(OID).zfill(4))
    outpointfile_sort=os.path.join(pointpath,os.path.basename(reachfeaturefile)+str(OID).zfill(4)+".shp")
    centerlinefile="centerline_"+os.path.basename(reachfeaturefile)+str(OID).zfill(4)
    bufferfile="in_memory/buffer"
    for i in upreaches:
        selection = '{field} = {val}'.format(field=field, val=i)
        updown=arcpy.SelectLayerByAttribute_management("reach_lyr", "ADD_TO_SELECTION", selection)
                                   
    arcpy.FeatureClassToFeatureClass_conversion (updown, "in_memory", centerlinefile)

    arcpy.UnsplitLine_management(in_features=os.path.join("in_memory", centerlinefile), out_feature_class=unsplitfile,
                                 dissolve_field="", statistics_fields="")

    arcpy.GeneratePointsAlongLines_management(Input_Features=unsplitfile,
                                          Output_Feature_Class=outpointfile_unsort,
                                          Point_Placement="DISTANCE", Distance="100 Meters", Percentage="", Include_End_Points="END_POINTS")
    arcpy.CalculateField_management(in_table=outpointfile_unsort, field="ORIG_FID", expression="!OID!", expression_type="PYTHON_9.3", code_block="")

    arcpy.MakeFeatureLayer_management(outpointfile_unsort,"unsortedpoints")
    arcpy.MakeFeatureLayer_management(os.path.join("in_memory", centerlinefile),"centerline")
    arcpy.SelectLayerByAttribute_management(in_layer_or_view="unsortedpoints", selection_type="NEW_SELECTION", where_clause='"ORIG_FID" =1')
    arcpy.Buffer_analysis(in_features="unsortedpoints", out_feature_class=bufferfile,
                          buffer_distance_or_field="10 Meters", line_side="FULL",
                          line_end_type="ROUND", dissolve_option="NONE", dissolve_field="", method="GEODESIC")

    min_value = arcpy.da.SearchCursor(os.path.join("in_memory", centerlinefile), "UPLAND_SKM", "{} IS NOT NULL".format("UPLAND_SKM"),
                                      sql_clause = (None, "ORDER BY {} ASC".format("UPLAND_SKM"))).next()[0]
    #print (min_value)
    arcpy.SelectLayerByLocation_management(in_layer="centerline", overlap_type="INTERSECT",
                                           select_features=bufferfile, search_distance="30 Meters",
                                           selection_type="NEW_SELECTION", invert_spatial_relationship="NOT_INVERT")
    selected_value = arcpy.da.SearchCursor("centerline", "UPLAND_SKM", "{} IS NOT NULL".format("UPLAND_SKM")).next()[0]
    if min_value == selected_value:
        arcpy.Sort_management(in_dataset=outpointfile_unsort, out_dataset=outpointfile_sort,
                              sort_field=[["ORIG_FID", "ASCENDING"]])
    else:
        arcpy.Sort_management(in_dataset=outpointfile_unsort, out_dataset=outpointfile_sort,
                              sort_field=[["ORIG_FID", "DESCENDING"]])  
    
    arcpy.CopyFeatures_management (os.path.join("in_memory", centerlinefile), os.path.join(centerlinepath, centerlinefile+".shp"))
    arcpy.Delete_management("reach_lyr")
    arcpy.Delete_management("unsortedpoints")
    arcpy.Delete_management("centerline")
    arcpy.Delete_management("in_memory/buffer")
    arcpy.Delete_management(outpointfile_unsort)
    arcpy.Delete_management(unsplitfile)
    arcpy.Delete_management(os.path.join("in_memory", centerlinefile))
                                     
    return (upreaches)

if __name__ == "__main__":
        
    featureclass="D:/process/process.gdb/all_arctic_gage"
    field=['NUOID','NDOID','LENGTH_KM','UPLAND_SKM','NOID','id','REACH_ID']
    reachpath="D:/process/FFR_river_network.gdb"
    pointpath="D:/process/gaugedataset_points_arcitc_new"
    centerlinepath="D:process/gaugedataset_centerline_arctic_new"
    ap=argparse.ArgumentParse()
    ap.add_argument('-s',type=int,required=True)
    ap.add_argument('-e',type=int,required=True)
    opps=ap.parse_args('-s -e'.split())
    start=opps.s
    end=opps.e
    
    with arcpy.da.SearchCursor(featureclass, field) as cursor:
        for row in cursor:
            if row[0] is None:
                upstream_str=['']
            else:
                upstream_str=row[0].split("_")
            downstream=[row[1]]
            length=row[2]
            upstreamland=row[3]
            noid=row[4]
            OID=row[5]
            reach=row[6]
            if reach is not None and OID >=start and OID <end:
                if len(upstream_str)>1:
                    upstream_int=[int(i) for i in upstream_str]
                else:
                    upstream_int=[]
                if downstream==[0]:
                    downstream=[]

                reachfeature=os.path.join(reachpath,"FFR_river_network_v1")
                up_reaches=search_reach1(upstream_int,length,upstreamland,reachfeature)
                down_reaches=search_reach2(downstream,length,upstreamland,reachfeature)

                allreaches=proclines(OID,noid,pointpath,reachfeature,up_reaches,down_reaches,centerlinepath)
                print (OID,allreaches)
                allreaches.insert(0,OID)
                with open("updown_0.csv", "a") as f:
                    writer = csv.writer(f)
                    writer.writerows([allreaches])

        



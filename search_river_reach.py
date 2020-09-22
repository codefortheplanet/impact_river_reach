import arcpy
import os

# Set environment settings
output_dir = "D:/LANL/GIS/compileddata/process"

# The NA layer's data will be saved to the workspace specified here
arcpy.env.workspace = os.path.join(output_dir, "process.gdb")
arcpy.env.overwriteOutput = True

gaugelocations="all_arctic_gage"
neartable="all_arctic_gage_NearTable"

#Create a Near table to select the closest reaches to the gauge points
arcpy.GenerateNearTable_analysis(in_features=gaugelocations, near_features="D:/process/FFR_river_network.gdb/RiverNetwork/FFR_river_network_v1_1",
                                 out_table=neartable,
                                 search_radius="2000 Meters", location="NO_LOCATION", angle="NO_ANGLE", closest="ALL",
                                 closest_count="10", method="GEODESIC")

# Join table for the reach attribute from Grill
arcpy.JoinField_management(in_data=neartable, in_field="NEAR_FID", join_table="D:/process/FFR_river_network.gdb/RiverNetwork/FFR_river_network_v1_1", join_field="OBJECTID", fields="REACH_ID;GOID;NOID;NUOID;NDOID;CON_ID;CONTINENT;COUNTRY;BAS_ID;BAS_NAME;LENGTH_KM;VOLUME_TCM;UPLAND_SKM;DIS_AV_CMS;RIV_ORD;ERO_YLD_TON;HYFALL;BB_ID;BB_NAME;BB_LEN_KM;BB_DIS_ORD;BB_VOL_TCM;BB_OCEAN;INC;DOF;DOR;SED;USE;URB;RDD;FLD;CSI;CSI_D;CSI_FF;CSI_FF1;CSI_FF2;CSI_FFID")

# Join table for the gauge area from MERIT DEM
arcpy.JoinField_management(in_data=neartable, in_field="IN_FID", join_table=gaugelocations, join_field="OBJECTID", fields="provided_drainage_area")

# Add field to store the value whether the basin area from MERIT DEM is within the tolerance range of reach upstream area (+-50%)
arcpy.AddField_management(in_table=neartable, field_name="typercent", field_type="SHORT", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
arcpy.CalculateField_management(in_table=neartable, field="typercent", expression="typercent( !provided_drainage_area!, !UPLAND_SKM!)", expression_type="PYTHON", code_block="def typercent(a,b):\n    if a<=b*1.5 and a>= b*0.5:\n        return 1\n    else:\n        return 0")

arcpy.MakeTableView_management(neartable,"neartable_lyr")
# Select all the near features that are within the tolerance range
neartolerance=arcpy.SelectLayerByAttribute_management(in_layer_or_view="neartable_lyr", selection_type="NEW_SELECTION", where_clause="typercent = 1 ")

# Compute statistics to return the min ranking (top 1) of the near features grouped by each input gauge feature 
arcpy.Statistics_analysis(in_table=neartolerance, out_table="all_arctic_gage_sum", statistics_fields="NEAR_RANK MIN", case_field="IN_FID")

# Join the top 1 ranking to the near table
arcpy.JoinField_management(in_data=neartable, in_field="IN_FID", join_table="all_arctic_gage_sum", join_field="IN_FID", fields="MIN_NEAR_RANK")

arcpy.MakeTableView_management(neartable,"neartable_lyr1")
# Select the top 1 attributes from the near table
top1fromnear=arcpy.SelectLayerByAttribute_management(in_layer_or_view="neartable_lyr1", selection_type="NEW_SELECTION", where_clause="NEAR_RANK = MIN_NEAR_RANK AND typercent = 1")

# Join the attributes back to the gauge location dataset 
arcpy.JoinField_management(in_data=gaugelocations, in_field="OBJECTID", join_table=top1fromnear, join_field="IN_FID", fields="REACH_ID;GOID;NOID;NUOID;NDOID;CON_ID;CONTINENT;COUNTRY;BAS_ID;BAS_NAME;LENGTH_KM;VOLUME_TCM;UPLAND_SKM;DIS_AV_CMS;RIV_ORD;ERO_YLD_TON;HYFALL;BB_ID;BB_NAME;BB_LEN_KM;BB_DIS_ORD;BB_VOL_TCM;BB_OCEAN;INC;DOF;DOR;SED;USE;URB;RDD;FLD;CSI;CSI_D;CSI_FF;CSI_FF1;CSI_FF2;CSI_FFID")

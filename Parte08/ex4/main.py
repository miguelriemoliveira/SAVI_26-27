#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from copy import deepcopy
import json
import math
import random
import signal
import sys
from matplotlib import cm
# from more_itertools import locate
import numpy as np
import open3d as o3d

viewpoint = {
	"class_name" : "ViewTrajectory",
	"interval" : 29,
	"is_loop" : False,
	"trajectory" : 
	[
		{
			"boundingbox_max" : [ 3.6699128165381372, 1.4274178742057815, 3.7624037267893198 ],
			"boundingbox_min" : [ -1.0396580696105957, -1.2458267211914062, -1.3300217410448241 ],
			"field_of_view" : 60.0,
			"front" : [ 0.73162677875171367, -0.56150126217398999, -0.38657287694612946 ],
			"lookat" : [ 1.4984309372276814, 0.1446049959383629, 1.2000099662766757 ],
			"up" : [ -0.63849140422310302, -0.76310638358867988, -0.099986869435024439 ],
			"zoom" : 0.55582366943359363
		}
	],
	"version_major" : 1,
	"version_minor" : 0
}

viewpoint_in_table_frame = {
	"class_name" : "ViewTrajectory",
	"interval" : 29,
	"is_loop" : False,
	"trajectory" : 
	[
		{
			"boundingbox_max" : [ 2.4618751550697415, 2.3941636861889428, 1.0472589686902234 ],
			"boundingbox_min" : [ -2.7440155996177888, -2.5388050867052656, -0.86343573524657757 ],
			"field_of_view" : 60.0,
			"front" : [ 0.51149944822684223, -0.60628663640636382, 0.60892103673521869 ],
			"lookat" : [ 0.78357886742432681, -0.7134470616936508, 0.55028167548461648 ],
			"up" : [ -0.49506686391245669, 0.37127800046831466, 0.7855325878817091 ],
			"zoom" : 0.12670196533203126
		}
	],
	"version_major" : 1,
	"version_minor" : 0
}

def draw3D(entities, window_name, viewpoint):

    o3d.visualization.draw_geometries(entities,
                                      zoom=0.34,
                                       front=viewpoint['trajectory'][0]['front'],
                                       lookat=viewpoint['trajectory'][0]['lookat'],
                                       up=viewpoint['trajectory'][0]['up'],
                                       window_name=window_name)
     
class PlaneSegmentation():

    def __init__(self, point_cloud):
        self.point_cloud = point_cloud
        self.a = None
        self.b = None
        self.c = None
        self.d = None
        self.inliers = None
        self.outliers = None

    def findPlane(self, distance_threshold=0.35, ransac_n=3, num_iterations=100):

        plane_model, inlier_idxs = self.point_cloud.segment_plane(distance_threshold=distance_threshold, 
                                                                  ransac_n=ransac_n, 
                                                                  num_iterations=num_iterations)

        self.a, self.b, self.c, self.d = plane_model # extract plane indices

        self.inliers = self.point_cloud.select_by_index(inlier_idxs, invert=False)
        self.outliers = self.point_cloud.select_by_index(inlier_idxs, invert=True)




# Main function
def main(): # this is our main function
    print("SAVI exercise")

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # initialize argparser
    ap = argparse.ArgumentParser()
    ap.add_argument("-pcf", "--point_cloud_file", type=str, required=False, 
                    default="../scene_point_cloud/scene.ply", help="Path to the point cloud file", )

    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # -------------------------------------------------------------------------
    # Load the point cloud
    # -------------------------------------------------------------------------
    original_pc = o3d.io.read_point_cloud(args['point_cloud_file'])
    print('Point cloud: ' + str(original_pc))

    frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5, origin=np.array([0., 0., 0.]))

    entities = [original_pc, frame]
#     draw3D(entities, "1. Original PC", viewpoint=viewpoint)

    # -------------------------------------------------------------------------
    # Segment the plane
    # -------------------------------------------------------------------------
    floor_segmentor = PlaneSegmentation(original_pc)
    floor_segmentor.findPlane(distance_threshold=0.03, ransac_n=3, num_iterations=1000)

    floor_pc = floor_segmentor.inliers
    floor_pc.paint_uniform_color([0, 0, 1]) # blue

    no_floor_pc = floor_segmentor.outliers
   
    # visualization 
    entities = [floor_pc, no_floor_pc, frame]
#     draw3D(entities, "2. Floor plane detection", viewpoint=viewpoint)
     
    # -------------------------------------------------------------------------
    # Compute the distance betweeen all points and the floor plane
    # -------------------------------------------------------------------------
    # Floor plane defined as: 
    #    a*x + b*y + c*z + d = 0
    # 
    # For a point x,y,z, the distance to the plane is:
    # 
    #  distance = abs(a*x + b*y + c*z + d) / srqt(a**2 + b**2 + c**2)  

    a,b,c,d = floor_segmentor.a, floor_segmentor.b, floor_segmentor.c, floor_segmentor.d

    arr = np.array(original_pc.points)
    print(arr.shape)
    xs = arr[:,0]
    ys = arr[:,1]
    zs = arr[:,2]

    distances_to_floor = abs(a * xs + b * ys + c * zs + d) / math.sqrt(a**2 + b**2 + c**2)

    print('distances: ' + str(distances_to_floor))
    print('distances shape: ' + str(distances_to_floor.shape))

    height_colors = cm.terrain( np.clip(distances_to_floor, 0, 2))
    height_colors = height_colors[:, 0:3] # remove the alpha channel that open3d does not like
#     print('Height colors shape' + str(height_colors.shape))

    original_pc_distance_to_floor_colors = deepcopy(original_pc)
    original_pc_distance_to_floor_colors.colors = o3d.utility.Vector3dVector(height_colors)

    entities = [original_pc_distance_to_floor_colors, frame]
#     draw3D(entities, "3. Distance to floor plane", viewpoint=viewpoint)

    # -------------------------------------------------------------------------
    # Filter points based on the estimated table height 
    # -------------------------------------------------------------------------
    table_height = 0.75
    table_min_heigh = table_height - 0.05
    table_max_heigh = table_height + 0.05

    idxs = np.where( (distances_to_floor > table_min_heigh) & (distances_to_floor < table_max_heigh) )[0] 

    points_at_table_height = original_pc.select_by_index(idxs, invert=False)
    points_at_table_height.paint_uniform_color([1, 0, 1]) # pink

    entities = [original_pc, frame, points_at_table_height]
#     draw3D(entities, "4. Points at table height", viewpoint)

    # -------------------------------------------------------------------------
    # Detect table plane
    # -------------------------------------------------------------------------
    table_segmentor = PlaneSegmentation(points_at_table_height)
    table_segmentor.findPlane(distance_threshold=0.01, ransac_n=3, num_iterations=1000)

    table_segmentor.inliers.paint_uniform_color([0, 1, 1]) # yellow

    entities = [original_pc, frame, table_segmentor.inliers]
#     draw3D(entities, "5. Table plane points", viewpoint)

    # -------------------------------------------------------------------------
    # Cluster points at table height
    # -------------------------------------------------------------------------
    labels = np.array(table_segmentor.inliers.cluster_dbscan(eps=0.2, min_points=10, print_progress=True))

    # Remove points that do not belong to a group
    group_idxs = list(set(labels))
    if -1 in group_idxs:
        group_idxs.remove(-1) # remove the last label, these are the ungrouped points

    point_cloud_of_groups = [] 
    for counter, group_idx in enumerate(group_idxs):

        idxs = np.where(labels == group_idx)[0]
        object_point_cloud = table_segmentor.inliers.select_by_index(idxs, invert=False)

        # Paint point cloud of group
        color = [random.uniform(0,1), random.uniform(0,1), random.uniform(0,1)]
        object_point_cloud.paint_uniform_color(color)

        point_cloud_of_groups.append(object_point_cloud)

    
    point_cloud_of_groups_gui = deepcopy(point_cloud_of_groups)
    entities = point_cloud_of_groups_gui
    entities.append(frame)
#     draw3D(entities, "6. Cluster points at table height", viewpoint)


    # -------------------------------------------------------------------------
    # Detect table point cloud as the biggest group
    # -------------------------------------------------------------------------

    table_pc = None

    for point_cloud in point_cloud_of_groups:
        num_points_in_point_cloud  = len(point_cloud.points) 

        if table_pc == None: # when we have no table_pc assume the first group pc is the table
            table_pc = point_cloud
        elif num_points_in_point_cloud > len(table_pc.points): # i we find a group with more points, this is tha table
            table_pc = point_cloud
 

    table_pc.paint_uniform_color([0.5, 0.5, 1]) # color ???

    entities = [original_pc, table_pc, frame]
    entities.append(frame)
    draw3D(entities, "7. Table poins ", viewpoint)

    # -------------------------------------------------------------------------
    # Detect table point cloud as the biggest group
    # -------------------------------------------------------------------------

    # Building an semi-arbitrary reference system on top of the table

    origin = np.array(table_pc.get_center())

    nz = -np.array([table_segmentor.a, table_segmentor.b, table_segmentor.c])

    # nx I select a ramdom point belongin to the table
    point1 = table_pc.points[0]

    nx = point1 - origin
    nx = nx / np.linalg.norm(nx) # make sure we have an unit vector

    # ny is the cross product between the nz and nx (order matters)
    ny = np.cross(nz, nx)

    # Assemble all into a transformation matrix
    T_scene_to_table = np.eye(4)
    T_scene_to_table[0:3,3] = origin
    T_scene_to_table[0:3, 0] = nx
    T_scene_to_table[0:3, 1] = ny
    T_scene_to_table[0:3, 2] = nz
    print('T=\n' + str(T_scene_to_table))

    table_frame = deepcopy(frame)
    table_frame.transform(T_scene_to_table)

    entities = [original_pc, frame, table_frame]
    draw3D(entities, "8. Table coordinate system", viewpoint)
    
    # -------------------------------------------------------------------------
    # transform the point cloud to the table coordinate system
    # -------------------------------------------------------------------------

    T_table_to_scene = np.linalg.inv(T_scene_to_table)

    original_pc_in_table = deepcopy(original_pc)
    original_pc_in_table.transform(T_table_to_scene)

    table_frame_in_table = deepcopy(table_frame)
    table_frame_in_table.transform(T_table_to_scene)

    table_pc_in_table_frame = deepcopy(table_pc)
    table_pc_in_table_frame.transform(T_table_to_scene)

    entities = [original_pc_in_table, table_frame_in_table]
#     draw3D(entities, "9. Point cloud in table coordinate system", viewpoint_in_table_frame)

    # -------------------------------------------------------------------------
    # Extract objects on top of table
    # -------------------------------------------------------------------------

    # find max and min x and y from the table_pc_in_table_frame
    arr = np.array(table_pc_in_table_frame.points)
    xmin, ymin = np.min(arr[:,0:2], axis=0)
    xmax, ymax = np.max(arr[:,0:2], axis=0)
    
    arr = np.array(original_pc_in_table.points)
    xs = arr[:,0]
    ys = arr[:,1]
    zs = arr[:,2]

    idxs = np.where( (zs > 0.01) & (zs < 0.4) &
                     (xs > xmin) & (xs < xmax) & 
                     (ys > ymin) & (ys < ymax) )[0]

    objects_pc = original_pc_in_table.select_by_index(idxs, invert=False)

    entities = [objects_pc, table_frame_in_table]
    draw3D(entities, "10. Objects on top of table", viewpoint_in_table_frame)

    # -------------------------------------------------------------------------
    # Split the objects into a point cloud per object 
    # -------------------------------------------------------------------------
    labels = np.array(objects_pc.cluster_dbscan(eps=0.03, min_points=50, print_progress=True))

    # Remove points that do not belong to a group
    group_idxs = list(set(labels))
    if -1 in group_idxs:
        group_idxs.remove(-1) # remove the last label, these are the ungrouped points

    point_clouds_of_objects = [] 
    for counter, group_idx in enumerate(group_idxs):

        idxs = np.where(labels == group_idx)[0]
        object_point_cloud = objects_pc.select_by_index(idxs, invert=False)

        # Paint point cloud of group
        color = [random.uniform(0,1), random.uniform(0,1), random.uniform(0,1)]
        object_point_cloud.paint_uniform_color(color)

        point_clouds_of_objects.append(object_point_cloud)


    
    entities = [table_frame_in_table]
    entities.extend(point_clouds_of_objects)
    draw3D(entities, "11. Separate each object into a point", viewpoint_in_table_frame)


    # -------------------------------------------------------------------------
    # Split the objects into a point cloud per object 
    # -------------------------------------------------------------------------
 
    for idx, point_cloud_of_object in enumerate(point_clouds_of_objects):
        filename = './output/object_' + str(idx) + '.ply'
        o3d.io.write_point_cloud(filename, point_cloud_of_object)

    




if __name__ == "__main__":
    main()





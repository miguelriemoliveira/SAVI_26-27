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
                        "boundingbox_max" : [ 6.5291471481323242, 34.024543762207031, 11.225864410400391 ],
                        "boundingbox_min" : [ -39.714397430419922, -16.512752532958984, -1.9472264051437378 ],
                        "field_of_view" : 60.0,
                        "front" : [ 0.90252725336848205, -0.21154048236017059, 0.37509356332783211 ],
                        "lookat" : [ -14.316933984735199, 2.1757857601535933, -0.14616852344082723 ],
                        "up" : [ -0.36710972183730356, 0.077374890705278865, 0.92695392464829884 ],
                        "zoom" : 0.3630252075195311
                }
        ],
        "version_major" : 1,
        "version_minor" : 0
}

# Main function
def main(): # this is our main function
    print("SAVI exercise")

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # initialize argparser
    ap = argparse.ArgumentParser()
    ap.add_argument("-pcf", "--point_cloud_file", type=str, required=False, 
                    default="../Ex2/factory_no_floor.pcd", help="Path to the point cloud file", )
    ap.add_argument("-mnp", "--max_num_planes", type=int, required=False, 
                    default=15)

    ap.add_argument("-at", "--angle_threshold", type=float, required=False, 
                    default=10, help='Angle threshold in degrees')
     
     
    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # Load the point cloud
    point_cloud = o3d.io.read_point_cloud(args['point_cloud_file'])
    print('Point cloud: ' + str(point_cloud))

    # -------------------------------------------------------------------------
    # Downsampling/
    # -------------------------------------------------------------------------
    point_cloud_sampled = point_cloud.voxel_down_sample(voxel_size=0.2)

    # point_cloud_sampled.estimate_normals(search_params=o3d.geometry.KDTreeSearchParamHybrid(0.5, max_nn=30))
    point_cloud_sampled.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.5, max_nn=30))
    point_cloud_sampled.orient_normals_to_align_with_direction(orientation_reference=np.array([0, 0, 1]))


    # -------------------------------------------------------------------------
    # Filter based on normals
    # -------------------------------------------------------------------------
 
    reference_orientation = np.array([0, 0, 1])
    norm_reference_orientation = np.linalg.norm(reference_orientation)

    normals = np.array(point_cloud_sampled.normals)
    print(normals)
    print(normals.shape)


    # For loop to cycle normals and  build a list of indices to copy later
    idxs_to_copy = []
    for idx_normal, normal in enumerate(normals):

        norm_normal = np.linalg.norm(normal)
        angle = math.acos( np.dot(normal, reference_orientation)  / ( norm_reference_orientation * norm_normal) )

        angle_in_deg = angle * 180/math.pi

        if angle_in_deg < args['angle_threshold']:
            idxs_to_copy.append(idx_normal)

    
    filtered_point_cloud = point_cloud_sampled.select_by_index(idxs_to_copy, invert=False)
    filtered_point_cloud.paint_uniform_color([0,1,0])

    # Ex7 to get the points belonging to non horizontal surfaces we use the inverse selection

    non_horizontal_point_cloud = point_cloud_sampled.select_by_index(idxs_to_copy, invert=True)
    non_horizontal_point_cloud.paint_uniform_color([0,1,1])

    # -------------------------------------------------------------------------
    # Visualization
    # -------------------------------------------------------------------------
    # Create drawing entities
    # entities = [point_cloud_sampled]
    # entities.extend(point_cloud_of_groups)
    entities = [point_cloud_sampled, filtered_point_cloud, non_horizontal_point_cloud]

    o3d.visualization.draw_geometries(entities,
                                      zoom=0.34,
                                       front=viewpoint['trajectory'][0]['front'],
                                       lookat=viewpoint['trajectory'][0]['lookat'],
                                       up=viewpoint['trajectory'][0]['up'])
      

if __name__ == "__main__":
    main()





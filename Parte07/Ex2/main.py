#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
import json
import random
import signal
import sys
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
                    default="../point_clouds/factory.ply", help="Path to the point cloud file", )
     
    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # Load the point cloud
    point_cloud = o3d.io.read_point_cloud(args['point_cloud_file'])
    print('Point cloud: ' + str(point_cloud))

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    # Find the ground plane
    plane_model, inlier_idxs = point_cloud.segment_plane(distance_threshold=0.3, ransac_n=3, num_iterations=100)

    # Hessian plane coefficients ->  Ax + By + Cz + D = 0
    a,b,c,d = plane_model 

    print('a=' + str(a) + ' b=' + str(b) +' c=' + str(c) +' d=' + str(d) )

    point_cloud_inliers = point_cloud.select_by_index(inlier_idxs, invert=False)
    point_cloud_inliers.paint_uniform_color([0.5, 0.5, 0])

    # Factory building and trees are the outliers of the ground plane
    point_cloud_outliers = point_cloud.select_by_index(inlier_idxs, invert=True)
#     point_cloud_outliers.paint_uniform_color([0.5, 0, 1])
    o3d.io.write_point_cloud('factory_no_floor.pcd', point_cloud_outliers, write_ascii=False)


    # -------------------------------------------------------------------------
    # Visualization
    # -------------------------------------------------------------------------
    # Create drawing entities
    entities = [point_cloud]
#     entities = [point_cloud_outliers, point_cloud_inliers]
#     entities = [point_cloud_outliers]

    o3d.visualization.draw_geometries(entities,
                                      zoom=0.34,
                                       front=viewpoint['trajectory'][0]['front'],
                                       lookat=viewpoint['trajectory'][0]['lookat'],
                                       up=viewpoint['trajectory'][0]['up'])
      

if __name__ == "__main__":
    main()





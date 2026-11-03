#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from copy import deepcopy
import json
import random
import signal
import sys
from matplotlib import cm
from more_itertools import locate
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
                    default="../Ex2/factory_no_floor.pcd", help="Path to the point cloud file", )
    ap.add_argument("-mnp", "--max_num_planes", type=int, required=False, 
                    default=15)
     
     
    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # Load the point cloud
    point_cloud = o3d.io.read_point_cloud(args['point_cloud_file'])
    print('Point cloud: ' + str(point_cloud))

    # -------------------------------------------------------------------------
    # Downsampling
    # -------------------------------------------------------------------------
    point_cloud_sampled = point_cloud.voxel_down_sample(voxel_size=0.2)

    # -------------------------------------------------------------------------
    # Clustering
    # -------------------------------------------------------------------------
    labels = point_cloud_sampled.cluster_dbscan(eps=2.0, min_points=100, print_progress=True)

    # print('labels = ' + str(labels[0:100]))

    # Remove points that do not belong to a group
    group_idxs = list(set(labels))
    group_idxs.remove(-1) # remove the last label, these are the ungrouped points
    # colormap = cm.Pastel1(range(0, 300))

    point_cloud_of_groups = [] 
    for counter, group_idx in enumerate(group_idxs):

        # This is to convert fro mthe labels representation to the point_cloud indices of this group representation, 
        # which is the format required by function select_by_index
        group_points_idx = list(locate(labels, lambda x: x == group_idx))

        group_point_cloud = point_cloud_sampled.select_by_index(group_points_idx, invert=False)

        # Paint point cloud of group
        color = [random.uniform(0,1), random.uniform(0,1), random.uniform(0,1)]
        # group_point_cloud.paint_uniform_color(color)

        point_cloud_of_groups.append(group_point_cloud)

    # -------------------------------------------------------------------------
    # Detect the largest group
    # -------------------------------------------------------------------------
    point_cloud_of_largest_group = None
    n_points_largest_group = None
    for point_cloud_of_group in point_cloud_of_groups:

        if point_cloud_of_largest_group == None:
            point_cloud_of_largest_group = point_cloud_of_group
            n_points_largest_group = len(point_cloud_of_largest_group.points)

        elif n_points_largest_group < len(point_cloud_of_group.points):
            point_cloud_of_largest_group = point_cloud_of_group
            n_points_largest_group = len(point_cloud_of_largest_group.points)


    # -------------------------------------------------------------------------
    # Visualization
    # -------------------------------------------------------------------------
    # Create drawing entities
    # entities = [point_cloud_sampled]
    # entities.extend(point_cloud_of_groups)
    entities = [point_cloud_of_largest_group]

    o3d.visualization.draw_geometries(entities,
                                      zoom=0.34,
                                       front=viewpoint['trajectory'][0]['front'],
                                       lookat=viewpoint['trajectory'][0]['lookat'],
                                       up=viewpoint['trajectory'][0]['up'])
      

if __name__ == "__main__":
    main()





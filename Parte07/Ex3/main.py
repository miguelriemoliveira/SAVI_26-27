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
    # Execution
    # -------------------------------------------------------------------------
    # Objective is to run ransac sementation progressively. 
    # when a plane is detected in one iteration of the progressive procedure, next iteration should be a ransac of the points 
    # minus the inliers of the previous iterations

    colormap = cm.Pastel1(range(0, args['max_num_planes']))
    point_cloud_remaning = deepcopy(point_cloud)
    inliers_of_planes = []

    for i in range(0,args['max_num_planes']): # progressive ransac procedures

        print('Remaining point cloud with ' + str(len(point_cloud_remaning.points)) + ' points ... ')

        ps = PlaneSegmentation(point_cloud_remaning)
        ps.findPlane()

        # paint point cloud inliers with uniform color from the colormap 
        color = colormap[i, 0:3]
        ps.inliers.paint_uniform_color(color)

        inliers_of_planes.append(ps.inliers)

        # Remove from the remaining points the inliers of this plane detection
        point_cloud_remaning = ps.outliers

        print('\n\nPlane detection iteration idx= ' + str(i))
        print('Detected plane with ' + str(len(ps.inliers.points)) + ' inliers')

    # -------------------------------------------------------------------------
    # Visualization
    # -------------------------------------------------------------------------
    # Create drawing entities
    entities = [point_cloud]
    entities.extend(inliers_of_planes)

    o3d.visualization.draw_geometries(entities,
                                      zoom=0.34,
                                       front=viewpoint['trajectory'][0]['front'],
                                       lookat=viewpoint['trajectory'][0]['lookat'],
                                       up=viewpoint['trajectory'][0]['up'])
      

if __name__ == "__main__":
    main()





#!/usr/bin/env python3 
# Shebang line" specifies the interpreter. 

# imports --------------------
import argparse
from copy import deepcopy
import glob
import json
import math
import random
import signal
import sys
from matplotlib import cm
# from more_itertools import locate
import numpy as np
import open3d as o3d



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
   


# Main function
def main(): # this is our main function
    print("SAVI exercise")

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    # initialize argparser
    ap = argparse.ArgumentParser()
    ap.add_argument("-of", "--objects_folder", type=str, required=False, 
                    default="../ex4/output", help="", )

    args = ap.parse_args()
    args = vars(args) # transform the args into a dictionary
    print('Input args: ' + str(args))

    # -------------------------------------------------------------------------
    # Load the point clouds
    # -------------------------------------------------------------------------

    filenames = glob.glob(args['objects_folder'] + '/' + '*.ply')
    print(filenames)

    objects_pcs = []
    for filename in filenames:

        object_pc = o3d.io.read_point_cloud(filename)
        objects_pcs.append(object_pc)

    frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5, origin=np.array([0., 0., 0.]))
    entities = [frame]
    entities.extend(objects_pcs)
    draw3D(entities, "1. Object point clouds ", viewpoint=viewpoint_in_table_frame)

    # -------------------------------------------------------------------------
    # Compute the object bounding boxes AABB and OBB
    # -------------------------------------------------------------------------

    aabbs = []
    obbs = []
    for object_pc in objects_pcs:

        aabb = object_pc.get_axis_aligned_bounding_box()
        aabb.color = [1,0,0] # define the color of aabb to red
        aabbs.append(aabb)

        obb = object_pc.get_oriented_bounding_box()
        obb.color = [0,1,0] # greeen color for obbs
        obbs.append(obb)




    entities = [frame]
    entities.extend(objects_pcs)
    entities.extend(aabbs)
    entities.extend(obbs)
    draw3D(entities, "2. Bounding boxes", viewpoint=viewpoint_in_table_frame)








if __name__ == "__main__":
    main()





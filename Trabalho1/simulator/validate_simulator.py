#!/usr/bin/env python3
# SAVI 26-27
# Miguel Riem Oliveira, DEM, UA
"""Validation of the simulator: takes each generated point cloud to the world with the true pose,
and measures the distance from the points to the scene geometry.

Usage:
    ./savi_box_simulator.py --batch configs/level_1.json --no_noise
    ./validate_simulator.py configs/level_1.json scenes/level_1_no_noise
"""

import argparse
import json
from pathlib import Path

import numpy as np
import open3d as o3d
import open3d.core as o3c

from savi_box_simulator import Scene, read_config


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("config")
    parser.add_argument("scene_folder")
    args = parser.parse_args()

    folder = Path(args.scene_folder)
    scene = Scene(read_config(args.config))
    ground_truth = json.loads((folder / "ground_truth.json").read_text(encoding="utf-8"))

    print(f"{'image':8s}{'points':>9s}{'mean mm':>10s}{'p99 mm':>9s}{'max mm':>9s}")
    for camera in ground_truth["cameras"]:
        cloud = o3d.io.read_point_cloud(str(folder / "point_clouds" / f"{camera['image']}.ply"))
        cloud.transform(np.array(camera["T_world_camera"]))
        points = np.asarray(cloud.points, np.float32)
        d = scene.raycaster.compute_distance(o3c.Tensor(points)).numpy() * 1000
        print(f"{camera['image']:8s}{len(points):9d}{d.mean():10.3f}{np.percentile(d, 99):9.3f}{d.max():9.3f}")


if __name__ == "__main__":
    main()

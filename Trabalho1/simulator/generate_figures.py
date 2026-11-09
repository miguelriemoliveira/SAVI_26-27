#!/usr/bin/env python3
# SAVI 26-27
# Miguel Riem Oliveira, DEM, UA
"""Generates the figures of the assignment in the ../docs folder, from the simulator.

Usage:
    ./savi_box_simulator.py --batch configs/level_*.json
    ./generate_figures.py
"""

import argparse
import json
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d

from savi_box_simulator import Scene, intrinsics_matrix, look_at, read_config

FOLDER = Path(__file__).parent
DOCS = FOLDER.parent / "docs"
CONFIGS = FOLDER / "configs"

# The captions are in Portuguese because the figures go in the assignment, which is in Portuguese
LEVEL_CAPTIONS = {
    "level_1": "Nível 1: uma caixa",
    "level_2": "Nível 2: várias caixas separadas, da mesma cor",
    "level_3_widths": "Nível 3: várias caixas em contacto, da mesma cor",
    "level_4": "Nível 4: várias caixas em contacto, de cores diferentes",
}
LEVEL_3_CAPTIONS = {
    "level_3_heights": "Alturas diferentes",
    "level_3_widths": "Larguras diferentes",
    "level_3_rotated": "Rodadas entre si",
    "level_3_aligned": "Iguais e alinhadas",
}
IMAGE_CAPTION = "Imagem {:03d}"
CLOUD_CAPTIONS = ("Nuvem agregada, com a cor dos pixels", "A mesma nuvem, com uma cor para cada câmara")
CLOUD_IMAGES = ("006", "007", "000")  # three neighbouring viewpoints
CAMERA_COLORS = np.array([[0.95, 0.55, 0.05], [0.55, 0.20, 0.75], [0.05, 0.65, 0.70]])


def close_view(name, eye=(0.62, -0.78, 0.62), target=(0.0, 0.0, 0.06)):
    """Renders the scene without noise, with a camera close to the boxes."""
    config = read_config(CONFIGS / f"{name}.json")
    intrinsics = config["intrinsics"]
    color, _ = Scene(config).render(look_at(eye, target), intrinsics_matrix(intrinsics), intrinsics["width"], intrinsics["height"])
    return color


def grid_figure(images, captions, columns, destination, width=12.0):
    rows = int(np.ceil(len(images) / columns))
    h, w = images[0].shape[:2]
    cell_height = (width / columns) * h / w + 0.45
    fig, axes = plt.subplots(rows, columns, figsize=(width, cell_height * rows), dpi=110, squeeze=False)
    for ax in axes.ravel():
        ax.set_axis_off()
    for ax, image, caption in zip(axes.ravel(), images, captions):
        ax.imshow(image)
        ax.set_title(caption, fontsize=12)
    fig.tight_layout(pad=0.5)
    fig.savefig(destination)
    plt.close(fig)
    print(destination.name)


def aggregated_cloud(folder, images):
    """Joins the point clouds of the given images in the world frame with the true poses, just for illustration.

    Returns the points, their colors and the index of the camera each point came from.
    """
    ground_truth = json.loads((folder / "ground_truth.json").read_text(encoding="utf-8"))
    poses = {camera["image"]: np.array(camera["T_world_camera"]) for camera in ground_truth["cameras"]}
    points, colors, cameras = [], [], []
    for i, image in enumerate(images):
        cloud = o3d.io.read_point_cloud(str(folder / "point_clouds" / f"{image}.ply"))
        cloud.transform(poses[image])
        points.append(np.asarray(cloud.points))
        colors.append(np.asarray(cloud.colors))
        cameras.append(np.full(len(cloud.points), i))
    return np.vstack(points), np.vstack(colors), np.concatenate(cameras)


def project(points, T_world_camera, f, width, height):
    T = np.linalg.inv(T_world_camera)
    p = points @ T[:3, :3].T + T[:3, 3]
    z = np.where(p[:, 2] > 0.05, p[:, 2], np.nan)
    u = np.round(f * p[:, 0] / z + width / 2)
    v = np.round(f * p[:, 1] / z + height / 2)
    valid = np.isfinite(z)
    return u[valid].astype(int), v[valid].astype(int), z[valid], valid


def splat(u, v, z, radius, width, height):
    """Pixel index and depth of each point, drawn as a square with the given radius."""
    for du in range(-radius, radius + 1):
        for dv in range(-radius, radius + 1):
            uu, vv = u + du, v + dv
            inside = (uu >= 0) & (uu < width) & (vv >= 0) & (vv < height)
            yield vv[inside] * width + uu[inside], z[inside], inside


def draw_points(points, colors, T_world_camera, f, width, height, voxel=0.005, background=1.0):
    """Draws a point cloud as separate dots, as seen from a virtual camera.

    The points, drawn as large squares, define the depth of the visible surfaces. Isolated points (flying pixels) are
    left out of this step, otherwise each one would hide a square around it. Then a downsampled cloud is drawn as
    small dots, keeping only the dots on those surfaces, so that the points behind them do not show through.
    """
    dense = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points)).voxel_down_sample(0.002)
    dense, _ = dense.remove_radius_outlier(nb_points=8, radius=0.008)
    u, v, z, _ = project(np.asarray(dense.points), T_world_camera, f, width, height)
    surface = np.full(height * width, np.inf)
    for index, zs, _ in splat(u, v, z, 3, width, height):
        np.minimum.at(surface, index, zs)

    # One point for each voxel, taken at random, so that the colors are not averaged and the cameras stay mixed
    shuffled = np.random.default_rng(0).permutation(len(points))
    _, first = np.unique(np.floor(points[shuffled] / voxel).astype(np.int64), axis=0, return_index=True)
    keep = shuffled[first]
    u, v, z, valid = project(points[keep], T_world_camera, f, width, height)
    c = colors[keep][valid]
    order = np.argsort(-z)
    u, v, z, c = u[order], v[order], z[order], c[order]
    image = np.full((height * width, 3), background, float)
    for index, zs, inside in splat(u, v, z, 1, width, height):
        visible = zs <= surface[index] + 0.02
        image[index[visible]] = c[inside][visible]
    return image.reshape(height, width, 3)


CLOUD_VIEW = look_at((1.25, -1.45, 1.05), (-0.05, 0.1, 0.0))


def aggregated_cloud_figure(scenes):
    """Aggregated point cloud of three viewpoints of the level 4 scene: pixel colors, and one color per camera."""
    T = CLOUD_VIEW
    points, colors, cameras = aggregated_cloud(scenes / "level_4", CLOUD_IMAGES)
    images = [np.clip(draw_points(points, c, T, 900, 1000, 700, voxel=0.012), 0, 1) for c in (colors, CAMERA_COLORS[cameras])]
    grid_figure(images, list(CLOUD_CAPTIONS), 2, DOCS / "aggregated_cloud.png")


def segmentation_figure(scenes):
    """The same aggregated cloud, with only the points on top of the table in their own color, the others in gray.

    The points are selected with the true table (top at z = 0 in the world frame), just to show the expected result.
    """
    folder = scenes / "level_4"
    table = json.loads((folder / "config.json").read_text(encoding="utf-8"))["table"]
    points, colors, _ = aggregated_cloud(folder, CLOUD_IMAGES)
    on_table = ((np.abs(points[:, 0]) < table["length"] / 2) & (np.abs(points[:, 1]) < table["width"] / 2)
                & (points[:, 2] > 0.005) & (points[:, 2] < 0.6))
    gray = 0.5 + 0.4 * colors.mean(axis=1, keepdims=True)  # keeps some shading, so that the room is still readable
    colors = np.where(on_table[:, None], colors, gray)
    image = np.clip(draw_points(points, colors, CLOUD_VIEW, 900, 1000, 700, voxel=0.012), 0, 1)
    plt.imsave(DOCS / "segmentation.png", image)
    print("segmentation.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenes", default=str(FOLDER / "scenes"), help="folder with the generated scenes")
    args = parser.parse_args()
    scenes = Path(args.scenes)
    DOCS.mkdir(exist_ok=True)

    grid_figure([close_view(n) for n in LEVEL_CAPTIONS], list(LEVEL_CAPTIONS.values()), 2, DOCS / "levels.png")
    grid_figure([close_view(n) for n in LEVEL_3_CAPTIONS], list(LEVEL_3_CAPTIONS.values()), 2, DOCS / "level_3_cases.png")

    views = [cv2.imread(str(scenes / "level_4" / "rgb" / f"{i:03d}.png"))[..., ::-1] for i in range(8)]
    grid_figure(views, [IMAGE_CAPTION.format(i) for i in range(8)], 4, DOCS / "views_around_table.png")

    aggregated_cloud_figure(scenes)
    segmentation_figure(scenes)


if __name__ == "__main__":
    main()

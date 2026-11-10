#!/usr/bin/env python3
# SAVI 26-27
# Miguel Riem Oliveira, DEM, UA
"""SAVI box simulator: RGB-D scenes with boxes on a table, based on ray casting.

Usage:
    ./savi_box_simulator.py
    ./savi_box_simulator.py --config configs/level_4.json
    ./savi_box_simulator.py --batch configs/level_*.json
    ./savi_box_simulator.py --batch configs/level_1.json --no_noise --output scenes

Without --batch, the simulator opens a window. Add boxes and change them in the panel, navigate the
3D view with the mouse (dragging turns around the table) and press "Capture" to acquire an image from that viewpoint. In the end,
export to a new scene folder. Ctrl+Q closes the window. With --batch, it generates scenes from
configuration files.

World frame: origin at the centre of the table top, z up.
Camera frame: x right, y down, z forward.
Units: meters.

Each box is given by x, y, z and yaw_deg. x and y are the center of the box, z is the height of its base above the
table top: z = 0 for a box resting on the table, z = height of the box below for a box stacked on top of another.
The box frame (T_world_box) has its origin at the center of the box, so its translation is (x, y, z + height / 2).

Each scene is a folder with:
    point_clouds/000.ply   colored point cloud, in the frame of the camera that acquired it
    rgb/000.png            corresponding color image
    intrinsics.json        camera parameters
    ground_truth.json      camera poses, box poses and box dimensions
    config.json            configuration that generated the scene
"""

import argparse
import copy
import json
import signal
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import open3d as o3d
import open3d.core as o3c
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering

INVALID_ID = o3d.t.geometry.RaycastingScene.INVALID_ID


# --------------------------------------
# Configuration
# --------------------------------------
def merge(base, new):
    """Merges two dictionaries. The values in new take priority."""
    result = dict(base)
    for key, value in new.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def read_config(path):
    """Reads a configuration. The "base" field names a file with default values."""
    path = Path(path)
    config = json.loads(path.read_text(encoding="utf-8"))
    if "base" in config:
        config = merge(read_config(path.parent / config.pop("base")), config)
    config.setdefault("name", path.stem)
    return config


# --------------------------------------
# Geometry
# --------------------------------------
def make_transform(x, y, z, yaw=0.0):
    c, s = np.cos(yaw), np.sin(yaw)
    T = np.eye(4)
    T[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    T[:3, 3] = [x, y, z]
    return T


def box_transform(box):
    """T_world_box: origin at the center of the box. The z of the box is the height of its base above the table top."""
    return make_transform(box["x"], box["y"], box.get("z", 0.0) + box["height"] / 2, np.radians(box.get("yaw_deg", 0.0)))


def box_top_below(boxes, index):
    """Height of the top of the highest box under the center of box index, or 0 (the table) if there is none.

    Only the boxes that come before it in the list count, so a new box always goes on top of the existing ones.
    """
    box, top = boxes[index], 0.0
    for other in boxes[:index]:
        # Center of the box in the frame of the other one, to compare with its half dimensions
        yaw = np.radians(other.get("yaw_deg", 0.0))
        dx, dy = box["x"] - other["x"], box["y"] - other["y"]
        u, v = np.cos(yaw) * dx + np.sin(yaw) * dy, -np.sin(yaw) * dx + np.cos(yaw) * dy
        if abs(u) <= other["length"] / 2 and abs(v) <= other["width"] / 2:
            top = max(top, other.get("z", 0.0) + other["height"])
    return top


def look_at(eye, target, up=(0.0, 0.0, 1.0)):
    """Camera pose in the world, with the z axis pointing from the eye to the target."""
    eye, target = np.asarray(eye, float), np.asarray(target, float)
    z = target - eye
    z /= np.linalg.norm(z)
    x = np.cross(z, up)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, z, eye
    return T


def cuboid(dimensions, T):
    """Vertices and triangles of a cuboid centered at the origin of T."""
    half = np.asarray(dimensions, float) / 2
    signs = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)
    vertices = (T[:3, :3] @ (signs * half).T).T + T[:3, 3]
    triangles = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                          [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]], np.uint32)
    return vertices.astype(np.float32), triangles


def camera_poses(config, rng):
    """List of T_world_camera poses: explicit, or in a circle around the table."""
    cameras = config["cameras"]
    if "poses" in cameras:
        return [pose_from_config(p) for p in cameras["poses"]]
    poses = []
    for i in range(cameras["count"]):
        angle = np.radians(cameras.get("start_angle_deg", 0.0)) + 2 * np.pi * i / cameras["count"]
        eye = np.array([cameras["radius"] * np.cos(angle), cameras["radius"] * np.sin(angle), cameras["height"]])
        eye += rng.normal(0, cameras.get("eye_jitter", 0.0), 3)
        target = np.asarray(cameras["target"], float) + rng.normal(0, cameras.get("target_jitter", 0.0), 3)
        poses.append(look_at(eye, target))
    return poses


def pose_from_config(pose):
    if "T_world_camera" in pose:
        return np.array(pose["T_world_camera"], float)
    return look_at(pose["eye"], pose["target"])


# --------------------------------------
# Textures, so that registration has information to rely on
# --------------------------------------
def smooth_noise(rng, side, scale):
    small = rng.random((side // scale + 1, side // scale + 1), dtype=np.float32)
    return cv2.resize(small, (side, side), interpolation=cv2.INTER_CUBIC)


def table_texture(rng, side=1024):
    """Plain pale table top, with one uniform color."""
    return np.full((side, side, 3), 0.80, np.float32) * np.array([0.92, 1.0, 0.98], np.float32)


def floor_texture(rng, side=1024, plank=28):
    """Wooden floor: planks with different tones, a grain along their length and a few knots."""
    wood = np.array([0.60, 0.43, 0.27], np.float32)
    t = np.zeros((side, side, 3), np.float32)
    for row in range(0, side, plank):
        x = -int(rng.integers(0, 320))
        while x < side:
            length = int(rng.integers(220, 420))
            t[row:row + plank, max(x, 0):x + length] = rng.uniform(0.72, 1.05) * wood
            t[row:row + plank, max(x + length - 1, 0):x + length] = 0.12
            if rng.random() < 0.3:
                knot = (int(x + rng.integers(0, length)), int(row + rng.integers(6, plank - 6)))
                cv2.ellipse(t, knot, (int(rng.integers(4, 10)), int(rng.integers(2, 4))), 0, 0, 360, (0.38, 0.26, 0.16), -1, cv2.LINE_AA)
            x += length
        t[row:row + 1, :] = 0.12
    grain = cv2.resize(rng.random((side, side // 48), dtype=np.float32), (side, side), interpolation=cv2.INTER_LINEAR)
    return t * (0.84 + 0.32 * grain)[..., None]


def wall_texture(rng, side=1024):
    """Painted plaster: one even color with faint irregularities."""
    relief = 0.93 + 0.05 * smooth_noise(rng, side, 128) + 0.03 * smooth_noise(rng, side, 12)
    grain = 0.012 * rng.standard_normal((side, side), dtype=np.float32)
    return np.clip(np.array([0.85, 0.82, 0.75], np.float32) * (relief + grain)[..., None], 0, 1)


def poster_texture(text_lines, width=1400, height=700):
    """Poster with text. There is only one in the room, so that it is not confused with itself in registration."""
    t = np.full((height, width, 3), (23, 41, 92), np.uint8)
    cv2.rectangle(t, (22, 22), (width - 23, height - 23), (250, 199, 38), 12, cv2.LINE_AA)
    for (x, side), color in zip(((90, 120), (225, 170), (410, 100)), ((184, 51, 46), (179, 135, 92), (51, 158, 71))):
        cv2.rectangle(t, (x, 640 - side), (x + side, 640), color, -1)
    for i, line in enumerate(text_lines):
        scale = 4.6
        (w, _), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_DUPLEX, scale, 12)
        cv2.putText(t, line, ((width - w) // 2, 190 + i * 170), cv2.FONT_HERSHEY_DUPLEX, scale, (255, 255, 255), 12, cv2.LINE_AA)
    return t.astype(np.float32) / 255


def room_texture_scale(room, texture):
    """Meters per texture pixel, for one texture to cover the room with a margin of half a meter at each side."""
    return (max(room["length"], room["width"], room["height"]) + 1) / texture.shape[0]


def sample_texture(texture, u, v):
    """Bilinear interpolation, with texture repetition."""
    side_v, side_u = texture.shape[:2]
    u, v = np.mod(u, side_u), np.mod(v, side_v)
    u0, v0 = u.astype(int), v.astype(int)
    du, dv = (u - u0)[:, None], (v - v0)[:, None]
    u1, v1 = (u0 + 1) % side_u, (v0 + 1) % side_v
    return ((1 - du) * (1 - dv) * texture[v0, u0] + du * (1 - dv) * texture[v0, u1]
            + (1 - du) * dv * texture[v1, u0] + du * dv * texture[v1, u1])


# --------------------------------------
# Furniture
# --------------------------------------
# Every object is built in its own frame: origin at the middle of its back, on the floor, width along x,
# front towards +y. This way an object is placed against a wall by giving a point of that wall and a rotation.
DARK_WOOD, LIGHT_WOOD = (0.36, 0.24, 0.16), (0.62, 0.46, 0.30)
WHITE_PAINT, METAL = (0.92, 0.91, 0.88), (0.32, 0.32, 0.34)
FABRIC, CUSHION, PILLOW = (0.30, 0.36, 0.40), (0.35, 0.41, 0.45), (0.72, 0.60, 0.36)
SHADE, TERRACOTTA, SOIL = (0.93, 0.88, 0.76), (0.66, 0.36, 0.24), (0.14, 0.10, 0.08)
GLASS, CURTAIN, BARK = (0.74, 0.86, 0.95), (0.64, 0.66, 0.60), (0.28, 0.20, 0.13)
LEAVES = ((0.14, 0.36, 0.17), (0.19, 0.44, 0.20), (0.11, 0.30, 0.16))
BOOKS = ((0.45, 0.17, 0.15), (0.17, 0.26, 0.40), (0.20, 0.34, 0.27), (0.70, 0.65, 0.54), (0.50, 0.38, 0.22), (0.26, 0.24, 0.26))


def block(dimensions, center):
    mesh = o3d.geometry.TriangleMesh.create_box(*dimensions)
    return mesh.translate(np.asarray(center, float) - np.asarray(dimensions, float) / 2)


def rod(start, end, radius):
    """Cylinder between two points."""
    start, end = np.asarray(start, float), np.asarray(end, float)
    z = (end - start) / np.linalg.norm(end - start)
    x = np.cross(z, (1.0, 0.0, 0.0) if abs(z[0]) < 0.9 else (0.0, 1.0, 0.0))
    x /= np.linalg.norm(x)
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, np.cross(z, x), z, (start + end) / 2
    return o3d.geometry.TriangleMesh.create_cylinder(radius, np.linalg.norm(end - start), resolution=10).transform(T)


def lathe(profile, sides=24):
    """Surface of revolution around z. The profile lists (radius, z) from the bottom to the top."""
    angles = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    vertices = [[r * np.cos(a), r * np.sin(a), z] for r, z in profile for a in angles]
    triangles = []
    for i in range(len(profile) - 1):
        for j in range(sides):
            a, b = i * sides + j, i * sides + (j + 1) % sides
            triangles += [[a, b, b + sides], [a, b + sides, a + sides]]
    mesh = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(vertices), o3d.utility.Vector3iVector(triangles))
    return mesh.remove_duplicated_vertices().remove_degenerate_triangles()


def leaf(base, yaw, droop, length, width):
    """Flattened ellipsoid that starts at the base and points in the direction given by yaw and droop."""
    mesh = o3d.geometry.TriangleMesh.create_sphere(1.0, resolution=5)
    v = np.asarray(mesh.vertices) * np.array([length / 2, width / 2, 0.004]) + np.array([length / 2, 0, 0])
    cy, sy, cd, sd = np.cos(yaw), np.sin(yaw), np.cos(droop), np.sin(droop)
    R = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]) @ np.array([[cd, 0, sd], [0, 1, 0], [-sd, 0, cd]])
    mesh.vertices = o3d.utility.Vector3dVector(v @ R.T + np.asarray(base, float))
    return mesh


def moved(parts, x, y, z):
    return [(mesh.translate((x, y, z)), color) for mesh, color in parts]


def plant(rng, height=1.5):
    s = height / 1.5
    parts = [(lathe([(0, 0), (0.13 * s, 0), (0.19 * s, 0.32 * s), (0.20 * s, 0.36 * s), (0, 0.36 * s)]), TERRACOTTA),
             (lathe([(0, 0.36 * s), (0.17 * s, 0.36 * s), (0, 0.365 * s)]), SOIL)]
    for stem in range(3):
        angle = 2 * np.pi * (stem / 3 + rng.uniform(-0.05, 0.05))
        lean = rng.uniform(0.10, 0.28) * s
        top = np.array([lean * np.cos(angle), lean * np.sin(angle), height * rng.uniform(0.82, 1.0)])
        bottom = np.array([0, 0, 0.3 * s])
        parts.append((rod(bottom, top, 0.012 * s), BARK))
        for fraction in np.linspace(0.3, 1.0, 16):
            yaw, droop = rng.uniform(0, 2 * np.pi), rng.uniform(-0.1, 0.8)
            length = rng.uniform(0.20, 0.34) * s
            base = bottom + fraction * (top - bottom)
            parts.append((leaf(base, yaw, droop, length, 0.42 * length), LEAVES[rng.integers(len(LEAVES))]))
    return parts


def wardrobe(rng, width=1.3, depth=0.55, height=2.05):
    parts = [(block((width, depth, height - 0.08), (0, depth / 2, height / 2 + 0.04)), LIGHT_WOOD),
             (block((width - 0.04, depth - 0.04, 0.08), (0, depth / 2, 0.04)), DARK_WOOD)]
    for side in (-1, 1):
        parts.append((block((width / 2 - 0.015, 0.02, height - 0.12), (side * width / 4, depth + 0.01, height / 2 + 0.04)), LIGHT_WOOD))
        parts.append((block((0.015, 0.02, 0.22), (side * 0.05, depth + 0.03, height / 2 + 0.05)), METAL))
    return parts


def bookcase(rng, width=1.2, depth=0.3, height=2.0, shelves=5):
    thickness = 0.025
    parts = [(block((width, 0.01, height), (0, 0.005, height / 2)), DARK_WOOD)]
    for side in (-1, 1):
        parts.append((block((thickness, depth, height), (side * (width - thickness) / 2, depth / 2, height / 2)), DARK_WOOD))
    levels = np.linspace(thickness / 2 + 0.05, height - thickness / 2, shelves + 1)
    gap = levels[1] - levels[0] - thickness
    for i, level in enumerate(levels):
        parts.append((block((width - 2 * thickness, depth, thickness), (0, depth / 2, level)), DARK_WOOD))
        if i == shelves:
            break
        x = -width / 2 + thickness + 0.01
        while x < width / 2 - thickness - 0.07:
            if rng.random() < 0.08:
                x += rng.uniform(0.04, 0.14)
                continue
            w, h, d = rng.uniform(0.018, 0.05), rng.uniform(0.6, 0.9) * gap, rng.uniform(0.14, 0.24)
            book = block((w, d, h), (x + w / 2, 0.02 + d / 2, level + thickness / 2 + h / 2))
            parts.append((book, BOOKS[rng.integers(len(BOOKS))]))
            x += w + 0.001
    return parts


def sideboard(rng, width=1.7, depth=0.45, height=0.82):
    parts = [(block((width, depth, height - 0.14), (0, depth / 2, 0.14 + (height - 0.14) / 2)), LIGHT_WOOD)]
    for sx in (-1, 1):
        for y in (0.05, depth - 0.05):
            parts.append((rod((sx * (width / 2 - 0.06), y, 0), (sx * (width / 2 - 0.06), y, 0.14), 0.015), DARK_WOOD))
    for i in range(3):
        x = (i - 1) * width / 3
        parts.append((block((width / 3 - 0.012, 0.018, height - 0.18), (x, depth + 0.009, 0.14 + (height - 0.14) / 2)), LIGHT_WOOD))
        parts.append((block((0.13, 0.018, 0.012), (x, depth + 0.027, height - 0.11)), METAL))
    parts += moved(plant(rng, height=0.6), width / 2 - 0.3, depth / 2, height)
    z = height
    for i in range(3):
        book = block((0.28 - 0.02 * i, 0.20, 0.035), (-width / 2 + 0.32, depth / 2, z + 0.0175))
        parts.append((book, BOOKS[rng.integers(len(BOOKS))]))
        z += 0.035
    vase = lathe([(0, 0), (0.05, 0), (0.09, 0.08), (0.06, 0.22), (0.04, 0.26), (0, 0.26)])
    return parts + moved([(vase, PILLOW)], 0.05, depth / 2, height)


def sofa(rng, seats=3, seat_width=0.62, depth=0.9):
    arm = 0.16
    width = seats * seat_width + 2 * arm
    parts = [(block((width, depth, 0.2), (0, depth / 2, 0.2)), FABRIC),
             (block((width, 0.2, 0.5), (0, 0.1, 0.55)), FABRIC)]
    for sx in (-1, 1):
        parts.append((block((arm, depth, 0.3), (sx * (width - arm) / 2, depth / 2, 0.45)), FABRIC))
        for y in (0.06, depth - 0.06):
            parts.append((rod((sx * (width / 2 - 0.06), y, 0), (sx * (width / 2 - 0.06), y, 0.1), 0.02), DARK_WOOD))
    for i in range(seats):
        x = (i - (seats - 1) / 2) * seat_width
        parts.append((block((seat_width - 0.012, depth - 0.2, 0.15), (x, 0.2 + (depth - 0.2) / 2, 0.375)), CUSHION))
        parts.append((block((seat_width - 0.012, 0.15, 0.36), (x, 0.275, 0.63)), CUSHION))
    if seats > 1:
        for sx, yaw in ((-1, 0.25), (1, -0.2)):
            pillow = block((0.38, 0.11, 0.38), (0, 0, 0))
            pillow.transform(make_transform(sx * (width / 2 - arm - 0.22), 0.42, 0.63, yaw))
            parts.append((pillow, PILLOW))
    return parts


def armchair(rng):
    return sofa(rng, seats=1, seat_width=0.68, depth=0.85)


def floor_lamp(rng, height=1.65):
    return [(lathe([(0, 0), (0.15, 0), (0.15, 0.02), (0.02, 0.04), (0, 0.04)]), METAL),
            (rod((0, 0, 0.03), (0, 0, height - 0.2), 0.012), METAL),
            (lathe([(0, height - 0.26), (0.21, height - 0.26), (0.12, height), (0, height)]), SHADE)]


def door(rng, width=0.9, height=2.05):
    parts = [(block((width + 0.16, 0.02, 0.08), (0, 0.01, height + 0.04)), WHITE_PAINT),
             (block((width, 0.035, height), (0, 0.0175, height / 2)), LIGHT_WOOD),
             (block((width - 0.3, 0.01, 0.72), (0, 0.04, 0.48)), DARK_WOOD),
             (block((width - 0.3, 0.01, 0.72), (0, 0.04, 1.42)), DARK_WOOD),
             (o3d.geometry.TriangleMesh.create_sphere(0.03, resolution=8).translate((width / 2 - 0.08, 0.07, 1.0)), METAL)]
    for side in (-1, 1):
        parts.append((block((0.08, 0.02, height), (side * (width / 2 + 0.04), 0.01, height / 2)), WHITE_PAINT))
    return parts


def window(rng, width=1.8, height=1.25):
    """The z of the object is the bottom of the window."""
    bar = 0.05
    parts = [(block((width, 0.015, height), (0, 0.0075, height / 2)), GLASS),
             (block((width + 0.1, 0.14, 0.03), (0, 0.07, -0.015)), WHITE_PAINT),
             (block((width + 0.2, 0.03, 0.03), (0, 0.13, height + 0.14)), METAL)]
    for z in (bar / 2, height / 2, height - bar / 2):
        parts.append((block((width, 0.03, bar), (0, 0.03, z)), WHITE_PAINT))
    for x in (-width / 2 + bar / 2, 0, width / 2 - bar / 2):
        parts.append((block((bar, 0.03, height), (x, 0.03, height / 2)), WHITE_PAINT))
    # Curtains: alternating pleats at both sides
    for side in (-1, 1):
        for i in range(7):
            x = side * (width / 2 + 0.06 - i * 0.06)
            y = 0.10 if i % 2 else 0.13
            parts.append((block((0.065, 0.03, height + 0.42), (x, y, (height + 0.42) / 2 - 0.3 + 0.03)), CURTAIN))
    return parts


def picture(rng, width=0.8, height=0.55):
    """Framed landscape. The z of the object is the bottom of the frame."""
    margin, inner_w, inner_h = 0.035, width - 0.15, height - 0.15
    parts = [(block((width, 0.025, height), (0, 0.0125, height / 2)), DARK_WOOD),
             (block((width - 2 * margin, 0.006, height - 2 * margin), (0, 0.027, height / 2)), WHITE_PAINT)]
    bottom = (height - inner_h) / 2
    for fraction, band, color in ((0.72, 0.28, (0.63, 0.74, 0.82)), (0.40, 0.32, (0.43, 0.48, 0.50)), (0.0, 0.40, (0.46, 0.54, 0.33))):
        center = (0, 0.032, bottom + inner_h * (fraction + band / 2))
        parts.append((block((inner_w, 0.004, inner_h * band), center), color))
    return parts


FURNITURE = {"plant": plant, "wardrobe": wardrobe, "bookcase": bookcase, "sideboard": sideboard, "sofa": sofa, "armchair": armchair,
             "floor_lamp": floor_lamp, "door": door, "window": window, "picture": picture}


def wall_at(x, y, length, width):
    """Name of the wall that contains this point, or None for a point away from the walls."""
    for name, distance in (("wall_0", width / 2 - y), ("wall_1", width / 2 + y), ("wall_2", length / 2 - x), ("wall_3", length / 2 + x)):
        if abs(distance) < 0.01:
            return name
    return None


def room_parts(config):
    """Skirting boards and furniture, as a list of (color, wall, mesh). The wall is the one the part is attached to, or None.

    The meshes are grouped by color and wall, to have few geometries.
    """
    rng = np.random.default_rng(config["seed"] + 2)
    floor_z = -config["table"]["height"]
    length, width = config["room"]["length"], config["room"]["width"]
    parts = {}

    def add(mesh, color, wall):
        key = (color, wall)
        parts[key] = parts[key] + mesh if key in parts else mesh

    for wall, x in (("wall_3", -length / 2 + 0.008), ("wall_2", length / 2 - 0.008)):
        add(block((0.016, width, 0.09), (x, 0, floor_z + 0.045)), WHITE_PAINT, wall)
    for wall, y in (("wall_1", -width / 2 + 0.008), ("wall_0", width / 2 - 0.008)):
        add(block((length, 0.016, 0.09), (0, y, floor_z + 0.045)), WHITE_PAINT, wall)

    for item in config.get("furniture", []):
        options = {k: v for k, v in item.items() if k not in ("type", "x", "y", "z", "yaw_deg")}
        T = make_transform(item["x"], item["y"], floor_z + item.get("z", 0.0), np.radians(item.get("yaw_deg", 0.0)))
        wall = wall_at(item["x"], item["y"], length, width)
        for mesh, color in FURNITURE[item["type"]](rng, **options):
            add(mesh.transform(T), color, wall)
    return [(color, wall, mesh) for (color, wall), mesh in parts.items()]


# --------------------------------------
# Scene
# --------------------------------------
WALL_MARGIN = 0.05
BACKGROUND = 0.93


def hidden_walls(eye, room):
    """Walls with the eye behind them. They are left out, with what is attached to them, so that they do not block the room.

    The same rule applies to the captured images and to the 3D view, so that both show the same.
    """
    half_length, half_width = room["length"] / 2 - WALL_MARGIN, room["width"] / 2 - WALL_MARGIN
    behind = {"wall_0": eye[1] >= half_width, "wall_1": eye[1] <= -half_width, "wall_2": eye[0] >= half_length, "wall_3": eye[0] <= -half_length}
    return tuple(wall for wall, is_behind in behind.items() if is_behind)


class Scene:
    def __init__(self, config):
        self.config = config
        self.parts = []
        rng = np.random.default_rng(config["seed"])

        table, room = config["table"], config["room"]
        floor_z = -table["height"]

        # Room: floor and four walls, with texture
        floor_tex, wall_tex = floor_texture(rng), wall_texture(rng)
        self.textures = {"floor": floor_tex, "wall": wall_tex}
        length, width, height = room["length"], room["width"], room["height"]
        # One texture covers the largest dimension of the room, so that it never repeats inside it
        room_scale = room_texture_scale(room, floor_tex)
        self._add((length + 0.2, width + 0.2, 0.1), make_transform(0, 0, floor_z - 0.05), texture=floor_tex, scale=room_scale)
        for wall, x in (("wall_3", -length / 2 - 0.05), ("wall_2", length / 2 + 0.05)):
            self._add((0.1, width + 0.2, height), make_transform(x, 0, floor_z + height / 2), texture=wall_tex, scale=room_scale, wall=wall)
        for wall, y in (("wall_1", -width / 2 - 0.05), ("wall_0", width / 2 + 0.05)):
            self._add((length + 0.2, 0.1, height), make_transform(0, y, floor_z + height / 2), texture=wall_tex, scale=room_scale, wall=wall)

        # Poster on the wall at +y. Seen from inside the room, x points right and z points up
        poster = config.get("poster")
        if poster:
            T = make_transform(poster["x"], width / 2 - 0.005, poster["z"])
            self.textures["poster"] = poster_texture(poster["text_lines"])
            self._add((poster["width"], 0.01, poster["height"]), T, texture=self.textures["poster"],
                      scale=poster["width"] / 1400, corner=(poster["x"] - poster["width"] / 2, poster["z"] + poster["height"] / 2),
                      wall="wall_0")

        # Table: top and four legs
        thickness = table["thickness"]
        self.textures["table"] = table_texture(rng)
        self._add((table["length"], table["width"], thickness), make_transform(0, 0, -thickness / 2),
                  texture=self.textures["table"], scale=0.002)
        leg = table["height"] - thickness
        for sx in (-1, 1):
            for sy in (-1, 1):
                T = make_transform(sx * (table["length"] / 2 - 0.06), sy * (table["width"] / 2 - 0.06), -thickness - leg / 2)
                self._add((0.05, 0.05, leg), T, color=(0.25, 0.22, 0.2))

        # Furniture: it gives geometry and texture to registration
        self.furniture = room_parts(config)
        for color, wall, mesh in self.furniture:
            self.parts.append((np.asarray(mesh.vertices, np.float32), np.asarray(mesh.triangles, np.uint32),
                               {"color": color, "texture": None, "scale": None, "corner": None}, wall))

        # Boxes, on the table or stacked on other boxes (z is the height of the base above the table top)
        self.boxes = []
        for box in config["boxes"]:
            T = box_transform(box)
            self._add((box["length"], box["width"], box["height"]), T, color=box["color"])
            self.boxes.append({"T_world_box": T, "x": box["x"], "y": box["y"], "z": box.get("z", 0.0),
                               "yaw_deg": box.get("yaw_deg", 0.0), "length": box["length"], "width": box["width"],
                               "height": box["height"], "color": box["color"]})

        # One ray casting scene for each set of hidden walls, built when needed
        self.views = {}
        self.raycaster, self.materials = self._view(())

    def _add(self, dimensions, T, color=None, texture=None, scale=None, corner=None, wall=None):
        vertices, triangles = cuboid(dimensions, T)
        self.parts.append((vertices, triangles, {"color": color, "texture": texture, "scale": scale, "corner": corner}, wall))

    def _view(self, hidden):
        if hidden not in self.views:
            raycaster = o3d.t.geometry.RaycastingScene()
            materials = {}
            for vertices, triangles, material, wall in self.parts:
                if wall not in hidden:
                    materials[raycaster.add_triangles(o3c.Tensor(vertices), o3c.Tensor(triangles))] = material
            self.views[hidden] = (raycaster, materials)
        return self.views[hidden]

    def _albedo(self, ids, points, normals, materials):
        albedo = np.zeros((*ids.shape, 3), np.float32)
        for geometry_id, material in materials.items():
            mask = ids == geometry_id
            if not mask.any():
                continue
            if material["texture"] is None:
                albedo[mask] = material["color"]
                continue
            if material["corner"] is not None:
                # Fixed mapping, so that the text of the poster is not mirrored or upside down
                u = (points[mask][:, 0] - material["corner"][0]) / material["scale"]
                v = (material["corner"][1] - points[mask][:, 2]) / material["scale"]
                albedo[mask] = sample_texture(material["texture"], u, v)
                continue
            # Projects the point onto the plane of the face: the normal axis is left out
            # The world origin falls in the middle of the texture, so the seam of the repetition stays far from it
            side = material["texture"].shape[0]
            p, axis = points[mask] / material["scale"] + side / 2, np.argmax(np.abs(normals[mask]), axis=1)
            u = np.where(axis == 0, p[:, 1], p[:, 0])
            v = np.where(axis == 2, p[:, 1], p[:, 2])
            albedo[mask] = sample_texture(material["texture"], u, v)
        return albedo

    def render(self, T_world_camera, K, width, height):
        """Casts one ray per pixel. Returns the color image and the depth, without noise."""
        u, v = np.meshgrid(np.arange(width, dtype=np.float32), np.arange(height, dtype=np.float32))
        # Direction in the camera frame, with z = 1: this way the ray's t is the depth itself
        directions = np.stack([(u - K[0, 2]) / K[0, 0], (v - K[1, 2]) / K[1, 1], np.ones_like(u)], axis=-1)
        directions = directions @ T_world_camera[:3, :3].T
        origin = np.broadcast_to(T_world_camera[:3, 3], directions.shape)
        rays = np.concatenate([origin, directions], axis=-1).astype(np.float32)
        raycaster, materials = self._view(hidden_walls(T_world_camera[:3, 3], self.config["room"]))
        answer = raycaster.cast_rays(o3c.Tensor(rays))

        t = answer["t_hit"].numpy()
        ids = answer["geometry_ids"].numpy()
        normals = answer["primitive_normals"].numpy()
        hit = ids != INVALID_ID
        depth = np.where(hit, t, 0.0).astype(np.float32)

        # The normal always points towards the camera
        normals = normals * np.where(np.sum(normals * directions, axis=-1, keepdims=True) > 0, -1.0, 1.0)
        points = origin + directions * np.where(hit, t, 0.0)[..., None]

        color = self._shade(points, normals, ids, raycaster, materials)
        color[~hit] = BACKGROUND
        return color, depth

    def _shade(self, points, normals, ids, raycaster, materials):
        light = self.config["light"]
        to_light = np.asarray(light["position"], np.float32) - points
        distance = np.linalg.norm(to_light, axis=-1, keepdims=True)
        lambert = np.clip(np.sum(normals * to_light / np.maximum(distance, 1e-6), axis=-1), 0, 1)

        # Shadows: a ray from the point to the light. If it hits something, the point is in shadow
        origins = points + 1e-3 * normals
        rays = np.concatenate([origins, np.asarray(light["position"]) - origins], axis=-1).astype(np.float32)
        shadow = raycaster.test_occlusions(o3c.Tensor(rays), tnear=1e-3, tfar=1.0).numpy()
        total_light = light["ambient"] + light["diffuse"] * lambert * (~shadow)
        color = self._albedo(ids, points, normals, materials) * total_light[..., None]
        return np.clip(color, 0, 1).astype(np.float32)


# --------------------------------------
# Noise
# --------------------------------------
def exposure(noise, seed, image):
    """Gain s and bias b of one image, as with automatic exposure: color = s * color + b.

    Each image has its own random generator, so that the window shows the same values the exported scene will have.
    """
    if not noise.get("exposure_changes", False):
        return 1.0, 0.0
    rng = np.random.default_rng([seed, image])
    return float(rng.normal(1.0, noise["gain_std"])), float(rng.normal(0.0, noise["bias_std"]))


def add_color_noise(color, noise, rng, misalignment, s=1.0, b=0.0):
    """Misalignment and blur mix the colors of neighboring objects near their boundaries. s and b come from exposure()."""
    if noise["blur_px"] > 0:
        color = cv2.GaussianBlur(color, (0, 0), noise["blur_px"])
    M = np.array([[1, 0, misalignment[0]], [0, 1, misalignment[1]]], np.float32)
    color = cv2.warpAffine(color, M, (color.shape[1], color.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    color = s * color + b + rng.normal(0, noise["color_std"], color.shape)
    return np.clip(color, 0, 1).astype(np.float32)


def add_depth_noise(z, noise, rng):
    """Noise that grows with the square of the distance, flying pixels and dropouts at edges."""
    kernel = np.ones((3, 3), np.uint8)
    zmin, zmax = cv2.erode(z, kernel), cv2.dilate(z, kernel)
    edge = (zmax - zmin) > noise["edge_threshold"]

    output = z + rng.normal(0, 1, z.shape) * noise["depth_std"] * z ** 2

    flying = edge & (rng.random(z.shape) < noise["flying_pixels"])
    output[flying] = (zmin + rng.random(z.shape) * (zmax - zmin))[flying]

    output[edge & (rng.random(z.shape) < noise["edge_dropouts"])] = 0.0
    output[(z <= 0) | (z > noise["max_depth"])] = 0.0
    return output.astype(np.float32)


# --------------------------------------
# Generation of a complete scene
# --------------------------------------
def intrinsics_matrix(intrinsics):
    return np.array([[intrinsics["fx"], 0, intrinsics["cx"]],
                     [0, intrinsics["fy"], intrinsics["cy"]],
                     [0, 0, 1]], np.float64)


def depth_to_point_cloud(z, rgb8, K):
    """Converts the depth image into a colored point cloud, in the camera frame."""
    v, u = np.nonzero(z > 0)
    depth = z[v, u]
    points = np.stack([(u - K[0, 2]) / K[0, 0] * depth, (v - K[1, 2]) / K[1, 1] * depth, depth], axis=-1)
    cloud = o3d.t.geometry.PointCloud()
    cloud.point.positions = o3c.Tensor(points.astype(np.float32))
    cloud.point.colors = o3c.Tensor(rgb8[v, u])
    return cloud


def write_scene(config, folder, with_noise=True, with_ground_truth=True):
    folder = Path(folder)
    (folder / "rgb").mkdir(parents=True, exist_ok=True)
    (folder / "point_clouds").mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(config["seed"] + 1)
    intrinsics = config["intrinsics"]
    K, width, height = intrinsics_matrix(intrinsics), intrinsics["width"], intrinsics["height"]
    scene = Scene(config)
    poses = camera_poses(config, rng)
    noise = config["noise"]

    # The misalignment between color and depth is a property of the camera: it is the same in all images
    angle = rng.uniform(0, 2 * np.pi)
    misalignment = noise["misalignment_px"] * np.array([np.cos(angle), np.sin(angle)])

    photometry = []
    for i, T in enumerate(poses):
        color, z = scene.render(T, K, width, height)
        s, b = 1.0, 0.0
        if with_noise:
            s, b = exposure(noise, config["seed"], i)
            color = add_color_noise(color, noise, rng, misalignment, s, b)
            z = add_depth_noise(z, noise, rng)
        photometry.append({"image": f"{i:03d}", "s": float(s), "b": float(b)})
        rgb8 = (color * 255 + 0.5).astype(np.uint8)
        cv2.imwrite(str(folder / "rgb" / f"{i:03d}.png"), rgb8[..., ::-1])
        o3d.t.io.write_point_cloud(str(folder / "point_clouds" / f"{i:03d}.ply"), depth_to_point_cloud(z, rgb8, K))

    (folder / "intrinsics.json").write_text(json.dumps(intrinsics, indent=2), encoding="utf-8")
    (folder / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    if with_ground_truth:
        T0_inv = np.linalg.inv(poses[0])
        ground_truth = {
            "cameras": [{"image": f"{i:03d}", "T_world_camera": T.tolist(), "T_camera0_camera": (T0_inv @ T).tolist()}
                        for i, T in enumerate(poses)],
            # x, y, yaw_deg: center and rotation of the box in the world (table) frame; z: height of its base above the table top
            "boxes": [{"x": b["x"], "y": b["y"], "z": b["z"], "yaw_deg": b["yaw_deg"],
                       "T_world_box": b["T_world_box"].tolist(), "T_camera0_box": (T0_inv @ b["T_world_box"]).tolist(),
                       "length": b["length"], "width": b["width"], "height": b["height"], "color": b["color"]}
                      for b in scene.boxes],
            "photometry": photometry,
            "with_noise": with_noise,
        }
        (folder / "ground_truth.json").write_text(json.dumps(ground_truth, indent=2), encoding="utf-8")
    return scene, poses


# --------------------------------------
# Frontend
# --------------------------------------
FOLDER = Path(__file__).parent
BOX_COLOR = [0.70, 0.53, 0.36]
# Camera axes: in the 3D view (OpenGL) y points up and z backwards; in the simulator y points down and z forward
GL_TO_CAMERA = np.diag([1.0, -1.0, -1.0, 1.0])
MODIFIER_KEYS = (int(gui.KeyName.LEFT_CONTROL), int(gui.KeyName.RIGHT_CONTROL), int(gui.KeyName.META))
QUIT_KEYS = (int(gui.KeyName.Q), int(gui.KeyName.W), int(gui.KeyName.E))
QUIT_KEY_SECONDS = 2.0
# 3D view: closest distance at which things are still drawn (meters), and vertical field of view
NEAR_CLIP = 0.02
# Turning the view with the mouse: elevation limit, so that the vertical stays defined, and closest pivot (meters)
ORBIT_MAX_ELEVATION = np.radians(85.0)
ORBIT_MIN_RADIUS = 0.2
VIEW_FOV_DEG = 49.0


def orbit_start(eye, forward, target):
    """Starts a turn around the point of the view axis closest to the target, so that the view does not jump.

    Returns the pivot, the distance to it, and the azimuth and elevation of the eye as seen from the pivot.
    """
    eye, forward = np.asarray(eye, float), np.asarray(forward, float)
    radius = max(float(np.dot(np.asarray(target, float) - eye, forward)), ORBIT_MIN_RADIUS)
    azimuth = float(np.arctan2(-forward[1], -forward[0]))
    elevation = float(np.clip(np.arcsin(np.clip(-forward[2], -1.0, 1.0)), -ORBIT_MAX_ELEVATION, ORBIT_MAX_ELEVATION))
    return eye + radius * forward, radius, azimuth, elevation


def orbit_eye(pivot, radius, azimuth, elevation):
    direction = np.array([np.cos(elevation) * np.cos(azimuth), np.cos(elevation) * np.sin(azimuth), np.sin(elevation)])
    return np.asarray(pivot, float) + radius * direction


def flat_shaded(mesh, color):
    """Without shared vertices, so that the faces do not look rounded in the 3D view."""
    vertices = np.asarray(mesh.vertices)[np.asarray(mesh.triangles)].reshape(-1, 3)
    triangles = np.arange(len(vertices)).reshape(-1, 3)
    flat = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(vertices), o3d.utility.Vector3iVector(triangles))
    flat.compute_vertex_normals()
    flat.paint_uniform_color(color)
    return flat


def cuboid_mesh(dimensions, T, color):
    return flat_shaded(block(dimensions, (0, 0, 0)).transform(T), color)


def textured_quad(origin, x_axis, y_axis, x_size, y_size, to_uv):
    """Rectangle facing the direction x_axis cross y_axis. to_uv gives the texture coordinates of a 3D point."""
    origin, x_axis, y_axis = np.asarray(origin, float), np.asarray(x_axis, float), np.asarray(y_axis, float)
    corners = [origin, origin + x_axis * x_size, origin + x_axis * x_size + y_axis * y_size, origin + y_axis * y_size]
    mesh = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(corners), o3d.utility.Vector3iVector([[0, 1, 2], [0, 2, 3]]))
    # The 3D view reads the images with v pointing up, while our textures have v pointing down
    uvs = [to_uv(corners[i]) for i in (0, 1, 2, 0, 2, 3)]
    mesh.triangle_uvs = o3d.utility.Vector2dVector([(u, 1 - v) for u, v in uvs])
    mesh.compute_vertex_normals()
    return mesh


def texture_material(texture):
    material = rendering.MaterialRecord()
    material.shader = "defaultUnlit"
    material.albedo_img = o3d.geometry.Image(np.ascontiguousarray((texture * 255).astype(np.uint8)))
    return material


CAMERA_COLOR = (0.9, 0.1, 0.1)
SELECTED_CAMERA_COLOR = (1.0, 0.65, 0.0)


def camera_lines(T, K, width, height, scale=0.12, color=CAMERA_COLOR):
    """Pyramid that represents a camera in the 3D view."""
    corners = [[0, 0], [width, 0], [width, height], [0, height]]
    points = [[0, 0, 0]] + [[(u - K[0, 2]) / K[0, 0] * scale, (v - K[1, 2]) / K[1, 1] * scale, scale] for u, v in corners]
    lines = [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [2, 3], [3, 4], [4, 1]]
    line_set = o3d.geometry.LineSet(o3d.utility.Vector3dVector(points), o3d.utility.Vector2iVector(lines))
    line_set.paint_uniform_color(color)
    line_set.transform(T)
    return line_set


class Frontend:
    def __init__(self, config):
        self.config = config
        self.poses = []
        self.current_image = -1  # image selected in the list of captured images
        self.camera_labels = []
        self.updating_list = False
        self.selected = 0 if config["boxes"] else -1

        self.window = gui.Application.instance.create_window("SAVIBoxes: simulator", 1500, 900)
        self.view = gui.SceneWidget()
        self.view.scene = rendering.Open3DScene(self.window.renderer)
        self.view.scene.set_background([BACKGROUND, BACKGROUND, BACKGROUND, 1.0])
        self.view.scene.set_lighting(rendering.Open3DScene.LightingProfile.NO_SHADOWS, (0.4, -0.5, -1.0))
        self.material = rendering.MaterialRecord()
        self.material.shader = "defaultLit"
        self.point_material = rendering.MaterialRecord()
        self.point_material.shader = "defaultUnlit"
        self.point_material.point_size = 3.0
        self.line_material = rendering.MaterialRecord()
        self.line_material.shader = "unlitLine"
        self.line_material.line_width = 2.0

        self._create_panel()
        self.window.set_on_layout(self._on_layout)
        self.modifier_time = None
        self.window.set_on_key(self._on_key)
        self.window.set_on_tick_event(self._on_tick)
        self.orbit = None
        self.view.set_on_mouse(self._on_mouse)
        self.window.add_child(self.view)
        self.window.add_child(self.panel)

        self._draw_environment()
        self._draw_boxes()
        room = self.config["room"]
        bounds = o3d.geometry.AxisAlignedBoundingBox([-room["length"] / 2, -room["width"] / 2, -self.config["table"]["height"]],
                                                     [room["length"] / 2, room["width"] / 2, room["height"]])
        self.view.setup_camera(VIEW_FOV_DEG, bounds, [0, 0, 0])
        self.view.look_at([0, 0, 0.05], [0.9, -1.1, 0.8], [0, 0, 1])
        self._set_clipping_planes()
        self._update_list()
        self._update_controls()

    def _on_mouse(self, event):
        """Dragging with the left button turns the view around the table, always with the vertical up.

        The other gestures (wheel, and dragging with Shift or Ctrl) are left to the 3D view.
        """
        ignored, consumed = gui.Widget.EventCallbackResult.IGNORED, gui.Widget.EventCallbackResult.CONSUMED
        if event.type == gui.MouseEvent.Type.BUTTON_DOWN:
            modifiers = (gui.KeyModifier.SHIFT, gui.KeyModifier.CTRL, gui.KeyModifier.ALT, gui.KeyModifier.META)
            if not event.is_button_down(gui.MouseButton.LEFT) or any(event.is_modifier_down(m) for m in modifiers):
                return ignored
            T = self._view_pose()
            pivot, radius, azimuth, elevation = orbit_start(T[:3, 3], T[:3, 2], self.config["cameras"]["target"])
            self.orbit = {"pivot": pivot, "radius": radius, "azimuth": azimuth, "elevation": elevation, "x": event.x, "y": event.y}
            return consumed
        if self.orbit is None:
            return ignored
        if event.type == gui.MouseEvent.Type.DRAG:
            # One drag along the height of the view is half a turn. The scene follows the mouse
            radians_per_pixel = np.pi / max(self.view.frame.height, 1)
            orbit = self.orbit
            orbit["azimuth"] -= (event.x - orbit["x"]) * radians_per_pixel
            orbit["elevation"] += (event.y - orbit["y"]) * radians_per_pixel
            orbit["elevation"] = float(np.clip(orbit["elevation"], -ORBIT_MAX_ELEVATION, ORBIT_MAX_ELEVATION))
            orbit["x"], orbit["y"] = event.x, event.y
            eye = orbit_eye(orbit["pivot"], orbit["radius"], orbit["azimuth"], orbit["elevation"])
            self.view.look_at(orbit["pivot"], eye, [0, 0, 1])
            self.window.post_redraw()
            return consumed
        if event.type == gui.MouseEvent.Type.BUTTON_UP:
            self.orbit = None
            return consumed
        return ignored

    def _on_tick(self):
        """Runs all the time, because the 3D view changes the camera by itself when it is moved."""
        redraw = False
        if abs(self.view.scene.camera.get_near() - NEAR_CLIP) > 1e-6:
            self._set_clipping_planes()
            redraw = True
        return self._update_walls() or redraw

    def _update_walls(self):
        """Hides the walls with the eye behind them, as in the captured images."""
        if self.show_cloud.checked:
            return False
        hidden = hidden_walls(self._view_pose()[:3, 3], self.config["room"])
        visible = {wall: wall not in hidden for wall in self.wall_parts}
        if visible == self.walls_visible:
            return False
        self.walls_visible = visible
        for wall, show in visible.items():
            for name in self.wall_parts[wall]:
                if self.view.scene.has_geometry(name):
                    self.view.scene.show_geometry(name, show)
        return True

    def _set_clipping_planes(self):
        """Keeps the near plane close to the eye, so that near objects do not disappear when the view gets close to them."""
        room = self.config["room"]
        rect = self.view.frame
        aspect = rect.width / rect.height if rect.height > 0 else 1.0
        far = 2 * max(room["length"], room["width"], room["height"])
        self.view.scene.camera.set_projection(VIEW_FOV_DEG, aspect, NEAR_CLIP, far, rendering.Camera.FovType.Vertical)

    def _on_key(self, event):
        """Ctrl+Q, Ctrl+W or Ctrl+E close the simulator (Cmd instead of Ctrl also works on the Mac)."""
        if event.key in MODIFIER_KEYS:
            self.modifier_time = time.time() if event.type == gui.KeyEvent.Type.DOWN else None
        elif event.type == gui.KeyEvent.Type.DOWN and event.key in QUIT_KEYS and self.modifier_time is not None:
            # The release of a modifier in another window never arrives here (Cmd+Tab), so an old press does not count
            if time.time() - self.modifier_time < QUIT_KEY_SECONDS:
                gui.Application.instance.quit()
                return True
        return False

    # --------------------------------------
    # Panel
    # --------------------------------------
    def _create_panel(self):
        em = self.window.theme.font_size
        # Scrollable, so that each widget keeps its size (a plain Vert squeezes the lists when the window is short)
        self.panel = gui.ScrollableVert(0.4 * em, gui.Margins(0.7 * em, 0.7 * em, 0.7 * em, 0.7 * em))

        self.panel.add_child(gui.Label("Boxes"))
        self.box_list = gui.ListView()
        self.box_list.set_max_visible_items(5)
        self.box_list.set_on_selection_changed(self._on_select)
        self.panel.add_child(self.box_list)
        self.panel.add_child(self._buttons(em, (("Add", self._add_box), ("Remove", self._remove_box),
                                                ("Stack", self._stack_box))))

        grid = gui.VGrid(2, 0.3 * em)
        self.controls = {}
        for key, text, minimum, maximum in (("x", "x (m)", -0.6, 0.6), ("y", "y (m)", -0.4, 0.4),
                                            ("z", "z, base (m)", 0.0, 0.6),
                                            ("yaw_deg", "rotation (deg)", -180.0, 180.0),
                                            ("length", "length (m)", 0.02, 0.6),
                                            ("width", "width (m)", 0.02, 0.6), ("height", "height (m)", 0.02, 0.6)):
            control = gui.Slider(gui.Slider.DOUBLE)
            control.set_limits(minimum, maximum)
            control.set_on_value_changed(lambda value, k=key: self._change(k, value))
            grid.add_child(gui.Label(text))
            grid.add_child(control)
            self.controls[key] = control
        self.color = gui.ColorEdit()
        self.color.set_on_value_changed(self._change_color)
        grid.add_child(gui.Label("color"))
        grid.add_child(self.color)
        self.panel.add_child(grid)
        self.panel.add_fixed(0.5 * em)

        self.panel.add_child(gui.Label("Cameras"))
        self.cameras_label = gui.Label("0 images captured")
        self.panel.add_child(self.cameras_label)
        self.panel.add_child(self._buttons(em, (("Capture", self._capture), ("Ring", self._ring), ("Clear", self._clear_cameras))))
        self.image_list = gui.ListView()
        self.image_list.set_max_visible_items(12)
        self.image_list.set_on_selection_changed(self._on_image_selected)
        self.panel.add_child(self.image_list)
        self.show_cloud = gui.Checkbox("Show point cloud of the selected image")
        self.show_cloud.set_on_checked(self._on_show_cloud)
        self.panel.add_child(self.show_cloud)
        self.image = gui.ImageWidget(o3d.geometry.Image(np.full((240, 320, 3), 230, np.uint8)))
        self.panel.add_child(self.image)
        self.panel.add_fixed(0.5 * em)

        self.panel.add_child(gui.Label("Export"))
        self.with_noise = gui.Checkbox("With noise")
        self.with_noise.checked = True
        self.panel.add_child(self.with_noise)
        self.exposure_changes = gui.Checkbox("Exposure changes")
        self.exposure_changes.checked = self.config["noise"].get("exposure_changes", False)
        self.exposure_changes.set_on_checked(self._on_exposure_changes)
        self.with_noise.set_on_checked(lambda checked: self._show_image())
        self.panel.add_child(self.exposure_changes)
        grid = gui.VGrid(2, 0.3 * em)
        self.scene_name = gui.TextEdit()
        self.scene_name.text_value = "new_scene"
        grid.add_child(gui.Label("name"))
        grid.add_child(self.scene_name)
        self.panel.add_child(grid)
        self.panel.add_child(self._buttons(em, (("Export scene", self._export), ("Open config", self._open), ("Save config", self._save_config))))
        self.message = gui.Label("")
        self.panel.add_child(self.message)

    @staticmethod
    def _buttons(em, definitions):
        row = gui.Horiz(0.4 * em)
        for text, function in definitions:
            button = gui.Button(text)
            button.set_on_clicked(function)
            row.add_child(button)
        return row

    def _on_layout(self, context):
        r = self.window.content_rect
        panel_width = 28 * self.window.theme.font_size
        self.view.frame = gui.Rect(r.x, r.y, r.width - panel_width, r.height)
        self.panel.frame = gui.Rect(r.get_right() - panel_width, r.y, panel_width, r.height)
        self._set_clipping_planes()

    def _update_list(self):
        self.box_list.set_items([f"Box {i + 1}" for i in range(len(self.config["boxes"]))])
        if self.selected >= 0:
            self.box_list.selected_index = self.selected

    def _update_controls(self):
        active = self.selected >= 0
        for key, control in self.controls.items():
            control.enabled = active
            if active:
                control.double_value = self.config["boxes"][self.selected].get(key, 0.0)
        self.color.enabled = active
        if active:
            self.color.color_value = gui.Color(*self.config["boxes"][self.selected]["color"])

    def _on_select(self, _text, _double_click):
        self.selected = self.box_list.selected_index
        self._update_controls()

    # --------------------------------------
    # Boxes
    # --------------------------------------
    def _add_box(self):
        n = len(self.config["boxes"])
        self.config["boxes"].append({"x": 0.05 * n, "y": 0.05 * n, "z": 0.0, "yaw_deg": 0.0, "length": 0.25, "width": 0.18,
                                     "height": 0.15, "color": list(BOX_COLOR)})
        self.selected = n
        self._update_list()
        self._update_controls()
        self._draw_boxes()

    def _stack_box(self):
        """Sets the z of the selected box so that it rests on the highest box under its center (or on the table)."""
        if self.selected < 0:
            return
        z = box_top_below(self.config["boxes"], self.selected)
        self.config["boxes"][self.selected]["z"] = z
        self.controls["z"].double_value = z
        self.message.text = f"Box {self.selected + 1}: z = {z:.3f} m"
        self._draw_boxes()

    def _remove_box(self):
        if self.selected < 0:
            return
        del self.config["boxes"][self.selected]
        self.selected = min(self.selected, len(self.config["boxes"]) - 1)
        self._update_list()
        self._update_controls()
        self._draw_boxes()

    def _change(self, key, value):
        if self.selected >= 0:
            self.config["boxes"][self.selected][key] = float(value)
            self._draw_boxes()

    def _change_color(self, color):
        if self.selected >= 0:
            self.config["boxes"][self.selected]["color"] = [float(color.red), float(color.green), float(color.blue)]
            self._draw_boxes()

    # --------------------------------------
    # Drawing in the 3D view
    # --------------------------------------
    def _draw_environment(self):
        """Same room as in the captured images."""
        scene = self.view.scene
        self.walls_visible = {}
        self.wall_parts = {f"wall_{i}": [f"wall_{i}"] for i in range(4)}
        self.wall_parts["wall_0"].append("poster")
        table, room = self.config["table"], self.config["room"]
        thickness, floor_z = table["thickness"], -table["height"]
        length, width, height = room["length"], room["width"], room["height"]
        room_scene = Scene(self.config)
        textures = room_scene.textures
        size = textures["wall"].shape[0]
        floor_scale, table_scale = room_texture_scale(room, textures["wall"]) * size, 0.002 * size

        floor_uv = lambda p: (p[0] / floor_scale + 0.5, p[1] / floor_scale + 0.5)
        wall_x_uv = lambda p: (p[1] / floor_scale + 0.5, p[2] / floor_scale + 0.5)
        wall_y_uv = lambda p: (p[0] / floor_scale + 0.5, p[2] / floor_scale + 0.5)
        table_uv = lambda p: (p[0] / table_scale + 0.5, p[1] / table_scale + 0.5)

        scene.add_geometry("floor", textured_quad((-length / 2, -width / 2, floor_z), (1, 0, 0), (0, 1, 0), length, width, floor_uv),
                           texture_material(textures["floor"]))
        wall_material = texture_material(textures["wall"])
        walls = (((-length / 2, width / 2, floor_z), (1, 0, 0), length, wall_y_uv),
                 ((length / 2, -width / 2, floor_z), (-1, 0, 0), length, wall_y_uv),
                 ((length / 2, width / 2, floor_z), (0, -1, 0), width, wall_x_uv),
                 ((-length / 2, -width / 2, floor_z), (0, 1, 0), width, wall_x_uv))
        for i, (origin, axis, size_along, to_uv) in enumerate(walls):
            scene.add_geometry(f"wall_{i}", textured_quad(origin, axis, (0, 0, 1), size_along, height, to_uv), wall_material)

        poster = self.config.get("poster")
        if poster:
            left, top = poster["x"] - poster["width"] / 2, poster["z"] + poster["height"] / 2
            poster_uv = lambda p: ((p[0] - left) / poster["width"], (top - p[2]) / poster["height"])
            quad = textured_quad((left, width / 2 - 0.01, poster["z"] - poster["height"] / 2), (1, 0, 0), (0, 0, 1),
                                 poster["width"], poster["height"], poster_uv)
            scene.add_geometry("poster", quad, texture_material(textures["poster"]))

        scene.add_geometry("table", cuboid_mesh((table["length"], table["width"], thickness),
                                                make_transform(0, 0, -thickness / 2 - 0.001), [0.78, 0.82, 0.8]), self.material)
        scene.add_geometry("table_top", textured_quad((-table["length"] / 2, -table["width"] / 2, 0.0), (1, 0, 0), (0, 1, 0),
                                                      table["length"], table["width"], table_uv), texture_material(textures["table"]))
        leg = table["height"] - thickness
        for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
            T = make_transform(sx * (table["length"] / 2 - 0.06), sy * (table["width"] / 2 - 0.06), -thickness - leg / 2)
            scene.add_geometry(f"leg_{i}", cuboid_mesh((0.05, 0.05, leg), T, [0.25, 0.22, 0.2]), self.material)
        for i, (color, wall, mesh) in enumerate(room_scene.furniture):
            scene.add_geometry(f"furniture_{i}", flat_shaded(mesh, color), self.material)
            if wall:
                self.wall_parts[wall].append(f"furniture_{i}")

    def _draw_boxes(self):
        scene = self.view.scene
        for i in range(32):
            if scene.has_geometry(f"box_{i}"):
                scene.remove_geometry(f"box_{i}")
        for i, b in enumerate(self.config["boxes"]):
            scene.add_geometry(f"box_{i}", cuboid_mesh((b["length"], b["width"], b["height"]), box_transform(b), b["color"]),
                               self.material)
        if self.show_cloud.checked:
            self._show_image()

    def _draw_cameras(self):
        scene = self.view.scene
        for i in range(256):
            if scene.has_geometry(f"camera_{i}"):
                scene.remove_geometry(f"camera_{i}")
        for label in self.camera_labels:
            self.view.remove_3d_label(label)
        self.camera_labels = []
        intrinsics = self.config["intrinsics"]
        for i, T in enumerate(self.poses):
            color = SELECTED_CAMERA_COLOR if i == self.current_image else CAMERA_COLOR
            lines = camera_lines(T, intrinsics_matrix(intrinsics), intrinsics["width"], intrinsics["height"], color=color)
            scene.add_geometry(f"camera_{i}", lines, self.line_material)
            # The number of the image, a little above the camera (the y axis of the camera points down)
            label = self.view.add_3d_label((T[:3, 3] - 0.04 * T[:3, 1]).astype(np.float32), f"{i:03d}")
            label.color = gui.Color(*color)
            self.camera_labels.append(label)
        self.cameras_label.text = f"{len(self.poses)} images captured"
        self.updating_list = True  # changing the list from the code is not a click
        self.image_list.set_items([f"Image {i:03d}" for i in range(len(self.poses))])
        if 0 <= self.current_image < len(self.poses):
            self.image_list.selected_index = self.current_image
        self.updating_list = False

    # --------------------------------------
    # Cameras
    # --------------------------------------
    def _view_pose(self):
        view = np.array(self.view.scene.camera.get_view_matrix(), float)
        return np.linalg.inv(view) @ GL_TO_CAMERA

    def _capture(self):
        pose = self._view_pose()
        self.poses.append(pose)
        self._show_image(len(self.poses) - 1)

    def _ring(self):
        """Adds the poses in a circle defined in the configuration."""
        rng = np.random.default_rng(self.config["seed"])
        base = {k: v for k, v in self.config["cameras"].items() if k != "poses"}
        self.poses += camera_poses({"cameras": base}, rng)
        self._show_image(len(self.poses) - 1)

    def _clear_cameras(self):
        self.poses = []
        self.current_image = -1
        self._draw_cameras()
        if self.view.scene.has_geometry("point_cloud"):
            self.view.scene.remove_geometry("point_cloud")

    def _on_image_selected(self, text, double_click):
        if not self.updating_list:
            self._go_to_image(self.image_list.selected_index)

    def _go_to_image(self, image):
        """Moves the 3D view to the viewpoint of a captured image, and shows that image."""
        if not 0 <= image < len(self.poses):
            return
        T = self.poses[image]
        eye, forward, up = T[:3, 3], T[:3, 2], -T[:3, 1]  # the y axis of the camera points down
        self.view.look_at(eye + forward, eye, up)
        self._show_image(image)

    def _show_image(self, image=None):
        """Shows a captured image, with the exposure it will have in the exported scene, and highlights its camera.

        By default, it shows the image selected in the list.
        """
        if not self.poses:
            return
        intrinsics = self.config["intrinsics"]
        image = self.current_image if image is None else image
        image = image if 0 <= image < len(self.poses) else len(self.poses) - 1
        self.current_image = image
        self._draw_cameras()
        T, K, noise = self.poses[image], intrinsics_matrix(intrinsics), self.config["noise"]
        color, z = Scene(self.config).render(T, K, intrinsics["width"], intrinsics["height"])
        if self.with_noise.checked:
            # Same exposure as in the exported scene. The other noise is random, as in any acquisition
            s, b = exposure(noise, self.config["seed"], image)
            rng = np.random.default_rng([self.config["seed"], image, 1])
            angle = rng.uniform(0, 2 * np.pi)
            misalignment = noise["misalignment_px"] * np.array([np.cos(angle), np.sin(angle)])
            color = add_color_noise(color, noise, rng, misalignment, s, b)
            z = add_depth_noise(z, noise, rng)
            if noise.get("exposure_changes", False):
                self.message.text = f"Image {image:03d}: s = {s:.2f}, b = {b:+.2f}"
        rgb8 = (color * 255 + 0.5).astype(np.uint8)
        self.image.update_image(o3d.geometry.Image(np.ascontiguousarray(rgb8[::2, ::2])))
        if self.show_cloud.checked:
            cloud = depth_to_point_cloud(z, rgb8, K).to_legacy().transform(T)
            if self.view.scene.has_geometry("point_cloud"):
                self.view.scene.remove_geometry("point_cloud")
            self.view.scene.add_geometry("point_cloud", cloud, self.point_material)
            self._show_scene(False)

    def _scene_names(self):
        """Names of the meshes of the room, the table and the boxes in the 3D view."""
        names = ["floor", "poster", "table", "table_top"] + [f"wall_{i}" for i in range(4)] + [f"leg_{i}" for i in range(4)]
        names += [f"furniture_{i}" for i in range(256)] + [f"box_{i}" for i in range(32)]
        return [name for name in names if self.view.scene.has_geometry(name)]

    def _show_scene(self, show):
        for name in self._scene_names():
            self.view.scene.show_geometry(name, show)
        self.walls_visible = {}  # the walls are checked again on the next tick

    def _on_show_cloud(self, checked):
        """Replaces the room, the table and the boxes by the point cloud of the selected image, in the world frame."""
        if checked:
            self._show_image()
        else:
            if self.view.scene.has_geometry("point_cloud"):
                self.view.scene.remove_geometry("point_cloud")
            self._show_scene(True)

    # --------------------------------------
    # Files
    # --------------------------------------
    def _config_to_export(self):
        config = copy.deepcopy(self.config)
        config["name"] = self.scene_name.text_value
        config["cameras"]["poses"] = [{"T_world_camera": T.tolist()} for T in self.poses]
        return config

    def _on_exposure_changes(self, checked):
        """Each image gets its own brightness and contrast (gain_std, bias_std), as with automatic exposure."""
        self.config["noise"]["exposure_changes"] = checked
        self._show_image()

    def _export(self):
        if not self.poses:
            self.message.text = "Capture at least one image first."
            return
        config = self._config_to_export()
        write_scene(config, FOLDER / "scenes" / config["name"], with_noise=self.with_noise.checked)
        self.message.text = f"Exported to scenes/{config['name']}"

    def _save_config(self):
        dialog = gui.FileDialog(gui.FileDialog.SAVE, "Save configuration", self.window.theme)
        dialog.set_path(str(FOLDER / "configs" / f"{self.scene_name.text_value}.json"))
        dialog.add_filter(".json", "Configuration (.json)")
        dialog.set_on_cancel(self.window.close_dialog)
        dialog.set_on_done(self._on_save)
        self.window.show_dialog(dialog)

    def _on_save(self, path):
        self.window.close_dialog()
        Path(path).write_text(json.dumps(self._config_to_export(), indent=2), encoding="utf-8")
        self.message.text = f"Saved: {Path(path).name}"

    def _open(self):
        dialog = gui.FileDialog(gui.FileDialog.OPEN, "Open configuration", self.window.theme)
        dialog.set_path(str(FOLDER / "configs"))
        dialog.add_filter(".json", "Configuration (.json)")
        dialog.set_on_cancel(self.window.close_dialog)
        dialog.set_on_done(self._on_open)
        self.window.show_dialog(dialog)

    def _on_open(self, path):
        self.window.close_dialog()
        self.config = read_config(path)
        self.scene_name.text_value = self.config["name"]
        self.exposure_changes.checked = self.config["noise"].get("exposure_changes", False)
        self.poses = [pose_from_config(p) for p in self.config["cameras"].get("poses", [])]
        self.current_image = -1
        self.selected = 0 if self.config["boxes"] else -1
        self.view.scene.clear_geometry()
        self._draw_environment()
        self._draw_boxes()
        self._draw_cameras()
        self._update_list()
        self._update_controls()


def self_test(frontend):
    """Goes through the frontend without intervention, to confirm that everything works."""
    app = gui.Application.instance
    window = frontend.window

    def step(function, wait=0.6):
        app.post_to_main_thread(window, function)
        time.sleep(wait)

    def move():
        frontend._change("x", 0.2)
        frontend._change("yaw_deg", 35.0)
        frontend.controls["x"].double_value = 0.2
        frontend.controls["yaw_deg"].double_value = 35.0

    def export():
        frontend.scene_name.text_value = "self_test"
        frontend._export()

    def report():
        print("EYE", frontend._view_pose()[:3, 3].round(3), "expected", frontend.poses[1][:3, 3].round(3), flush=True)
        print("SELF TEST:", frontend.message.text, len(frontend.poses), "poses", flush=True)

    time.sleep(2.0)
    step(frontend._add_box)
    step(move)
    step(frontend._capture, 1.0)
    step(lambda: frontend.view.look_at([0, 0, 0.05], [-1.0, -0.9, 0.7], [0, 0, 1]))
    step(frontend._capture, 1.0)
    step(frontend._ring, 1.0)
    step(export, 3.0)
    step(report)
    app.post_to_main_thread(window, app.quit)


def generate_scenes(args):
    for path in args.batch:
        if Path(path).name == "base.json":
            continue
        config = read_config(path)
        if args.exposure_changes:
            config["noise"]["exposure_changes"] = True
        name = config["name"] + ("_no_noise" if args.no_noise else "") + ("_exposure" if args.exposure_changes else "")
        folder = Path(args.output) / name
        _, poses = write_scene(config, folder, with_noise=not args.no_noise, with_ground_truth=not args.no_ground_truth)
        print(f"{name}: {len(poses)} images in {folder}")


def open_frontend(args):
    gui.Application.instance.initialize()
    frontend = Frontend(read_config(args.config))
    if args.self_test:
        threading.Thread(target=self_test, args=(frontend,), daemon=True).start()
    gui.Application.instance.run()


def main():
    # The window's loop runs outside Python, so without this Ctrl+C in the terminal would do nothing
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=str(FOLDER / "configs" / "base.json"), help="initial configuration of the window")
    parser.add_argument("--batch", nargs="+", metavar="CONFIG", help="generates scenes from configuration files, without a window")
    parser.add_argument("--output", default=str(FOLDER / "scenes"), help="folder where --batch writes the scenes")
    parser.add_argument("--no_noise", action="store_true", help="--batch generates the images without noise")
    parser.add_argument("--exposure_changes", action="store_true", help="--batch gives each image its own brightness and contrast")
    parser.add_argument("--no_ground_truth", action="store_true", help="--batch does not write ground_truth.json (test scenes)")
    parser.add_argument("--self_test", action="store_true", help="goes through the window automatically and exits")
    args = parser.parse_args()

    if args.batch:
        generate_scenes(args)
    else:
        open_frontend(args)


if __name__ == "__main__":
    main()

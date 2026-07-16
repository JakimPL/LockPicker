import argparse
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

PPU = 72.0
BOARD_PX_W = 1000.0
BOARD_PX_H = 800.0
BAR_W_PX = 80.0
BAR_PITCH_PX = 85.0
X_OFFSET_PX = 150.0
MAX_HEIGHT = 11.0
BOARD_W = BOARD_PX_W / PPU
BOARD_H = BOARD_PX_H / PPU
COL_W = BAR_W_PX / PPU
PIN_W = COL_W - 0.07
PIN_D = 0.5
PLATE_FACE_Y = -0.15
PLATE_BACK_Y = 0.55
COLUMNS = 7
PICK_TIP = 20.0 / PPU
PICK_SHAFT_R = 0.07

HEX = {
    "chamber_shadow": "2A2622",
    "chamber_dark": "1E1B18",
    "plate": "211E1B",
    "plate_dark": "161311",
    "bore": "0A0807",
    "key": "FFC98A",
    "fill": "4A5560",
    "hover": "FFD9A0",
    "enamel": "8E2F2B",
    "steel": "8C9298",
    "steel_hi": "E8EDF2",
    "brass": "C9A24B",
    "brass_hi": "F2D98C",
    "copper": "B26E4F",
    "copper_hi": "E8A87C",
    "patina": "4E7C6B",
    "jam": "6E6E82",
    "pick": "56687E",
    "pick_hi": "9FB4CC",
    "grip_a": "AFC5AF",
    "grip_b": "C5AFAF",
    "rosette": "3E4348",
    "rim": "BFD4E8",
}

LEVEL = [
    (0, True, 4, "steel", None),
    (0, False, 3, "brass", None),
    (1, True, 6, "steel", "master"),
    (1, False, 2, "copper", None),
    (2, True, 3, "brass", "hover"),
    (2, False, 5, "steel", None),
    (3, True, 5, "copper", "jam"),
    (3, False, 4, "brass", None),
    (4, True, 2, "steel", None),
    (4, False, 6, "copper", "master"),
    (5, False, 7, "steel", None),
    (6, True, 8, "brass", None),
    (6, False, 1, "steel", None),
]


def srgb_channel(v):
    c = v / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(code, alpha=1.0):
    r, g, b = (int(code[i : i + 2], 16) for i in (0, 2, 4))
    return (srgb_channel(r), srgb_channel(g), srgb_channel(b), alpha)


def hex_scale(code, factor):
    parts = []
    for i in (0, 2, 4):
        parts.append(f"{min(255, int(int(code[i:i + 2], 16) * factor)):02X}")
    return "".join(parts)


def hex_mult(code, mult):
    parts = []
    for i in (0, 2, 4):
        v = int(code[i : i + 2], 16) * int(mult[i : i + 2], 16) // 255
        parts.append(f"{v:02X}")
    return "".join(parts)


def lerp_lin(a, b, t, gain=1.0):
    return tuple(min(1.0, (a[i] + (b[i] - a[i]) * t) * gain) for i in range(3)) + (1.0,)


def px_to_x(px):
    return (px - BOARD_PX_W / 2) / PPU


def column_center_px(pos):
    return X_OFFSET_PX + pos * BAR_PITCH_PX + BAR_W_PX / 2


def sk(node, ident, out=False):
    for s in node.outputs if out else node.inputs:
        if s.identifier == ident:
            return s
    raise KeyError(ident)


def new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    return mat, nt, bsdf


def add_roughness(nt, bsdf, rough, spread=0.05, brushed=0.05):
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 14.0
    noise.inputs["Detail"].default_value = 6.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = max(rough - spread, 0.03)
    mr.inputs["To Max"].default_value = min(rough + spread, 1.0)
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (25.0, 25.0, 1.2)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    streaks = nt.nodes.new("ShaderNodeTexNoise")
    streaks.inputs["Scale"].default_value = 1.0
    streaks.inputs["Detail"].default_value = 4.0
    nt.links.new(mapping.outputs["Vector"], streaks.inputs["Vector"])
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = 0.5
    nt.links.new(streaks.outputs["Fac"], sub.inputs[0])
    scale = nt.nodes.new("ShaderNodeMath")
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = brushed
    nt.links.new(sub.outputs[0], scale.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(mr.outputs["Result"], add.inputs[0])
    nt.links.new(scale.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], bsdf.inputs["Roughness"])


def mix_rgb(nt, a_color, b_color):
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.clamp_factor = True
    if a_color is not None:
        sk(mix, "A_Color").default_value = a_color
    if b_color is not None:
        sk(mix, "B_Color").default_value = b_color
    return mix


def add_edge_wear(nt, base_color, hi_color, start=0.6, end=0.74, strength=0.85):
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = start
    ramp.color_ramp.elements[1].position = end
    nt.links.new(geo.outputs["Pointiness"], ramp.inputs["Fac"])
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    fac.inputs[1].default_value = strength
    nt.links.new(ramp.outputs["Color"], fac.inputs[0])
    mix = mix_rgb(nt, base_color, hi_color)
    nt.links.new(fac.outputs[0], sk(mix, "Factor_Float"))
    return mix


def add_bevel(nt, bsdf, radius=0.02):
    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 4
    bevel.inputs["Radius"].default_value = radius
    nt.links.new(bevel.outputs["Normal"], bsdf.inputs["Normal"])


def metal_mat(name, base_code, hi_code, rough, patina=False, hover=False, jam=False):
    if jam:
        base_code = hex_mult(base_code, HEX["jam"])
        hi_code = hex_mult(hi_code, HEX["jam"])
        rough = min(rough + 0.15, 0.9)
    base = hex_lin(base_code)
    hi = hex_lin(hi_code)
    mat, nt, bsdf = new_mat(name)
    bsdf.inputs["Metallic"].default_value = 1.0
    add_roughness(nt, bsdf, rough)
    add_bevel(nt, bsdf)
    wear = add_edge_wear(nt, base, hi)
    if patina:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.34
        ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
        ramp.color_ramp.elements[1].position = 0.47
        ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
        nt.links.new(geo.outputs["Pointiness"], ramp.inputs["Fac"])
        pat = mix_rgb(nt, base, hex_lin(HEX["patina"]))
        nt.links.new(ramp.outputs["Color"], sk(pat, "Factor_Float"))
        nt.links.new(sk(pat, "Result_Color", out=True), sk(wear, "A_Color"))
    nt.links.new(sk(wear, "Result_Color", out=True), bsdf.inputs["Base Color"])
    if hover:
        bsdf.inputs["Emission Color"].default_value = hex_lin(HEX["hover"])
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.65
        power = nt.nodes.new("ShaderNodeMath")
        power.operation = "POWER"
        power.inputs[1].default_value = 3.0
        nt.links.new(lw.outputs["Facing"], power.inputs[0])
        gain = nt.nodes.new("ShaderNodeMath")
        gain.operation = "MULTIPLY"
        gain.inputs[1].default_value = 2.2
        nt.links.new(power.outputs[0], gain.inputs[0])
        nt.links.new(gain.outputs[0], bsdf.inputs["Emission Strength"])
    return mat


def plate_mat(name):
    base = hex_lin(HEX["plate"])
    dark = hex_lin(HEX["plate_dark"])
    key = hex_lin(HEX["key"])
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    nt.nodes.remove(bsdf)
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mottle = nt.nodes.new("ShaderNodeTexNoise")
    mottle.inputs["Scale"].default_value = 3.5
    mottle.inputs["Detail"].default_value = 8.0
    mix_dark = mix_rgb(nt, base, dark)
    nt.links.new(mottle.outputs["Fac"], sk(mix_dark, "Factor_Float"))
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    rim_ramp = nt.nodes.new("ShaderNodeValToRGB")
    rim_ramp.color_ramp.elements[0].position = 0.65
    rim_ramp.color_ramp.elements[1].position = 0.78
    nt.links.new(geo.outputs["Pointiness"], rim_ramp.inputs["Fac"])
    rim_fac = nt.nodes.new("ShaderNodeMath")
    rim_fac.operation = "MULTIPLY"
    rim_fac.inputs[1].default_value = 0.5
    nt.links.new(rim_ramp.outputs["Color"], rim_fac.inputs[0])
    rim_mix = mix_rgb(nt, None, lerp_lin(base, key, 0.5, gain=1.6))
    nt.links.new(sk(mix_dark, "Result_Color", out=True), sk(rim_mix, "A_Color"))
    nt.links.new(rim_fac.outputs[0], sk(rim_mix, "Factor_Float"))
    coord = nt.nodes.new("ShaderNodeTexCoord")
    pool_map = nt.nodes.new("ShaderNodeMapping")
    pool_map.inputs["Location"].default_value = (0.58, -0.1, -0.58)
    pool_map.inputs["Scale"].default_value = (0.18, 0.18, 0.18)
    nt.links.new(coord.outputs["Object"], pool_map.inputs["Vector"])
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    nt.links.new(pool_map.outputs["Vector"], grad.inputs["Vector"])
    pool_fac = nt.nodes.new("ShaderNodeMath")
    pool_fac.operation = "MULTIPLY"
    pool_fac.inputs[1].default_value = 0.4
    nt.links.new(grad.outputs["Fac"], pool_fac.inputs[0])
    pool_mix = mix_rgb(nt, None, lerp_lin(base, key, 0.45, gain=1.6))
    nt.links.new(sk(rim_mix, "Result_Color", out=True), sk(pool_mix, "A_Color"))
    nt.links.new(pool_fac.outputs[0], sk(pool_mix, "Factor_Float"))
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs["Vector"])
    depth = nt.nodes.new("ShaderNodeMapRange")
    depth.inputs["From Min"].default_value = -0.1
    depth.inputs["From Max"].default_value = 0.35
    nt.links.new(sep.outputs["Y"], depth.inputs["Value"])
    depth_mix = mix_rgb(nt, None, hex_lin("070606"))
    nt.links.new(sk(pool_mix, "Result_Color", out=True), sk(depth_mix, "A_Color"))
    nt.links.new(depth.outputs["Result"], sk(depth_mix, "Factor_Float"))
    nt.links.new(sk(depth_mix, "Result_Color", out=True), emit.inputs["Color"])
    return mat


def bore_mat(name):
    mat, nt, bsdf = new_mat(name)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.05
    bsdf.inputs["Base Color"].default_value = hex_lin(HEX["bore"])
    add_roughness(nt, bsdf, 0.85, spread=0.08, brushed=0.2)
    return mat


def enamel_mat(name):
    mat, nt, bsdf = new_mat(name)
    bsdf.inputs["Base Color"].default_value = hex_lin(HEX["enamel"])
    bsdf.inputs["Roughness"].default_value = 0.12
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.08
    return mat


def grip_mat(name, code):
    mat, nt, bsdf = new_mat(name)
    bsdf.inputs["Base Color"].default_value = hex_lin(code)
    bsdf.inputs["Roughness"].default_value = 0.65
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 25.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def build_materials():
    mats = {}
    mats["steel"] = metal_mat("pin_steel", HEX["steel"], HEX["steel_hi"], 0.18)
    mats["brass"] = metal_mat("pin_brass", HEX["brass"], HEX["brass_hi"], 0.28)
    mats["copper"] = metal_mat("pin_copper", HEX["copper"], HEX["copper_hi"], 0.33, patina=True)
    mats["brass_hover"] = metal_mat("pin_brass_hover", HEX["brass"], HEX["brass_hi"], 0.28, hover=True)
    mats["copper_jam"] = metal_mat("pin_copper_jam", HEX["copper"], HEX["copper_hi"], 0.33, patina=True, jam=True)
    mats["frame"] = plate_mat("frame_plate")
    mats["bore"] = bore_mat("bore_iron")
    mats["enamel"] = enamel_mat("badge_enamel")
    mats["rosette"] = metal_mat("badge_rosette", HEX["rosette"], HEX["steel"], 0.4)
    mats["pick"] = metal_mat("pick_steel", HEX["pick"], HEX["pick_hi"], 0.15)
    mats["ferrule"] = metal_mat("pick_ferrule", HEX["brass"], HEX["brass_hi"], 0.35)
    mats["grip_a"] = grip_mat("pick_grip_a", hex_scale(HEX["grip_a"], 0.75))
    mats["grip_b"] = grip_mat("pick_grip_b", hex_scale(HEX["grip_b"], 0.75))
    return mats


def obj_from_bm(name, bm, collection, materials=()):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for mat in materials:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def add_box(bm, size, center):
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    bmesh.ops.scale(bm, vec=Vector(size), verts=verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    return verts


def tag_new_faces(bm, index):
    for face in bm.faces:
        if not face.tag:
            face.material_index = index
            face.tag = True


def build_pin(name, upper, collection, material):
    bm = bmesh.new()
    d = 1.0 if upper else -1.0
    add_box(bm, (PIN_W, PIN_D, MAX_HEIGHT), (0.0, PIN_D / 2, d * MAX_HEIGHT / 2))
    long_edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > MAX_HEIGHT - 1e-3]
    front_edges = [e for e in long_edges if all(v.co.y < 0.01 for v in e.verts)]
    back_edges = [e for e in long_edges if all(v.co.y > PIN_D - 0.01 for v in e.verts)]
    bmesh.ops.bevel(
        bm,
        geom=front_edges,
        offset=0.24,
        offset_type="OFFSET",
        segments=5,
        profile=0.5,
        affect="EDGES",
        clamp_overlap=True,
    )
    bmesh.ops.bevel(
        bm,
        geom=back_edges,
        offset=0.06,
        offset_type="OFFSET",
        segments=2,
        profile=0.7,
        affect="EDGES",
        clamp_overlap=True,
    )
    tip_edges = [e for e in bm.edges if all(abs(v.co.z) < 1e-4 for v in e.verts)]
    bmesh.ops.bevel(
        bm,
        geom=tip_edges,
        offset=0.12,
        offset_type="OFFSET",
        segments=3,
        profile=0.7,
        affect="EDGES",
        clamp_overlap=True,
    )
    collar_verts = add_box(bm, (PIN_W + 0.06, PIN_D + 0.04, 0.22), (0.0, PIN_D / 2, d * 0.82))
    collar_edges = {e for v in collar_verts for e in v.link_edges}
    bmesh.ops.bevel(
        bm,
        geom=list(collar_edges),
        offset=0.03,
        offset_type="OFFSET",
        segments=2,
        profile=0.7,
        affect="EDGES",
        clamp_overlap=True,
    )
    return obj_from_bm(name, bm, collection, [material])


def build_frame(collection, material, columns):
    bm = bmesh.new()
    w = BOARD_W + 4.0
    h = BOARD_H + 4.0
    depth = PLATE_BACK_Y - PLATE_FACE_Y
    add_box(bm, (w, depth, h), (0.0, PLATE_FACE_Y + depth / 2, 0.0))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=48, use_grid_fill=True)
    obj = obj_from_bm("frame_plate", bm, collection, [material])
    cutter_bm = bmesh.new()
    for pos in range(columns):
        cx = px_to_x(column_center_px(pos))
        add_box(cutter_bm, (COL_W + 0.04, depth + 0.4, h + 0.2), (cx, PLATE_FACE_Y + depth / 2, 0.0))
    cutter = obj_from_bm("frame_slots_cut", cutter_bm, collection)
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    mod = obj.modifiers.new("slots", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "EXACT"
    return obj


def build_screws(collection, mats):
    bm = bmesh.new()
    rot_x = Matrix.Rotation(math.pi / 2, 3, "X")
    positions = [
        (-5.9, 4.6, 0.3),
        (-5.9, 0.0, 1.2),
        (-5.9, -4.6, 2.4),
        (5.15, 4.6, 0.9),
        (5.15, 0.0, 1.9),
        (5.15, -4.6, 0.1),
    ]
    for x, z, angle in positions:
        head = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.13, radius2=0.115, depth=0.07)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_x, verts=head["verts"])
        bmesh.ops.translate(bm, vec=Vector((x, -0.165, z)), verts=head["verts"])
        tag_new_faces(bm, 0)
        slot = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.22, 0.05, 0.045)), verts=slot["verts"])
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(angle, 3, "Y"), verts=slot["verts"])
        bmesh.ops.translate(bm, vec=Vector((x, -0.2, z)), verts=slot["verts"])
        tag_new_faces(bm, 1)
    return obj_from_bm("frame_screws", bm, collection, [mats["rosette"], mats["bore"]])


def build_bg(collection, material):
    bm = bmesh.new()
    add_box(bm, (BOARD_W + 6.0, 0.6, BOARD_H + 6.0), (0.0, 1.2, 0.0))
    return obj_from_bm("bg_wall", bm, collection, [material])


def build_pick(name, shape, collection, mats, grip):
    bm = bmesh.new()
    rot_y = Matrix.Rotation(math.pi / 2, 3, "Y")
    shaft = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=PICK_SHAFT_R, radius2=PICK_SHAFT_R, depth=3.1)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_y, verts=shaft["verts"])
    bmesh.ops.translate(bm, vec=Vector((-1.6, 0.0, 0.0)), verts=shaft["verts"])
    tag_new_faces(bm, 0)
    if shape == "diamond":
        tip = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.39, 0.14, 0.39)), verts=tip["verts"])
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 4, 3, "Y"), verts=tip["verts"])
    else:
        tip = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=PICK_TIP)
        bmesh.ops.scale(bm, vec=Vector((1.0, 0.5, 1.0)), verts=tip["verts"])
    tag_new_faces(bm, 0)
    ferrule = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.1, radius2=0.1, depth=0.35)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_y, verts=ferrule["verts"])
    bmesh.ops.translate(bm, vec=Vector((-3.3, 0.0, 0.0)), verts=ferrule["verts"])
    tag_new_faces(bm, 1)
    grip_part = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.095, radius2=0.095, depth=1.3)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_y, verts=grip_part["verts"])
    bmesh.ops.translate(bm, vec=Vector((-4.0, 0.0, 0.0)), verts=grip_part["verts"])
    tag_new_faces(bm, 2)
    return obj_from_bm(name, bm, collection, [mats["pick"], mats["ferrule"], grip])


def build_badge(collection, mats):
    bm = bmesh.new()
    rot_x = Matrix.Rotation(math.pi / 2, 3, "X")
    ring = bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.21, radius2=0.19, depth=0.055)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_x, verts=ring["verts"])
    bmesh.ops.translate(bm, vec=Vector((0.0, -0.03, 0.0)), verts=ring["verts"])
    tag_new_faces(bm, 0)
    inlay = bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.12, radius2=0.12, depth=0.05)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_x, verts=inlay["verts"])
    bmesh.ops.translate(bm, vec=Vector((0.0, -0.04, 0.0)), verts=inlay["verts"])
    tag_new_faces(bm, 1)
    return obj_from_bm("badge_master", bm, collection, [mats["rosette"], mats["enamel"]])


def build_shadowcatcher(collection):
    bm = bmesh.new()
    add_box(bm, (BOARD_W + 4.0, 0.02, BOARD_H + 4.0), (0.0, 0.89, 0.0))
    obj = obj_from_bm("shadowcatcher", bm, collection)
    obj.is_shadow_catcher = True
    obj.hide_render = True
    return obj


def add_sun(name, direction, code, energy, angle, collection):
    light = bpy.data.lights.new(name, "SUN")
    light.color = hex_lin(code)[:3]
    light.energy = energy
    light.angle = angle
    obj = bpy.data.objects.new(name, light)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector(direction).normalized().to_track_quat("-Z", "Y")
    collection.objects.link(obj)
    return obj


def add_camera(name, location, ortho_scale, collection):
    cam = bpy.data.cameras.new(name)
    cam.type = "ORTHO"
    cam.ortho_scale = ortho_scale
    cam.clip_start = 0.1
    cam.clip_end = 100.0
    obj = bpy.data.objects.new(name, cam)
    obj.location = location
    obj.rotation_euler = (math.pi / 2, 0.0, 0.0)
    collection.objects.link(obj)
    return obj


def build_world(scene):
    world = bpy.data.worlds.new("workshop")
    world.use_nodes = True
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    zterm = nt.nodes.new("ShaderNodeMath")
    zterm.operation = "MULTIPLY"
    zterm.inputs[1].default_value = 0.9
    nt.links.new(sep.outputs["Z"], zterm.inputs[0])
    xterm = nt.nodes.new("ShaderNodeMath")
    xterm.operation = "MULTIPLY"
    xterm.inputs[1].default_value = -0.35
    nt.links.new(sep.outputs["X"], xterm.inputs[0])
    combined = nt.nodes.new("ShaderNodeMath")
    combined.operation = "ADD"
    nt.links.new(zterm.outputs[0], combined.inputs[0])
    nt.links.new(xterm.outputs[0], combined.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    nt.links.new(combined.outputs[0], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = hex_lin("101112")
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = lerp_lin(hex_lin(HEX["key"]), (1.0, 1.0, 1.0, 1.0), 0.25, gain=1.7)
    mid = ramp.color_ramp.elements.new(0.45)
    mid.color = hex_lin("5A6672")
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.55
    scene.world = world


def place_copy(proto, name, location, collection, material=None):
    obj = proto.copy()
    obj.name = name
    obj.location = location
    obj.hide_render = False
    collection.objects.link(obj)
    if material is not None:
        obj.material_slots[0].link = "OBJECT"
        obj.material_slots[0].material = material
    return obj


def build_lookdev(collection, protos, mats):
    for pos, upper, height, metal, state in LEVEL:
        x = px_to_x(column_center_px(pos))
        tip = BOARD_H / 2 - height if upper else -BOARD_H / 2 + height
        mat = mats[metal]
        if state == "hover":
            mat = mats[f"{metal}_hover"]
        elif state == "jam":
            mat = mats[f"{metal}_jam"]
        proto = protos["upper"] if upper else protos["lower"]
        place_copy(proto, f"pin_{pos}_{'u' if upper else 'l'}", (x, 0.0, tip), collection, mat)
        if state == "master":
            badge_z = tip + (30.0 / PPU if upper else -30.0 / PPU)
            place_copy(protos["badge"], f"badge_{pos}", (x, 0.0, badge_z), collection)
    hover_pos, hover_height = 2, 3
    engaged_x = px_to_x(column_center_px(hover_pos))
    engaged_z = BOARD_H / 2 - hover_height - 20.0 / PPU
    place_copy(protos["pick_diamond"], "pick_engaged", (engaged_x, -0.24, engaged_z), collection)
    idle_x = px_to_x(80.0)
    place_copy(protos["pick_circle"], "pick_idle", (idle_x, -0.24, -40.0 / PPU), collection)


def enable_gpu():
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        return "CPU"
    for device_type in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = device_type
        except TypeError:
            continue
        prefs.get_devices()
        found = False
        for dev in prefs.devices:
            dev.use = dev.type == device_type
            found = found or dev.use
        if found:
            return device_type
    return "CPU"


def setup_render(scene, samples):
    scene.render.engine = "CYCLES"
    device_type = enable_gpu()
    scene.cycles.device = "CPU" if device_type == "CPU" else "GPU"
    scene.cycles.samples = samples
    scene.cycles.seed = 0
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPTIX" if device_type == "OPTIX" else "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.render.resolution_x = 2000
    scene.render.resolution_y = 1600
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.3
    for look in ("AgX - Base Contrast", "Base Contrast", "None"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue
    print(f"render device: {device_type}")
    return device_type


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", required=True)
    parser.add_argument("--still", default=None)
    parser.add_argument("--samples", type=int, default=256)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    mats = build_materials()
    collections = {}
    for name in (
        "BG",
        "FRAME",
        "TUMBLER_UPPER",
        "TUMBLER_LOWER",
        "PICK_DIAMOND",
        "PICK_CIRCLE",
        "BADGE_MASTER",
        "SHADOWCATCHER",
        "RIG",
        "LOOKDEV",
    ):
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
        collections[name] = col
    build_world(scene)
    build_bg(collections["BG"], mats["bore"])
    build_frame(collections["FRAME"], mats["frame"], COLUMNS)
    build_screws(collections["FRAME"], mats)
    protos = {}
    protos["upper"] = build_pin("tumbler_upper", True, collections["TUMBLER_UPPER"], mats["steel"])
    protos["upper"].location = (-20.0, 0.0, -BOARD_H / 2)
    protos["lower"] = build_pin("tumbler_lower", False, collections["TUMBLER_LOWER"], mats["steel"])
    protos["lower"].location = (-17.0, 0.0, BOARD_H / 2)
    protos["pick_diamond"] = build_pick("pick_diamond", "diamond", collections["PICK_DIAMOND"], mats, mats["grip_a"])
    protos["pick_diamond"].location = (-24.0, 0.0, 2.0)
    protos["pick_circle"] = build_pick("pick_circle", "circle", collections["PICK_CIRCLE"], mats, mats["grip_b"])
    protos["pick_circle"].location = (-24.0, 0.0, 0.0)
    protos["badge"] = build_badge(collections["BADGE_MASTER"], mats)
    protos["badge"].location = (-24.0, 0.0, -2.0)
    for proto in protos.values():
        proto.hide_render = True
    build_shadowcatcher(collections["SHADOWCATCHER"])
    add_sun("sun_key", (0.5, 0.7, -0.5), HEX["key"], 6.0, 0.06, collections["RIG"])
    add_sun("sun_rim", (-0.75, 0.35, -0.12), HEX["rim"], 1.6, 0.35, collections["RIG"])
    cam_board = add_camera("CAM_BOARD", (0.0, -15.0, 0.0), BOARD_W, collections["RIG"])
    add_camera("CAM_TUMBLER_UPPER", (-20.0, -15.0, 0.0), 1.6, collections["RIG"])
    add_camera("CAM_TUMBLER_LOWER", (-17.0, -15.0, 0.0), 1.6, collections["RIG"])
    add_camera("CAM_PICK", (-22.0, -15.0, 1.0), 6.0, collections["RIG"])
    add_camera("CAM_BADGE", (-24.0, -15.0, -2.0), 0.6, collections["RIG"])
    build_lookdev(collections["LOOKDEV"], protos, mats)
    setup_render(scene, args.samples)
    scene.camera = cam_board
    blend_path = Path(args.blend)
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"saved: {blend_path}")
    if args.still:
        still_path = Path(args.still)
        still_path.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(still_path)
        bpy.ops.render.render(write_still=True)
        print(f"rendered: {still_path}")


main()

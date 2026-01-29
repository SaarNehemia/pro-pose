import bpy
import os

# --- CONFIG ---
CHARACTER_NAME = 'Yukihiro2'
CHARACTER_FBX = rf"C:\Users\saar.nehemia\PycharmProjects\pro-pose\assets\avatars\{CHARACTER_NAME}.fbx"
ANIMATIONS_DIR = r"C:\Users\saar.nehemia\PycharmProjects\pro-pose\assets\animations"
EXPORT_PATH = rf"C:\Users\saar.nehemia\PycharmProjects\pro-pose\assets\fighters\{CHARACTER_NAME}.glb"

SCALE = 1  # Uniform scale factor


# --- HELPERS ---
def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_fbx(path):
    bpy.ops.import_scene.fbx(filepath=path)


def get_armature():
    return next((obj for obj in bpy.data.objects if obj.type == 'ARMATURE'), None)


def get_meshes():
    return [obj for obj in bpy.data.objects if obj.type == 'MESH']


def scale_objects(scale):
    for obj in bpy.data.objects:
        if obj.type in {'MESH', 'ARMATURE'}:
            obj.scale = [scale] * 3
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(scale=True)


def add_action_to_nla(armature, action):
    if not armature.animation_data:
        armature.animation_data_create()
    track = armature.animation_data.nla_tracks.new()
    track.name = action.name
    strip = track.strips.new(action.name, int(action.frame_range[0]), action)
    strip.action_frame_start = action.frame_range[0]
    strip.action_frame_end = action.frame_range[1]


# --- MAIN ---
def main():
    clean_scene()

    # Step 1: Import base character
    import_fbx(CHARACTER_FBX)

    # Remove action imported with character
    for action in bpy.data.actions:
        bpy.data.actions.remove(action)

    # Get armature
    base_armature = get_armature()
    if not base_armature:
        raise RuntimeError("Could not find base armature.")

    # Step 3: Scale everything
    scale_objects(SCALE)

    # Step 2: Import and add animations
    for fname in os.listdir(ANIMATIONS_DIR):
        if not fname.lower().endswith('.fbx'):
            continue

        anim_path = os.path.join(ANIMATIONS_DIR, fname)
        anim_name = os.path.splitext(fname)[0]

        # Import the animation FBX
        import_fbx(anim_path)

        for action in bpy.data.actions:
            if 'Armature.001' in action.name:
                action.name = anim_name
                add_action_to_nla(base_armature, action)

        # Optionally delete imported animation armature/mesh
        for obj in bpy.context.selected_objects:
            if obj != base_armature:
                bpy.data.objects.remove(obj, do_unlink=True)

    print(f'Exporting animations: {list(bpy.data.actions)}...')

    # Step 4: Export to GLB
    bpy.ops.export_scene.gltf(
        filepath=EXPORT_PATH,
        export_format='GLB',
        export_apply=True
    )

    print(f"✅ Exported to {EXPORT_PATH}")


# --- RUN ---
if __name__ == "__main__":
    main()

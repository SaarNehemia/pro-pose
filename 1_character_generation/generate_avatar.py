# generate_avatar.py
import os
import subprocess


def run_pifuhd(image_path, output_dir='assets/avatars'):
    assert os.path.exists(image_path), "Image file does not exist!"

    os.makedirs(output_dir, exist_ok=True)
    command = [
        'python', 'apps/simple_test.py',
        '--input_path', image_path,
        '--output_dir', output_dir
    ]
    subprocess.run(command, cwd='pifuhd')  # assumes you've cloned PIFuHD
    print(f"Avatar mesh saved to {output_dir}")

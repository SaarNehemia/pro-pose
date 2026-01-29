from direct.gui.OnscreenText import OnscreenText
from panda3d.core import loadPrcFileData
import subprocess
import numpy as np
from panda3d.core import PNMImage

loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'fullscreen 0')
loadPrcFileData('', 'win-size 1280 720')  # or any resolution you want
loadPrcFileData('', 'win-origin 100 100')

from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import WindowProperties, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerEvent
from panda3d.core import Vec3, Filename, getModelPath
from direct.task import Task
import sys

# Set model path
model_path = r"C:\Users\saar.nehemia\PycharmProjects\pro-pose\assets\fighters"
getModelPath().append_directory(Filename.from_os_specific(model_path))

CHARACTERS_LIST = ["Ninja.glb", "Erika Archer.glb", "Mousey.glb", "Yukihiro.glb"]  # Yukihiro not working
CHARACTER_GLTF = CHARACTERS_LIST[0]
ENEMY_GLTF = CHARACTERS_LIST[2]


class FightingGame(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.setup_camera()

        self.key_map = {"w": False, "a": False, "s": False, "d": False,
                        "i": False, "j": False, "k": False, "l": False}

        self.accept_keys()

        self.player1 = self.load_character(glb_path=CHARACTER_GLTF,
                                           pos=Vec3(-2, 10, 0), scale=0.05, name="Player1")
        self.player2 = self.load_character(glb_path=ENEMY_GLTF,
                                           pos=Vec3(2, 10, 0), scale=0.05, name="Player2")

        self.status_text = OnscreenText(text="Use WASD + IJKL for Player 1",
                                        pos=(-1.3, 0.9), scale=0.05, align=0, mayChange=True)

        self.last_attack = None
        self.attack_timer = 0.0
        self.attack_cooldown = 2.0

        self.taskMgr.add(self.update, "update")

    def record_game(self):
        self.record_width = self.win.getXSize()
        self.record_height = self.win.getYSize()
        self.record_fps = 30
        self.pnmimage = PNMImage(self.record_width, self.record_height)

        self.ffmpeg_pipe = subprocess.Popen([
            'ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', f'{self.record_width}x{self.record_height}',
            '-r', str(self.record_fps),
            '-i', '-',
            '-an',
            '-vcodec', 'libx264',
            '-pix_fmt', 'yuv420p',
            'output.mp4'
        ], stdin=subprocess.PIPE)

        self.taskMgr.add(self.record_frame, "RecordFrameTask")
        self.accept("escape", self.stop_recording)  # Esc key to stop

    def record_frame(self, task):
        if self.win is None or self.win.isClosed():
            return task.done
        self.win.getScreenshot(self.pnmimage)
        frame = np.array(self.pnmimage.getRamImage()).reshape((self.record_height, self.record_width, 3))
        try:
            self.ffmpeg_pipe.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print("⚠️ ffmpeg pipe closed.")
            return task.done
        return task.cont

    def stop_recording(self):
        print("🎬 Stopping recording...")
        if self.ffmpeg_pipe:
            try:
                self.ffmpeg_pipe.stdin.close()
                self.ffmpeg_pipe.wait()
                print("✅ Video saved as output.mp4")
            except Exception as e:
                print("Error stopping recording:", e)
        self.userExit()

    def setup_camera(self):
        self.cam.setPos(0, -30, 15)
        self.cam.lookAt(0, 0, 10)

    def accept_keys(self):
        for key in self.key_map:
            self.accept(key, self.set_key, [key, True])
            self.accept(key + "-up", self.set_key, [key, False])
        self.accept("escape", sys.exit)

    def set_key(self, key, value):
        self.key_map[key] = value

    def load_character(self, glb_path, pos, scale, name):
        actor = Actor(glb_path)
        actor.reparentTo(self.render)
        actor.setPos(pos)
        actor.setScale(scale)
        actor.setName(name)
        if "1" in name:
            actor.setH(90)
        else:
            actor.setH(-90)
        print(f"{name} animations: {actor.getAnimNames()}")
        return actor

    def move_character(self, character, direction):
        speed = 2
        if direction == "forward":
            character.setY(character, -speed)
        elif direction == "back":
            character.setY(character, speed)
        elif direction == "left":
            character.setX(character, speed)
        elif direction == "right":
            character.setX(character, -speed)

    def update(self, task):
        dt = globalClock.getDt()
        self.attack_timer = max(0.0, self.attack_timer - dt)

        # Handle attack input
        if self.attack_timer <= 0.0:
            if self.key_map["i"]:
                self.player1.play("Punch1")
                self.last_attack = "Punch1"
                self.attack_timer = self.attack_cooldown
            elif self.key_map["j"]:
                self.player1.play("Punch2")
                self.last_attack = "Punch2"
                self.attack_timer = self.attack_cooldown
            elif self.key_map["k"]:
                self.player1.play("Kick1")
                self.last_attack = "Kick1"
                self.attack_timer = self.attack_cooldown
            elif self.key_map["l"]:
                self.player1.play("Kick2")
                self.last_attack = "Kick2"
                self.attack_timer = self.attack_cooldown
            else:
                self.last_attack = None

        # Walk animations (looping only when changed)
        if self.last_attack is None or not self.player1.getAnimControl(self.last_attack).isPlaying():
            move_dir = None
            if self.key_map["d"]:
                self.move_character(self.player1, "forward")
                move_dir = "Standing Walk Forward"
            elif self.key_map["a"]:
                self.move_character(self.player1, "back")
                move_dir = "Standing Walk Back"
            elif self.key_map["w"]:
                self.move_character(self.player1, "left")
                move_dir = "Standing Walk Left"
            elif self.key_map["s"]:
                self.move_character(self.player1, "right")
                move_dir = "Standing Walk Right"

            if move_dir:
                # Only loop if the anim isn't already playing
                if not self.player1.getCurrentAnim() == move_dir:
                    self.player1.loop(move_dir)
            else:
                # Only stop if currently playing a walk anim
                if self.player1.getCurrentAnim() and "Standing Walk" in self.player1.getCurrentAnim():
                    self.player1.stop()

        # Simple AI
        # p1_pos = self.player1.getPos()
        # p2_pos = self.player2.getPos()
        # direction = p1_pos - p2_pos
        # if direction.length() > 0.1:
        #     direction.normalize()
        #     self.player2.setPos(self.player2.getPos() + direction * 0.02)
        #     self.player2.loop("Standing Walk Forward")

        return Task.cont


if __name__ == '__main__':
    app = FightingGame()
    app.run()

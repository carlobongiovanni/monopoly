from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

# ground
bg = Entity(model='plane', texture='grass', collider="mesh", scale=(200, 1, 200))

Sky()

player = FirstPersonController(z = 30)

# model comes from https://free3d.com/3d-models/
man = Entity(
    model="FinalBaseMesh.obj",
    texture=None,
    collider="mesh",
    scale=.2
)


def update():
    man.rotation_y += 100 * time.dt

app.run()

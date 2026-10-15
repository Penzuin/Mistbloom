scoreboard players add #t moonball 1
execute if score #t moonball matches 8.. if entity @a[x=106,y=208,z=138,dx=52,dy=40,dz=53] run function moonball:music/beat
execute if score #t moonball matches 8.. run scoreboard players set #t moonball 0
execute as @a[x=90,y=170,z=80,dx=90,dy=100,dz=140,tag=!moonball_in] run title @s times 20 70 30
execute as @a[x=90,y=170,z=80,dx=90,dy=100,dz=140,tag=!moonball_in] run title @s subtitle {"text":"a Mistbloom Studios showcase","color":"#9fb3d9"}
execute as @a[x=90,y=170,z=80,dx=90,dy=100,dz=140,tag=!moonball_in] run title @s title {"text":"Moonlit Ballroom","color":"#f2c97d"}
tag @a[x=90,y=170,z=80,dx=90,dy=100,dz=140,tag=!moonball_in] add moonball_in
tag @a[tag=moonball_in] remove moonball_out
execute as @a[tag=moonball_in] unless entity @s[x=90,y=170,z=80,dx=90,dy=100,dz=140] run tag @s remove moonball_in
execute if entity @a[x=90,y=170,z=80,dx=90,dy=100,dz=140] positioned 132 211 108 run particle minecraft:cloud ~ ~ ~ 14 0.3 14 0.003 2
execute if entity @a[x=90,y=170,z=80,dx=90,dy=100,dz=140] positioned 132 216 108 run particle minecraft:white_ash ~ ~ ~ 16 6 16 0 4
execute if entity @a[x=106,y=208,z=138,dx=52,dy=40,dz=53] positioned 132 213 162 run particle minecraft:end_rod ~ ~ ~ 9 2 9 0.004 1
execute if entity @a[x=106,y=208,z=138,dx=52,dy=40,dz=53] positioned 132 222 164 run particle minecraft:soul ~ ~ ~ 18 4 22 0.002 1
execute if score #t moonball matches 0 if score #beat moonball matches 0 run title @a[x=106,y=208,z=138,dx=52,dy=40,dz=53] actionbar {"text":"Right-click the ghosts. They're friendly!","color":"#c9b8f0"}

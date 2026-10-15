scoreboard players add #t moonball 1
execute if score #t moonball matches 8.. if entity @a[x=126,y=209,z=130,dx=12,dy=22,dz=24] run function moonball:music/beat
execute if score #t moonball matches 8.. run scoreboard players set #t moonball 0
execute as @a[x=114,y=185,z=103,dx=36,dy=60,dz=56,tag=!moonball_in] run title @s times 20 70 30
execute as @a[x=114,y=185,z=103,dx=36,dy=60,dz=56,tag=!moonball_in] run title @s subtitle {"text":"a Mistbloom Studios showcase","color":"#9fb3d9"}
execute as @a[x=114,y=185,z=103,dx=36,dy=60,dz=56,tag=!moonball_in] run title @s title {"text":"Moonlit Ballroom","color":"#f2c97d"}
tag @a[x=114,y=185,z=103,dx=36,dy=60,dz=56,tag=!moonball_in] add moonball_in
execute as @a[tag=moonball_in] unless entity @s[x=114,y=185,z=103,dx=36,dy=60,dz=56] run tag @s remove moonball_in
execute if entity @a[x=114,y=185,z=103,dx=36,dy=60,dz=56] positioned 132 211 126 run particle minecraft:cloud ~ ~ ~ 12 0.3 18 0.003 1
execute if entity @a[x=114,y=185,z=103,dx=36,dy=60,dz=56] positioned 132 218 134 run particle minecraft:white_ash ~ ~ ~ 12 6 18 0 3
execute if entity @a[x=126,y=209,z=130,dx=12,dy=22,dz=24] positioned 132 213 143 run particle minecraft:end_rod ~ ~ ~ 3 1.5 3 0.003 1
execute if entity @a[x=126,y=209,z=130,dx=12,dy=22,dz=24] positioned 132 217 142 run particle minecraft:soul ~ ~ ~ 4 2 10 0.002 1

execute as @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92,tag=!hfest_in] run title @s times 20 70 30
execute as @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92,tag=!hfest_in] run title @s subtitle {"text":"a Mistbloom Studios showcase","color":"#c9b8f0"}
execute as @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92,tag=!hfest_in] run title @s title {"text":"Halloween Festival","color":"#ffb15c"}
tag @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92,tag=!hfest_in] add hfest_in
execute as @a[tag=hfest_in] unless entity @s[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92] run tag @s remove hfest_in
execute if entity @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92] positioned -1450 156 -560 run particle minecraft:white_ash ~ ~ ~ 26 5 30 0 4
execute if entity @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92] positioned -1429 151.2 -560 run particle minecraft:soul ~ ~ ~ 5 0.4 8 0.004 1
execute if entity @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92] positioned -1424 152 -559.5 run particle minecraft:end_rod ~ ~ ~ 1.5 1.5 3 0.002 1
execute if entity @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92] positioned -1474.5 151.6 -570.5 run particle minecraft:witch ~ ~ ~ 0.3 0.2 0.3 0.01 1
execute if entity @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92] positioned -1449.5 151.6 -559.5 run particle minecraft:effect ~ ~ ~ 0.2 0.1 0.2 0.01 1
execute if entity @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92] positioned -1432.5 153 -581.5 run particle minecraft:lava ~ ~ ~ 0.4 0.2 0.4 0 1
execute if entity @a[x=-1486,y=144,z=-604,dx=72,dy=40,dz=92] positioned -1450 150.3 -562 run particle minecraft:cloud ~ ~ ~ 28 0.2 34 0.002 1

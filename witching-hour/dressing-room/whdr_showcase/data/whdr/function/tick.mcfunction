execute as @a[x=-1474,y=144,z=-785,dx=48,dy=30,dz=56,tag=!whdr_in] run title @s times 15 60 25
execute as @a[x=-1474,y=144,z=-785,dx=48,dy=30,dz=56,tag=!whdr_in] run title @s subtitle {"text":"dressing room","color":"#c9b8f0"}
execute as @a[x=-1474,y=144,z=-785,dx=48,dy=30,dz=56,tag=!whdr_in] run title @s title {"text":"Witching Hour","color":"#e8c8ff"}
tag @a[x=-1474,y=144,z=-785,dx=48,dy=30,dz=56,tag=!whdr_in] add whdr_in
execute as @a[tag=whdr_in] unless entity @s[x=-1474,y=144,z=-785,dx=48,dy=30,dz=56] run tag @s remove whdr_in
execute if entity @a[x=-1459,y=150,z=-761,dx=18,dy=8,dz=17] positioned -1449.5 152.3 -747.5 run particle minecraft:end_rod ~ ~ ~ 1.2 0.6 1.2 0.002 1
execute if entity @a[x=-1459,y=150,z=-761,dx=18,dy=8,dz=17] positioned -1442.5 153.9 -750.5 run particle minecraft:witch ~ ~ ~ 0.2 0.2 0.2 0.01 1

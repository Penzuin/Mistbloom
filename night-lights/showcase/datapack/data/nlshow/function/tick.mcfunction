execute as @a[x=187,y=136,z=385,dx=26,dy=34,dz=29,tag=!nl_in] run title @s times 20 70 30
execute as @a[x=187,y=136,z=385,dx=26,dy=34,dz=29,tag=!nl_in] run title @s subtitle {"text":"a Mistbloom Studios showcase","color":"#9fb3d9"}
execute as @a[x=187,y=136,z=385,dx=26,dy=34,dz=29,tag=!nl_in] run title @s title {"text":"Night Lights","color":"#f2c97d"}
tag @a[x=187,y=136,z=385,dx=26,dy=34,dz=29,tag=!nl_in] add nl_in
execute as @a[tag=nl_in] unless entity @s[x=187,y=136,z=385,dx=26,dy=34,dz=29] run tag @s remove nl_in
execute if entity @a[x=187,y=136,z=385,dx=26,dy=34,dz=29] positioned 200 152 400 run particle minecraft:firefly ~ ~ ~ 8 1.5 10 0 1
execute if entity @a[x=187,y=136,z=385,dx=26,dy=34,dz=29] positioned 200 151 398 run particle minecraft:cloud ~ ~ ~ 8 0.2 9 0.002 1

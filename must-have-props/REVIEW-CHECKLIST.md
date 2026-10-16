# Must-Have Props v1.0 - review checklist

- [x] 14 pieces, 18 models (4 lights with off + on models), 15 elements or fewer each
- [x] Every model faces north; hitboxes match (crate, barrel 1x1 barrier; crate stack, bench 2x1 barriers; street lamp 1x2 barriers; interactions for the rest)
- [x] Crate and barrel open 27 slots; bench seats two at 0.4; 4 lights toggle (levels 15, 15, 12, 15; the street lamp light sits in the lantern block above its barrier)
- [x] Hanging lantern places on ceilings only; everything else on floors
- [x] Flame textures animate (.mcmeta, 8 frames x 2 ticks) and stay clear of their card edges
- [x] Every item_model / toggled_item_model in musthave.yml has a model and texture
- [x] README.txt and LICENSE.txt are plain text with CRLF line endings
- [x] Store copy: version range 1.21.4 to 1.26.2, Nexo, Discord link, no banned phrases
- [x] Main image: grouped rows in listing order, no pieces overlapping (mask test), neutral look
- [x] Price: $10

Test on the UltraServers "Selling Test" server: /nexo reload all, /nexo inventory, place each piece, hang the lantern from a ceiling and check its height, toggle all 4 lights, open the crate and barrel, sit on the bench.
- [x] Independent read-only review: no blocking issues; fixed bench armrest and apple z-fighting, candle dish bottom, crate stack top barrier, signpost hitbox width, street lamp light position, hanging lantern chain and wheel readability

"""README.txt for the Witching Hour download, in the user's template."""


def readme(entries, version):
    return """Witching Hour - Mistbloom Studios
==================================================

Six witchy cosmetics for HMCCosmetics that players can wear all year.

INSTALL - Drag and Drop (Nexo)
--------------
1. Copy everything inside Nexo/plugins/ into your server's plugins/ folder.
2. Run /nexo reload all, then /cosmetic reload.
3. Open the menu with /cosmetic menu witching_hour.

Using ItemsAdder or Oraxen instead? Copy that folder's plugins/ the same way,
then run /iazip or /oraxen reload all, then /cosmetic reload.
No items plugin? Copy "No items plugin/plugins/" and add the resource pack zip to your server.

Permissions are hmccosmetics.<id>, for example hmccosmetics.witch_hat

Requires Minecraft 1.21.4 or newer and HMCCosmetics 2.9 or newer
Support: discord.gg/QUJ8ntw7eS
"""

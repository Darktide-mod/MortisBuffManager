# Mortis Trials Buff Manager - Local and Realms

Mortis Trials Buff Manager requires SoloPlay and also supports Realms sessions. Choose Mortis Trials Buffs through the talent-tree UI, with the host controlling selection limits and validation in Realms. The mod has its own settings; Talent Point Manager is not required.

## 2.0.3 update

- Fix the unclosable empty picker and lingering entry when opening the talent tree with this mod disabled in DMF. Native widgets start visible, so picker content now defaults hidden and all passes check the framework state.
- Disabling an open picker clears its controls, restores the native summary button and releases resources. Stale button callbacks and late resource callbacks cannot reopen it or change selections.
- Re-enabling restores the entry even if the talent tree opened while disabled. Both Close and Esc work. Saved Buff selections and native effects are unchanged.
- Reproduce the old failure and verify the fix with real DMF toggling and native UIWidget.init. Retain the previous button-material fix; live-game retesting is still needed.


## Features

- Select native Mortis Trials Buffs using a list in the talent-tree UI.
- Filter choices through native Buff pools and family, class, ability and talent requirements.
- Set a selection limit from 1 to 64; the default is 32.
- Use separate local and Realms scopes, with host-controlled rules for Realms guests.
- English, Simplified Chinese and Traditional Chinese. Buff names use the game's translations.

When the mission itself is Mortis Trials, enabling preconfigured Buffs also disables the native reward drafts for that mission.

The master switch is off by default. Local and Realms scopes are enabled beneath it. The limit is the maximum number of selected entries, not arbitrary stacks of a single Buff or a guarantee that every Buff is eligible for every build.

## Requirements and installation

Requires Darktide Mod Loader, Darktide Mod Framework and SoloPlay. For Realms co-op, also install Realms; SoloPlay remains required. Talent Point Manager and the two Havoc mods are optional companions.

## Vortex installation

- Close the game. Set up Darktide as a managed game in Vortex and install the requirements listed above.
- Download this mod's installation ZIP from Files. In Vortex, use Install From File to import it, then enable the mod and select Deploy Mods.
- Open Load Order, enable MortisBuffManager and place it after SoloPlay. Preserve your other mods.
- Start the game and open Mod Options → Mortis Trials Buff Manager. Enable the master switch to use preconfigured Buffs.

## Manual installation

- Close the game and install the requirements listed above, following each dependency's instructions.
- Open the Darktide game folder. In Steam: Properties → Installed Files → Browse.
- Open the game's mods folder and extract this ZIP there. Its top-level folder is MortisBuffManager. The resulting path must be mods/MortisBuffManager.
- Open mods/mod_load_order.txt and add MortisBuffManager on its own line after SoloPlay. Preserve all other entries.
- Save the file and start the game. Open Mod Options → Mortis Trials Buff Manager and enable the master switch.

Disable the old combined TalentAndMortisManager before using the split version. The mod loads Mortis resources already provided by the game; it does not include extracted game artwork.

## Framework switch

Darktide Mod Framework provides the mod enable/disable switch. This mod also has its own feature master switch, which is off by default; enable both to use the feature. Disabling the framework switch stops updates and runs cleanup without changing your saved feature settings.

## Getting started

Open Mod Options → Mortis Trials Buff Manager. Enable custom Mortis Buffs, choose the local or Realms scopes and set the selection limit. Open the talent tree and use the Mortis Buff selection controls to choose eligible entries. Recheck the list when changing class, ability, talents or Buff family.

In Realms, guests need the same mod to submit their own choices. The host's limit and validation rules determine what is accepted. Use matching versions across the group.

## Limits and compatibility

The mod operates in supported local contexts, such as the Psykhanium and local single-player sessions, or under Realms host authority. It does not promise Buffs or permanent progression in official matchmaking.

Eligibility follows the available native data; this is not a promise that all Buffs can be combined. Mods that replace Mortis selection, mission Buff management or the same talent-tree controls can conflict.

The current release passed code and simulated checks but has not received a new live-game test. Restart after changing the game's language.

## Version 2.0.2

- Fixed the talent-page button resource dependency that could crash the engine when the inventory page unloaded, including transitions in the Realms preparation screen.
- The Mortis entry, seven family buttons, Clear and Close now use the talent view's native terminal-button materials. The entry is safe to draw after inventory-page resources unload, even before opening the picker.
- Preserved button sizes and 20-point labels, existing selections and native Buff behavior. No additional inventory package is kept resident.
- Added regression checks using native widget and button definitions, reproducing the old dependency and checking the new material set, repeated open/close cycles, callbacks and all three languages. The proprietary renderer has not been tested live.
- Fully exit and restart the game after updating; use the same version across your Realms group.

## Version 2.0.1

- Completed English, Simplified Chinese and Traditional Chinese settings text.
- Moved documentation into this mod's own folder to remove the shared README conflict between the four individual Vortex packages.

## Credits

Split from the earlier combined TalentAndMortisManager. Solo Play and Realms: deluxghost. Native Mortis systems, Buff definitions and referenced assets: Fatshark. Game-source reference: Aussiemon/Darktide-Source-Code. This is an independent community project.

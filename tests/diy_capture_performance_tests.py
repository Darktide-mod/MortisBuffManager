"""Real eligibility capture, with native live extension/template outputs supplied."""
from harness import *
import json
L.globals().Q=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/diy/diy_eligibility')
L.execute('''
local definitions={g={player_ability={ability_type="grenade_ability",ability={name="profile_grenade",max_charges=3}}},
 c={player_ability={ability_type="combat_ability",ability={name="profile_combat",ability_group="profile_combat",cooldown=30}}}}
local definition_reads,sorts,action_scans=0,0,0
local profile={archetype={name="veteran",base_talents={g=1,c=1},talents=setmetatable({},{__index=function(_,k)definition_reads=definition_reads+1;return definitions[k]end})},talents={},loadout={}}
for i=1,60 do profile.talents['talent_'..i]=1 end
local melee={name="sword",keywords={"melee"},actions={}}
local gun={name="gun",keywords={"ranged"},hud_configuration={uses_ammunition=true},actions={reload={kind="reload_state"}}}
for i=1,100 do melee.actions[i]={kind="melee"};gun.actions[i]={kind="shoot"}end
local live={grenade_ability={name="live_grenade",max_charges=2},combat_ability={name="live_combat",ability_group="live_combat",cooldown=20}}
local slots={slot_primary=melee,slot_secondary=gun}
local unit={};ALIVE={[unit]=true}
local ability={equipped_abilities=function()return live end}
ScriptUnit={has_extension=function(_,name)
 if name=="ability_system"then return ability end
 if name=="visual_loadout_system"then return {weapon_template_from_slot=function(_,slot)return slots[slot]end}end
end}
local player={player_unit=unit,profile=function()return profile end,archetype_name=function()return "veteran"end}
local raw_sort=table.sort;table.sort=function(...)sorts=sorts+1;return raw_sort(...)end
local raw_pairs=pairs;pairs=function(t)
 if t==melee.actions or t==gun.actions then action_scans=action_scans+1 end
 return raw_pairs(t)
end
local start=os.clock()
for i=1,1000 do
 local setup=Q.capture(player,"fire",nil,false)
 assert(setup.complete and setup.grenade_ability=="live_grenade" and setup.combat_ability=="live_combat")
 assert(setup.resources.ammo and setup.resources.reload and setup.resources.melee and setup.talents.talent_60)
end
capture_report={captures=1000,profile_ability_lookups=definition_reads,talent_sorts=sorts,weapon_action_scans=action_scans,fixture_cpu_ms=(os.clock()-start)*1000}
-- Native live abilities are authoritative, including incomplete live setup.
live={};assert(not Q.capture(player,"fire",nil,false).complete)
-- Editor preview still derives the pending profile, not the spawned loadout.
profile.loadout={slot_primary=melee,slot_secondary=gun}
local preview=Q.capture(player,"fire",function(item)return item end,true)
assert(preview.complete and preview.grenade_ability=="profile_grenade")
live={grenade_ability={name="respawn_grenade"},combat_ability={ability_group="respawn_combat",cooldown=10}}
slots.slot_secondary={name="staff",keywords={"ranged"},actions={}}
local changed=Q.capture(player,"fire",nil,false)
assert(changed.complete and not changed.resources.ammo and changed.weapons.staff and changed.grenade_ability=="respawn_grenade")
-- Replaced metadata tables refresh cached native template classification.
gun.actions={};slots.slot_secondary=gun
assert(not Q.capture(player,"fire",nil,false).resources.reload)
''')
result=dict(L.globals().capture_report.items())
if '--report-only' not in sys.argv:
    assert result['profile_ability_lookups']==0,result
    assert result['talent_sorts']==0,result
    assert result['weapon_action_scans']==2,result
if '--output' in sys.argv:
    Path(sys.argv[sys.argv.index('--output')+1]).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
print('Eligibility capture: live ability reuse, complete/incomplete setup, profile preview, weapon/ability replacement and metadata invalidation checked.')

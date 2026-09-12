"""Production eligibility/selection with native ability data and weapon metadata.

Weapon metadata is extracted from native source; action bodies/render assets are
not executed. Profile and live extension boundaries are controlled fixtures.
"""
from harness import *
import subprocess

def native(path):
    return subprocess.check_output(['git','-c','gc.auto=0','show','HEAD:'+path+'.lua'],cwd=GAME).decode('utf-8-sig')

native_cache={}
native_cache['scripts/utilities/ui/text']=L.execute('return {convert_to_roman_numerals=function(n)return tostring(n)end}')
native_cache['scripts/settings/lunge/lunge_templates']=L.execute('return setmetatable({},{__index=function(_,k)return {name=k}end})')
native_cache['scripts/utilities/companion/companion_servo_skull_ability']=L.table()
native_cache['scripts/settings/companion/companion_servo_skull_settings']=L.table()
def native_require(path):
    if path not in native_cache:native_cache[path]=L.execute(native(path),name='@native/'+path)
    return native_cache[path]
L.globals().require=native_require
abilities={}
for archetype in ['veteran','zealot','psyker','ogryn','adamant','broker','cryptic']:
    entries=native_require('scripts/settings/ability/player_abilities/abilities/'+archetype+'_abilities')
    for name,record in entries.items():record.name=name
    abilities[archetype]=entries
L.globals().Abilities=L.table_from(abilities)

weapons={}
for folder,name in [('combat_swords','combatsword_p1_m1'),('lasguns','lasgun_p1_m1'),('force_staffs','forcestaff_p1_m1'),('plasma_rifles','plasmagun_p1_m1')]:
    source=native('scripts/settings/equipment/weapon_templates/'+folder+'/'+name)
    keywords=re.search(r'weapon_template.keywords\s*=\s*\{([^}]+)',source)
    assert keywords,name
    weapons[name]={'name':name,'keywords':re.findall(r'"([^"]+)"',keywords[1]),
        'hud_configuration':{'uses_ammunition':bool(re.search(r'uses_ammunition\s*=\s*true',source))},
        'actions':[{'kind':k} for k in re.findall(r'kind\s*=\s*"(reload_state|reload_shotgun|ranged_load_special)"',source)]}
    if 'weapon_template.overheat_configuration' in source:weapons[name]['overheat_configuration']={}
native_cache['scripts/settings/equipment/weapon_templates/weapon_templates']=tbl(weapons)
L.globals().W=native_require('scripts/utilities/weapon/weapon_template')
for symbol,name in [('Q','diy_eligibility'),('S','diy_schema'),('E','diy_engine'),('K','diy_catalog')]:
    L.globals()[symbol]=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/diy/'+name)
L.execute('''
local function profile(class,grenade,combat,weapon)
 local a=Abilities[class]
 local p={archetype={name=class,base_talents={g=1,c=1},talents={
  g={player_ability={ability_type="grenade_ability",ability=a[grenade]}},
  c={player_ability={ability_type="combat_ability",ability=a[combat]}}}},talents={},
  loadout={slot_primary={weapon_template="combatsword_p1_m1"},slot_secondary={weapon_template=weapon}}}
 if class=="psyker" then p.archetype.warp_charge={} end
 return {profile_data=p,profile=function()return p end,archetype_name=function()return class end}
end
local function capture(p)return Q.capture(p,"critical",W.weapon_template_from_item,true)end
local p=profile("psyker","psyker_smite","psyker_discharge_shout","forcestaff_p1_m1")
local s=capture(p);assert(s.complete and s.resources.warp_charge and not s.resources.ammo and not s.resources.grenade_charges)
assert(Q.matches({availability={archetypes={"psyker"},grenade_abilities={"psyker_smite"},combat_abilities={"psyker_shout"},weapons={"forcestaff_p1_m1"},weapon_keywords={"ranged"},families={"critical"}}},s))
for _,a in ipairs({{archetypes={"veteran"}},{grenade_abilities={"psyker_throwing_knives"}},{combat_abilities={"psyker_shield"}},{weapons={"lasgun_p1_m1"}},{families={"fire"}},{resources={"ammo"}},{resources={"grenade_charges"}}}) do assert(not Q.matches({availability=a},s))end
assert(not Q.matches({targets={archetypes={"ogryn"}}},s))
assert(not Q.matches({targets={exclude_tags={"player"}}},s))
assert(Q.matches({conditions={{field="health",op="lt",value=.3}},passive={stats={damage=.2}}},s),"Combat condition is not an equipment restriction")
assert(not Q.matches({passive={stats={reload_speed=.2}}},s))
assert(not Q.matches({passive={keywords={"no_ammo_consumption"}}},s))
assert(not Q.matches({rules={{actions={{type="ammo",amount=.2}}}}},s))
assert(Q.matches({availability={any_resources={"warp_charge","overheat"}},rules={{actions={{type="warp_charge"},{type="overheat"}}}}},s))
assert(not Q.matches({availability={any_resources={"warp_charge","ammo"}},passive={keywords={"no_ammo_consumption"}}},s),"Alternative actions cannot bypass passive requirements")
p.profile_data.talents.need=0;assert(not Q.matches({availability={talents={"need"}}},capture(p)))
p.profile_data.talents.need=false;assert(not Q.matches({availability={talents={"need"}}},capture(p)))
p.profile_data.talents.need=1;assert(Q.matches({availability={talents={"need"}}},capture(p)))
p.profile_data.archetype.talents.g2={player_ability={ability_type="grenade_ability",ability=Abilities.psyker.psyker_throwing_knives}}
p.profile_data.talents.g2=1;s=capture(p);assert(s.complete and s.grenade_ability=="psyker_throwing_knives" and s.resources.grenade_charges)
-- Conflicting selected skills wait until the live/profile data settles.
p.profile_data.talents.g=1;assert(not capture(p).complete);p.profile_data.talents.g=nil
p.profile_data.loadout.slot_secondary.weapon_progression_template="lasgun_p1_m1"
s=capture(p);assert(s.resources.ammo and s.resources.reload and s.weapons.lasgun_p1_m1)
p.profile_data.loadout.slot_secondary.weapon_progression_template="plasmagun_p1_m1"
s=capture(p);assert(s.resources.ammo and s.resources.overheat)
p.profile_data.loadout.slot_secondary=nil;assert(not capture(p).complete)
assert(not Q.matches({},Q.capture(nil)))
-- Cover every actual Blitz/combat record; charges come from native definitions.
local combinations=0
for class,a in pairs(Abilities) do for gn,g in pairs(a) do if g.ability_type=="grenade_ability" then
 for cn,c in pairs(a) do if c.ability_type=="combat_ability" then
  local b=capture(profile(class,gn,cn,"lasgun_p1_m1"));assert(b.complete,class..gn..cn)
  assert(b.grenade_ability==gn and b.combat_ability==c.ability_group)
  assert(b.resources.grenade_charges==((g.max_charges or 0)>0))
  assert(b.resources.combat_ability==((c.cooldown or 0)>0));combinations=combinations+1
 end end
end end end
-- Filter before quotas/exclusivity, in both random and saved manual modes.
local doc={id="eligibility",entries={}};local good={}
for i=1,40 do local valid=i%2==0;local id="item_"..i
 doc.entries[i]={id=id,enabled=true,tier=(math.floor((i-1)/2)%4)+1,weight=valid and 1 or 100000,
  exclusive_group=i<3 and "first" or nil,availability={archetypes={valid and "psyker" or "ogryn"}}};good[id]=valid
end
local setup=capture(profile("psyker","psyker_smite","psyker_discharge_shout","forcestaff_p1_m1"))
local eligible=function(e)return Q.matches(e,setup)end
for seed=1,1000 do local ids=E.choose(doc,{mode="random",max_total=8,tier_limits={2,2,2,2}},seed,eligible)
 assert(#ids==8);for _,id in ipairs(ids)do assert(good[id])end
end
local ids=E.choose(doc,{mode="manual",max_total=1,tier_limits={1,1,1,1},selected={"item_1","item_2"}},1,eligible)
assert(#ids==1 and ids[1]=="item_2","Invalid saved selection must not consume a slot/group")
print("Native ability capture combinations: "..combinations.."; eligible random draws: 1000")
''')
print('DIY eligibility: native ability definitions and weapon resolver, profile changes, class/Blitz/combat/talents/weapons/resources, pending builds and pre-quota filtering: PASS')

# Exercise the real CharacterSheet resolver and real tree topology, including
# profiles that carry base talents together with a chosen Blitz or upgrade.
# Only ability metadata is extracted from talent declarations: unrelated buff
# formatters and render resources are not needed by this native API call.
L.execute('''
function table.clear(t) for k in pairs(t) do t[k]=nil end end
function table.set(t) local out={} for _,v in ipairs(t)do out[v]=true end return out end
function table.make_unique(t) return t end
upairs=pairs
table.shallow_copy=table.clone
function table.append(a,b)for _,v in ipairs(b)do a[#a+1]=v end return a end
Log={info=function()end,error=function()end}
''')
archetypes={}
for name,records in abilities.items():
    source=native('scripts/settings/ability/archetype_talents/talents/'+name+'_talents')
    definitions={}
    indent='\t' if 'archetype_talents.talents = {' in source else '\t\t'
    for talent,body in re.findall(r'\n'+indent+r'(\w+) = \{(.*?)(?=\n'+indent+r'\w+ = \{|\n'+indent[:-1]+r'\},?)',source,re.S):
        entry=re.search(r'player_ability = \{\s*ability_type = "(\w+)",\s*ability = PlayerAbilities\.(\w+)',body)
        if entry:
            kind,ability=entry.groups()
            definitions[talent]={'player_ability':{'ability_type':kind,'ability':records[ability]}}
    source=native('scripts/settings/archetype/archetypes/'+name+'_archetype')
    base_body=re.search(r'\n\tbase_talents = \{(.*?)\n\t\},',source,re.S).group(1)
    base={key:int(value) for key,value in re.findall(r'(\w+) = (\d+)',base_body)}
    for key in base:definitions.setdefault(key,{})
    layout=re.search(r'\btalent_layout_file_path = "([^"]+)"',source).group(1)
    native_nodes=native_require(layout)['nodes']
    selectable={node['talent'] for _,node in native_nodes.items() if node['talent']}
    definitions={key:value for key,value in definitions.items() if key in base or key in selectable}
    archetypes[name]=tbl({'name':name,'talents':definitions,'base_talents':base,'talent_layout_file_path':layout})
L.globals().NativeArchetypes=L.table_from(archetypes)
L.globals().C=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_catalog')
L.globals().A=native_require('scripts/managers/mission_buffs/mission_buffs_allowed_buffs')
L.globals().D=native_require('scripts/settings/buff/hordes_buffs/hordes_buffs_data')
L.globals().CharacterSheet=native_require('scripts/utilities/character_sheet')
L.execute('''
local checked,blitz_branches=0,0
local known={};for name in pairs(D)do known[name]=true end
for class,archetype in pairs(NativeArchetypes)do
 local grenades,combats={},{}
 for name,definition in pairs(archetype.talents)do
  local pa=definition.player_ability
  if pa and pa.ability_type=="grenade_ability"then grenades[#grenades+1]=name
  elseif pa and pa.ability_type=="combat_ability"then combats[#combats+1]=name end
 end
 assert(#grenades>0 and #combats>0,class)
 blitz_branches=blitz_branches+#grenades
 for _,grenade in ipairs(grenades)do for _,combat in ipairs(combats)do
  local selected=table.clone(archetype.base_talents);selected[grenade]=1;selected[combat]=1
  local profile={archetype=archetype,talents=selected,loadout={slot_primary={weapon_template="combatsword_p1_m1"},slot_secondary={weapon_template="lasgun_p1_m1"}}}
  local player={profile=function()return profile end,archetype_name=function()return class end}
  local native={};CharacterSheet.class_loadout(profile,native,false,selected,true)
  local setup=Q.capture(player,"fire",W.weapon_template_from_item,true)
  assert(setup.complete,class..":"..grenade..":"..combat)
  assert(setup.grenade_ability==native.grenade_ability.name and setup.combat_ability==native.combat_ability.ability_group)
  local fallback_grenade,fallback_combat=C.resolve_profile_abilities(profile)
  assert(fallback_grenade==setup.grenade_ability and fallback_combat==setup.combat_ability)
  local _,pool=C.valid_for_setup(A,known,setup,"fire")
  for _,name in ipairs(A.legendary_buffs[class].grenade_ability[setup.grenade_ability] or {})do
   assert(pool[name],"Missing native Blitz reward: "..class..":"..grenade..":"..name)
  end
  checked=checked+1
 end end
end
-- Upgrades that have no native ability_group previously cleared the Blitz.
for _,case in ipairs({{"adamant","adamant_grenade","adamant_grenade_improved","adamant_grenade_improved"},
 {"broker","broker_blitz_flash_grenade","broker_blitz_flash_grenade_improved","broker_flash_grenade_improved"}})do
 local archetype=NativeArchetypes[case[1]]
 assert(archetype.talents[case[2]] and archetype.talents[case[3]],case[3])
 local selected=table.clone(archetype.base_talents);selected[case[2]]=1;selected[case[3]]=1
 local profile={archetype=archetype,talents=selected,loadout={slot_primary={weapon_template="combatsword_p1_m1"},slot_secondary={weapon_template="lasgun_p1_m1"}}}
 local player={profile=function()return profile end,archetype_name=function()return case[1]end}
 local setup=Q.capture(player,nil,W.weapon_template_from_item,true)
 assert(setup.complete and setup.grenade_ability==case[4],case[3])
 local _,pool=C.valid_for_setup(A,known,setup)
 assert(pool.hordes_buff_grenade_replenishment_over_time and pool.hordes_buff_extra_grenade_throw_chance)
end
print("Native talent-tree profile combinations checked: "..checked.."; Blitz branches: "..blitz_branches)
''')
print('Native profile eligibility: real CharacterSheet/tree priorities, all seven archetypes, base/replacement coexistence and upgraded Blitz reward pools: PASS')

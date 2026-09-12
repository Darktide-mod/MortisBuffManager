"""Compare production route/legendary selection against real game Lua and data."""
from harness import *
import subprocess
def native(path):
    file=GAME/(path+'.lua')
    return file.read_text(encoding='utf-8-sig') if file.exists() else subprocess.check_output(
        ['git','-c','gc.auto=0','show','HEAD:'+path+'.lua'],cwd=GAME).decode('utf-8-sig')
native_cache={}
def native_require(path):
    if path not in native_cache: native_cache[path]=L.execute(native(path),name='@native/'+path)
    return native_cache[path]
L.execute('''
upairs=pairs
function table.make_unique(t) end
table.shallow_copy=table.clone
function table.append(a,b) for _,v in ipairs(b) do a[#a+1]=v end;return a end
function table.swap_delete(t,i) t[i]=t[#t];t[#t]=nil end
function class() local t={};t.__index=t;return t end
Log={info=function() end,error=function() end}
''')
L.globals().require=native_require
allowed=native_require('scripts/managers/mission_buffs/mission_buffs_allowed_buffs')
settings=native_require('scripts/managers/mission_buffs/mission_buffs_settings')
data=native_require('scripts/settings/buff/hordes_buffs/hordes_buffs_data')
selector=native_require('scripts/managers/mission_buffs/mission_buffs_selector')
# Read the actual native wave arrays without loading unrelated mission/UI dependencies.
wave_source=native('scripts/settings/hordes_mode_settings')
waves=[int(n) for n in re.search(r'give_legendary_buffs_at_waves\s*=\s*\{([^}]+)',wave_source).group(1).replace(',',' ').split()]
catalog=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_catalog')
draft=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_draft')
L.globals().A=allowed;L.globals().S=settings;L.globals().D=data;L.globals().C=catalog
L.globals().Selector=selector;L.globals().Draft=draft;L.globals().W=tbl({'give_legendary_buffs_at_waves':waves})
L.execute('''
local known={};for name in pairs(D) do known[name]=true end
local count=0
for archetype, class_buffs in pairs(A.legendary_buffs) do
 if archetype~="generic" then
  local grenades={"missing"};for name in pairs(class_buffs.grenade_ability or {}) do grenades[#grenades+1]=name end
  local abilities={"missing"};for name in pairs(class_buffs.combat_ability or {}) do abilities[#abilities+1]=name end
  for _,grenade in ipairs(grenades) do for _,ability in ipairs(abilities) do
   local talents={};for name in pairs(class_buffs.talent_specific or {}) do talents[name]=1 end
   local setup={archetype=archetype,grenade_ability=grenade,combat_ability=ability,talents=talents}
   local p={archetype_name=function() return archetype end,player_unit={},
    peer_id=function() return "test" end,profile=function() return {talents=talents} end}
   ScriptUnit={has_extension=function() return {
    has_ability_type=function() return true end,
    equipped_abilities=function() return {grenade_ability={name=grenade},combat_ability={ability_group=ability}} end} end}
   local handler={does_player_have_buff_saved=function() return false end,give_buff_to_player=function() end}
   local selector=setmetatable({_mission_buffs_handler=handler},Selector)
   local native=selector:_get_valid_legendary_buffs_for_player_setup(p)
   local excluded={};if #native>0 then excluded[native[1]]=true end
   local pool=C.draft_for_setup(A,known,setup,D,S,W,nil,excluded)
   local expected={};for _,name in ipairs(native) do if not excluded[name] then expected[name]=true end end
   for category,list in pairs(pool.legendary) do for _,name in ipairs(list) do
    assert(expected[name] and D[name].filter_category==category,name);expected[name]=nil
   end end
   assert(next(expected)==nil,"Missing native eligible reward")
   assert(#pool.families==#A.available_family_builds)
   for _,family in ipairs(pool.families) do
    local run=Draft.new(archetype..family);local record=Draft.player(run,"player")
    local only=table.clone_instance(pool);only.families={family}
    local first=function() return 1 end
    Draft.tick(run,record,64,only,0,first)
    assert(record.active.kind=="family")
    assert(Draft.choose(run,record,record.active.id,1,64,only,1,first))
    assert(record.selected[1]==A.buff_families[family].priority_buffs[1],"Opening priority Buff")
    Draft.progress(run,.8);Draft.tick(run,record,64,only,2,first)
    local choices=0
    while record.active do
     assert(record.completed>=1 and record.completed<=9)
     for _,name in ipairs(record.active.choices) do
      assert(not D[name].is_family_buff)
     end
     choices=choices+1;assert(choices<=9)
     assert(Draft.choose(run,record,record.active.id,1,64,only,3+choices,first))
    end
    assert(#record.selected<=19 and choices==9 and record.completed==10)
    local route={};for _,name in ipairs(A.buff_families[family].buffs) do route[name]=true end
    for i,name in ipairs(record.selected) do
     if i>1 and D[name].is_family_buff then assert(route[name],"Other-route Buff leaked") end
    end
    local race=Draft.new(archetype..family,"competition");local racer=Draft.player(race,"player")
    racer.earned=64
    Draft.tick(race,racer,64,only,0,first)
    assert(Draft.choose(race,racer,racer.active.id,1,64,only,1,first))
    local route_set={};for _,name in ipairs(A.buff_families[family].priority_buffs) do route_set[name]=true end
    for name in pairs(route) do route_set[name]=true end
    local route_count=0;for _ in pairs(route_set) do route_count=route_count+1 end
    assert(#racer.selected==2 and racer.active.kind=="legendary")
    for _,name in ipairs(racer.selected) do assert(route_set[name]) end
    for pick=1,2 do
     for _,name in ipairs(racer.active.choices) do assert(not D[name].is_family_buff) end
     assert(Draft.choose(race,racer,racer.active.id,1,64,only,2+pick,first))
     assert(#racer.selected==math.min(route_count,pick+2)+pick,"Every round pairs route and non-route rewards")
    end
   end
   count=count+1
  end end
 end
end
print("Native character/Blitz/combat pool combinations checked: "..count)
''')
print('Native Mortis data: all seven archetypes, route priorities, selected-route isolation, backend exclusions, native legendary categories/weights, paired non-route choices and ten early reward rounds: PASS')

L.execute('''
local known={};for name in pairs(D)do known[name]=true end
local function pool(secondary)
 return C.draft_for_setup(A,known,{archetype="psyker",grenade_ability="psyker_smite",combat_ability="psyker_shout",talents={},resources={},weapon_slots={slot_secondary=secondary}},D,S,W)
end
local staff=pool({ranged=true});local gun=pool({ranged=true,ammo=true,reload=true})
local function names(p)local r={}for _,route in pairs(p.routes)do for _,id in ipairs(route.priority)do r[id]=true end;for _,id in ipairs(route.buffs)do r[id]=true end end
 for _,list in pairs(p.legendary)do for _,id in ipairs(list)do r[id]=true end end;return r end
local a,b=names(staff),names(gun)
assert(not table.array_contains(staff.families,"cowboy") and table.array_contains(gun.families,"cowboy"))
local n=0;for id in pairs(C.resource_requirements)do
 assert(not a[id],id);n=n+1
end;assert(n==8)
assert(b.hordes_buff_auto_clip_fill_while_melee)
-- Rebuilding a pool invalidates cards already shown, before spending a round.
local first=function()return 1 end
local run=Draft.new("swap","competition");local p=Draft.player(run,"p");p.earned=3
local only=table.clone_instance(gun);only.families={"cowboy"}
Draft.tick(run,p,3,only,0,first);local old=p.active.id
assert(not Draft.choose(run,p,old,1,3,staff,1,first));assert(#p.selected==0 and p.completed==0)
Draft.tick(run,p,3,staff,2,first);assert(p.active and p.active.id~=old)
for _,id in ipairs(p.active.choices)do assert(id~="cowboy")end
''')
print('Native resource eligibility: all eight audited dependencies, staff/gun routes and stale cards after equipment change: PASS')

L.execute('''
local names,known,sources=C.all_selectable(A,D)
local expected={}
for family,group in pairs(A.buff_families)do
 for _,list in ipairs({group.priority_buffs or {},group.buffs or {}})do for _,id in ipairs(list)do
  assert(sources[id] and sources[id].family_lookup[family],id..': missing native family provenance')
  expected[id]='family'
 end end
end
for _,id in ipairs(A.legendary_buffs.generic)do expected[id]='generic' end
for class,group in pairs(A.legendary_buffs)do if class~='generic' then
 for _,id in ipairs(group.generic or {})do expected[id]='class';assert(sources[id].archetype_lookup[class])end
 for _,kind in ipairs({'grenade_ability','combat_ability','talent_specific'})do
  for _,list in pairs(group[kind] or {})do for _,id in ipairs(list)do
   expected[id]='class';assert(sources[id].archetype_lookup[class],id..': wrong native class')
  end end
 end
end end
local count=0
for _,id in ipairs(names)do
 assert(sources[id].kind==expected[id],id..': wrong native catalog category')
 count=count+1
end
assert(count>100)
print('Native catalog provenance: '..count..' talents classified by official families, generic rewards and class/Blitz/ability requirements')
''')

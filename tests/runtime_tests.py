"""Actual runtime adapters: native Buff manager contract, mode switching, sources and authority."""
from harness import *
L.globals().M=mod
L.execute('''
function table.size(t) local n=0; for _ in pairs(t) do n=n+1 end; return n end
function M:persistent_table() self.state=self.state or {}; return self.state end
M._settings={enable_custom_mortis_buffs=true,mortis_buff_limit=2,mortis_mode="preselect"}
ALIVE={}; unit={}; ALIVE[unit]=true
mode="hub"; assets=true; host_type="solo"; is_host=true
ability={equipped_abilities=function() return {grenade_ability={name="grenade"},combat_ability={ability_group="charge"}} end,
 has_ability_type=function() return true end}
ScriptUnit={has_extension=function(_,name) return name=="ability_system" and ability or {} end}
local profile={character_id="hero",talents={}}
P={player_unit=unit,peer_id=function() return "host" end,local_player_id=function() return 1 end,
 character_id=function() return "hero" end,profile=function() return profile end,
 archetype_name=function() return "ogryn" end,is_human_controlled=function() return true end}
saved={}; applied={}; calls={add=0,remove=0}
handler={does_player_have_buff_saved=function(_,player,name) return saved[name]==true end}
manager={_game_mode_name="coop_complete_objective",_mission_buffs_handler=handler,_is_server_or_host=function() return true end,
 _add_externally_controlled_buff_to_player=function(_,player,name) assert(player==P); saved[name]=true;applied[name]=true;calls.add=calls.add+1 end,
 _remove_externally_controlled_buff_from_player=function(_,player,name) saved[name]=nil;applied[name]=nil;calls.remove=calls.remove+1 end}
Managers={player={local_player_safe=function() return P end,human_players=function() return {P} end},
 package={has_loaded=function() return assets end},
 multiplayer_session={host_type=function() return host_type end},connection={is_host=function() return is_host end,is_client=function() return not is_host end},
 state={game_mode={game_mode_name=function() return mode end,game_mode=function() return {_mission_buffs_manager=mode~="hub" and manager or nil} end},
 game_session={is_server=function() return is_host end},
 player_unit_spawn={owner=function(_,u) return u==unit and P end}}}
Allowed={buff_families={fire={buffs={"fire_a","fire_b"}},electric={buffs={"electric_a"}}},
 legendary_buffs={generic={"general_a","general_b"},ogryn={generic={"ogryn_a"}},psyker={generic={"psyker_a"}}}}
Data={};for _,name in ipairs({"fire_a","fire_b","electric_a","general_a","general_b","ogryn_a","psyker_a"}) do Data[name]={title=name,filter_category="regular"} end
Survival={};Horde={};Objectives={};AttackReports={}
''')
for path,value in {
'scripts/managers/mission_buffs/mission_buffs_allowed_buffs': L.globals().Allowed,
'scripts/settings/buff/hordes_buffs/hordes_buffs_data': L.globals().Data,
'scripts/managers/game_mode/game_modes/game_mode_survival': L.globals().Survival,
'scripts/managers/mission_buffs/horde_mission_buffs_manager': L.globals().Horde,
'scripts/ui/constant_elements/elements/mission_buffs/utilities/mission_buffs_parser': tbl({}),
'scripts/extension_systems/mission_objective/mission_objective_system': L.globals().Objectives,
'scripts/managers/attack_report/attack_report_manager': L.globals().AttackReports,
}.items(): cache[path]=value
L.execute('TestBreed={unit_breed_or_nil=function(u) return u.breed end,is_minion=function(b) return b.breed_type=="minion" end,enemy_type=function(b) return b.kind end}')
cache['scripts/utilities/breed']=L.globals().TestBreed
load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/session')
load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_buffs')
L.execute('''
M.mortis_buffs_on_all_mods_loaded()
assert(M.mortis_talent_ui_snapshot(P).editable)
assert(M.set_mortis_family_from_talent_ui(P,"fire"))
assert(M.toggle_mortis_buff_from_talent_ui(P,"fire_a"))
assert(M.toggle_mortis_buff_from_talent_ui(P,"ogryn_a"))
assert(not M.toggle_mortis_buff_from_talent_ui(P,"general_a"))
M:update_mortis_buffs(0) -- exercised below with the dot API
'''.replace('M:update_mortis_buffs(0) -- exercised below with the dot API','M.update_mortis_buffs(0)'))
L.execute('''
assert(calls.add==0)
mode="coop_complete_objective";assets=false;M.update_mortis_buffs(0.5);assert(calls.add==0)
assert(not M.mortis_talent_ui_snapshot(P).editable)
assert(not M.toggle_mortis_buff_from_talent_ui(P,"fire_b"))
assets=true;M.update_mortis_buffs(0.5);assert(calls.add==2 and applied.fire_a and applied.ogryn_a)
M._settings.mortis_buff_limit=1;M.mortis_buffs_on_setting_changed("mortis_buff_limit");M.update_mortis_buffs(0.5)
assert(table.size(applied)==1 and #M:get("tamm_mortis_selections_v1").hero==2)
M._settings.mortis_mode="draft";M._settings.mortis_buff_limit=8;M.mortis_buffs_on_setting_changed("mortis_mode");M.update_mortis_buffs(0.5)
assert(table.size(applied)==0)
local snap=M.mortis_draft_snapshot();assert(snap.active and snap.active.kind=="family" and #snap.active.choices==2)
for _,name in ipairs(snap.active.choices) do assert(name~="psyker_a","Wrong-class Buff in pool") end
assert(M.choose_mortis_draft(1));M.update_mortis_buffs(0.5)
assert(table.size(applied)==1 and M.mortis_draft_snapshot().family==snap.active.choices[1])
function hook(target,name)
 for _,h in ipairs(hooks) do if h.target==target and h.name==name then return h.fn end end
 error(name)
end
local native_calls=0
local obj={_is_server=true,active_objective=function(_,name) return name~="missing" and {is_side_mission=function() return name=="side" end} end}
local original=function() native_calls=native_calls+1;return "native" end
assert(hook(Objectives,"start_mission_objective")(original,obj,"main",1)=="native")
hook(Objectives,"start_mission_objective")(original,obj,"main",1)
hook(Objectives,"start_mission_objective")(original,obj,"side",1)
hook(Objectives,"start_mission_objective")(original,obj,"missing",1)
M.update_mortis_buffs(0.5);assert(M.mortis_draft_snapshot().earned==2 and native_calls==4)
local native_reward=function() error("Native modal reward pipeline must be suppressed") end
manager._game_mode_name="survival";mode="survival";handler.check_if_all_players_chosen_family=function() end
hook(Horde,"_request_buff_family_choice")(native_reward,manager)
hook(Horde,"_request_legendary_buff_choice")(native_reward,manager)
assert(hook(Survival,"_handle_giving_buffs_for_wave")(native_reward,{_is_server=true},2)==false)
assert(M.mortis_draft_snapshot().earned==3)
mode="coop_complete_objective";manager._game_mode_name=mode
M._settings.mortis_mode="competition";M.mortis_buffs_on_setting_changed("mortis_mode");M.update_mortis_buffs(0.5)
assert(M.mortis_draft_snapshot().earned==1)
local attack=hook(AttackReports,"add_attack_result")
for _,kind in ipairs({"horde","special","elite","monster"}) do
 local victim={breed={breed_type="minion",kind=kind}}
 attack({_is_server=true},nil,victim,unit,nil,nil,nil,1,"died")
 attack({_is_server=true},nil,victim,unit,nil,nil,nil,1,"died")
end
assert(M.mortis_draft_snapshot().progress==47.75)
attack({_is_server=false},nil,{breed={breed_type="minion",kind="monster"}},unit,nil,nil,nil,1,"died")
assert(M.mortis_draft_snapshot().progress==47.75,"Client report cannot grant host rewards")
local revision=M.mortis_rules().revision
M._settings.mortis_competition_hud_style="hidden";M.mortis_buffs_on_setting_changed("mortis_competition_hud_style")
assert(M.mortis_rules().revision==revision and M.mortis_draft_snapshot().progress==47.75,"Local HUD preference must not alter host rules or rewards")
M._settings.mortis_buff_limit=0;M.mortis_buffs_on_setting_changed("mortis_buff_limit");M.update_mortis_buffs(0.5)
assert(not M.mortis_draft_snapshot().active and table.size(applied)==0)
M.cleanup_mortis_buffs();assert(not M.mortis_draft_snapshot())
mode="hub";M.update_mortis_buffs(0.5);assert(not M.mortis_draft_snapshot())
M._settings.mortis_buff_limit=8;mode="coop_complete_objective";M.update_mortis_buffs(0.5)
assert(M.mortis_draft_snapshot().spent==0 and M.mortis_draft_snapshot().earned==1)
''')
print('Actual Buff runtime: startup, preselection lock/cap, native resource gate and add/remove calls, class eligibility, mode changes, objective dedup, survival modal suppression/waves, weighted killer attribution, zero points and second mission: PASS')

# Native BossExtension computes weakness from spawn max health, not remaining HP.
import subprocess
boss_source=subprocess.check_output(['git','-c','gc.auto=0','show','HEAD:scripts/extension_systems/boss/boss_extension.lua'],cwd=GAME).decode('utf-8-sig')
cache['scripts/settings/boss/boss_name_templates']=tbl({})
L.execute('function class() local c={};c.__index=c;return c end')
L.globals().Boss=L.execute(boss_source)
L.execute('''
M.cleanup_mortis_buffs();M._settings.mortis_mode="competition";M._settings.mortis_buff_limit=32
M._settings.mortis_kill_boss=11;M._settings.mortis_kill_weakened_boss=7.5;M._settings.mortis_kill_captain=31
M.update_mortis_buffs(.5)
local original=ScriptUnit.has_extension
ScriptUnit.has_extension=function(u,name) if name=="boss_system" then return u.boss end;return original(u,name) end
ScriptUnit.extension=function(u,name)
 if name=="health_system" then return {max_health=function() return u.max_health end} end
 if name=="unit_data_system" then return {breed=function() return u.breed end} end
end
Managers.state.difficulty={get_minion_max_health=function() return 1000 end}
local attack=hook(AttackReports,"add_attack_result")
local function victim(kind,maximum)
 local u={breed={breed_type="minion",kind=kind,name=kind,trigger_boss_health_bar_on_aggro=true},max_health=maximum}
 u.boss=setmetatable({_unit=u,_breed=u.breed},Boss);u.boss:extensions_ready();return u
end
local normal= victim("monster",1000);local weak=victim("monster",400);local captain=victim("captain",400)
assert(not normal.boss:is_weakened() and weak.boss:is_weakened())
attack({_is_server=true},nil,normal,unit,nil,nil,nil,1,"died");assert(M.mortis_draft_snapshot().progress==11)
attack({_is_server=true},nil,weak,unit,nil,nil,nil,1,"died");assert(M.mortis_draft_snapshot().progress==18.5)
attack({_is_server=true},nil,captain,unit,nil,nil,nil,1,"died");assert(M.mortis_draft_snapshot().progress==49.5)
-- Saved values (including zero/fractions) win; absent values use independent defaults.
M._settings.mortis_kill_weakened_boss=0
attack({_is_server=true},nil,victim("monster",400),unit,nil,nil,nil,1,"died")
assert(M.mortis_draft_snapshot().progress==49.5)
M.cleanup_mortis_buffs()
M._settings.mortis_kill_boss=nil;M._settings.mortis_kill_weakened_boss=nil;M._settings.mortis_kill_captain=nil
M.update_mortis_buffs(.5)
attack({_is_server=true},nil,victim("monster",1000),unit,nil,nil,nil,1,"died");assert(M.mortis_draft_snapshot().progress==40)
attack({_is_server=true},nil,victim("monster",400),unit,nil,nil,nil,1,"died");assert(M.mortis_draft_snapshot().progress==60)
attack({_is_server=true},nil,victim("captain",400),unit,nil,nil,nil,1,"died");assert(M.mortis_draft_snapshot().progress==10)
M._settings.mortis_mode="draft";M.mortis_buffs_on_setting_changed("mortis_mode")
assert(M._settings.mortis_buff_limit==32 and M.mortis_rules().limit==10)
''')
print('Actual kill hook + native BossExtension: ordinary/weak max-health flag, captain precedence, fractional weights, progress-mode host cap PASS')
L.execute('''
M.cleanup_mortis_buffs()
Allowed.available_family_builds={"fire"};Allowed.buff_families={fire={priority_buffs={"route_1"},buffs={}}}
Allowed.legendary_buffs.generic={}
for i=1,99 do
 local name="route_"..i
 if i>1 then Allowed.buff_families.fire.buffs[#Allowed.buff_families.fire.buffs+1]=name end
 Data[name]={title=name,filter_category="regular",is_family_buff=true};M.mortis_known_buffs[name]=true
end
for i=1,110 do
 local name="common_"..i;Allowed.legendary_buffs.generic[i]=name
 Data[name]={title=name,filter_category="regular"};M.mortis_known_buffs[name]=true
end
M._settings.mortis_mode="draft";M._settings.mortis_buff_limit=0
M.update_mortis_buffs(.5)
assert(M.mortis_rules().limit==10 and M.choose_mortis_draft(1))
for i=1,9 do hook(Objectives,"start_mission_objective")(function() end,{_is_server=true,active_objective=function() return {is_side_mission=function() return false end} end},"stage"..i,1) end
M.update_mortis_buffs(.5)
while M.mortis_draft_snapshot().active do assert(M.choose_mortis_draft(1));M.update_mortis_buffs(.5) end
assert(table.size(applied)==19 and M.mortis_talent_ui_snapshot(P).limit==19,"All nineteen progress Buffs reach the actual native application API: applied="..table.size(applied).." spent="..M.mortis_draft_snapshot().spent.." earned="..M.mortis_draft_snapshot().earned.." limit="..M.mortis_talent_ui_snapshot(P).limit)
M._settings.mortis_mode="competition";M._settings.mortis_buff_limit=99
M.mortis_buffs_on_setting_changed("mortis_mode");M.update_mortis_buffs(.5)
M._settings.mortis_kill_horde=100
for i=1,98 do hook(AttackReports,"add_attack_result")({_is_server=true},nil,{breed={breed_type="minion",kind="horde"}},unit,nil,nil,nil,1,"died") end
M.update_mortis_buffs(.5)
while M.mortis_draft_snapshot().active do assert(M.choose_mortis_draft(1));M.update_mortis_buffs(.5) end
assert(table.size(applied)==197 and M.mortis_rules().limit==99 and M.mortis_talent_ui_snapshot(P).limit==197,"Round quota must not truncate actual Buff application to 99")
M._settings.mortis_buff_limit=2;M.mortis_buffs_on_setting_changed("mortis_buff_limit");M.update_mortis_buffs(.5)
assert(table.size(applied)==3)
M._settings.mortis_buff_limit=99;M.mortis_buffs_on_setting_changed("mortis_buff_limit");M.update_mortis_buffs(.5)
assert(table.size(applied)==197 and not M.mortis_draft_snapshot().active)
M.cleanup_mortis_buffs();assert(table.size(applied)==0)
''')
print('Native application adapter: fixed progress 19, competition 99 rounds / 197 Buffs, round-bound reductions, restoration and removal PASS')

L.execute('''
local helper="hordes_buff_ogryn_basic_box_spawns_cluster"
local old=ability.equipped_abilities
local old_mode,old_limit=M._settings.mortis_mode,M._settings.mortis_buff_limit
ability.equipped_abilities=function()return {grenade_ability={name="ogryn_grenade_box"},combat_ability={ability_group="charge"}}end
M._settings.mortis_mode="preselect";M._settings.mortis_buff_limit=0
M.mortis_buffs_on_setting_changed("mortis_mode");M.update_mortis_buffs(.5)
assert(applied[helper] and table.size(applied)==1,"Basic box helper is independent of reward quota")
ability.equipped_abilities=old;M.update_mortis_buffs(.5)
assert(not applied[helper],"Changing Blitz removes our helper")
ability.equipped_abilities=function()return {grenade_ability={name="ogryn_grenade_box"},combat_ability={ability_group="charge"}}end
saved[helper]=true;M.update_mortis_buffs(.5);M.cleanup_mortis_buffs()
assert(saved[helper] and not applied[helper],"Already native-owned helper must not be adopted or removed")
saved[helper]=nil;M.update_mortis_buffs(.5);assert(applied[helper]);M.cleanup_mortis_buffs();assert(not saved[helper])
ability.equipped_abilities=old;M._settings.mortis_mode=old_mode;M._settings.mortis_buff_limit=old_limit
M.mortis_buffs_on_setting_changed("mortis_mode");M.cleanup_mortis_buffs()
''')
print('Basic Ogryn box adapter: no reward quota consumed, Blitz changes, native ownership preservation and cleanup: PASS')

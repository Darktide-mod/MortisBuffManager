"""Project-local migration, DMF localization/toggling and SoloPlay/Realms authority."""
from harness import *

name=PROJECT.name
L.globals().tested_mod=mod
L.globals().tested_name=name
L.execute('''
Application.user_setting=function() return {TalentAndMortisManager={local_talent_points=99,
    tamm_custom_talent_builds_v1={hero={points=99}},enable_custom_talent_points=true,
    enable_custom_mortis_buffs=true,mortis_buff_limit=64,tamm_mortis_selections_v1={hero={"buff_a"}}}} end
''')
load_mod(f'{name}/scripts/mods/{name}/modules/migration')
key='local_talent_points' if name=='TalentPointManager' else 'mortis_buff_limit'
foreign_key='tamm_mortis_selections_v1' if name=='TalentPointManager' else 'tamm_custom_talent_builds_v1'
assert mod.get(mod,key)==(99 if name=='TalentPointManager' else 64)
assert mod.get(mod,foreign_key) is None
mod.set(mod,key,50)
load_mod(f'{name}/scripts/mods/{name}/modules/migration')
assert mod.get(mod,key)==50
assert len(list(L.globals().mods.keys()))==1
print('Standalone one-time settings migration and subsystem isolation: PASS')

load_mod(f'{name}/scripts/mods/{name}/modules/session')
L.execute('''
for _,case in ipairs({{"solo",true,true},{"solo_backend",true,true},{"realms",true,true},{"realms",false,false}}) do
    Managers.state={game_mode={game_mode_name=function() return "havoc" end},game_session={is_server=function() return case[2] end}}
    Managers.multiplayer_session={host_type=function() return case[1] end}
    Managers.connection={is_host=function() return case[2] end,is_client=function() return not case[2] end}
    assert(tested_mod.is_server_authority()==case[3])
end
Managers.state={}
''')
print('SoloPlay and Realms host/client authority: PASS')

assert data.is_togglable is True
competition=next(widget for _,widget in data.options.widgets.items() if widget.setting_id=='mortis_competition_group')
assert {widget.setting_id: widget.default_value for _,widget in competition.sub_widgets.items()} == {
    'mortis_kill_horde': .25, 'mortis_kill_special': 5, 'mortis_kill_elite': 2.5,
    'mortis_kill_boss': 40, 'mortis_kill_weakened_boss': 20, 'mortis_kill_captain': 50}
def check_no_debug(widgets):
    for _,widget in widgets.items():
        assert not (widget.setting_id or '').startswith('mortis_debug_')
        if widget.sub_widgets: check_no_debug(widget.sub_widgets)
check_no_debug(data.options.widgets)
mod.set(mod,'mortis_debug_input',True)
stable_data=load_mod(f'{name}/scripts/mods/{name}/{name}_data')
assert mod.get(mod,'mortis_debug_input') is False
assert mod._settings.mortis_debug_input is False
check_no_debug(stable_data.options.widgets)
print('Stable build: no Debug controls and previously enabled diagnostics cleared: PASS')
for k,entry in mod.localization.items():
    formats=[]
    for lang in ('en','zh-cn','zh-tw'):
        assert isinstance(entry[lang],str) and entry[lang],(k,lang)
        if lang=='en': assert not re.search('[\u3400-\u9fff]',entry[lang]),k
        formats.append(re.findall(r'%(?:[-+ #0]*\d*(?:\.\d+)?[cdfgiousxXq]|%)',entry[lang]))
    assert formats[0]==formats[1]==formats[2],k
for lang in ('en','zh-cn','zh-tw'):
    L.globals().test_language=lang
    L.execute('''
Application.user_setting=function() return test_language end
DMFMod={}; CLASS.LocalizationManager={}
local dmf=new_test_mod("DMF")
dmf.io_dofile=function() return {} end
function dmf:get_name() return "DMF" end
function tested_mod:get_name() return tested_name end
''')
    lua_file(FIXTURES/'mods/dmf/scripts/mods/dmf/modules/core/localization.lua')
    mod.localize=L.globals().DMFMod.localize
    L.globals().mods.DMF.initialize_mod_localization(mod,mod.localization)
    for key,value in mod.localization.items():
        specs=re.findall(r'%(?:[-+ #0]*\d*(?:\.\d+)?[cdfgiousxXq]|%)',value[lang])
        result=mod.localize(mod,key,*[3 for spec in specs if spec!='%%'])
        assert isinstance(result,str) and result!='<'+key+'>',(lang,key)
print('Three languages through the actual DMF formatter: PASS')

# Exercise actual entrypoint callbacks while stubbing the heavyweight game subsystems.
kind='custom_talents' if name=='TalentPointManager' else 'mortis_buffs'
L.globals().tested_kind=kind
L.execute('''
local dmf=mods.DMF
tested_mod._togglable=true
function tested_mod:get_internal_data(key)
    if key=="is_togglable" then return self._togglable end
    if key=="is_enabled" then return self:is_enabled() end
    return false
end
function dmf.set_internal_data(m,key,value) if key=="is_enabled" then m._enabled=value end end
function dmf.inject_hud_elements() end
function dmf.remove_injected_hud_elements() end
function dmf.mod_enabled_event(m,initial) if m.on_enabled then m.on_enabled(initial) end end
function dmf.mod_disabled_event(m,initial) if m.on_disabled then m.on_disabled(initial) end end
tested_mod._cleanup_calls=0; tested_mod._update_calls=0
tested_mod.io_dofile=function(self,path)
    if path:find("diy_mortis",1,true) then return {update=function() tested_mod._diy_updates=(tested_mod._diy_updates or 0)+1 end,finish=function() tested_mod._diy_finishes=(tested_mod._diy_finishes or 0)+1 end} end
    if path:find("workspace_router",1,true) then return {install=function() end,enable=function() end,cleanup=function() end,open=function() return true end} end
    if path:find("_data",1,true) then return {options={widgets={}}} end
end
tested_mod["cleanup_"..tested_kind]=function() tested_mod._cleanup_calls=tested_mod._cleanup_calls+1 end
tested_mod["update_"..tested_kind]=function() tested_mod._update_calls=tested_mod._update_calls+1 end
tested_mod.resume_custom_talents=function() end
tested_mod.release_mortis_talent_ui_package=function() end
tested_mod.cleanup_mortis_talent_ui=function() end
''')
load_mod(f'{name}/scripts/mods/{name}/{name}')
lua_file(FIXTURES/'mods/dmf/scripts/mods/dmf/modules/core/toggling.lua')
L.execute('''
mods.DMF.initialize_mod_state(tested_mod)
tested_mod.update(0.1)
assert(tested_mod._update_calls==1)
mods.DMF.mod_state_changed(tested_name,false)
assert(not tested_mod:is_enabled() and not tested_mod._hooks_enabled and tested_mod._cleanup_calls==1)
tested_mod.update(0.1)
assert(tested_mod._update_calls==1)
mods.DMF.mod_state_changed(tested_name,true)
tested_mod.update(0.1)
assert(tested_mod._update_calls==2)
assert(tested_mod._diy_updates==2 and tested_mod._diy_finishes==1)
tested_mod.on_game_state_changed("exit","GameplayStateRun")
assert(tested_mod._cleanup_calls==2)
assert(tested_mod._diy_finishes==2)
''')
assert set(L.globals().mods.keys())=={name,'DMF'}
print('Actual DMF enable/disable, update suppression and mission cleanup: PASS')
L.execute('''
local original=tested_mod.io_dofile
tested_mod.io_dofile=function(self,path)
    if path:find("diy_mortis",1,true) then return false end
    return original(self,path)
end
''')
load_mod(f'{name}/scripts/mods/{name}/{name}')
L.execute('''
local before=tested_mod._update_calls
for i=1,1000 do tested_mod.update(.016) end
assert(tested_mod._update_calls==before+1000,"Other gameplay still updates after DIY initialization failure")
tested_mod.on_game_state_changed("exit","GameplayStateRun")
tested_mod.on_disabled();tested_mod.on_unload()
''')
print('Failed DIY initialization: 1,000 entrypoint updates, mission exit, disable and unload without repeated errors: PASS')

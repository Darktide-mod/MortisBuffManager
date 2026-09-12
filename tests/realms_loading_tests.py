"""Actual DMF IO loader/hooks and native class inheritance; no manual hook dispatch."""
from harness import *
import os, subprocess

def native(path):
    p=GAME/path
    return p.read_text(encoding='utf-8-sig') if p.is_file() else subprocess.check_output(
        ['git','-c','gc.auto=0','show','HEAD:'+path],cwd=GAME).decode('utf-8-sig')

realms=Path(os.environ.get('DARKTIDE_REALMS_SOURCE', FIXTURES/'mods/Realms'))
view_path='Realms/scripts/mods/Realms/views/preparation_view/preparation_view'
view_source=(realms/'scripts/mods/Realms/views/preparation_view/preparation_view.lua').read_text(encoding='utf-8-sig')
register_source=(realms/'scripts/mods/Realms/views/preparation_view/register.lua').read_text(encoding='utf-8-sig')
controls_source=(SOURCES/'MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_realms_controls.lua').read_text(encoding='utf-8-sig')
class_source=native('scripts/foundation/utilities/class.lua')
hooks_source=(FIXTURES/'mods/dmf/scripts/mods/dmf/modules/core/hooks.lua').read_text(encoding='utf-8-sig')
require_source=(FIXTURES/'mods/dmf/scripts/mods/dmf/modules/core/require.lua').read_text(encoding='utf-8-sig')

def setup():
    vm=LuaRuntime(unpack_returned_tuples=True)
    vm.globals().view_source=view_source
    vm.globals().view_path=view_path
    vm.execute('''
CLASS={}; CLASSES=CLASS; DMFMod={}; mods={}; resources={}; io_files={}
function get_mod(name) return mods[name] end
function table.is_empty(t) return next(t)==nil end
function new_mod(name)
 local m=setmetatable({_name=name,_enabled=true},{__index=DMFMod}); mods[name]=m; return m
end
function DMFMod:is_enabled() return self._enabled end
function DMFMod:get_name() return self._name end
function DMFMod:get_internal_data() return false end
function DMFMod:info(...) end
function DMFMod:warning(...) error(string.format(...)) end
function DMFMod:error(...) error(string.format(...)) end
function DMFMod:io_dofile(path)
 if path==view_path then io_view_loads=io_view_loads+1; return assert(loadstring(view_source))() end
 assert(io_files[path],path); return io_files[path]
end
function DMFMod:register_view(data) registered_view=data; return true end
local dmf=new_mod("DMF")
function dmf.check_wrong_argument_type(_,_,key,value,...)
 for _,kind in ipairs({...}) do if type(value)==kind then return false end end
 error("Invalid argument "..key..": "..type(value))
end
function dmf.safe_call_nr(_,_,fn,...) return fn(...) end
Mods={require_store={}}; require_cache={}
function require(path)
 local value=require_cache[path]
 if value==nil then
  value=resources[path]; assert(value,path); require_cache[path]=value
  Mods.require_store[path]={value}
 end
 return value
end
Mods.original_require=require
resources["scripts/foundation/utilities/error"]={}
io_view_loads=0
''')
    vm.execute(class_source)
    vm.execute('''
class("InputService"); CLASS.InputService.start_simulate_action=function() end
CLASS.InputService.stop_simulate_action=function() end
class("InputManager"); CLASS.InputManager.update=function() end
class("BaseView"); CLASS.BaseView.on_exit=function(self) self.exited=true end
local grid=class("ViewElementGrid")
grid.present_grid_layout=function(self,layout,blueprints)
 self.layout=layout; self.blueprints=blueprints; self.present_count=(self.present_count or 0)+1
end
grid.widgets=function() return {} end
grid.set_handle_grid_navigation=function() end
original_grid_present=grid.present_grid_layout
resources["scripts/ui/view_elements/view_element_grid/view_element_grid"]=grid
''')
    vm.execute(hooks_source)
    vm.execute(require_source)
    vm.execute('''
m=new_mod("MortisBuffManager"); host=true; connected=true
m.mortis_realms_controls_active=function() return m:is_enabled() and host and connected end
-- Reproduce the old registration without ever manually calling its callback.
file_callback_count=0
m:hook_require(view_path,function() file_callback_count=file_callback_count+1 end)
r=new_mod("Realms"); rows={{peer_id="host",name="Host",portrait={},skills={},weapons={}}}
r._preparation={player_rows=function() return rows end}
r._preparation_chat={restore_layout=function() end}
definitions={blueprints={player={size={1262,80}}},update_player_latency=function() end}
io_files["Realms/scripts/mods/Realms/views/preparation_view/preparation_view_definitions"]=definitions
io_files["Realms/scripts/mods/Realms/views/preparation_view/preparation_view_layout"]={}
io_files["Realms/scripts/mods/Realms/views/preparation_view/view_element_talent_tooltip"]={}
io_files["Realms/scripts/mods/Realms/views/view_packages"]={for_view=function() return {} end}
resources["scripts/settings/wwise_game_sync/wwise_game_sync_settings"]={state_groups={options={ingame_menu="menu"}}}
''')
    for path in re.findall(r'require\("([^"]+)"\)',view_source+register_source):
        if vm.globals().resources[path] is None: vm.globals().resources[path]=vm.table()
    return vm

def run(order):
    vm=setup()
    if order=='before':
        vm.globals().Controls=vm.execute(controls_source)
        vm.globals().Controls.install()
    vm.execute(register_source)
    vm.execute('''
assert(registered_view.view_settings.path==view_path)
View=require(registered_view.view_settings.path)
assert(io_view_loads==1 and file_callback_count==0,"DMF IO path must bypass hook_require")
-- Render/world boundaries only: keep the real class, row and loading methods.
View.init=function(self)
 self._player_grid=CLASS.RealmsPreparationGrid:new()
 self._sync_portraits=function() end; self._sync_player_sounds=function() end
 self._portrait_slots={}; self._clear_hover=function() end
 self:_present_player_rows(true)
end
''')
    if order=='after':
        vm.globals().Controls=vm.execute(controls_source)
        vm.globals().Controls.install()
    vm.execute('''
view=View:new()
assert(#view._player_grid.layout==3,"empty host room must show its own rule row on first construction")
assert(view._player_grid.layout[1].widget_type=="mbm_global_rules")
assert(CLASS.ViewElementGrid.present_grid_layout==original_grid_present,"unrelated grids must remain untouched")
assert(not definitions.blueprints.mbm_global_rules,"shared blueprint must remain untouched")
view:_present_player_rows(false)
assert(view._player_grid.present_count==1,"unchanged refresh must not rebuild")
rows[2]={peer_id="guest",name="Guest",portrait={},skills={},weapons={}}
view:_present_player_rows(false); assert(#view._player_grid.layout==5)
rows[2]=nil; view:_present_player_rows(false); assert(#view._player_grid.layout==3)
host=false; view:_present_player_rows(false)
assert(#view._player_grid.layout==1,"guest must not see host controls")
host=true; view:_present_player_rows(false); assert(#view._player_grid.layout==3)
view._player_grid._mbm_edit={text="77"}; view._mbm_input={}
m:disable_all_hooks(); m._enabled=false
-- Disabling hooks alone leaves the old layout and input state behind.
assert(#view._player_grid.layout==3 and view._player_grid._mbm_edit)
Controls.cleanup()
assert(#view._player_grid.layout==1 and not view._player_grid._mbm_edit and not view._mbm_input)
assert(not view._player_grid._mbm_realms_view)
m._enabled=true; m:enable_all_hooks(); view:_present_player_rows(false)
assert(#view._player_grid.layout==3)
view._player_grid._mbm_edit={}; view._mbm_input={}; view:on_exit()
assert(view.exited and not view._player_grid._mbm_edit and not view._mbm_input)
view=View:new(); assert(#view._player_grid.layout==3,"reopen must not duplicate controls")
assert(file_callback_count==0 and io_view_loads==1)
-- UIViewHandler requires the IO view again when a new room recreates it.
for room=2,4 do
 view:on_exit()
 local previous_init=View.init
 View=require(registered_view.view_settings.path)
 View.init=previous_init
 view=View:new()
 assert(io_view_loads==room)
 assert(#view._player_grid.layout==3,"reloaded room "..room.." lost global Mortis controls")
 host=false; view:_present_player_rows(false); assert(#view._player_grid.layout==1)
 host=true; view:_present_player_rows(false); assert(#view._player_grid.layout==3)
end
assert(file_callback_count==0)
-- A room can be recreated while Mortis is disabled; enabling must attach to it.
view:on_exit(); m:disable_all_hooks(); m._enabled=false; Controls.cleanup()
local init=View.init
View=require(registered_view.view_settings.path); View.init=init
view=View:new(); assert(#view._player_grid.layout==1)
m._enabled=true; m:enable_all_hooks(); Controls.refresh_hooks()
view:_present_player_rows(false); assert(#view._player_grid.layout==3)
for i=1,10 do Controls.refresh_hooks() end
view:_present_player_rows(false); assert(#view._player_grid.layout==3)
assert(CLASS.ViewElementGrid.present_grid_layout==original_grid_present)
''')
    return vm

if __name__=='__main__':
    for order in ('before','after'):
        run(order)
        print(f'Actual DMF add_require_path IO loading + native copied inheritance, hooks {order} Realms load: PASS')
    print('Old file callback never fires; fixed host-only row appears on first construction with no guests: PASS')
    print('Four consecutive room IO reloads, reload while disabled, re-enable, repeated attachment without rehook, host/guest rows and unrelated grid isolation: PASS')

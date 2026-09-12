"""Native view-handler containment, with engine drawing/worlds recorded at the boundary."""
from pathlib import Path
import subprocess
from workspace_tests import L, PROJECT, MODULE
from project_env import GAME

def native(path):
    return subprocess.check_output(
        ['git', '-c', 'gc.auto=0', 'show', 'HEAD:'+path], cwd=GAME).decode('utf-8-sig')

# The previous production shell is a compatibility fixture for an optional
# provider that still implements the original shared-window protocol.
L.execute('FixedShell=Shell; M._workspace_shell_class=nil')
L.globals().LegacyShell = L.execute((PROJECT/'tests/fixtures/workspace_shell_4_1_2.lua').read_text(encoding='utf-8'))
L.execute('M._workspace_shell_class=FixedShell')
L.globals().Lifecycle = L.execute((MODULE/'workspace_lifecycle.lua').read_text(encoding='utf-8'))
L.execute('''
local original_require=require
function require(path)
 if path=="scripts/ui/view_elements/view_element_base" then return ViewElementBase end
 if path=="scripts/ui/view_transition_ui" then return {} end
 if path=="scripts/ui/pass_templates/button_pass_templates" then
  local result=original_require(path);result.terminal_button=result.terminal_button or {};return result
 end
 return original_require(path)
end
local base_update=BaseView.update
function BaseView:update(dt,t,input)
 self.last_input=input;base_update(self,dt,t,input);return self._pass_input,self._pass_draw
end
function BaseView:is_view_requirements_complete() return not self.test_loading end
function BaseView:is_using_input() return true end
function BaseView:set_render_scale(value) self._render_scale=value end
function BaseView:trigger_resolution_update() end
function BaseView:draw(dt,t,input,layer)
 drawn[self.view_name]=true;self.last_draw_input=input;self.last_draw_layer=layer
 for _,element in ipairs(self._elements_array or {}) do
  if element==self._top_panel then navigation_layer=layer+element._draw_layer end
 end
end
M.diy_library={revision=0}
M.mortis_talent_ui_available=function() return true end
local empty_ui={build=function() end}
function M:io_dofile(path)
 if path:match('workspace_router$') then return Router end
 if path:match('workspace_lifecycle$') then return Lifecycle end
 if path:match('mortis_workspace_ui$') then return empty_ui end
 if path:match('mortis_workspace_model$') or path:match('diy_examples$') then return {} end
 error(path)
end
''')
L.globals().Handler = L.execute(native('scripts/managers/ui/ui_view_handler.lua'))
L.globals().Catalog = L.execute((MODULE/'mortis_workspace_view.lua').read_text(encoding='utf-8'))
L.execute('''
for name in pairs(registry.owners) do if name~=tested_name then registry.owners[name]=nil end end
local catalog_name=M.workspace_page.view_name
function flush()
 local work=closed;closed={}
 for name in pairs(work) do
  local view=views[name];if view and view.on_exit then view:on_exit() end
  views[name]=nil;pending[name]=nil
 end
 local work=pending;pending={}
 for name,context in pairs(work) do
  local view
  if name==M._workspace_window_name then
   view=setmetatable({view_name=name},Shell);view:init({},context)
  elseif name==catalog_name then
   view=setmetatable({view_name=name},Catalog);view:init({},context)
  else
   view=setmetatable({view_name=name,_elements_array={},_pass_input=true,_pass_draw=true,
    can_select_workspace_page=function() return true end,
    select_workspace_page=function() return true end,
    can_exit=function() return true end}, {__index=BaseView})
  end
  views[name]=view;if view.on_enter then view:on_enter() end
 end
end
worlds={};world_changes={}
Managers.world={is_world_enabled=function(_,name) return worlds[name] end,
 enable_world=function(_,name,enabled) worlds[name]=enabled;world_changes[#world_changes+1]={name,enabled} end,
 set_world_layer=function() end}
local room=setmetatable({view_name='realms_room',_elements_array={},_pass_input=false,_pass_draw=false,
 update=function(self,dt,t,input)
  self.last_input=input;self.updates=(self.updates or 0)+1
  return false,false
 end}, {__index=BaseView})
function reset_room()
 reset();views.realms_room=room;room.ready=true;room.room_id='unchanged_room'
 handler=setmetatable({_active_views_data={},_active_views_array={},_num_active_views=0,
  _registered_view_worlds={},_curent_frame_view_layers={},_render_scale=1,
  _get_input=function() return input,null_input,false end}, {__index=Handler})
 -- Realms registers its main, grid and tooltip worlds with this native API.
 for i,name in ipairs({'realms_main','realms_grid','realms_tooltip'}) do handler:register_view_world('realms_room',name,9+i) end
end
function frame()
 local order={'realms_room'};local seen={realms_room=true}
 for _,call in ipairs(opened) do if views[call.name] and not seen[call.name] then
  order[#order+1]=call.name;seen[call.name]=true
 end end
 local data={}
 for _,name in ipairs(order) do data[name]={name=name,instance=views[name]} end
 handler._active_views_array=order;handler._active_views_data=data;handler._num_active_views=#order
 drawn={};navigation_layer=nil
 handler:_update_views(0,0,true)
 handler:_draw_views(0,0,true,false,false)
end
function room_hidden()
 assert(not drawn.realms_room,'Realms must not draw beneath the workspace')
 assert(not worlds.realms_main and not worlds.realms_grid and not worlds.realms_tooltip,'Disable every registered Realms world')
 assert(room.last_input==null_input,'No input reaches the room underneath')
 assert(room.ready and room.room_id=='unchanged_room','Do not close or mutate the Realms session')
end
function room_restored()
 assert(drawn.realms_room and room.last_input==input,'Restore room draw and input after closing')
 assert(worlds.realms_main and worlds.realms_grid and worlds.realms_tooltip,'Restore all room worlds')
end
-- Reproduce the old draw-through behavior using the unchanged production
-- shell and a transparent child, exactly as the old catalog returned.
Shell=LegacyShell;reset_room();local old=open('equipment');frame()
assert(drawn.realms_room and worlds.realms_main and worlds.realms_grid and worlds.realms_tooltip)
assert(room.last_input==null_input,'Old behavior blocked input but kept drawing')
assert(not old._workspace_blocks_background)
baseline_reproduced=true

for _,shell_class in ipairs({FixedShell,LegacyShell}) do
 Shell=shell_class;reset_room();local s=open('mortis');frame();room_hidden()
 assert(drawn[s.view_name] and drawn[catalog_name],'Keep both navigation and catalog drawn')
 assert(views[catalog_name].last_input==input and s.last_input==input,'Catalog and navigation remain interactive')
 local background=views[catalog_name]._widgets_by_name.background
 assert(background.visible and background.scenegraph_id=='screen')
 assert(navigation_layer>views[catalog_name].last_draw_layer,'Opaque catalog background stays below the parent navigation')
 local installed_update=s.update
 for cycle=1,3 do
  -- This covers the frame waiting for a child to close, the opening frame,
  -- loading, and return to Mortis in the same window.
  local departed=views[catalog_name]
  assert(Router.open('talents'));frame();room_hidden()
  assert(not drawn[catalog_name],'The real Catalog.draw must stop in the same frame the shell releases it')
  -- Retain the departed native instance through a delayed destruction boundary.
  -- No draw, hover or keyboard update may replay it while the next page loads.
  departed.last_input=nil;local elapsed=departed._elapsed
  for waiting=1,30 do
   frame();room_hidden()
   assert(not drawn[catalog_name] and departed.last_input==nil and departed._elapsed==elapsed,
    'A released Catalog instance must remain inactive until native destruction completes')
  end
  flush();frame();room_hidden();flush()
  local child=views[s._child];assert(child);child.test_loading=true
  frame();room_hidden();assert(drawn[s.view_name] and not drawn[child.view_name])
  child.test_loading=false;frame();room_hidden();assert(drawn[child.view_name])
  assert(Router.open('mortis'));settle(s);frame();room_hidden()
  assert(s.update==installed_update,'Do not stack compatibility wrappers when reopening the page')
 end
 -- Even the invalid-session exit path must contain the background until the
 -- current shell and its child have actually been removed.
 profile_missing=true;frame();room_hidden();assert(closed[s.view_name]);profile_missing=false
 flush();flush();frame();room_restored()
 -- Open again, then use the real shared Back handler and deferred close.
 s=open('mortis');frame();room_hidden();back_pressed=true;frame();room_hidden();back_pressed=false
 assert(closed[s.view_name]);flush();flush();frame();room_restored()
 -- A new legacy instance starts unchanged: no mutation of provider classes.
 if shell_class==LegacyShell then
  s=open('equipment');frame();assert(drawn.realms_room and not s._workspace_blocks_background)
 end
end
-- Without a workspace parent, this page is itself the draw/input boundary.
local solo=setmetatable({},Catalog);solo:init({},{});solo._diy_revision=0
local pass_input,pass_draw=solo:update(0,0,input)
assert(not pass_input and not pass_draw)
''')
print('Workspace layering: old overlap reproduced; native view handler blocks Realms drawing/input and all three UI worlds; current/legacy hosts, loading, tab switches, repeated opening, Back and invalid-session restoration: PASS')

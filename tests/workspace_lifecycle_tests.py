"""Use the native handler's immediate close/destroy with the native tab menu."""
import subprocess
from workspace_tests import L, PROJECT, MODULE
from project_env import GAME

def native(path):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', 'show', 'HEAD:' + path], cwd=GAME).decode('utf-8-sig')

L.globals().Lifecycle = L.execute((MODULE / 'workspace_lifecycle.lua').read_text(encoding='utf-8'))
L.execute('''
local parent={_child='mortis'}
assert(Lifecycle.is_current(nil,'mortis'),'A standalone page has no shell ownership constraint')
assert(Lifecycle.is_current(parent,'mortis'),'The requested child is current while loading')
parent._requested_page='talents'
assert(Lifecycle.is_current(parent,'mortis'),'A queued request must not blank the current page')
parent._child=nil
assert(not Lifecycle.is_current(parent,'mortis'),'A released child must stop input and drawing immediately')
parent._child='talents'
assert(not Lifecycle.is_current(parent,'mortis'),'A departed Mortis child must not repaint over another page')
parent._child='mortis';parent._workspace_closing=true
assert(not Lifecycle.is_current(parent,'mortis'),'Closing animation must not replay old content')
local deleted=setmetatable({__deleted=true},{__index=function() error('Accessed a destroyed shell') end})
assert(not Lifecycle.is_current(deleted,'mortis'),'Never read fields from a destroyed parent')
''')
L.execute('FixedShell=Shell; M._workspace_shell_class=nil')
L.globals().LegacyShell = L.execute((PROJECT / 'tests/fixtures/workspace_shell_4_1_2.lua').read_text(encoding='utf-8'))
L.execute('M._workspace_shell_class=nil')
# Exact installed 0.5.1 shell; relocate only its owner/router in this fixture.
installed_shell=(PROJECT/'tests/fixtures/workspace_shell_realms_0_5_1.lua').read_text(encoding='utf-8')
installed_shell=installed_shell.replace('get_mod("realms_loadout")','get_mod("MortisBuffManager")')
installed_shell=installed_shell.replace('realms_loadout/scripts/mods/realms_loadout/workspace_router',
                                      'MortisBuffManager/scripts/mods/MortisBuffManager/modules/workspace_router')
L.globals().InstalledShell=L.execute(installed_shell)
L.execute('M._workspace_shell_class=FixedShell')
L.execute('''
local original_require = require
function require(path)
 if path == "scripts/ui/view_transition_ui" then return {} end
 if path == "scripts/ui/view_elements/view_element_base" then return ViewElementBase end
 if path == "fixture_shell" then return Shell end
 if path == "fixture_child" then return Child end
 return original_require(path)
end
function table.index_of(t,value) for i,v in ipairs(t) do if v==value then return i end end;return -1 end
DevParameters={ui_unsafe_view_destroy=true}
Log={error=function(_,message) error(message) end}
Managers.account={leaving_game=function() return false end}
Managers.event={unregister=function() end}
function BaseView:entered() return true end
function BaseView:trigger_on_exit_animation() end
function BaseView:on_exit_animation_done() return true end
function BaseView:destroy() self.__deleted=true end
function BaseView:is_view_requirements_complete() return not self.test_loading end
function BaseView:is_using_input() return true end
function BaseView:draw() drawn[self.view_name]=true end
function BaseView:set_render_scale(value) self._render_scale=value end
function BaseView:trigger_resolution_update() end
local original_init = BaseView.init
function BaseView:init(definitions,settings,context)
 self.view_name=settings.name
 original_init(self,definitions,settings,context)
end
Child={};Child.__index=Child;setmetatable(Child,{__index=BaseView})
function Child:new(settings,context)
 local child=setmetatable({view_name=settings.name,_context=context,_pass_input=true,_pass_draw=true,
  _elements_array={},subtab=context.workspace_tab},Child)
 if context.workspace_tab=='mortis' and patch_legacy then Lifecycle.attach(context.parent) end
 return child
end
function Child:on_enter() end
function Child:on_exit()
 child_exits[self.view_name]=(child_exits[self.view_name] or 0)+1
 if reentrant_close then self._context.parent:_close_page() end
end
function Child:update() return true,true end
function Child:can_exit() return true end
function Child:can_select_workspace_page() return true end
function Child:select_workspace_page(tab) self.subtab=tab;return true end
''')
L.globals().Handler = L.execute(native('scripts/managers/ui/ui_view_handler.lua'))
L.execute('''
local initial_ui=Managers.ui
function reset_native(shell,patched)
 Shell=shell;patch_legacy=patched;reset();child_exits={};drawn={};reentrant_close=false
 handler=setmetatable({_active_views_data={},_active_views_array={},_num_active_views=0,
  _registered_view_worlds={},_curent_frame_view_layers={},_render_scale=1,
  _get_time=function() return 1 end,_get_input=function() return input,null_input,false end,
  _transition_ui={destroy=function() end},_view_list={}}, {__index=Handler})
 handler._view_list[M._workspace_window_name]={path='fixture_shell',name=M._workspace_window_name}
 for _,entry in ipairs(Router.entries(P)) do
  handler._view_list[entry.page.view_name]={path='fixture_child',name=entry.page.view_name}
 end
 Managers.ui={get_input_alias_key=function(_,key) return key end}
 for _,method in ipairs({'view_active','view_instance','close_view','is_view_closing'}) do
  Managers.ui[method]=function(_,...) return handler[method](handler,...) end
 end
 function Managers.ui:open_view(name,a,b,c,d,context)
  opened[#opened+1]={name=name,context=context}
  handler:open_view(name,a,b,c,d,context)
  local instance=handler:view_instance(name)
  if instance and instance.on_enter then instance:on_enter() end
  return true
 end
 assert(Router.open('mortis'))
 local s=handler:view_instance(M._workspace_window_name)
 handler:_update_views(.016,1,true)
 assert(s._selected_page=='mortis' and handler:view_active(s._child))
 return s
end

-- Reproduce the exact logged crash: the native destroy loop removes the
-- child first, then the legacy shell unconditionally tries to close it again.
local s=reset_native(LegacyShell,false)
local ok,reason=pcall(function() handler:destroy() end)
assert(not ok and tostring(reason):find('view_data',1,true),tostring(reason))

for _,shell in ipairs({FixedShell,LegacyShell,InstalledShell}) do
 s=reset_native(shell,true)
 local methods={s._close_page,s.on_exit}
 Lifecycle.attach(s)
 assert(s._close_page==methods[1] and s.on_exit==methods[2],'Install only once per parent window')
 local mortis=Router.page('mortis',P).view_name
 for cycle=1,8 do
  for _,tab in ipairs({'talents','equipment','cosmetics','forge','mortis'}) do
   tab_widget(s,tab).content.hotspot.pressed_callback()
   for frame=1,4 do handler:_update_views(.016,frame,true) end
   assert(s._selected_page==tab and s._child==Router.page(tab,P).view_name)
   local count=#opened
   for frame=1,120 do
    handler:_update_views(.016,frame,true);drawn={};handler:_draw_views(.016,frame,true,false,false)
    assert(tab_widget(s,tab).content.hotspot.is_selected,'The selected native tab stays stable')
    assert(#opened==count,'Idle frames must never reopen a previous page')
    assert((tab=='mortis')==not not drawn[mortis],'The departed Mortis page must not draw')
   end
  end
 end
 -- Atomic shutdown discards queued tab requests and accepts native child-first teardown.
 assert(Router.open('talents'))
 handler:destroy()
 assert(handler._num_active_views==0 and s._requested_page==nil)
 -- A closing native view may still be updated while its exit animation runs.
 s=reset_native(shell,true);assert(Router.open('talents'));local count=#opened
 s._workspace_closing=true
 assert(not s:select_page('equipment'))
 for frame=1,30 do handler:_update_views(.016,frame,true) end
 assert(#opened==count,'Closing windows cannot open a queued or newly clicked page')
 handler:destroy()
 -- Force-close callback reentry must not recursively destroy the same child.
 s=reset_native(shell,true);reentrant_close=true
 s:_close_page()
 assert(child_exits[mortis]==1 and not handler:view_active(mortis))
 reentrant_close=false;handler:destroy()
end
Managers.ui=initial_ui
''')
print('Workspace lifecycle: logged native child-first teardown crash reproduced; current/legacy/installed Realms Loadout 0.5.1 hosts, synchronous close, native tab callbacks, 4800 stable frames per host, no stale Mortis drawing or repeated opens: PASS')

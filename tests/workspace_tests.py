"""Run the actual independent extension protocol across async UI boundaries."""
from pathlib import Path
import sys
from project_env import PROJECT
from lupa.luajit21 import LuaRuntime
NAME = PROJECT.name
MODULE = PROJECT / 'src' / NAME / 'scripts/mods' / NAME
if NAME != 'realms_loadout': MODULE /= 'modules'
L = LuaRuntime(unpack_returned_tuples=True)
L.globals().tested_name = NAME
L.execute('''
function table.clone_instance(t)
 if type(t)~="table" then return t end
 local r={};for k,v in pairs(t) do r[k]=table.clone_instance(v) end;return r
end
mods={DMF={}};views={};pending={};closed={};opened={};events={}
M={_enabled=true,commands={}};mods[tested_name]=M
function M:is_enabled() return self._enabled end
function M:localize(k) return k end
function M:add_require_path() end
registered={}
function M:register_view(v) registered[v.view_name]=v.view_settings end
function M:command(name,help,fn) self.commands[name]=fn end
function M:notify(message) notified=message end
function get_mod(name)
 assert(name==tested_name or name=="DMF" or name=="Realms", "Optional mod lookup: "..name)
 return mods[name]
end
function Localize(key) return key end
P={character_id=function() return character or "hero" end,profile=function() if profile_missing then return nil end;return {archetype={},selected_nodes={native=1}} end}
Managers={player={local_player_safe=function() return P end},connection={_connection_host={}}}
Managers.ui={view_instance=function(_,name) return views[name] end,
 view_active=function(_,name) return views[name]~=nil or pending[name]~=nil end,
 open_view=function(_,name,_,_,_,_,context)
  assert(not views[name] and not pending[name],"duplicate open "..name)
  assert(name~="inventory_background_view","Never open the I-key window")
  opened[#opened+1]={name=name,context=context};pending[name]=context
 end,
 close_view=function(_,name,force) closed[name]=true end}
BaseView={}
function BaseView:init(definitions,settings,context)
 self._definitions=definitions;self._widgets_by_name={};self._widgets={}
 for name,def in pairs(definitions.widget_definitions) do self._widgets[#self._widgets+1]=self:_create_widget(name,def) end
end
function BaseView:_create_widget(name,def)
 local w=table.clone_instance(def);w.name=name;w.offset={0,0,0};self._widgets_by_name[name]=w;return w
end
function BaseView:_unregister_widget_name(name) self._widgets_by_name[name]=nil end
function BaseView:on_enter() end
function BaseView:on_exit() end
function BaseView:update() end
function BaseView:_register_event(event,method) events[event]=method end
function BaseView:_unregister_event(event) events[event]=nil end
function class(name,parent)
 local c={super=BaseView};c.__index=c;setmetatable(c,{__index=BaseView});return c
end
function require(path)
 if path=="scripts/ui/views/views" then return {inventory_background_view={levels={"native_inventory_scene"},disable_game_world=true}} end
 if path=="scripts/ui/views/base_view" then return BaseView end
 if path=="scripts/ui/pass_templates/button_pass_templates" then return {terminal_button={}} end
 if path=="scripts/managers/ui/ui_widget" then
  return {create_definition=function(passes,scene,content) content=content or {};content.hotspot={};return {content=content,scenegraph_id=scene} end}
 end
 error(path)
end
input={get=function(_,key) return key=="back" and back_pressed or false end}
function tick(shell) return shell:update(0.016,1,input) end
function flush()
 local work=closed;closed={}
 for name in pairs(work) do
  local view=views[name];if view and view.on_exit then view:on_exit() end
  views[name]=nil;pending[name]=nil
 end
 local work=pending;pending={}
 for name,context in pairs(work) do
  if name:find("workspace_view",1,true) then
   local view=setmetatable({view_name=name},Shell)
   view:init({},context);views[name]=view;view:on_enter()
  else
   views[name]={subtab=context.workspace_tab,can_exit=function() return not busy end,
    can_select_workspace_page=function() return ready~=false and not busy end,
    select_workspace_page=function(self,tab) if ready==false or busy then return false end;self.subtab=tab;return true end}
  end
 end
end
function settle(s) for i=1,4 do tick(s);flush() end end
function reset() views={};pending={};closed={};opened={};events={} end
function open(tab)
 assert(Router.open(tab));flush();local s=views[M._workspace_window_name];settle(s);return s
end
''')
from workspace_menu_test_env import install
install(L, PROJECT.parent.parent)
router = L.execute((MODULE/'workspace_router.lua').read_text(encoding='utf-8'))
L.globals().Router = router
L.globals().M.io_dofile = lambda *_: router
router.install()
assert L.globals().registered[NAME.lower()+"_workspace_native_view"].levels[1]=="native_inventory_scene"
L.globals().Shell = L.execute((MODULE/'workspace_shell.lua').read_text(encoding='utf-8'))
command = {'realms_loadout':'rl','TalentPointManager':'talentpoints','MortisBuffManager':'mortisbuffs'}[NAME]
assert L.globals().M.commands[command] is not None
assert set(L.globals().M.commands.keys()) == {command}, 'Do not retain conflicting command aliases.'
L.execute('''
registry=mods.DMF._inventory_extensions_v1
local function page(name,selectable)
 return {view_name=name,available=function() return not blocked end,
  prepare=function() prepared=(prepared or 0)+1 end,
  commit=function() committed=(committed or 0)+1 end,
  can_select=selectable and function(v,tab) return v:can_select_workspace_page(tab) end or nil,
  select=selectable and function(v,tab) return v:select_workspace_page(tab) end or nil}
end
local equipment,talents,mortis=page("equipment_child",true),page("talents_child"),page("mortis_child")
local function entry(id,order,p)
 return {id=id,order=order,label=function() return id end,page=p}
end
fixtures={
 {entry("equipment",10,equipment),entry("cosmetics",20,equipment),entry("forge",30,equipment)},
 {entry("talents",40,talents)},
 {entry("mortis",50,mortis)},
}
local function register(i)
 registry.owners["unknown_extension_"..i]={enabled=function() return true end,
  pages=function() return fixtures[i] end,window="unknown_window_"..i,request=function() end}
end
function tab_widget(s,id)
 for i,entry in ipairs(s._entries) do if entry.id==id then return s._top_panel._content_widgets[i] end end
end
function has_tab(s,id) return tab_widget(s,id)~=nil end
-- All subsets, including zero extensions: native functionality always exists.
for mask=0,7 do
 for i=1,3 do
  registry.owners["unknown_extension_"..i]=nil
  if math.floor(mask/2^(i-1))%2==1 then register(i) end
 end
 reset();local s=open("equipment")
 local loadout=mask%2==1;local talent=math.floor(mask/2)%2==1;local mortis_on=math.floor(mask/4)%2==1
 assert(has_tab(s,"equipment") and has_tab(s,"cosmetics") and has_tab(s,"talents"))
 assert(has_tab(s,"forge")==loadout and has_tab(s,"mortis")==mortis_on)
 assert(#s._widgets==1 and #s._elements_array==2,"One native panel and one close legend; no floating header")
 assert(s._top_panel:num_entries()==3+(loadout and 1 or 0)+(mortis_on and 1 or 0),"No hidden placeholders")
 assert((not Router.page("equipment",P).native)==loadout)
 assert((not Router.page("talents",P).native)==talent)
 for _,entry in ipairs(Router.entries(P)) do
  assert(Router.open(entry.id));settle(s)
  assert(s._selected_page==entry.id and views[s._child])
 end
 assert(not Router.open("unregistered"))
 -- Return to every native/extended page without ever opening original inventory.
 assert(Router.open("talents"));settle(s);assert(Router.open("equipment"));settle(s)
 local count=0;for _,call in ipairs(opened) do if call.name:find("workspace_view",1,true) then count=count+1 end end
 assert(count==1)
end
-- Extension IDs and insertion points are not enumerated by the consumer.
registry.owners.external={enabled=function() return true end,window="external_shell",request=function() end,
 pages=function() return {extra} end}
extra=entry("future_page",35,page("future_child"))
reset();local s=open("future_page");assert(has_tab(s,"future_page"))
registry.owners.external=nil;settle(s)
assert(not has_tab(s,"future_page") and s._selected_page=="equipment")
-- A feature disabling its replacement restores native talents.
fixtures[2][1].applies=function() return feature_on end;feature_on=true
assert(Router.open("talents"));settle(s);feature_on=false;settle(s)
assert(s._selected_page=="talents" and s._page.native)
feature_on=true;settle(s);assert(s._page==talents)
fixtures[2][1].applies=nil
-- Withdraw a live provider and destroy its actual controls; fallback to native.
assert(Router.open("forge"));settle(s)
local retired_panel=s._top_panel
registry.owners.unknown_extension_1=nil;settle(s)
assert(not has_tab(s,"forge") and s._selected_page=="equipment" and s._page.native)
assert(retired_panel._destroyed and next(retired_panel._widgets_by_name)==nil,"Remove the actual native element")
register(1);settle(s);assert(has_tab(s,"forge") and s._page==equipment)
assert(Router.open("mortis"));settle(s)
registry.owners.unknown_extension_3=nil;settle(s)
assert(not has_tab(s,"mortis") and s._selected_page=="equipment")
register(3);settle(s)
-- Legitimate edit restrictions remain; they do not signal missing mods.
blocked=true;tick(s);assert(has_tab(s,"mortis") and tab_widget(s,"mortis").content.hotspot.disabled)
assert(not Router.open("mortis"));blocked=false
-- The inventory instance is reused across Equipment/Cosmetics/Forge.
assert(Router.open("equipment"));settle(s);local child=views[s._child];local count=#opened
for _,tab in ipairs({"cosmetics","forge","equipment"}) do
 assert(Router.open(tab));settle(s);assert(views[s._child]==child and #opened==count and child.subtab==tab)
end
ready=false;tick(s);assert(not Router.open("cosmetics"));ready=true
busy=true;assert(not Router.open("talents"));busy=false
-- The native menu handles clicks, selection effects, sound and shoulder keys.
tab_widget(s,"forge").content.hotspot.pressed_callback();settle(s)
assert(s._selected_page=="forge" and views[s._child]==child)
assert(s._top_panel._last_sound=="native_tab_pressed")
s._top_panel:_select_next_tab("forward");settle(s)
assert(s._selected_page=="talents" and tab_widget(s,"talents").content.hotspot.is_selected)
blocked=true;tick(s);s._top_panel:_select_next_tab("forward");settle(s)
assert(s._selected_page=="talents");blocked=false
assert(Router.open("equipment"));settle(s)
-- A child's visible native Back legend prevents a duplicate shared entry.
child=views[s._child];child._input_legend_element={_entries={{input_action="back",is_visible=true}}}
assert(not s:_needs_close_legend());child._input_legend_element=nil;assert(s:_needs_close_legend())
-- Cancel a queued navigation by clicking the current page.
assert(Router.open("talents"));assert(Router.open("equipment"));settle(s);assert(s._selected_page=="equipment")
-- Events are declared by an extension, never by the shared shell.
talents.nodes_event="fixture_nodes";talents.nodes_updated=function(parent,nodes) recorded=nodes end
assert(Router.open("talents"));settle(s);assert(events.fixture_nodes)
s:event_workspace_nodes_updated(42);assert(recorded==42)
assert(Router.open("equipment"));settle(s);assert(not events.fixture_nodes)
-- Wait for grandchildren too, so pending native views cannot overlap.
child=views[s._child];child.workspace_children=function() return {"grandchild"} end
views.grandchild={};assert(Router.open("talents"));tick(s);flush();tick(s)
assert(not pending.talents_child and not views.talents_child)
views.grandchild=nil;settle(s);assert(s._selected_page=="talents")
-- Requests to a not-yet-created shell reuse the pending window.
reset();assert(Router.open("equipment"));assert(Router.open("talents") and #opened==1)
flush();s=views[M._workspace_window_name];settle(s);assert(s._selected_page=="talents")
-- Resources may disappear while entering/leaving a Realms room.
profile_missing=true;assert(not Router.open("talents"));tick(s);assert(s._workspace_invalid);flush()
profile_missing=false;reset();s=open("talents")
-- Character/connection boundaries discard obsolete edits and close.
character="different";tick(s);assert(s._workspace_invalid and closed[M._workspace_window_name]);flush();character=nil
reset();s=open("talents");Managers.connection._connection_host={};tick(s);assert(s._workspace_invalid);flush()
reset();views.inventory_background_view={marker=true};assert(not Router.open("talents"))
assert(views.inventory_background_view.marker)
reset();s=open("talents");busy=true;back_pressed=true;tick(s);assert(not closed[M._workspace_window_name])
busy=false;tick(s);assert(closed[M._workspace_window_name]);flush();back_pressed=false
-- Explicit unregister/re-register, including cancellation during resource load.
reset();assert(Router.open("equipment"));M._enabled=false;Router.cleanup();flush()
assert(not registry.owners[tested_name] and not Router.open("equipment") and not views[M._workspace_window_name])
M._enabled=true;Router.enable();s=open("talents")
assert(registry.owners[tested_name]);M._enabled=false;Router.cleanup();flush()
assert(not views[M._workspace_window_name]);M._enabled=true;Router.enable()
-- Geometry for the supported three-to-five-page combinations.
for i=1,3 do register(i) end
reset();geometry=open("equipment")
''')
g = L.globals().geometry
scene = g._top_panel._definitions.scenegraph_definition
assert g._definitions.scenegraph_definition.header is None
assert g._widgets_by_name.close is None
assert scene.top_panel.scale=='fit_width'
assert scene.top_panel.position[2]==100 and scene.top_panel.size[2]==100
for width,height in ((1920,1080),(2560,1440),(3840,2160),(1920,1200),(3440,1440),(5120,1440),(1600,1200)):
    for scale in (min(width/1920,height/1080),height/1080):
        L.globals().RESOLUTION_LOOKUP.width=width
        g._render_scale=scale
        L.globals().tick(g)
        panel=g._top_panel
        length=panel._grid_length
        assert length<=width/scale-160
        assert abs(panel._ui_scenegraph.grid_content_pivot.position[1]+length/2)<0.001
        rects=[(w.offset[1],w.offset[1]+w.content.size[1]) for w in panel._content_widgets.values()]
        assert all(a[1]<b[0] for a,b in zip(rects,rects[1:]))
        assert all(w.content.size[2]==100 and w.style.text.font_size==36 for w in panel._content_widgets.values())
L.globals().RESOLUTION_LOOKUP.width=1920;g._render_scale=1;L.globals().tick(g)
for i,w in g._top_panel._content_widgets.items():
    assert w.content.size[1]==g._navigation_widths[i], 'Natural widths restored after widening'
assert L.eval('require("scripts/ui/view_elements/view_element_menu_panel/view_element_menu_panel_settings").button_max_size[1]')==300
print(NAME+': native menu element, click/gamepad navigation, original sizing and adaptive fit, native fallbacks, extension removal, async children, independent saves and lifecycle guards: PASS')

L.execute("""
local calls=0;local original=Router.entries
Router.entries=function(...) calls=calls+1;return original(...) end
local panel=geometry._top_panel
for i=1,120 do tick(geometry) end
assert(calls==120 and geometry._top_panel==panel,"Resolve once per frame; do not rebuild a stable native navigation panel")
Router.entries=original
""")
print(NAME+': 120 idle frames, one extension-list resolution per frame, no native navigation rebuilds: PASS')

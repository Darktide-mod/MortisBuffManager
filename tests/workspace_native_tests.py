"""Actual native menu/navigation/save methods in the standalone fallback adapter."""
from pathlib import Path
import re, subprocess, sys
from project_env import PROJECT
ROOT = PROJECT.parent.parent
from lupa.luajit21 import LuaRuntime
NAME = PROJECT.name
MODULE = PROJECT/'src'/NAME/'scripts/mods'/NAME
if NAME != 'realms_loadout': MODULE /= 'modules'
path = 'scripts/ui/views/inventory_background_view/inventory_background_view.lua'
source = subprocess.check_output(
    ['git','-c','gc.auto=0','show','HEAD:'+path],cwd=ROOT/'dev-support/game-source').decode('utf-8-sig')
L = LuaRuntime(unpack_returned_tuples=True)
L.execute('''
function table.clone_instance(t)
 if type(t)~="table" then return t end
 local r={};for k,v in pairs(t) do r[k]=table.clone_instance(v) end;return r
end
table.clone=table.clone_instance
function table.merge_recursive(a,b) for k,v in pairs(b) do a[k]=v end;return a end
function Localize(k) return k end
function callback(fn) return fn end
Color=setmetatable({},{__index=function() return function() return {255,0,0,0} end end})
Breeds={human={body_size="human"}};ITEM_TYPES={};ItemSlotSettings={};PlayerProgressionUnlocks={}
UiSettings={};UiSoundEvents={};Views={}
ProfileUtils={get_active_profile_preset_id=function() return preset_id end,
 get_profile_preset=function() return preset end,
 save_talent_nodes_for_profile_preset=function(_,nodes) preset_write=nodes end}
TalentLayoutParser={filter_layout_talents=function(p,k,n,d)
 if d then for k,v in pairs(n) do d[k]=v end;return d end
 return table.clone(n)
end, is_talent_selection_valid=function() return valid~=false end,talents_version=function() return 1 end}
M={};function get_mod() return M end
profile={character_id="hero",archetype={breed="human",talent_layout_file_path="native_layout"},loadout={},selected_nodes={extended=99}}
player={profile=function() return profile end}
router={page=function() return {native=not override} end,native_nodes=function() return {official=1} end}
Native={super={on_exit=function() end}}
Native.__index=Native
function class() local c={super=Native};c.__index=c;setmetatable(c,{__index=Native});return c end
function Native:_add_element(_,name) assert(name~="top_panel","No duplicate menu allocated");return {} end
function Native:is_inventory_synced() return ready~=false end
function Native:can_exit() return not busy end
function Native:_update_has_empty_talent_nodes() end
function Native:_set_player_profile_information() end
function Native:_setup_profile_presets() self:event_on_profile_preset_changed(preset) end
function Native:event_on_profile_preset_changed(preset)
 if preset then self._valid_profile_equipped_talents=table.clone(preset.talents) end
end
function Native:_update_loadout_validation() end
function Native:_get_valid_new_items() return {},{} end
function Native:_update_equipped_items() end
function Native:_check_toggle_companion() end
function Native:_start_animation() end
function Native:_update_missing_warning_marker() end
function Native:_unload_portrait_icon() end
function Native:_unload_portrait_frame() end
function Native:_unload_insignia() end
function Native:_equip_local_changes() equipment_writes=(equipment_writes or 0)+1 end
views={};opened={}
Managers={ui={view_active=function(_,name) return views[name]~=nil end,
 view_instance=function(_,name) return views[name] end,
 open_view=function(_,name,_,_,_,_,ctx,settings)
  assert(name=="inventory_view" or name=="talent_builder_view",name)
  assert(settings and settings.parent_transition_view=="native_wrapper", "Use actual parent for native rendering")
  opened[#opened+1]={name=name,context=ctx};views[name]={supports_changeable_context=function() return true end}
 end,close_view=function(_,name) views[name]=nil end},
 data_service={talents={set_talents_v2=function(_,p,info) native_write=info end,release_icons=function() end}}}
function require(path)
 if path=="scripts/ui/views/inventory_background_view/inventory_background_view" then return Native end
 if path=="scripts/utilities/profile_utils" then return ProfileUtils end
 if path:find("talent_layout_parser",1,true) then return TalentLayoutParser end
 error(path)
end
''')
for method in ('_setup_top_panel','_setup_inventory','_force_select_panel_index','_on_panel_option_pressed',
               '_switch_active_view','event_player_talent_node_updated','_apply_current_talents_to_profile',
               '_save_current_talents_to_profile_preset','on_exit'):
    m = re.search(r'^InventoryBackgroundView\.'+method+r' = function\b.*?^end$',source,re.M|re.S)
    assert m, method
    L.execute(m[0].replace('InventoryBackgroundView.', 'Native.'))
panel=L.execute((MODULE/'workspace_panel.lua').read_text(encoding='utf-8'))
L.globals().M.io_dofile = lambda _,p: panel if p.endswith('workspace_panel') else L.globals().router
L.globals().View=L.execute((MODULE/'workspace_native_view.lua').read_text(encoding='utf-8'))
L.execute('''
function make(tab,readonly)
 local v=setmetatable({view_name="native_wrapper",_context={workspace_tab=tab,parent={_workspace_invalid=false}},
  _preview_player=player,_is_own_player=true,_is_readonly=readonly,_using_cursor_navigation=true,
  _active_talent_loadout={nodes={}},_widgets_by_name={loading={content={}}}},View)
 return v
end
local v=make("talents",false)
v:_setup_inventory()
assert(#opened==1 and opened[1].name=="talent_builder_view","Direct native talents without first opening equipment")
assert(v._workspace_native_indices.talents==4,"Native mastery entry changes talent index")
assert(opened[1].context.current_profile_equipped_talents.official==1)
assert(not opened[1].context.current_profile_equipped_talents.extended)
assert(not v._top_panel.visible and not v._top_panel.entries,"Only selection state, no second menu")
assert(v:select_workspace_page("equipment"));local count=#opened
assert(v:select_workspace_page("cosmetics") and #opened==count)
assert(v._active_view_context.changeable_context.tabs[1].telemetry_name=="inventory_view_cosmetics")
v:event_player_talent_node_updated({extended=99})
v:_apply_current_talents_to_profile();assert(not native_write and not preset_write,"Browsing equipment cannot save talents")
assert(v:select_workspace_page("talents"));override=true
v:event_player_talent_node_updated({extended=99});assert(not v._workspace_native_edited)
override=false;v:event_player_talent_node_updated({native_choice=1})
v:_apply_current_talents_to_profile();assert(native_write.node_tiers.native_choice==1 and not native_write.node_tiers.extended)
ready=false;assert(not v:select_workspace_page("equipment"));ready=true
busy=true;assert(not v:select_workspace_page("equipment"));busy=false
assert(not v:select_workspace_page("forge") and not v:select_workspace_page("mortis"))
assert(v:workspace_children()[1]=="talent_builder_view")
native_write=nil;v._context.parent._workspace_invalid=true;v:on_exit()
assert(not native_write and not equipment_writes,"No write after character/session invalidation")
views={};opened={};local r=make("talents",true);r:_setup_inventory()
assert(r._workspace_native_indices.talents==3 and opened[1].name=="talent_builder_view")
views={};opened={};preset_id="preset";preset={talents={saved=1}}
local e=make("equipment",false);e:_setup_inventory()
assert(e._current_profile_equipped_talents.saved==1 and not e._current_profile_equipped_talents.extended)
assert(opened[1].context.changeable_context.tabs[1].telemetry_name=="inventory_view_loadout")
assert(not e._workspace_native_edited,"Initial preset synchronization must not count as an edit")
e:event_on_profile_preset_changed({talents={new_preset=1}});e:_apply_current_talents_to_profile()
assert(native_write.node_tiers.new_preset==1,"Switching native presets still applies their normal talents")
native_write=nil;override=true;local x=make("equipment",false);x:_setup_inventory()
x:event_on_profile_preset_changed({talents={new_preset=1}});x:_apply_current_talents_to_profile()
assert(not native_write,"Equipment presets do not overwrite an active talent extension")
''')
print(NAME+': native equipment/cosmetics/talent callbacks, original preset input, extended-build write isolation and deferred exit: PASS')

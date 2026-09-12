"""Optional sibling integration: both independently installed mods, actual DMF chains."""
from realms_loading_tests import *
talent=Path(os.environ.get('DARKTIDE_TALENT_SOURCE', PROJECT.parent/'TalentPointManager/src/TalentPointManager'))
companion=talent/'scripts/mods/TalentPointManager/modules/realms_player_controls.lua'
if not companion.is_file():
    print('Optional combined Realms UI check skipped: Talent source is not present.')
    raise SystemExit(0)
for order in ('mortis_first','talent_first'):
    vm=setup()
    vm.execute('''
t=new_mod("TalentPointManager")
t.realms_talent_controls_active=function() return t:is_enabled() and host and connected end
function engine_init(self)
 self._player_grid=CLASS.RealmsPreparationGrid:new()
 self._sync_portraits=function() end; self._sync_player_sounds=function() end
 self._portrait_slots={}; self._clear_hover=function() end
 self:_present_player_rows(true)
end
function engine_update(self,dt,time,input)
 assert(self._mbm_input==raw_input and self._tpm_input==raw_input,"Both editors must receive raw input")
 assert(input==null_input,"Typing must still mask native view shortcuts")
end
''')
    vm.globals().view_source=view_source.replace('return RealmsPreparationView','RealmsPreparationView.init=engine_init\nRealmsPreparationView.update=engine_update\nreturn RealmsPreparationView')
    vm.globals().MC=vm.execute(controls_source)
    vm.globals().TC=vm.execute(companion.read_text(encoding='utf-8-sig'))
    for name in (('MC','TC') if order=='mortis_first' else ('TC','MC')):vm.globals()[name].install()
    vm.execute(register_source)
    vm.execute('''
View=require(registered_view.view_settings.path)
for i=2,4 do rows[i]={peer_id="guest"..i,name="Guest "..i,portrait={},skills={},weapons={}} end
view=View:new()
function assert_rows(players,mortis,talent)
 local counts={};local seen={}; local total=0
 for _,row in ipairs(view._player_grid.layout) do
  local kind=row.widget_type;counts[kind]=(counts[kind] or 0)+1
  if kind=="player" then seen[row.peer_id]={} end
  if kind=="mbm_deployment" then assert(not row.peer_id);seen[row.mbm_status_peer].mortis=true end
  if kind=="tpm_player_rules" then assert(not row.peer_id);seen[row.tpm_peer_id].talent=true end
  total=total+view._player_grid.blueprints[kind].size[2]+8
 end
 assert(counts.player==players,"player count "..tostring(counts.player))
 assert((counts.mbm_global_rules or 0)==(mortis and 1 or 0),"global count "..tostring(counts.mbm_global_rules))
 assert((counts.mbm_deployment or 0)==(mortis and players or 0),"Mortis status count "..tostring(counts.mbm_deployment))
 assert((counts.tpm_player_rules or 0)==(talent and players or 0),"Talent count "..tostring(counts.tpm_player_rules))
 for _,value in pairs(seen) do assert((value.mortis or false)==mortis and (value.talent or false)==talent) end
 return total-8
end
assert(assert_rows(4,true,true)==884)
-- Native Realms grid scrolls to the fourth status with both native and DIY rows.
assert(not definitions.blueprints.tpm_player_rules and not definitions.blueprints.mbm_global_rules)
local methods={View.update,View._present_player_rows,CLASS.RealmsPreparationGrid.present_grid_layout}
for i=1,30 do MC.refresh_hooks();TC.refresh_hooks() end
assert(methods[1]==View.update and methods[2]==View._present_player_rows and methods[3]==CLASS.RealmsPreparationGrid.present_grid_layout,"Repeated dual attachment must not grow wrappers")
view:_present_player_rows(true);assert_rows(4,true,true)
null_input={is_null_service=function() return true end,null_service=function(self) return self end}
raw_input={is_null_service=function() return false end,null_service=function() return null_input end}
for _,field in ipairs({"_mbm_edit","_tpm_edit"}) do
 view._player_grid[field]={};view:update(.016,1,raw_input)
 assert(not view._realms_rule_control_input);view._player_grid[field]=nil
end
m._enabled=false;m:disable_all_hooks();MC.cleanup();assert_rows(4,false,true)
m._enabled=true;m:enable_all_hooks();MC.refresh_hooks();view:_present_player_rows(false);assert_rows(4,true,true)
t._enabled=false;t:disable_all_hooks();TC.cleanup();assert_rows(4,true,false)
t._enabled=true;t:enable_all_hooks();TC.refresh_hooks();view:_present_player_rows(false);assert_rows(4,true,true)
host=false;view:_present_player_rows(false);assert_rows(4,false,false)
host=true;rows[4]=nil;view:_present_player_rows(false);assert_rows(3,true,true)
for room=2,4 do
 view:on_exit();View=require(registered_view.view_settings.path);view=View:new()
 assert_rows(3,true,true)
 for i=1,4 do TC.refresh_hooks();MC.refresh_hooks() end
 view:_present_player_rows(true);assert_rows(3,true,true)
end
assert(CLASS.ViewElementGrid.present_grid_layout==original_grid_present)
''')
    print('Dual mod controls '+order+': four-player rows, native scrolling geometry, stable hook chains, raw input, separate disable, host/guest, dropout and four room loads PASS')

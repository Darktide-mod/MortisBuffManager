"""Production hooks with native action scheduling, cost, spawn and burn methods.
Renderer, world entities and final damage services are simulated boundaries.
"""
from pathlib import Path
import sys,re,subprocess
from project_env import GAME
R=Path(__file__).resolve().parents[3]
from lupa.luajit21 import LuaRuntime
L=LuaRuntime(unpack_returned_tuples=True)
def native(name):return subprocess.check_output(['git','show','HEAD:scripts/extension_systems/weapon/actions/'+name+'.lua'],cwd=GAME).decode('utf-8-sig')
def methods(cls,file,names):
 s=native(file)
 for name in names:
  match=re.search(r'^'+re.escape(cls+'.'+name)+r' = function .*?^end\s*$',s,re.M|re.S);assert match,(cls,name);L.execute(match[0])
L.execute(r'''
function table.clear(t)for k in pairs(t)do t[k]=nil end end
math.clamp=function(v,a,b)return math.max(a,math.min(b,v))end
callbacks={};classes={};enabled=true;copies=5;paid=0;spawned={};fired={};deleted={};explosions={}
M={is_enabled=function()return enabled end,diy_mortis={ranged_salvo_count=function()return copies end}}
function M:hook_require(path,callback)callbacks[path]=callback end
function M:hook(class,name,fn)local original=class[name];class[name]=function(...)return fn(original,...)end end
get_mod=function()return M end
function attach(name,class)callbacks['scripts/extension_systems/weapon/actions/'..name](class);classes[name]=class end
function action(class)
 return setmetatable({_is_server=true,_player_unit={},_inventory_component={wielded_slot='slot_secondary'},_weapon_template={keywords={'ranged'}},
 _weapon={item={}},_critical_strike_component={is_active=false},_shot_result={},_action_settings={},_charge_component={charge_level=.7}}, {__index=class})
end
ActionSpawnProjectile={super={start=function(self,settings)self._action_settings=settings end,finish=function()end}}
ActionExplosion={super={start=function(self,settings)self._action_settings=settings end}}
ActionFlamerGas={_damage_target=function()end}
Unit={alive=function()return true end,set_unit_visibility=function()end}
Quaternion={identity=function()return 0 end}
ScriptUnit={extension=function(unit)return unit.locomotion or {}end,has_extension=function(unit)return unit.buff end}
Managers={state={unit_spawner={spawn_network_unit=function(self,...)
 local unit={charge=select(15,...),critical=select(13,...),locomotion={}};spawned[#spawned+1]=unit;return unit
end,mark_for_deletion=function(_,u)deleted[u]=true end},player_unit_spawn={relinquish_unit_ownership=function()end}}}
ActionUtility={ability_item=function()return {}end,is_within_trigger_time=function(time,dt,trigger)return time>=trigger and time-dt<trigger end}
projectile_locomotion_states={sleep='sleep'};keywords={guaranteed_smite_critical_strike='guaranteed'};DEFAULT_FIRE_TIME=.1
NetworkConstants={weapon_charge_level={min=0,max=1}};AttackSettings={attack_types={explosion='explosion'}};DEFAULT_POWER_LEVEL=500
Explosion={create_explosion=function(...)explosions[#explosions+1]={...}end}
ALIVE={}
''')
methods('ActionSpawnProjectile','action_spawn_projectile',['start','fixed_update','finish','_spawn_projectile_unit','_pay_for_projectile'])
methods('ActionExplosion','action_trigger_explosion',['start','_explode'])
methods('ActionFlamerGas','action_flamer_gas',['_burn_targets'])
L.execute(r'''
ActionSpawnProjectile._fire_projectile=function(self,t,u)
 if self.fail_fire and #fired==self.fail_fire then error('fire failure')end
 fired[#fired+1]=u;return 'fired',nil,7
end
function staff(critical,surge)
 local a=action(ActionSpawnProjectile)
 a._critical_strike_component.is_active=critical;a._projectiles_fire_offsets={};a._projectiles_fired={};a._projectile_units={};a._projectile_locomotion_extensions={}
 a._buff_extension={has_keyword=function(_,k)return surge and k=='critical_strike_second_projectile'end,stat_buffs=function()return {charge_level_modifier=1.2}end}
 a._projectile_template=function()return {}end;a._first_person_component={position=0,rotation=0};a._side_system={side_by_unit={}}
 a._check_for_critical_strike=function()end;a._weapon_action_component={time_scale=1};a._player={remote=false};a._shooting_status_component={num_shots=0}
 a._pay_warp_charge_cost_immediate=function(self,t,c)paid=paid+1;assert(c==.7)end
 a._proc_buffs=function(self)self.proc=(self.proc or 0)+1 end;a._weapon_spread_extension={randomized_spread=function()end}
 return a
end
''')
L.execute((R/'projects/MortisBuffManager/src/MortisBuffManager/scripts/mods/MortisBuffManager/modules/diy_ranged_salvo.lua').read_text(encoding='utf-8'))
L.execute(r'''
attach('action_spawn_projectile',ActionSpawnProjectile);attach('action_trigger_explosion',ActionExplosion);attach('action_flamer_gas',ActionFlamerGas)
for _,surge in ipairs({false,true})do
 spawned={};fired={};paid=0
 local a=staff(surge,surge);local setting={use_charge=true,charge_template={}}
 a:start(setting,0);assert(#spawned==(surge and 2 or 1),'Native Surge creates two sleeping originals')
 a:fixed_update(.1,.1,.1);a:fixed_update(.1,.2,.2);a:finish('done',nil,.2,.2)
 assert(#fired==(surge and 10 or 5) and #spawned==#fired)
 assert(paid==1 and a.proc==1 and a._shooting_status_component.num_shots==1 and a._charge_component.charge_level==0)
 for _,unit in ipairs(spawned)do assert(math.abs(unit.charge-.84)<1e-9 and unit.critical==surge,'Every copy retains original charge once, including delayed Surge')end
end
-- A paid interruption uses the preserved charge even after payment zeroed it.
spawned={};fired={};paid=0;local a=staff(false,false);a:start({use_charge=true,charge_template={}},0)
a:_pay_for_projectile(0);a._projectiles_paid_for=true;a:finish('interrupted',nil,0,0)
assert(#fired==5 and paid==1);for _,u in ipairs(fired)do assert(math.abs(u.charge-.84)<1e-9)end
spawned={};fired={};paid=0;a=staff(false,false);a:start({use_charge=true,charge_template={}},0);a:finish('cancelled',nil,0,0)
assert(#fired==0 and paid==0 and deleted[spawned[1]],'Unpaid cancellation does not invent an attack')
-- Native explosion start pays once; five native explosion calls preserve power/charge.
local e=action(ActionExplosion);e._action_module_charge_component={charge_level=.7};e._action_module_position_finder_component={position=0}
e._check_for_critical_strike=function()end;e._pay_warp_charge_cost_immediate=function()paid=paid+1 end
paid=0;explosions={};e:start({use_charge=true,explosion_template='trauma'},0)
assert(paid==1 and #explosions==5);for _,v in ipairs(explosions)do assert(v[8]==.7)end
-- Real native flame stack ceiling and single timer advancement survive repetition.
local target={};local stacks,adds,refreshes=0,0,0
target.buff={current_stacks=function()return stacks end,add_internally_controlled_buff_with_stacks=function(_,name,n)stacks=stacks+n;adds=adds+1 end,
 refresh_duration_of_stacking_buff=function()refreshes=refreshes+1 end};ALIVE[target]=true
local f=action(ActionFlamerGas);f._burn_time=.1;f._dot_targets={[target]=true};f._dot_max_stacks=3;f._flamer_gas_template={dot_buff_name='burn'};f._dot_stack_application_rate=.5
local targets=f._dot_targets;f:_burn_targets(.1,1,false)
assert(stacks==3 and adds==3 and refreshes==2 and f._burn_time==.5 and f._dot_targets==targets and next(targets)==nil)
f._dot_targets[target]=true;f:_burn_targets(.1,1.1,false);assert(f._burn_time==.4 and adds==3 and f._dot_targets[target])
-- Hit-scan/projectile/lightning wrappers keep nil returns, hit flags and guard errors.
for _,pair in ipairs({{'action_shoot_hit_scan','_shoot'},{'action_shoot_projectile','_shoot'},{'action_chain_lightning','_deal_damage'}, {'action_flamer_gas_burst','_damage_target'}})do
 local calls=0;local class={_burn_target=function()end};class[pair[2]]=function(self)calls=calls+1;self._shot_result.hit_minion=calls==1;return 'first',nil,9 end
 attach(pair[1],class);callbacks['scripts/extension_systems/weapon/actions/'..pair[1]](class)
 local o=action(class);local one,two,three=o[pair[2]](o);assert(calls==5 and one=='first' and two==nil and three==9 and o._shot_result.hit_minion)
 for _,kind in ipairs({'client','primary','ability','disabled','no_effect'})do
  calls=0;o._is_server=kind~='client';o._inventory_component.wielded_slot=kind=='primary' and 'slot_primary' or kind=='ability' and 'slot_combat_ability' or 'slot_secondary'
  enabled=kind~='disabled';copies=kind=='no_effect' and 1 or 5;o[pair[2]](o);assert(calls==1,kind)
 end;enabled=true;copies=5
end
local count=0;local bad={_shoot=function()count=count+1;if count==2 then error('boom')end;return 5 end};attach('action_shoot_hit_scan',bad)
local b=action(bad);assert(not pcall(b._shoot,b));count=10;b:_shoot();assert(count==15,'Reentrancy guard released on failure')
-- Shotgun primitives are repeated only inside their original hit pass.
local attacks,blast,status=0,0,0
local ranged={execute_attack=function(...)attacks=attacks+1;local proc=select(19,...);assert(not proc.seen);proc.seen=true;return 2,attacks==2 and 'died' or 'hit','good',attacks==3 end}
local explosion={create_explosion=function(...)blast=blast+1 end}
callbacks['scripts/utilities/action/ranged_action'](ranged);callbacks['scripts/utilities/attack/explosion'](explosion)
local pellets={_add_shotshell_buff=function()status=status+1 end,_process_hits=function(self)
 local args={1,self._player_unit};for i=3,18 do args[i]=0 end;args[19]={};args[20]=1
 local damage,result,eff,weak=ranged.execute_attack(unpack(args));assert(damage==10 and result=='died' and weak)
 explosion.create_explosion(nil,nil,nil,nil,self._player_unit);self:_add_shotshell_buff();return nil,4
end}
attach('action_shoot_pellets',pellets);local s=action(pellets);local n,v=s:_process_hits();assert(attacks==5 and blast==5 and status==5 and n==nil and v==4)
ranged.execute_attack(1,s._player_unit,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,{});assert(attacks==6,'Scope ends after native hit processing')
''')
source=native('action_shoot_pellets')
assert 'local NUM_PELLETS = 32' in source
print('Salvo: native staff start/spawn/payment/update/finish = 5 or Surge 10 with one cost, delayed charge and interruption; native explosion and flame caps; client/slot/disable guards, return/error restoration and scoped shotgun primitives PASS (engine boundaries simulated)')

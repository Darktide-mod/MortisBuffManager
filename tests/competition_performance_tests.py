"""Actual mod updates/kill adapter; native managers are controlled fixtures.
Counts measure redundant mod work, not live frame rate or native Buff effects.
"""
from harness import *
import runtime_tests
import json
L.execute('''
perf_report={}
local native_context=M.session_context
local contexts=setmetatable({},{__mode="k"});local context_count=0
M.session_context=function(...)
 local c=native_context(...)
 if not contexts[c]then contexts[c]=true;context_count=context_count+1 end
 return c
end
local notify=M.mortis_host_policy.notify;local notify_calls,notify_ids=0,0
M.mortis_host_policy.notify=function(kind,ids,...)
 if kind=="native" then notify_calls=notify_calls+1;notify_ids=notify_ids+#ids end
 return notify(kind,ids,...)
end
local raw_extensions=ScriptUnit.has_extension;local bosses=0
ScriptUnit.has_extension=function(u,name,...)
 if name=="boss_system"then bosses=bosses+1 end
 return raw_extensions(u,name,...)
end
local raw_type=TestBreed.enemy_type;local types=0
TestBreed.enemy_type=function(...)types=types+1;return raw_type(...)end
local raw_breed=TestBreed.unit_breed_or_nil;local breeds=0
TestBreed.unit_breed_or_nil=function(...)breeds=breeds+1;return raw_breed(...)end
local attack=hook(AttackReports,"add_attack_result")
for _,reward_mode in ipairs({"preselect","draft","competition"})do
 M.cleanup_mortis_buffs();mode="hub";host_type="solo";is_host=true
 M._settings.enable_custom_mortis_buffs=true;M._settings.mortis_buff_limit=64
 M._settings.mortis_mode=reward_mode;M._settings.mortis_kill_horde=.01
 M.mortis_buffs_on_setting_changed("mortis_mode")
 mode="coop_complete_objective";M.update_mortis_buffs(.5)
 if reward_mode~="preselect"then assert(M.choose_mortis_draft(1))end
 local c,n,ids=context_count,notify_calls,notify_ids
 local start=os.clock()
 for i=1,3600 do M.update_mortis_buffs(1/60);M.mortis_draft_snapshot() end
 local elapsed=os.clock()-start
 perf_report[reward_mode]={frames=3600,context_objects=context_count-c,native_notice_calls=notify_calls-n,native_notice_ids=notify_ids-ids,fixture_cpu_ms=elapsed*1000}
 if reward_mode=="competition"then
  local before=M.mortis_draft_snapshot();local b,t,x=breeds,types,bosses
  local breed={breed_type="minion",kind="horde"};local player_unit=P.player_unit
  local owner=Managers.state.player_unit_spawn.owner
  Managers.state.player_unit_spawn.owner=function(_,u)if u==player_unit then return P end end
  for i=1,1000 do local victim={breed=breed}
   attack({_is_server=true},nil,victim,player_unit,nil,nil,nil,1,"died")
   attack({_is_server=true},nil,victim,player_unit,nil,nil,nil,1,"died")
  end
  local after=M.mortis_draft_snapshot()
  assert(math.abs(after.progress-before.progress-10)<.00001,"Duplicate native reports must not grant duplicate progress")
  perf_report.kills={unique_deaths=1000,reports=2000,breed_reads=breeds-b,breed_classifications=types-t,boss_extension_reads=bosses-x}
  M._settings.mortis_kill_horde=0
  attack({_is_server=true},nil,{breed=breed},player_unit,nil,nil,nil,1,"died")
  perf_report.zero_weight_changed_snapshot=M.mortis_draft_snapshot()~=after
  Managers.state.player_unit_spawn.owner=owner
 end
end
-- Cached native context must still react to all role/mode changes immediately.
local stable=M.session_context();assert(stable.is_solo_play and stable.is_server)
host_type="realms";is_host=false;local client=M.session_context()
assert(client.is_realms_client and not client.is_server and client~=stable)
is_host=true;local host=M.session_context();assert(host.is_realms_host and host.is_server and host~=client)
mode="hub";assert(M.session_context().is_hub)
''')
def convert(v):
    if hasattr(v,'items'):return {k:convert(x) for k,x in v.items()}
    return v
result=convert(L.globals().perf_report)
if '--report-only' not in sys.argv:
    for mode in ['preselect','draft','competition']:
        assert result[mode]['context_objects']<=1,(mode,result)
        assert result[mode]['native_notice_calls']==0,(mode,result)
    assert result['kills']['breed_reads']==1000,result
    assert result['kills']['breed_classifications']==1,result
    assert result['kills']['boss_extension_reads']==0,result
    assert not result['zero_weight_changed_snapshot'],result
if '--output' in sys.argv:
    Path(sys.argv[sys.argv.index('--output')+1]).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
print('All three modes and 2,000 native attack reports: counts measured; manager fixtures do not establish live FPS.')

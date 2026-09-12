from runtime_tests import *
L.globals().Policy=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_host_policy')
L.globals().Manifest=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_diy_manifest')
L.execute(r'''
local values,notices={},{};local client,active=false,false;local token,conn={},{};local remote;local revision,writes=1,0;local missing={}
local m={get=function(_,k)return values[k]end,set=function(_,k,v)values[k]=table.clone_instance(v);writes=writes+1 end,is_enabled=function()return true end,
 localize=function(_,key,arg)return key..':'..tostring(arg)end,notify=function(_,message)notices[#notices+1]=message end}
local api={client=function()return client end,remote=function()return remote end,mission=function()return active,token end,
 identity=function()return conn,'character'end,revision=function()return revision end,known=function(k,id)return k=='diy' and type(id)=='string' and id:match('^library/')end,
 changed=function()revision=revision+1 end,missing=function(id)return missing[id] or {}end,availability=function()return {library='library'}end}
local p=Policy.new(m,api)
assert(not p.set('native','anything',false) and p.allowed('native','anything'),'Native pool has no individual bans')
assert(not Policy.valid({native={buff=true},diy={}}))
assert(p.set('diy','library/salvo',false));assert(not p.allowed('diy','different_library/salvo'),'Host canonical ID applies across library names')
assert(#p.filter('diy',{'salvo','okay'},'library/')==1)
local name=function(id)return id end
p.notify('diy',{'okay'},'library/',name);assert(#notices==0)
p.notify('diy',{'salvo'},'library/',name);p.notify('diy',{'salvo'},'library/',name);assert(#notices==1)
active=true;local frozen=p.current();assert(not p.set('diy','library/salvo',true) and p.current()==frozen)
values.mortis_host_bans_v1.diy['library/salvo']=nil;assert(not p.allowed('diy','library/salvo'))
active=false;missing.lost={{name='Guest',reason='missing'}}
local before=writes;local changed,skipped=p.set_many({'library/a','library/b','invalid'},false)
assert(changed==2 and skipped==1 and writes==before+1,'Batch commits once')
assert(p.set('diy','library/lost',false));changed,skipped=p.set_many({'library/a','library/lost'},true)
assert(changed==1 and skipped==1 and not p.allowed('diy','library/lost'))
for _,bad in ipairs({1,'text',true,{[2]='library/a'},{no='library/a'}})do assert(p.set_many(bad,false)==0)end
client=true;assert(not p.current() and not p.set('diy','library/a',false))
remote={revision=99,bans={native={},diy={['library/a']=true}}};assert(p.revision()==99 and not p.allowed('diy','library/a'))
remote={revision=100,bans={native={bad=true},diy={}}};assert(not p.current(),'Reject forged individual native ban')
local hash='0123456789abcdef:42';local manifest={enabled=true,entries={a=hash,b=hash}}
assert(Manifest.valid(manifest) and not Manifest.valid({enabled=true,entries={a='bad'}}))
local availability=Manifest.build('library',manifest,{
 {name='Complete',manifest={enabled=true,entries={a=hash,b=hash,extra=hash}}},
 {name='Subset',manifest={enabled=true,entries={a=hash}}},
 {name='Changed weight',manifest={enabled=true,entries={a='fedcba9876543210:42',b=hash}}}})
assert(Manifest.valid_availability(availability));assert(#Manifest.missing(availability,'a')==1 and Manifest.missing(availability,'a')[1].name=='Changed weight')
assert(#Manifest.missing(availability,'b')==1 and Manifest.missing(availability,'b')[1].name=='Subset')
assert(not Manifest.valid_limits({max_total=2,tier_limits={1,2,3,2}}))
for reason=1,6 do local a=Manifest.build('library',manifest,{{name='Guest',reason=reason}});assert(Manifest.missing(a,'a')[1].reason==Manifest.reasons[reason])end
mode='hub';host_type='solo';is_host=true;M.cleanup_mortis_buffs();M._settings.mortis_mode='preselect'
assert(not M.mortis_host_policy.set('native','common_1',false))
M.diy_mortis={enabled=function()return diy_enabled end,manifest=function()return {enabled=true,entries={}},'library'end}
for _,native in ipairs({false,true})do for _,diy in ipairs({false,true})do
 M._settings.enable_custom_mortis_buffs=native;diy_enabled=diy
 local rules=M.mortis_rules();assert(rules.native_enabled==native and rules.diy_enabled==diy and rules.enabled==(native or diy))
end end
''')
print('Host policy: whole native pool only, four source combinations, atomic DIY batches, missing definitions, canonical IDs, mission freeze, targeted notices, forged packets and compressed named-peer manifests PASS')
for name in ('diy_library','diy_schema','diy_codec','diy_catalog'):
 L.globals()[name]=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/diy/'+name)
L.execute(r'''
mode='hub';is_host=true;host_type='realms';local connection={};Managers.connection._connection_host=connection
local realms=new_test_mod('Realms');realms._session={is_active_host=function()return is_host end,is_active_client=function()return not is_host end}
M.diy_library=diy_library.new(M,'mortis',diy_catalog,diy_schema,diy_codec,{}, {busy=function()return mode~='hub'end,changed=M.mortis_diy_configuration_changed})
M.diy_mortis.enabled=function()return M.diy_library.options.enabled end
M._settings.mortis_mode='draft';M._settings.mortis_buff_limit=26;M._settings.enable_custom_mortis_buffs=false
assert(M.set_mortis_diy_rules(99,true,connection));local rules=M.mortis_global_rules_snapshot()
assert(rules.diy_limits.max_total==99 and rules.diy_enabled and not rules.native_enabled and rules.limit==10 and M._settings.mortis_buff_limit==26)
assert(Manifest.valid_limits(rules.diy_limits) and rules.diy_limits.tier_limits==nil)
assert(not M.set_mortis_diy_rules(100,true,connection) and not M.set_mortis_diy_rules(1.5,true,connection) and not M.set_mortis_diy_rules(8,true,{}))
assert(M.diy_library.options.max_total==99)
is_host=false;assert(not M.set_mortis_diy_rules(8,true,connection));is_host=true
mode='coop_complete_objective';assert(not M.set_mortis_diy_rules(8,true,connection));mode='hub'
assert(M.set_mortis_diy_rules(0,false,connection));assert(M.diy_library.options.max_total==0 and not M.diy_library.options.enabled)
host_type='solo';assert(not M.set_mortis_diy_rules(8,true,connection));assert(M.mortis_workspace_set_diy_rules(8,true))
''')
print('Production DIY settings API: actual validated library, host/connection checks, independent source/point changes, 0–99 range, fixed-progress independence, room synchronization, mission lock and SoloPlay fallback PASS')

"""Exercise real queue and transport modules, including loss/reordering and kill credits."""
from harness import *
L.globals().Draft=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_draft')
L.globals().Coordinator=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_coordinator')
L.execute('''
local pool=route_test_pool(); local first=function() return 1 end
assert(Draft.limit("preselect",32)==32 and Draft.limit("preselect",100)==99)
assert(Draft.limit("draft",0)==10 and Draft.buff_limit("draft",0)==19)
assert(Draft.limit("competition",0)==0 and Draft.buff_limit("competition",64)==127)
local run=Draft.new("mission1");local p=Draft.player(run,"p")
Draft.tick(run,p,0,pool,0,first);local first_id=p.active.id
assert(p.active.kind=="family" and #p.active.choices==3 and p.active.deadline==60)
Draft.progress(run,.8);Draft.progress(run,.1);assert(run.earned==10)
for i=1,20 do Draft.event(run,"objective:"..i) end;assert(run.earned==10)
assert(Draft.snapshot(run,p,64,1).limit==19 and Draft.snapshot(run,p,64,1).queued==9)
Draft.tick(run,p,64,pool,160,first)
assert(p.family=="fire" and #p.selected==2 and p.selected[1]=="family_fire_1")
assert(p.active.kind=="legendary" and math.abs(p.active.deadline-224.23)<.001)
assert(not Draft.choose(run,p,first_id,2,10,pool,161,first))
local id=p.active.id
assert(not Draft.choose(run,p,id,4,10,pool,161,first))
assert(not Draft.choose(run,p,id,0/0,10,pool,161,first))
assert(Draft.choose(run,p,id,2,10,pool,162,first))
assert(#p.selected==4 and math.abs(p.active.deadline-228.46)<.001)
local seen={};for _,name in ipairs(p.selected) do assert(not seen[name]);seen[name]=true end
for _,name in ipairs(p.active.choices) do assert(not seen[name]) end
Draft.tick(run,p,0,pool,163,first);assert(math.abs(p.active.deadline-228.46)<.001,"Progress quota ignores the stored slider value")
Draft.tick(run,p,10,pool,1000,first);assert(#p.selected==6 and math.abs(p.active.deadline-1064.23)<.001)
while p.active do assert(Draft.choose(run,p,p.active.id,1,10,pool,1001,first)) end
assert(#p.selected==19 and p.completed==10 and Draft.snapshot(run,p,10,1001).queued==0)
local race=Draft.new("race","competition");local a,b=Draft.player(race,"a"),Draft.player(race,"b")
Draft.tick(race,b,0,pool,0,first);assert(not b.active)
for i=1,399 do Draft.kill(a,.25) end
assert(a.earned==1 and a.progress==99.75 and b.earned==1)
Draft.kill(a,2.5);assert(a.earned==2 and a.progress==2.25)
Draft.tick(race,a,64,pool,0,first);assert(a.active.kind=="family")
assert(Draft.choose(race,a,a.active.id,1,64,pool,1,first))
assert(#a.selected==2 and a.active.kind=="legendary" and a.selected[1]=="family_fire_1")
for i=1,40 do Draft.kill(a,100) end
Draft.tick(race,a,64,pool,2,first)
assert(#a.selected==2,"Waiting for the current choice must not grant queued route rewards")
local first_legendary=a.active.id
Draft.tick(race,a,64,pool,1000,first)
assert(#a.selected==4 and math.abs(a.active.deadline-1064.23)<.001,"Only one queued timeout per tick")
assert(not Draft.choose(race,a,first_legendary,1,64,pool,1001,first))
Draft.tick(race,a,1,pool,1001,first);assert(not a.active and #a.selected==4)
assert(Draft.snapshot(race,a,1,1001).spent==1)
Draft.tick(race,a,64,pool,1002,first);assert(math.abs(a.active.deadline-1064.23)<.001 and #a.selected==4,"Reopening a round must not duplicate its automatic grant")
while a.active do
    for _,name in ipairs(a.active.choices) do assert(name:match("^buff_"),"Choices never contain route Buffs") end
    assert(Draft.choose(race,a,a.active.id,1,64,pool,1003,first))
end
assert(#a.selected==42 and a.exhausted)
-- Lower quotas restrict rewards by their original round, even after route exhaustion.
assert(Draft.snapshot(race,a,12,1004).spent==21)
local seen={};for _,name in ipairs(a.selected) do assert(not seen[name]);seen[name]=true end
Draft.kill(a,100);Draft.tick(race,a,64,pool,1004,first);assert(a.exhausted and #a.selected==42)
assert(#b.selected==0 and b.earned==1)
local cap=Draft.new("cap","competition");local c=Draft.player(cap,"c");c.earned=99
Draft.tick(cap,c,3,pool,0,first)
while c.active do assert(Draft.choose(cap,c,c.active.id,1,3,pool,1,first)) end
assert(c.completed==3 and #c.selected==5,"Three reward rounds include the opening, not three total Buffs")
local small=route_test_pool();small.legendary.regular={"buff_1","buff_2"}
small.routes.fire.buffs={"family_fire_2"}
local last=Draft.new("last","competition");local d=Draft.player(last,"d")
Draft.tick(last,d,64,small,0,first);assert(Draft.choose(last,d,d.active.id,1,64,small,1,first))
Draft.kill(d,100);Draft.tick(last,d,64,small,2,first)
assert(d.active and #d.active.choices==2,"Two remaining Buffs produce exactly two choices")
assert(Draft.choose(last,d,d.active.id,1,64,small,3,first));assert(#d.selected==3 and not d.active)
Draft.kill(d,100);Draft.tick(last,d,64,small,4,first)
assert(#d.selected==4 and d.completed==3 and not d.active,"The sole remaining Buff is granted without input or a timer")
Draft.kill(d,100);Draft.tick(last,d,64,small,5,first)
assert(d.exhausted and not d.active and #d.selected==4)
local single=route_test_pool();single.legendary.regular={"buff_1"}
local quota=Draft.new("quota","competition");local e=Draft.player(quota,"e");e.earned=64
Draft.tick(quota,e,1,single,0,first);assert(Draft.choose(quota,e,e.active.id,1,1,single,1,first))
assert(#e.selected==1 and not e.active,"No automatic final Buff may bypass an exhausted round quota")
local boundary=Draft.new("boundaries")
Draft.progress(boundary,.079);assert(boundary.earned==1)
Draft.progress(boundary,.08);assert(boundary.earned==2)
Draft.progress(boundary,.799);assert(boundary.earned==9)
Draft.progress(boundary,.8);assert(boundary.earned==10)
''')
print('Actual draft core: fresh 60s per choice, long-frame timeout, queue, invalid/duplicate replies, cap changes, unique/exhausted pools and fractional personal kill progress: PASS')
L.execute('''
function player(peer,character)
 return {peer_id=function() return peer end,character_id=function() return character end,
  local_player_id=function() return 1 end,archetype_name=function() return "ogryn" end}
end
host_player=player("host","h"); guest_player=player("guest","g")
all_players={host_player,guest_player}; mission=nil; connection={}; role="client"
rules={enabled=true,limit=10,mode="draft",revision=1}
host_shared={}; client_shared={}; packets={}; callbacks={}; joins={}; leaves={}
host_mod=new_test_mod("host"); guest_mod=new_test_mod("guest")
input_trace={}
for _,m in ipairs({host_mod,guest_mod}) do
 m.mortis_input_trace=function(event,detail) input_trace[#input_trace+1]=event.." "..detail end
end
local function transport(name)
 return {network_is_available=function() return true end,
  network_register=function(_,_,cb) callbacks[name]=cb; return true end,
  network_on_peer_joined=function(_,cb) joins[name]=cb end,
  network_on_peer_left=function(_,cb) leaves[name]=cb end,
  network_send=function(_,_,recipient,packet)
   packets[#packets+1]={from=name,to=recipient,payload=table.clone_instance(packet)}; return true
  end}
end
local hnet,cnet=transport("host"),transport("guest")
local pool=route_test_pool()
local function api(host)
 return {context=function() return connection,host and "host" or role,host and nil or "host" end,
  realms=function() return host and hnet or cnet end,
  rules=function() return table.clone_instance(host and rules or {enabled=false,limit=1,mode="preselect",revision=0}) end,
  local_player=function() return host and host_player or guest_player end,
  players=function() return all_players end, key=function(p) return p:peer_id()..":"..p:character_id() end,
  mission=function() return host and mission end, ready=function() return true end,
  pool=function() return pool end, known=route_test_known, known_family=route_test_family,
  progress=function() return nil end, assets_ready=function() return true end,
  payload=function() return {character_id=guest_player:character_id(),archetype="ogryn",local_player_id=1,selection={"buff_1"}} end,
  accept=function() return true end}
end
H=Coordinator.new(host_mod,Draft,api(true),host_shared)
C=Coordinator.new(guest_mod,Draft,api(false),client_shared)
function pump()
 local safety=0
 while #packets>0 do
  local packet=table.remove(packets,1); safety=safety+1; assert(safety<100)
  if callbacks[packet.to] then callbacks[packet.to](packet.from,packet.payload) end
 end
end
H:update(0.5); C:update(0.5); pump()
assert(C:rules().mode=="draft" and C:rules().limit==10,"Guest must obey host, not its local settings")
assert(not H.run and not C:snapshot(),"Room with no mission does not deal cards")
mission={}; H:update(0.5); C:update(0.5); pump()
local s=C:snapshot(); assert(s.active and #s.active.choices==3 and s.earned==1)
local id=s.active.id
C:receive("attacker",{protocol=10,kind="state",epoch="fake",sequence=999,rules=rules})
assert(C:snapshot().active.id==id)
for i=1,9 do H:event("obj:"..i) end
H:update(0.5); pump(); assert(C:snapshot().queued==9)
C:choose(guest_player,id,2); packets={} -- lose first choice packet
C:update(0.5); pump(); H:update(0.5); pump()
assert(C:snapshot().spent==2 and C:snapshot().active.id~=id,"Choice retry recovers a dropped packet")
assert(not C.pending_choice,"Guest acknowledgment still resolves a retried choice without diagnostics")
assert(#input_trace==0,"Stable transport must not call old diagnostic callbacks")
H:receive("guest",{protocol=10,kind="choose",epoch=H.epoch,character="g",id=id,index=1}); pump()
assert(C:snapshot().spent==2)
H:receive("guest",{protocol=10,kind="choose",epoch=H.epoch,character="h",id=C:snapshot().active.id,index=1}); pump()
assert(C:snapshot().spent==2,"Cannot choose for another character")
local before=C:snapshot(); local nextid=before.active.id
local timing=H:host_snapshot(guest_player).active
local seconds=timing.remaining+(timing.delay or 0)
for i=1,math.ceil(seconds*2) do H:update(0.5);C:update(0.5);pump() end
local after=C:snapshot()
assert(after.spent==4 and after.active.remaining>59,"Next queued choice gets a new full minute")
leaves.host("guest"); leaves.guest("host"); all_players={host_player}; H:update(0.5); pump()
all_players={host_player,guest_player}; joins.host("guest"); C:update(2); pump()
assert(C:snapshot().spent==4,"Reconnect retains this character's mission draft")
rules.enabled=false; rules.revision=2; H:changed(); H:update(0.5); pump()
assert(not C:rules().enabled and not C:snapshot())
rules.enabled=true
rules.mode="competition";rules.limit=8;rules.revision=3;H:changed();H:update(0.5);pump()
local unit={};H:kill(guest_player,unit,50);H:kill(guest_player,unit,50)
assert(H:host_snapshot(guest_player).progress==50,"Duplicate death notification counted once")
H:kill(guest_player,{},50); H:update(0.5);pump()
assert(C:snapshot().earned==2 and H:host_snapshot(host_player).earned==1)
rules.limit=99;rules.revision=4;H:changed();pump()
for i=1,20 do H:kill(guest_player,{},100) end
C:choose(guest_player,C:snapshot().active.id,1);pump();H:update(.5);pump()
local legendary=C:snapshot()
assert(legendary.spent==2 and legendary.active.kind=="legendary" and legendary.queued>0)
C:choose(guest_player,legendary.active.id,2);pump();H:update(.5);pump()
assert(C:snapshot().spent==4 and C:snapshot().active.remaining>59,"Guest must receive both rewards for every round")
local old_packet={protocol=10,kind="state",epoch=H.epoch,sequence=1,character="g",rules=rules,draft=before}
C:receive("host",old_packet); assert(C:snapshot().mode=="competition","Out-of-order state cannot rewind")
-- Large compatible pools exercise the full wire/application capacity separately from draw counts.
for _,family in ipairs(pool.families) do
 for i=11,99 do pool.routes[family].buffs[#pool.routes[family].buffs+1]="family_"..family.."_"..i end
end
for i=33,110 do pool.legendary.regular[i]="buff_"..i end
mission={};H:update(.5);C:update(2);pump()
for i=1,98 do H:kill(guest_player,{},100) end
H:update(.5);pump()
local picks=0
while C:snapshot().active do
 picks=picks+1;assert(picks<=99)
 assert(C:choose(guest_player,C:snapshot().active.id,1));pump();H:update(.5);C:update(.5);pump()
end
assert(picks==99 and C:snapshot().spent==197 and #C:snapshot().selected==197)
assert(C:rules().limit==99 and C:snapshot().limit==197 and C:snapshot().queued==0)
rules.limit=2;rules.revision=5;H:changed();H:update(.5);pump()
assert(C:snapshot().spent==3 and #C:snapshot().selected==3)
rules.limit=99;rules.revision=6;H:changed();H:update(.5);pump()
assert(C:snapshot().spent==197 and not C:snapshot().active,"Raising the quota restores history without duplicate choices")
host_mod._enabled=false;H:cleanup();pump();assert(not C:rules().enabled and not C:snapshot())
host_mod._enabled=true;mission=nil;connection={};H:update(0.5);C:update(0.5);pump()
assert(not C:snapshot(),"Second room cannot keep the previous run")
mission={};H:update(0.5);C:update(2);pump();assert(C:snapshot().earned==1)
guest_player=player("guest","newchar");all_players={host_player,guest_player};C:update(0.5);H:update(0.5);pump()
assert(C:snapshot().spent==0,"Changing character never inherits previous character rewards")
''')
print('Actual coordinator: empty room, authoritative rules, host authentication, join/leave/rejoin, choice retries, duplicate/stale packets, character isolation, timeout, shared caps, kill ownership, disable and second-room reset: PASS')

L.execute('''
-- Quota closure is independent from completion of already earned choices.
local pool=route_test_pool();local first=function() return 1 end
local run=Draft.new("notice","competition");local p=Draft.player(run,"p")
Draft.tick(run,p,3,pool,0,first)
Draft.kill(p,100,3);Draft.kill(p,100,3)
assert(p.earned==3 and not Draft.counting(p,3) and p.progress==0)
local version=p.version
for i=1,1000 do assert(Draft.kill(p,.25,3)==false) end
assert(p.version==version and p.earned==3)
assert(Draft.choose(run,p,p.active.id,1,3,pool,1,first))
local s=Draft.snapshot(run,p,3,1)
assert(not s.counting and s.active and #s.rewards==1 and s.rewards[1].name==p.selected[1])
assert(Draft.choose(run,p,p.active.id,1,3,pool,2,first))
s=Draft.snapshot(run,p,3,2);assert(#s.rewards==2 and s.rewards[2].round==2)
assert(Draft.counting(p,4));assert(Draft.kill(p,5,4));assert(p.progress==5)
-- Sole remaining non-route candidate still produces an acquisition notice.
pool.legendary.regular={"buff_1"};run=Draft.new("single","competition");p=Draft.player(run,"p")
Draft.tick(run,p,3,pool,0,first);Draft.choose(run,p,p.active.id,1,3,pool,1,first)
Draft.kill(p,100,3);Draft.tick(run,p,3,pool,2,first)
s=Draft.snapshot(run,p,3,2)
assert(not s.active and #s.rewards==3 and s.rewards[3].name=="buff_1")
-- Idle clients receive no unsolicited 2 Hz full snapshot stream.
H:update(.5);pump();packets={}
for i=1,3 do H:update(.5) end
assert(#packets==0)
local local_a,lag_a=H:snapshot();H:update(.1);local local_b,lag_b=H:snapshot()
assert(local_a==local_b and lag_b>lag_a,"Same-version host HUD reads reuse their arrays while countdown advances")
C:update(2);pump();assert(C:rules(),"Heartbeat still refreshes client authority")
''')
print('Terminal quota: frozen counters with pending rewards, quota increase, ordered automatic/sole-candidate notices, unchanged-state network suppression and cached countdown snapshots: PASS')

L.execute('''
local pool=route_test_pool();local first=function() return 1 end
local run=Draft.new("presentation","competition");local p=Draft.player(run,"p");p.earned=3
Draft.tick(run,p,3,pool,0,first);assert(Draft.choose(run,p,p.active.id,1,3,pool,1,first))
assert(Draft.award_hold_time==3 and math.abs(Draft.reveal_time-3.43)<.0001)
assert(math.abs(p.active.ready_at-5.23)<.0001 and math.abs(p.active.deadline-65.23)<.0001)
local s=Draft.snapshot(run,p,3,2)
assert(s.active.remaining==60 and math.abs(s.active.delay-3.23)<.0001)
Draft.tick(run,p,3,pool,65.22,first);assert(p.completed==1)
Draft.tick(run,p,3,pool,65.23,first);assert(p.completed==2)
assert(math.abs(p.active.deadline-p.active.ready_at-60)<.0001)
''')
print('Award pacing: selection, fade-in, three-second hold and fade-out precede a fresh sixty-second next choice: PASS')

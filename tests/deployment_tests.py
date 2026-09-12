"""Unready/missing clients cannot stall or consume another player's rewards."""
from harness import *
L.globals().Draft=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_draft')
L.globals().Coordinator=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_coordinator')
L.execute('''
function player(peer) return {peer_id=function() return peer end,local_player_id=function() return 1 end,
 character_id=function() return peer.."-character" end} end
P=player("host");A=player("healthy");B=player("loading");D=player("missing")
players={P,A,B,D};room={};mission={};warnings={};packets={};left=nil;joined=nil
rules={enabled=true,mode="draft",limit=10,revision=1}
local net={network_is_available=function() return true end,
 network_register=function() return true end,network_on_peer_left=function(_,f) left=f end,
 network_on_peer_joined=function(_,f) joined=f end,
 network_send=function(_,_,peer,packet)
  if peer=="missing" then return false,"target_rpc_unsupported" end
  packets[#packets+1]=packet;return true
 end}
local pool=route_test_pool()
local m=new_test_mod("test");local shared={}
H=Coordinator.new(m,Draft,{
 context=function() return room,"host" end,realms=function() return net end,rules=function() return table.clone(rules) end,
 key=function(p) return p:peer_id() end,local_player=function() return P end,players=function() return players end,
 mission=function() return mission end,ready=function() return true end,assets_ready=function() return true end,
 version="3.0.0",pool=function() return pool end,progress=function() return .8 end,known=route_test_known,known_family=route_test_family,
 warn_peer=function(p,status) warnings[#warnings+1]=p:peer_id()..":"..status end},shared)
function hello(peer,session,ready) H:receive(peer,{protocol=10,kind="request",request=session,assets_ready=ready,version="3.0.0"}) end
function choose(peer,session,id)
 H:receive(peer,{protocol=10,kind="choose",epoch=H.epoch,session=session,character=peer.."-character",id=id,index=1})
end
H:update(.5);hello("healthy","a1",true);hello("loading","b1",false);H:update(.5)
assert(H:deployment("healthy").status=="ready" and H:deployment("healthy").version=="3.0.0")
assert(H:deployment("loading").status=="loading_assets" and H:deployment("missing").status=="incompatible")
assert(H:eligible(A) and not H:eligible(B) and not H:eligible(D))
assert(H:host_snapshot(A).active and not H:host_snapshot(B).active and not H:host_snapshot(D).active)
local active=H:host_snapshot(A).active
choose("healthy","a1",active.id);assert(H:host_snapshot(A).spent==2)
H:kill(A,{},100);H:update(.5);assert(H:host_snapshot(A).active)
for i=1,20 do hello("healthy","a1",true);hello("loading","b1",false);H:update(.5) end
assert(#warnings==2,"Only one notice each for missing and still-loading clients")
hello("loading","b1",true);H:update(.5)
assert(H:host_snapshot(B).active.remaining==60,"Readiness starts a full minute")
local bid=H:host_snapshot(B).active.id
H:receive("loading",{protocol=10,kind="leave",epoch=H.epoch,session="b1"});H:update(.5)
assert(not H:eligible(B) and H:deployment("loading").status=="disabled")
hello("loading","b1",true);assert(not H:eligible(B),"Delayed heartbeat cannot re-enable a disabled mod")
hello("loading","b2",true);H:update(.5);assert(H:eligible(B))
choose("loading","b1",bid);assert(H:host_snapshot(B).spent==0,"Old session choice rejected")
choose("loading","b2",bid);assert(H:host_snapshot(B).spent==2)
H:kill(B,{},100);H:update(.5)
left("loading");players={P,A,D};H:update(.5)
local remaining=H:host_snapshot(B).active.remaining
for i=1,140 do hello("healthy","a1",true);H:update(.5) end
assert(H:host_snapshot(A).spent==4,"Healthy client timeout still advances while another is away")
assert(H:host_snapshot(B).spent==2 and H:host_snapshot(B).active.remaining==remaining,"Absent client's active choice is suspended")
hello("loading","b3",true);assert(not H:eligible(B),"Packets cannot create membership")
players={P,A,B,D};joined("loading");hello("loading","b2",true);assert(not H:eligible(B))
hello("loading","b3",true);H:update(.5)
assert(H:host_snapshot(B).spent==2 and H:host_snapshot(B).active.remaining==remaining)
-- Lost heartbeat has a bounded lease and a visible state; no whole-room wait.
for i=1,20 do hello("healthy","a1",true);H:update(.5) end
assert(not H:eligible(B) and H:deployment("loading").status=="disconnected")
assert(H:eligible(A))
H:receive("missing",{protocol=10,kind="leave",epoch=H.epoch}) -- no handshake/session is harmless
''')
print('Four-player deployment: ready/loading/missing versions, one-off notices, disabled/stale packets, membership, reconnect state/timer, expired lease and healthy-player isolation PASS')
L.globals().Manifest=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_diy_manifest')
L.execute(r'''
local hash='0123456789abcdef:42';local host_manifest={enabled=true,entries={a=hash,b=hash}}
local native_pool=route_test_pool();local roster={P,A,B,D};local left,joined
for _,p in ipairs(roster)do p.profile=function(self)return {name=string.rep('中',50)..self:peer_id()}end end
local same=function(a,b)
 if a.library~=b.library or #a.players~=#b.players then return false end
 for k,v in pairs(a.players)do if b.players[k]~=v then return false end end
 for k,v in pairs(a.blocked)do if b.blocked[k]~=v then return false end end
 for k,v in pairs(b.blocked)do if a.blocked[k]~=v then return false end end
 return true
end
local net={network_is_available=function()return true end,network_register=function()return true end,network_send=function()return true end,
 network_on_peer_left=function(_,fn)left=fn end,network_on_peer_joined=function(_,fn)joined=fn end}
local h=Coordinator.new(new_test_mod('manifests'),Draft,{context=function()return room,'host'end,realms=function()return net end,
 rules=function()return {enabled=false,mode='preselect',limit=6,revision=1}end,mission=function()end,key=function(p)return p:peer_id()end,
 local_player=function()return P end,players=function()return roster end,ready=function()return true end,assets_ready=function()return true end,
 pool=function()return native_pool end,known=route_test_known,known_family=route_test_family,
 diy_manifest=function()return host_manifest,'library'end,valid_manifest=Manifest.valid,diy_availability=Manifest.build,same_availability=same}, {})
h:update(.5);local pending=h:compatibility();assert(#Manifest.missing(pending,'a')==3)
for _,name in ipairs(pending.players)do assert(#name==126 and name:sub(-3)=='中','Names truncate at a UTF-8 character boundary')end
local function hello(p,manifest,nonce,protocol)
 h:receive(p:peer_id(),{protocol=protocol or 10,kind='request',request=nonce or 'one',character=p:character_id(),assets_ready=true,diy_manifest=manifest})
end
hello(A,host_manifest,'obsolete',8);assert(not h.peer_state[A:peer_id()].last_seen,'Old protocol cannot confirm definitions')
hello(A,host_manifest);hello(B,{enabled=true,entries={a=hash}});hello(D,{enabled=true,entries={a=hash,b='fedcba9876543210:42'}})
local availability=h:compatibility();assert(#Manifest.missing(availability,'a')==0 and #Manifest.missing(availability,'b')==2)
assert(h:compatibility()==availability,'Unchanged room keeps the cached availability object')
h:receive(B:peer_id(),{protocol=10,kind='leave',session='one',epoch=h.epoch})
assert(Manifest.missing(h:compatibility(),'a')[1].reason=='disabled')
roster={P,A,D};left(B:peer_id());assert(#Manifest.missing(h:compatibility(),'a')==0)
roster={P,A};left(D:peer_id());assert(#Manifest.missing(h:compatibility(),'b')==0,'Leaving restores entries available to every remaining player')
for i=1,18 do h:update(.5)end
assert(Manifest.missing(h:compatibility(),'a')[1].reason=='disconnected')
hello(A,host_manifest,'two');assert(#Manifest.missing(h:compatibility(),'a')==0)
''')
print('Actual coordinator manifests: protocol-eight rejection, three guests, matching/subset/different definitions, UTF-8 names, cached state, disable, leave, lease expiry and reconnect PASS')

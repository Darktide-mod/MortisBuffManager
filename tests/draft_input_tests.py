"""Exercise early capture against native input mappings and InputService methods."""
from ui_native_env import *
L.execute('function class(name) local c={}; _G[name]=c; return c end')
for path in ('scripts/managers/input/input_filters', 'scripts/managers/input/null_input_service',
             'scripts/settings/input/default_ingame_input_filters'):
    cache[path]=tbl({})
service=L.execute(native('scripts/managers/input/input_service.lua'))
cache['scripts/managers/input/input_service']=service
L.globals().Defaults=L.execute(native('scripts/settings/input/default_ingame_input_settings.lua'))
L.globals().Utils=cache['scripts/managers/input/input_utils']
L.globals().M=mod
L.globals().I=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_draft_input')
L.execute('''
logs={};function M:info(fmt,...) logs[#logs+1]=string.format(fmt,...) end
held={};pressed={};local valid={['left ctrl']=true,['right ctrl']=true}
for i=1,3 do valid[tostring(i)]=true;valid['num '..i]=true end
Keyboard={button_index=function(k) if valid[k] then return k end end,
 button=function(k) return held[k] and 1 or 0 end,pressed=function(k) return pressed[k]==true end}
other_ui=false; Managers.ui={using_input=function() return other_ui end}
snapshot={active={id='one',choices={'a','b','c'}}};awaiting=false
function M.mortis_draft_snapshot() return snapshot,0,awaiting end
visible='one';selectable=true
function context() return visible,selectable end
I.context=context
local capture,filter
for _,h in ipairs(hooks) do
 if h.target==InputManager and h.name=='_update_services' then capture=h.fn end
 if h.target==InputService and h.name=='get_with_filters' then filter=h.fn end
end
assert(capture and filter)
function tick(p,h,dt) pressed=p or {};held=h or {};capture({},dt or .016) end
S=setmetatable({type=Defaults.service_type,_aliases=table.clone_instance(Defaults.aliases),_actions={}}, {__index=InputService})
local function add(action,rule)
 local kind=rule.type
 local callbacks={}
 for _,binding in ipairs(S._aliases[rule.key_alias]) do
  local main=Utils.split_key(binding)
  callbacks[#callbacks+1]=function()
   local key=main:gsub('^keyboard_','')
   if kind=='button' then return held[key] and 1 or 0 end
   return (kind=='held' and held[key] or pressed[key])==true
  end
 end
 S._actions[action]={key_alias=rule.key_alias,type=kind,callbacks=callbacks,default_func=InputService.ACTION_TYPES[kind].default_device_func}
end
for action,rule in pairs(Defaults.settings) do if rule.key_alias then add(action,rule) end end
function read(action,locks) return filter(InputService.get_with_filters,S,action,locks or {}) end
-- Reproduce native leakage, then verify the early hook before gameplay/HUD.
tick({['2']=true},{['2']=true,['left ctrl']=true})
assert(InputService.get_with_filters(S,'wield_2',{})==true,'Vanilla Ctrl+2 still wields')
assert(read('wield_2')==false and read('wield_2')==false)
assert(I.take('one')==2 and not I.take('one'))
assert(#logs==0,'Diagnostics default off')
-- Movement/crouch, attack, wheel and an unrelated number still pass through.
pressed.mouse_left=true;pressed.mouse_wheel_down=true;pressed['4']=true;held.w=true
assert(read('action_one_pressed')==true and read('wield_scroll_down')==true and read('wield_4')==true)
assert(read('crouching')==true)
for action,rule in pairs(S._actions) do
 if rule.key_alias=='keyboard_move_forward' then assert(read(action)==InputService._get(S,action)) end
end
-- Same held chord cannot consume a queued card, even with repeated pressed events.
snapshot.active.id='two';visible='two'
for n=1,20 do tick({['2']=true},{['2']=true,['left ctrl']=true});assert(not I.take('two')) end
tick();tick({['3']=true},{['right ctrl']=true});assert(I.take('two')==3 and not read('wield_3'))
-- Quick Ctrl tap within one frame; keypad names recognized by engine only.
tick();tick({['1']=true,['left ctrl']=true});assert(I.take('two')==1 and not read('wield_1'))
tick();tick({['num 2']=true},{['right ctrl']=true});assert(I.take('two')==2)
-- Normal numbers, no card, and another UI keep their original behavior.
tick();tick({['1']=true});assert(not I.take('two') and read('wield_1'))
tick();visible=nil;snapshot.active=nil
tick({['1']=true},{['left ctrl']=true});assert(read('wield_1') and not I.pending)
tick();visible='two';snapshot.active={id='two',choices={'d','e','f'}};other_ui=true
tick({['2']=true},{['left ctrl']=true});assert(not I.pending and read('wield_2'))
local locks={keyboard_2=true};assert(not read('wield_2',locks) and locks.keyboard_2 and not locks.keyboard_1)
other_ui=false;tick()
-- Outgoing cards consume a chord but cannot choose the next unseen card.
visible='one';selectable=false
tick({['1']=true},{['left ctrl']=true});assert(not I.pending and not read('wield_1'))
visible='two';selectable=true
tick({['1']=true},{['1']=true,['left ctrl']=true});assert(not I.pending)
tick();tick({['1']=true},{['left ctrl']=true});assert(I.take('two')==1)
-- A bound custom action follows the claimed physical key; unrelated keys do not.
S._aliases.custom={'keyboard_left ctrl+keyboard_2'};add('custom',{key_alias='custom',type='pressed'})
tick();tick({['2']=true},{['left ctrl']=true});assert(not read('custom'))
S.type='View';assert(read('wield_2'));S.type='Ingame'
-- Buffer expires or cancels on menu/ID changes; cleanup and DMF disable release input.
tick({}, {}, .4);assert(not I.pending)
tick({['2']=true},{['left ctrl']=true});other_ui=true;tick();assert(not I.pending);other_ui=false
tick({['2']=true},{['left ctrl']=true});snapshot.active.id='three';tick();assert(not I.pending)
I.cleanup();assert(not I.context and next(I.claimed)==nil)
I.context=context;visible='three'
tick({['1']=true},{['left ctrl']=true});M._enabled=false;assert(read('wield_1'))
tick();M._enabled=true;tick({['1']=true},{['left ctrl']=true});assert(I.take('three')==1)
-- Stable builds ignore stale or externally restored diagnostic settings.
M._settings.mortis_debug_input=true;tick()
tick({['2']=true},{['left ctrl']=true,['2']=true});read('wield_2');read('wield_2')
assert(I.take('three')==2 and not read('wield_2'))
for n=1,30 do tick({}, {['left ctrl']=true,['2']=true});read('wield_2') end
tick();tick({['2']=true});read('wield_2')
assert(#logs==0 and not I.trace and not I.observed and not I.traced_actions)
visible=nil;snapshot.active=nil;tick()
tick({['3']=true},{['left ctrl']=true});assert(not I.pending and read('wield_3') and #logs==0)
''')
print('Native input: Ctrl leakage reproduction, early capture, short taps, keypad, one-press/one-card, outgoing cards, typing, custom bindings, disable cleanup and stable diagnostics removal: PASS')

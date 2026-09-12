"""Export the actual Lua picker, HUD and Realms definitions with localized sample data."""
from pathlib import Path
import json,sys
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'tests'))
from ui_native_env import *
L.globals().M=mod
load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_talent_ui')
HUD=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_draft_hud')
Controls=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_realms_controls')
result=json.loads((CHECKS/'ui-layouts.json').read_text(encoding='utf-8'))
def tr(key,*args):return mod.localize(mod,key,*args)
names={
'en':['Extra ability charge','Explosive ranged kills','Damage reflected','Unstoppable momentum','Stagger pulse','Burning melee strikes','Healing on grenade explosion','Improved critical damage','Electric retaliation','Resilient resolve'],
'zh-cn':['额外技能充能','远程击杀爆炸','伤害反弹','势不可挡','踉跄冲击','近战烈焰','手雷爆炸治疗','暴击伤害强化','电流反击','坚韧意志'],
'zh-tw':['額外技能充能','遠程擊殺爆炸','傷害反彈','勢不可擋','踉蹌衝擊','近戰烈焰','手榴彈爆炸治療','暴擊傷害強化','電流反擊','堅韌意志']}
descriptions={
'en':['Gain an additional combat ability charge.','Ranged kills trigger an explosion around the defeated enemy.','Reflect a portion of incoming melee damage back to the attacker.'],
'zh-cn':['获得额外的战斗技能充能。','远程击杀会在被击败的敌人周围引发爆炸。','将受到的部分近战伤害反弹给攻击者。'],
'zh-tw':['獲得額外的戰鬥技能充能。','遠程擊殺會在被擊敗的敵人周圍引發爆炸。','將受到的部分近戰傷害反彈給攻擊者。']}
def bounds(graph,name):
    if name=='screen':return (0,0,1920,1080)
    if name=='info_banner':return (0,900,1920,180)
    g=graph[name]; x,y,pw,ph=bounds(graph,g.parent)
    w,h=g.size[1],g.size[2];pos=g.position
    align=g.horizontal_alignment
    x+=((pw-w)/2 if align=='center' else pw-w if align=='right' else 0)+(pos[1] if pos else 0)
    align=g.vertical_alignment
    y+=((ph-h)/2 if align=='center' else ph-h if align=='bottom' else 0)+(pos[2] if pos else 0)
    return x,y,w,h
for lang in names:
    L.globals().test_language=lang
    mod._mortis_workspace_class=None
    load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_talent_ui')
    # Real picker callbacks populate the native widgets, including filters and capacity text.
    entries=[dict(buff_name='sample_'+str(i),display_name=n,description=descriptions[lang][i%3],source_kind=['class','generic','family'][i%3],source_family='fire',source_requirement='class',valid=True,selected=i<3) for i,n in enumerate(names[lang])]
    L.globals().Sample=tbl(dict(selected_count=3,limit=8,mode='preselect',editable=True,entries=entries,family='fire',archetype='ogryn',abilities_ready=True,apply_to_self=True))
    L.execute('''
    M.mortis_talent_ui_available=function() return true end
    M.mortis_talent_ui_snapshot=function() return table.clone_instance(Sample) end
    Managers.package={load=function(_,_,_,callback) callback();return 1 end,release=function() end}
    P={};Managers.player={local_player_safe=function()return P end}
    view=setmetatable({}, {__index=MBMWorkspaceMortisView})
    view:init({}, {player=P,parent={view_name="workspace"}})
    view:on_enter()
    ''')
    items=[]
    def add(key,box,text='',**kw):
        x,y,w,h=box;items.append(dict(key=key,x=x,y=y,w=w,h=h,text=text,**kw))
    graph=L.globals().view._definitions.scenegraph_definition
    widgets=L.globals().view._widgets_by_name
    for name,w in widgets.items():
        if not name.startswith('tamm_mortis_') or name in ('tamm_mortis_button','tamm_mortis_dimmer') or not w.visible:continue
        box=bounds(graph,w.scenegraph_id)
        if name.endswith('_panel'):add(name,box,fill=True,panel=True)
        elif name.startswith('tamm_mortis_row_'):
            add(name,box,fill=True,selected=bool(w.content.selected),checkbox=True)
            x,y,bw,bh=box
            add(name+'_text',(x+106,y,bw-122,bh),w.content.label,font=20)
        elif name.endswith('_icon'):add(name,box,icon=True)
        elif name.endswith('_scrollbar'):add(name,box,fill=True)
        else:
            text=w.content.original_text or w.content.text or ''
            fs=w.style.text.font_size if w.style.text else 20
            add(name,box,text,font=fs or 20,center=True,fill=bool(w.content.hotspot),selected=bool(w.content.hotspot and w.content.hotspot.is_selected))
    add('workspace_title',(105,55,1200,60),{'en':'CHARACTER','zh-cn':'角色','zh-tw':'角色'}[lang],font=36)
    add('workspace_tabs',(105,144,1690,50),{'en':'Loadouts      Talents      Mortis      DIY talents','zh-cn':'配装      天赋      死灵天赋      DIY 天赋','zh-tw':'配裝      天賦      死靈天賦      DIY 天賦'}[lang],font=24)
    result[lang+'_picker']=items
    L.execute('view:on_exit()')
    # HUD text/icon rectangles come straight from the game's widget pass definitions.
    hud_graph,defs=HUD.definitions()
    for mode in ('draft','competition'):
        items=[]
        add('header',bounds(hud_graph,'panel')[:2]+(HUD.geometry.width,28),tr('mortis_route_header',48,0,0,10) if mode=='draft' else tr('mortis_draft_header',48,2,11,32),font=21,center=True)
        for i in range(1,4):
            name='card_'+str(i);box=bounds(hud_graph,name);add(name,box,fill=True,panel=True,frame=True)
            definition=defs[name]
            for field in ('title','description','key','icon'):
                style=definition.style[field];x,y,w,h=box;off=style.offset
                rect=(x+off[1],y+off[2],style.size[1],style.size[2])
                route=('fire','electric','critical')[i-1]
                opening={'en':['Burning melee hits','Electric ranged hits','Critical strikes'],'zh-cn':['近战命中燃烧','远程命中电击','暴击强化'],'zh-tw':['近戰命中燃燒','遠程命中電擊','暴擊強化']}[lang][i-1]
                text=(tr('mortis_talent_ui_family_'+route) if mode=='draft' else names[lang][i-1]) if field=='title' else (tr('mortis_route_description',opening) if mode=='draft' else descriptions[lang][i-1]) if field=='description' else 'Ctrl + '+str(i) if field=='key' else ''
                add(name+'_'+field,rect,text,font=style.font_size or 20,center=field=='key',icon=field=='icon',top=field=='description',text_padding=0)
            x,y,w,h=box;add(name+'_timer',(x,y+h-3,w*0.8,3),fill=True,timer=True)
        if mode=='competition':
            box=bounds(hud_graph,'competition_status');x,y,w,h=box
            add('competition',box,fill=True,panel=True)
            for field in ('text','track','fill'):
                style=defs.progress.style[field];off=style.offset
                bw=style.size[1] if field!='fill' else (HUD.geometry.progress_width-24)*0.5775
                rect=(x+off[1],y+off[2],bw,style.size[2])
                add('competition_'+field,rect,tr('mortis_competition_percentage',57.75) if field=='text' else '',
                    font=style.font_size or 17,center=True,fill=field!='text',timer=field=='fill',text_padding=0)
        result[lang+'_'+mode]=items
    # Global rule row and per-player deployment rows use the actual grid blueprints.
    L.execute('''
    M.mortis_realms_controls_active=function() return true end
    M.mortis_global_rules_snapshot=function() return {mode="competition",limit=8,enabled=true,revision=1},"room" end
    M.mortis_peer_deployment=function(peer) return {status=peer=="guest" and "loading_assets" or "ready",version="3.1.1"} end
    ''')
    items=[];width=1262;x=(1920-width)/2;y=170
    blueprint=Controls.blueprint(width)
    w=L.globals().UIWidget.init('rules',L.globals().UIWidget.create_definition(blueprint.pass_template,'row'))
    grid=tbl({'_mbm_realms_view':{}});blueprint.init(grid,w,tbl({}))
    add('global_background',(x,y,width,108),fill=True,panel=True)
    for field in ('label','enable','minus','points','plus','status','preselect','draft','competition'):
        id='mbm_'+field;style=w.style[id]
        add(id,(x+style.offset[1],y+style.offset[2],style.size[1],style.size[2]),w.content[id],font=style.font_size,
            fill=field not in ('label','status'),center=field not in ('label','status'),selected=field=='competition')
    layout,blueprints=Controls.wrap_layout(grid,tbl([{'widget_type':'player','peer_id':'host'},{'widget_type':'player','peer_id':'guest'}]),tbl({'player':{'size':[width,80]}}))
    bp=blueprints.mbm_deployment
    for idx,peer in enumerate(('host','guest')):
        py=y+126+idx*158
        add('player_'+peer,(x,py,width,96),{'host':('Host · Ogryn' if lang=='en' else '房主 · 欧格林' if lang=='zh-cn' else '房主 · 歐格林'),'guest':('Guest · Psyker' if lang=='en' else '客机 · 灵能者' if lang=='zh-cn' else '客機 · 靈能者')}[peer],font=24,fill=True)
        dw=L.globals().UIWidget.init('deployment',L.globals().UIWidget.create_definition(bp.pass_template,'row'))
        bp.init(grid,dw,tbl({'mbm_status_peer':peer}));bp.update(grid,dw)
        add('deployment_'+peer,(x+16,py+96,width-32,32),dw.content.text,font=17,color='muted' if peer=='guest' else 'gold')
    result[lang+'_realms']=items
# Test fitted canvas bounds at common aspect ratios; scale is native fit, not a stretched HUD.
for label,items in result.items():
    for item in items:
        assert 0<=item['x'] and 0<=item['y'] and item['x']+item['w']<=1920 and item['y']+item['h']<=1000,(label,item)
    for w,h in ((1920,1080),(1280,720),(2560,1440),(1920,1200),(3440,1440),(1440,1080)):
        scale=min(w/1920,h/1080)
        for item in items:assert item['w']*scale<=w and item['h']*scale<=h
(CHECKS/'ui-layouts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Exported real picker/HUD/Realms widget geometry in three languages; six resolution/aspect cases checked.')

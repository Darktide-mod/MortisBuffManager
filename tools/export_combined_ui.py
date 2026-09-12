"""Optional visual QA of both real control blueprints; no runtime dependency."""
from pathlib import Path
import json,sys,os
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'tests'))
from ui_native_env import *
talent=Path(os.environ.get('DARKTIDE_TALENT_SOURCE',PROJECT.parent/'TalentPointManager/src/TalentPointManager'))
if not talent.is_dir():
    print('Talent source absent: retaining the standalone Mortis preview.')
    raise SystemExit(0)
MC=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_realms_controls')
T=L.globals().new_test_mod('TalentPointManager');L.globals().T=T;L.globals().M=mod
T.localization=L.execute((talent/'scripts/mods/TalentPointManager/TalentPointManager_localization.lua').read_text(encoding='utf-8-sig'))
TC=L.execute((talent/'scripts/mods/TalentPointManager/modules/realms_player_controls.lua').read_text(encoding='utf-8-sig'))
L.execute('''
M.mortis_realms_controls_active=function() return true end
M.mortis_global_rules_snapshot=function() return {enabled=true,mode="competition",limit=8,revision=1},"room" end
M.mortis_peer_deployment=function(peer) return {status=peer=="guestA" and "loading_assets" or peer=="guestB" and "incompatible" or "ready",version=peer~="guestB" and "3.1.1" or nil} end
T.realms_talent_controls_active=function() return true end
T.realms_talent_player_rules=function(peer) return {enabled=true,realms_player_points=peer=="host" and 60 or 45,unlock_all_auras=true,unlock_all_keystones=true,revision=1},"room" end
T.realms_talent_deployment=function(peer) return {status=peer=="guestA" and "loading" or "accepted",version="2.2.1"} end
''')
realms=FIXTURES/'mods/Realms/scripts/mods/Realms/views/preparation_view'
native_layout=L.execute((realms/'preparation_view_layout.lua').read_text(encoding='utf-8-sig'))
width=native_layout.player_row_width
result=json.loads((CHECKS/'ui-layouts.json').read_text(encoding='utf-8'))
for lang in ('en','zh-cn','zh-tw'):
    L.globals().test_language=lang;items=[]
    def add(key,x,y,w,h,text='',**options):items.append(dict(key=key,x=x,y=y,w=w,h=h,text=text,**options))
    x=native_layout.outer_margin+native_layout.panel_inset;y=native_layout.panel_top+native_layout.grid_top
    add('players_panel',80,180,1320,780,fill=True,panel=True)
    add('mission_panel',1440,180,400,780,fill=True,panel=True)
    add('mission_title',1460,196,360,48,{'en':'Mission details','zh-cn':'任务信息','zh-tw':'任務資訊'}[lang],font=24)
    add('mission_rules',1460,256,360,100,'SoloPlay + Realms\nMortis 3.1.1\nTalent 2.2.2',font=20)
    add('host_controls',x,180,width,36,{'en':'Host controls · Global Mortis rules / Per-player talent rules','zh-cn':'房主管理 · 全局死灵规则 / 按玩家调整天赋','zh-tw':'房主管理 · 全域死靈規則 / 依玩家調整天賦'}[lang],font=20)
    grid=tbl({'_mbm_realms_view':{},'_tpm_realms_view':{}})
    layout=tbl([{'widget_type':'player','peer_id':p} for p in ('host','guestA','guestB')])
    layout,bps=TC.wrap_layout(grid,layout,tbl({'player':{'size':[width,80]}}))
    layout,bps=MC.wrap_layout(grid,layout,bps)
    for idx in range(1,len(layout)+1):
        row=layout[idx];kind=row.widget_type;bp=bps[kind];height=bp.size[2]
        if kind=='player':
            names={'en':{'host':'Host · Ogryn','guestA':'Guest A · Psyker','guestB':'Guest B · Arbites'},'zh-cn':{'host':'房主 · 欧格林','guestA':'客机 A · 灵能者','guestB':'客机 B · 法务官'},'zh-tw':{'host':'房主 · 歐格林','guestA':'客機 A · 靈能者','guestB':'客機 B · 法務官'}}
            add('player_'+row.peer_id,x,y,width,height,names[lang][row.peer_id],font=24,fill=True)
        else:
            widget=L.globals().UIWidget.init(kind,L.globals().UIWidget.create_definition(bp.pass_template,'row'))
            bp.init(grid,widget,row)
            if bp.update:bp.update(grid,widget,None,0)
            add(kind+str(idx),x,y,width,height,fill=True,panel=True)
            for k,style in widget.style.items():
                text=widget.content[k]
                if isinstance(text,str) and style.font_size:
                    button=k not in ('mbm_label','mbm_status','tpm_label','tpm_status','text')
                    add(kind+str(idx)+k,x+style.offset[1],y+style.offset[2],style.size[1],style.size[2],text,
                        font=style.font_size,center=button,fill=button,selected=k=='mbm_competition',text_padding=0,
                        rgb=[style.text_color[i] for i in (2,3,4)] if k=='text' else None)
        y+=height+native_layout.row_spacing
    assert y<=native_layout.panel_top+native_layout.grid_top+native_layout.player_grid_size[2]
    result[lang+'_realms']=items
(CHECKS/'ui-layouts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Exported both actual mod controls together in native Realms geometry, in three languages.')

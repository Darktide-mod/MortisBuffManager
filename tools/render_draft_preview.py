"""Internal layout QA from actual HUD update/draw callbacks; no game or release images."""
from pathlib import Path
import sys,json,math
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'tests'))
from ui_native_env import *
from PIL import Image,ImageDraw,ImageFont
OUT=PROJECT/'build/draft-preview';OUT.mkdir(parents=True,exist_ok=True)
fonts={}
def font(n):
    n=round(n)
    if n not in fonts:fonts[n]=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
    return fonts[n]
def wrap(text,width,size):
    f=font(size);lines=[]
    for paragraph in text.split('\n'):
        words=paragraph.split(' ') if test_lang=='en' else list(paragraph)
        line=''
        for word in words:
            v=line+(' ' if test_lang=='en' and line else '')+word
            if line and f.getlength(v)>width:lines.append(line);line=word
            else:line=v
        lines.append(line)
    return lines
def measure(_,text,style,size,*rest):
    lines=wrap(text,size[1],style.font_size)
    return size[1],math.ceil(len(lines)*style.font_size*1.28)
L.globals().UIRenderer.styled_text_size=measure
L.globals().M=mod
HUD=load_mod('MortisBuffManager/scripts/mods/MortisBuffManager/modules/mortis_draft_hud')
L.globals().HUD=HUD
L.execute('''
P={};Managers.player={local_player_safe=function() return P end}
Managers.world={is_world_enabled=function() return true end};Managers.package={has_loaded=function() return true end}
Managers.ui={using_input=function() return false end};RESOLUTION_LOOKUP={scale=1,inverse_scale=1}
input={is_null_service=function() return false end};hud={_player=P,_world_name="world",_ui_renderer={}}
function M.mortis_draft_snapshot() return snapshot,0,false end
function M.mortis_choice_ui_data(name) return samples[name] end
function tick(dt)
 for _,h in ipairs(hooks) do if h.target==UIHud and h.name=="update" then h.fn(hud,dt,0,input) end end
 rendered={}
 for _,h in ipairs(hooks) do if h.target==UIHud and h.name=="draw" then h.fn(hud,dt,0,input) end end
end
UIRenderer.begin_pass=function(_,g) graph=g end;UIRenderer.end_pass=function() end
UIWidget.draw=function(w) rendered[#rendered+1]=table.clone_instance(w) end
''')
samples={
'en': [('Extra ability charge','Gain an additional combat ability charge.'),('Explosive ranged kills','Ranged kills trigger an explosion around the defeated enemy. This effect can trigger once every 1 second.'),('Healing on grenade explosion','When a grenade explodes, allies within its area recover health. Each ally can benefit once per explosion.')],
'zh-cn':[('额外技能充能','获得额外的战斗技能充能。'),('远程击杀爆炸','远程击杀会在被击败的敌人周围引发爆炸。此效果每 1 秒最多触发一次。'),('手雷爆炸治疗','手雷爆炸时，范围内的队友恢复生命值。每名队友每次爆炸只能获得一次治疗。')],
'zh-tw':[('額外技能充能','獲得額外的戰鬥技能充能。'),('遠程擊殺爆炸','遠程擊殺會在被擊敗的敵人周圍引發爆炸。此效果每 1 秒最多觸發一次。'),('手榴彈爆炸治療','手榴彈爆炸時，範圍內的隊友恢復生命值。每名隊友每次爆炸只能獲得一次治療。')]}
def bounds(g,key):
    if key in ('screen','canvas'):return 0,0,1920,1080
    n=g[key];x,y,pw,ph=bounds(g,n.parent);w,h=n.size[1],n.size[2]
    x+=(pw-w)/2 if n.horizontal_alignment=='center' else 0
    y+=(ph-h) if n.vertical_alignment=='bottom' else 0
    return x+n.position[1],y+n.position[2],w,h
records=[]
for test_lang,entries in samples.items():
    L.globals().test_language=test_lang
    L.execute('HUD.cleanup()')
    L.globals().samples=tbl({chr(97+i):dict(display_name=n,description=d,subtitle='Major Buff' if test_lang=='en' else '主要 Buff') for i,(n,d) in enumerate(entries)})
    L.globals().snapshot=tbl(dict(epoch=test_lang,mode='competition',counting=True,completed=1,rewards=[],active=dict(id='1',kind='legendary',choices=['a','b','c'],remaining=48),progress=57.75,spent=2,earned=4,queued=1,limit=7))
    for stage in ('choices','selected','award'):
        if stage=='selected':
            L.globals().snapshot.active=None;L.globals().snapshot.last=tbl(dict(id='1',index=2))
            L.globals().snapshot.completed=2;L.globals().snapshot.rewards=tbl([dict(id=3,name='c',round=2)])
        L.globals().tick(.4 if stage=='choices' else .1 if stage=='selected' else .8)
        if stage in ('choices','award'):L.globals().tick(.3)  # Inspect after the real fade-in.
        graph=L.globals().graph
        im=Image.new('RGB',(1920,1080),(9,16,13));draw=ImageDraw.Draw(im)
        boxes=[]
        for _,widget in L.globals().rendered.items():
            x,y,w,h=bounds(graph,widget.scenegraph_id);x+=widget.offset[1];y+=widget.offset[2];alpha=widget.alpha_multiplier or 1
            boxes.append((x,y,w,h))
            if widget.style.background:
                c=widget.style.background.color
                draw.rectangle((x,y,x+w,y+h),fill=tuple(round(c[i]*alpha) for i in (2,3,4)),outline=(183,158,89))
            for key in ('title','subtitle','description','key','label','text'):
                text=widget.content[key];style=widget.style[key]
                if not isinstance(text,str) or not style or not text:continue
                xx,yy=x+style.offset[1],y+style.offset[2];ww,hh=style.size[1],style.size[2]
                lines=wrap(text,ww,style.font_size);lh=math.ceil(style.font_size*1.28)
                assert len(lines)*lh<=hh+3,(test_lang,stage,key,text,hh)
                if style.text_vertical_alignment!='top':yy+=(hh-len(lines)*lh)/2
                for line in lines:
                    tx=xx+(ww-font(style.font_size).getlength(line))/2 if style.text_horizontal_alignment=='center' else xx
                    draw.text((tx,yy),line,font=font(style.font_size),fill=tuple(round(v*alpha) for v in (232,229,210)));yy+=lh
        for width,height in ((1920,1080),(1920,1200),(2560,1080),(1440,1080)):
            scale=min(width/1920,height/1080);dx=(width-1920*scale)/2;dy=(height-1080*scale)/2
            for x,y,w,h in boxes:assert dx+x*scale>=0 and dy+y*scale>=0 and dx+(x+w)*scale<=width and dy+(y+h)*scale<=height
            canvas=Image.new('RGB',(width,height),(9,16,13));canvas.paste(im.resize((round(1920*scale),round(1080*scale))), (round(dx),round(dy)))
            ImageDraw.Draw(canvas).text((30,height-38),'Internal UI layout check - sample text, not a gameplay capture',font=font(16),fill=(130,145,135))
            filename=f'{test_lang}-{stage}-{width}x{height}.png';canvas.save(OUT/filename);records.append(filename)
(OUT/'checks.json').write_text(json.dumps(dict(layouts=len(records),status='passed'),indent=2),encoding='utf-8')
print(f'Actual HUD callbacks: {len(records)} internal renders, full text and bounds checked across three languages / four aspect ratios.')

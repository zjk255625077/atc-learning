import re

with open('易错知识（毛玻璃效果）_副本.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ================================================================
# 1. BUILD NEW atcData (11 items)
# ================================================================

# Color classes
GRAY = "text-[#1d1d1f] bg-[#f5f5f7] border-[#e8e8ed]"
BLUE = "text-[#0071e3] bg-[#e8f2ff] border-[#bfdbfe]"
GREEN = "text-[#16a34a] bg-[#f0fdf4] border-[#dcfce7]"
RED = "text-[#e11d48] bg-[#fff1f2] border-[#ffe4e6]"

atcData_items = [
    # [0] 首次呼叫放行
    "{id:'delivery',phaseGroup:'Delivery',phaseColor:'"+GRAY+"',icon:'🏢',title:'首次呼叫放行 (Delivery)',formula:'[Delivery] + [飞机呼号] + [机位] + [通播代号] + PDI([位置]+[目的地]) + [请求放行]',example:'\"Wuhan Delivery, ACA909, gate 21, info E, PDI Shanghai, request clearance.\"',why:'Delivery席位负责放行许可发布。机组首次联系须声明位置(PDI)和通播版本，管制员据此发布包含目的地、航路、初始高度、应答机编码的放行许可。全依赖飞行员的口头汇报获知机位信息，以便规划推出顺序和滑行路线。飞行员在首次联系时必须告知当前机位编号和所抄收气象通播（ATIS）的最新版本代码（A-Z 循环）。管制员如果发现飞行员未抄收最新通播版本，将拒绝放行并要求先完成抄收——因为 QNH、RVR 等标准气压和跑道视程数据一旦过期，可能导致起飞阶段的高度表偏差和飞行冲突。'}",
    
    # [1] 推出与滑行
    "{id:'ground',phaseGroup:'Ground',phaseColor:'"+GRAY+"',icon:'🚜',title:'推出与滑行 (Ground)',formula:'[Ground] + [飞机呼号] + [机位] + [请求推出/滑行]',example:'\"Wuhan Ground, ACA909, gate 21, request pushback.\"',why:'地面滑行阶段是机场运行中事故隐患最高的环节之一。飞行员在首次联系地面时必须按标准格式汇报三要素：① 当前准确的机位编号，供管制员在地面雷达或场监屏幕上快速锁定目标；② 请求的具体动作：推出、开车、滑行等；③ 机上掌握的场压或通播代号。地面管制员的视野受建筑和道面遮挡严重，对每架飞机的判断几乎完全依赖无线电报告——位置和意图的完整陈述，是防止地面误听和误操作的关键保障。'}",
    
    # [2] 跑道外等待
    "{id:'tower_hold',phaseGroup:'Tower',phaseColor:'"+BLUE+"',icon:'🛑',title:'跑道外等待 (Tower Holding)',formula:'[Tower] + [飞机呼号] + [在XX跑道外等待]',example:'\"Wuhan Tower, ACA909, holding short of runway 36R.\"',why:'跑道外等待（Hold Short of Runway）是防止跑道侵入的第一道防线。飞行员由地面频率切换至塔台频率的瞬间，塔台管制员的最高优先级是确认该航空器是否已准确到达指定的等待点，以及是否符合 hold short of runway 的限制要求。完整的汇报不仅仅是一个格式问题——它在法律层面构成了「我已确认跑道边界、承诺不越线」的口头承诺，是目视观察与雷达监视之外的第三重安全红线保障。'}",
    
    # [3] 起飞 (NEW - split from 起飞与离场)
    "{id:'takeoff',phaseGroup:'Tower',phaseColor:'"+BLUE+"',icon:'🚀',title:'起飞 (Takeoff)',formula:'[Tower] + [飞机呼号] + [跑道号] + cleared for takeoff + [起始高度] + [应答机编码]',example:'\"Beijing Tower, CCA1501, holding point 36R, ready.\" / \"CCA1501, wind 210/5, QNH 1013, RWY 36R, cleared for takeoff, initial climb 6000ft, squawk 4321.\"',why:'起飞阶段由塔台(Tower)管制。机组在进入跑道前必须获得起飞许可，包含跑道号、风向风速、修正海压(QNH)、起始高度和应答机编码。起飞指令须完整复诵，不得使用Roger/Wilco代替。起飞后按照指令联系离场管制(Departure)。'}",
    
    # [4] 离场 (NEW - split from 起飞与离场)
    "{id:'departure',phaseGroup:'Departure',phaseColor:'"+GREEN+"',icon:'✈️',title:'离场 (Departure)',formula:'[Departure] + [飞机呼号] + [通过高度] + [爬升到目标高度] + [应答机编码]',example:'\"Beijing Departure, CCA1501, passing 1500 climbing FL180.\" / \"CCA1501, radar identified, climb FL270, squawk 4321.\"',why:'离场管制(Departure)负责起飞后至航路阶段的爬升间隔调配。根据ICAO Doc 4444，当飞机首次进入雷达管制区时，管制员必须将SSR二次雷达显示的高度标牌与飞行员的口头报告进行交叉比对。飞行员必须同时报告passing（当前正通过的高度）和climbing to（目标高度层），两者差值在±60米以内才能宣布Radar Identified。'}",
    
    # [5] 航路巡航
    "{id:'control',phaseGroup:'Control',phaseColor:'"+GREEN+"',icon:'🛩️',title:'航路巡航 (Control)',formula:'[Control] + [飞机呼号] + [保持高度层] + [应答机编码确认]',example:'\"Wuhan Control, ACA909, maintaining FL330.\"',why:'巡航阶段以保持固定高度层（Maintain FLXXX）为特征。飞行员在首次联系新的区域管制中心时，必须以 maintaining 而不是 passing 来报告当前高度。少数飞行员习惯性地沿用离场阶段的 passing + climbing 格式，若误用在平飞巡航阶段，会让管制员以为该航空器正处于爬升或下降的过渡过程中，从而错误计算与其他飞机之间的垂直间隔。maintaining 是法律意义上的稳定保持状态，而 passing 是穿越状态，两者有着本质区别——选错用词可能触发不必要的冲突告警。'}",
    
    # [6] 下降与进近
    "{id:'approach_inbound',phaseGroup:'Approach',phaseColor:'"+GREEN+"',icon:'📉',title:'下降与进近 (Descent & Approach)',formula:'[Approach] + [飞机呼号] + [高度层] + [飞往航路点] + [进近程序]',example:'\"Wuhan Approach, ACA909, maintaining FL150, inbound JM.\"',why:'进近管制是整个飞行剖面中工作负荷最高的环节。管制员需要在有限的时间窗口内，将来自不同方向、不同高度的进场飞机排列成有序的降落队列。飞行员在首次联系进近时，除了报告当前高度，还必须汇报正在飞向的标准进场交接点名称，这相当于告诉管制员：我从哪扇航路大门进入终端区。没有这个交接点信息，管制员就需要额外花时间在雷达屏幕上搜寻匹配你的航迹属于哪条进场流，进而直接影响后续排序、下降时机和间隔调配的效率与安全。进近排序常用句型：① Number two in sequence, follow the aircraft ahead. ② Reduce speed to 180 knots for sequencing. ③ Orbit right for spacing. 这些句型需配合完整复诵，确保排序间隔安全准确。'}",
    
    # [7] 最终进近 (NEW - split from 进近与着陆)
    "{id:'final_approach',phaseGroup:'Approach',phaseColor:'"+GREEN+"',icon:'📍',title:'最终进近 (Final Approach)',formula:'[Approach] + [飞机呼号] + established [进近方式] + runway [跑道号]',example:'\"Beijing Approach, CCA1501, established ILS Runway 36R.\" / \"CCA1501, continue, number one, contact Tower 118.7.\"',why:'最终进近(Final Approach)阶段，飞机已建立仪表着陆系统(ILS)的航向道和下滑道。进近管制负责建立最终排序间隔，机组必须报告已建立进近。当飞机稳定在航向道和下滑道上，管制员将指令联系塔台(Tower)获取着陆许可。建立进近后的标准话术为 established ILS Runway XX。'}",
    
    # [8] 复飞 (NEW - split from 进近与着陆)
    "{id:'go_around',phaseGroup:'Tower',phaseColor:'"+RED+"',icon:'🔄',title:'复飞 (Go-around)',formula:'[Tower] + [飞机呼号] + go around + [复飞高度] + [复飞程序]',example:'\"CCA1501, go around, climb to 900 meters, follow missed approach procedure.\" / \"Go around, climb 900 meters, CCA1501.\"',why:'复飞(Go-around)是中断进近的标准程序，可能由于跑道占用、前机未脱离、间隔不足、风切变或接地条件不具备等原因触发。机组收到复飞指令后必须立即执行，不得犹豫。复飞后需按指定高度爬升并按复飞程序飞行，随后联系进近管制获取进一步指令。复飞指令须完整复诵高度和程序。'}",
    
    # [9] 着陆 (NEW - split from 进近与着陆)
    "{id:'landing',phaseGroup:'Tower',phaseColor:'"+BLUE+"',icon:'🛬',title:'着陆 (Landing)',formula:'[Tower] + [飞机呼号] + [风] + Runway [跑道号] + cleared to land',example:'\"CCA1501, wind 350/8, RVR 800m, Runway 36R, cleared to land.\" / \"Runway 36R, cleared to land, CCA1501.\"',why:'着陆许可是最高优先级指令，必须完整复诵包含跑道号和许可指令的完整内容。根据ICAO标准，着陆许可包含：① 跑道号(Runway XX) ② 风向风速 ③ 跑道视程(RVR)或能见度 ④ 许可指令(cleared to land)。涉及着陆的许可绝对不能使用Roger或Wilco简化，这是ICAO/CCAR的绝对红线。着陆后需及时脱离跑道并联系地面管制。'}",
    
    # [10] 脱离 (NEW)
    "{id:'vacate',phaseGroup:'Ground',phaseColor:'"+GRAY+"',icon:'🚗',title:'脱离跑道 (Vacate)',formula:'[Tower/Ground] + [飞机呼号] + vacated [跑道号] + via [滑行道] + [滑行指令]',example:'\"Beijing Ground, CCA1501, vacated 36R via high-speed, request taxi to stand.\" / \"CCA1501, taxi to stand 4 via Alpha, hold short.\"',why:'脱离跑道(Vacate)阶段是着陆与地面滑行之间的过渡环节。飞行员脱离跑道后必须先在塔台频率报告 vacated + 跑道号 + 脱离滑行道，然后根据指令联系地面管制(Ground)。地面管制发布滑行至停机位的指令，包含具体滑行路线和等待点。未报告脱离前不得自行切换频率。'}",
]

new_atcData = 'const atcData=[' + ','.join(atcData_items) + '];'

# ================================================================
# 2. BUILD NEW FLIGHT_PHASES (11 items)
# ================================================================

fp_items = [
    # [0] id:1 - 首次呼叫与放行许可
    """{id:1,number:"PHASE 01",name:"首次呼叫与放行许可",engName:"Clearance Delivery",sector:"Delivery",freq:"121.70",formulas:[{type:"主动呼叫",formulaHtml:"[Delivery]+[飞机呼号]+[机位]+info[通播代号]+PDI[位置]+[目的地]+request clearance"},{type:"复诵",formulaHtml:"Cleared to[目的]+via[离场]+initially climb[高度]+squawk[编码]+[飞机呼号]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Delivery, CCA1501, stand 321, info A, PDI Shanghai Pudong, request clearance.",textChn:"北京放行，国航1501，机位321，A通播，PDI上海浦东，请求放行。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, cleared to Shanghai Pudong via DYNAR-1A departure, initial climb 9000ft, squawk 4321.",textChn:"国航1501，许可沿DYNAR-1A离场至上海浦东，起始上升9000英尺，应答机4321。"},{role:"PILOT",roleName:"飞行员",textEng:"Cleared to Shanghai Pudong via DYNAR-1A, initial climb 9000ft, squawk 4321, CCA1501.",textChn:"许可DYNAR-1A去浦东，起始9000英尺应答机4321，国航1501。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, readback correct, contact Ground 121.9 when ready for pushback.",textChn:"国航1501，复诵正确，推开联系地面121.9。"}]}""",
    
    # [1] id:2 - 推出与滑行
    """{id:2,number:"PHASE 02",name:"推出与滑行",engName:"Pushback & Taxi",sector:"Ground",freq:"121.90",formulas:[{type:"推出",formulaHtml:"[Ground]+[飞机呼号]+pushback[机位]+request taxi"},{type:"滑行",formulaHtml:"[Ground]+[飞机呼号]+taxi via[滑行道]+to[等待点]+hold short+[飞机呼号]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Ground, CCA1501, stand 321, request pushback and start up.",textChn:"北京地面，国航1501，机位321，请求推开开车。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, pushback approved, nose east.",textChn:"国航1501，推开批准，机头朝东。"},{role:"PILOT",roleName:"飞行员",textEng:"Pushback approved, nose east, CCA1501.",textChn:"推开批准机头朝东，国航1501。"},{role:"PILOT",roleName:"飞行员",textEng:"Beijing Ground, CCA1501, pushback complete, request taxi.",textChn:"北京地面，国航1501，推开完毕，请求滑行。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, taxi to holding point Runway 36R via Romeo, hold short.",textChn:"国航1501，经Romeo滑行至36R等待点等待。"},{role:"PILOT",roleName:"飞行员",textEng:"Taxi to holding point 36R via Romeo, hold short, CCA1501.",textChn:"经Romeo滑行至36R等待等待，国航1501。"}]}""",
    
    # [2] id:3 - 跑道外等待
    """{id:3,number:"PHASE 03",name:"跑道外等待",engName:"Hold Short",sector:"Tower",freq:"118.70",formulas:[{type:"等待指令",formulaHtml:"[Tower]+[飞机呼号]+hold short of runway[跑道号]"},{type:"穿越许可",formulaHtml:"[Tower]+[飞机呼号]+cross runway[跑道号]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Tower, CCA1501, holding short of Runway 36R.",textChn:"北京塔台，国航1501，36R外等待。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, hold short of Runway 36R, number one for departure.",textChn:"国航1501，36R外等待，起飞第一位。"},{role:"PILOT",roleName:"飞行员",textEng:"Hold short of 36R, CCA1501.",textChn:"36R外等待，国航1501。"}]}""",
    
    # [3] id:4 - 起飞 (NEW - split from current id:3)
    """{id:4,number:"PHASE 04",name:"起飞",engName:"Takeoff",sector:"Tower",freq:"118.70",formulas:[{type:"起飞许可",formulaHtml:"[Tower]+[飞机呼号]+[跑道]+[风]+QNH[海压]+cleared for takeoff+initial climb[高度]+squawk[编码]"},{type:"联系离场",formulaHtml:"[Tower]+[飞机呼号]+contact[离场频率]}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Tower, CCA1501, holding point 36R, ready for departure.",textChn:"北京塔台，国航1501，36R等待点，准备好起飞。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, wind 210/5, QNH 1013, Runway 36R, cleared for takeoff, initial climb 6000ft, squawk 4321.",textChn:"国航1501，风210/5，QNH1013，36R，许可起飞，初始上升6000英尺，应答机4321。"},{role:"PILOT",roleName:"飞行员",textEng:"Cleared for takeoff 36R, initial climb 6000ft, squawk 4321, CCA1501.",textChn:"许可起飞36R，起始6000英尺应答机4321，国航1501。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, contact Departure 125.6.",textChn:"国航1501，联系离场125.6。"},{role:"PILOT",roleName:"飞行员",textEng:"Contact Departure 125.6, CCA1501.",textChn:"联系离场125.6，国航1501。"}]}""",
    
    # [4] id:5 - 离场 (NEW - split from id:4 Departure/Climb)
    """{id:5,number:"PHASE 05",name:"离场",engName:"Departure",sector:"Departure",freq:"125.60",formulas:[{type:"首次呼叫",formulaHtml:"[Departure]+[飞机呼号]+passing[高度]+climbing to[目标高度]"},{type:"雷达识别",formulaHtml:"[Departure]+[飞机呼号]+radar identified+climb[高度]+squawk[编码]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Departure, CCA1501, passing 1500 climbing FL180.",textChn:"北京离场，国航1501，通过1500上升FL180。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, radar identified, climb FL270, squawk 4321.",textChn:"国航1501，雷达识别，上升FL270，应答机4321。"},{role:"PILOT",roleName:"飞行员",textEng:"Climb FL270, squawk 4321, CCA1501.",textChn:"上升FL270应答机4321，国航1501。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, contact Control 132.8.",textChn:"国航1501，联系区调132.8。"},{role:"PILOT",roleName:"飞行员",textEng:"Contact Control 132.8, CCA1501.",textChn:"联系区调132.8，国航1501。"}]}""",
    
    # [5] id:6 - 航路巡航 (original id:4)
    """{id:6,number:"PHASE 06",name:"航路巡航",engName:"En-Route Cruise",sector:"Control",freq:"132.80",formulas:[{type:"首次呼叫",formulaHtml:"[Control]+[飞机呼号]+maintaining[高度层]"},{type:"指令复诵",formulaHtml:"[Control]+[飞机呼号]+climb/descend to[高度层]+squawk[编码]+[飞机呼号]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Control, CCA1501, maintaining FL270.",textChn:"北京区调，国航1501，保持FL270。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, climb FL330, expedite through FL310 due traffic.",textChn:"国航1501，上升FL330，加速通过FL310。"},{role:"PILOT",roleName:"飞行员",textEng:"Climb FL330, expedite through FL310, CCA1501.",textChn:"上升FL330加速通过FL310，国航1501。"}]}""",
    
    # [6] id:7 - 下降与进近 (original id:5)
    """{id:7,number:"PHASE 07",name:"下降与进近",engName:"Descent & Approach",sector:"Approach",freq:"119.70",formulas:[{type:"下降复诵",formulaHtml:"[Approach]+[飞机呼号]+descend to[高度]+QNH[海压]+[限速]"},{type:"进场复诵",formulaHtml:"[Approach]+[飞机呼号]+follow[程序]+approach for[跑道]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Approach, CCA1501, descending FL150.",textChn:"北京进近，国航1501，下降FL150。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, report maintaining FL150 at JM.",textChn:"国航1501，报告在JM点保持FL150。"},{role:"PILOT",roleName:"飞行员",textEng:"Maintaining FL150 at JM, CCA1501.",textChn:"JM点保持FL150，国航1501。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, descend 3000m, QNH 1013, follow JM-1A approach 36R.",textChn:"国航1501，下降3000米QNH1013，跟随JM-1A进近36R。"},{role:"PILOT",roleName:"飞行员",textEng:"Descend 3000m, QNH 1013, JM-1A approach 36R, CCA1501.",textChn:"下降3000米QNH1013，JM-1A进近36R，国航1501。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, reduce speed to 180 knots, number two in sequence.",textChn:"国航1501，减速180节，排序第二位。"},{role:"PILOT",roleName:"飞行员",textEng:"Reduce speed 180, number two, CCA1501.",textChn:"减速180，第二位，国航1501。"}]}""",
    
    # [7] id:8 - 最终进近 (NEW - split from id:6)
    """{id:8,number:"PHASE 08",name:"最终进近",engName:"Final Approach",sector:"Approach",freq:"119.70",formulas:[{type:"建立进近",formulaHtml:"[Approach]+[飞机呼号]+established[进近方式]+runway[跑道号]"},{type:"联系塔台",formulaHtml:"[Approach]+[飞机呼号]+contact Tower[频率]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Approach, CCA1501, established ILS Runway 36R.",textChn:"北京进近，国航1501，建立36R进近。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, continue approach, number one in sequence.",textChn:"国航1501，继续进近，排序第一位。"},{role:"PILOT",roleName:"飞行员",textEng:"Continue approach, CCA1501.",textChn:"继续进近，国航1501。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, contact Tower 118.7.",textChn:"国航1501，联系塔台118.7。"},{role:"PILOT",roleName:"飞行员",textEng:"Contact Tower 118.7, CCA1501.",textChn:"联系塔台118.7，国航1501。"}]}""",
    
    # [8] id:9 - 复飞 (NEW - from existing go-around content)
    """{id:9,number:"PHASE 09",name:"复飞",engName:"Go-around",sector:"Tower",freq:"118.70",formulas:[{type:"复飞指令",formulaHtml:"[Tower]+[飞机呼号]+go around+[复飞高度]+[复飞程序]"},{type:"报告",formulaHtml:"[飞行员]+[飞机呼号]+going around+[复飞高度]"}],dialogue:[{role:"ATC",roleName:"管制员",textEng:"CCA1501, go around, climb to 900 meters, follow missed approach procedure.",textChn:"国航1501，复飞，上升900米，按复飞程序。"},{role:"PILOT",roleName:"飞行员",textEng:"Go around, climb 900 meters, CCA1501.",textChn:"复飞上升900米，国航1501。"},{role:"PILOT",roleName:"飞行员",textEng:"Beijing Approach, CCA1501, going around, climbing 900 meters.",textChn:"北京进近，国航1501，复飞上升900米。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, maintain 900 meters, expect further clearance.",textChn:"国航1501，保持900米，等待进一步指令。"}]}""",
    
    # [9] id:10 - 着陆 (NEW - split from id:6)
    """{id:10,number:"PHASE 10",name:"着陆",engName:"Landing",sector:"Tower",freq:"118.70",formulas:[{type:"五边汇报",formulaHtml:"[Tower]+[飞机呼号]+established ILS runway[跑道号]"},{type:"着陆许可",formulaHtml:"[Tower]+[飞机呼号]+[风]+RVR[能见度]+Runway[跑道号]+cleared to land+[飞机呼号]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Tower, CCA1501, established ILS Runway 36R.",textChn:"北京塔台，国航1501，建立36R进近。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, continue approach.",textChn:"国航1501，继续进近。"},{role:"PILOT",roleName:"飞行员",textEng:"Continue approach, CCA1501.",textChn:"继续进近，国航1501。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, wind 350/8, RVR 800m, Runway 36R, cleared to land.",textChn:"国航1501，风350/8，跑道视程800米，36R可以着陆。"},{role:"PILOT",roleName:"飞行员",textEng:"Runway 36R, cleared to land, CCA1501.",textChn:"36R可以着陆，国航1501。"}]}""",
    
    # [10] id:11 - 脱离 (NEW)
    """{id:11,number:"PHASE 11",name:"脱离跑道",engName:"Vacate Runway",sector:"Ground",freq:"121.90",formulas:[{type:"脱离报告",formulaHtml:"[Tower]+[飞机呼号]+vacated[跑道号]+via[滑行道]"},{type:"滑行指令",formulaHtml:"[Ground]+[飞机呼号]+taxi to[停机位]+via[路线]+hold short+[飞机呼号]"}],dialogue:[{role:"PILOT",roleName:"飞行员",textEng:"Beijing Tower, CCA1501, vacated 36R via high-speed turnoff.",textChn:"北京塔台，国航1501，高速脱离36R。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, contact Ground 121.9.",textChn:"国航1501，联系地面121.9。"},{role:"PILOT",roleName:"飞行员",textEng:"Contact Ground 121.9, CCA1501.",textChn:"联系地面121.9，国航1501。"},{role:"PILOT",roleName:"飞行员",textEng:"Beijing Ground, CCA1501, vacated 36R, request taxi to stand.",textChn:"北京地面，国航1501，脱离36R，请求滑行至机位。"},{role:"ATC",roleName:"管制员",textEng:"CCA1501, taxi to stand 4 via Alpha, hold short of runway.",textChn:"国航1501，经Alpha滑行至4号位，等待。"},{role:"PILOT",roleName:"飞行员",textEng:"Taxi to stand 4 via Alpha, hold short, CCA1501.",textChn:"经Alpha滑行至4号位等待，国航1501。"}]}""",
]

new_FLIGHT_PHASES = 'const FLIGHT_PHASES=[' + ','.join(fp_items) + '];'

# ================================================================
# 3. REPLACE IN FILE
# ================================================================

# Replace atcData
old_atc_start = content.find('const atcData=[')
old_atc_end = content.find('];', old_atc_start) + 2
print(f"atcData: replacing {old_atc_end - old_atc_start} bytes with {len(new_atcData)} bytes")
content = content[:old_atc_start] + new_atcData + content[old_atc_end:]

# Replace FLIGHT_PHASES
old_fp_start = content.find('const FLIGHT_PHASES=[')
old_fp_end = content.find('];', old_fp_start) + 2
print(f"FLIGHT_PHASES: replacing {old_fp_end - old_fp_start} bytes with {len(new_FLIGHT_PHASES)} bytes")
content = content[:old_fp_start] + new_FLIGHT_PHASES + content[old_fp_end:]

# ================================================================
# 4. BUILD NEW HARDCODED BUTTONS HTML
# ================================================================

btn_templates = [
    # (icon, title, engName, badge, badgeColor)
    ('🏢', '首次呼叫放行', 'Delivery', 'Delivery', GRAY),
    ('🚜', '推出与滑行', 'Ground', 'Ground', GRAY),
    ('🛑', '跑道外等待', 'Tower', 'Tower', BLUE),
    ('🚀', '起飞', 'Takeoff', 'Tower', BLUE),
    ('✈️', '离场', 'Departure', 'Departure', GREEN),
    ('🛩️', '航路巡航', 'Control', 'Control', GREEN),
    ('📉', '下降与进近', 'Approach', 'Approach', GREEN),
    ('📍', '最终进近', 'Final Approach', 'Approach', GREEN),
    ('🔄', '复飞', 'Go-around', 'Tower', RED),
    ('🛬', '着陆', 'Landing', 'Tower', BLUE),
    ('🚗', '脱离跑道', 'Vacate', 'Ground', GRAY),
]

# Badge color mapping
badge_colors = {
    'Delivery': 'bg-[#f5f5f7] text-[#86868b] border',
    'Ground': 'bg-[#f5f5f7] text-[#86868b] border',
    'Tower': 'bg-[#e8f2ff]/20 text-[#0071e3] border border-[#bfdbfe]',
    'Departure': 'bg-[#f0fdf4] text-[#16a34a] border border-[#dcfce7]',
    'Control': 'bg-[#f0fdf4] text-[#16a34a] border border-[#dcfce7]',
    'Approach': 'bg-[#f0fdf4] text-[#16a34a] border border-[#dcfce7]',
}

button_htmls = []
for i, (icon, title, eng_name, badge, color) in enumerate(btn_templates):
    bc = badge_colors.get(badge, badge_colors['Delivery'])
    btn = f"""<button onclick="selectPhase({i})" class="phase-btn w-full text-left flex items-center justify-between p-3.5 rounded-2xl glass hover:bg-[var(--hover-bg)] transition-all group"><div class="flex items-center gap-3.5"><span class="absolute left-[-13px] flex h-6 w-6 items-center justify-center rounded-full bg-[#f5f5f7] border border-[#e8e8ed] text-[11px] font-semibold text-[#86868b] group-hover:scale-105 transition-all">{i+1}</span><span class="text-lg">{icon}</span><div><div class="font-semibold text-[#1d1d1f] text-sm">{title}</div><div class="text-xs text-[#86868b]">{eng_name}</div></div></div><span class="text-[10px] font-semibold {bc} px-2.5 py-0.5 rounded-full">{badge}</span></button>"""
    button_htmls.append(btn)

new_buttons_html = f'<div class="lg:col-span-5 space-y-2.5"><div class="relative pl-4 border-l border-[#e8e8ed] ml-3 space-y-2">\n' + '\n'.join(button_htmls) + '\n</div></div>'

# Find and replace the button section
old_btn_start = content.find('<div class="lg:col-span-5 space-y-2.5">')
old_btn_end = content.find('</div>\n</div>\n<div class="lg:col-span-7">', old_btn_start) + len('</div>')
# The section ends with: </div></div>
# But let me be more precise - find the closing pattern
# After the buttons section: </div></div><div class="lg:col-span-7">
old_btn_section = content[old_btn_start:old_btn_end]
# The button section includes the buttons container div + closing divs
# Looking at: <div class="lg:col-span-5 space-y-2.5">...buttons...</div></div>
# The </div></div> closes the space-y-2.5 and the parent relative div

# Find the exact end - search for the end of the button section
# The button section is followed by <div class="lg:col-span-7">
btn_section_end_search = old_btn_start
# Find the buttons container: <div class="lg:col-span-5 space-y-2.5">
# Then find its closing </div>
# And the parent </div> that closes <div class="relative pl-4...">

# Count the div nesting from old_btn_start
btn_section_end = old_btn_start
depth = 0
# The section starts with <div class="lg:col-span-5...
# We need to find the matching closings: </div></div>
# which closes the col-span-5 and the relative pl-4 divs

# Simple approach: find the pattern
# After the buttons section: </div>\n</div>\n<div class="lg:col-span-7">
search_pattern = '</div>\n</div>\n<div class="lg:col-span-7">'
pat_pos = content.find(search_pattern, old_btn_start)
if pat_pos > 0:
    old_btn_end = pat_pos  # End before the <div class="lg:col-span-7">
    old_btn_full = content[old_btn_start:old_btn_end + len('</div>')]  # Include the last </div>
    # Actually, we want to replace just the buttons part, keeping the surrounding structure
    # The section structure is: <div class="lg:col-span-5 space-y-2.5"><div class="relative pl-4...">buttons</div></div>
    # We want to replace the content inside lg:col-span-5
    
    # Let me find the inner div with relative pl-4
    inner_start = content.find('<div class="relative pl-4', old_btn_start)
    inner_end = content.find('</div></div>', old_btn_start, pat_pos)
    if inner_end > 0:
        inner_end += len('</div>')  # Include first </div>
        
        # New buttons content (the inner part with the buttons)
        new_buttons_inner = '<div class="relative pl-4 border-l border-[#e8e8ed] ml-3 space-y-2">\n' + '\n'.join(button_htmls) + '\n</div>'
        
        # Replace
        content = content[:inner_start] + new_buttons_inner + content[inner_end:]
        print(f"Button section: replaced {inner_end - inner_start} bytes")
    else:
        print("Could not find inner button div end!")
else:
    print("Could not find button section end pattern!")

# ================================================================
# 5. UPDATE JS MAP FUNCTION
# ================================================================

old_map = 'var map=[0,1,2,3,4,5,5];'
new_map = 'var map=[0,1,2,3,4,5,6,7,8,9,10];'
if old_map in content:
    content = content.replace(old_map, new_map)
    print("Updated JS map function")
else:
    print(f"⚠️ Could not find old map: '{old_map}'")
    # Try finding alternative
    for m in re.finditer(r'var map=\[', content):
        print(f"  Found alternative at {m.start()}: ...{content[m.start():m.start()+50]}...")

# ================================================================
# 6. UPDATE section heading
# ================================================================

content = content.replace(
    '从放行到着陆，全阶段完整话术模板、标准示范与深度运行解析',
    '从放行到脱离，11个阶段的完整话术模板、标准示范与深度运行解析'
)

# ================================================================
# 7. VERIFY
# ================================================================

# Count atcData items
atc_match = re.search(r'const atcData=\[([\s\S]*?)\];', content, re.DOTALL)
atc_count = 0 if not atc_match else atc_match.group(1).count("phaseGroup:'")
print(f"\natcData items: {atc_count}")

# Count FLIGHT_PHASES items
fp_match = re.search(r'const FLIGHT_PHASES=\[([\s\S]*?)\];', content, re.DOTALL)
fp_count = 0 if not fp_match else fp_match.group(1).count('name:"')
print(f"FLIGHT_PHASES items: {fp_count}")

# Count buttons
btns = len(re.findall(r'<button[^>]*class="phase-btn', content))
print(f"Phase buttons in HTML: {btns}")

# Check map
if 'var map=[0,1,2,3,4,5,6,7,8,9,10]' in content:
    print("✅ Map function updated correctly")
else:
    print("⚠️ Map function may need verification")

# Check all data structures
print(f"\nFile size: {len(content)} chars")
print(f"Has DOCTYPE: {'<!DOCTYPE html>' in content}")
print(f"Has </html>: {'</html>' in content}")

# Save
with open('易错知识（毛玻璃效果）_副本.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("\n✅ File saved!")

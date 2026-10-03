/* The Signature Computer Chip Maker and Archive — deterministic chip engine.
   Same family + seed -> same design forever. Runs in node and browser. */
"use strict";
(function(root){
function xmur3(str){var h=1779033703^str.length;for(var i=0;i<str.length;i++){h=Math.imul(h^str.charCodeAt(i),3432918353);h=h<<13|h>>>19;}return function(){h=Math.imul(h^(h>>>16),2246822507);h=Math.imul(h^(h>>>13),3266489909);return (h^=h>>>16)>>>0;};}
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function RNG(key){var s=xmur3(String(key))();return mulberry32(s);}
function pick(r,arr){return arr[Math.floor(r()*arr.length)];}
function ri(r,a,b){return a+Math.floor(r()*(b-a+1));}
function rf(r,a,b,d){var v=a+r()*(b-a);return d==null?v:+v.toFixed(d);}
function fmt(n){return n.toLocaleString("en-US");}

var PRE=["Volt","Helix","Nova","Flux","Tera","Pulse","Zenith","Axiom","Cobalt","Drift","Ember","Ferro","Ion","Lumen","Onyx","Kryo","Grav","Jolt","Nexus","Prism","Quanta","Ridge","Slate","Torque","Umbra","Vex","Weld","Xen","Yield","Zephyr"];
var MID=["Core","Forge","Mesh","Grid","Weave","Stack","Array","Engine","Matrix","Node","Circuit","Signal","Vector","Spark","Alloy"];
var SUF=["X1","X4","M7","S9","P2","Q5","R3","T8","V6","Z2","A1","B5","C3","D9","E4"];

/* Family definitions: label, unit noun, node per era, ranges. All Signature-original. */
var FAMS={
CPU:{label:"Signature CPU",unit:"cores",desc:"General-purpose central processor for computers, servers and embedded controllers.",nodes:{Historic:["180nm","130nm","90nm","65nm","45nm"],Modern:["32nm","22nm","14nm","10nm","7nm","5nm"],Projected:["3nm","2nm","1.4nm","1nm","sub-nm"]},tr:[5e7,3e10],die:[40,600],pins:[256,4096],tdp:[4,280],clk:[0.5,6.2],units:[2,128]},
GPU:{label:"Signature GPU",unit:"shader cores",desc:"Parallel graphics and compute processor for rendering, simulation and AI training.",nodes:{Historic:["180nm","130nm","90nm","65nm","55nm"],Modern:["28nm","16nm","12nm","8nm","7nm","5nm"],Projected:["4nm","3nm","2nm","1.4nm"]},tr:[1e8,8e10],die:[120,900],pins:[512,4096],tdp:[25,600],clk:[0.4,3.4],units:[128,18432]},
NPU:{label:"Signature NPU AI Accelerator",unit:"TOPS",desc:"Neural-network accelerator for on-device AI inference and training.",nodes:{Historic:["90nm","65nm","45nm"],Modern:["28nm","16nm","12nm","7nm","5nm"],Projected:["3nm","2nm","1.4nm"]},tr:[5e8,5e10],die:[60,700],pins:[256,2048],tdp:[2,400],clk:[0.5,2.8],units:[4,512]},
SOC:{label:"Signature SoC",unit:"integrated blocks",desc:"Complete system-on-chip: CPU, GPU, NPU, memory and I/O on one die.",nodes:{Historic:["130nm","90nm","65nm","45nm"],Modern:["28nm","16nm","10nm","7nm","5nm","4nm"],Projected:["3nm","2nm","1.4nm","1nm"]},tr:[2e8,4e10],die:[50,500],pins:[256,2048],tdp:[1,120],clk:[0.8,4.2],units:[6,48]},
MCU:{label:"Signature Microcontroller",unit:"peripherals",desc:"Tiny control chip for appliances, sensors, toys and industrial gear.",nodes:{Historic:["350nm","250nm","180nm","130nm"],Modern:["90nm","65nm","55nm","40nm"],Projected:["28nm","22nm","16nm"]},tr:[1e5,5e7],die:[4,80],pins:[8,256],tdp:[0.01,5],clk:[0.004,0.6],units:[4,32]},
FPGA:{label:"Signature FPGA",unit:"logic cells",desc:"Field-programmable gate array: logic you rewire in software after manufacture.",nodes:{Historic:["180nm","130nm","90nm","65nm"],Modern:["40nm","28nm","20nm","16nm"],Projected:["10nm","7nm","5nm"]},tr:[1e6,4e10],die:[20,600],pins:[64,2048],tdp:[1,150],clk:[0.1,1.2],units:[1000,9000000]},
MEMC:{label:"Signature Memory Controller",unit:"channels",desc:"High-bandwidth memory controller bridging processors to DRAM and stacked memory.",nodes:{Historic:["180nm","130nm","90nm"],Modern:["65nm","40nm","28nm","16nm"],Projected:["10nm","7nm"]},tr:[1e7,2e9],die:[20,200],pins:[128,2048],tdp:[2,60],clk:[0.4,3.2],units:[1,16]},
SENSOR:{label:"Signature Sensor Chip",unit:"sensor pixels",desc:"Image, motion, environmental and biometric sensing with on-chip processing.",nodes:{Historic:["350nm","250nm","180nm"],Modern:["130nm","90nm","65nm","45nm"],Projected:["28nm","22nm"]},tr:[1e6,8e8],die:[9,150],pins:[16,512],tdp:[0.05,8],clk:[0.01,1.0],units:[1000,200000000]},
PMIC:{label:"Signature Power Management IC",unit:"power rails",desc:"Voltage regulation, battery charging and power sequencing for whole boards.",nodes:{Historic:["500nm","350nm","250nm"],Modern:["180nm","130nm","90nm","65nm"],Projected:["55nm","40nm"]},tr:[1e5,5e7],die:[4,60],pins:[8,256],tdp:[0.1,40],clk:[0.001,0.05],units:[2,24]},
QCTRL:{label:"Signature Quantum Control Chip",unit:"qubit channels",desc:"Cryogenic control and readout electronics for quantum processors.",nodes:{Historic:["250nm","180nm"],Modern:["90nm","65nm","40nm","28nm"],Projected:["22nm","16nm","14nm"]},tr:[1e6,5e8],die:[10,120],pins:[64,1024],tdp:[0.05,15],clk:[0.1,6.0],units:[4,1024]},
PHOT:{label:"Signature Photonic Chip",unit:"optical lanes",desc:"Light-based interconnect and compute using on-chip lasers and waveguides.",nodes:{Historic:["250nm","180nm","130nm"],Modern:["90nm","65nm","45nm"],Projected:["32nm","22nm"]},tr:[1e6,1e9],die:[15,200],pins:[32,1024],tdp:[1,80],clk:[1.0,100.0],units:[4,256]},
NEURO:{label:"Signature Neuromorphic Chip",unit:"artificial neurons",desc:"Brain-inspired spiking-neural processor for ultra-low-power cognition.",nodes:{Historic:["180nm","130nm"],Modern:["90nm","65nm","45nm","28nm"],Projected:["16nm","10nm","7nm"]},tr:[1e7,2e10],die:[20,400],pins:[64,1024],tdp:[0.05,50],clk:[0.01,1.5],units:[1000,8000000]},
DSP:{label:"Signature DSP",unit:"MAC units",desc:"Digital signal processor for audio, radio, radar and motor control math.",nodes:{Historic:["250nm","180nm","130nm","90nm"],Modern:["65nm","45nm","40nm","28nm"],Projected:["16nm","12nm"]},tr:[1e6,3e9],die:[10,150],pins:[48,1024],tdp:[0.2,45],clk:[0.1,2.5],units:[2,512]},
MODEM:{label:"Signature Baseband Modem",unit:"radio chains",desc:"Cellular, Wi-Fi and satellite baseband with on-chip RF control.",nodes:{Historic:["180nm","130nm","90nm"],Modern:["65nm","45nm","28nm","16nm"],Projected:["10nm","7nm"]},tr:[5e7,1.5e10],die:[25,250],pins:[128,1024],tdp:[0.5,25],clk:[0.3,4.0],units:[1,16]},
SEC:{label:"Signature Security Enclave",unit:"crypto engines",desc:"Hardware root of trust: secure boot, encryption and key vault on isolated silicon.",nodes:{Historic:["180nm","130nm","90nm"],Modern:["65nm","40nm","28nm","22nm"],Projected:["16nm","12nm"]},tr:[1e7,4e9],die:[8,120],pins:[32,512],tdp:[0.1,20],clk:[0.1,2.0],units:[1,32]},
CHIPLET:{label:"Signature Chiplet Interconnect",unit:"die links",desc:"High-speed die-to-die fabric stitching chiplets into one package.",nodes:{Historic:["130nm","90nm","65nm"],Modern:["45nm","32nm","28nm","16nm"],Projected:["10nm","7nm"]},tr:[5e7,8e9],die:[30,300],pins:[256,4096],tdp:[2,90],clk:[0.5,8.0],units:[2,64]}
};
var FAMKEYS=Object.keys(FAMS);
/* Consistency pass: engine version stamped on every rendered record's provenance line. */
var ENGVER="1.0";

var SUBSTRATES=["monocrystalline silicon","silicon-on-insulator","gallium nitride on silicon","silicon carbide","strained silicon germanium"];
var METALS=["copper dual-damascene interconnect","cobalt-capped copper","ruthenium liners","tungsten vias"];
var DIEL=["low-k organosilicate glass","silicon carbonitride caps","air-gap isolation (projected nodes)"];
var PKGS=["SIG-BGA","SIG-LGA","SIG-QFN","SIG-WLCSP","SIG-EMIB-2.5D","SIG-CoWoS-3D"];
/* GEMINI #20 FIXES: per-design electrical, interface and status data (deterministic, seeded). */
var VOLTS={Historic:["5.0 V","3.3 V","2.5 V","1.8 V"],Modern:["1.2 V","1.0 V","0.9 V","0.8 V"],Projected:["0.75 V","0.7 V","0.65 V","0.6 V"]};
var IOSETS={
CPU:["PCIe 5.0 x16","DDR5-5600 x2","USB4","2x 10GbE","SPI flash","JTAG","64x GPIO"],
GPU:["PCIe 5.0 x16","HBM3 x4","DisplayPort 2.1 x4","NVLink-class die link","JTAG"],
NPU:["PCIe 4.0 x8","LPDDR5X","MIPI CSI-2 x4","I2C control","JTAG"],
SOC:["PCIe 4.0 x4","LPDDR5","USB 3.2 x2","MIPI DSI/CSI","Wi-Fi/BT radio IF","40x GPIO"],
MCU:["SPI","I2C x2","UART x3","CAN-FD","12-bit ADC x16","32x GPIO","SWD debug"],
FPGA:["PCIe 4.0 x8","DDR4 x2","QSFP28 x4","JTAG","user I/O bank x240"],
MEMC:["DDR5-6400 x4","HBM3 x2","CXL 2.0","JTAG"],
SENSOR:["MIPI CSI-2 x4","I2C","SPI","parallel pixel bus"],
PMIC:["PMBus","I2C","power-good outputs","enable inputs"],
QCTRL:["cryo microwave lines","baseband AWG IF","SPI readout","room-temp JTAG"],
PHOT:["optical fiber array x8","PCIe 4.0 x8","I2C","JTAG"],
NEURO:["AER event bus","SPI","I2C","32x GPIO"],
DSP:["I2S x4","TDM audio","SPI","McASP","JTAG"],
MODEM:["RF front-end IF","PCIe 3.0 x2","USB 2.0","SIM IF","I2C"],
SEC:["SPI slave","I2C","secure JTAG (fused)","tamper pins"],
CHIPLET:["UCIe die-to-die x8","PCIe 5.0 x16","sideband I2C","JTAG"]};
var PROCASSUMP={
Historic:["Standard-cell library assumed at this node; single-patterning lithography; aluminum/copper backend per era norms. No low-k dielectric modeled."],
Modern:["Standard-cell library assumed; multi-patterning where the node requires it; low-k dielectric modeled. Assumes a commercial foundry logic process of this class — no fab-specific PDK data used."],
Projected:["Projected-node design: assumes future lithography capability; all dimensions are targets, not measured silicon. Backside power delivery and stacked-FET assumptions are projections, not verified process data."]};
var FABREMAIN=["Physical verification (DRC/LVS) against a real foundry PDK","Timing closure and sign-off static timing analysis","Tape-out database (GDSII/OASIS) generation","Silicon bring-up and electrical characterization","Foundry qualification and yield ramp"];

function chipName(idx){var g=Math.floor(idx/6750);return "Signature "+PRE[idx%30]+MID[Math.floor(idx/30)%15]+" "+SUF[Math.floor(idx/450)%15]+(g>0?" G"+g:"");}

function renderChip(row){
  var r=RNG("chip:"+row.id+":"+row.seed);
  var F=FAMS[row.fam];
  var era=row.era;
  var node=pick(r,F.nodes[era]);
  var tr=Math.round(Math.exp(Math.log(F.tr[0])+r()*(Math.log(F.tr[1])-Math.log(F.tr[0]))));
  var die=rf(r,F.die[0],F.die[1],1);
  var pins=ri(r,F.pins[0],F.pins[1]);
  var tdp=rf(r,F.tdp[0],F.tdp[1],tdpDec(F.tdp));
  var clk=rf(r,F.clk[0],F.clk[1],2);
  var units=ri(r,F.units[0],Math.min(F.units[1],F.units[0]+Math.floor(r()*Math.min(F.units[1],64))+ (F.units[1]>1000?Math.floor(r()*F.units[1]*0.2):0)));
  var pkg=pick(r,PKGS);
  var sub=pick(r,SUBSTRATES), metal=pick(r,METALS), diel=pick(r,DIEL);
  var isa="Signature ISA v"+ri(r,1,9)+"."+ri(r,0,9)+" (original Signature instruction set)";
  var sigpart="SIG-CHIP-"+String(1000+Math.floor(r()*9000));
  var blocks=makeBlocks(r,row.fam,clk,tdp,pins);
  var arch=archText(row,F,era,node,tr,die,clk,units,tdp);
  var mfg=mfgText(row,era,node,pkg,sub,metal,diel);
  /* GEMINI #20 FIXES: electrical + interface + honesty fields (all deterministic). */
  var volt=pick(r,VOLTS[era]);
  var pkgSide=Math.round((Math.sqrt(die)*1.7+pins/160)*10)/10;
  var pkgDims=pkgSide.toFixed(1)+" x "+pkgSide.toFixed(1)+" x "+pick(r,["1.2","1.7","2.1","2.6"])+" mm";
  var ioPool=IOSETS[row.fam]||IOSETS.CPU,io=[],qi;
  for(qi=0;qi<ioPool.length;qi++){if(r()<0.62)io.push(ioPool[qi]);}
  if(io.length<3)io=ioPool.slice(0,3);
  var procAssump=pick(r,PROCASSUMP[era]);
  var thermAssump=row.fam==="QCTRL"?"Operates at approx 4 K inside a cryostat; room-temperature control assumed at the vacuum feedthrough.":"Junction temperature <= 105 C assumed; heat spreader required above "+Math.round(tdp)+" W; characterized in 25 C still air.";
  var designOrigin=era==="Historic"?"HISTORIC-CLASS RE-IMAGINING - a Signature-original tribute to a historic chip class. It is NOT the real historical part and carries no real part number.":"SIGNATURE ORIGINAL - an original Signature-line design. No real manufacturer's branding, part numbers, or datasheet text are used.";
  var designStatus="CONCEPTUAL DESIGN - architecture study, NOT fabrication-ready.";
  return {id:row.id,fam:row.fam,era:era,name:row.name,sigpart:sigpart,label:F.label,unit:F.unit,famdesc:F.desc,
    node:node,transistors:tr,die:die,pins:pins,tdp:tdp,clk:clk,units:units,pkg:pkg,sub:sub,metal:metal,diel:diel,
    isa:isa,arch:arch,mfg:mfg,blocks:blocks,
    voltage:volt,pkgDims:pkgDims,io:io,procAssump:procAssump,thermAssump:thermAssump,
    designOrigin:designOrigin,designStatus:designStatus,fabRemain:FABREMAIN,seed:row.seed,engineVer:ENGVER,
    lineage:"Signature-line original design drafted by the Signature System. Every Signature chip is an original work: no real manufacturer's branding, part numbers, or datasheet text are used anywhere in this archive."};
}
function tdpDec(range){return range[1]<10?2:range[1]<100?1:0;}
function archText(row,F,era,node,tr,die,clk,units,tdp){
  var e=era==="Historic"?"a historic-class design in the Signature archive, re-imagined with modern design discipline":era==="Modern"?"a current-generation Signature design":"a projected future Signature design, drafted ahead of its manufacturing node";
  return "The "+row.name+" is "+e+". It implements the "+F.label.toLowerCase()+" class: "+F.desc.toLowerCase()+" Fabricated on a "+node+" process, it integrates "+fmt(tr)+" transistors on a "+die+" mm² die, delivering "+fmt(units)+" "+F.unit+" at up to "+clk+" GHz within a "+tdp+" W envelope. The on-chip interconnect, clock tree, and power delivery were co-designed so the part scales from handheld to datacenter boards without redesign.";
}
function mfgText(row,era,node,pkg,sub,metal,diel){
  return "Manufacturing notes: "+sub+" substrate; "+metal+" interconnect with "+diel+" dielectric; "+node+" lithography with multi-patterning where the node requires it; assembled in a "+pkg+" package with underfill and a nickel-plated copper heat spreader. Binning sorts parts into three speed grades; every lot passes burn-in, scan-chain, and memory-BIST before the Signature stamp is applied.";
}
function makeBlocks(r,fam,clk,tdp,pins){
  var B=[
   ["Core Compute Array","The main execution engines of the die. Datapaths, schedulers and register files live here; this block sets the chip's headline performance."],
   ["Power Regulation","On-die voltage regulators and power gates. Delivers clean power per block and shuts idle regions down to near zero."],
   ["Memory Interface","Controllers and PHYs talking to external DRAM or stacked memory. Sets the chip's memory bandwidth ceiling."],
   ["I/O Cluster","High-speed serial links, general-purpose pins and board-level interfaces for everything off-chip."],
   ["Clock & Timing Tree","PLL/DLL clock synthesis and balanced distribution so every block ticks in sync at up to "+clk+" GHz."],
   ["Thermal Dissipation Plane","Copper pours, thermal vias and sensor diodes that move "+tdp+" W of heat out to the spreader."],
   ["Security Enclave","Isolated root of trust: secure boot, key storage and crypto accelerators, fenced from the main cores."],
   ["Debug & Test Port","Boundary scan, trace and bring-up interfaces used in the factory and the lab."]
  ];
  var famTweak={GPU:["Shader Array","Thousands of parallel shader lanes with texture units and ray-tracing blocks."],
    NPU:["Neural Engine Mesh","Systolic arrays of multiply-accumulate units tuned for matrix math."],
    MCU:["Peripheral Set","Timers, ADCs, serial ports and GPIO for talking to the physical world."],
    SENSOR:["Pixel / Sense Array","The sensing elements themselves, with per-site amplifiers and digitizers."],
    PMIC:["Regulator Bank","Buck, boost and LDO regulators sequencing every rail on the board."],
    QCTRL:["Qubit Control Fabric","Microwave pulse generators and readout chains for qubit control."],
    FPGA:["Programmable Fabric","Lookup tables and switch matrices the user rewires in software."],
    PHOT:["Photonic Lane Array","On-chip lasers, modulators and waveguides carrying data as light."],
    NEURO:["Neuron Core Field","Spiking neuron cores with local synaptic memory."],
    SOC:["Heterogeneous Tile Set","CPU, GPU, NPU and I/O tiles sharing one memory system."]};
  if(famTweak[fam]) B[0]=famTweak[fam];
  return B.map(function(b,i){return {n:"S"+(i+1),name:b[0],desc:b[1]};});
}

/* ---- SVG circuit board, theme-matched (navy + copper) ---- */
function boardSVG(chip){
  var r=RNG("board:"+chip.id);
  var W=820,H=560;
  var secs=[
    {x:30,y:30,w:170,h:86},{x:620,y:30,w:170,h:86},
    {x:30,y:446,w:170,h:86},{x:620,y:446,w:170,h:86},
    {x:30,y:220,w:130,h:120},{x:660,y:220,w:130,h:120},
    {x:300,y:30,w:220,h:64},{x:300,y:466,w:220,h:64}
  ];
  var cx=410,cy=280,pw=200,ph=150;
  var s='<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Circuit board layout for '+chip.name+'">';
  s+='<defs><pattern id="cu" width="14" height="14" patternUnits="userSpaceOnUse"><path d="M0 14L14 0" stroke="#1d3a5f" stroke-width="1"/></pattern></defs>';
  s+='<rect x="8" y="8" width="'+(W-16)+'" height="'+(H-16)+'" rx="18" fill="#0d2036" stroke="#d08a3e" stroke-width="3"/>';
  s+='<rect x="8" y="8" width="'+(W-16)+'" height="'+(H-16)+'" rx="18" fill="url(#cu)" opacity="0.5"/>';
  // mounting holes
  [[36,36],[W-36,36],[36,H-36],[W-36,H-36]].forEach(function(p){s+='<circle cx="'+p[0]+'" cy="'+p[1]+'" r="10" fill="#081426" stroke="#d08a3e" stroke-width="2"/>';});
  // section pads + traces
  chip.blocks.forEach(function(b,i){
    var g=secs[i]; var gx=g.x+g.w/2, gy=g.y+g.h/2;
    var ex=cx+(gx<cx?-pw/2:pw/2), ey=cy+(gy<cy?-ph/2:ph/2)+(i%3-1)*24;
    var mx=(gx+ex)/2;
    s+='<path d="M'+gx+' '+gy+' L'+mx+' '+gy+' L'+mx+' '+ey+' L'+ex+' '+ey+'" fill="none" stroke="#d08a3e" stroke-width="3"/>';
    s+='<circle cx="'+ex+'" cy="'+ey+'" r="5" fill="#e8b34b"/>';
    s+='<rect x="'+g.x+'" y="'+g.y+'" width="'+g.w+'" height="'+g.h+'" rx="8" fill="#12294a" stroke="#4fd8e8" stroke-width="2"/>';
    s+='<text x="'+(g.x+10)+'" y="'+(g.y+24)+'" fill="#e8b34b" font-size="15" font-family="monospace" font-weight="bold">'+b.n+'</text>';
    var nm=b.name.length>20?b.name.slice(0,19)+"…":b.name;
    s+='<text x="'+(g.x+10)+'" y="'+(g.y+46)+'" fill="#cfe8ff" font-size="12.5" font-family="monospace">'+esc(nm)+'</text>';
    // little components in pad
    for(var k=0;k<4;k++){s+='<rect x="'+(g.x+12+k*26)+'" y="'+(g.y+g.h-26)+'" width="18" height="12" rx="2" fill="#0a1628" stroke="#d08a3e" stroke-width="1.2"/>';}
  });
  // central package
  s+='<rect x="'+(cx-pw/2)+'" y="'+(cy-ph/2)+'" width="'+pw+'" height="'+ph+'" rx="10" fill="#1a2f4d" stroke="#e8b34b" stroke-width="3"/>';
  for(var p=0;p<10;p++){var px=cx-pw/2+14+p*((pw-28)/9);s+='<rect x="'+(px-4)+'" y="'+(cy-ph/2-12)+'" width="8" height="12" fill="#c9a227"/>';s+='<rect x="'+(px-4)+'" y="'+(cy+ph/2)+'" width="8" height="12" fill="#c9a227"/>';}
  s+='<rect x="'+(cx-70)+'" y="'+(cy-40)+'" width="140" height="80" rx="6" fill="#0a1628" stroke="#4fd8e8" stroke-width="2"/>';
  s+='<text x="'+cx+'" y="'+(cy-12)+'" text-anchor="middle" fill="#e8b34b" font-size="14" font-family="monospace" font-weight="bold">'+esc(chip.sigpart)+'</text>';
  s+='<text x="'+cx+'" y="'+(cy+10)+'" text-anchor="middle" fill="#cfe8ff" font-size="11" font-family="monospace">'+esc(chip.node)+' · '+fmt(chip.transistors)+' T</text>';
  s+='<circle cx="'+(cx-pw/2+16)+'" cy="'+(cy-ph/2+16)+'" r="4" fill="#e8b34b"/>';
  s+='<text x="'+(cx-pw/2+10)+'" y="'+(cy+ph/2-10)+'" fill="#7fa8c9" font-size="10" font-family="monospace">'+esc(chip.id)+'</text>';
  s+='</svg>';
  return s;
}
function esc(t){return String(t).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}

/* ---- Canonical machine-readable record (JAH-CHIP-RECORD/1.0) ----
   Every numeric value carries an explicit unit and a value-kind.
   ALL values are GENERATED_TARGET: deterministically generated design
   targets from the design seed. None are measured, simulated,
   manufactured, or tested. Statuses are explicit, never blank. */
var RECORD_SCHEMA="JAH-CHIP-RECORD/1.0";
function canonicalRecord(row){
  var c=renderChip(row);
  var rp=RNG("pins:"+row.id+":"+row.seed);
  var pins=c.pins;
  var gnd=Math.max(4,Math.round(pins*0.15)), pwr=Math.max(2,Math.round(pins*0.12)),
      clk=Math.max(2,Math.round(pins*0.02)), rsv=Math.floor(rp()*8);
  var sig=pins-gnd-pwr-clk-rsv;
  var pinGroups=[
    {group:"PWR", purpose:"power delivery", count:pwr, voltage_domain:c.voltage, direction:"in"},
    {group:"GND", purpose:"ground return", count:gnd, voltage_domain:"0 V", direction:"in"},
    {group:"CLK", purpose:"clock distribution", count:clk, voltage_domain:c.voltage, direction:"in/out"},
    {group:"SIG", purpose:"signal I/O", count:sig, voltage_domain:"1.8/3.3 V I/O", direction:"in/out"},
    {group:"RSV", purpose:"reserved / no-connect", count:rsv, voltage_domain:"n/a", direction:"n/a"}
  ];
  var specs=[
    {key:"transistors", label:"Transistor count", value:c.transistors, unit:"count", kind:"GENERATED_TARGET"},
    {key:"die_area", label:"Die area", value:c.die, unit:"mm²", kind:"GENERATED_TARGET"},
    {key:"clock", label:"Clock", value:c.clk, unit:"GHz", kind:"GENERATED_TARGET"},
    {key:"tdp", label:"Power envelope (TDP)", value:c.tdp, unit:"W", kind:"GENERATED_TARGET"},
    {key:"pins", label:"Pin count", value:c.pins, unit:"count", kind:"GENERATED_TARGET"},
    {key:"core_voltage", label:"Core voltage", value:parseFloat(c.voltage), unit:"V", kind:"GENERATED_TARGET"},
    {key:"process_node", label:"Process node class", value:c.node, unit:"nm-class", kind:"GENERATED_TARGET"},
    {key:"functional_units", label:"Functional units ("+c.unit+")", value:c.units, unit:"count", kind:"GENERATED_TARGET"},
    {key:"package_dims", label:"Package dimensions", value:c.pkgDims, unit:"mm", kind:"GENERATED_TARGET"}
  ];
  c.record_schema=RECORD_SCHEMA;
  c.record_version="1.0";
  c.canonical_url="https://justinahiggins614-cmyk.github.io/signature-chip-maker/?chip="+c.id;
  c.creation_mode="SIGNATURE-GENERATED";
  c.value_kind="GENERATED_TARGET";
  c.design_status="CONCEPT";
  c.sim_status="NOT_SIMULATED";
  c.test_status="NOT_TESTED";
  c.mfg_status="NOT_MANUFACTURED";
  c.completeness_status="CONCEPT";
  c.specs=specs;
  c.pin_groups=pinGroups;
  c.pin_map_note="Functional pin-group map generated from the pin count — NOT a fabrication pinout. Per-pin netlists do not exist for conceptual designs.";
  c.diagram={kind:"GENERATED_BLOCK_DIAGRAM", version:ENGVER, synced_with:"blocks[]",
    note:"Deterministic board illustration generated from the same block data as the spec table. It is a block diagram, not a schematic and not a fabrication drawing."};
  c.parent_chip_id=null;
  c.derived_from=null;
  c.lineage_note="Standalone Signature-original design. No parent chip; no real manufacturer's part is referenced.";
  return c;
}

root.ChipEngine={FAMS:FAMKEYS,FAMDEF:FAMS,renderChip:renderChip,canonicalRecord:canonicalRecord,boardSVG:boardSVG,chipName:chipName,esc:esc,RNG:RNG,fmt:fmt,version:ENGVER,recordSchema:RECORD_SCHEMA};
})(typeof window!=="undefined"?window:(typeof module!=="undefined"?module.exports:{}));

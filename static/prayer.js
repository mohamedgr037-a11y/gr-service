const PN=["Fajr","Dhuhr","Asr","Maghrib","Isha"];
const PA={Fajr:"الفجر",Dhuhr:"الظهر",Asr:"العصر",Maghrib:"المغرب",Isha:"العشاء"};
let ptimes=null,ptimers=[];
if("serviceWorker" in navigator)navigator.serviceWorker.register("/sw.js").catch(()=>{});
async function notify(t,b){
try{const r=await navigator.serviceWorker.getRegistration();if(r){await r.showNotification(t,{body:b,vibrate:[300,150,300]});return}}catch(e){}
try{new Notification(t,{body:b})}catch(e){}}
function pname(n){return lang=="ar"?PA[n]:n}
function schedule(){
ptimers.forEach(clearTimeout);ptimers=[];if(!ptimes)return;
const bf=+$("pb").value,now=Date.now(),ar=lang=="ar";
PN.forEach(n=>{
const hm=ptimes[n].split(":"),d=new Date();d.setHours(+hm[0],+hm[1],0,0);const t=d.getTime();
if(bf>0&&t-bf*60000>now)ptimers.push(setTimeout(()=>notify("🕌 "+pname(n),ar?"بعد "+bf+" دقيقة":"Dans "+bf+" min"),t-bf*60000-now));
if(t>now)ptimers.push(setTimeout(()=>notify("🕌 "+pname(n),ar?"حان الآن وقت الصلاة":"C'est l'heure de la prière"),t-now));
})}
function drawPrayer(){
if(!ptimes)return;const now=new Date();let nx=null;
PN.forEach(n=>{const hm=ptimes[n].split(":"),d=new Date();d.setHours(+hm[0],+hm[1],0,0);if(!nx&&d>now)nx=n});
let h="";PN.forEach(n=>{h+='<div class="prow'+(n==nx?" nx":"")+'"><span>'+pname(n)+'</span><span>'+ptimes[n]+'</span></div>'});
$("pout").innerHTML=h}
async function prayer(){
const c=$("pc").value.trim(),r=$("pr").value.trim();if(!c||!r)return;
$("pout").textContent="⏳ ...";
try{
const j=await (await fetch("https://api.aladhan.com/v1/timingsByCity?method=3&city="+encodeURIComponent(r)+"&country="+encodeURIComponent(c))).json();
if(!j.data||!j.data.timings){$("pout").textContent="❌ Introuvable / غير موجود";return}
ptimes={};PN.forEach(n=>ptimes[n]=j.data.timings[n].slice(0,5));
localStorage.setItem("pcity",JSON.stringify({c:c,r:r}));
drawPrayer();schedule();
}catch(e){$("pout").textContent=tr("err")}}
$("pgo").onclick=prayer;$("pb").onchange=schedule;
$("pn").onclick=async()=>{
try{const p=await Notification.requestPermission();
if(p=="granted"){notify("🕌 G-R Service","✅ OK");schedule()}else alert("Notifications refusées / تم رفض الإشعارات")}catch(e){alert("Non supporté / غير مدعوم")}};
try{const sc=JSON.parse(localStorage.getItem("pcity")||"null");if(sc){$("pc").value=sc.c;$("pr").value=sc.r;prayer()}}catch(e){}

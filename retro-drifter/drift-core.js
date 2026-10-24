/* Retro Drift deterministic vehicle core. No DOM/rendering/browser APIs. */
export const DEFAULT_TUNING=Object.freeze({
 driftTriggerThrottle:.20,driftTriggerBrake:.20,driftTimeScale:.36,driftMaxHeadingRadians:Math.PI*.995,
 driftYawRate:1.90,driftSteerResponse:5.8,driftYawDamping:2.0,driftVelocityFollow:1.65,driftExitCatch:.62,
 normalYawRate:1.85,normalSteerResponse:6.2,normalYawDamping:6.0,normalVelocityFollow:11.5,
 normalTurnLow:.58,normalTurnMid:1.65,normalHighSpeedCut:.25,normalSteerExponent:1.35,lowSpeedYawBoost:1.0,
 acceleration:285,boostAcceleration:520,boostThreshold:.82,brakeDeceleration:250,rollingDrag:.022,
 driftDrive:170,driftDrag:24,minSpeed:0,maxSpeed:320,minDriftSpeed:5,worldSpeedScale:.22,
 pitchResponse:8.6,rollResponse:8.8,rolloverSpeed:175,rolloverBrake:.86,rolloverSteer:.78,rolloverImpulse:5.3,flipDuration:1.15
});
export function createVehicleState(o={}){return{x:0,z:0,bodyYaw:0,velocityYaw:0,yawRate:0,speed:12,drifting:false,driftBaseYaw:0,driftBaseSteer:0,driftEntrySpeed:0,pitch:0,roll:0,height:0,rollVelocity:0,pitchVelocity:0,flipping:false,flipTime:0,...o}}
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function angleDelta(a,b){let d=(a-b+Math.PI)%(Math.PI*2);if(d<0)d+=Math.PI*2;return d-Math.PI}
function approachAngle(a,b,k){return a+angleDelta(b,a)*clamp(k,0,1)}
function normalYawTarget(speed,steer,t){
 const low=clamp(speed/90,0,1),high=clamp((speed-160)/160,0,1),m=Math.abs(steer);
 const shaped=Math.sign(steer)*Math.pow(m,t.normalSteerExponent??1);
 const rate=(t.normalTurnLow+(t.normalTurnMid-t.normalTurnLow)*low)*(1-t.normalHighSpeedCut*high);
 return shaped*rate;
}
export function stepVehicle(s,input,realDt,t=DEFAULT_TUNING){
 const dt=clamp(realDt,0,.04),throttle=clamp(input.throttle??0,0,1),steer=clamp(input.steer??0,-1,1),brake=clamp(input.brake??0,0,1);
 if(!Number.isFinite(s.yawRate))s.yawRate=0;
 const driftCommand=!!input.handbrake||(brake>t.driftTriggerBrake&&throttle>t.driftTriggerThrottle);
 if(s.flipping){
  s.flipTime+=dt;s.roll+=s.rollVelocity*dt;s.pitch+=s.pitchVelocity*dt;s.height=Math.max(0,Math.sin(Math.min(1,s.flipTime/t.flipDuration)*Math.PI)*1.65);
  s.yawRate*=Math.exp(-3.5*dt);s.speed*=Math.pow(.11,dt);s.x+=Math.sin(s.velocityYaw)*s.speed*dt*t.worldSpeedScale;s.z-=Math.cos(s.velocityYaw)*s.speed*dt*t.worldSpeedScale;
  if(s.flipTime>=t.flipDuration){s.flipping=false;s.flipTime=0;s.height=s.roll=s.pitch=s.rollVelocity=s.pitchVelocity=s.yawRate=0;s.speed=Math.min(s.speed,20);s.velocityYaw=s.bodyYaw}return s
 }
 if(driftCommand&&!s.drifting){s.drifting=true;s.driftBaseYaw=s.bodyYaw;s.driftBaseSteer=steer;s.driftEntrySpeed=s.speed}
 else if(!driftCommand&&s.drifting){s.drifting=false;s.velocityYaw=approachAngle(s.velocityYaw,s.bodyYaw,t.driftExitCatch);s.yawRate*=.82}
 const simDt=dt*(s.drifting?t.driftTimeScale:1),before=s.speed;
 if(s.drifting){
  const speedAuthority=.82+.18*clamp(s.speed/100,0,1),targetRate=steer*t.driftYawRate*speedAuthority;
  s.yawRate+=(targetRate-s.yawRate)*clamp(dt*t.driftSteerResponse,0,1);
  if(Math.abs(steer)<.02)s.yawRate*=Math.exp(-t.driftYawDamping*dt);
  s.bodyYaw+=s.yawRate*dt;
  s.velocityYaw=approachAngle(s.velocityYaw,s.bodyYaw,simDt*t.driftVelocityFollow);
  s.speed+=throttle*t.driftDrive*simDt;s.speed-=brake*t.driftDrag*simDt;s.speed=clamp(s.speed,t.minDriftSpeed,t.maxSpeed)
 } else {
  const targetRate=normalYawTarget(s.speed,steer,t);
  s.yawRate+=(targetRate-s.yawRate)*clamp(dt*t.normalSteerResponse,0,1);
  if(Math.abs(steer)<.02)s.yawRate*=Math.exp(-t.normalYawDamping*dt);
  s.bodyYaw+=s.yawRate*simDt;
  s.velocityYaw=approachAngle(s.velocityYaw,s.bodyYaw,simDt*t.normalVelocityFollow);
  const boost=throttle>t.boostThreshold?((throttle-t.boostThreshold)/(1-t.boostThreshold))*t.boostAcceleration:0;
  s.speed+=(throttle*t.acceleration+boost)*simDt;s.speed-=brake*t.brakeDeceleration*simDt;s.speed-=s.speed*t.rollingDrag*simDt;s.speed=clamp(s.speed,t.minSpeed,t.maxSpeed)
 }
 const la=dt>0?(s.speed-before)/dt:0,pt=clamp(-la/520,-.19,.32);s.pitch+=(pt-s.pitch)*clamp(dt*t.pitchResponse,0,1);
 const gap=angleDelta(s.bodyYaw,s.velocityYaw),load=Math.abs(steer)*(s.speed/t.maxSpeed)+Math.abs(gap)*.95,rt=clamp(-steer*load*.38,-.38,.38);s.roll+=(rt-s.roll)*clamp(dt*t.rollResponse,0,1);
 const sev=(s.speed/t.maxSpeed)*Math.max(brake/t.rolloverBrake,0)*Math.max(Math.abs(steer)/t.rolloverSteer,0)*(1+Math.abs(gap)*1.6);if(!s.drifting&&s.speed>t.rolloverSpeed&&brake>t.rolloverBrake&&Math.abs(steer)>t.rolloverSteer&&sev>1){s.flipping=true;s.flipTime=0;s.rollVelocity=-Math.sign(steer||1)*t.rolloverImpulse*clamp(sev,1,1.9);s.pitchVelocity=-1.8-brake*2.5;s.drifting=false}
 s.x+=Math.sin(s.velocityYaw)*s.speed*simDt*t.worldSpeedScale;s.z-=Math.cos(s.velocityYaw)*s.speed*simDt*t.worldSpeedScale;return s
}
export function snapshotVehicle(s){return[s.x,s.z,s.bodyYaw,s.velocityYaw,s.speed,s.drifting?1:0,s.pitch,s.roll,s.flipping?1:0]}

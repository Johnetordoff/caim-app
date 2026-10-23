/* Retro Drift deterministic vehicle core. */
export const DEFAULT_TUNING = Object.freeze({
  driftTriggerThrottle: 0.28,
  driftTimeScale: 0.48,
  driftMaxHeadingRadians: Math.PI * 0.53,
  driftYawResponse: 6.8,
  driftVelocityFollow: 0.46,
  driftExitCatch: 0.42,
  normalYawRate: 1.24,
  normalVelocityFollow: 6.4,
  acceleration: 48,
  brakeDeceleration: 78,
  coastDeceleration: 7.5,
  rollingDrag: 0.065,
  driftDrive: 14,
  driftDrag: 18,
  minSpeed: 0,
  maxSpeed: 70,
  minDriftSpeed: 6,
  worldSpeedScale: 0.17,
});
export function createVehicleState(overrides={}){return{x:0,z:0,bodyYaw:0,velocityYaw:0,speed:10,drifting:false,driftBaseYaw:0,driftBaseSteer:0,driftEntrySpeed:0,...overrides};}
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function angleDelta(a,b){let d=(a-b+Math.PI)%(Math.PI*2);if(d<0)d+=Math.PI*2;return d-Math.PI;}
function approachAngle(a,b,k){return a+angleDelta(b,a)*clamp(k,0,1);}
export function stepVehicle(state,input,realDt,tuning=DEFAULT_TUNING){
 const dt=clamp(realDt,0,0.04),throttle=clamp(input.throttle??0,0,1),steer=clamp(input.steer??0,-1,1),brake=!!input.brake;
 const driftCommand=!!input.handbrake||(brake&&throttle>tuning.driftTriggerThrottle);
 if(driftCommand&&!state.drifting){state.drifting=true;state.driftBaseYaw=state.bodyYaw;state.driftBaseSteer=steer;state.driftEntrySpeed=state.speed;}
 else if(!driftCommand&&state.drifting){state.drifting=false;state.velocityYaw=approachAngle(state.velocityYaw,state.bodyYaw,tuning.driftExitCatch);}
 const simDt=dt*(state.drifting?tuning.driftTimeScale:1);
 if(state.drifting){const request=clamp(steer-state.driftBaseSteer,-1,1),targetYaw=state.driftBaseYaw+request*tuning.driftMaxHeadingRadians;state.bodyYaw=approachAngle(state.bodyYaw,targetYaw,dt*tuning.driftYawResponse);state.velocityYaw=approachAngle(state.velocityYaw,state.bodyYaw,simDt*tuning.driftVelocityFollow);state.speed+=throttle*tuning.driftDrive*simDt-tuning.driftDrag*simDt;state.speed=clamp(state.speed,tuning.minDriftSpeed,Math.max(tuning.minDriftSpeed,state.driftEntrySpeed*1.05));}
 else{const speedFactor=.34+Math.min(1,state.speed/46)*.78;state.bodyYaw+=steer*tuning.normalYawRate*speedFactor*simDt;state.velocityYaw=approachAngle(state.velocityYaw,state.bodyYaw,simDt*tuning.normalVelocityFollow);state.speed+=throttle*tuning.acceleration*simDt;state.speed-=(1-throttle)*tuning.coastDeceleration*simDt;if(brake)state.speed-=tuning.brakeDeceleration*simDt;state.speed-=state.speed*tuning.rollingDrag*simDt;state.speed=clamp(state.speed,tuning.minSpeed,tuning.maxSpeed);}
 state.x+=Math.sin(state.velocityYaw)*state.speed*simDt*tuning.worldSpeedScale;state.z-=Math.cos(state.velocityYaw)*state.speed*simDt*tuning.worldSpeedScale;return state;
}
export function snapshotVehicle(state){return[state.x,state.z,state.bodyYaw,state.velocityYaw,state.speed,state.drifting?1:0];}

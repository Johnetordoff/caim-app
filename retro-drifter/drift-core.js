/* Retro Drift deterministic vehicle core.
 * No DOM, rendering, timers, or browser APIs.
 */
export const DEFAULT_TUNING = Object.freeze({
  driftTriggerThrottle: 0.24,
  driftTriggerBrake: 0.24,
  driftTimeScale: 0.48,
  driftMaxHeadingRadians: Math.PI * 0.53,
  driftYawResponse: 6.8,
  driftVelocityFollow: 0.42,
  driftExitCatch: 0.48,
  normalYawRate: 1.08,
  normalVelocityFollow: 10.5,
  acceleration: 54,
  brakeDeceleration: 125,
  rollingDrag: 0.05,
  driftDrive: 16,
  driftDrag: 20,
  minSpeed: 0,
  maxSpeed: 72,
  minDriftSpeed: 4,
  worldSpeedScale: 0.17,
  pitchResponse: 7.5,
  rollResponse: 8.0,
  rolloverSpeed: 34,
  rolloverBrake: 0.68,
  rolloverSteer: 0.48,
  rolloverImpulse: 4.8,
  flipDuration: 1.25,
});
export function createVehicleState(overrides={}){return{x:0,z:0,bodyYaw:0,velocityYaw:0,speed:10,drifting:false,driftBaseYaw:0,driftBaseSteer:0,driftEntrySpeed:0,pitch:0,roll:0,height:0,rollVelocity:0,pitchVelocity:0,flipping:false,flipTime:0,...overrides}}
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));function angleDelta(a,b){let d=(a-b+Math.PI)%(Math.PI*2);if(d<0)d+=Math.PI*2;return d-Math.PI}function approachAngle(a,b,k){return a+angleDelta(b,a)*clamp(k,0,1)}
export function stepVehicle(state,input,realDt,tuning=DEFAULT_TUNING){const dt=clamp(realDt,0,.04),throttle=clamp(input.throttle??0,0,1),steer=clamp(input.steer??0,-1,1),brake=clamp(input.brake??0,0,1),driftCommand=!!input.handbrake||(brake>tuning.driftTriggerBrake&&throttle>tuning.driftTriggerThrottle);if(state.flipping){state.flipTime+=dt;state.roll+=state.rollVelocity*dt;state.pitch+=state.pitchVelocity*dt;state.height=Math.max(0,Math.sin(Math.min(1,state.flipTime/tuning.flipDuration)*Math.PI)*1.45);state.speed*=Math.pow(.16,dt);state.x+=Math.sin(state.velocityYaw)*state.speed*dt*tuning.worldSpeedScale;state.z-=Math.cos(state.velocityYaw)*state.speed*dt*tuning.worldSpeedScale;if(state.flipTime>=tuning.flipDuration){state.flipping=false;state.flipTime=0;state.height=state.roll=state.pitch=state.rollVelocity=state.pitchVelocity=0;state.speed=Math.min(state.speed,8);state.velocityYaw=state.bodyYaw}return state}if(driftCommand&&!state.drifting){state.drifting=true;state.driftBaseYaw=state.bodyYaw;state.driftBaseSteer=steer;state.driftEntrySpeed=state.speed}else if(!driftCommand&&state.drifting){state.drifting=false;state.velocityYaw=approachAngle(state.velocityYaw,state.bodyYaw,tuning.driftExitCatch)}const simDt=dt*(state.drifting?tuning.driftTimeScale:1),beforeSpeed=state.speed;if(state.drifting){const request=clamp(steer-state.driftBaseSteer,-1,1),targetYaw=state.driftBaseYaw+request*tuning.driftMaxHeadingRadians;state.bodyYaw=approachAngle(state.bodyYaw,targetYaw,dt*tuning.driftYawResponse);state.velocityYaw=approachAngle(state.velocityYaw,state.bodyYaw,simDt*tuning.driftVelocityFollow);state.speed+=throttle*tuning.driftDrive*simDt;state.speed-=brake*tuning.driftDrag*simDt;state.speed=clamp(state.speed,tuning.minDriftSpeed,Math.max(tuning.minDriftSpeed,state.driftEntrySpeed*1.06))}else{const speedFactor=.30+Math.min(1,state.speed/48)*.72;state.bodyYaw+=steer*tuning.normalYawRate*speedFactor*simDt;state.velocityYaw=approachAngle(state.velocityYaw,state.bodyYaw,simDt*tuning.normalVelocityFollow);state.speed+=throttle*tuning.acceleration*simDt;state.speed-=brake*tuning.brakeDeceleration*simDt;state.speed-=state.speed*tuning.rollingDrag*simDt;state.speed=clamp(state.speed,tuning.minSpeed,tuning.maxSpeed)}const longitudinalAccel=dt>0?(state.speed-beforeSpeed)/dt:0,pitchTarget=clamp(-longitudinalAccel/210,-.14,.24);state.pitch+=(pitchTarget-state.pitch)*clamp(dt*tuning.pitchResponse,0,1);const yawGap=angleDelta(state.bodyYaw,state.velocityYaw),lateralLoad=Math.abs(steer)*(state.speed/tuning.maxSpeed)+Math.abs(yawGap)*.9,rollTarget=clamp(-steer*lateralLoad*.34,-.34,.34);state.roll+=(rollTarget-state.roll)*clamp(dt*tuning.rollResponse,0,1);const rolloverSeverity=(state.speed/tuning.maxSpeed)*Math.max(brake/tuning.rolloverBrake,0)*Math.max(Math.abs(steer)/tuning.rolloverSteer,0)*(1+Math.abs(yawGap)*1.5);if(state.speed>tuning.rolloverSpeed&&brake>tuning.rolloverBrake&&Math.abs(steer)>tuning.rolloverSteer&&rolloverSeverity>1){state.flipping=true;state.flipTime=0;state.rollVelocity=-Math.sign(steer||1)*tuning.rolloverImpulse*clamp(rolloverSeverity,1,1.8);state.pitchVelocity=-1.5-brake*2.2;state.drifting=false}state.x+=Math.sin(state.velocityYaw)*state.speed*simDt*tuning.worldSpeedScale;state.z-=Math.cos(state.velocityYaw)*state.speed*simDt*tuning.worldSpeedScale;return state}
export function snapshotVehicle(state){return[state.x,state.z,state.bodyYaw,state.velocityYaw,state.speed,state.drifting?1:0,state.pitch,state.roll,state.flipping?1:0]}

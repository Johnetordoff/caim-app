export const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function steeringFromRail(x,width){if(!Number.isFinite(x)||!Number.isFinite(width)||width<=0)return 0;const raw=(x/width-.5)*2,dead=.04,m=Math.abs(raw);if(m<=dead)return 0;return Math.sign(raw)*Math.min(1,(m-dead)/(1-dead))}
export function steeringFromDrag(x,width,anchorX){const absolute=steeringFromRail(x,width);if(!Number.isFinite(anchorX))return absolute;const delta=(x-anchorX)/(width*.30);return clamp(absolute*.62+delta*.72,-1,1)}
export function throttleFromHorizontal(x,width){if(!Number.isFinite(x)||!Number.isFinite(width)||width<=0)return 0;const left=width*.56,right=width*.96;return clamp((x-left)/(right-left),0,1)}
export function brakeFromPull(y,height){if(!Number.isFinite(y)||!Number.isFinite(height)||height<=0)return 0;const top=height*.58,bottom=height*.94;return clamp((bottom-y)/(bottom-top),0,1)}

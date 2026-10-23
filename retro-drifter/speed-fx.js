export const clamp01=v=>Math.max(0,Math.min(1,v));
export function speedFx(speed,maxSpeed=320){
 const n=clamp01(speed/Math.max(1,maxSpeed));
 const rush=clamp01((n-.38)/.42);
 const streak=rush*rush;
 const barrier=clamp01((n-.78)/.12);
 const shock=barrier*barrier*(3-2*barrier);
 return {normalized:n,rush,streak,barrier:shock,fovKick:streak*.16+shock*.13,trailLength:1+streak*9+shock*14,starBrightness:.25+streak*.8+shock*1.4};
}

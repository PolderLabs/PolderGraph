import{e as dn,g as Vn}from"./graphology-C3ymkwNA.js";function Ut(a,r){(r==null||r>a.length)&&(r=a.length);for(var t=0,e=Array(r);t<r;t++)e[t]=a[t];return e}function ea(a,r){if(a){if(typeof a=="string")return Ut(a,r);var t={}.toString.call(a).slice(8,-1);return t==="Object"&&a.constructor&&(t=a.constructor.name),t==="Map"||t==="Set"?Array.from(a):t==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t)?Ut(a,r):void 0}}function M(a,r){var t=typeof Symbol<"u"&&a[Symbol.iterator]||a["@@iterator"];if(!t){if(Array.isArray(a)||(t=ea(a))||r){t&&(a=t);var e=0,n=function(){};return{s:n,n:function(){return e>=a.length?{done:!0}:{done:!1,value:a[e++]}},e:function(l){throw l},f:n}}throw new TypeError(`Invalid attempt to iterate non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var i,o=!0,s=!1;return{s:function(){t=t.call(a)},n:function(){var l=t.next();return o=l.done,l},e:function(l){s=!0,i=l},f:function(){try{o||t.return==null||t.return()}finally{if(s)throw i}}}}function Xn(a){if(Array.isArray(a))return a}function qn(a,r){var t=a==null?null:typeof Symbol<"u"&&a[Symbol.iterator]||a["@@iterator"];if(t!=null){var e,n,i,o,s=[],l=!0,d=!1;try{if(i=(t=t.call(a)).next,r===0){if(Object(t)!==t)return;l=!1}else for(;!(l=(e=i.call(t)).done)&&(s.push(e.value),s.length!==r);l=!0);}catch(h){d=!0,n=h}finally{try{if(!l&&t.return!=null&&(o=t.return(),Object(o)!==o))return}finally{if(d)throw n}}return s}}function jn(){throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function Q(a,r){return Xn(a)||qn(a,r)||ea(a,r)||jn()}var Ke={black:"#000000",silver:"#C0C0C0",gray:"#808080",grey:"#808080",white:"#FFFFFF",maroon:"#800000",red:"#FF0000",purple:"#800080",fuchsia:"#FF00FF",green:"#008000",lime:"#00FF00",olive:"#808000",yellow:"#FFFF00",navy:"#000080",blue:"#0000FF",teal:"#008080",aqua:"#00FFFF",darkblue:"#00008B",mediumblue:"#0000CD",darkgreen:"#006400",darkcyan:"#008B8B",deepskyblue:"#00BFFF",darkturquoise:"#00CED1",mediumspringgreen:"#00FA9A",springgreen:"#00FF7F",cyan:"#00FFFF",midnightblue:"#191970",dodgerblue:"#1E90FF",lightseagreen:"#20B2AA",forestgreen:"#228B22",seagreen:"#2E8B57",darkslategray:"#2F4F4F",darkslategrey:"#2F4F4F",limegreen:"#32CD32",mediumseagreen:"#3CB371",turquoise:"#40E0D0",royalblue:"#4169E1",steelblue:"#4682B4",darkslateblue:"#483D8B",mediumturquoise:"#48D1CC",indigo:"#4B0082",darkolivegreen:"#556B2F",cadetblue:"#5F9EA0",cornflowerblue:"#6495ED",rebeccapurple:"#663399",mediumaquamarine:"#66CDAA",dimgray:"#696969",dimgrey:"#696969",slateblue:"#6A5ACD",olivedrab:"#6B8E23",slategray:"#708090",slategrey:"#708090",lightslategray:"#778899",lightslategrey:"#778899",mediumslateblue:"#7B68EE",lawngreen:"#7CFC00",chartreuse:"#7FFF00",aquamarine:"#7FFFD4",skyblue:"#87CEEB",lightskyblue:"#87CEFA",blueviolet:"#8A2BE2",darkred:"#8B0000",darkmagenta:"#8B008B",saddlebrown:"#8B4513",darkseagreen:"#8FBC8F",lightgreen:"#90EE90",mediumpurple:"#9370DB",darkviolet:"#9400D3",palegreen:"#98FB98",darkorchid:"#9932CC",yellowgreen:"#9ACD32",sienna:"#A0522D",brown:"#A52A2A",darkgray:"#A9A9A9",darkgrey:"#A9A9A9",lightblue:"#ADD8E6",greenyellow:"#ADFF2F",paleturquoise:"#AFEEEE",lightsteelblue:"#B0C4DE",powderblue:"#B0E0E6",firebrick:"#B22222",darkgoldenrod:"#B8860B",mediumorchid:"#BA55D3",rosybrown:"#BC8F8F",darkkhaki:"#BDB76B",mediumvioletred:"#C71585",indianred:"#CD5C5C",peru:"#CD853F",chocolate:"#D2691E",tan:"#D2B48C",lightgray:"#D3D3D3",lightgrey:"#D3D3D3",thistle:"#D8BFD8",orchid:"#DA70D6",goldenrod:"#DAA520",palevioletred:"#DB7093",crimson:"#DC143C",gainsboro:"#DCDCDC",plum:"#DDA0DD",burlywood:"#DEB887",lightcyan:"#E0FFFF",lavender:"#E6E6FA",darksalmon:"#E9967A",violet:"#EE82EE",palegoldenrod:"#EEE8AA",lightcoral:"#F08080",khaki:"#F0E68C",aliceblue:"#F0F8FF",honeydew:"#F0FFF0",azure:"#F0FFFF",sandybrown:"#F4A460",wheat:"#F5DEB3",beige:"#F5F5DC",whitesmoke:"#F5F5F5",mintcream:"#F5FFFA",ghostwhite:"#F8F8FF",salmon:"#FA8072",antiquewhite:"#FAEBD7",linen:"#FAF0E6",lightgoldenrodyellow:"#FAFAD2",oldlace:"#FDF5E6",magenta:"#FF00FF",deeppink:"#FF1493",orangered:"#FF4500",tomato:"#FF6347",hotpink:"#FF69B4",coral:"#FF7F50",darkorange:"#FF8C00",lightsalmon:"#FFA07A",orange:"#FFA500",lightpink:"#FFB6C1",pink:"#FFC0CB",gold:"#FFD700",peachpuff:"#FFDAB9",navajowhite:"#FFDEAD",moccasin:"#FFE4B5",bisque:"#FFE4C4",mistyrose:"#FFE4E1",blanchedalmond:"#FFEBCD",papayawhip:"#FFEFD5",lavenderblush:"#FFF0F5",seashell:"#FFF5EE",cornsilk:"#FFF8DC",lemonchiffon:"#FFFACD",floralwhite:"#FFFAF0",snow:"#FFFAFA",lightyellow:"#FFFFE0",ivory:"#FFFFF0"},un=new Int8Array(4),gt=new Int32Array(un.buffer,0,1),hn=new Float32Array(un.buffer,0,1),Yn=/^\s*rgba?\s*\(/,Kn=/^\s*rgba?\s*\(\s*([0-9]*)\s*,\s*([0-9]*)\s*,\s*([0-9]*)(?:\s*,\s*(.*)?)?\)\s*$/;function St(a){var r=0,t=0,e=0,n=1,i=a.toLowerCase();if(i==="transparent")return{r:0,g:0,b:0,a:0};if(i in Ke)return St(Ke[i]);if(a[0]==="#")a.length===4?(r=parseInt(a.charAt(1)+a.charAt(1),16),t=parseInt(a.charAt(2)+a.charAt(2),16),e=parseInt(a.charAt(3)+a.charAt(3),16)):(r=parseInt(a.charAt(1)+a.charAt(2),16),t=parseInt(a.charAt(3)+a.charAt(4),16),e=parseInt(a.charAt(5)+a.charAt(6),16)),a.length===9&&(n=parseInt(a.charAt(7)+a.charAt(8),16)/255);else if(Yn.test(a)){var o=a.match(Kn);o&&(r=+o[1],t=+o[2],e=+o[3],o[4]&&(n=+o[4]))}return{r,g:t,b:e,a:n}}function Is(a){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!1,t=St(a),e=t.r,n=t.g,i=t.b,o=t.a;return r?[e/255*o,n/255*o,i/255*o,o]:[e/255,n/255,i/255,o]}var We={};for(var it in Ke)We[it]=me(Ke[it]),We[Ke[it]]=We[it];function cn(a,r,t,e,n){return gt[0]=e<<24|t<<16|r<<8|a,gt[0]=gt[0]&4278190079,hn[0]}function me(a){if(a=a.toLowerCase(),typeof We[a]<"u")return We[a];var r=St(a),t=r.r,e=r.g,n=r.b,i=r.a;i=i*255|0;var o=cn(t,e,n,i);return We[a]=o,o}function Ze(a,r){hn[0]=me(a);var t=gt[0],e=t&255,n=t>>8&255,i=t>>16&255,o=t>>24&255;return[e,n,i,o]}function yt(a){var r=a>>>8&255,t=a>>>16&255,e=a>>>24&255,n=a&255;return(n<<24|e<<16|t<<8|r)>>>0}function Zn(a,r,t,e){return(t<<24|r<<16|a<<8|e)>>>0}function $n(a,r,t,e,n,i){var o=Math.floor(t/i*n),s=Math.floor(a.drawingBufferHeight/i-e/i*n),l=new Uint8Array(4);a.bindFramebuffer(a.FRAMEBUFFER,r),a.readPixels(o,s,1,1,a.RGBA,a.UNSIGNED_BYTE,l);var d=Q(l,4),h=d[0],u=d[1],c=d[2],v=d[3];return[h,u,c,v]}function Qn(a){var r=St(a),t=r.r,e=r.g,n=r.b,i=r.a,o=(t/255).toFixed(6),s=(e/255).toFixed(6),l=(n/255).toFixed(6),d=i.toFixed(6);return"vec4(".concat(o,", ").concat(s,", ").concat(l,", ").concat(d,")")}function Jn(a,r){if(typeof a!="object"||!a)return a;var t=a[Symbol.toPrimitive];if(t!==void 0){var e=t.call(a,r);if(typeof e!="object")return e;throw new TypeError("@@toPrimitive must return a primitive value.")}return String(a)}function fn(a){var r=Jn(a,"string");return typeof r=="symbol"?r:r+""}function S(a,r,t){return(r=fn(r))in a?Object.defineProperty(a,r,{value:t,enumerable:!0,configurable:!0,writable:!0}):a[r]=t,a}function va(a,r){var t=Object.keys(a);if(Object.getOwnPropertySymbols){var e=Object.getOwnPropertySymbols(a);r&&(e=e.filter(function(n){return Object.getOwnPropertyDescriptor(a,n).enumerable})),t.push.apply(t,e)}return t}function N(a){for(var r=1;r<arguments.length;r++){var t=arguments[r]!=null?arguments[r]:{};r%2?va(Object(t),!0).forEach(function(e){S(a,e,t[e])}):Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(t)):va(Object(t)).forEach(function(e){Object.defineProperty(a,e,Object.getOwnPropertyDescriptor(t,e))})}return a}function V(a,r){if(!(a instanceof r))throw new TypeError("Cannot call a class as a function")}function ma(a,r){for(var t=0;t<r.length;t++){var e=r[t];e.enumerable=e.enumerable||!1,e.configurable=!0,"value"in e&&(e.writable=!0),Object.defineProperty(a,fn(e.key),e)}}function X(a,r,t){return r&&ma(a.prototype,r),t&&ma(a,t),Object.defineProperty(a,"prototype",{writable:!1}),a}function Ue(a){return Ue=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(r){return r.__proto__||Object.getPrototypeOf(r)},Ue(a)}function gn(){try{var a=!Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],function(){}))}catch{}return(gn=function(){return!!a})()}function er(a){if(a===void 0)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return a}function tr(a,r){if(r&&(typeof r=="object"||typeof r=="function"))return r;if(r!==void 0)throw new TypeError("Derived constructors may only return object or undefined");return er(a)}function ee(a,r,t){return r=Ue(r),tr(a,gn()?Reflect.construct(r,t||[],Ue(a).constructor):r.apply(a,t))}function Ot(a,r){return Ot=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},Ot(a,r)}function te(a,r){if(typeof r!="function"&&r!==null)throw new TypeError("Super expression must either be null or a function");a.prototype=Object.create(r&&r.prototype,{constructor:{value:a,writable:!0,configurable:!0}}),Object.defineProperty(a,"prototype",{writable:!1}),r&&Ot(a,r)}function q(a){"@babel/helpers - typeof";return q=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(r){return typeof r}:function(r){return r&&typeof Symbol=="function"&&r.constructor===Symbol&&r!==Symbol.prototype?"symbol":typeof r},q(a)}function ar(a){if(Array.isArray(a))return Ut(a)}function nr(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)}function rr(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function H(a){return ar(a)||nr(a)||ea(a)||rr()}function De(a){return q(a)==="object"&&a!==null&&"attribute"in a}function ir(){var a=`
float sdf_circle(vec2 uv, float size) {
  return length(uv) - size;
}
`;return{name:"circle",glsl:a,uniforms:[]}}function or(a){var r,t=WebGL2RenderingContext,e=t.UNSIGNED_BYTE,n=(r=void 0)!==null&&r!==void 0?r:{attribute:"color"};if(!De(n)){var i=n,o=`
vec4 layer_fill() {
  return `.concat(Qn(i),`;
}
`);return{name:"fill",uniforms:[],attributes:[],glsl:o}}var s=n.attribute,l=`
vec4 layer_fill(vec4 v_fillColor) {
  return v_fillColor;
}
`;return{name:"fill",uniforms:[],attributes:[{name:"fillColor",size:4,type:e,normalized:!0,source:s}],glsl:l}}function tt(){var a=`
// Plain solid color layer
vec4 layer_plain(EdgeContext ctx) {
  return v_color;
}
`;return{name:"plain",glsl:a,uniforms:[],attributes:[]}}function sr(){var a=`
// Position at parameter t ∈ [0, 1]
vec2 path_straight_position(float t, vec2 source, vec2 target) {
  return mix(source, target, t);
}

// Total length of the path (analytical - more efficient than sampling)
float path_straight_length(vec2 source, vec2 target) {
  return length(target - source);
}
`;return{name:"straight",segments:1,minBodyLengthRatio:0,linearParameterization:!0,glsl:a,uniforms:[],attributes:[]}}function lr(a){var r=a??{},t=r.segments,e=t===void 0?32:t,n=`
const float LOOP_PI = 3.141592653589793;

float loopWorldRadius() {
  float nodeWorldRadius = v_sourceNodeSize * u_correctionRatio / u_sizeRatio;
  return max(v_loopRadius * nodeWorldRadius, 0.001);
}

// Cubic Bézier with P0 = P3 = source.
// Control points extend outward orthogonal to the node surface at exit/entry angles.
vec2 path_loop_position(float t, vec2 source, vec2 target) {
  float R = loopWorldRadius();
  float angle = v_loopAngle + (v_loopFixedOrientation > 0.5 ? u_cameraAngle : 0.0);
  float halfSpread = v_loopSpread * 0.5;

  float exitAngle = angle - halfSpread;
  float entryAngle = angle + halfSpread;

  // Control point distance: at t=0.5 the Bézier reaches 0.75 * cpDist * cos(halfSpread)
  // from source. Solve for cpDist so the loop tip reaches exactly R.
  float cpDist = R / (0.75 * cos(halfSpread));

  vec2 cp1 = source + cpDist * vec2(cos(exitAngle), sin(exitAngle));
  vec2 cp2 = source + cpDist * vec2(cos(entryAngle), sin(entryAngle));

  float u = 1.0 - t;
  vec2 d1 = cp1 - source;
  vec2 d2 = cp2 - source;
  return source + 3.0 * t * u * (u * d1 + t * d2);
}

// Approximate arc length via chord sampling
float path_loop_length(vec2 source, vec2 target) {
  float len = 0.0;
  vec2 prev = path_loop_position(0.0, source, target);
  const int STEPS = 16;
  for (int i = 1; i <= STEPS; i++) {
    float t = float(i) / float(STEPS);
    vec2 cur = path_loop_position(t, source, target);
    len += length(cur - prev);
    prev = cur;
  }
  return len;
}
`;return{name:"loop",segments:e,glsl:n,uniforms:[],attributes:[{name:"loopRadius",size:1,type:WebGL2RenderingContext.FLOAT},{name:"loopAngle",size:1,type:WebGL2RenderingContext.FLOAT},{name:"loopSpread",size:1,type:WebGL2RenderingContext.FLOAT},{name:"loopFixedOrientation",size:1,type:WebGL2RenderingContext.FLOAT}],variables:{loopRadius:{type:"number",default:4},loopAngle:{type:"number",default:Math.PI/4},loopSpread:{type:"number",default:80*Math.PI/180},loopFixedOrientation:{type:"number",default:0}},spread:{variable:"loopRadius",compute:function(o){return o+4}}}}var dr=function(r){return r},ur=function(r){return r*r},hr=function(r){return r*(2-r)},cr=function(r){return(r*=2)<1?.5*r*r:-.5*(--r*(r-2)-1)},fr=function(r){return r*r*r},gr=function(r){return--r*r*r+1},vr=function(r){return(r*=2)<1?.5*r*r*r:.5*((r-=2)*r*r+2)},mr=function(r){return r===0?0:Math.pow(2,10*(r-1))},pr=function(r){return r===1?1:1-Math.pow(2,-10*r)},br=function(r){return r===0?0:r===1?1:r<.5?Math.pow(2,10*(2*r-1))/2:(2-Math.pow(2,-10*(2*r-1)))/2},pa={linear:dr,quadraticIn:ur,quadraticOut:hr,quadraticInOut:cr,cubicIn:fr,cubicOut:gr,cubicInOut:vr,exponentialIn:mr,exponentialOut:pr,exponentialInOut:br};function vn(a){return a?typeof a=="function"?a:pa[a]:pa.linear}function xr(a){return q(a)==="object"&&"glsl"in a&&!("attributes"in a)}function yr(a){return q(a)==="object"&&"glsl"in a&&!("attributes"in a)}var Ht={shapes:[ir()],variables:{},layers:[or()],label:{},backdrop:{},labelAttachments:{}},vt={paths:[sr(),lr()],extremities:[],variables:{},layers:[tt()],defaultHead:"none",defaultTail:"none",label:{}},Vt=["nodes","topNodes"],Xt=["edges","topEdges"],qt=[].concat(Xt,Vt),Tr={nodes:Ht,edges:vt,depthLayers:H(qt)};function ta(a){return q(a)==="object"&&a!==null&&"attribute"in a}function mn(a){return typeof a=="function"}function pn(a){return q(a)==="object"&&a!==null&&"when"in a&&typeof a.when=="function"&&"then"in a}function bn(a){return q(a)==="object"&&a!==null&&"whenState"in a&&"then"in a}function xn(a){return q(a)==="object"&&a!==null&&"whenData"in a&&"then"in a}var _r={isHovered:!1,isLabelHovered:!1,isHidden:!1,isHighlighted:!1,isDragged:!1},Sr={isHovered:!1,isLabelHovered:!1,isHidden:!1,isHighlighted:!1,parallelIndex:0,parallelCount:1},Er={isIdle:!0,isPanning:!1,isZooming:!1,isDragging:!1,hasHovered:!1,hasHighlighted:!1};function Rr(a){return N(N({},_r),a)}function Ar(a){return N(N({},Sr),a)}function ba(a){return N(N({},Er),a)}var Dr={x:{attribute:"x"},y:{attribute:"y"},size:{whenState:"isHovered",then:{attribute:"size",defaultValue:12},else:{attribute:"size",defaultValue:10}},color:{attribute:"color",defaultValue:"#666"},label:{attribute:"label"},visibility:{whenState:"isHidden",then:"hidden",else:"visible"},labelVisibility:{whenState:"isHovered",then:"visible",else:"auto"},backdropVisibility:{whenState:"isHovered",then:"visible",else:"hidden"},backdropColor:"#ffffff",backdropShadowColor:"rgba(0, 0, 0, 0.5)",backdropShadowBlur:12,backdropPadding:6},Cr={size:{attribute:"size",defaultValue:1},color:{attribute:"color",defaultValue:"#ccc"},label:{attribute:"label"},visibility:{whenState:"isHidden",then:"hidden",else:"visible"}},Ft={nodes:N(N({},Dr),{},{depth:{whenState:"isHovered",then:"topNodes",else:"nodes"}}),edges:N(N({},Cr),{},{depth:{whenState:["isHighlighted","isHovered"],then:"topEdges",else:"edges"}})};function Lr(a){return"min"in a||"max"in a||"minValue"in a||"maxValue"in a||"easing"in a}function Pr(a){return"dict"in a}function Et(a,r){return typeof a=="string"?r[a]===!0:Array.isArray(a)?a.every(function(t){return r[t]===!0}):q(a)==="object"&&a!==null?Object.entries(a).every(function(t){var e=Q(t,2),n=e[0],i=e[1];return r[n]===i}):!1}function Fr(a,r){var t=r[a.attribute];return t===void 0?a.defaultValue:t}function kr(a,r,t){var e,n,i,o,s=r[a.attribute];if(s===void 0)return a.defaultValue;var l=Number(s);if(isNaN(l))return a.defaultValue;if(a.min===void 0&&a.max===void 0)return l;var d=(e=a.minValue)!==null&&e!==void 0?e:l,h=(n=a.maxValue)!==null&&n!==void 0?n:l;if(h===d){var u;return(u=a.min)!==null&&u!==void 0?u:l}var c=(l-d)/(h-d);c=Math.max(0,Math.min(1,c));var v=vn(a.easing);c=v(c);var b=(i=a.min)!==null&&i!==void 0?i:0,m=(o=a.max)!==null&&o!==void 0?o:1;return b+c*(m-b)}function wr(a,r){var t=r[a.attribute];if(t===void 0)return a.defaultValue;var e=String(t);return e in a.dict?a.dict[e]:a.defaultValue}function Ir(a,r,t){return Pr(a)?wr(a,r):Lr(a)?kr(a,r):Fr(a,r)}function yn(a,r){return typeof a=="string"?!!r[a]:Array.isArray(a)?a.every(function(t){return!!r[t]}):q(a)==="object"&&a!==null?Object.entries(a).every(function(t){var e=Q(t,2),n=e[0],i=e[1];return r[n]===i}):!1}function mt(a,r,t,e,n,i){if(a==null)return i;if(q(a)!=="object"&&typeof a!="function")return a;if(pn(a)){var o=a.when(r,t,e,n)?a.then:a.else;return o===void 0?i:mt(o,r,t,e,n,i)}if(bn(a)){var s=Et(a.whenState,t)?a.then:a.else;return s===void 0?i:mt(s,r,t,e,n,i)}if(xn(a)){var l=yn(a.whenData,r)?a.then:a.else;return l===void 0?i:mt(l,r,t,e,n,i)}if(mn(a)){var d=a(r,t,e,n);return d??i}if(ta(a)){var h=Ir(a,r);return h??i}return a}function ce(a){if(a==null)return"static";if(pn(a))return"graph-state";if(bn(a)){var r=ce(a.then),t=a.else!==void 0?ce(a.else):"static";return ue("item-state",ue(r,t))}if(xn(a)){var e=ce(a.then),n=a.else!==void 0?ce(a.else):"static";return ue(e,n)}return mn(a)?"graph-state":(ta(a),"static")}function ue(a,r){return a==="graph-state"||r==="graph-state"?"graph-state":a==="item-state"||r==="item-state"?"item-state":"static"}function xa(a){if(!a)return{dependency:"static",xAttribute:null,yAttribute:null};var r=Array.isArray(a)?a:[a],t="static",e=null,n=null,i=M(r),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;if("matchData"in s&&"cases"in s)for(var l=s.cases,d=0,h=Object.values(l);d<h.length;d++)for(var u=h[d],c=0,v=Object.values(u);c<v.length;c++){var b=v[c];t=ue(t,ce(b))}else if("matchState"in s&&"cases"in s){t=ue(t,"item-state");for(var m=s.cases,x=0,g=Object.values(m);x<g.length;x++)for(var f=g[x],p=0,y=Object.values(f);p<y.length;p++){var T=y[p];t=ue(t,ce(T))}}else if("when"in s&&"then"in s)t="graph-state";else if("whenState"in s){t=ue(t,"item-state");var _=s.then;if(_&&q(_)==="object")for(var E=0,A=Object.values(_);E<A.length;E++){var R=A[E];t=ue(t,ce(R))}var L=s.else;if(L&&q(L)==="object")for(var F=0,C=Object.values(L);F<C.length;F++){var P=C[F];t=ue(t,ce(P))}}else if("whenData"in s){var D=s.then;if(D&&q(D)==="object")for(var k=0,w=Object.values(D);k<w.length;k++){var I=w[k];t=ue(t,ce(I))}var G=s.else;if(G&&q(G)==="object")for(var z=0,B=Object.values(G);z<B.length;z++){var O=B[z];t=ue(t,ce(O))}}else for(var W=0,U=Object.entries(s);W<U.length;W++){var K=Q(U[W],2),Z=K[0],J=K[1];if(!na.has(Z)&&(t=ue(t,ce(J)),(Z==="x"||Z==="y")&&ta(J))){var ie=J.attribute;Z==="x"&&!e&&(e=ie),Z==="y"&&!n&&(n=ie)}}}}catch(ae){i.e(ae)}finally{i.f()}return{dependency:t,xAttribute:e,yAttribute:n}}var Te={size:10,color:"#666",opacity:1,shape:"circle",rotationAlignment:"viewport",labelRotationAlignment:"viewport",visibility:"visible",depth:"nodes",zIndex:0,label:"",labelColor:"#000",labelSize:12,labelFont:"sans-serif",labelVisibility:"auto",labelPosition:"right",labelAngle:0,labelDepth:"nodes",backdropVisibility:"hidden",backdropColor:"transparent",backdropShadowColor:"transparent",backdropShadowBlur:0,backdropPadding:0,backdropBorderColor:"transparent",backdropBorderWidth:0,backdropCornerRadius:0,backdropLabelPadding:-1,backdropArea:"both",labelAttachment:null,labelAttachmentPlacement:"below"},aa={size:1,color:"#ccc",opacity:1,path:"straight",selfLoopPath:"loop",parallelSpread:.25,tail:"none",head:"none",visibility:"visible",depth:"edges",zIndex:0,label:"",labelColor:"#666",labelVisibility:"auto",labelDepth:"edges"},na=new Set(["when","whenState","whenData","then","else"]),ya=Object.keys(Te),zr=Object.values(Te),Ta=Object.keys(aa),Mr=Object.values(aa);function we(a,r,t,e,n,i,o){for(var s in r){var l;if(!na.has(s)){var d=(l=a[s])!==null&&l!==void 0?l:o[s];a[s]=mt(r[s],t,e,n,i,d)}}"depth"in r&&!("labelDepth"in r)&&(a.labelDepth=a.depth)}function Tn(a,r,t,e,n,i,o){var s=M(r),l;try{for(s.s();!(l=s.n()).done;){var d=l.value;if("matchData"in d&&"cases"in d){var h,u=String((h=t[d.matchData])!==null&&h!==void 0?h:""),c=d.cases;u in c&&we(a,c[u],t,e,n,i,o)}else if("matchState"in d&&"cases"in d){var v,b=String((v=e[d.matchState])!==null&&v!==void 0?v:""),m=d.cases;b in m&&we(a,m[b],t,e,n,i,o)}else if("when"in d&&"then"in d){var x=d.when;if(!x(t,e,n,i))continue;we(a,d.then,t,e,n,i,o)}else if("whenState"in d&&"then"in d){if(!Et(d.whenState,e))continue;we(a,d.then,t,e,n,i,o)}else if("whenData"in d&&"then"in d){if(!yn(d.whenData,t))continue;we(a,d.then,t,e,n,i,o)}else we(a,d,t,e,n,i,o)}}catch(g){s.e(g)}finally{s.f()}}function _a(a,r,t,e,n,i){for(var o=i||{},s=o,l=0,d=ya.length;l<d;l++)s[ya[l]]=zr[l];if(s.x=void 0,s.y=void 0,s.labelBackgroundColor=void 0,s.labelBackgroundPadding=void 0,s.labelCursor=void 0,!a){var h,u,c,v,b;return s.x=(h=r.x)!==null&&h!==void 0?h:0,s.y=(u=r.y)!==null&&u!==void 0?u:0,o.size=(c=r.size)!==null&&c!==void 0?c:10,o.color=(v=r.color)!==null&&v!==void 0?v:"#666",o.label=(b=r.label)!==null&&b!==void 0?b:"",o}var m=Array.isArray(a)?a:[a];return Tn(s,m,r,t,e,n,Te),o}function Sa(a,r,t,e,n,i){for(var o=i||{},s=o,l=0,d=Ta.length;l<d;l++)s[Ta[l]]=Mr[l];if(!a){var h,u,c;return o.size=(h=r.size)!==null&&h!==void 0?h:1,o.color=(u=r.color)!==null&&u!==void 0?u:"#ccc",o.label=(c=r.label)!==null&&c!==void 0?c:"",o}var v=Array.isArray(a)?a:[a];return Tn(s,v,r,t,e,n,aa),typeof s.labelPosition=="number"&&(s.labelPosition=void 0),o}function Nr(a,r,t){var e,n;if(a==null)return t;if(typeof a=="function")return(e=a(r))!==null&&e!==void 0?e:t;if(q(a)==="object"&&"when"in a){var i,o=a,s=o.when(r),l=s?o.then:o.else;return l===void 0?t:typeof l=="function"?(i=l(r))!==null&&i!==void 0?i:t:l??t}if(q(a)==="object"&&"whenState"in a){var d,h=a,u=Et(h.whenState,r),c=u?h.then:h.else;return c===void 0?t:typeof c=="function"?(d=c(r))!==null&&d!==void 0?d:t:c??t}return(n=a)!==null&&n!==void 0?n:t}function Ea(a,r){var t={};if(!a)return t;var e=Array.isArray(a)?a:[a],n=M(e),i;try{for(n.s();!(i=n.n()).done;){var o=i.value;if("when"in o&&"then"in o){var s=o.when(r),l=s?o.then:o.else;l&&q(l)==="object"&&kt(t,l,r)}else if("whenState"in o&&"then"in o){var d=Et(o.whenState,r),h=d?o.then:o.else;h&&q(h)==="object"&&kt(t,h,r)}else kt(t,o,r)}}catch(u){n.e(u)}finally{n.f()}return t}function kt(a,r,t){for(var e=0,n=Object.entries(r);e<n.length;e++){var i=Q(n[e],2),o=i[0],s=i[1];na.has(o)||(a[o]=Nr(s,t))}}var ra=(function(a){function r(){var t;return V(this,r),t=ee(this,r),t.rawEmitter=t,t}return te(r,a),X(r)})(dn.EventEmitter),wt,Ra;function Gr(){return Ra||(Ra=1,wt=function(r){return r!==null&&typeof r=="object"&&typeof r.addUndirectedEdgeWithKey=="function"&&typeof r.dropNode=="function"&&typeof r.multi=="boolean"}),wt}var Br=Gr();const Wr=Vn(Br);var Ur={easing:"quadraticInOut",duration:150};function he(){return Float32Array.of(1,0,0,0,1,0,0,0,1)}function ot(a,r,t){return a[0]=r,a[4]=typeof t=="number"?t:r,a}function Aa(a,r){var t=Math.sin(r),e=Math.cos(r);return a[0]=e,a[1]=t,a[3]=-t,a[4]=e,a}function Da(a,r,t){return a[6]=r,a[7]=t,a}function ye(a,r){var t=a[0],e=a[1],n=a[2],i=a[3],o=a[4],s=a[5],l=a[6],d=a[7],h=a[8],u=r[0],c=r[1],v=r[2],b=r[3],m=r[4],x=r[5],g=r[6],f=r[7],p=r[8];return a[0]=u*t+c*i+v*l,a[1]=u*e+c*o+v*d,a[2]=u*n+c*s+v*h,a[3]=b*t+m*i+x*l,a[4]=b*e+m*o+x*d,a[5]=b*n+m*s+x*h,a[6]=g*t+f*i+p*l,a[7]=g*e+f*o+p*d,a[8]=g*n+f*s+p*h,a}function _n(a,r){var t=Math.cos(r),e=Math.sin(r);return{x:t*a.x+e*a.y,y:-e*a.x+t*a.y}}function Je(a,r){var t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:1,e=a[0],n=a[1],i=a[3],o=a[4],s=a[6],l=a[7],d=r.x,h=r.y;return{x:d*e+h*i+s*t,y:d*n+h*o+l*t}}function Or(a,r){var t=a.height/a.width,e=r.height/r.width;return t<1&&e>1||t>1&&e<1?1:Math.min(Math.max(e,1/e),Math.max(1/t,t))}function Ae(a,r,t,e,n){var i=a.angle,o=a.ratio,s=a.x,l=a.y,d=r.width,h=r.height,u=he(),c=Math.min(d,h)-2*e,v=Or(r,t);return n?(ye(u,Da(he(),s,l)),ye(u,ot(he(),o)),ye(u,Aa(he(),i)),ye(u,ot(he(),d/c/2/v,h/c/2/v))):(ye(u,ot(he(),2*(c/d)*v,2*(c/h)*v)),ye(u,Aa(he(),-i)),ye(u,ot(he(),1/o)),ye(u,Da(he(),-s,-l))),u}function Hr(a,r,t){var e=Je(a,{x:Math.cos(r.angle),y:Math.sin(r.angle)},0),n=e.x,i=e.y;return 1/Math.sqrt(Math.pow(n,2)+Math.pow(i,2))/t.width}function Ce(a){return a.labelVisibility==="visible"&&a.visibility!=="hidden"}function Ca(a){return a.backdropVisibility==="visible"&&a.visibility!=="hidden"}function It(a){return[a.rotationAlignment==="graph"?1:0,a.labelRotationAlignment==="graph"?1:0]}function La(a,r,t){var e=a[r];if(e)for(var n=0;n<e.length;n++){var i=e[n];if(!(t<i.offset||t>=i.offset+i.count)){if(i.count===1)e.splice(n,1);else if(t===i.offset)i.offset++,i.count--;else if(t===i.offset+i.count-1)i.count--;else{var o=t+1,s=i.offset+i.count-o;i.count=t-i.offset,e.splice(n+1,0,{offset:o,count:s})}return}}}function Pa(a,r,t){if(!a[r]){a[r]=[{offset:t,count:1}];return}for(var e=a[r],n=e.length,i=0;i<e.length;i++)if(t<e[i].offset){n=i;break}var o=n>0?e[n-1]:null,s=n<e.length?e[n]:null,l=o&&o.offset+o.count===t,d=s&&t+1===s.offset;l&&d?(o.count+=1+s.count,e.splice(n,1)):l?o.count++:d?(s.offset--,s.count++):e.splice(n,0,{offset:t,count:1})}function Vr(a){if(!Wr(a))throw new Error("Sigma: invalid graph instance.")}function jt(a){var r=Q(a.x,2),t=r[0],e=r[1],n=Q(a.y,2),i=n[0],o=n[1],s=Math.max(e-t,o-i),l=(e+t)/2,d=(o+i)/2;(s===0||Math.abs(s)===1/0||isNaN(s))&&(s=1),isNaN(l)&&(l=0),isNaN(d)&&(d=0);var h=function(c){return{x:.5+(c.x-l)/s,y:.5+(c.y-d)/s}};return h.applyTo=function(u){u.x=.5+(u.x-l)/s,u.y=.5+(u.y-d)/s},h.inverse=function(u){return{x:l+s*(u.x-.5),y:d+s*(u.y-.5)}},h.ratio=s,h}function Fa(a,r){var t=r.size;if(t!==0){var e=a.length;a.length+=t;var n=0;r.forEach(function(i){a[e+n]=i,n++})}}function Xr(a){a=a||{};for(var r=0,t=arguments.length<=1?0:arguments.length-1;r<t;r++){var e=r+1<1||arguments.length<=r+1?void 0:arguments[r+1];e&&Object.assign(a,e)}return a}function Xe(a,r){for(var t in r)if(Object.prototype.hasOwnProperty.call(r,t)&&r[t]!==a[t])return!0;return!1}function Ie(a,r,t){t?a.add(r):a.delete(r)}var ia={hideEdgesOnMove:!1,hideLabelsOnMove:!1,renderLabels:!0,renderEdgeLabels:!1,enableEdgeEvents:!1,nodeLabelEvents:!1,edgeLabelEvents:!1,pickingDownSizingRatio:2,nodePickingPadding:0,edgePickingPadding:4,labelPickingPadding:10,stagePadding:30,minEdgeThickness:1.7,antiAliasingFeather:1,dragTimeout:100,draggedEventsTolerance:3,inertiaDuration:200,inertiaRatio:3,zoomDuration:250,zoomingRatio:1.7,doubleClickTimeout:300,doubleClickZoomingRatio:2.2,doubleClickZoomingDuration:200,tapMoveTolerance:10,zoomToSizeRatioFunction:Math.sqrt,itemSizesReference:"positions",autoRescale:!0,autoRescaleContent:"positions",enableNodeDrag:!1,getDraggedNodes:function(r){return[r]},dragPositionToAttributes:null,labelDensity:1,labelGridCellSize:100,labelRenderedSizeThreshold:6,labelPixelSnapping:!0,minCameraRatio:null,maxCameraRatio:null,enableCameraZooming:!0,enableScrollBlocking:!0,scrollBlockingReleaseThreshold:5,enableCameraPanning:!0,enableCameraRotation:!0,enableCameraMouseRotation:!0,cameraPanBoundaries:null,allowInvalidContainer:!1,DEBUG_displayPickingLayer:!1};function zt(a){if(typeof a.labelDensity!="number"||a.labelDensity<0)throw new Error("Settings: invalid `labelDensity`. Expecting a positive number.");var r=a.minCameraRatio,t=a.maxCameraRatio;if(typeof r=="number"&&typeof t=="number"&&t<r)throw new Error("Settings: invalid camera ratio boundaries. Expecting `maxCameraRatio` to be greater than `minCameraRatio`.")}function qr(a){return Xr({},ia,a)}var jr=new Set(["italic","oblique"]),Yr=new Set(["bold","bolder","lighter"]);function Mt(a){for(var r="normal",t="normal",e=a.trim(),n=e.split(/\s+/),i=0,o=0;o<n.length;o++){var s=n[o].toLowerCase();if(jr.has(s))t=s,i=o+1;else if(Yr.has(s)||/^\d{3}$/.test(s))r=s,i=o+1;else if(s==="normal")i=o+1;else break}var l=n.slice(i).join(" ");return{family:l||e,weight:r,style:t}}function ka(a,r,t){var e=document.createElement(a);if(r)for(var n in r)e.style[n]=r[n];if(t)for(var i in t)e.setAttribute(i,t[i]);return e}function Yt(){return typeof window.devicePixelRatio<"u"?window.devicePixelRatio:1}function Kr(a){return a.normalized?1:a.size}function Nt(a){var r=0;return a.forEach(function(t){return r+=Kr(t)}),r}function Sn(a,r,t){var e=a==="VERTEX"?r.VERTEX_SHADER:r.FRAGMENT_SHADER,n=r.createShader(e);if(n===null)throw new Error("loadShader: error while creating the shader");r.shaderSource(n,t),r.compileShader(n);var i=r.getShaderParameter(n,r.COMPILE_STATUS);if(!i){var o=r.getShaderInfoLog(n);throw r.deleteShader(n),new Error(`loadShader: error while compiling the shader:
`.concat(o,`
`).concat(t))}return n}function oa(a,r){return Sn("VERTEX",a,r)}function sa(a,r){return Sn("FRAGMENT",a,r)}function la(a,r){var t=a.createProgram();if(t===null)throw new Error("loadProgram: error while creating the program.");var e,n;for(e=0,n=r.length;e<n;e++)a.attachShader(t,r[e]);a.linkProgram(t);var i=a.getProgramParameter(t,a.LINK_STATUS);if(!i)throw a.deleteProgram(t),new Error("loadProgram: error while linking the program.");return t}function wa(a){var r=a.gl,t=a.buffer,e=a.program,n=a.vertexShader,i=a.fragmentShader;r.deleteShader(n),r.deleteShader(i),r.deleteProgram(e),r.deleteBuffer(t)}function Y(a){return a%1===0?a.toFixed(1):a.toString()}var $e={right:0,left:1,above:2,below:3,over:4},et=5,Ia=3,En=`
float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
float nodeRadiusGraphSpace = nodeSize * u_correctionRatio / u_sizeRatio * 2.0;
float nodeRadiusNDC = nodeRadiusGraphSpace * matrixScaleX;
float nodeRadiusPixels = nodeRadiusNDC * u_resolution.x / 2.0;
`,Zr=`
mat2 rotate2D(float angle) {
  float c = cos(angle);
  float s = sin(angle);
  return mat2(c, -s, s, c);
}
`,Rn=`
vec2 getLabelDirection(float positionMode) {
  if (positionMode < 0.5) return vec2(1.0, 0.0);   // Right
  if (positionMode < 1.5) return vec2(-1.0, 0.0);  // Left
  if (positionMode < 2.5) return vec2(0.0, -1.0);  // Above
  if (positionMode < 3.5) return vec2(0.0, 1.0);   // Below
  return vec2(0.0);                                 // Over (centered)
}
`,$r=`
float sdfBox(vec2 p, vec2 halfSize) {
  vec2 d = abs(p) - halfSize;
  return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}
`,Qr=`
float sdfRotatedBox(vec2 p, vec2 halfSize, float angle) {
  float c = cos(-angle);
  float s = sin(-angle);
  vec2 rotatedP = mat2(c, -s, s, c) * p;
  return sdfBox(rotatedP, halfSize);
}
`,Jr=`
float sdfRoundedBox(vec2 p, vec2 halfSize, float radius) {
  vec2 d = abs(p) - halfSize + radius;
  return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - radius;
}
`,ei=`
float sdfRoundedRotatedBox(vec2 p, vec2 halfSize, float angle, float radius) {
  float c = cos(-angle);
  float s = sin(-angle);
  vec2 rotatedP = mat2(c, -s, s, c) * p;
  return sdfRoundedBox(rotatedP, halfSize, radius);
}
`,An=`
vec2 labelBoxCenter(float positionMode, float labelStart, vec2 halfSize, float textHalfY) {
  if (positionMode < 0.5) return vec2(labelStart + halfSize.x, 0.0);    // right
  if (positionMode < 1.5) return vec2(-(labelStart + halfSize.x), 0.0); // left
  if (positionMode < 2.5) return vec2(0.0, -(labelStart + textHalfY));  // above
  if (positionMode < 3.5) return vec2(0.0, labelStart + textHalfY);     // below
  return vec2(0.0);                                                     // over
}
`,Dn=2,be=`
vec4 readNodeData(sampler2D nodeDataTexture, int nodeDataTextureWidth, int nodeIndex) {
  int t = nodeIndex * `.concat(Dn,`;
  ivec2 coord = ivec2(t % nodeDataTextureWidth, t / nodeDataTextureWidth);
  return texelFetch(nodeDataTexture, coord, 0);
}
`),Pe=`
vec4 readNodeFlags(sampler2D nodeDataTexture, int nodeDataTextureWidth, int nodeIndex) {
  int t = nodeIndex * `.concat(Dn,` + 1;
  ivec2 coord = ivec2(t % nodeDataTextureWidth, t / nodeDataTextureWidth);
  return texelFetch(nodeDataTexture, coord, 0);
}
`),Ve=`
vec4 readFrameTexel(sampler2D frameTexture, int frameTextureWidth, int index) {
  ivec2 coord = ivec2(index % frameTextureWidth, index / frameTextureWidth);
  return texelFetch(frameTexture, coord, 0);
}
`;function ti(a,r){var t=function(s){return s.uniforms.filter(function(l){return l.type==="float"}).map(function(l){var d;return Y((d=l.value)!==null&&d!==void 0?d:0)})},e=function(s){var l=t(s);return l.length>0?"sdf_".concat(s.name,"(uv, size, ").concat(l.join(", "),")"):"sdf_".concat(s.name,"(uv, size)")};if(a.length===1)return{code:za(e(a[0])),multiShape:!1};var n=a.map(function(o,s){return"    case ".concat(r?r[s]:s,": return ").concat(e(o),";")}).join(`
`),i=`
float queryShapeSDF(int shapeId, vec2 uv, float size) {
  switch (shapeId) {
`.concat(n,`
    default: return `).concat(e(a[0]),`;
  }
}
int g_shapeId;
`).concat(za("queryShapeSDF(g_shapeId, uv, size)"),`
`);return{code:i,multiShape:!0}}function za(a){return`
float findEdgeDistance(vec2 direction, float size) {
  float lo = 0.0, hi = 2.0;
  for (int i = 0; i < 8; i++) {
    float mid = (lo + hi) * 0.5;
    vec2 uv = direction * mid;
    if (`.concat(a,` < 0.0) lo = mid; else hi = mid;
  }
  return (lo + hi) * 0.5;
}
`)}function ai(a,r){for(;!{}.hasOwnProperty.call(a,r)&&(a=Ue(a))!==null;);return a}function Kt(){return Kt=typeof Reflect<"u"&&Reflect.get?Reflect.get.bind():function(a,r,t){var e=ai(a,r);if(e){var n=Object.getOwnPropertyDescriptor(e,r);return n.get?n.get.call(arguments.length<3?a:t):n.value}},Kt.apply(null,arguments)}function ne(a,r,t,e){var n=Kt(Ue(a.prototype),r,t);return typeof n=="function"?function(i){return n.apply(t,i)}:n}var ni=1024,ri=1.5,ii=4096,da=(function(){function a(r,t){var e=arguments.length>2&&arguments[2]!==void 0?arguments[2]:ni;V(this,a),S(this,"texture",null),S(this,"dirty",!1),S(this,"dirtyRangeStart",1/0),S(this,"dirtyRangeEnd",-1),S(this,"indexMap",new Map),S(this,"freeIndices",[]),S(this,"nextIndex",0),this.gl=r,this.TEXELS_PER_ITEM=t,this.capacity=this.roundUpToPowerOfTwo(e);var n=this.computeTextureDimensions(this.capacity);this.textureWidth=n.width,this.textureHeight=n.height,this.data=new Float32Array(this.textureWidth*this.textureHeight*4),this.createTexture()}return X(a,[{key:"computeTextureDimensions",value:function(t){var e=t*this.TEXELS_PER_ITEM,n=Math.min(e,ii),i=Math.ceil(e/n);return{width:n,height:i}}},{key:"roundUpToPowerOfTwo",value:function(t){return Math.pow(2,Math.ceil(Math.log2(Math.max(1,t))))}},{key:"createTexture",value:function(){var t=this.gl;this.texture=t.createTexture(),t.activeTexture(t.TEXTURE0),t.bindTexture(t.TEXTURE_2D,this.texture),t.texImage2D(t.TEXTURE_2D,0,t.RGBA32F,this.textureWidth,this.textureHeight,0,t.RGBA,t.FLOAT,this.data),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MIN_FILTER,t.NEAREST),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MAG_FILTER,t.NEAREST),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_S,t.CLAMP_TO_EDGE),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_T,t.CLAMP_TO_EDGE),t.bindTexture(t.TEXTURE_2D,null)}},{key:"resize",value:function(t){if(!(t<=this.capacity)){var e=this.roundUpToPowerOfTwo(Math.ceil(t*ri)),n=this.gl,i=this.computeTextureDimensions(e),o=new Float32Array(i.width*i.height*4);o.set(this.data),this.texture&&n.deleteTexture(this.texture),this.data=o,this.capacity=e,this.textureWidth=i.width,this.textureHeight=i.height,this.createTexture(),this.dirty=!0,this.dirtyRangeStart=0,this.dirtyRangeEnd=this.nextIndex}}},{key:"allocate",value:function(t){var e=this.indexMap.get(t);if(e!==void 0)return e;var n;return this.freeIndices.length>0?n=this.freeIndices.pop():(n=this.nextIndex++,n>=this.capacity&&this.resize(n+1)),this.indexMap.set(t,n),n}},{key:"free",value:function(t){var e=this.indexMap.get(t);if(e!==void 0){this.indexMap.delete(t),this.freeIndices.push(e);for(var n=e*this.TEXELS_PER_ITEM*4,i=0;i<this.TEXELS_PER_ITEM*4;i++)this.data[n+i]=0;this.markDirty(e)}}},{key:"getIndex",value:function(t){var e;return(e=this.indexMap.get(t))!==null&&e!==void 0?e:-1}},{key:"has",value:function(t){return this.indexMap.has(t)}},{key:"markDirty",value:function(t){this.dirty=!0,this.dirtyRangeStart=Math.min(this.dirtyRangeStart,t),this.dirtyRangeEnd=Math.max(this.dirtyRangeEnd,t+1)}},{key:"upload",value:function(){if(!(!this.dirty||!this.texture)){var t=this.gl,e=this.textureWidth;t.activeTexture(t.TEXTURE0),t.bindTexture(t.TEXTURE_2D,this.texture);var n=this.dirtyRangeStart*this.TEXELS_PER_ITEM,i=Math.min(this.dirtyRangeEnd*this.TEXELS_PER_ITEM,this.capacity*this.TEXELS_PER_ITEM);if(n<i)for(var o=Math.floor(n/e),s=Math.floor((i-1)/e),l=o;l<=s;l++){var d=l*e,h=Math.min(d+e,this.capacity*this.TEXELS_PER_ITEM),u=Math.max(n,d),c=Math.min(i,h);if(u<c){var v=u-d,b=c-u,m=this.data.subarray(u*4,c*4);t.texSubImage2D(t.TEXTURE_2D,0,v,l,b,1,t.RGBA,t.FLOAT,m)}}t.bindTexture(t.TEXTURE_2D,null),this.dirty=!1,this.dirtyRangeStart=1/0,this.dirtyRangeEnd=-1}}},{key:"bind",value:function(t){var e=this.gl;e.activeTexture(e.TEXTURE0+t),e.bindTexture(e.TEXTURE_2D,this.texture)}},{key:"getTexture",value:function(){return this.texture}},{key:"getCapacity",value:function(){return this.capacity}},{key:"getTextureWidth",value:function(){return this.textureWidth}},{key:"getTexelsPerItem",value:function(){return this.TEXELS_PER_ITEM}},{key:"getCount",value:function(){return this.indexMap.size}},{key:"getHighWaterMark",value:function(){return this.nextIndex}},{key:"isDirty",value:function(){return this.dirty}},{key:"clear",value:function(){this.indexMap.clear(),this.freeIndices=[],this.nextIndex=0,this.data.fill(0),this.dirty=!0,this.dirtyRangeStart=0,this.dirtyRangeEnd=this.capacity}},{key:"kill",value:function(){this.texture&&(this.gl.deleteTexture(this.texture),this.texture=null),this.indexMap.clear(),this.freeIndices=[]}}])})();function fe(a){var r={},t={},e=0,n=M(a),i;try{for(n.s();!(i=n.n()).done;){var o=i.value,s=M(o.attributes),l;try{for(s.s();!(l=s.n()).done;){var d=l.value,h=d.name.replace(/^a_/,"");h in r||(r[h]=e,t[h]=d,e+=d.size)}}catch(u){s.e(u)}finally{s.f()}}}catch(u){n.e(u)}finally{n.f()}return{floatsPerItem:e,texelsPerItem:Math.max(1,Math.ceil(e/4)),offsets:r,specs:t}}var Rt=(function(a){function r(t,e,n){var i;return V(this,r),i=ee(this,r,[t,e.texelsPerItem,n]),i.floatsPerItem=e.floatsPerItem,i}return te(r,a),X(r,[{key:"updateAllAttributes",value:function(e,n){var i=this.indexMap.get(e);i===void 0&&(i=this.allocate(e));for(var o=i*this.TEXELS_PER_ITEM*4,s=Math.min(n.length,this.floatsPerItem),l=0;l<s;l++)this.data[o+l]=n[l];this.markDirty(i)}}])})(da);function At(a,r,t){for(var e=[],n=new Set,i=0;i<a.length;i++){var o=a[i],s=M(o.attributes),l;try{for(s.s();!(l=s.n()).done;){var d=l.value,h=d.name.replace(/^a_/,"");if(!n.has(h)){n.add(h);var u=r.offsets[h];if(u!==void 0){var c=t?.get(i);e.push({sourceKey:d.source||h,packedOffset:u,size:d.size,isColor:d.size===4&&!!d.normalized,defaultNum:typeof d.defaultValue=="number"?d.defaultValue:0,defaultColor:typeof d.defaultValue=="string"?d.defaultValue:"",sourceIndex:i,hasLifecycleHook:!!(c!=null&&c.getAttributeData)})}}}}catch(v){s.e(v)}finally{s.f()}}return e}function Dt(a,r,t,e,n,i,o){t.fill(0);for(var s=0,l=a.length;s<l;s++){var d=a[s],h=d.packedOffset,u=void 0;if(d.hasLifecycleHook){var c=i.get(d.sourceIndex-o);u=c.getAttributeData(r,d.sourceKey),u===null&&(u=r[d.sourceKey])}else u=r[d.sourceKey];if(d.isColor){var v=typeof u=="string"?u:d.defaultColor||e,b=Ze(v),m=Q(b,4),x=m[0],g=m[1],f=m[2],p=m[3];t[h]=x/255,t[h+1]=g/255,t[h+2]=f/255,t[h+3]=p/255*n}else if(d.size===1)t[h]=typeof u=="number"?u:d.defaultNum;else{var y=Array.isArray(u)?u:null;if(y)for(var T=0;T<d.size;T++){var _;t[h+T]=(_=y[T])!==null&&_!==void 0?_:0}}}}var st=["r","g","b","a"];function Cn(a,r){var t=a.offsets,e=a.specs,n=a.texelsPerItem,i=a.floatsPerItem,o=Object.keys(t);if(o.length===0||i===0)return{fetchCode:"",varyingAssignments:""};var s=r.varPrefix,l=r.baseTexelExpr,d=r.textureWidthUniform,h=r.textureSamplerUniform,u=[];u.push("  int ".concat(s,"BaseTexel = ").concat(l,";")),u.push("");for(var c=0;c<n;c++)u.push("  ivec2 ".concat(s,"Coord").concat(c," = ivec2((").concat(s,"BaseTexel + ").concat(c,") % ").concat(d,", (").concat(s,"BaseTexel + ").concat(c,") / ").concat(d,");")),u.push("  vec4 ".concat(s,"Texel").concat(c," = texelFetch(").concat(h,", ").concat(s,"Coord").concat(c,", 0);"));u.push("");for(var v=[],b=function(){var f=x[m],p=e[f],y=t[f],T=Math.floor(y/4),_=y%4,E="".concat(s,"Texel").concat(T),A="".concat(s,"Texel").concat(T+1);if(p.size===1)u.push("  float fetched_".concat(f," = ").concat(E,".").concat(st[_],";"));else if(p.size===4&&_===0)u.push("  vec4 fetched_".concat(f," = ").concat(E,";"));else{var R=_+p.size;if(R<=4){var L="vec".concat(p.size),F=st.slice(_,R).join("");u.push("  ".concat(L," fetched_").concat(f," = ").concat(E,".").concat(F,";"))}else{var C=p.size===4?"vec4":"vec".concat(p.size),P=st.slice(_).map(function(w){return"".concat(E,".").concat(w)}),D=st.slice(0,R-4).map(function(w){return"".concat(A,".").concat(w)}),k=[].concat(H(P),H(D)).join(", ");u.push("  ".concat(C," fetched_").concat(f," = ").concat(C,"(").concat(k,");"))}}v.push("  v_".concat(f," = fetched_").concat(f,";"))},m=0,x=o;m<x.length;m++)b();return{fetchCode:u.join(`
`),varyingAssignments:v.join(`
`)}}function ua(a,r,t){if(!(!r||t.type==="sampler2D"))switch(t.type){case"float":a.uniform1f(r,t.value);break;case"int":case"bool":a.uniform1i(r,t.value);break;case"vec2":a.uniform2fv(r,t.value);break;case"vec3":a.uniform3fv(r,t.value);break;case"vec4":a.uniform4fv(r,t.value);break;case"mat3":a.uniformMatrix3fv(r,!1,t.value);break;case"mat4":a.uniformMatrix4fv(r,!1,t.value);break}}var oi=S(S(S(S(S(S(S(S({},WebGL2RenderingContext.BOOL,1),WebGL2RenderingContext.BYTE,1),WebGL2RenderingContext.UNSIGNED_BYTE,1),WebGL2RenderingContext.SHORT,2),WebGL2RenderingContext.UNSIGNED_SHORT,2),WebGL2RenderingContext.INT,4),WebGL2RenderingContext.UNSIGNED_INT,4),WebGL2RenderingContext.FLOAT,4);function Ma(a){var r=a.match(/^(#version[^\n]*\n)/);return r?r[1]+`#define PICKING_MODE
`+a.slice(r[1].length):`#define PICKING_MODE
`+a}var Fe=(function(){function a(r,t,e){V(this,a),S(this,"floats",new Float32Array),S(this,"ints",new Uint32Array),S(this,"constantArray",new Float32Array),S(this,"capacity",0),S(this,"verticesCount",0),S(this,"bufferGeneration",0),S(this,"uploadedGeneration",new Map),S(this,"constantBufferGeneration",0),S(this,"uploadedConstantGeneration",new Map),S(this,"renderOffset",0),S(this,"renderCount",-1),S(this,"pickProgram",null);var n=this.getDefinition();if(this.VERTICES=n.VERTICES,this.VERTEX_SHADER_SOURCE=n.VERTEX_SHADER_SOURCE,this.FRAGMENT_SHADER_SOURCE=n.FRAGMENT_SHADER_SOURCE,this.UNIFORMS=n.UNIFORMS,this.ATTRIBUTES=n.ATTRIBUTES,this.METHOD=n.METHOD,this.CONSTANT_ATTRIBUTES="CONSTANT_ATTRIBUTES"in n?n.CONSTANT_ATTRIBUTES:[],this.CONSTANT_DATA="CONSTANT_DATA"in n?n.CONSTANT_DATA:[],this.isInstanced="CONSTANT_ATTRIBUTES"in n,this.ATTRIBUTES_ITEMS_COUNT=Nt(this.ATTRIBUTES),this.STRIDE=this.VERTICES*this.ATTRIBUTES_ITEMS_COUNT,this.renderer=e,this.normalProgram=this.getProgramInfo("normal",r,n.VERTEX_SHADER_SOURCE,n.FRAGMENT_SHADER_SOURCE,null),this.pickProgram=this.getProgramInfo("pick",r,Ma(n.VERTEX_SHADER_SOURCE),Ma(n.FRAGMENT_SHADER_SOURCE),null),this.isInstanced){var i=Nt(this.CONSTANT_ATTRIBUTES);if(this.CONSTANT_DATA.length!==this.VERTICES)throw new Error("Program: error while getting constant data (expected ".concat(this.VERTICES," items, received ").concat(this.CONSTANT_DATA.length," instead)"));this.constantArray=new Float32Array(this.CONSTANT_DATA.length*i);for(var o=0;o<this.CONSTANT_DATA.length;o++){var s=this.CONSTANT_DATA[o];if(s.length!==i)throw new Error("Program: error while getting constant data (one vector has ".concat(s.length," items instead of ").concat(i,")"));for(var l=0;l<s.length;l++)this.constantArray[o*i+l]=s[l]}this.STRIDE=this.ATTRIBUTES_ITEMS_COUNT}}return X(a,[{key:"kill",value:function(){wa(this.normalProgram),this.pickProgram&&wa(this.pickProgram)}},{key:"getProgramInfo",value:function(t,e,n,i,o){var s=e.createBuffer();if(s===null)throw new Error("Program: error while creating the WebGL buffer.");var l=oa(e,n),d=sa(e,i),h=la(e,[l,d]),u={};this.UNIFORMS.forEach(function(b){var m=e.getUniformLocation(h,b);m&&(u[b]=m)});var c={};this.ATTRIBUTES.forEach(function(b){c[b.name]=e.getAttribLocation(h,b.name)});var v;if(this.isInstanced&&(this.CONSTANT_ATTRIBUTES.forEach(function(b){c[b.name]=e.getAttribLocation(h,b.name)}),v=e.createBuffer(),v===null))throw new Error("Program: error while creating the WebGL constant buffer.");return{name:t,program:h,gl:e,frameBuffer:o,buffer:s,constantBuffer:v||{},uniformLocations:u,attributeLocations:c,isPicking:t==="pick",vertexShader:l,fragmentShader:d}}},{key:"bindProgram",value:function(t){var e=this,n=0,i=t.gl,o=t.buffer;this.isInstanced?(i.bindBuffer(i.ARRAY_BUFFER,t.constantBuffer),n=0,this.CONSTANT_ATTRIBUTES.forEach(function(s){return n+=e.bindAttribute(s,t,n,!1)}),this.uploadedConstantGeneration.get(t.constantBuffer)!==this.constantBufferGeneration&&(i.bufferData(i.ARRAY_BUFFER,this.constantArray,i.STATIC_DRAW),this.uploadedConstantGeneration.set(t.constantBuffer,this.constantBufferGeneration)),i.bindBuffer(i.ARRAY_BUFFER,t.buffer),n=this.renderOffset*this.ATTRIBUTES_ITEMS_COUNT*Float32Array.BYTES_PER_ELEMENT,this.ATTRIBUTES.forEach(function(s){return n+=e.bindAttribute(s,t,n,!0)}),this.uploadedGeneration.get(o)!==this.bufferGeneration&&(i.bufferData(i.ARRAY_BUFFER,this.floats,i.DYNAMIC_DRAW),this.uploadedGeneration.set(o,this.bufferGeneration))):(i.bindBuffer(i.ARRAY_BUFFER,o),n=0,this.ATTRIBUTES.forEach(function(s){return n+=e.bindAttribute(s,t,n)}),this.uploadedGeneration.get(o)!==this.bufferGeneration&&(i.bufferData(i.ARRAY_BUFFER,this.floats,i.DYNAMIC_DRAW),this.uploadedGeneration.set(o,this.bufferGeneration))),i.bindBuffer(i.ARRAY_BUFFER,null)}},{key:"unbindProgram",value:function(t){var e=this;this.isInstanced?(this.CONSTANT_ATTRIBUTES.forEach(function(n){return e.unbindAttribute(n,t,!1)}),this.ATTRIBUTES.forEach(function(n){return e.unbindAttribute(n,t,!0)})):this.ATTRIBUTES.forEach(function(n){return e.unbindAttribute(n,t)})}},{key:"bindAttribute",value:function(t,e,n,i){var o=oi[t.type];if(typeof o!="number")throw new Error('Program.bind: yet unsupported attribute type "'.concat(t.type,'"'));var s=e.attributeLocations[t.name],l=e.gl;if(s!==-1){l.enableVertexAttribArray(s);var d=this.isInstanced?(i?this.ATTRIBUTES_ITEMS_COUNT:Nt(this.CONSTANT_ATTRIBUTES))*Float32Array.BYTES_PER_ELEMENT:this.ATTRIBUTES_ITEMS_COUNT*Float32Array.BYTES_PER_ELEMENT;l.vertexAttribPointer(s,t.size,t.type,t.normalized||!1,d,n),this.isInstanced&&i&&l.vertexAttribDivisor(s,1)}return t.size*o}},{key:"unbindAttribute",value:function(t,e,n){var i=e.attributeLocations[t.name],o=e.gl;i!==-1&&(o.disableVertexAttribArray(i),this.isInstanced&&n&&o.vertexAttribDivisor(i,0))}},{key:"reallocate",value:function(t){t!==this.capacity&&(this.capacity=t,this.verticesCount=this.VERTICES*t,this.floats=new Float32Array(this.isInstanced?this.capacity*this.ATTRIBUTES_ITEMS_COUNT:this.verticesCount*this.ATTRIBUTES_ITEMS_COUNT),this.ints=new Uint32Array(this.floats.buffer),this.invalidateBuffers())}},{key:"invalidateBuffers",value:function(){this.bufferGeneration++,this.constantBufferGeneration++}},{key:"hasNothingToRender",value:function(){return this.verticesCount===0}},{key:"setTypedUniform",value:function(t,e){var n;ua(e.gl,(n=e.uniformLocations[t.name])!==null&&n!==void 0?n:null,t)}},{key:"renderProgram",value:function(t,e){var n=e.gl,i=e.program,o=e.isPicking;o?n.disable(n.BLEND):n.enable(n.BLEND),n.useProgram(i),this.setUniforms(t,e),this.drawWebGL(this.METHOD,e)}},{key:"render",value:function(t,e,n){if(!this.hasNothingToRender()){this.renderOffset=e??0,this.renderCount=n??-1;var i=this.normalProgram.gl;if(i.bindFramebuffer(i.FRAMEBUFFER,null),i.viewport(0,0,t.width*t.pixelRatio,t.height*t.pixelRatio),this.bindProgram(this.normalProgram),this.renderProgram(t,this.normalProgram),this.unbindProgram(this.normalProgram),this.pickProgram&&t.pickingFrameBuffer){var o=Math.ceil(t.width*t.pixelRatio/t.downSizingRatio),s=Math.ceil(t.height*t.pixelRatio/t.downSizingRatio);i.bindFramebuffer(i.FRAMEBUFFER,t.pickingFrameBuffer),i.viewport(0,0,o,s),this.bindProgram(this.pickProgram),this.renderProgram(t,this.pickProgram),this.unbindProgram(this.pickProgram),i.bindFramebuffer(i.FRAMEBUFFER,null),i.viewport(0,0,t.width*t.pixelRatio,t.height*t.pixelRatio)}}}},{key:"drawWebGL",value:function(t,e){var n=e.gl,i=this.renderCount>=0?this.renderCount:this.capacity;this.isInstanced?n.drawArraysInstanced(t,0,this.VERTICES,i):n.drawArrays(t,this.renderOffset*this.VERTICES,i*this.VERTICES)}}])})(),Tt=new Map,Ln=new Map,si=0;function li(a){var r=a.name,t=a.uniforms.filter(function(e){return e.type==="float"&&e.value!==void 0&&e.value!==0}).map(function(e){return"".concat(e.name.replace("u_",""),"=").concat(e.value)}).sort();return t.length>0&&(r+="#"+t.join("#")),r}function di(a){var r=li(a);if(!Tt.has(r)){var t={},e=M(a.uniforms),n;try{for(e.s();!(n=e.n()).done;){var i=n.value;i.type==="float"&&i.value!==void 0&&(t[i.name]=i.value)}}catch(o){e.e(o)}finally{e.f()}Tt.set(r,{shape:a,uniformValues:t,slug:r}),Ln.set(r,si++)}return r}function pt(a){var r;return(r=Ln.get(a))!==null&&r!==void 0?r:-1}function Pn(a){var r=[],t=new Set,e=new Set,n=/mat2 rotate2D\(float angle\)\s*\{[^}]+\}/,i=M(a),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;if(!e.has(s.name)){e.add(s.name);var l=s.glsl;n.test(l)&&(t.has("rotate2D")?l=l.replace(n,""):t.add("rotate2D")),r.push(l)}}}catch(d){i.e(d)}finally{i.f()}return r.join(`
`)}function ui(){return Pn(Array.from(Tt.values()).map(function(a){return a.shape}))}function hi(){var a=Array.from(Tt.entries());if(a.length===0)return`
float querySDF(int shapeId, vec2 uv, float size) {
  return length(uv) - size;
}
`;var r=a.map(function(t,e){var n=Q(t,2),i=n[0],o=n[1],s=o.shape,l=o.uniformValues,d=s.uniforms.filter(function(c){return c.type==="float"}),h=d.map(function(c){var v;return Y((v=l[c.name])!==null&&v!==void 0?v:0)}),u=h.length===0?"sdf_".concat(s.name,"(uv, size)"):"sdf_".concat(s.name,"(uv, size, ").concat(h.join(", "),")");return"    case ".concat(e,": return ").concat(u,"; // ").concat(i)}).join(`
`);return`
float querySDF(int shapeId, vec2 uv, float size) {
  switch (shapeId) {
`.concat(r,`
    default: return length(uv) - size;
  }
}
`)}function ha(a){return Pn(a)}function at(a){return H(new Map(a.flatMap(function(r){return r.uniforms}).map(function(r){return[r.name,r]})).values())}function ci(a,r){var t;if(a.length===0)return`
void queryNodeSDF(int shapeId, vec2 uv, float size) {
  context.sdf = length(uv) - size;
  context.inradiusFactor = 1.0;
}
`;var e=function(c){var v=c.uniforms.filter(function(m){return m.type==="float"}),b=v.map(function(m){var x;return Y((x=m.value)!==null&&x!==void 0?x:0)});return b.length===0?"sdf_".concat(c.name,"(uv, size)"):"sdf_".concat(c.name,"(uv, size, ").concat(b.join(", "),")")};if(a.length===1){var n,i=a[0];return`
void queryNodeSDF(int shapeId, vec2 uv, float size) {
  context.sdf = `.concat(e(i),`;
  context.inradiusFactor = `).concat(Y((n=i.inradiusFactor)!==null&&n!==void 0?n:1),`;
}
`)}var o=a.map(function(u,c){var v;return"    case ".concat(c,": // ").concat(u.name,`
      context.sdf = `).concat(e(u),`;
      context.inradiusFactor = `).concat(Y((v=u.inradiusFactor)!==null&&v!==void 0?v:1),`;
      break;`)}).join(`
`),s=a[0],l="",d="shapeId";if(r&&r.length>1){var h=r.map(function(u,c){return"    case ".concat(u,": return ").concat(c,"; // ").concat(a[c].name)}).join(`
`);l=`
int globalToLocalShapeId(int globalId) {
  switch (globalId) {
`.concat(h,`
    default: return 0;
  }
}
`),d="globalToLocalShapeId(shapeId)"}return"".concat(l,`
void queryNodeSDF(int shapeId, vec2 uv, float size) {
  switch (`).concat(d,`) {
`).concat(o,`
    default:
      context.sdf = `).concat(e(s),`;
      context.inradiusFactor = `).concat(Y((t=s.inradiusFactor)!==null&&t!==void 0?t:1),`;
  }
}
`)}var Re=2,ca=7,fi={below:0,above:1,left:2,right:3};function gi(){var a=`#version 300 es
precision highp float;

uniform mat3 u_matrix;
uniform vec2 u_resolution;
uniform float u_labelPixelSnapping;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform float u_pixelRatio;
uniform float u_labelMargin;
uniform float u_zoomLabelSizeRatio;

uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_nodeFrameTexture;
uniform int u_nodeFrameTextureWidth;

// Atlas size is fixed at 2048×2048 — matches AttachmentManager.ATLAS_SIZE.
uniform sampler2D u_atlasTexture;
const vec2 u_atlasSize = vec2(2048.0);

// Per-instance
in float a_nodeIndex;           // node-data texture index
in vec4 a_atlasRect;            // x, y, width, height in atlas pixels
in vec2 a_attachmentSize;       // attachment dimensions (CSS px)
in float a_positionMode;        // label position: 0=right 1=left 2=above 3=below 4=over
in float a_attachmentPlacement; // 0=below 1=above 2=left 3=right (relative to label)
in float a_labelWidth;          // label width (CSS px)
in float a_labelHeight;         // label height: font line box (CSS px)
in float a_textHeight;          // actual glyph height (CSS px)
in float a_labelAngle;          // label rotation angle (radians)

// Per-vertex (constant)
in vec2 a_quadCorner;           // [-1,-1], [1,-1], [-1,1], [1,1]

out vec2 v_texCoord;

`.concat(be,`
`).concat(Pe,`
`).concat(Ve,`
`).concat(An,`
`).concat(Zr,`

void main() {
  int nodeIdx = int(a_nodeIndex);

  // Node data: (x, y, size, shapeId).
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 nodePos = nodeData.xy;
  float nodeSize = nodeData.z;

  // Normalized edge distance from the shared frame texture (the frame-pass ran
  // the SDF search once; we just read the result).
  float edgeDist = readFrameTexel(u_nodeFrameTexture, u_nodeFrameTextureWidth, nodeIdx).r;

  // Per-node label rotation alignment: 0 = viewport, 1 = label turns with camera.
  float labelRotation = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).g;

  vec3 nodeClip = u_matrix * vec3(nodePos, 1.0);

  // Node radius in physical pixels (matches label/background).
  float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
  float nodeRadiusGraphSpace = nodeSize * u_correctionRatio / u_sizeRatio * 2.0;
  float nodeRadiusPixels = nodeRadiusGraphSpace * matrixScaleX * u_resolution.x / 2.0;

  // CSS-px inputs -> physical px, scaled by the zoom-dependent label ratio, so
  // the attachment stays glued to the label box exactly as the label scales.
  float zoomScale = u_zoomLabelSizeRatio;
  vec2 labelHalf = vec2(a_labelWidth, a_labelHeight) * 0.5 * zoomScale * u_pixelRatio;
  vec2 attachHalf = a_attachmentSize * 0.5 * zoomScale * u_pixelRatio;
  float gap = `).concat(Re.toFixed(1),` * zoomScale * u_pixelRatio;
  float labelMargin = u_labelMargin * zoomScale * u_pixelRatio;

  // Graph-aligned labels add the camera angle so the attachment orbits with the box.
  mat2 labelRotMat = rotate2D(a_labelAngle - labelRotation * u_cameraAngle);

  // Label box center relative to the node center (pre-rotation). The shape-aware
  // edge distance comes from the frame texture, so placement matches the label.
  vec2 boxCenter = vec2(0.0);
  if (a_positionMode < 4.0) {
    float labelStart = nodeRadiusPixels * edgeDist + labelMargin;
    float textHalf = a_textHeight * 0.5 * zoomScale * u_pixelRatio;
    boxCenter = labelBoxCenter(a_positionMode, labelStart, labelHalf, textHalf);
  }

  // Horizontal anchor of below/above attachments tracks the label position, so
  // the attachment hangs from the label edge nearest the node (or is centered
  // when the label itself is node-centered): right->left, left->right, else center.
  float anchorX = 0.0;
  if (a_positionMode < 0.5) anchorX = -labelHalf.x + attachHalf.x;       // right label
  else if (a_positionMode < 1.5) anchorX = labelHalf.x - attachHalf.x;   // left label

  // Attachment center relative to the box (pre-rotation, Y-down). This offset
  // depends only on the box, the gap and the attachment size — never the shape.
  vec2 attachCenter;
  if (a_attachmentPlacement < 0.5) {
    // below
    attachCenter = boxCenter + vec2(anchorX, labelHalf.y + gap + attachHalf.y);
  } else if (a_attachmentPlacement < 1.5) {
    // above
    attachCenter = boxCenter + vec2(anchorX, -(labelHalf.y + gap + attachHalf.y));
  } else if (a_attachmentPlacement < 2.5) {
    // left, top-aligned
    attachCenter = boxCenter + vec2(-(labelHalf.x + gap + attachHalf.x), -labelHalf.y + attachHalf.y);
  } else {
    // right, top-aligned
    attachCenter = boxCenter + vec2(labelHalf.x + gap + attachHalf.x, -labelHalf.y + attachHalf.y);
  }

  // Rotate the whole assembly by the label angle, around the node center.
  vec2 rotatedCenter = labelRotMat * attachCenter;
  vec2 cornerOffset = labelRotMat * (a_quadCorner * attachHalf);

  // Node center in screen px (Y-down).
  vec2 nodeScreen = vec2(
    (nodeClip.x + 1.0) * u_resolution.x,
    (1.0 - nodeClip.y) * u_resolution.y
  ) * 0.5;

  // Snap node center to the pixel grid so label/backdrop/attachment move as one.
  vec2 snapDelta = (round(nodeScreen) - nodeScreen) * u_labelPixelSnapping;

  // Snap the quad's top-left to integer pixels so atlas texels map 1:1.
  vec2 centerScreen = nodeScreen + rotatedCenter + snapDelta;
  vec2 topLeft = centerScreen - attachHalf;
  topLeft = mix(topLeft, round(topLeft), u_labelPixelSnapping);
  centerScreen = topLeft + attachHalf;

  vec2 vertexScreen = centerScreen + cornerOffset;
  gl_Position = vec4(
    vertexScreen.x * 2.0 / u_resolution.x - 1.0,
    1.0 - vertexScreen.y * 2.0 / u_resolution.y,
    0.0, 1.0
  );

  vec2 texOrigin = a_atlasRect.xy / u_atlasSize;
  vec2 texSize = a_atlasRect.zw / u_atlasSize;
  vec2 uv = (a_quadCorner + 1.0) / 2.0;
  v_texCoord = texOrigin + uv * texSize;
}
`);return a}var vi=`#version 300 es
precision highp float;

uniform sampler2D u_atlasTexture;

in vec2 v_texCoord;

layout(location = 0) out vec4 fragColor;
#ifdef PICKING_MODE
layout(location = 1) out vec4 pickColor;
#endif

void main() {
  // Canvas textures are premultiplied; output directly for (ONE, 1-SRC_ALPHA) blending
  vec4 color = texture(u_atlasTexture, v_texCoord);
  if (color.a < 0.01) discard;
  fragColor = color;
#ifdef PICKING_MODE
  pickColor = vec4(0.0); // Attachments are not pickable
#endif
}
`;function mi(a,r,t,e){var n,i,o=e.label,s=o===void 0?{}:o,l=(n=s.margin)!==null&&n!==void 0?n:et,d=(i=s.zoomToLabelSizeRatioFunction)!==null&&i!==void 0?i:function(){return 1},h=gi(),u=vi,c=(function(v){function b(){var m;V(this,b);for(var x=arguments.length,g=new Array(x),f=0;f<x;f++)g[f]=arguments[f];return m=ee(this,b,[].concat(g)),S(m,"totalCount",0),S(m,"bufferCapacity",0),m}return te(b,v),X(b,[{key:"getDefinition",value:function(){var x=WebGL2RenderingContext,g=x.FLOAT,f=x.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:h,FRAGMENT_SHADER_SOURCE:u,METHOD:f,UNIFORMS:["u_matrix","u_resolution","u_labelPixelSnapping","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_pixelRatio","u_labelMargin","u_zoomLabelSizeRatio","u_nodeDataTexture","u_nodeDataTextureWidth","u_nodeFrameTexture","u_nodeFrameTextureWidth","u_atlasTexture"],ATTRIBUTES:[{name:"a_nodeIndex",size:1,type:g},{name:"a_atlasRect",size:4,type:g},{name:"a_attachmentSize",size:2,type:g},{name:"a_positionMode",size:1,type:g},{name:"a_attachmentPlacement",size:1,type:g},{name:"a_labelWidth",size:1,type:g},{name:"a_labelHeight",size:1,type:g},{name:"a_textHeight",size:1,type:g},{name:"a_labelAngle",size:1,type:g}],CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:g}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"processAttachment",value:function(x,g){var f=this.floats,p=x*this.STRIDE;f[p++]=g.nodeIndex,f[p++]=g.atlasX,f[p++]=g.atlasY,f[p++]=g.atlasW,f[p++]=g.atlasH,f[p++]=g.attachWidth,f[p++]=g.attachHeight,f[p++]=g.positionMode,f[p++]=g.attachmentPlacement,f[p++]=g.labelWidth,f[p++]=g.labelHeight,f[p++]=g.textHeight,f[p++]=g.labelAngle}},{key:"setUniforms",value:function(x,g){var f=g.gl,p=g.uniformLocations;f.uniformMatrix3fv(p.u_matrix,!1,x.matrix),f.uniform2f(p.u_resolution,x.width*x.pixelRatio,x.height*x.pixelRatio),f.uniform1f(p.u_labelPixelSnapping,x.labelPixelSnapping),f.uniform1f(p.u_sizeRatio,x.sizeRatio),f.uniform1f(p.u_correctionRatio,x.correctionRatio),f.uniform1f(p.u_cameraAngle,x.cameraAngle),f.uniform1f(p.u_pixelRatio,x.pixelRatio),f.uniform1f(p.u_labelMargin,b.labelMargin),f.uniform1f(p.u_zoomLabelSizeRatio,1/d(x.zoomRatio)),f.uniform1i(p.u_nodeDataTexture,x.nodeDataTextureUnit),f.uniform1i(p.u_nodeDataTextureWidth,x.nodeDataTextureWidth),f.uniform1i(p.u_nodeFrameTexture,x.nodeFrameTextureUnit),f.uniform1i(p.u_nodeFrameTextureWidth,x.nodeFrameTextureWidth),f.uniform1i(p.u_atlasTexture,ca)}},{key:"reallocateAttachments",value:function(x){this.totalCount=x,x>this.bufferCapacity&&(this.bufferCapacity=Math.max(x,Math.ceil(this.bufferCapacity*1.5)||10),ne(b,"reallocate",this)([this.bufferCapacity]))}},{key:"hasNothingToRender",value:function(){return this.totalCount===0}},{key:"drawWebGL",value:function(x,g){var f=g.gl;this.totalCount!==0&&f.drawArraysInstanced(x,0,this.VERTICES,this.totalCount)}}])})(Fe);return S(c,"labelMargin",l),new c(a,r,t)}function pi(a){var r,t,e=a.shapes,n=a.shapeGlobalIds,i=e.length===1?"float inradiusFactor = ".concat(Y((r=e[0].inradiusFactor)!==null&&r!==void 0?r:1),";"):"float inradiusFactor = ".concat(Y((t=e[0].inradiusFactor)!==null&&t!==void 0?t:1),`;
  switch (int(shapeId)) {
`).concat(e.map(function(s,l){var d,h=n?n[l]:l;return"    case ".concat(h,": inradiusFactor = ").concat(Y((d=s.inradiusFactor)!==null&&d!==void 0?d:1),"; break;")}).join(`
`),`
    default: break;
  }`),o=`#version 300 es

in float a_nodeIndex;
in float a_labelWidth;
in float a_labelHeight;
in float a_textHeight;
in float a_positionMode;
in float a_labelAngle;
in vec4 a_backdropColor;
in vec4 a_backdropShadowColor;
in float a_backdropShadowBlur;
in float a_backdropPadding;
in vec4 a_backdropBorderColor;
in vec4 a_backdropExtra; // [borderWidth, cornerRadius, labelPadding, area]
in vec2 a_labelBoxOffset;
in vec2 a_quadCorner;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform vec2 u_resolution;
uniform float u_pixelRatio;
uniform float u_labelMargin;
uniform float u_zoomLabelSizeRatio;
uniform float u_labelPixelSnapping;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_nodeFrameTexture;
uniform int u_nodeFrameTextureWidth;

out vec2 v_uv;
out vec2 v_nodeCenter;
out float v_nodeRadius;
out vec2 v_labelCenter;
out vec2 v_labelHalfSize;
out float v_aaWidth;
out float v_shapeId;
out float v_nodeRotation;
out float v_labelAngle;
out vec4 v_backdropColor;
out vec4 v_backdropShadowColor;
out float v_backdropShadowBlur;
out float v_backdropPadding;
out vec4 v_backdropBorderColor;
out float v_backdropBorderWidth;
out float v_backdropCornerRadius;
out float v_backdropArea;

`.concat(be,`
`).concat(Pe,`
`).concat(Ve,`

void main() {
  int nodeIdx = int(a_nodeIndex);

  // Node data: (x, y, size, shapeId). shapeId (global) is forwarded to the
  // fragment shader, which keeps the shape SDF for the outline.
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 nodePosition = nodeData.xy;
  float nodeSize = nodeData.z;
  float shapeId = nodeData.w;

  // Per-node rotation alignment (0 = viewport, 1 = graph). nodeRotation drives
  // the fragment's shape outline; labelRotation turns the label box with camera.
  vec4 nodeFlags = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  float nodeRotation = nodeFlags.r;
  float labelRotation = nodeFlags.g;
  v_nodeRotation = nodeRotation;

  `).concat(En,`
  // CSS pixel attributes are multiplied by u_pixelRatio to match nodeRadiusPixels,
  // which is already in physical pixels (nodeRadiusNDC * u_resolution.x / 2.0).
  float padding = a_backdropPadding * u_pixelRatio;
  float shadowBlur = a_backdropShadowBlur * u_pixelRatio;
  // Unpack a_backdropExtra: [borderWidth, cornerRadius, labelPadding, area]
  float borderWidth = a_backdropExtra.x * u_pixelRatio;
  float cornerRadius = a_backdropExtra.y * u_pixelRatio;
  float labelPad = a_backdropExtra.z * u_pixelRatio;
  float backdropArea = a_backdropExtra.w;
  // Use 2x shadowBlur so the Gaussian fully decays before the quad edge
  float totalExpansion = shadowBlur * 2.0 + borderWidth;
  float enlargedRadius = nodeRadiusPixels + padding;

  // Circumscribed radius for the quad bounds. Non-circular shapes reach past
  // their inradius out to their circumradius (= enlargedRadius / inradiusFactor),
  // in any direction once rotated. The axis-aligned quad must contain that, or
  // the fill/shadow gets clipped (square corners, triangle tip, etc.).
  `).concat(i,`
  float boundRadius = enlargedRadius / inradiusFactor;

  // Apply zoom-dependent label size scaling
  float zoomScale = u_zoomLabelSizeRatio;
  float labelW = a_labelWidth * zoomScale * u_pixelRatio;
  float labelH = a_labelHeight * zoomScale * u_pixelRatio;
  float labelMargin = u_labelMargin * zoomScale * u_pixelRatio;

  // Only apply labelPad when a label is actually present
  float effectiveLabelPad = labelW > 0.0 ? labelPad : 0.0;
  vec2 labelHalfSize = vec2(labelW * 0.5 + effectiveLabelPad, labelH * 0.5 + effectiveLabelPad);
  vec2 labelOffset = vec2(0.0);

  // Effective label angle: intrinsic angle plus the camera angle when the label
  // is graph-aligned, so the box orbits the node in lockstep with the frame-pass.
  float labelAngle = a_labelAngle - labelRotation * u_cameraAngle;
  float la_c = cos(labelAngle);
  float la_s = sin(labelAngle);
  mat2 labelRotMat = mat2(la_c, -la_s, la_s, la_c);

  vec3 nodeClip = u_matrix * vec3(nodePosition, 1.0);
  vec2 snapDelta = vec2(0.0);

  if (labelW > 0.0) {
    // labelW > 0.0 means this node's label is displayed, so the frame-pass wrote
    // its edge distance this frame.
    float edgeDistPixels = nodeRadiusPixels * readFrameTexel(u_nodeFrameTexture, u_nodeFrameTextureWidth, nodeIdx).r;
    // labelMargin matches the label shader's margin (gap from node edge to text)
    float labelStart = edgeDistPixels + labelMargin;
    // Above/below center on the actual glyph height, not the font line box, so
    // the box stays aligned with the rendered text (matches labelBoxCenter()).
    float textHalf = a_textHeight * zoomScale * u_pixelRatio * 0.5;

    // Snap node center to pixel grid so label/backdrop/attachment move as a unit
    vec2 nodeScreen = vec2(
      (nodeClip.x + 1.0) * u_resolution.x,
      (1.0 - nodeClip.y) * u_resolution.y
    ) * 0.5;
    snapDelta = (round(nodeScreen) - nodeScreen) * u_labelPixelSnapping;

    if (a_positionMode < 0.5) {
      // Right: box spans from node center to text end + padding
      float boxRightEdge = labelStart + labelW + labelPad;
      labelOffset = vec2(boxRightEdge * 0.5, 0.0);
      labelHalfSize.x = boxRightEdge * 0.5;
    } else if (a_positionMode < 1.5) {
      // Left: mirror of right
      float boxLeftEdge = labelStart + labelW + labelPad;
      labelOffset = vec2(-boxLeftEdge * 0.5, 0.0);
      labelHalfSize.x = boxLeftEdge * 0.5;
    } else if (a_positionMode < 2.5) {
      // Above: text bottom at labelStart, centered horizontally
      labelOffset = vec2(0.0, -(labelStart + textHalf));
    } else if (a_positionMode < 3.5) {
      // Below: text top at labelStart, centered horizontally
      labelOffset = vec2(0.0, labelStart + textHalf);
    }
    // over (>=4): labelOffset stays (0,0) — text centered on the node.

    // The attachment-cover shift is in label space (like the attachment itself),
    // so rotate it together with the position offset — otherwise the box drifts
    // off the attachment as the label angle grows.
    labelOffset = labelRotMat * (labelOffset + a_labelBoxOffset * zoomScale * u_pixelRatio);
  }

  // For node-only mode, zero out label dimensions
  if (backdropArea > 0.5 && backdropArea < 1.5) {
    labelHalfSize = vec2(0.0);
    labelOffset = vec2(0.0);
  }

  vec2 minBound, maxBound;

  bool hasLabelBounds = labelW > 0.0 && (backdropArea > 1.5 || backdropArea < 0.5);

  if (hasLabelBounds) {
    // Union with label bounds (area=both) or label-only bounds (area=label)
    vec2 labelMin, labelMax;

    if (a_labelAngle != 0.0) {
      vec2 corner1 = labelOffset + labelRotMat * vec2(-labelHalfSize.x, -labelHalfSize.y);
      vec2 corner2 = labelOffset + labelRotMat * vec2(labelHalfSize.x, -labelHalfSize.y);
      vec2 corner3 = labelOffset + labelRotMat * vec2(labelHalfSize.x, labelHalfSize.y);
      vec2 corner4 = labelOffset + labelRotMat * vec2(-labelHalfSize.x, labelHalfSize.y);
      labelMin = min(min(corner1, corner2), min(corner3, corner4));
      labelMax = max(max(corner1, corner2), max(corner3, corner4));
    } else {
      labelMin = labelOffset - labelHalfSize;
      labelMax = labelOffset + labelHalfSize;
    }

    if (backdropArea > 1.5) {
      // Label-only: bounds from label rect only
      minBound = labelMin - totalExpansion;
      maxBound = labelMax + totalExpansion;
    } else {
      // Both: union of node + label
      minBound = min(-vec2(boundRadius), labelMin) - totalExpansion;
      maxBound = max(vec2(boundRadius), labelMax) + totalExpansion;
    }
  } else {
    // Node-only or no visible label
    float totalRadius = boundRadius + totalExpansion;
    minBound = -vec2(totalRadius);
    maxBound = vec2(totalRadius);
  }

  vec2 quadSize = maxBound - minBound;
  vec2 quadCenter = (minBound + maxBound) * 0.5;

  vec2 localPos = quadCenter + a_quadCorner * quadSize * 0.5 + snapDelta;
  vec2 ndcOffset = localPos * 2.0 / u_resolution;
  ndcOffset.y = -ndcOffset.y;

  gl_Position = vec4(nodeClip.xy + ndcOffset, 0.0, 1.0);

  v_uv = localPos;
  v_nodeCenter = vec2(0.0);
  v_nodeRadius = nodeRadiusPixels;
  v_labelCenter = labelOffset;
  v_labelHalfSize = labelHalfSize;
  v_aaWidth = 1.0;
  v_shapeId = shapeId;
  v_labelAngle = labelAngle;
  v_backdropColor = a_backdropColor;
  v_backdropShadowColor = a_backdropShadowColor;
  v_backdropShadowBlur = a_backdropShadowBlur;
  v_backdropPadding = a_backdropPadding;
  v_backdropBorderColor = a_backdropBorderColor;
  v_backdropBorderWidth = borderWidth;
  v_backdropCornerRadius = cornerRadius;
  v_backdropArea = backdropArea;
}
`);return o}function bi(a){var r=a.shapes,t=a.shapeGlobalIds,e=ha(r),n=at(r).map(function(g){return"uniform ".concat(g.type," ").concat(g.name,";")}).join(`
`),i;if(r.length===1){var o=r[0],s=o.uniforms.filter(function(g){return g.type==="float"}),l=s.map(function(g){var f;return Y((f=g.value)!==null&&f!==void 0?f:0)}),d=l.length>0?"sdf_".concat(o.name,"(nodeUV, 1.0, ").concat(l.join(", "),")"):"sdf_".concat(o.name,"(nodeUV, 1.0)");i="float nodeSdfNormalized = ".concat(d,";")}else{var h=r.map(function(g,f){var p=g.uniforms.filter(function(E){return E.type==="float"}),y=p.map(function(E){var A;return Y((A=E.value)!==null&&A!==void 0?A:0)}),T=y.length>0?"sdf_".concat(g.name,"(nodeUV, 1.0, ").concat(y.join(", "),")"):"sdf_".concat(g.name,"(nodeUV, 1.0)"),_=t?t[f]:f;return"    case ".concat(_,": nodeSdfNormalized = ").concat(T,"; break;")}).join(`
`),u=r[0],c=u.uniforms.filter(function(g){return g.type==="float"}),v=c.map(function(g){var f;return Y((f=g.value)!==null&&f!==void 0?f:0)}),b=v.length>0?"sdf_".concat(u.name,"(nodeUV, 1.0, ").concat(v.join(", "),")"):"sdf_".concat(u.name,"(nodeUV, 1.0)");i=`float nodeSdfNormalized;
  int shapeId = int(v_shapeId);
  switch (shapeId) {
`.concat(h,`
    default: nodeSdfNormalized = `).concat(b,`;
  }`)}var m=`float effectiveRadius = max(enlargedRadius - cornerRadius, 0.01);
  float ca = u_cameraAngle * v_nodeRotation;
  float ca_c = cos(ca);
  float ca_s = sin(ca);
  vec2 rotatedScreenUV = mat2(ca_c, -ca_s, ca_s, ca_c) * screenUV;
  vec2 nodeUV = vec2(rotatedScreenUV.x, -rotatedScreenUV.y) / effectiveRadius;`,x=`#version 300 es
precision highp float;

in vec2 v_uv;
in vec2 v_nodeCenter;
in float v_nodeRadius;
in vec2 v_labelCenter;
in vec2 v_labelHalfSize;
in float v_aaWidth;
in float v_shapeId;
in float v_nodeRotation;
in float v_labelAngle;
in vec4 v_backdropColor;
in vec4 v_backdropShadowColor;
in float v_backdropShadowBlur;
in float v_backdropPadding;
in vec4 v_backdropBorderColor;
in float v_backdropBorderWidth;
in float v_backdropCornerRadius;
in float v_backdropArea;

uniform float u_cameraAngle;
`.concat(n,`

layout(location = 0) out vec4 fragColor;
layout(location = 1) out vec4 fragPicking;

`).concat(e,`
`).concat($r,`
`).concat(Qr,`
`).concat(Jr,`
`).concat(ei,`

void main() {
  vec4 backdropColor = v_backdropColor;
  vec4 shadowColor = v_backdropShadowColor;
  float shadowBlur = v_backdropShadowBlur;
  float padding = v_backdropPadding;
  vec4 borderColor = v_backdropBorderColor;
  float borderWidth = v_backdropBorderWidth;
  float cornerRadius = v_backdropCornerRadius;

  float enlargedRadius = v_nodeRadius + padding;
  vec2 screenUV = v_uv - v_nodeCenter;
  `).concat(m,`

  // Query the correct shape SDF based on shapeId
  `).concat(i,`
  float nodeSdfPixels = nodeSdfNormalized * effectiveRadius - cornerRadius;

  // Label SDF with optional corner radius and rotation
  float labelSdfPixels;
  if (v_labelHalfSize.x > 0.0) {
    vec2 labelP = v_uv - v_labelCenter;
    labelSdfPixels = sdfRoundedRotatedBox(labelP, v_labelHalfSize, v_labelAngle, cornerRadius);
  } else {
    labelSdfPixels = 10000.0;
  }

  // Select area: 0=both, 1=node, 2=label
  float combinedSdf;
  if (v_backdropArea > 1.5) {
    combinedSdf = labelSdfPixels;
  } else if (v_backdropArea > 0.5) {
    combinedSdf = nodeSdfPixels;
  } else {
    combinedSdf = min(nodeSdfPixels, labelSdfPixels);
  }

  // Fill + border composite
  float outerEdge = smoothstep(v_aaWidth, -v_aaWidth, combinedSdf);
  vec4 background;
  if (borderWidth > 0.5) {
    float innerEdge = smoothstep(v_aaWidth, -v_aaWidth, combinedSdf + borderWidth);
    float fillAlpha = innerEdge * backdropColor.a;
    vec4 fill = vec4(backdropColor.rgb * fillAlpha, fillAlpha);
    float borderAlpha = (outerEdge - innerEdge) * borderColor.a;
    vec4 border = vec4(borderColor.rgb * borderAlpha, borderAlpha);
    background = fill + border * (1.0 - fill.a);
  } else {
    float fillAlpha = outerEdge * backdropColor.a;
    background = vec4(backdropColor.rgb * fillAlpha, fillAlpha);
  }

  // Gaussian-like shadow falloff (mimics canvas shadowBlur)
  vec4 shadow = vec4(0.0);
  float sigma = shadowBlur / 2.5;
  if (sigma > 0.001) {
    float shadowDist = max(0.0, combinedSdf);
    float shadowAlpha = exp(-(shadowDist * shadowDist) / (2.0 * sigma * sigma)) * shadowColor.a;
    shadow = vec4(shadowColor.rgb * shadowAlpha, shadowAlpha);
  }

  fragColor = background + shadow * (1.0 - background.a);
  fragPicking = vec4(0.0);
}
`);return x}function xi(a){var r=["u_matrix","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_resolution","u_pixelRatio","u_labelMargin","u_zoomLabelSizeRatio","u_labelPixelSnapping","u_nodeDataTexture","u_nodeDataTextureWidth","u_nodeFrameTexture","u_nodeFrameTextureWidth"],t=M(at(a)),e;try{for(t.s();!(e=t.n()).done;){var n=e.value;r.includes(n.name)||r.push(n.name)}}catch(i){t.e(i)}finally{t.f()}return r}function yi(a){return{vertexShader:pi(a),fragmentShader:bi(a),uniforms:xi(a.shapes)}}function Ti(a,r,t,e){var n,i,o=e.label,s=o===void 0?{}:o,l=e.shapes,d=e.shapeGlobalIds;if(l.length===0)throw new Error("createBackdropProgram: at least one shape must be provided in 'shapes'");var h=(n=s.margin)!==null&&n!==void 0?n:5,u=(i=s.zoomToLabelSizeRatioFunction)!==null&&i!==void 0?i:function(){return 1},c={shapes:l,shapeGlobalIds:d},v=yi(c),b=(function(m){function x(){var g;V(this,x);for(var f=arguments.length,p=new Array(f),y=0;y<f;y++)p[y]=arguments[y];return g=ee(this,x,[].concat(p)),S(g,"totalBackdropCount",0),S(g,"bufferCapacity",0),g}return te(x,m),X(x,[{key:"getDefinition",value:function(){var f=WebGL2RenderingContext,p=f.FLOAT,y=f.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:v.vertexShader,FRAGMENT_SHADER_SOURCE:v.fragmentShader,METHOD:y,UNIFORMS:v.uniforms,ATTRIBUTES:[{name:"a_nodeIndex",size:1,type:p},{name:"a_labelWidth",size:1,type:p},{name:"a_labelHeight",size:1,type:p},{name:"a_textHeight",size:1,type:p},{name:"a_positionMode",size:1,type:p},{name:"a_labelAngle",size:1,type:p},{name:"a_backdropColor",size:4,type:p},{name:"a_backdropShadowColor",size:4,type:p},{name:"a_backdropShadowBlur",size:1,type:p},{name:"a_backdropPadding",size:1,type:p},{name:"a_backdropBorderColor",size:4,type:p},{name:"a_backdropExtra",size:4,type:p},{name:"a_labelBoxOffset",size:2,type:p}],CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:p}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"processBackdrop",value:function(f,p){var y=this.floats,T=this.STRIDE,_=f*T;y[_++]=p.nodeIndex,y[_++]=p.labelWidth,y[_++]=p.labelHeight,y[_++]=p.textHeight,y[_++]=$e[p.position],y[_++]=p.labelAngle,y[_++]=p.backdropColor[0],y[_++]=p.backdropColor[1],y[_++]=p.backdropColor[2],y[_++]=p.backdropColor[3],y[_++]=p.backdropShadowColor[0],y[_++]=p.backdropShadowColor[1],y[_++]=p.backdropShadowColor[2],y[_++]=p.backdropShadowColor[3],y[_++]=p.backdropShadowBlur,y[_++]=p.backdropPadding,y[_++]=p.backdropBorderColor[0],y[_++]=p.backdropBorderColor[1],y[_++]=p.backdropBorderColor[2],y[_++]=p.backdropBorderColor[3],y[_++]=p.backdropBorderWidth,y[_++]=p.backdropCornerRadius,y[_++]=p.backdropLabelPadding,y[_++]=p.backdropArea,y[_++]=p.labelBoxOffset[0],y[_++]=p.labelBoxOffset[1]}},{key:"setUniforms",value:function(f,p){var y=p.gl,T=p.uniformLocations;y.uniformMatrix3fv(T.u_matrix,!1,f.matrix),y.uniform1f(T.u_sizeRatio,f.sizeRatio),y.uniform1f(T.u_correctionRatio,f.correctionRatio),y.uniform1f(T.u_cameraAngle,f.cameraAngle),y.uniform2f(T.u_resolution,f.width*f.pixelRatio,f.height*f.pixelRatio),y.uniform1f(T.u_pixelRatio,f.pixelRatio),y.uniform1f(T.u_labelMargin,x.labelMargin),y.uniform1f(T.u_zoomLabelSizeRatio,1/u(f.zoomRatio)),y.uniform1f(T.u_labelPixelSnapping,f.labelPixelSnapping),y.uniform1i(T.u_nodeDataTexture,f.nodeDataTextureUnit),y.uniform1i(T.u_nodeDataTextureWidth,f.nodeDataTextureWidth),y.uniform1i(T.u_nodeFrameTexture,f.nodeFrameTextureUnit),y.uniform1i(T.u_nodeFrameTextureWidth,f.nodeFrameTextureWidth);var _=M(at(l)),E;try{for(_.s();!(E=_.n()).done;){var A=E.value;this.setTypedUniform(A,p)}}catch(R){_.e(R)}finally{_.f()}}},{key:"hasNothingToRender",value:function(){return this.totalBackdropCount===0}},{key:"drawWebGL",value:function(f,p){var y=p.gl;this.totalBackdropCount!==0&&(this.isInstanced?y.drawArraysInstanced(f,0,this.VERTICES,this.totalBackdropCount):y.drawArrays(f,0,this.totalBackdropCount*this.VERTICES))}},{key:"reallocate",value:function(f){this.totalBackdropCount=f,f>this.bufferCapacity&&(this.bufferCapacity=Math.max(f,Math.ceil(this.bufferCapacity*1.5)||10),ne(x,"reallocate",this)([this.bufferCapacity]))}}])})(Fe);return S(b,"labelMargin",h),new b(a,r,t)}function _i(a,r){var t=new Set(["u_matrix","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_pickingPadding","u_nodeDataTexture","u_layerAttributeTexture"]),e=new Set,n=a.flatMap(function(c){return c.uniforms}).filter(function(c){return t.has(c.name)||e.has(c.name)?!1:(e.add(c.name),!0)}).map(function(c){return"uniform ".concat(c.type," ").concat(c.name,";")}).join(`
`),i=r.flatMap(function(c){return c.uniforms}).filter(function(c){return t.has(c.name)||e.has(c.name)?!1:(e.add(c.name),!0)}).map(function(c){return"uniform ".concat(c.type," ").concat(c.name,";")}).join(`
`),o=new Set,s=r.flatMap(function(c){return c.attributes}).filter(function(c){var v=c.name.replace(/^a_/,"");return o.has(v)?!1:(o.add(v),!0)}).map(function(c){var v=c.name.replace(/^a_/,""),b=c.size===1?"float":"vec".concat(c.size);return"out ".concat(b," v_").concat(v,";")}).join(`
`),l=Cn(fe(r),{varPrefix:"layer",baseTexelExpr:"nodeIdx * u_layerAttributeTexelsPerNode",textureWidthUniform:"u_layerAttributeTextureWidth",textureSamplerUniform:"u_layerAttributeTexture"}),d=l.fetchCode,h=l.varyingAssignments,u=`#version 300 es

// Standard node attributes (per instance) - minimal buffer usage
in float a_nodeIndex;  // Index into node data texture AND layer attribute texture
in vec4 a_id;          // Node ID for picking

// Constant attributes (per vertex, same for all instances)
in vec2 a_quadCorner;  // (-1,-1), (1,-1), (1,1), (-1,1) for quad corners

// Standard uniforms
uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
#ifdef PICKING_MODE
uniform float u_pickingPadding;
#endif
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;

// Layer attribute texture uniforms
uniform sampler2D u_layerAttributeTexture;
uniform int u_layerAttributeTextureWidth;
uniform int u_layerAttributeTexelsPerNode;

`.concat(n,`
`).concat(i,`

// Standard varyings
out vec2 v_uv;                    // Normalized coordinates [-1, 1]
out vec4 v_id;
out float v_antialiasingWidth;    // Width for antialiasing in UV space
out float v_pixelSize;            // Node size in pixels (for pixel-mode borders)
out float v_pixelToUV;            // Conversion factor: multiply by this to convert screen pixels to UV units
out float v_shapeId;              // Shape ID for multi-shape programs

// Layer varyings
`).concat(s,`

// Node-data fetch helpers (geometry texel + rotation-flags texel)
`).concat(be,`
`).concat(Pe,`

void main() {
  // Fetch node geometry: vec4(x, y, size, shapeId).
  int nodeIdx = int(a_nodeIndex);
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 a_position = nodeData.xy;
  float a_size = nodeData.z;
  v_shapeId = nodeData.w;  // Pass shape ID to fragment shader

  // Per-node rotation alignment: 0 = viewport (screen-upright), 1 = graph.
  float nodeRotation = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).r;

`).concat(d,`

  // Calculate the actual size in pixels
  float size = a_size * u_correctionRatio / u_sizeRatio * 2.0;

  // In PICKING_MODE, inflate the quad by nodePickingPadding pixels on each side
  #ifdef PICKING_MODE
    float paddedSize = size + u_pickingPadding * u_correctionRatio;
    vec2 offset = a_quadCorner * paddedSize;
  #else
    vec2 offset = a_quadCorner * size;
  #endif
  // Counter-rotate the quad offset so viewport-aligned nodes stay upright as the
  // camera turns. Graph-aligned nodes (nodeRotation=1) skip it and turn with the
  // camera. The angle scales by (1 - nodeRotation) so both fall out of one path.
  {
    float ca = u_cameraAngle * (1.0 - nodeRotation);
    float c = cos(ca);
    float s = sin(ca);
    offset = mat2(c, s, -s, c) * offset;
  }
  vec2 position = a_position + offset;

  gl_Position = vec4(
    (u_matrix * vec3(position, 1)).xy,
    0,
    1
  );

  // In PICKING_MODE, UV is scaled beyond [-1, 1] to match the inflated quad
  #ifdef PICKING_MODE
    v_uv = a_quadCorner * (paddedSize / size);
  #else
    v_uv = a_quadCorner;
  #endif

  // Pass ID to fragment shader
  v_id = a_id;

  // Pass pixel size for layers that need pixel-mode calculations
  // Multiply by 2 because 'size' is half-width (offset from center), not full diameter
  v_pixelSize = size * 2.0;

  // Conversion factor from screen pixels to UV units
  // Same derivation as v_antialiasingWidth which represents ~1 pixel in UV space
  // P pixels in UV space = P * u_correctionRatio / size
  v_pixelToUV = u_correctionRatio / size;

  // We use an antialiasing width of 1px (so v_pixelToUV)
  v_antialiasingWidth = v_pixelToUV;

  // Pass layer attributes to fragment shader (fetched from texture)
`).concat(h,`
}
`);return u}function Si(a,r,t){var e=r.map(function(v,b){var m="layer_".concat(v.name),x=[].concat(H(v.attributes.map(function(g){return"v_".concat(g.name.replace(/^a_/,""))})),H(v.uniforms.map(function(g){return g.name}))).join(", ");return"  // Layer ".concat(b+1,": ").concat(v.name,`
  color = blendOver(color, `).concat(m,"(").concat(x,"));")}).join(`

`),n=new Set(["u_correctionRatio"]),i=new Set,o=a.flatMap(function(v){return v.uniforms}).filter(function(v){return n.has(v.name)||i.has(v.name)?!1:(i.add(v.name),!0)}).map(function(v){return"uniform ".concat(v.type," ").concat(v.name,";")}).join(`
`),s=r.flatMap(function(v){return v.uniforms}).filter(function(v){return n.has(v.name)||i.has(v.name)?!1:(i.add(v.name),!0)}).map(function(v){return"uniform ".concat(v.type," ").concat(v.name,";")}).join(`
`),l=new Set,d=r.flatMap(function(v){return v.attributes}).filter(function(v){var b=v.name.replace(/^a_/,"");return l.has(b)?!1:(l.add(b),!0)}).map(function(v){var b=v.name.replace(/^a_/,""),m=v.size===1?"float":"vec".concat(v.size);return"in ".concat(m," v_").concat(b,";")}).join(`
`),h=ha(a),u=ci(a,t),c=`#version 300 es
precision highp float;

// Standard varyings
in vec2 v_uv;
in vec4 v_id;
in float v_antialiasingWidth;
in float v_pixelSize;
in float v_pixelToUV;
in float v_shapeId;  // Shape ID for multi-shape programs

// Standard uniforms (needed for some layer calculations like pixel-mode borders)
uniform float u_correctionRatio;
#ifdef PICKING_MODE
uniform float u_pickingPadding;
#endif

// Shape uniforms
`.concat(o,`

// Layer uniforms
`).concat(s,`

// Layer varyings
`).concat(d,`

// Fragment output (single target - picking handled via separate pass)
out vec4 fragColor;

// LayerContext struct - provides rendering context to all layers
struct LayerContext {
  float sdf;             // Signed distance from shape boundary (negative inside)
  vec2 uv;               // UV coordinates [-1, 1], center at (0,0)
  float shapeSize;       // Effective shape size (~diameter) in UV space (1.0 - aaWidth)
  float shapeHalfSize;   // Effective shape half size (~radius) in UV space
  float pixelSize;       // Node full size (~diameter) in screen pixels
  float aaWidth;         // Anti-aliasing width for smooth transitions
  float correctionRatio; // Scaling factor for consistent rendering across zoom levels
  float pixelToUV;       // Conversion factor: multiply screen pixels by this to get UV units
  float inradiusFactor;  // Ratio of inradius to circumradius (shape depth factor)
};

LayerContext context;  // Global instance, populated before layer calls

// Alpha "over" compositing for layer blending
vec4 blendOver(vec4 bg, vec4 fg) {
  float a = fg.a;
  return vec4(mix(bg.rgb, fg.rgb, a), bg.a + a * (1.0 - bg.a));
}

// SDF shape functions
`).concat(h,`

// Shape selector function (sets context.sdf and context.inradiusFactor)
`).concat(u,`

// Layer functions
`).concat(r.map(function(v){return v.glsl}).join(`

`),`

void main() {
  // 1. Setup LayerContext (available to all layer functions)
  context.shapeSize = 1.0 - v_antialiasingWidth;
  context.shapeHalfSize = context.shapeSize * 0.5;
  context.pixelSize = v_pixelSize;
  context.uv = v_uv;
  context.aaWidth = v_antialiasingWidth;
  context.correctionRatio = u_correctionRatio;
  context.pixelToUV = v_pixelToUV;

  // Query shape SDF based on shapeId (sets context.sdf and context.inradiusFactor)
  queryNodeSDF(int(v_shapeId), v_uv, context.shapeSize);

  // 2. Early discard for pixels fully outside the shape (with AA margin)
  // In PICKING_MODE, allow extra fragments up to the picking padding distance
  #ifdef PICKING_MODE
    if (context.sdf > u_pickingPadding * v_pixelToUV + context.aaWidth) discard;
  #else
    if (context.sdf > context.aaWidth) discard;
  #endif

  // 3. Apply layers sequentially with "over" compositing
  vec4 color = vec4(0.0);

`).concat(e,`

  #ifdef PICKING_MODE
    // Picking pass: output node ID for pixels within the picking area.
    if (context.sdf > u_pickingPadding * v_pixelToUV) discard;
    fragColor = v_id;
  #else
    // Visual pass: apply antialiasing at shape boundary
    // smoothstep provides smooth transition from opaque to transparent
    float alpha = smoothstep(context.aaWidth, -context.aaWidth, context.sdf);
    // Mix with transparent to fade both color AND alpha together (avoids bright halo)
    fragColor = mix(vec4(0.0), color, alpha);
  #endif
}
`);return c}function Ei(a,r){var t=new Set;return t.add("u_matrix"),t.add("u_sizeRatio"),t.add("u_correctionRatio"),t.add("u_cameraAngle"),t.add("u_pickingPadding"),t.add("u_nodeDataTexture"),t.add("u_nodeDataTextureWidth"),t.add("u_layerAttributeTexture"),t.add("u_layerAttributeTextureWidth"),t.add("u_layerAttributeTexelsPerNode"),a.forEach(function(e){e.uniforms.forEach(function(n){return t.add(n.name)})}),r.forEach(function(e){e.uniforms.forEach(function(n){return t.add(n.name)})}),Array.from(t)}function Ri(a){var r=WebGL2RenderingContext,t=r.UNSIGNED_BYTE,e=r.FLOAT;return[{name:"a_nodeIndex",size:1,type:e},{name:"a_id",size:4,type:t,normalized:!0}]}function Na(a){var r=a.shapes,t=a.layers,e=a.shapeGlobalIds;return{vertexShader:_i(r,t),fragmentShader:Si(r,t,e),uniforms:Ei(r,t),attributes:Ri()}}var Fn=(function(a){function r(){var t;V(this,r);for(var e=arguments.length,n=new Array(e),i=0;i<e;i++)n[i]=arguments[i];return t=ee(this,r,[].concat(n)),S(t,"totalCharacterCount",0),S(t,"bufferCapacity",0),t}return te(r,a),X(r,[{key:"processLabel",value:function(e,n,i){if(i.hidden||!i.text)return 0;for(var o=i.text,s=o.length,l=0;l<s;l++){var d=o[l];this.processCharacter(n+l,i,d,l)}return s}},{key:"hasNothingToRender",value:function(){return this.totalCharacterCount===0}},{key:"drawWebGL",value:function(e,n){var i=n.gl;this.totalCharacterCount!==0&&(this.isInstanced?i.drawArraysInstanced(e,0,this.VERTICES,this.totalCharacterCount):i.drawArrays(e,0,this.totalCharacterCount*this.VERTICES))}},{key:"reallocate",value:function(e){this.totalCharacterCount=e,e>this.bufferCapacity&&(this.bufferCapacity=Math.max(e,Math.ceil(this.bufferCapacity*1.5)||1e3),ne(r,"reallocate",this)([this.bufferCapacity]))}}])})(Fe);function Ai(){var a=`#version 300 es

in float a_nodeIndex;
in vec4 a_id;
in vec4 a_color;
in float a_labelWidth;
in float a_labelHeight;
in float a_textHeight;
in float a_positionMode;
in float a_labelAngle;
in float a_padding;
in vec2 a_quadCorner;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform vec2 u_resolution;
uniform float u_pixelRatio;
uniform float u_labelMargin;
uniform float u_zoomLabelSizeRatio;
uniform float u_labelPixelSnapping;
uniform float u_pickingPadding;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_nodeFrameTexture;
uniform int u_nodeFrameTextureWidth;

out vec4 v_id;
out vec4 v_color;

`.concat(be,`
`).concat(Pe,`
`).concat(Ve,`
`).concat(An,`

void main() {
  int nodeIdx = int(a_nodeIndex);

  // Node data: (x, y, size, shapeId).
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 nodePosition = nodeData.xy;
  float nodeSize = nodeData.z;

  // Shape-aware edge distance, read once from the shared frame texture.
  float edgeDist = readFrameTexel(u_nodeFrameTexture, u_nodeFrameTextureWidth, nodeIdx).r;

  // Per-node label rotation alignment: 0 = viewport, 1 = label turns with camera.
  float labelRotation = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).g;

  `).concat(En,`

  float zoomScale = u_zoomLabelSizeRatio;
  float labelW = a_labelWidth * zoomScale * u_pixelRatio;
  float labelH = a_labelHeight * zoomScale * u_pixelRatio;
  float labelMargin = u_labelMargin * zoomScale * u_pixelRatio;
#ifdef PICKING_MODE
  float padding = u_pickingPadding * u_pixelRatio;
#else
  float padding = a_padding * u_pixelRatio;
#endif

  if (labelW <= 0.0) {
    gl_Position = vec4(2.0, 0.0, 0.0, 1.0);
    v_id = vec4(0.0);
    v_color = vec4(0.0);
    return;
  }

  vec2 labelHalfSize = vec2(labelW * 0.5 + padding, labelH * 0.5 + padding);
  vec2 labelOffset = vec2(0.0);

  // Graph-aligned labels add the camera angle so the rect orbits with the text.
  float labelAngle = a_labelAngle - labelRotation * u_cameraAngle;
  float la_c = cos(labelAngle);
  float la_s = sin(labelAngle);
  mat2 labelRotMat = mat2(la_c, -la_s, la_s, la_c);

  vec3 nodeClip = u_matrix * vec3(nodePosition, 1.0);
  vec2 nodeScreen = vec2(
    (nodeClip.x + 1.0) * u_resolution.x,
    (1.0 - nodeClip.y) * u_resolution.y
  ) * 0.5;
  vec2 snapDelta = (round(nodeScreen) - nodeScreen) * u_labelPixelSnapping;

  if (a_positionMode < 4.0) {
    float labelStart = nodeRadiusPixels * edgeDist + labelMargin;
    float textHalf = a_textHeight * zoomScale * u_pixelRatio * 0.5;
    // Box center uses the text half-size; the padding expands the quad below.
    labelOffset = labelRotMat * labelBoxCenter(a_positionMode, labelStart, vec2(labelW * 0.5, labelH * 0.5), textHalf);
  }

  // Rotate the rect with the label so it stays aligned with the (rotated) text.
  vec2 localPos = labelOffset + labelRotMat * (a_quadCorner * labelHalfSize);
  vec2 ndcOffset = (localPos + snapDelta) * 2.0 / u_resolution;
  ndcOffset.y = -ndcOffset.y;

  gl_Position = vec4(nodeClip.xy + ndcOffset, 0.0, 1.0);
  v_id = a_id;
  v_color = a_color;
}
`);return a}var Di=`#version 300 es
precision highp float;

in vec4 v_id;
in vec4 v_color;

out vec4 fragColor;

void main() {
  #ifdef PICKING_MODE
    fragColor = v_id;
  #else
    if (v_color.a <= 0.0) discard;
    // v_color is non-premultiplied RGBA (0-1); convert to premultiplied for blending
    fragColor = vec4(v_color.rgb * v_color.a, v_color.a);
  #endif
}
`;function Ci(a,r,t,e){var n,i,o=e.label,s=o===void 0?{}:o,l=(n=s.margin)!==null&&n!==void 0?n:et,d=(i=s.zoomToLabelSizeRatioFunction)!==null&&i!==void 0?i:function(){return 1},h=Ai(),u=(function(c){function v(){var b;V(this,v);for(var m=arguments.length,x=new Array(m),g=0;g<m;g++)x[g]=arguments[g];return b=ee(this,v,[].concat(x)),S(b,"totalCount",0),S(b,"bufferCapacity",0),b}return te(v,c),X(v,[{key:"getDefinition",value:function(){var m=WebGL2RenderingContext,x=m.FLOAT,g=m.UNSIGNED_BYTE,f=m.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:h,FRAGMENT_SHADER_SOURCE:Di,METHOD:f,UNIFORMS:["u_matrix","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_resolution","u_pixelRatio","u_labelMargin","u_zoomLabelSizeRatio","u_labelPixelSnapping","u_pickingPadding","u_nodeDataTexture","u_nodeDataTextureWidth","u_nodeFrameTexture","u_nodeFrameTextureWidth"],ATTRIBUTES:[{name:"a_nodeIndex",size:1,type:x},{name:"a_id",size:4,type:g,normalized:!0},{name:"a_color",size:4,type:g,normalized:!0},{name:"a_labelWidth",size:1,type:x},{name:"a_labelHeight",size:1,type:x},{name:"a_textHeight",size:1,type:x},{name:"a_positionMode",size:1,type:x},{name:"a_labelAngle",size:1,type:x},{name:"a_padding",size:1,type:x}],CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:x}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"processLabelBackground",value:function(m,x){var g=this.floats,f=this.ints,p=m*this.STRIDE;g[p++]=x.nodeIndex,f[p++]=x.id,g[p++]=x.color,g[p++]=x.labelWidth,g[p++]=x.labelHeight,g[p++]=x.textHeight,g[p++]=x.positionMode,g[p++]=x.labelAngle,g[p++]=x.padding}},{key:"setUniforms",value:function(m,x){var g=x.gl,f=x.uniformLocations;g.uniformMatrix3fv(f.u_matrix,!1,m.matrix),g.uniform1f(f.u_sizeRatio,m.sizeRatio),g.uniform1f(f.u_correctionRatio,m.correctionRatio),g.uniform1f(f.u_cameraAngle,m.cameraAngle),g.uniform2f(f.u_resolution,m.width*m.pixelRatio,m.height*m.pixelRatio),g.uniform1f(f.u_pixelRatio,m.pixelRatio),g.uniform1f(f.u_labelMargin,v.labelMargin),g.uniform1f(f.u_zoomLabelSizeRatio,1/d(m.zoomRatio)),g.uniform1f(f.u_labelPixelSnapping,m.labelPixelSnapping),g.uniform1f(f.u_pickingPadding,m.labelPickingPadding),g.uniform1i(f.u_nodeDataTexture,m.nodeDataTextureUnit),g.uniform1i(f.u_nodeDataTextureWidth,m.nodeDataTextureWidth),g.uniform1i(f.u_nodeFrameTexture,m.nodeFrameTextureUnit),g.uniform1i(f.u_nodeFrameTextureWidth,m.nodeFrameTextureWidth)}},{key:"hasNothingToRender",value:function(){return this.totalCount===0}},{key:"drawWebGL",value:function(m,x){var g=x.gl;this.totalCount!==0&&g.drawArraysInstanced(g.TRIANGLE_STRIP,0,this.VERTICES,this.totalCount)}},{key:"reallocate",value:function(m){this.totalCount=m,m>this.bufferCapacity&&(this.bufferCapacity=Math.max(m,Math.ceil(this.bufferCapacity*1.5)||10),ne(v,"reallocate",this)([this.bufferCapacity]))}}])})(Fe);return S(u,"labelMargin",l),new u(a,r,t)}var pe={fontSize:64,buffer:8,radius:24,cutoff:.25,maxTextureSize:2048,debounceTimeout:100},qe=2,Qe=1e20;function Li(a,r,t,e,n){var i=a+n*4,o=document.createElement("canvas");o.width=i,o.height=i;var s=o.getContext("2d",{willReadFrequently:!0});return s.font="".concat(e," ").concat(t," ").concat(a,"px ").concat(r),s.textBaseline="alphabetic",s.textAlign="left",s.fillStyle="black",{ctx:s,canvasSize:i,gridOuter:new Float64Array(i*i),gridInner:new Float64Array(i*i),f:new Float64Array(i),z:new Float64Array(i+1),v:new Uint16Array(i)}}function Pi(a,r,t,e,n){var i=a.ctx,o=a.canvasSize,s=i.measureText(r),l=s.width,d=s.actualBoundingBoxAscent,h=s.actualBoundingBoxDescent,u=s.actualBoundingBoxLeft,c=s.actualBoundingBoxRight,v=Math.ceil(d),b=Math.ceil(u),m=Math.max(0,Math.min(o-t,Math.ceil(u)+Math.ceil(c))),x=Math.min(o-t,v+Math.ceil(h)),g=m+2*t,f=x+2*t,p=Math.max(g*f,0),y=new Uint8ClampedArray(p),T={data:y,width:g,height:f,glyphWidth:m,glyphHeight:x,glyphTop:v,glyphLeft:b,glyphAdvance:l};if(m===0||x===0)return T;var _=a.gridInner,E=a.gridOuter;i.clearRect(t,t,m,x),i.fillText(r,t+b,t+v);var A=i.getImageData(t,t,m,x);E.fill(Qe,0,p),_.fill(0,0,p);for(var R=0;R<x;R++)for(var L=0;L<m;L++){var F=A.data[4*(R*m+L)+3]/255;if(F!==0){var C=(R+t)*g+L+t;if(F===1)E[C]=0,_[C]=Qe;else{var P=.5-F;E[C]=P>0?P*P:0,_[C]=P<0?P*P:0}}}Ga(E,0,0,g,f,g,a.f,a.v,a.z),Ga(_,t,t,m,x,g,a.f,a.v,a.z);for(var D=0;D<p;D++){var k=Math.sqrt(E[D])-Math.sqrt(_[D]);y[D]=Math.round(255-255*(k/e+n))}return T}function Ga(a,r,t,e,n,i,o,s,l){for(var d=r;d<r+e;d++)Ba(a,t*i+d,i,n,o,s,l);for(var h=t;h<t+n;h++)Ba(a,h*i+r,1,e,o,s,l)}function Ba(a,r,t,e,n,i,o){i[0]=0,o[0]=-Qe,o[1]=Qe,n[0]=a[r];for(var s=1,l=0,d=0;s<e;s++){n[s]=a[r+s*t];var h=s*s;do{var u=i[l];d=(n[s]-n[u]+h-u*u)/(s-u)/2}while(d<=o[l]&&--l>-1);l++,i[l]=s,o[l]=d,o[l+1]=Qe}for(var c=0,v=0;c<e;c++){for(;o[v+1]<c;)v++;var b=i[v],m=c-b;a[r+c*t]=n[b]+m*m}}var Oe=(function(a){function r(){var t,e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return V(this,r),t=ee(this,r),S(t,"fonts",new Map),S(t,"textures",[]),S(t,"cursor",{x:0,y:0,rowHeight:0,atlasIndex:0}),S(t,"pendingGlyphs",[]),S(t,"debounceTimer",null),t.options=N(N({},pe),e),t.canvas=document.createElement("canvas"),t.canvas.width=t.options.maxTextureSize,t.canvas.height=t.options.maxTextureSize,t.ctx=t.canvas.getContext("2d",{willReadFrequently:!0}),t.measureCanvas=document.createElement("canvas"),t.measureCtx=t.measureCanvas.getContext("2d"),t.textures.push(t.ctx.getImageData(0,0,1,1)),t}return te(r,a),X(r,[{key:"getFontKey",value:function(e){return"".concat(e.family,"-").concat(e.weight,"-").concat(e.style)}},{key:"registerFont",value:function(e){var n=this.getFontKey(e);if(this.fonts.has(n))return n;var i=Li(this.options.fontSize,e.family,e.weight,e.style,this.options.buffer);return this.fonts.set(n,{descriptor:e,generator:i,glyphs:new Map}),n}},{key:"ensureGlyphs",value:function(e,n){var i=this.fonts.get(n);if(!i)throw new Error('Font "'.concat(n,'" is not registered. Call registerFont() first.'));var o=!1,s=M(e),l;try{for(s.s();!(l=s.n()).done;){var d=l.value,h=d.codePointAt(0);h!==void 0&&(i.glyphs.has(h)||(this.pendingGlyphs.push({fontKey:n,charCode:h}),o=!0))}}catch(u){s.e(u)}finally{s.f()}o&&this.scheduleTextureGeneration()}},{key:"measureText",value:function(e,n){var i=this.fonts.get(n);if(!i)throw new Error('Font "'.concat(n,'" is not registered.'));var o=i.descriptor,s=o.family,l=o.weight,d=o.style;return this.measureCtx.font="".concat(d," ").concat(l," ").concat(this.options.fontSize,"px ").concat(s),this.measureCtx.measureText(e).width}},{key:"getGlyph",value:function(e,n){var i=this.fonts.get(n);if(i)return i.glyphs.get(e)}},{key:"getTextures",value:function(){return this.textures}},{key:"getFontCount",value:function(){return this.fonts.size}},{key:"getGlyphCount",value:function(){var e=0,n=M(this.fonts.values()),i;try{for(n.s();!(i=n.n()).done;){var o=i.value;e+=o.glyphs.size}}catch(s){n.e(s)}finally{n.f()}return e}},{key:"hasPendingGlyphs",value:function(){return this.pendingGlyphs.length>0}},{key:"flush",value:function(){this.debounceTimer&&(clearTimeout(this.debounceTimer),this.debounceTimer=null),this.generateTextures()}},{key:"destroy",value:function(){this.debounceTimer&&clearTimeout(this.debounceTimer),this.fonts.clear(),this.textures=[],this.pendingGlyphs=[],this.removeAllListeners()}},{key:"scheduleTextureGeneration",value:function(){var e=this;this.debounceTimer===null&&(this.options.debounceTimeout===null?this.generateTextures():this.debounceTimer=setTimeout(function(){e.debounceTimer=null,e.generateTextures()},this.options.debounceTimeout))}},{key:"generateTextures",value:function(){if(this.pendingGlyphs.length!==0){var e=this.options,n=e.maxTextureSize,i=e.buffer,o=e.radius,s=e.cutoff,l=M(this.pendingGlyphs),d;try{for(l.s();!(d=l.n()).done;){var h=d.value,u=h.fontKey,c=h.charCode,v=this.fonts.get(u);if(!(!v||v.glyphs.has(c))){var b=String.fromCodePoint(c),m=Pi(v.generator,b,i,o,s),x=m.width,g=m.height;this.cursor.x+x+qe>n&&(this.cursor.x=0,this.cursor.y+=this.cursor.rowHeight+qe,this.cursor.rowHeight=0),this.cursor.y+g+qe>n&&(this.finalizeCurrentTexture(),this.cursor={x:0,y:0,rowHeight:0,atlasIndex:this.cursor.atlasIndex+1},this.ctx.clearRect(0,0,n,n));for(var f=m.data,p=new Uint8ClampedArray(x*g*4),y=0;y<f.length;y++){var T=y*4;p[T]=255,p[T+1]=255,p[T+2]=255,p[T+3]=f[y]}var _=new ImageData(p,x,g);this.ctx.putImageData(_,this.cursor.x,this.cursor.y);var E={charCode:c,width:m.glyphWidth,height:m.glyphHeight,bearingX:-m.glyphLeft-i,bearingY:m.glyphTop+i,advance:m.glyphAdvance,atlasX:this.cursor.x,atlasY:this.cursor.y,atlasWidth:x,atlasHeight:g,atlasIndex:this.cursor.atlasIndex};v.glyphs.set(c,E),this.cursor.x+=x+qe,this.cursor.rowHeight=Math.max(this.cursor.rowHeight,g)}}}catch(A){l.e(A)}finally{l.f()}this.finalizeCurrentTexture(),this.pendingGlyphs=[],this.emit(r.ATLAS_UPDATED_EVENT,{textures:this.textures,glyphCount:this.getGlyphCount()})}}},{key:"finalizeCurrentTexture",value:function(){var e=this.options.maxTextureSize,n=Math.min(e,Math.max(this.cursor.x,this.cursor.rowHeight>0?e:1)),i=Math.min(e,this.cursor.y+this.cursor.rowHeight+qe),o=this.ctx.getImageData(0,0,n,i);this.cursor.atlasIndex>=this.textures.length?this.textures.push(o):this.textures[this.cursor.atlasIndex]=o}}])})(dn.EventEmitter);S(Oe,"ATLAS_UPDATED_EVENT","atlasUpdated");var Fi=pe.fontSize;function ki(){var a=`  // -------------------------------------------------------------------------
  // Step 3: Calculate position offset from the shared edge distance
  // -------------------------------------------------------------------------
  vec2 positionOffset = vec2(0.0);

  if (a_positionMode < 4.0) {
    vec2 screenDir = getLabelDirection(a_positionMode);
    float boundaryDistPixels = nodeRadiusPixels * edgeDist;
    positionOffset = screenDir * (boundaryDistPixels + margin);
  }`,r=`#version 300 es

// ============================================================================
// Attributes
// ============================================================================

// Per-character (instanced)
in float a_nodeIndex;        // Index into node data texture
in vec2 a_charOffset;        // Character offset from label origin (pixels)
in vec2 a_charSize;          // Character dimensions (pixels)
in vec4 a_texCoords;         // Atlas coords: (x, y, width, height) in pixels
in vec4 a_color;             // Text color (RGBA)
in float a_margin;           // Gap between node edge and label (pixels)
in float a_positionMode;     // Position: 0=right, 1=left, 2=above, 3=below, 4=over
in float a_labelWidth;       // Total label width (pixels)
in float a_labelHeight;      // Label height (pixels)
in float a_verticalCenter;   // Vertical center offset from baseline (pixels)
in float a_textHeight;       // Actual text height: maxAscent + maxDescent (pixels)
in float a_labelAngle;       // Label rotation angle (radians)

// Per-vertex (constant quad corners)
in vec2 a_quadCorner;        // Quad corner: [-1,-1], [1,-1], [-1,1], [1,1]

// ============================================================================
// Uniforms
// ============================================================================

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform vec2 u_resolution;
uniform vec2 u_atlasSize;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_nodeFrameTexture;
uniform int u_nodeFrameTextureWidth;
uniform float u_zoomLabelSizeRatio;
uniform float u_labelPixelSnapping;
uniform float u_pixelRatio;

// ============================================================================
// Varyings
// ============================================================================

out vec2 v_texCoord;
out vec4 v_color;
out float v_fontScale;

// ============================================================================
// Constants
// ============================================================================

const float bias = 255.0 / 254.0;
const float ATLAS_FONT_SIZE = `.concat(Y(Fi),`;

// ============================================================================
// Helper Functions
// ============================================================================

`).concat(be,`
`).concat(Pe,`
`).concat(Ve,`
`).concat(Rn,`

// ============================================================================
// Main
// ============================================================================

void main() {
  // -------------------------------------------------------------------------
  // Step 0: Fetch node data + shared edge distance from textures
  // -------------------------------------------------------------------------
  // Node-data texture format: vec4(x, y, size, shapeId)
  // 2D texture layout: texCoord = (index % width, index / width)
  int nodeIdx = int(a_nodeIndex);
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 a_anchorPosition = nodeData.xy;
  float a_nodeSize = nodeData.z;

  // Normalized edge distance from the shared frame texture (the frame-pass ran
  // the SDF search once; the label just reads the result).
  float edgeDist = readFrameTexel(u_nodeFrameTexture, u_nodeFrameTextureWidth, nodeIdx).r;

  // Per-node label rotation alignment: 0 = viewport, 1 = label turns with camera.
  float labelRotation = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).g;

  // Apply zoom-dependent label size scaling
  // Positional values are in CSS pixels; multiply by u_pixelRatio to convert to
  // physical pixels, which is what the NDC conversion (/ u_resolution) expects.
  float zoomScale = u_zoomLabelSizeRatio;
  float margin = a_margin * zoomScale * u_pixelRatio;
  vec2 charOffset = a_charOffset * zoomScale * u_pixelRatio;
  vec2 charSize = a_charSize * zoomScale * u_pixelRatio;
  float labelWidth = a_labelWidth * zoomScale * u_pixelRatio;
  float labelHeight = a_labelHeight * zoomScale;

  // Font scale: ratio of CSS label size to the base atlas font size.
  // Divided by u_pixelRatio because the atlas is generated at ATLAS_FONT_SIZE * pixelRatio,
  // which cancels out the u_pixelRatio in the fragment shader's gamma formula and keeps
  // the anti-aliasing band width consistent across pixel densities.
  v_fontScale = a_labelHeight * zoomScale / (ATLAS_FONT_SIZE * u_pixelRatio);

  // -------------------------------------------------------------------------
  // Step 1: Transform node position to clip space
  // -------------------------------------------------------------------------
  vec3 anchorClip = u_matrix * vec3(a_anchorPosition, 1.0);

  // -------------------------------------------------------------------------
  // Step 2: Convert node size to screen pixels
  // -------------------------------------------------------------------------
  float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
  float nodeRadiusGraphSpace = a_nodeSize * u_correctionRatio / u_sizeRatio * 2.0;
  float nodeRadiusNDC = nodeRadiusGraphSpace * matrixScaleX;
  float nodeRadiusPixels = nodeRadiusNDC * u_resolution.x / 2.0;

`).concat(a,`

  // -------------------------------------------------------------------------
  // Step 4: Calculate final vertex position
  // -------------------------------------------------------------------------
  vec2 cornerOffset = (a_quadCorner + 1.0) * 0.5;
  vec2 charPixelPos = positionOffset + charOffset + cornerOffset * charSize;

  // Apply text alignment based on position mode
  float verticalCenter = a_verticalCenter * zoomScale * u_pixelRatio;
  float textHeight = a_textHeight * zoomScale * u_pixelRatio;
  float baselineToDescent = textHeight / 2.0 - verticalCenter;
  float baselineToAscent = textHeight / 2.0 + verticalCenter;

  if (a_positionMode < 0.5) {
    // Right: vertically center
    charPixelPos.y += verticalCenter;
  } else if (a_positionMode < 1.5) {
    // Left: right-align and vertically center
    charPixelPos.x -= labelWidth;
    charPixelPos.y += verticalCenter;
  } else if (a_positionMode < 2.5) {
    // Above: center horizontally, bottom of text at anchor
    charPixelPos.x -= labelWidth * 0.5;
    charPixelPos.y -= baselineToDescent;
  } else if (a_positionMode < 3.5) {
    // Below: center horizontally, top of text at anchor
    charPixelPos.x -= labelWidth * 0.5;
    charPixelPos.y += baselineToAscent;
  } else {
    // Over: center both
    charPixelPos.x -= labelWidth * 0.5;
    charPixelPos.y += verticalCenter;
  }

  // Apply label angle rotation. Graph-aligned labels add the camera angle so the
  // whole label orbits the node in lockstep with the frame-pass edge distance.
  float labelAngle = a_labelAngle - labelRotation * u_cameraAngle;
  float la_c = cos(labelAngle);
  float la_s = sin(labelAngle);
  mat2 labelRotMat = mat2(la_c, -la_s, la_s, la_c);
  charPixelPos = labelRotMat * charPixelPos;

  // Snap node center to pixel grid so label/backdrop/attachment move as a unit
  vec2 nodeScreen = vec2(
    (anchorClip.x + 1.0) * u_resolution.x,
    (1.0 - anchorClip.y) * u_resolution.y
  ) * 0.5;
  charPixelPos += (round(nodeScreen) - nodeScreen) * u_labelPixelSnapping;

  // Convert to NDC (flip Y: screen Y-down -> clip Y-up)
  vec2 ndcOffset = vec2(charPixelPos.x, -charPixelPos.y) * 2.0 / u_resolution;
  gl_Position = vec4(anchorClip.xy + ndcOffset, 0.0, 1.0);

  // -------------------------------------------------------------------------
  // Step 5: Texture coordinates
  // -------------------------------------------------------------------------
  v_texCoord = (a_texCoords.xy + cornerOffset * a_texCoords.zw) / u_atlasSize;

  // -------------------------------------------------------------------------
  // Step 6: Pass color
  // -------------------------------------------------------------------------
  v_color = a_color;
  v_color.a *= bias;
}
`);return r}function wi(){var a=`#version 300 es
precision highp float;

in vec2 v_texCoord;
in vec4 v_color;
in float v_fontScale;

uniform sampler2D u_atlas;
uniform float u_gamma;
uniform float u_sdfBuffer;
uniform float u_pixelRatio;

// Fragment output (single target - picking handled via separate pass)
out vec4 fragColor;

void main() {
  #ifdef PICKING_MODE
    // Labels are not pickable - discard all fragments in picking mode
    discard;
  #else
    // Sample SDF value from atlas (high = inside glyph, low = outside)
    float sdfValue = texture(u_atlas, v_texCoord).a;

    // Edge threshold: 1.0 - cutoff = 0.75 for default cutoff=0.25
    // This is where the glyph edge is located in the SDF
    float edgeThreshold = 1.0 - u_sdfBuffer;

    // Gamma controls the anti-aliasing band width.
    // Scale inversely with font scale so small labels get a wider AA band
    // (smoother) and large labels get a tighter band (sharper).
    float gamma = u_gamma / (u_pixelRatio * v_fontScale);

    // Pure gamma-based anti-aliasing using smoothstep
    // The AA band extends from (threshold - gamma) to (threshold + gamma)
    float alpha = smoothstep(edgeThreshold - gamma, edgeThreshold + gamma, sdfValue);

    // Premultiplied alpha output for correct blending
    float finalAlpha = v_color.a * alpha;
    fragColor = vec4(v_color.rgb * finalAlpha, finalAlpha);
  #endif
}
`;return a}function Ii(){return["u_matrix","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_resolution","u_atlasSize","u_atlas","u_gamma","u_sdfBuffer","u_pixelRatio","u_nodeDataTexture","u_nodeDataTextureWidth","u_nodeFrameTexture","u_nodeFrameTextureWidth","u_zoomLabelSizeRatio","u_labelPixelSnapping"]}function zi(){return{vertexShader:ki(),fragmentShader:wi(),uniforms:Ii()}}function Mi(a,r,t,e){var n,i,o=e.label,s=o===void 0?{}:o,l=(n=s.margin)!==null&&n!==void 0?n:et,d=(i=s.zoomToLabelSizeRatioFunction)!==null&&i!==void 0?i:function(){return 1},h=zi(),u=(function(c){function v(b,m,x){var g,f,p,y;if(V(this,v),y=ee(this,v,[b,m,x]),S(y,"atlasTexture",null),S(y,"atlasNeedsUpdate",!1),S(y,"labelGlyphCache",new Map),y.atlasFontSize=pe.fontSize*Yt(),y.atlasManager=new Oe({fontSize:y.atlasFontSize}),y.gamma=.025,y.sdfBuffer=pe.cutoff,y.atlasTexture=b.createTexture(),!y.atlasTexture)throw new Error("NodeLabelProgram: failed to create atlas texture");b.bindTexture(b.TEXTURE_2D,y.atlasTexture),b.texParameteri(b.TEXTURE_2D,b.TEXTURE_WRAP_S,b.CLAMP_TO_EDGE),b.texParameteri(b.TEXTURE_2D,b.TEXTURE_WRAP_T,b.CLAMP_TO_EDGE),b.texParameteri(b.TEXTURE_2D,b.TEXTURE_MIN_FILTER,b.LINEAR),b.texParameteri(b.TEXTURE_2D,b.TEXTURE_MAG_FILTER,b.LINEAR),b.bindTexture(b.TEXTURE_2D,null),y.atlasManager.on(Oe.ATLAS_UPDATED_EVENT,function(){y.atlasNeedsUpdate=!0});var T={family:((g=s.font)===null||g===void 0?void 0:g.family)||"sans-serif",weight:((f=s.font)===null||f===void 0?void 0:f.weight)||"normal",style:((p=s.font)===null||p===void 0?void 0:p.style)||"normal"};return y.defaultFontKey=y.atlasManager.registerFont(T),y}return te(v,c),X(v,[{key:"getDefinition",value:function(){var m=WebGL2RenderingContext,x=m.FLOAT,g=m.UNSIGNED_BYTE,f=m.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:h.vertexShader,FRAGMENT_SHADER_SOURCE:h.fragmentShader,METHOD:f,UNIFORMS:h.uniforms,ATTRIBUTES:[{name:"a_nodeIndex",size:1,type:x},{name:"a_charOffset",size:2,type:x},{name:"a_charSize",size:2,type:x},{name:"a_texCoords",size:4,type:x},{name:"a_color",size:4,type:g,normalized:!0},{name:"a_margin",size:1,type:x},{name:"a_positionMode",size:1,type:x},{name:"a_labelWidth",size:1,type:x},{name:"a_labelHeight",size:1,type:x},{name:"a_verticalCenter",size:1,type:x},{name:"a_textHeight",size:1,type:x},{name:"a_labelAngle",size:1,type:x}],CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:x}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"prepareLabelGlyphs",value:function(m,x){if(x.hidden||!x.text){this.labelGlyphCache.delete(m);return}var g=x.text,f=x.fontKey||this.defaultFontKey;this.atlasManager.ensureGlyphs(g,f);var p=[],y=[],T=0,_=0,E=0,A=M(g),R;try{for(A.s();!(R=A.n()).done;){var L=R.value,F=L.codePointAt(0);if(F===void 0){p.push(void 0),y.push(T);continue}var C=this.atlasManager.getGlyph(F,f);p.push(C),y.push(T),C&&(T+=C.advance,_=Math.max(_,C.bearingY),E=Math.max(E,C.atlasHeight-C.bearingY))}}catch(P){A.e(P)}finally{A.f()}this.labelGlyphCache.set(m,{glyphs:p,xOffsets:y,totalWidth:T,totalHeight:_+E,verticalCenterOffset:(_-E)/2})}},{key:"processCharacter",value:function(m,x,g,f){var p=this.floats,y=this.STRIDE,T=m*y,_=this.labelGlyphCache.get(x.parentKey);if(!_||!_.glyphs[f]){for(var E=0;E<y;E++)p[T+E]=0;return}var A=_.glyphs[f],R=_.xOffsets[f],L=x.size/this.atlasFontSize,F=me(x.color),C=T;p[C++]=x.nodeIndex,p[C++]=(R+A.bearingX)*L,p[C++]=-A.bearingY*L,p[C++]=A.atlasWidth*L,p[C++]=A.atlasHeight*L,p[C++]=A.atlasX,p[C++]=A.atlasY,p[C++]=A.atlasWidth,p[C++]=A.atlasHeight,p[C++]=F,p[C++]=x.margin,p[C++]=$e[x.position],p[C++]=_.totalWidth*L,p[C++]=x.size,p[C++]=_.verticalCenterOffset*L,p[C++]=_.totalHeight*L,p[C++]=x.labelAngle}},{key:"processLabel",value:function(m,x,g){return this.prepareLabelGlyphs(m,g),ne(v,"processLabel",this)([m,x,g])}},{key:"updateAtlasTexture",value:function(){if(this.atlasNeedsUpdate){var m=this.normalProgram.gl,x=this.atlasManager.getTextures();if(x.length!==0){var g=x[0];m.bindTexture(m.TEXTURE_2D,this.atlasTexture),m.texImage2D(m.TEXTURE_2D,0,m.RGBA,g.width,g.height,0,m.RGBA,m.UNSIGNED_BYTE,g.data),m.bindTexture(m.TEXTURE_2D,null),this.atlasNeedsUpdate=!1}}}},{key:"setUniforms",value:function(m,x){var g=x.gl,f=x.uniformLocations;g.uniformMatrix3fv(f.u_matrix,!1,m.matrix),g.uniform1f(f.u_sizeRatio,m.sizeRatio),g.uniform1f(f.u_correctionRatio,m.correctionRatio),g.uniform1f(f.u_cameraAngle,m.cameraAngle),g.uniform2f(f.u_resolution,m.width*m.pixelRatio,m.height*m.pixelRatio);var p=this.atlasManager.getTextures();p.length>0?g.uniform2f(f.u_atlasSize,p[0].width,p[0].height):g.uniform2f(f.u_atlasSize,1,1),g.activeTexture(g.TEXTURE0),g.bindTexture(g.TEXTURE_2D,this.atlasTexture),g.uniform1i(f.u_atlas,0),f.u_nodeDataTexture!==void 0&&g.uniform1i(f.u_nodeDataTexture,m.nodeDataTextureUnit),f.u_nodeDataTextureWidth!==void 0&&g.uniform1i(f.u_nodeDataTextureWidth,m.nodeDataTextureWidth),g.uniform1i(f.u_nodeFrameTexture,m.nodeFrameTextureUnit),g.uniform1i(f.u_nodeFrameTextureWidth,m.nodeFrameTextureWidth),g.uniform1f(f.u_gamma,this.gamma),g.uniform1f(f.u_sdfBuffer,this.sdfBuffer),g.uniform1f(f.u_pixelRatio,m.pixelRatio),g.uniform1f(f.u_zoomLabelSizeRatio,1/v.zoomToLabelSizeRatioFunction(m.zoomRatio)),g.uniform1f(f.u_labelPixelSnapping,m.labelPixelSnapping)}},{key:"renderProgram",value:function(m,x){this.updateAtlasTexture(),this.atlasManager.hasPendingGlyphs()&&(this.atlasManager.flush(),this.updateAtlasTexture()),ne(v,"renderProgram",this)([m,x])}},{key:"registerFont",value:function(m){var x=arguments.length>1&&arguments[1]!==void 0?arguments[1]:"normal",g=arguments.length>2&&arguments[2]!==void 0?arguments[2]:"normal";return this.atlasManager.registerFont({family:m,weight:x,style:g})}},{key:"getAtlasManager",value:function(){return this.atlasManager}},{key:"measureLabel",value:function(m,x,g){var f=g||this.defaultFontKey;this.atlasManager.ensureGlyphs(m,f),this.atlasManager.hasPendingGlyphs()&&this.atlasManager.flush();var p=0,y=0,T=0,_=M(m),E;try{for(_.s();!(E=_.n()).done;){var A=E.value,R=A.codePointAt(0);if(R!==void 0){var L=this.atlasManager.getGlyph(R,f);L&&(p+=L.advance,y=Math.max(y,L.bearingY),T=Math.max(T,L.atlasHeight-L.bearingY))}}}catch(C){_.e(C)}finally{_.f()}var F=x/this.atlasFontSize;return{width:p*F,height:x,textHeight:(y+T)*F}}},{key:"ensureGlyphsReady",value:function(m,x){var g=x||this.defaultFontKey,f=M(m),p;try{for(f.s();!(p=f.n()).done;){var y=p.value;this.atlasManager.ensureGlyphs(y,g)}}catch(T){f.e(T)}finally{f.f()}this.atlasManager.flush()}},{key:"kill",value:function(){var m=this.normalProgram.gl;this.atlasTexture&&(m.deleteTexture(this.atlasTexture),this.atlasTexture=null),this.atlasManager.destroy(),this.labelGlyphCache.clear(),ne(v,"kill",this)([])}}])})(Fn);return S(u,"labelMargin",l),S(u,"zoomToLabelSizeRatioFunction",d),new u(a,r,t)}var Ni=`#version 300 es
precision highp float;

in float v_edgeDist;

// R32F target: only the .r channel is stored.
out vec4 fragColor;

void main() {
  fragColor = vec4(v_edgeDist, 0.0, 0.0, 0.0);
}
`;function Gi(a,r){var t=ha(a),e=at(a).map(function(l){return"uniform ".concat(l.type," ").concat(l.name,";")}).join(`
`),n=ti(a,r),i=n.code,o=n.multiShape,s=`#version 300 es
precision highp float;

uniform float u_cameraAngle;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform float u_frameTextureWidth;
uniform float u_frameTextureHeight;
`.concat(e,`

in float a_nodeIndex;     // node-data texture index (also the target frame texel)
in float a_positionMode;  // 0=right 1=left 2=above 3=below 4=over
in float a_labelAngle;    // intrinsic label angle (radians)

out float v_edgeDist;

`).concat(be,`
`).concat(Pe,`
`).concat(t,`
`).concat(i,`
`).concat(Rn,`

void main() {
  int nodeIdx = int(a_nodeIndex);
  `).concat(o?`// Multi-shape: the shape id lives in the node-data texture's .w channel:
  g_shapeId = int(readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).w);`:"// Single-shape mode, shape id not needed",`

  // Per-node rotation alignment (0 = viewport, 1 = graph).
  vec4 nodeFlags = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  float nodeRotation = nodeFlags.r;
  float labelRotation = nodeFlags.g;

  // Effective angle: intrinsic (style-given) plus the camera angle when the label
  // is graph-aligned. The companions place the box at this same angle.
  float effectiveAngle = a_labelAngle - labelRotation * u_cameraAngle;

  // The "over" mode (4) sits on the node center, so it has no edge distance.
  float edgeDist = 0.0;
  if (a_positionMode < 4.0) {
    vec2 screenDir = getLabelDirection(a_positionMode);
    // Rotate by the effective label angle. Inlined rather than via rotate2D()
    // because the shape SDFs (getShapeGLSLForShapes) already define that helper
    // for multi-shape programs, and redefining it would be a GLSL error.
    float ea_c = cos(effectiveAngle);
    float ea_s = sin(effectiveAngle);
    vec2 rotatedScreenDir = mat2(ea_c, -ea_s, ea_s, ea_c) * screenDir;
    // Screen (Y-down) -> SDF (Y-up).
    vec2 sdfDir = vec2(rotatedScreenDir.x, -rotatedScreenDir.y);
    // Counter-rotate into the shape's local frame for graph-aligned nodes, so the
    // boundary is queried against the shape's actual on-screen orientation.
    float nodeCa = -u_cameraAngle * nodeRotation;
    float nc = cos(nodeCa), ns = sin(nodeCa);
    sdfDir = mat2(nc, -ns, ns, nc) * sdfDir;
    edgeDist = findEdgeDistance(sdfDir, 1.0);
  }
  v_edgeDist = edgeDist;

  // Scatter to this node's texel center in the frame texture.
  float x = mod(a_nodeIndex, u_frameTextureWidth);
  float y = floor(a_nodeIndex / u_frameTextureWidth);
  vec2 ndc = (vec2(x, y) + 0.5) / vec2(u_frameTextureWidth, u_frameTextureHeight) * 2.0 - 1.0;
  gl_Position = vec4(ndc, 0.0, 1.0);
  gl_PointSize = 1.0;
}
`);return s}var kn=(function(){function a(r,t){V(this,a),S(this,"uniformLocations",{});var e=t.shapes,n=t.shapeGlobalIds;if(e.length===0)throw new Error("NodeLabelFramePass: at least one shape must be provided");this.gl=r,this.shapeUniforms=at(e),this.vertexShader=oa(r,Gi(e,n)),this.fragmentShader=sa(r,Ni),this.program=la(r,[this.vertexShader,this.fragmentShader]);var i=["u_cameraAngle","u_nodeDataTexture","u_nodeDataTextureWidth","u_frameTextureWidth","u_frameTextureHeight"].concat(H(this.shapeUniforms.map(function(x){return x.name}))),o=M(i),s;try{for(o.s();!(s=o.n()).done;){var l=s.value;this.uniformLocations[l]=r.getUniformLocation(this.program,l)}}catch(x){o.e(x)}finally{o.f()}var d=a.FLOATS_PER_POINT*4;this.vao=r.createVertexArray(),this.buffer=r.createBuffer(),r.bindVertexArray(this.vao),r.bindBuffer(r.ARRAY_BUFFER,this.buffer);var h=M([["a_nodeIndex",0],["a_positionMode",4],["a_labelAngle",8]]),u;try{for(h.s();!(u=h.n()).done;){var c=Q(u.value,2),v=c[0],b=c[1],m=r.getAttribLocation(this.program,v);m>=0&&(r.enableVertexAttribArray(m),r.vertexAttribPointer(m,1,r.FLOAT,!1,d,b))}}catch(x){h.e(x)}finally{h.f()}r.bindVertexArray(null)}return X(a,[{key:"run",value:function(t,e,n,i){if(e!==0){var o=this.gl;o.useProgram(this.program),o.bindVertexArray(this.vao),o.bindBuffer(o.ARRAY_BUFFER,this.buffer),o.bufferData(o.ARRAY_BUFFER,t.subarray(0,e*a.FLOATS_PER_POINT),o.DYNAMIC_DRAW);var s=this.uniformLocations;o.uniform1f(s.u_cameraAngle,i.cameraAngle),o.uniform1i(s.u_nodeDataTexture,i.nodeDataTextureUnit),o.uniform1i(s.u_nodeDataTextureWidth,i.nodeDataTextureWidth),o.uniform1f(s.u_frameTextureWidth,n.getTextureWidth()),o.uniform1f(s.u_frameTextureHeight,n.getTextureHeight());var l=M(this.shapeUniforms),d;try{for(l.s();!(d=l.n()).done;){var h=d.value;ua(o,this.uniformLocations[h.name],h)}}catch(u){l.e(u)}finally{l.f()}n.bindAsRenderTarget(),o.disable(o.BLEND),o.disable(o.DEPTH_TEST),o.drawArrays(o.POINTS,0,e),o.bindFramebuffer(o.FRAMEBUFFER,null),o.bindVertexArray(null)}}},{key:"kill",value:function(){var t=this.gl;t.deleteProgram(this.program),t.deleteShader(this.vertexShader),t.deleteShader(this.fragmentShader),t.deleteBuffer(this.buffer),t.deleteVertexArray(this.vao)}}])})();S(kn,"FLOATS_PER_POINT",3);var Wa=5;function Bi(a,r,t,e){var n,i=e.label,o=i===void 0?{}:i,s=e.shapes;if(s.length===0)throw new Error("createNodeProgram: at least one shape must be provided in 'shapes'");var l={},d=[],h;s.forEach(function(y,T){var _=di(y);T===0&&(h=_),l[y.name]=T,d[T]=pt(_)});var u=H(e.layers),c=Na({shapes:s,layers:u,shapeGlobalIds:s.length>1?d:void 0}),v=Mi(a,null,t,{label:o}),b=Ti(a,null,t,{shapes:s,label:o,shapeGlobalIds:s.length>1?d:void 0}),m=Ci(a,r,t,{label:o}),x=e.labelAttachments&&Object.keys(e.labelAttachments).length>0?mi(a,null,t,{label:o}):null,g=new kn(a,{shapes:s,shapeGlobalIds:s.length>1?d:void 0}),f=fe(u),p=(n=(function(y){function T(_,E,A){var R;V(this,T),R=ee(this,T,[_,E,A]),S(R,"layerLifecycles",new Map),S(R,"layersNeedingRegeneration",new Set),S(R,"attrDescriptors",[]),R._pickingBuffer=E;var L=p.layerTextures.get(_);L||(L=new Rt(_,f),p.layerTextures.set(_,L)),R.layerAttributeTexture=L;var F=p.textureRefCounts.get(_)||0;p.textureRefCounts.set(_,F+1),R.packedAttributeData=new Float32Array(f.floatsPerItem),u.forEach(function(P,D){if(P.lifecycle){var k={gl:_,renderer:{refresh:function(){return A.refresh()}},getUniformLocation:function(G){return _.getUniformLocation(R.normalProgram.program,G)},requestShaderRegeneration:function(){R.layersNeedingRegeneration.add(D)},requestRefresh:function(){A.refresh()}},w=P.lifecycle(k);R.layerLifecycles.set(D,w)}}),R.layerLifecycles.forEach(function(P){var D;(D=P.init)===null||D===void 0||D.call(P)});var C=new Map;return R.layerLifecycles.forEach(function(P,D){P.getAttributeData&&C.set(D,P)}),R.attrDescriptors=At(u,f,C),R}return te(T,y),X(T,[{key:"getDefinition",value:function(){var E=WebGL2RenderingContext,A=E.FLOAT,R=E.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:c.vertexShader,FRAGMENT_SHADER_SOURCE:c.fragmentShader,METHOD:R,UNIFORMS:c.uniforms,ATTRIBUTES:c.attributes,CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:A}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"maybeRegenerateShaders",value:function(){var E=this;if(this.layersNeedingRegeneration.size!==0){u=u.map(function(D,k){if(E.layersNeedingRegeneration.has(k)){var w=E.layerLifecycles.get(k);if(w!=null&&w.regenerate){var I=w.regenerate();return N(N({},I),{},{lifecycle:D.lifecycle})}}return D}),this.layersNeedingRegeneration.clear(),c=Na({shapes:s,layers:u,shapeGlobalIds:s.length>1?d:void 0});var A=this.normalProgram.gl,R=this.normalProgram,L=R.program,F=R.buffer,C=R.vertexShader,P=R.fragmentShader;A.deleteProgram(L),A.deleteBuffer(F),A.deleteShader(C),A.deleteShader(P),this.normalProgram=this.getProgramInfo("normal",A,c.vertexShader,c.fragmentShader,this._pickingBuffer)}}},{key:"allocateNode",value:function(E){this.layerAttributeTexture.allocate(E)}},{key:"freeNode",value:function(E){this.layerAttributeTexture.free(E)}},{key:"uploadLayerTexture",value:function(){this.layerAttributeTexture.upload()}},{key:"process",value:function(E,A,R,L,F){var C=A*this.STRIDE;if(R.visibility==="hidden"){for(var P=C+this.STRIDE;C<P;C++)this.floats[C]=0;return}this.processVisibleItem(yt(E),C,R,L,F)}},{key:"processVisibleItem",value:function(E,A,R,L,F){var C,P=this.floats,D=this.ints;if(P[A++]=L,D[A++]=E,f.floatsPerItem!==0){var k=this.packedAttributeData;Dt(this.attrDescriptors,R,k,R.color,(C=R.opacity)!==null&&C!==void 0?C:1,this.layerLifecycles,0),this.layerAttributeTexture.updateAllAttributes(F,k)}}},{key:"setUniforms",value:function(E,A){var R=this,L=A.gl,F=A.uniformLocations;F.u_matrix&&L.uniformMatrix3fv(F.u_matrix,!1,E.matrix),F.u_sizeRatio&&L.uniform1f(F.u_sizeRatio,E.sizeRatio),F.u_correctionRatio&&L.uniform1f(F.u_correctionRatio,E.correctionRatio),F.u_pickingPadding&&L.uniform1f(F.u_pickingPadding,E.nodePickingPadding),F.u_cameraAngle&&L.uniform1f(F.u_cameraAngle,E.cameraAngle),F.u_nodeDataTexture&&L.uniform1i(F.u_nodeDataTexture,E.nodeDataTextureUnit),F.u_nodeDataTextureWidth&&L.uniform1i(F.u_nodeDataTextureWidth,E.nodeDataTextureWidth),F.u_layerAttributeTexture&&(this.layerAttributeTexture.bind(Wa),L.uniform1i(F.u_layerAttributeTexture,Wa)),F.u_layerAttributeTextureWidth&&L.uniform1i(F.u_layerAttributeTextureWidth,this.layerAttributeTexture.getTextureWidth()),F.u_layerAttributeTexelsPerNode&&L.uniform1i(F.u_layerAttributeTexelsPerNode,this.layerAttributeTexture.getTexelsPerItem()),s.forEach(function(C){C.uniforms.forEach(function(P){R.setTypedUniform(P,A)})}),u.forEach(function(C){C.uniforms.forEach(function(P){R.setTypedUniform(P,A)})})}},{key:"renderProgram",value:function(E,A){this.maybeRegenerateShaders();var R=A.gl,L=A.program;R.useProgram(L),A===this.normalProgram&&this.layerLifecycles.forEach(function(F){var C;(C=F.beforeRender)===null||C===void 0||C.call(F)}),ne(T,"renderProgram",this)([E,A])}},{key:"kill",value:function(){this.layerLifecycles.forEach(function(R){var L;(L=R.kill)===null||L===void 0||L.call(R)}),this.layerLifecycles.clear();var E=this.normalProgram.gl,A=(p.textureRefCounts.get(E)||1)-1;A<=0?(this.layerAttributeTexture.kill(),p.layerTextures.delete(E),p.textureRefCounts.delete(E)):p.textureRefCounts.set(E,A),ne(T,"kill",this)([])}}])})(Fe),S(n,"layerTextures",new WeakMap),S(n,"textureRefCounts",new WeakMap),n);return{nodeProgram:new p(a,null,t),labelProgram:v,backdropProgram:b,labelBackgroundProgram:m,attachmentProgram:x,framePass:g,shapeSlug:h,shapeNameToIndex:s.length>1?l:void 0,shapeGlobalIds:s.length>1?d:void 0}}var _e=6;function nt(a){var r=a.offsets,t=a.specs,e=a.floatsPerItem,n=Object.keys(r);if(n.length===0||e===0)return{uniformDeclarations:"",uniformNames:[],vertexVaryingDeclarations:"",fragmentVaryingDeclarations:"",fetchCode:"",varyingAssignments:""};var i=`
uniform sampler2D u_edgeAttributeTexture;
uniform int u_edgeAttributeTextureWidth;
uniform int u_edgeAttributeTexelsPerEdge;`,o=["u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge"],s=n.map(function(v){var b=t[v].size===1?"float":"vec".concat(t[v].size);return"".concat(b," v_").concat(v,";")}),l=s.map(function(v){return"out ".concat(v)}).join(`
`),d=s.map(function(v){return"in ".concat(v)}).join(`
`),h=Cn(a,{varPrefix:"attr",baseTexelExpr:"edgeIdx * u_edgeAttributeTexelsPerEdge",textureWidthUniform:"u_edgeAttributeTextureWidth",textureSamplerUniform:"u_edgeAttributeTexture"}),u=h.fetchCode,c=h.varyingAssignments;return{uniformDeclarations:i,uniformNames:o,vertexVaryingDeclarations:l,fragmentVaryingDeclarations:d,fetchCode:u,varyingAssignments:c}}function Wi(a){return`
float findSourceClampT_`.concat(a,`(vec2 source, float sourceSize, int sourceShapeId, float sourceRotateAlign, vec2 target, float margin) {
  float lo = 0.0, hi = 0.5;
  float nodeExtent = sourceSize * u_correctionRatio / u_sizeRatio * 2.0;
  float effectiveSize = 1.0 - u_correctionRatio / nodeExtent;

  // Counter-rotate the query point so viewport-aligned nodes (rotateAlign=0) are
  // clamped against their on-screen orientation; graph-aligned nodes skip it.
  float ca = u_cameraAngle * (1.0 - sourceRotateAlign);
  float rc = cos(ca), rs = sin(ca);
  mat2 rot = mat2(rc, -rs, rs, rc);

  for (int i = 0; i < 12; i++) {
    float mid = (lo + hi) * 0.5;
    vec2 pos = path_`).concat(a,`_position(mid, source, target);
    vec2 localPos = rot * ((pos - source) / nodeExtent);
    float sdf = querySDF(sourceShapeId, localPos, effectiveSize);
    if (sdf < 0.0) lo = mid;
    else hi = mid;
  }

  float pathLen = path_`).concat(a,`_length(source, target);
  float marginT = (margin * u_correctionRatio / u_sizeRatio) / pathLen;
  return (lo + hi) * 0.5 + marginT;
}
`)}function Ui(a){return`
float findTargetClampT_`.concat(a,`(vec2 source, vec2 target, float targetSize, int targetShapeId, float targetRotateAlign, float margin) {
  float lo = 0.5, hi = 1.0;
  float nodeExtent = targetSize * u_correctionRatio / u_sizeRatio * 2.0;
  float effectiveSize = 1.0 - u_correctionRatio / nodeExtent;

  // See findSourceClampT_ for the rotation rationale.
  float ca = u_cameraAngle * (1.0 - targetRotateAlign);
  float rc = cos(ca), rs = sin(ca);
  mat2 rot = mat2(rc, -rs, rs, rc);

  for (int i = 0; i < 12; i++) {
    float mid = (lo + hi) * 0.5;
    vec2 pos = path_`).concat(a,`_position(mid, source, target);
    vec2 localPos = rot * ((pos - target) / nodeExtent);
    float sdf = querySDF(targetShapeId, localPos, effectiveSize);
    if (sdf < 0.0) hi = mid;
    else lo = mid;
  }

  float pathLen = path_`).concat(a,`_length(source, target);
  float marginT = (margin * u_correctionRatio / u_sizeRatio) / pathLen;
  return (lo + hi) * 0.5 - marginT;
}
`)}function wn(a){return`
// Auto-generated numerical tangent (from position via finite differences)
vec2 path_`.concat(a,`_tangent(float t, vec2 source, vec2 target) {
  float epsilon = 0.001;
  float t1 = max(0.0, t - epsilon);
  float t2 = min(1.0, t + epsilon);
  vec2 p1 = path_`).concat(a,`_position(t1, source, target);
  vec2 p2 = path_`).concat(a,`_position(t2, source, target);
  return normalize(p2 - p1);
}

// Auto-generated normal (perpendicular to tangent)
vec2 path_`).concat(a,`_normal(float t, vec2 source, vec2 target) {
  vec2 tangent = path_`).concat(a,`_tangent(t, source, target);
  return vec2(-tangent.y, tangent.x);
}
`)}function Oi(a){return`
// Auto-generated path length (samples position 16 times)
float path_`.concat(a,`_length(vec2 source, vec2 target) {
  float len = 0.0;
  vec2 prev = path_`).concat(a,`_position(0.0, source, target);
  for (int i = 1; i <= 16; i++) {
    float t = float(i) / 16.0;
    vec2 curr = path_`).concat(a,`_position(t, source, target);
    len += length(curr - prev);
    prev = curr;
  }
  return len;
}
`)}function Hi(a){return`
// Auto-generated closest_t (coarse sample + ternary search)
float path_`.concat(a,`_closest_t(vec2 p, vec2 source, vec2 target) {
  // Coarse search: find best among 10 samples
  float bestT = 0.0;
  float bestDist = 1e10;
  for (int i = 0; i <= 10; i++) {
    float t = float(i) / 10.0;
    vec2 pos = path_`).concat(a,`_position(t, source, target);
    float d = length(p - pos);
    if (d < bestDist) {
      bestDist = d;
      bestT = t;
    }
  }

  // Refine with ternary search
  float lo = max(0.0, bestT - 0.1);
  float hi = min(1.0, bestT + 0.1);
  for (int i = 0; i < 10; i++) {
    float mid1 = lo + (hi - lo) / 3.0;
    float mid2 = hi - (hi - lo) / 3.0;
    float d1 = length(p - path_`).concat(a,`_position(mid1, source, target));
    float d2 = length(p - path_`).concat(a,`_position(mid2, source, target));
    if (d1 < d2) {
      hi = mid2;
    } else {
      lo = mid1;
    }
  }
  return (lo + hi) * 0.5;
}
`)}function Vi(a){return`
// Auto-generated signed distance (via closest_t + normal)
float path_`.concat(a,`_distance(vec2 p, vec2 source, vec2 target) {
  float closestT = path_`).concat(a,`_closest_t(p, source, target);
  vec2 closest = path_`).concat(a,`_position(closestT, source, target);
  vec2 diff = p - closest;
  float dist = length(diff);
  if (dist < 0.0001) return 0.0;

  // Get normal at closest point
  vec2 normal = path_`).concat(a,`_normal(closestT, source, target);
  return dist * sign(dot(diff, normal));
}
`)}function Xi(a){return`
// Auto-generated t_at_distance (binary search)
float path_`.concat(a,`_t_at_distance(float targetDist, vec2 source, vec2 target) {
  if (targetDist <= 0.0) return 0.0;

  float totalLen = path_`).concat(a,`_length(source, target);
  if (targetDist >= totalLen) return 1.0;

  // Binary search for t
  float lo = 0.0, hi = 1.0;
  for (int i = 0; i < 12; i++) {
    float mid = (lo + hi) * 0.5;

    // Compute arc length from 0 to mid
    float arcLen = 0.0;
    vec2 prev = path_`).concat(a,`_position(0.0, source, target);
    for (int j = 1; j <= 8; j++) {
      float t = mid * float(j) / 8.0;
      vec2 curr = path_`).concat(a,`_position(t, source, target);
      arcLen += length(curr - prev);
      prev = curr;
    }

    if (arcLen < targetDist) {
      lo = mid;
    } else {
      hi = mid;
    }
  }
  return (lo + hi) * 0.5;
}
`)}function lt(a,r){var t=new RegExp("\\b(float|vec[234]|void|int|bool)\\s+".concat(r,"\\s*\\("));return t.test(a)}function In(a,r){var t=[];return lt(r,"path_".concat(a,"_length"))||t.push(Oi(a)),lt(r,"path_".concat(a,"_closest_t"))||t.push(Hi(a)),lt(r,"path_".concat(a,"_distance"))||t.push(Vi(a)),lt(r,"path_".concat(a,"_t_at_distance"))||t.push(Xi(a)),t.length>0?`
// ============================================================================
// Auto-generated fallback functions (path only provided position)
// ============================================================================
`.concat(t.join(`
`)):""}function zn(a){var r,t,e,n=a.paths,i=a.layers,o=(r=a.extremities)!==null&&r!==void 0?r:[];if(n.length===0)throw new Error("At least one path is required in 'paths'");if(i.length===0)throw new Error("At least one layer is required in 'layers'");var s=(t=a.defaultHead)!==null&&t!==void 0?t:"none",l=(e=a.defaultTail)!==null&&e!==void 0?e:"none";return{paths:n,extremities:o,layers:i,path:n[0],layer:i[0],defaultHead:s,defaultTail:l}}var Mn=WebGL2RenderingContext,bt=Mn.FLOAT,Ua=Mn.UNSIGNED_BYTE;function qi(a,r,t){var e=new Set(["u_matrix","u_sizeRatio","u_correctionRatio","u_zoomRatio","u_pixelRatio","u_cameraAngle","u_minEdgeThickness","u_pickingPadding","u_nodeDataTexture","u_nodeDataTextureWidth","u_edgeDataTexture","u_edgeDataTextureWidth","u_edgeFrameTexture","u_edgeFrameTextureWidth","u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge"]),n=new Set(e);return a.forEach(function(i){return i.uniforms.forEach(function(o){return n.add(o.name)})}),r.forEach(function(i){return i.uniforms.forEach(function(o){return n.add(o.name)})}),t.forEach(function(i){return i.uniforms.forEach(function(o){return n.add(o.name)})}),Array.from(n)}function fa(a){var r=new Set,t=[],e=M(a),n;try{for(e.s();!(n=e.n()).done;){var i=n.value;r.has(i.name)||(r.add(i.name),t.push("// Path: ".concat(i.name)),t.push(i.glsl),t.push(wn(i.name)),t.push(In(i.name,i.glsl)))}}catch(o){e.e(o)}finally{e.f()}return t.join(`

`)}function ji(a){var r=[],t=M(a),e;try{for(t.s();!(e=t.n()).done;){var n=e.value;r.push("// Extremity: ".concat(n.name)),r.push(n.glsl)}}catch(i){t.e(i)}finally{t.f()}return r.join(`

`)}var Yi=[{queryName:"queryPathPosition",pathFunc:"position",returnType:"vec2",params:"float t, vec2 source, vec2 target",args:"t, source, target"},{queryName:"queryPathTangent",pathFunc:"tangent",returnType:"vec2",params:"float t, vec2 source, vec2 target",args:"t, source, target"},{queryName:"queryPathNormal",pathFunc:"normal",returnType:"vec2",params:"float t, vec2 source, vec2 target",args:"t, source, target"},{queryName:"queryPathLength",pathFunc:"length",returnType:"float",params:"vec2 source, vec2 target",args:"source, target"},{queryName:"queryPathClosestT",pathFunc:"closest_t",returnType:"float",params:"vec2 p, vec2 source, vec2 target",args:"p, source, target"}];function Ki(a,r){var t=r.queryName,e=r.pathFunc,n=r.returnType,i=r.params,o=r.args;if(a.length===1)return"".concat(n," ").concat(t,"(int pathId, ").concat(i,`) {
  return path_`).concat(a[0].name,"_").concat(e,"(").concat(o,`);
}`);var s=a.map(function(l,d){return"    case ".concat(d,": return path_").concat(l.name,"_").concat(e,"(").concat(o,");")}).join(`
`);return"".concat(n," ").concat(t,"(int pathId, ").concat(i,`) {
  switch (pathId) {
`).concat(s,`
    default: return path_`).concat(a[0].name,"_").concat(e,"(").concat(o,`);
  }
}`)}function ga(a){return Yi.map(function(r){return Ki(a,r)}).join(`

`)}function Zi(a){if(a.length===1)return`float queryExtremitySDF(int extremityId, vec2 uv, float lengthRatio, float widthRatio) {
  return extremity_`.concat(a[0].name,`(uv, lengthRatio, widthRatio);
}`);var r=a.map(function(t,e){return"    case ".concat(e,": return extremity_").concat(t.name,"(uv, lengthRatio, widthRatio);")}).join(`
`);return`float queryExtremitySDF(int extremityId, vec2 uv, float lengthRatio, float widthRatio) {
  switch (extremityId) {
`.concat(r,`
    default: return extremity_`).concat(a[0].name,`(uv, lengthRatio, widthRatio);
  }
}`)}function $i(a){var r=[],t=M(a),e;try{for(t.s();!(e=t.n()).done;){var n=e.value;r.push(Wi(n.name)),r.push(Ui(n.name))}}catch(s){t.e(s)}finally{t.f()}if(a.length===1)r.push(`
float queryFindSourceClampT(int pathId, vec2 source, float sourceSize, int sourceShapeId, float sourceRotateAlign, vec2 target, float margin) {
  return findSourceClampT_`.concat(a[0].name,`(source, sourceSize, sourceShapeId, sourceRotateAlign, target, margin);
}

float queryFindTargetClampT(int pathId, vec2 source, vec2 target, float targetSize, int targetShapeId, float targetRotateAlign, float margin) {
  return findTargetClampT_`).concat(a[0].name,`(source, target, targetSize, targetShapeId, targetRotateAlign, margin);
}`));else{var i=a.map(function(s,l){return"    case ".concat(l,": return findSourceClampT_").concat(s.name,"(source, sourceSize, sourceShapeId, sourceRotateAlign, target, margin);")}).join(`
`),o=a.map(function(s,l){return"    case ".concat(l,": return findTargetClampT_").concat(s.name,"(source, target, targetSize, targetShapeId, targetRotateAlign, margin);")}).join(`
`);r.push(`
float queryFindSourceClampT(int pathId, vec2 source, float sourceSize, int sourceShapeId, float sourceRotateAlign, vec2 target, float margin) {
  switch (pathId) {
`.concat(i,`
    default: return findSourceClampT_`).concat(a[0].name,`(source, sourceSize, sourceShapeId, sourceRotateAlign, target, margin);
  }
}

float queryFindTargetClampT(int pathId, vec2 source, vec2 target, float targetSize, int targetShapeId, float targetRotateAlign, float margin) {
  switch (pathId) {
`).concat(o,`
    default: return findTargetClampT_`).concat(a[0].name,`(source, target, targetSize, targetShapeId, targetRotateAlign, margin);
  }
}`))}return r.join(`

`)}function Qi(a,r,t){var e=fe([].concat(H(a),H(t))),n=nt(e),i=new Set,o=[],s=function(c){i.has(c.name)||(i.add(c.name),o.push("uniform ".concat(c.type," ").concat(c.name,";")))};a.forEach(function(u){return u.uniforms.forEach(s)}),r.forEach(function(u){return u.uniforms.forEach(s)});var l=r.map(function(u){return Y(u.widthFactor)}).join(", "),d=Math.max.apply(Math,H(a.map(function(u){return u.minBodyLengthRatio||0}))),h=`#version 300 es

// Node and edge data textures
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_edgeDataTexture;
uniform int u_edgeDataTextureWidth;

// Edge attribute texture (for path-specific attributes like curvature)
`.concat(n.uniformDeclarations,`

// Render params needed for clamping
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform float u_minEdgeThickness;

// Edge-frame texture dimensions, for scattering each point to its texel
uniform float u_frameTextureWidth;
uniform float u_frameTextureHeight;

// Custom path/extremity uniforms
`).concat(o.join(`
`),`

// Path attribute varyings — assigned so path functions can read them as globals
`).concat(n.vertexVaryingDeclarations,`

// Node size varyings — read by path functions like loop
out float v_sourceNodeSize;
out float v_targetNodeSize;

// Scattered output written to the edge-frame texel: [tStart, tEnd, straightenFactor, pathLength]
out vec4 v_clamp;

// Extremity width factor array (needed for extremityScale computation)
const float EXTREMITY_WIDTH_FACTORS[`).concat(r.length,"] = float[](").concat(l,`);

// Node-data fetch helpers (geometry texel + rotation-flags texel)
`).concat(be,`
`).concat(Pe,`

// Shape SDFs for node boundary clamping
`).concat(ui(),`
`).concat(hi(),`

// Path functions
`).concat(fa(a),`
`).concat(ga(a),`
`).concat($i(a),`

void main() {
  // One point per edge-data row; the row index is the edge-frame texel target.
  int edgeIdx = gl_VertexID;
  int texel0Idx = edgeIdx * 2;
  int texel1Idx = edgeIdx * 2 + 1;
  ivec2 edgeTexCoord0 = ivec2(texel0Idx % u_edgeDataTextureWidth, texel0Idx / u_edgeDataTextureWidth);
  ivec2 edgeTexCoord1 = ivec2(texel1Idx % u_edgeDataTextureWidth, texel1Idx / u_edgeDataTextureWidth);
  vec4 edgeData0 = texelFetch(u_edgeDataTexture, edgeTexCoord0, 0);
  vec4 edgeData1 = texelFetch(u_edgeDataTexture, edgeTexCoord1, 0);

  int srcIdx = int(edgeData0.x);
  int tgtIdx = int(edgeData0.y);
  float a_thickness = edgeData0.z;
  float a_headLengthRatio = edgeData1.x;
  float a_tailLengthRatio = edgeData1.y;
  int pathId = int(edgeData1.z);
  int extremityPacked = int(edgeData1.w);
  int headId = extremityPacked >> 4;
  int tailId = extremityPacked & 15;

  // Fetch path/layer attributes and assign to path-function globals
`).concat(n.fetchCode,`
`).concat(n.varyingAssignments,`

  // Fetch node geometry (texel 0) and rotation flags (texel 1).
  vec4 srcNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  vec4 tgtNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);

  vec2 a_source = srcNodeData.xy;
  vec2 a_target = tgtNodeData.xy;
  float a_sourceSize = srcNodeData.z;
  float a_targetSize = tgtNodeData.z;
  float a_sourceShapeId = srcNodeData.w;
  float a_targetShapeId = tgtNodeData.w;
  // Per-node rotation alignment (0 = viewport, 1 = graph), for boundary clamping.
  float a_sourceRotateAlign = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx).r;
  float a_targetRotateAlign = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx).r;

  v_sourceNodeSize = a_sourceSize;
  v_targetNodeSize = a_targetSize;

  float headLengthRatio = a_headLengthRatio;
  float tailLengthRatio = a_tailLengthRatio;
  float headWidthFactor = EXTREMITY_WIDTH_FACTORS[headId];
  float tailWidthFactor = EXTREMITY_WIDTH_FACTORS[tailId];
  float minBodyLengthRatio = `).concat(Y(d),`;

  // Thickness in WebGL units (needed to compute clamping margin and extremity lengths)
  float pixelsThickness = max(a_thickness, u_minEdgeThickness * u_sizeRatio);
  float webGLThickness = pixelsThickness * u_correctionRatio / u_sizeRatio;

  // SDF clamping: find where the edge body meets the node boundaries. Always
  // searched (ungated) so labels get a true boundary clamp; the body re-applies
  // its extremity gating in-shader.
  float tStart = queryFindSourceClampT(pathId, a_source, a_sourceSize, int(a_sourceShapeId), a_sourceRotateAlign, a_target, 0.0);
  float tEnd = queryFindTargetClampT(pathId, a_source, a_target, a_targetSize, int(a_targetShapeId), a_targetRotateAlign, 0.0);

  // straightenFactor (frame .z) is consumed only by the body, which runs to the
  // node center when an extremity is absent. Derive the straightening math from
  // these gated clamps — not the ungated boundary ones above — so it matches the
  // geometry it drives. The ungated tStart/tEnd remain what labels read.
  float bodyTStart = tailLengthRatio > 0.0 ? tStart : 0.0;
  float bodyTEnd = headLengthRatio > 0.0 ? tEnd : 1.0;

  // Path length and zone boundaries (needed for straightening check)
  float pathLength = queryPathLength(pathId, a_source, a_target);
  float visibleLength = pathLength * (bodyTEnd - bodyTStart);

  float headLength = headLengthRatio * webGLThickness;
  float tailLength = tailLengthRatio * webGLThickness;
  float minBodyLength = minBodyLengthRatio * webGLThickness;

  float totalNeededLength = headLength + tailLength + minBodyLength;
  float extremityScale = 1.0;
  if (totalNeededLength > visibleLength && totalNeededLength > 0.0001) {
    extremityScale = visibleLength / totalNeededLength;
    headLength *= extremityScale;
    tailLength *= extremityScale;
  }

  float headLengthT = pathLength > 0.0001 ? headLength / pathLength : 0.0;
  float tailLengthT = pathLength > 0.0001 ? tailLength / pathLength : 0.0;

  float tTailEnd = bodyTStart + tailLengthT;
  float tHeadStart = bodyTEnd - headLengthT;
  if (tTailEnd > tHeadStart) {
    float mid = (bodyTStart + bodyTEnd) * 0.5;
    tTailEnd = mid;
    tHeadStart = mid;
  }

  // Straighten factor: blend toward straight line when path twists in extremity zones
  float straightenFactor = 0.0;
  {
    float maxDeviation = 0.0;
    if (tailLengthT > 0.0001) {
      vec2 tailTang = queryPathTangent(pathId, tTailEnd, a_source, a_target);
      vec2 tailChord = queryPathPosition(pathId, bodyTStart, a_source, a_target)
                     - queryPathPosition(pathId, tTailEnd, a_source, a_target);
      float tailChordLen = length(tailChord);
      if (tailChordLen > 0.0001) {
        maxDeviation = max(maxDeviation, 1.0 - dot(-tailTang, tailChord / tailChordLen));
      }
    }
    if (headLengthT > 0.0001) {
      vec2 headTang = queryPathTangent(pathId, tHeadStart, a_source, a_target);
      vec2 headChord = queryPathPosition(pathId, bodyTEnd, a_source, a_target)
                     - queryPathPosition(pathId, tHeadStart, a_source, a_target);
      float headChordLen = length(headChord);
      if (headChordLen > 0.0001) {
        maxDeviation = max(maxDeviation, 1.0 - dot(headTang, headChord / headChordLen));
      }
    }
    straightenFactor = smoothstep(0.035, 0.5, maxDeviation);
  }

  // When straightening, blend the ungated tStart/tEnd (the label-facing clamps)
  // toward straight-line clamp positions.
  if (straightenFactor > 0.001) {
    if (tailLengthRatio > 0.0) {
      float srcExtent = a_sourceSize * u_correctionRatio / u_sizeRatio * 2.0;
      float srcEffective = 1.0 - u_correctionRatio / srcExtent;
      float srcCa = u_cameraAngle * (1.0 - a_sourceRotateAlign);
      mat2 srcRot = mat2(cos(srcCa), -sin(srcCa), sin(srcCa), cos(srcCa));
      float lo = 0.0, hi = 0.5;
      for (int i = 0; i < 12; i++) {
        float mid = (lo + hi) * 0.5;
        vec2 pos = mix(a_source, a_target, mid);
        vec2 localPos = srcRot * ((pos - a_source) / srcExtent);
        float sdf = querySDF(int(a_sourceShapeId), localPos, srcEffective);
        if (sdf < 0.0) lo = mid; else hi = mid;
      }
      tStart = mix(tStart, (lo + hi) * 0.5, straightenFactor);
    }
    if (headLengthRatio > 0.0) {
      float tgtExtent = a_targetSize * u_correctionRatio / u_sizeRatio * 2.0;
      float tgtEffective = 1.0 - u_correctionRatio / tgtExtent;
      float tgtCa = u_cameraAngle * (1.0 - a_targetRotateAlign);
      mat2 tgtRot = mat2(cos(tgtCa), -sin(tgtCa), sin(tgtCa), cos(tgtCa));
      float lo = 0.5, hi = 1.0;
      for (int i = 0; i < 12; i++) {
        float mid = (lo + hi) * 0.5;
        vec2 pos = mix(a_source, a_target, mid);
        vec2 localPos = tgtRot * ((pos - a_target) / tgtExtent);
        float sdf = querySDF(int(a_targetShapeId), localPos, tgtEffective);
        if (sdf < 0.0) hi = mid; else lo = mid;
      }
      tEnd = mix(tEnd, (lo + hi) * 0.5, straightenFactor);
    }
  }

  v_clamp = vec4(tStart, tEnd, straightenFactor, pathLength);

  // Scatter this point to its edge's texel center in the frame texture.
  float x = mod(float(edgeIdx), u_frameTextureWidth);
  float y = floor(float(edgeIdx) / u_frameTextureWidth);
  vec2 ndc = (vec2(x, y) + 0.5) / vec2(u_frameTextureWidth, u_frameTextureHeight) * 2.0 - 1.0;
  gl_Position = vec4(ndc, 0.0, 1.0);
  gl_PointSize = 1.0;
}
`);return h}var dt=0,Oa=1,ut=2;function Ji(a,r,t){var e=[];t&&(e.push([dt,0,-1],[dt,0,1]),e.push([dt,1,-1],[dt,1,1]));for(var n=0;n<=a;n++){var i=n/a;e.push([Oa,i,-1],[Oa,i,1])}return r&&(e.push([ut,0,-1],[ut,0,1]),e.push([ut,1,-1],[ut,1,1])),{data:e,attributes:[{name:"a_zone",size:1,type:bt},{name:"a_zoneT",size:1,type:bt},{name:"a_side",size:1,type:bt}],verticesPerEdge:e.length}}function eo(a,r,t,e){var n=fe([].concat(H(a),H(t))),i=nt(n),o=new Set(["u_matrix","u_sizeRatio","u_correctionRatio","u_zoomRatio","u_pixelRatio","u_cameraAngle","u_minEdgeThickness","u_pickingPadding","u_nodeDataTexture"]),s=new Set,l=[],d=function(m){!o.has(m.name)&&!s.has(m.name)&&(s.add(m.name),l.push("uniform ".concat(m.type," ").concat(m.name,";")))};a.forEach(function(b){return b.uniforms.forEach(d)}),r.forEach(function(b){return b.uniforms.forEach(d)}),t.forEach(function(b){return b.uniforms.forEach(d)});var h=e.map(function(b){var m=b.size===1?"float":"vec".concat(b.size);return"in ".concat(m," ").concat(b.name,";")}).join(`
`),u=r.map(function(b){return Y(b.widthFactor)}).join(", "),c=Math.max.apply(Math,H(a.map(function(b){return b.minBodyLengthRatio||0}))),v=`#version 300 es

// Constant attributes (per vertex)
`.concat(h,`

// Per-edge attributes
// Edge data (source/target indices, thickness, extremity ratios, path/extremity IDs)
// is fetched from edge data texture via edge index
in float a_edgeIndex;   // Index into edge data texture
in vec4 a_color;        // Edge color
in vec4 a_id;           // Edge ID for picking

// Standard uniforms
uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_zoomRatio;
uniform float u_pixelRatio;
uniform float u_cameraAngle;
uniform float u_minEdgeThickness;
#ifdef PICKING_MODE
uniform float u_pickingPadding;
#endif
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_edgeDataTexture;
uniform int u_edgeDataTextureWidth;
uniform sampler2D u_edgeFrameTexture;
uniform int u_edgeFrameTextureWidth;

// Edge path attribute texture uniforms
`).concat(i.uniformDeclarations,`

// Custom uniforms
`).concat(l.join(`
`),`

// Standard varyings
out vec4 v_color;
out vec4 v_id;
out float v_thickness;       // Edge body thickness (in consistent units)
out float v_maxWidthFactor;  // Max width factor for geometry expansion
out float v_t;
out float v_tStart;
out float v_tEnd;
out float v_side;
out float v_antialiasingWidth;  // Anti-aliasing width (normalized: u_correctionRatio / thickness)
out vec2 v_source;
out vec2 v_target;
out float v_edgeLength;
out vec2 v_position;         // World position of the vertex (for position-based distance)
out float v_sourceNodeSize;  // Source node size (mirrored in labels/generator.ts as plain float)
out float v_targetNodeSize;  // Target node size (mirrored in labels/generator.ts as plain float)

// Zone varyings
out float v_zone;            // 0=tail, 1=body, 2=head
out float v_zoneT;           // Position within zone [0,1]
out float v_headLengthRatio; // Head length as ratio of thickness
out float v_tailLengthRatio; // Tail length as ratio of thickness
out float v_headWidthRatio;  // Head width factor
out float v_tailWidthRatio;  // Tail width factor

// Multi-path/extremity varyings
flat out int v_pathId;
flat out int v_headId;
flat out int v_tailId;

// Path/layer attribute varyings (fetched from edge attribute texture)
`).concat(i.vertexVaryingDeclarations,`

const float bias = 255.0 / 254.0;

// Width factor array for extremities (shared pool for head/tail)
const float EXTREMITY_WIDTH_FACTORS[`).concat(r.length,"] = float[](").concat(u,`);

// All path functions
`).concat(fa(a),`

// Path selector functions
`).concat(ga(a),`

// Node-data fetch helper (geometry texel of the two-texel node stride)
`).concat(be,`

// Per-edge clamp from the frame-pass (tStart, tEnd, straightenFactor, pathLength)
`).concat(Ve,`

void main() {
  // Fetch edge data from edge texture (2 texels per edge)
  // Texel 0: sourceNodeIndex, targetNodeIndex, thickness, reserved
  // Texel 1: headLengthRatio, tailLengthRatio, pathId, (headId << 4) | tailId
  int edgeIdx = int(a_edgeIndex);
  int texel0Idx = edgeIdx * 2;
  int texel1Idx = edgeIdx * 2 + 1;
  ivec2 edgeTexCoord0 = ivec2(texel0Idx % u_edgeDataTextureWidth, texel0Idx / u_edgeDataTextureWidth);
  ivec2 edgeTexCoord1 = ivec2(texel1Idx % u_edgeDataTextureWidth, texel1Idx / u_edgeDataTextureWidth);
  vec4 edgeData0 = texelFetch(u_edgeDataTexture, edgeTexCoord0, 0);
  vec4 edgeData1 = texelFetch(u_edgeDataTexture, edgeTexCoord1, 0);

  // Unpack edge data
  int srcIdx = int(edgeData0.x);
  int tgtIdx = int(edgeData0.y);
  float a_thickness = edgeData0.z;
  // edgeData0.w is now reserved (curvature moved to path attribute texture)
  float a_headLengthRatio = edgeData1.x;
  float a_tailLengthRatio = edgeData1.y;
  int pathId = int(edgeData1.z);
  int extremityPacked = int(edgeData1.w);
  int headId = extremityPacked >> 4;
  int tailId = extremityPacked & 15;

  // Fetch path/layer attributes from edge attribute texture
`).concat(i.fetchCode,`

  // Assign path/layer attribute varyings
`).concat(i.varyingAssignments,`

  // Fetch source and target node geometry (texel 0 of the two-texel node stride)
  vec4 srcNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  vec4 tgtNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);

  vec2 a_source = srcNodeData.xy;
  vec2 a_target = tgtNodeData.xy;
  float a_sourceSize = srcNodeData.z;
  float a_targetSize = tgtNodeData.z;

  // Assign node size varyings early (path functions like loops need them during clamping)
  v_sourceNodeSize = a_sourceSize;
  v_targetNodeSize = a_targetSize;

  // Convert thickness to WebGL units
  float minThickness = u_minEdgeThickness;
  float pixelsThickness = max(a_thickness, minThickness * u_sizeRatio);
  float webGLThickness = pixelsThickness * u_correctionRatio / u_sizeRatio;

  // Extremity parameters from ID lookups (shared pool)
  float headLengthRatio = a_headLengthRatio;
  float tailLengthRatio = a_tailLengthRatio;
  float headWidthFactor = EXTREMITY_WIDTH_FACTORS[headId];
  float tailWidthFactor = EXTREMITY_WIDTH_FACTORS[tailId];
  float minBodyLengthRatio = `).concat(Y(c),`;

  // Per-edge values from the frame-pass texture (read by edge index).
  // tStart/tEnd are the ungated boundary clamps: re-apply the body's extremity
  // gating here (no extremity → body runs to the node center, 0/1).
  vec4 frameClamp = readFrameTexel(u_edgeFrameTexture, u_edgeFrameTextureWidth, edgeIdx);
  float tStart           = a_tailLengthRatio > 0.0 ? frameClamp.x : 0.0;
  float tEnd             = a_headLengthRatio > 0.0 ? frameClamp.y : 1.0;
  float straightenFactor = frameClamp.z;
  float pathLength       = frameClamp.w;

  // Width factor for geometry expansion (use max of both extremities)
  float widthFactor = max(max(headWidthFactor, tailWidthFactor), 1.0);

  // Anti-aliasing width (~1 pixel, normalized by thickness)
  float antialiasingWidth = u_correctionRatio / webGLThickness;

  float visibleLength = pathLength * (tEnd - tStart);

  // Compute extremity lengths in world units
  float headLength = headLengthRatio * webGLThickness;
  float tailLength = tailLengthRatio * webGLThickness;
  float minBodyLength = minBodyLengthRatio * webGLThickness;

  // Handle short edges: scale down extremities if needed
  float totalNeededLength = headLength + tailLength + minBodyLength;
  float extremityScale = 1.0;
  if (totalNeededLength > visibleLength && totalNeededLength > 0.0001) {
    extremityScale = visibleLength / totalNeededLength;
    headLength *= extremityScale;
    tailLength *= extremityScale;
  }

  // Convert lengths to t-values
  float headLengthT = pathLength > 0.0001 ? headLength / pathLength : 0.0;
  float tailLengthT = pathLength > 0.0001 ? tailLength / pathLength : 0.0;

  // Zone boundaries in t-space
  float tTailEnd = tStart + tailLengthT;
  float tHeadStart = tEnd - headLengthT;

  // Ensure body has non-negative length
  if (tTailEnd > tHeadStart) {
    float mid = (tStart + tEnd) * 0.5;
    tTailEnd = mid;
    tHeadStart = mid;
  }

  // Convert to webGL units for geometry expansion
  float aaWidthWebGL = antialiasingWidth * webGLThickness;

  // Extra geometry width for picking padding (0 in visual mode)
  #ifdef PICKING_MODE
    float pickingPaddingWebGL = u_pickingPadding * u_correctionRatio;
  #else
    float pickingPaddingWebGL = 0.0;
  #endif

  // Straight-line direction and normal (for blending when straightenFactor > 0)
  vec2 straightDir = length(a_target - a_source) > 0.0001
    ? normalize(a_target - a_source) : vec2(1.0, 0.0);
  vec2 straightNormal = vec2(-straightDir.y, straightDir.x);

  // Zone-based vertex processing using path selectors
  vec2 position;
  vec2 normal;
  float t;
  float zone = a_zone;
  float zoneT = a_zoneT;
  float side = a_side;

  // Scaled extremity width factors (geometry must be at least as wide as body)
  float scaledTailWidth = max(tailWidthFactor * extremityScale, 1.0);
  float scaledHeadWidth = max(headWidthFactor * extremityScale, 1.0);

  if (zone < 0.5) {
    // TAIL ZONE: rectangular quad with scaled width
    vec2 tang = queryPathTangent(pathId, tTailEnd, a_source, a_target);
    normal = vec2(-tang.y, tang.x);
    vec2 centerPos = mix(queryPathPosition(pathId, tStart, a_source, a_target),
                         queryPathPosition(pathId, tTailEnd, a_source, a_target), zoneT);
    float halfWidth = webGLThickness * scaledTailWidth * 0.5 + aaWidthWebGL + pickingPaddingWebGL;
    position = centerPos + normal * side * halfWidth;
    t = mix(tStart, tTailEnd, zoneT);

  } else if (zone < 1.5) {
    // BODY ZONE: follows path curvature with width = 1.0
    t = mix(tTailEnd, tHeadStart, zoneT);
    normal = queryPathNormal(pathId, t, a_source, a_target);
    float halfWidth = webGLThickness * 0.5 + aaWidthWebGL + pickingPaddingWebGL;
    position = queryPathPosition(pathId, t, a_source, a_target) + normal * side * halfWidth;

  } else {
    // HEAD ZONE: rectangular quad with scaled width
    vec2 tang = queryPathTangent(pathId, tHeadStart, a_source, a_target);
    normal = vec2(-tang.y, tang.x);
    vec2 centerPos = mix(queryPathPosition(pathId, tHeadStart, a_source, a_target),
                         queryPathPosition(pathId, tEnd, a_source, a_target), zoneT);
    float halfWidth = webGLThickness * scaledHeadWidth * 0.5 + aaWidthWebGL + pickingPaddingWebGL;
    position = centerPos + normal * side * halfWidth;
    t = mix(tHeadStart, tEnd, zoneT);
  }

  // Blend toward straight line based on path twist in extremity zones
  if (straightenFactor > 0.001) {
    float zoneWidth = zone < 0.5 ? webGLThickness * scaledTailWidth * 0.5 + aaWidthWebGL + pickingPaddingWebGL :
                      zone < 1.5 ? webGLThickness * 0.5 + aaWidthWebGL + pickingPaddingWebGL :
                      webGLThickness * scaledHeadWidth * 0.5 + aaWidthWebGL + pickingPaddingWebGL;
    vec2 straightPos = mix(a_source, a_target, t) + straightNormal * side * zoneWidth;
    position = mix(position, straightPos, straightenFactor);
  }

  gl_Position = vec4((u_matrix * vec3(position, 1.0)).xy, 0.0, 1.0);

  // Pass varyings to fragment shader
  v_color = a_color;
  v_color.a *= bias;
  v_id = a_id;
  v_thickness = webGLThickness;
  v_maxWidthFactor = widthFactor;
  v_t = t;
  v_tStart = tStart;
  v_tEnd = tEnd;
  v_side = side;
  v_antialiasingWidth = antialiasingWidth;
  v_source = a_source;
  v_target = a_target;
  v_edgeLength = pathLength;
  v_position = position;

  // Zone varyings
  v_zone = zone;
  v_zoneT = zoneT;
  v_headLengthRatio = headLengthRatio * extremityScale;
  v_tailLengthRatio = tailLengthRatio * extremityScale;
  // Scale extremity width proportionally with length when crushed
  v_headWidthRatio = headWidthFactor * extremityScale;
  v_tailWidthRatio = tailWidthFactor * extremityScale;

  // Multi-path varyings
  v_pathId = pathId;
  v_headId = headId;
  v_tailId = tailId;
}
`);return v}function to(a,r,t){var e=fe([].concat(H(a),H(t))),n=nt(e),i=new Set(["u_matrix","u_sizeRatio","u_correctionRatio","u_zoomRatio","u_pixelRatio","u_cameraAngle","u_minEdgeThickness","u_pickingPadding"]),o=new Set,s=[],l=function(v){!i.has(v.name)&&!o.has(v.name)&&(o.add(v.name),s.push("uniform ".concat(v.type," ").concat(v.name,";")))};a.forEach(function(c){return c.uniforms.forEach(l)}),r.forEach(function(c){return c.uniforms.forEach(l)}),t.forEach(function(c){return c.uniforms.forEach(l)});var d=r.map(function(c){var v;return Y((v=c.baseRatio)!==null&&v!==void 0?v:.5)}).join(", "),h=t.map(function(c,v){return"  // Layer ".concat(v+1,": ").concat(c.name,`
  color = blendOver(color, layer_`).concat(c.name,"(context));")}).join(`

`),u=`#version 300 es
precision highp float;

// Standard varyings
in vec4 v_color;
in vec4 v_id;
in float v_thickness;       // Edge body thickness
in float v_maxWidthFactor;  // Max width factor for geometry expansion
in float v_t;
in float v_tStart;
in float v_tEnd;
in float v_side;
in float v_antialiasingWidth;  // Anti-aliasing width (normalized: u_correctionRatio / thickness)
in vec2 v_source;
in vec2 v_target;
in float v_edgeLength;
in vec2 v_position;          // World position of the fragment
in float v_sourceNodeSize;   // Source node size (mirrored in labels/generator.ts as plain float)
in float v_targetNodeSize;   // Target node size (mirrored in labels/generator.ts as plain float)

// Zone varyings
in float v_zone;            // 0=tail, 1=body, 2=head
in float v_zoneT;           // Position within zone [0,1]
in float v_headLengthRatio; // Head length as ratio of thickness (scaled for short edges)
in float v_tailLengthRatio; // Tail length as ratio of thickness (scaled for short edges)
in float v_headWidthRatio;  // Head width factor
in float v_tailWidthRatio;  // Tail width factor

// Multi-path/extremity varyings
flat in int v_pathId;
flat in int v_headId;
flat in int v_tailId;

// Path/layer attribute varyings (from vertex shader texture fetch)
`.concat(n.fragmentVaryingDeclarations,`

// Standard uniforms (needed by some path types)
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
#ifdef PICKING_MODE
uniform float u_pickingPadding;
#endif

// Custom uniforms
`).concat(s.join(`
`),`

// Fragment output (single target - picking handled via separate pass)
out vec4 fragColor;

// Base ratio array for extremities (shared pool for head/tail)
const float EXTREMITY_BASE_RATIOS[`).concat(r.length,"] = float[](").concat(d,`);

// EdgeContext struct
struct EdgeContext {
  float t;                   // Position along path [0, 1]
  float sdf;                 // Signed distance from centerline
  vec2 position;             // World position
  vec2 tangent;              // Path tangent
  vec2 normal;               // Path normal
  float thickness;           // Edge thickness
  float aaWidth;             // Anti-aliasing width
  float edgeLength;          // Total path length
  float tStart;              // Clamped start t
  float tEnd;                // Clamped end t
  float distanceFromSource;  // Arc distance from source
  float distanceToTarget;    // Arc distance to target
};

EdgeContext context;

// Alpha "over" compositing for layer blending
vec4 blendOver(vec4 bg, vec4 fg) {
  float a = fg.a;
  return vec4(mix(bg.rgb, fg.rgb, a), bg.a + a * (1.0 - bg.a));
}

// All path functions
`).concat(fa(a),`

// Path selector functions
`).concat(ga(a),`

// All extremity functions
`).concat(ji(r),`

// Extremity SDF selector (shared pool for head/tail)
`).concat(Zi(r),`

// Layer functions
`).concat(t.map(function(c){return c.glsl}).join(`

`),`

// Helper: Compute arc length using path selector
float computeArcLengthMulti(int pathId, float t0, float t1, vec2 source, vec2 target, int samples) {
  float arcLen = 0.0;
  vec2 prev = queryPathPosition(pathId, t0, source, target);
  for (int i = 1; i <= samples; i++) {
    float t = t0 + (t1 - t0) * float(i) / float(samples);
    vec2 curr = queryPathPosition(pathId, t, source, target);
    arcLen += length(curr - prev);
    prev = curr;
  }
  return arcLen;
}

void main() {
  // Compute normalized t within visible edge (0 = start, 1 = end)
  float tNorm = (v_t - v_tStart) / max(v_tEnd - v_tStart, 0.0001);

  // Edge body half-thickness
  float halfThickness = v_thickness * 0.5;

  // Convert normalized AA width to webGL units (~1 pixel)
  float aaWidthWebGL = v_antialiasingWidth * v_thickness;

  // Distance from centerline based on v_side interpolation
  float zoneWidthFactor = v_zone < 0.5 ? v_tailWidthRatio :
                          v_zone < 1.5 ? 1.0 :
                          v_headWidthRatio;
  // In PICKING_MODE, inflate halfGeometryWidth to match the inflated vertex geometry
  #ifdef PICKING_MODE
    float halfGeometryWidth = halfThickness * zoneWidthFactor + aaWidthWebGL + u_pickingPadding * aaWidthWebGL;
  #else
    float halfGeometryWidth = halfThickness * zoneWidthFactor + aaWidthWebGL;
  #endif
  float distFromCenter = abs(v_side) * halfGeometryWidth;

  // Populate EdgeContext (for layer functions)
  context.t = tNorm;
  context.sdf = distFromCenter - halfThickness;
  context.position = queryPathPosition(v_pathId, v_t, v_source, v_target);
  context.tangent = queryPathTangent(v_pathId, v_t, v_source, v_target);
  context.normal = queryPathNormal(v_pathId, v_t, v_source, v_target);
  context.thickness = v_thickness;
  context.aaWidth = aaWidthWebGL;
  context.edgeLength = v_edgeLength;
  context.tStart = v_tStart;
  context.tEnd = v_tEnd;

  // Compute arc distances
  float visibleLength = v_edgeLength * (v_tEnd - v_tStart);
  float pathT = v_t;
  float pathTNorm = tNorm;
`).concat(a.every(function(c){return c.linearParameterization})?`  // All paths have linear parameterization: t maps directly to arc distance
  context.distanceFromSource = pathTNorm * visibleLength;
  context.distanceToTarget = (1.0 - pathTNorm) * visibleLength;`:a.every(function(c){return!c.linearParameterization})?`  // No paths have linear parameterization: use numerical integration
  context.distanceFromSource = computeArcLengthMulti(v_pathId, v_tStart, pathT, v_source, v_target, 16);
  context.distanceToTarget = computeArcLengthMulti(v_pathId, pathT, v_tEnd, v_source, v_target, 16);`:`  // Mixed parameterization: use analytical for linear paths, numerical for others
  if (`.concat(a.filter(function(c){return c.linearParameterization}).map(function(c){return"v_pathId == ".concat(a.indexOf(c))}).join(" || "),`) {
    context.distanceFromSource = pathTNorm * visibleLength;
    context.distanceToTarget = (1.0 - pathTNorm) * visibleLength;
  } else {
    context.distanceFromSource = computeArcLengthMulti(v_pathId, v_tStart, pathT, v_source, v_target, 16);
    context.distanceToTarget = computeArcLengthMulti(v_pathId, pathT, v_tEnd, v_source, v_target, 16);
  }`),`

  // Compute SDF based on zone using extremity selector (shared pool)
  float bodySDF = distFromCenter - halfThickness;
  float finalSDF;

  // Get base ratios from shared array
  float headBaseRatio = EXTREMITY_BASE_RATIOS[v_headId];
  float tailBaseRatio = EXTREMITY_BASE_RATIOS[v_tailId];

  if (v_zone < 0.5) {
    // TAIL ZONE: v_zoneT goes 0 (tip) to 1 (base)
    vec2 uv = vec2((1.0 - v_zoneT) * v_tailLengthRatio, v_side * v_tailWidthRatio * 0.5);
    float tailSDF = queryExtremitySDF(v_tailId, uv, v_tailLengthRatio, v_tailWidthRatio) * v_thickness;

    // Apply union only near base (v_zoneT > 1 - baseRatio)
    if (v_zoneT > 1.0 - tailBaseRatio) {
      finalSDF = min(tailSDF, bodySDF);
    } else {
      finalSDF = tailSDF;
    }
  } else if (v_zone < 1.5) {
    // BODY ZONE: distance from centerline
    finalSDF = bodySDF;
  } else {
    // HEAD ZONE: v_zoneT goes 0 (base) to 1 (tip)
    vec2 uv = vec2(v_zoneT * v_headLengthRatio, v_side * v_headWidthRatio * 0.5);
    float headSDF = queryExtremitySDF(v_headId, uv, v_headLengthRatio, v_headWidthRatio) * v_thickness;

    // Apply union only near base (v_zoneT < baseRatio)
    if (v_zoneT < headBaseRatio) {
      finalSDF = min(headSDF, bodySDF);
    } else {
      finalSDF = headSDF;
    }
  }

  #ifdef PICKING_MODE
    // Picking pass: output edge ID for pixels within the picking area
    if (finalSDF > u_pickingPadding * aaWidthWebGL) discard;
    fragColor = v_id;
  #else
    // Visual pass: anti-aliased edge with layers
    float alpha = smoothstep(aaWidthWebGL, -aaWidthWebGL, finalSDF);
    if (alpha < 0.01) discard;

    // Apply layers sequentially with "over" compositing
    vec4 color = vec4(0.0);

`).concat(h,`

    // Mix with transparent to fade both color AND alpha (pre-multiplied alpha for correct blending)
    fragColor = mix(vec4(0.0), color, alpha);
  #endif
}
`);return u}function ao(a,r,t){var e=De(r.length)?!0:r.length>0,n=De(t.length)?!0:t.length>0;if(a.generateConstantData){var i=a.generateConstantData();return{data:i.data,attributes:i.attributes,verticesPerEdge:i.verticesPerEdge}}return Ji(a.segments,e,n)}function Ha(a){var r=zn(a),t=r.paths,e=r.extremities,n=r.layers,i=new Map,o=new Map,s=new Map,l=M(t),d;try{for(l.s();!(d=l.n()).done;){var h=d.value,u=M(e),c;try{for(u.s();!(c=u.n()).done;){var v=c.value,b=M(e),m;try{for(b.s();!(m=b.n()).done;){var x=m.value,g="".concat(h.name,":").concat(v.name,":").concat(x.name),f=ao(h,v,x);i.set(g,f.verticesPerEdge),o.set(g,f.data);var p=M(f.attributes),y;try{for(p.s();!(y=p.n()).done;){var T=y.value;s.has(T.name)||s.set(T.name,T)}}catch(W){p.e(W)}finally{p.f()}}}catch(W){b.e(W)}finally{b.f()}}}catch(W){u.e(W)}finally{u.f()}}}catch(W){l.e(W)}finally{l.f()}var _=Array.from(s.values()),E={};_.forEach(function(W,U){E[W.name]=U});var A=0,R="",L=M(i),F;try{for(L.s();!(F=L.n()).done;){var C=Q(F.value,2),P=C[0],D=C[1];D>A&&(A=D,R=P)}}catch(W){L.e(W)}finally{L.f()}var k=o.get(R)||[],w=R.split(":"),I=Q(w,1),G=I[0],z=t.find(function(W){return W.name===G}),B=[];z!=null&&z.generateConstantData?B=z.generateConstantData().attributes:B=[{name:"a_zone"},{name:"a_zoneT"},{name:"a_side"}];var O=k.map(function(W){var U=new Array(_.length).fill(0);return B.forEach(function(K,Z){var J=E[K.name];J!==void 0&&Z<W.length&&(U[J]=W[Z])}),U});return{vertexShader:eo(t,e,n,_),fragmentShader:to(t,e,n),uniforms:qi(t,e,n),attributes:no(),verticesPerEdge:A,constantData:O,constantAttributes:_,vertexCountsPerCombination:i,constantDataPerCombination:o}}function no(a,r,t){return[{name:"a_edgeIndex",size:1,type:bt},{name:"a_color",size:4,type:Ua,normalized:!0},{name:"a_id",size:4,type:Ua,normalized:!0}]}var ro=`#version 300 es
precision highp float;

in vec4 v_clamp;

// RGBA32F target: stores (tStart, tEnd, straightenFactor, pathLength).
out vec4 fragColor;

void main() {
  fragColor = v_clamp;
}
`,io=(function(){function a(r,t){V(this,a),S(this,"uniformLocations",{});var e=t.paths,n=t.extremities,i=t.layers;this.gl=r,this.hasAttributeData=fe([].concat(H(e),H(i))).floatsPerItem>0,this.vertexShader=oa(r,Qi(e,n,i)),this.fragmentShader=sa(r,ro),this.program=la(r,[this.vertexShader,this.fragmentShader]);var o=new Set;this.customUniforms=[];for(var s=0,l=[].concat(H(e),H(n));s<l.length;s++){var d=l[s],h=M(d.uniforms),u;try{for(h.s();!(u=h.n()).done;){var c=u.value;o.has(c.name)||(o.add(c.name),this.customUniforms.push(c))}}catch(g){h.e(g)}finally{h.f()}}var v=["u_sizeRatio","u_correctionRatio","u_cameraAngle","u_minEdgeThickness","u_nodeDataTexture","u_nodeDataTextureWidth","u_edgeDataTexture","u_edgeDataTextureWidth","u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge","u_frameTextureWidth","u_frameTextureHeight"].concat(H(this.customUniforms.map(function(g){return g.name}))),b=M(v),m;try{for(b.s();!(m=b.n()).done;){var x=m.value;this.uniformLocations[x]=r.getUniformLocation(this.program,x)}}catch(g){b.e(g)}finally{b.f()}this.vao=r.createVertexArray()}return X(a,[{key:"run",value:function(t,e,n,i){if(n!==0){var o=this.gl,s=this.uniformLocations;o.useProgram(this.program),o.bindVertexArray(this.vao),s.u_sizeRatio&&o.uniform1f(s.u_sizeRatio,t.sizeRatio),s.u_correctionRatio&&o.uniform1f(s.u_correctionRatio,t.correctionRatio),s.u_cameraAngle&&o.uniform1f(s.u_cameraAngle,t.cameraAngle),s.u_minEdgeThickness&&o.uniform1f(s.u_minEdgeThickness,t.minEdgeThickness),s.u_nodeDataTexture&&o.uniform1i(s.u_nodeDataTexture,t.nodeDataTextureUnit),s.u_nodeDataTextureWidth&&o.uniform1i(s.u_nodeDataTextureWidth,t.nodeDataTextureWidth),s.u_edgeDataTexture&&o.uniform1i(s.u_edgeDataTexture,t.edgeDataTextureUnit),s.u_edgeDataTextureWidth&&o.uniform1i(s.u_edgeDataTextureWidth,t.edgeDataTextureWidth),s.u_frameTextureWidth&&o.uniform1f(s.u_frameTextureWidth,e.getTextureWidth()),s.u_frameTextureHeight&&o.uniform1f(s.u_frameTextureHeight,e.getTextureHeight()),this.hasAttributeData&&i&&(i.bind(_e),s.u_edgeAttributeTexture&&o.uniform1i(s.u_edgeAttributeTexture,_e),s.u_edgeAttributeTextureWidth&&o.uniform1i(s.u_edgeAttributeTextureWidth,i.getTextureWidth()),s.u_edgeAttributeTexelsPerEdge&&o.uniform1i(s.u_edgeAttributeTexelsPerEdge,i.getTexelsPerItem()));var l=M(this.customUniforms),d;try{for(l.s();!(d=l.n()).done;){var h=d.value;ua(o,this.uniformLocations[h.name],h)}}catch(u){l.e(u)}finally{l.f()}e.bindAsRenderTarget(),o.disable(o.BLEND),o.disable(o.DEPTH_TEST),o.drawArrays(o.POINTS,0,n),o.bindFramebuffer(o.FRAMEBUFFER,null),o.bindVertexArray(null)}}},{key:"kill",value:function(){var t=this.gl;t.deleteProgram(this.program),t.deleteShader(this.vertexShader),t.deleteShader(this.fragmentShader),t.deleteVertexArray(this.vao)}}])})();function je(a,r,t,e,n,i){if(a.length===1)return"".concat(e," ").concat(r,"(int pathId, ").concat(n,`) {
  return path_`).concat(a[0].name,"_").concat(t,"(").concat(i,`);
}`);var o=a.map(function(s,l){return"    case ".concat(l,": return path_").concat(s.name,"_").concat(t,"(").concat(i,");")}).join(`
`);return"".concat(e," ").concat(r,"(int pathId, ").concat(n,`) {
  switch (pathId) {
`).concat(o,`
    default: return path_`).concat(a[0].name,"_").concat(t,"(").concat(i,`);
  }
}`)}var oo=`
vec3 computeEdgeLabelBodyBounds(
  float tStart, float tEnd, float pathLength,
  float webGLThickness, float headLengthRatio, float tailLengthRatio
) {
  float visibleLength = pathLength * (tEnd - tStart);

  float headLength = headLengthRatio * webGLThickness;
  float tailLength = tailLengthRatio * webGLThickness;
  float totalNeededLength = headLength + tailLength;
  if (totalNeededLength > visibleLength && totalNeededLength > 0.0001) {
    float extremityScale = visibleLength / totalNeededLength;
    headLength *= extremityScale;
    tailLength *= extremityScale;
  }

  float bodyStartDist = tStart * pathLength + tailLength;
  float bodyEndDist = tEnd * pathLength - headLength;
  return vec3(bodyStartDist, bodyEndDist, max(bodyEndDist - bodyStartDist, 0.0));
}
`;function so(a,r){var t=Y(a),e=Y(r);return`
float computeEdgeLabelAlpha(float bodyLength, float textWidthWebGL) {
  float ratio = textWidthWebGL > 0.0001 ? min(bodyLength / textWidthWebGL, 1.0) : 1.0;
  if (ratio < `.concat(t,`) return 0.0;
  if (ratio < `).concat(e,") return (ratio - ").concat(t,") / (").concat(e," - ").concat(t,`);
  return 1.0;
}
`)}var lo=`
float computeEdgeLabelPerpOffset(
  float positionMode,
  float halfThickness, float marginWebGL, float halfTextHeight,
  vec2 source, vec2 target, mat3 matrix
) {
  float magnitude = halfThickness + marginWebGL + halfTextHeight;
  if (positionMode == 1.0) return magnitude;
  if (positionMode == 2.0) return -magnitude;
  if (positionMode == 3.0) {
    vec3 sc = matrix * vec3(source, 1.0);
    vec3 tc = matrix * vec3(target, 1.0);
    return sc.x < tc.x ? magnitude : -magnitude;
  }
  return 0.0;
}
`;function Nn(a){var r=a.paths,t=a.minVisibilityThreshold,e=a.fullVisibilityThreshold,n=r.some(function(s){return s.hasSharpCorners}),i=r.map(function(s){return"// --- Path: ".concat(s.name,` ---
`).concat(s.glsl,`

// Tangent/normal functions: analytical if provided, otherwise numerical
`).concat(s.analyticalTangentGlsl||wn(s.name),`

// Auto-generated fallbacks for any missing path functions
`).concat(In(s.name,s.glsl),`

// Corner skip helpers (for paths with sharp corners like step/taxi)
`).concat(s.cornerSkipGlsl||"",`
`)}).join(`
`),o=n?`// Corner function selectors (only some paths have sharp corners)
vec2 queryGetCornerTs(int pathId, vec2 source, vec2 target) {
  switch (pathId) {
`.concat(r.map(function(s,l){return s.hasSharpCorners?"    case ".concat(l,": return path_").concat(s.name,"_getCornerTs(source, target);"):"    case ".concat(l,": return vec2(-1.0, -1.0); // No corners for ").concat(s.name)}).join(`
`),`
    default: return vec2(-1.0, -1.0);
  }
}

vec2 queryGetCornerConcavity(int pathId, vec2 source, vec2 target, float perpOffset) {
  switch (pathId) {
`).concat(r.map(function(s,l){return s.hasSharpCorners?"    case ".concat(l,": return path_").concat(s.name,"_getCornerConcavity(source, target, perpOffset);"):"    case ".concat(l,": return vec2(0.0, 0.0); // No corners for ").concat(s.name)}).join(`
`),`
    default: return vec2(0.0, 0.0);
  }
}`):"";return`
// ============================================================================
// Node data fetch (geometry texel) and per-edge clamp fetch (edge-frame texture)
// ============================================================================

`.concat(be,`
`).concat(Ve,`

// ============================================================================
// Path Functions (one block per path)
// ============================================================================

`).concat(i,`

// ============================================================================
// Path Query Selectors (dispatch by pathId)
// ============================================================================

`).concat(je(r,"queryPathPosition","position","vec2","float t, vec2 source, vec2 target","t, source, target"),`

`).concat(je(r,"queryPathTangent","tangent","vec2","float t, vec2 source, vec2 target","t, source, target"),`

`).concat(je(r,"queryPathNormal","normal","vec2","float t, vec2 source, vec2 target","t, source, target"),`

`).concat(je(r,"queryPathLength","length","float","vec2 source, vec2 target","source, target"),`

`).concat(je(r,"queryPathTAtDistance","t_at_distance","float","float dist, vec2 source, vec2 target","dist, source, target"),`

`).concat(o,`

// ============================================================================
// Shared helpers (body bounds, alpha ramp, perpendicular offset)
// ============================================================================

`).concat(oo,`
`).concat(so(t,e),`
`).concat(lo,`
`)}var uo=pe.fontSize,ho=new Map,Gn=24,Va=(Gn+1)*2;function co(a){var r=a.paths,t=a.fontSizeMode,e=a.headLengthRatio,n=a.tailLengthRatio,i=a.minVisibilityThreshold,o=a.fullVisibilityThreshold,s=t==="scaled",l=tt(),d=fe([].concat(H(r),[l])),h=nt(d),u=`#version 300 es

// Per-instance attributes
in float a_edgeIndex;
in float a_edgeAttrIndex;
in float a_baseFontSize;
in float a_totalTextWidth;
in float a_positionMode;
in float a_margin;
in float a_padding;
in vec4 a_color;
in vec4 a_id;

// Per-vertex (constant) attribute: strip vertex index
in float a_vertexIndex;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_pixelRatio;
uniform float u_cameraAngle;
uniform vec2 u_resolution;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_edgeDataTexture;
uniform int u_edgeDataTextureWidth;
uniform sampler2D u_edgeFrameTexture; // Per-edge clamp (tStart, tEnd, straightenFactor, pathLength)
uniform int u_edgeFrameTextureWidth;
`.concat(s?"uniform float u_zoomSizeRatio;":"",`

`).concat(h.uniformDeclarations,`

out vec4 v_color;
out vec4 v_id;
out float v_alphaModifier;

const float ATLAS_FONT_SIZE = `).concat(Y(uo),`;
const float HEAD_RATIO = `).concat(Y(e),`;
const float TAIL_RATIO = `).concat(Y(n),`;
const int RIBBON_SEGMENTS = `).concat(Gn,`;

// Path attribute varyings (declared as plain locals since this shader has no FS inputs for them)
`).concat(h.vertexVaryingDeclarations.replace(/out /g,""),`

// Node size variables used by some path functions (self-loops, etc.)
float v_sourceNodeSize;
float v_targetNodeSize;

// Shared preamble: shape SDFs, path functions + selectors, clamp, helpers.
`).concat(Nn({paths:r,minVisibilityThreshold:i,fullVisibilityThreshold:o}),`

void main() {
  int vIdx = int(a_vertexIndex);
  int pairIdx = vIdx / 2;
  int side = vIdx - pairIdx * 2; // 0 = left/bottom, 1 = right/top

  // --- Fetch edge data (2 texels per edge) ---
  int edgeIdx = int(a_edgeIndex);
  int texel0Idx = edgeIdx * 2;
  int texel1Idx = edgeIdx * 2 + 1;
  ivec2 e0 = ivec2(texel0Idx % u_edgeDataTextureWidth, texel0Idx / u_edgeDataTextureWidth);
  ivec2 e1 = ivec2(texel1Idx % u_edgeDataTextureWidth, texel1Idx / u_edgeDataTextureWidth);
  vec4 edgeData0 = texelFetch(u_edgeDataTexture, e0, 0);
  vec4 edgeData1 = texelFetch(u_edgeDataTexture, e1, 0);

  int srcIdx = int(edgeData0.x);
  int tgtIdx = int(edgeData0.y);
  float thickness = edgeData0.z;
  int pathId = int(edgeData1.z);

  // --- Fetch path attributes (curvature, etc.) ---
  {
    int edgeIdx = int(a_edgeAttrIndex);
`).concat(h.fetchCode,`
`).concat(h.varyingAssignments,`
  }

  // --- Fetch node data: geometry (texel 0) + rotation flags (texel 1) ---
  vec4 srcN = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  vec4 tgtN = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);

  vec2 source = srcN.xy;
  vec2 target = tgtN.xy;
  float sourceSize = srcN.z;
  float targetSize = tgtN.z;
  v_sourceNodeSize = sourceSize;
  v_targetNodeSize = targetSize;

  // --- Pixel-to-graph conversion (fixed font mode) ---
  float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
  float pixelToGraph = 2.0 / (matrixScaleX * u_resolution.x);

  float webGLThickness = thickness * u_correctionRatio / u_sizeRatio;

  // --- Body bounds (shared with edge label shader) ---
  vec4 edgeClamp = readFrameTexel(u_edgeFrameTexture, u_edgeFrameTextureWidth, edgeIdx);
  vec3 bodyBounds = computeEdgeLabelBodyBounds(
    edgeClamp.x, edgeClamp.y, edgeClamp.w,
    webGLThickness, HEAD_RATIO, TAIL_RATIO
  );
  float bodyStartDist = bodyBounds.x;
  float bodyEndDist = bodyBounds.y;
  float bodyLength = bodyBounds.z;

  // --- Text dimensions ---
  float baseFontSize = a_baseFontSize;
  `).concat(s?`float fontScale = baseFontSize / ATLAS_FONT_SIZE * u_zoomSizeRatio;
  float textWidthWebGL = a_totalTextWidth * fontScale * u_correctionRatio / u_sizeRatio;
  float halfTextHeight = baseFontSize * 0.35 * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;
  float marginWebGL = a_margin * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;`:`float fontScale = baseFontSize / ATLAS_FONT_SIZE;
  float textWidthWebGL = a_totalTextWidth * fontScale * pixelToGraph;
  float halfTextHeight = baseFontSize * 0.35 * pixelToGraph;
  float marginWebGL = a_margin * pixelToGraph;`,`
  float paddingWebGL = a_padding * pixelToGraph;

  // --- Alpha modifier (shared with edge label shader) ---
  float alphaModifier = computeEdgeLabelAlpha(bodyLength, textWidthWebGL);
  if (alphaModifier <= 0.0 || textWidthWebGL <= 0.0) {
    gl_Position = vec4(2.0, 0.0, 0.0, 1.0);
    v_color = vec4(0.0);
    v_id = vec4(0.0);
    v_alphaModifier = 0.0;
    return;
  }

  // --- Perpendicular offset (shared with edge label shader) ---
  float halfThickness = webGLThickness * 0.5;
  float perpOffset = computeEdgeLabelPerpOffset(
    a_positionMode, halfThickness, marginWebGL, halfTextHeight, source, target, u_matrix
  );

  // --- Ribbon span (clipped to body) ---
  float bodyCenterDist = (bodyStartDist + bodyEndDist) * 0.5;
  float halfTextWebGL = textWidthWebGL * 0.5;
  float labelStartDist = max(bodyCenterDist - halfTextWebGL, bodyStartDist);
  float labelEndDist = min(bodyCenterDist + halfTextWebGL, bodyEndDist);

  // Sample centerline at this pair, then apply perpendicular offset.
  // The ribbon follows the centerline path (simple & robust); for curved edges
  // this closely matches the offset path the characters sit on.
  float u = float(pairIdx) / float(RIBBON_SEGMENTS);
  float arcDist = mix(labelStartDist, labelEndDist, u);
  float t = queryPathTAtDistance(pathId, arcDist, source, target);
  vec2 pos = queryPathPosition(pathId, t, source, target);
  vec2 tan = queryPathTangent(pathId, t, source, target);
  vec2 perp = vec2(-tan.y, tan.x);

  vec2 centerPos = pos + perp * perpOffset;

  float halfRibbon = halfTextHeight + paddingWebGL;
  float sideSign = side == 0 ? -1.0 : 1.0;
  vec2 ribbonPos = centerPos + perp * (sideSign * halfRibbon);

  vec3 clipPos = u_matrix * vec3(ribbonPos, 1.0);
  gl_Position = vec4(clipPos.xy, 0.0, 1.0);

  v_color = a_color;
  v_id = a_id;
  v_alphaModifier = alphaModifier;
}
`);return u}var fo=`#version 300 es
precision highp float;

in vec4 v_color;
in vec4 v_id;
in float v_alphaModifier;

out vec4 fragColor;

void main() {
#ifdef PICKING_MODE
  if (v_alphaModifier <= 0.0) discard;
  fragColor = v_id;
#else
  float alpha = v_color.a * v_alphaModifier;
  if (alpha <= 0.0) discard;
  fragColor = vec4(v_color.rgb * alpha, alpha);
#endif
}
`;function go(a,r,t,e){var n=e.shaderConfig,i=n.paths,o=n.fontSizeMode;if(i.length===0)throw new Error("createEdgeLabelBackgroundProgram: shaderConfig must declare at least one path");var s=tt(),l=fe([].concat(H(i),[s])),d=At([].concat(H(i),[s]),l),h=co(n),u=(function(c){function v(b,m,x){var g;return V(this,v),g=ee(this,v,[b,m,x]),S(g,"totalCount",0),S(g,"bufferCapacity",0),S(g,"edgeAttributeTexture",null),g.edgeAttributeTexture=new Rt(b,l),g.packedAttributeData=new Float32Array(l.floatsPerItem),g}return te(v,c),X(v,[{key:"getDefinition",value:function(){for(var m=WebGL2RenderingContext,x=m.FLOAT,g=m.UNSIGNED_BYTE,f=m.TRIANGLE_STRIP,p=[],y=0;y<Va;y++)p.push([y]);var T=["u_matrix","u_sizeRatio","u_correctionRatio","u_pixelRatio","u_cameraAngle","u_resolution","u_nodeDataTexture","u_nodeDataTextureWidth","u_edgeDataTexture","u_edgeDataTextureWidth","u_edgeFrameTexture","u_edgeFrameTextureWidth"];return o==="scaled"&&T.push("u_zoomSizeRatio"),l.floatsPerItem>0&&T.push("u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge"),{VERTICES:Va,VERTEX_SHADER_SOURCE:h,FRAGMENT_SHADER_SOURCE:fo,METHOD:f,UNIFORMS:T,ATTRIBUTES:[{name:"a_edgeIndex",size:1,type:x},{name:"a_edgeAttrIndex",size:1,type:x},{name:"a_baseFontSize",size:1,type:x},{name:"a_totalTextWidth",size:1,type:x},{name:"a_positionMode",size:1,type:x},{name:"a_margin",size:1,type:x},{name:"a_padding",size:1,type:x},{name:"a_color",size:4,type:g,normalized:!0},{name:"a_id",size:4,type:g,normalized:!0}],CONSTANT_ATTRIBUTES:[{name:"a_vertexIndex",size:1,type:x}],CONSTANT_DATA:p}}},{key:"processEdgeLabelBackground",value:function(m,x,g){var f=0;if(this.edgeAttributeTexture&&l.floatsPerItem>0){f=this.edgeAttributeTexture.allocate(x);var p=this.packedAttributeData;Dt(d,g.edgeAttributes,p,"",1,ho,0),this.edgeAttributeTexture.updateAllAttributes(x,p)}var y=this.floats,T=this.ints,_=m*this.STRIDE;y[_++]=g.edgeIndex,y[_++]=f,y[_++]=g.baseFontSize,y[_++]=g.totalTextWidth,y[_++]=g.positionMode,y[_++]=g.margin,y[_++]=g.padding,y[_++]=g.color,T[_++]=g.id}},{key:"setUniforms",value:function(m,x){var g=x.gl,f=x.uniformLocations;if(g.uniformMatrix3fv(f.u_matrix,!1,m.matrix),g.uniform1f(f.u_sizeRatio,m.sizeRatio),g.uniform1f(f.u_correctionRatio,m.correctionRatio),g.uniform1f(f.u_pixelRatio,m.pixelRatio),g.uniform1f(f.u_cameraAngle,m.cameraAngle),g.uniform2f(f.u_resolution,m.width,m.height),f.u_nodeDataTexture!==void 0&&g.uniform1i(f.u_nodeDataTexture,m.nodeDataTextureUnit),f.u_nodeDataTextureWidth!==void 0&&g.uniform1i(f.u_nodeDataTextureWidth,m.nodeDataTextureWidth),f.u_edgeDataTexture!==void 0&&g.uniform1i(f.u_edgeDataTexture,m.edgeDataTextureUnit),f.u_edgeDataTextureWidth!==void 0&&g.uniform1i(f.u_edgeDataTextureWidth,m.edgeDataTextureWidth),f.u_edgeFrameTexture!==void 0&&g.uniform1i(f.u_edgeFrameTexture,m.edgeFrameTextureUnit),f.u_edgeFrameTextureWidth!==void 0&&g.uniform1i(f.u_edgeFrameTextureWidth,m.edgeFrameTextureWidth),o==="scaled"&&f.u_zoomSizeRatio!==void 0){var p=this.renderer.getSetting("zoomToSizeRatioFunction");g.uniform1f(f.u_zoomSizeRatio,1/p(m.zoomRatio))}this.edgeAttributeTexture&&l.floatsPerItem>0&&f.u_edgeAttributeTexture!==void 0&&(this.edgeAttributeTexture.bind(_e),g.uniform1i(f.u_edgeAttributeTexture,_e),g.uniform1i(f.u_edgeAttributeTextureWidth,this.edgeAttributeTexture.getTextureWidth()),g.uniform1i(f.u_edgeAttributeTexelsPerEdge,this.edgeAttributeTexture.getTexelsPerItem()))}},{key:"renderProgram",value:function(m,x){this.edgeAttributeTexture&&l.floatsPerItem>0&&this.edgeAttributeTexture.upload(),ne(v,"renderProgram",this)([m,x])}},{key:"kill",value:function(){this.edgeAttributeTexture&&(this.edgeAttributeTexture.kill(),this.edgeAttributeTexture=null),ne(v,"kill",this)([])}},{key:"drawWebGL",value:function(m,x){var g=x.gl;this.totalCount!==0&&g.drawArraysInstanced(g.TRIANGLE_STRIP,0,this.VERTICES,this.totalCount)}},{key:"reallocate",value:function(m){this.totalCount=m,m>this.bufferCapacity&&(this.bufferCapacity=Math.max(m,Math.ceil(this.bufferCapacity*1.5)||10),ne(v,"reallocate",this)([this.bufferCapacity]))}}])})(Fe);return new u(a,r,t)}function Bn(a){var r,t,e,n,i;return{paths:a.paths,headLengthRatio:(r=a.headLengthRatio)!==null&&r!==void 0?r:0,tailLengthRatio:(t=a.tailLengthRatio)!==null&&t!==void 0?t:0,fontSizeMode:(e=a.fontSizeMode)!==null&&e!==void 0?e:"fixed",minVisibilityThreshold:(n=a.minVisibilityThreshold)!==null&&n!==void 0?n:.7,fullVisibilityThreshold:(i=a.fullVisibilityThreshold)!==null&&i!==void 0?i:.8}}var vo=pe.fontSize,mo=17/64;function po(a){var r=a.paths,t=a.hasBorder,e=t===void 0?!1:t,n=a.fontSizeMode,i=n===void 0?"fixed":n,o=a.minVisibilityThreshold,s=o===void 0?.5:o,l=a.fullVisibilityThreshold,d=l===void 0?.6:l,h=i==="scaled",u=r.some(function(x){return x.hasSharpCorners}),c=tt(),v=fe([].concat(H(r),[c])),b=nt(v),m=`#version 300 es

// ============================================================================
// Attributes - Per Character (Instanced)
// ============================================================================

// Edge geometry: indices for texture lookup
// Edge data (source/target node indices, thickness, head/tail ratios) is fetched from edge data texture
// Edge path attributes (curvature, etc.) are fetched from edge attribute texture
in float a_edgeIndex;       // Index into edge data texture
in float a_edgeAttrIndex;   // Index into edge attribute texture (for curvature, etc.)
in float a_baseFontSize;    // Base font size in pixels (per-label)

// Character metrics (in glyph units = atlas font size pixels)
in vec4 a_charMetrics;      // (charTextOffset, charAdvance, totalTextWidth, positionMode)
in vec4 a_charDims;         // (charSize.x, charSize.y, charOffset.x, charOffset.y)

// Atlas texture coordinates
in vec4 a_texCoords;        // (x, y, width, height) in atlas pixels

// Label parameters
in vec2 a_labelParams;      // (margin, unused)

// Appearance
in vec4 a_color;            // Character color (RGBA, normalized)
`.concat(e?"in vec4 a_borderColor;      // Border color (RGBA, normalized)":"",`

// ============================================================================
// Attributes - Per Vertex (Constant)
// ============================================================================

in vec2 a_quadCorner;       // Quad corner: (0,0), (1,0), (0,1), (1,1)

// ============================================================================
// Uniforms
// ============================================================================

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_pixelRatio;
uniform float u_cameraAngle;    // Required by node shape SDFs
// u_sdfBufferPixels kept for ABI compatibility but unused in shader
uniform float u_sdfBufferPixels;
uniform vec2 u_resolution;
uniform vec2 u_atlasSize;
uniform sampler2D u_nodeDataTexture; // Shared texture with node position/size/shape data
uniform int u_nodeDataTextureWidth;  // Width of 2D node data texture for coordinate calculation
uniform sampler2D u_edgeDataTexture; // Shared texture with edge data
uniform int u_edgeDataTextureWidth;  // Width of 2D edge data texture for coordinate calculation
uniform sampler2D u_edgeFrameTexture; // Per-edge clamp (tStart, tEnd, straightenFactor, pathLength)
uniform int u_edgeFrameTextureWidth;
`).concat(h?"uniform float u_zoomSizeRatio;  // Zoom-based size ratio from zoomToSizeRatioFunction":"",`

// Edge path attribute texture uniforms (for curvature and other path attributes)
`).concat(b.uniformDeclarations,`

// ============================================================================
// Varyings
// ============================================================================

out vec2 v_texCoord;
out vec4 v_color;
`).concat(e?"out vec4 v_borderColor;":"",`
out float v_edgeFade;  // 0 = fully visible, 1 = fully faded (outside body)
out float v_alphaModifier;  // 0-1 based on label visibility ratio
out float v_fontScale;  // Ratio of rendered font size to atlas font size
`).concat(e?"out float v_positionMode;  // Position mode for conditional border (0=over needs border)":"",`

// ============================================================================
// Constants
// ============================================================================

const float bias = 255.0 / 254.0;
const float FADE_WIDTH_PIXELS = 15.0;  // Width of fade gradient in pixels
const float ATLAS_FONT_SIZE = `).concat(Y(vo),`;  // Base font size used in SDF atlas
const float VERTICAL_CENTER_RATIO = `).concat(Y(mo),`;  // Baseline to visual center ratio

// ============================================================================
// Path Attribute Variables (set in main, used by path functions)
// ============================================================================
// Path attributes are fetched from the edge attribute texture and stored in
// variables with v_ prefix (e.g., v_curvature) for path functions to access.
`).concat(b.vertexVaryingDeclarations.replace(/out /g,""),`

// Node size variables (set in main, used by some path functions like loops).
// These mirror the v_sourceNodeSize / v_targetNodeSize varyings in generator.ts,
// but are plain floats here since the label shader is vertex-only.
float v_sourceNodeSize;
float v_targetNodeSize;

// Shared preamble: shape SDFs, path functions + selectors, clamp, helpers.
`).concat(Nn({paths:r,minVisibilityThreshold:s,fullVisibilityThreshold:d}),`

// ============================================================================
// Main
// ============================================================================

void main() {
  // -------------------------------------------------------------------------
  // Fetch edge data from edge texture (2 texels per edge)
  // -------------------------------------------------------------------------
  // Texel 0: sourceNodeIndex, targetNodeIndex, thickness, reserved
  // Texel 1: headLengthRatio, tailLengthRatio, pathId, extremityIds
  int edgeIdx = int(a_edgeIndex);
  int texel0Idx = edgeIdx * 2;
  int texel1Idx = edgeIdx * 2 + 1;
  ivec2 edgeTexCoord0 = ivec2(texel0Idx % u_edgeDataTextureWidth, texel0Idx / u_edgeDataTextureWidth);
  ivec2 edgeTexCoord1 = ivec2(texel1Idx % u_edgeDataTextureWidth, texel1Idx / u_edgeDataTextureWidth);
  vec4 edgeData0 = texelFetch(u_edgeDataTexture, edgeTexCoord0, 0);
  vec4 edgeData1 = texelFetch(u_edgeDataTexture, edgeTexCoord1, 0);

  // Unpack edge data
  int srcIdx = int(edgeData0.x);
  int tgtIdx = int(edgeData0.y);
  float thickness = edgeData0.z;
  // edgeData0.w is reserved
  float headLengthRatio = edgeData1.x;
  float tailLengthRatio = edgeData1.y;
  int pathId = int(edgeData1.z);  // Path type for multi-path support
  float baseFontSize = a_baseFontSize;

  // -------------------------------------------------------------------------
  // Fetch path attributes from edge attribute texture
  // -------------------------------------------------------------------------
  // Note: The fetch code uses 'edgeIdx' variable, so we set it to the attribute texture index
  {
    int edgeIdx = int(a_edgeAttrIndex);  // Use attribute texture index for path attributes
`).concat(b.fetchCode,`
`).concat(b.varyingAssignments,`
  }

  // -------------------------------------------------------------------------
  // Fetch node data from node texture (geometry texel + rotation-flags texel)
  // -------------------------------------------------------------------------
  vec4 srcNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  vec4 tgtNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);

  vec2 source = srcNodeData.xy;
  vec2 target = tgtNodeData.xy;
  float sourceSize = srcNodeData.z;
  float targetSize = tgtNodeData.z;
  v_sourceNodeSize = sourceSize;
  v_targetNodeSize = targetSize;
  float charTextOffset = a_charMetrics.x;
  float charAdvance = a_charMetrics.y;
  float totalTextWidth = a_charMetrics.z;
  float positionMode = a_charMetrics.w;
  vec2 charSize = a_charDims.xy;
  vec2 charOffset = a_charDims.zw;
  float margin = a_labelParams.x;

  // -------------------------------------------------------------------------
  // Compute pixel-to-graph conversion (for fixed font size mode)
  // -------------------------------------------------------------------------
  // This converts screen pixels to graph units such that N pixels on screen
  // becomes N pixels regardless of zoom level.
  // matrixScaleX is how much the matrix scales graph units to clip space
  float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
  float pixelToGraph = 2.0 / (matrixScaleX * u_resolution.x);

  // -------------------------------------------------------------------------
  // Step 1: Convert thickness to WebGL units
  // -------------------------------------------------------------------------
  float webGLThickness = thickness * u_correctionRatio / u_sizeRatio;

  // -------------------------------------------------------------------------
  // Step 2: Compute body bounds (truncated at node boundaries + extremities)
  // -------------------------------------------------------------------------
  vec4 edgeClamp = readFrameTexel(u_edgeFrameTexture, u_edgeFrameTextureWidth, edgeIdx);
  vec3 bodyBounds = computeEdgeLabelBodyBounds(
    edgeClamp.x, edgeClamp.y, edgeClamp.w,
    webGLThickness, headLengthRatio, tailLengthRatio
  );
  float bodyStartDist = bodyBounds.x;
  float bodyEndDist = bodyBounds.y;
  float bodyLength = bodyBounds.z;

  // -------------------------------------------------------------------------
  // Step 3: Compute font scale and text dimensions
  // -------------------------------------------------------------------------
  // Font size modes:
  // - "fixed": Constant pixel size regardless of zoom, using pixelToGraph conversion
  // - "scaled": Scales with zoom using zoomToSizeRatioFunction
  `).concat(h?`// Scaled mode: font scales with zoom
  float fontScale = baseFontSize / ATLAS_FONT_SIZE * u_zoomSizeRatio;
  // Convert glyph-unit metrics to WebGL units (scales with zoom)
  float textWidthWebGL = totalTextWidth * fontScale * u_correctionRatio / u_sizeRatio;
  float charOffsetWebGL = charTextOffset * fontScale * u_correctionRatio / u_sizeRatio;
  float charAdvanceWebGL = charAdvance * fontScale * u_correctionRatio / u_sizeRatio;`:`// Fixed mode: font stays constant in screen pixels
  float fontScale = baseFontSize / ATLAS_FONT_SIZE;
  // Convert glyph-unit metrics to graph units using pixelToGraph (zoom-independent)
  float textWidthWebGL = totalTextWidth * fontScale * pixelToGraph;
  float charOffsetWebGL = charTextOffset * fontScale * pixelToGraph;
  float charAdvanceWebGL = charAdvance * fontScale * pixelToGraph;`,`

  // Font scale varying for fragment shader gamma scaling.
  // Ratio of rendered font size to atlas font size — used to tighten the
  // anti-aliasing band for large labels so they stay sharp.
  v_fontScale = fontScale;

  // -------------------------------------------------------------------------
  // Step 4: Alpha modifier from how much of the label fits in the body
  // -------------------------------------------------------------------------
  float alphaModifier = computeEdgeLabelAlpha(bodyLength, textWidthWebGL);

  // -------------------------------------------------------------------------
  // Step 5: Compute character center offset (truncation check moved to after curvature adjustment)
  // -------------------------------------------------------------------------
  // Character center position relative to label center (on centerline, before curvature adjustment)
  float charCenterOffset = charOffsetWebGL + charAdvanceWebGL * 0.5 - textWidthWebGL * 0.5;

  // -------------------------------------------------------------------------
  // Step 6: Compute perpendicular offset based on position mode
  // -------------------------------------------------------------------------
  // Position modes: 0=over, 1=above, 2=below, 3=auto
  // Needed early for curvature-adaptive character spacing in Step 7
  float halfThickness = webGLThickness * 0.5;
  `).concat(h?`// Scaled mode: margin and text height scale with zoom (same factor as font)
  float marginWebGL = margin * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;
  float halfTextHeight = baseFontSize * 0.35 * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;`:`// Fixed mode: margin and text height stay constant in screen pixels
  float marginWebGL = margin * pixelToGraph;
  float halfTextHeight = baseFontSize * 0.35 * pixelToGraph;`,`
  float perpOffset = computeEdgeLabelPerpOffset(
    positionMode, halfThickness, marginWebGL, halfTextHeight, source, target, u_matrix
  );

  // -------------------------------------------------------------------------
  // Step 7: Position character on path using offset path traversal
  // -------------------------------------------------------------------------
  // Body center in arc distance
  float bodyCenterDist = (bodyStartDist + bodyEndDist) * 0.5;

  // For "over" mode (perpOffset = 0), use simple centerline placement
  // For above/below modes, walk along the offset path to find correct position
  float charT;

  if (perpOffset == 0.0) {
    // Simple case: place on centerline
    float charArcDist = bodyCenterDist + charCenterOffset;
    charT = queryPathTAtDistance(pathId, charArcDist, source, target);
  } else {
    // Offset path traversal: walk along the offset curve to find character position
    // This ensures even character spacing regardless of curvature

    // Start from body center on offset path
    float centerT = queryPathTAtDistance(pathId, bodyCenterDist, source, target);

    `).concat(u?`// -----------------------------------------------------------------------
    // Corner skip setup for step/taxi edges with above/below labels
    // -----------------------------------------------------------------------
    // At concave corners (inner side of the bend), characters would bunch up
    // because the offset path has near-zero arc length. We detect corner
    // crossings during the offset path traversal and add skip distance.

    // Get corner t values and concavity
    vec2 cornerTs = queryGetCornerTs(pathId, source, target);
    vec2 concavity = queryGetCornerConcavity(pathId, source, target, perpOffset);

    // Skip distance in graph units, proportional to on-screen font size
    // For fixed mode: use pixelToGraph so gap stays constant regardless of zoom
    // For scaled mode: use the same conversion as text width
    `.concat(h?"float skipDistGraph = STEP_INNER_CORNER_SKIP_FACTOR * baseFontSize * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;":"float skipDistGraph = STEP_INNER_CORNER_SKIP_FACTOR * baseFontSize * pixelToGraph;",`

    // Corner t values for detecting crossings during traversal
    float corner1T = cornerTs.x;
    float corner2T = cornerTs.y;
    bool corner1IsConcave = concavity.x > 0.5;
    bool corner2IsConcave = concavity.y > 0.5;`):"",`

    // Target distance along offset path from center
    float targetOffsetDist = abs(charCenterOffset);

    // Handle center character (charCenterOffset ≈ 0) - no search needed
    if (targetOffsetDist < 0.0001) {
      charT = centerT;
    } else {
      vec2 centerPos = queryPathPosition(pathId, centerT, source, target);
      vec2 centerNormal = queryPathNormal(pathId, centerT, source, target);
      vec2 offsetCenter = centerPos + centerNormal * perpOffset;

      float searchDir = charCenterOffset > 0.0 ? 1.0 : -1.0;

      // Search bounds (t values for body start and end)
      float tBodyStart = queryPathTAtDistance(pathId, bodyStartDist, source, target);
      float tBodyEnd = queryPathTAtDistance(pathId, bodyEndDist, source, target);

      // Walk along offset path to find character position
      float accumDist = 0.0;
      vec2 prevOffsetPos = offsetCenter;
      float prevT = centerT;
      float foundT = centerT;

      // Search range depends on direction
      float tSearchEnd = searchDir > 0.0 ? tBodyEnd : tBodyStart;

      `).concat(u?`// Track which concave corners we've crossed to add skip distance
      bool crossedCorner1 = false;
      bool crossedCorner2 = false;
      float effectiveTargetDist = targetOffsetDist;`:"",`

      const int STEPS = 32;
      for (int i = 1; i <= STEPS; i++) {
        // Step along centerline t, from center toward target
        float stepT = centerT + searchDir * float(i) * abs(tSearchEnd - centerT) / float(STEPS);

        `).concat(u?`// Check for concave corner crossings and add skip distance
        // Corner 1 crossing check
        if (corner1IsConcave && !crossedCorner1) {
          bool crossingCorner1 = (searchDir > 0.0)
            ? (prevT < corner1T && stepT >= corner1T)
            : (prevT > corner1T && stepT <= corner1T);
          if (crossingCorner1) {
            crossedCorner1 = true;
            effectiveTargetDist += skipDistGraph;
          }
        }

        // Corner 2 crossing check
        if (corner2IsConcave && !crossedCorner2) {
          bool crossingCorner2 = (searchDir > 0.0)
            ? (prevT < corner2T && stepT >= corner2T)
            : (prevT > corner2T && stepT <= corner2T);
          if (crossingCorner2) {
            crossedCorner2 = true;
            effectiveTargetDist += skipDistGraph;
          }
        }`:"",`

        // Compute offset position at this t
        vec2 stepPos = queryPathPosition(pathId, stepT, source, target);
        vec2 stepNormal = queryPathNormal(pathId, stepT, source, target);
        vec2 offsetPos = stepPos + stepNormal * perpOffset;

        // Distance along offset path
        float segDist = length(offsetPos - prevOffsetPos);

        `).concat(u?`if (accumDist + segDist >= effectiveTargetDist) {
          // Interpolate within segment to find exact t
          float remaining = effectiveTargetDist - accumDist;
          float segT = remaining / max(segDist, 0.0001);
          foundT = mix(prevT, stepT, segT);
          break;
        }`:`if (accumDist + segDist >= targetOffsetDist) {
          // Interpolate within segment to find exact t
          float remaining = targetOffsetDist - accumDist;
          float segT = remaining / max(segDist, 0.0001);
          foundT = mix(prevT, stepT, segT);
          break;
        }`,`

        accumDist += segDist;
        prevOffsetPos = offsetPos;
        prevT = stepT;
        // Update foundT to last valid position in case loop exhausts without finding target
        foundT = stepT;
      }

      charT = foundT;
    }
  }

  // Get position and tangent at final character position
  vec2 pathPos = queryPathPosition(pathId, charT, source, target);
  vec2 tangent = queryPathTangent(pathId, charT, source, target);

  // Compute perpendicular direction (90 degrees from tangent)
  vec2 perpDir = vec2(-tangent.y, tangent.x);

  // Apply perpendicular offset to path position
  vec2 offsetPathPos = pathPos + perpDir * perpOffset;

  // -------------------------------------------------------------------------
  // Step 8: Build character quad
  // -------------------------------------------------------------------------
  // Character size in screen pixels
  vec2 charSizePixels = charSize * fontScale;

  // Character offset from origin to the atlas region's top-left corner.
  // bearingX/bearingY already include the SDF buffer.
  vec2 charOffsetPixels = charOffset * fontScale;

  // The character's local X offset from pathPos (which is at character center)
  float charLocalX = -charAdvance * 0.5 * fontScale;

  // Build quad position:
  // - Start at character origin (charLocalX on X axis, 0 on Y axis = baseline)
  // - Add bearing offset to get to atlas region corner
  // - Add quad corner * size to get vertex position
  vec2 quadPos;
  quadPos.x = charLocalX + charOffsetPixels.x + a_quadCorner.x * charSizePixels.x;
  // charOffset.y = -bearingY (negated), so -charOffsetPixels.y = bearingY * fontScale
  // (distance from baseline to atlas region top, positive = upward)
  // Quad corner (0,0) = bottom-left, (1,1) = top-right
  quadPos.y = -charOffsetPixels.y - charSizePixels.y * (1.0 - a_quadCorner.y);

  // Center vertically on the path by offsetting by half the visual text height
  // VERTICAL_CENTER_RATIO is the distance from baseline to visual center as a ratio of atlas font size
  float verticalCenterOffset = VERTICAL_CENTER_RATIO * ATLAS_FONT_SIZE * fontScale;
  quadPos.y -= verticalCenterOffset;

  // -------------------------------------------------------------------------
  // Step 9: Rotate quad to align with tangent
  // -------------------------------------------------------------------------
  // Rotation matrix from tangent
  // tangent = (cos(angle), sin(angle)), so we can build rotation directly
  mat2 rotation = mat2(tangent.x, tangent.y, -tangent.y, tangent.x);

  // Convert pixel offset to WebGL units for rotation
  `).concat(h?"vec2 quadPosWebGL = quadPos * u_correctionRatio / u_sizeRatio; // Scaled mode":"vec2 quadPosWebGL = quadPos * pixelToGraph; // Fixed mode: use pixelToGraph for zoom-independent size",`

  // Rotate around character center on path
  vec2 rotatedOffset = rotation * quadPosWebGL;

  // Final position in graph space (using offset path position for above/below modes)
  vec2 worldPos = offsetPathPos + rotatedOffset;

  // -------------------------------------------------------------------------
  // Step 10: Transform to clip space
  // -------------------------------------------------------------------------
  vec3 clipPos = u_matrix * vec3(worldPos, 1.0);
  gl_Position = vec4(clipPos.xy, 0.0, 1.0);

  // -------------------------------------------------------------------------
  // Step 11: Texture coordinates
  // -------------------------------------------------------------------------
  // Flip Y for texture coordinates (texture Y goes down, quad Y goes up)
  vec2 texCorner = vec2(a_quadCorner.x, 1.0 - a_quadCorner.y);
  v_texCoord = (a_texCoords.xy + texCorner * a_texCoords.zw) / u_atlasSize;

  // -------------------------------------------------------------------------
  // Step 12: Pass color, border color, and alpha modifier
  // -------------------------------------------------------------------------
  v_color = a_color;
  v_color.a *= bias;
`).concat(e?`  v_borderColor = a_borderColor;
  v_borderColor.a *= bias;
  v_positionMode = positionMode;`:"",`
  v_alphaModifier = alphaModifier;

  // -------------------------------------------------------------------------
  // Step 13: Compute edge fade for soft truncation
  // -------------------------------------------------------------------------
  // Convert fade width from pixels to WebGL units
  `).concat(h?"float fadeWidthWebGL = FADE_WIDTH_PIXELS * u_correctionRatio / u_sizeRatio;":"float fadeWidthWebGL = FADE_WIDTH_PIXELS * pixelToGraph;",`

  // Compute the arc position of THIS VERTEX (not just character center)
  // The quad extends from charCenter - advance/2 to charCenter + advance/2
  // a_quadCorner.x is 0 for left edge, 1 for right edge
  float vertexLocalOffset = (a_quadCorner.x - 0.5) * charAdvanceWebGL;
  float vertexArcOffset = charCenterOffset + vertexLocalOffset;

  // Compute distance from body edges (positive = inside body, negative = outside)
  float halfBody = bodyLength * 0.5;
  float distFromStart = vertexArcOffset + halfBody;  // Distance from body start edge
  float distFromEnd = halfBody - vertexArcOffset;    // Distance from body end edge
  float distFromEdge = min(distFromStart, distFromEnd);

  // Compute fade: 0 = fully visible (deep inside body), 1 = fully faded (at body edge)
  // Fade goes from 0 (at 2*fadeWidth inside) to 1 (at body edge)
  // This ensures text is fully transparent before reaching extremities
  v_edgeFade = 1.0 - smoothstep(0.0, fadeWidthWebGL * 2.0, distFromEdge);
}
`);return m}function bo(){var a=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},r=a.hasBorder,t=r===void 0?!1:r,e=`#version 300 es
precision highp float;

in vec2 v_texCoord;
in vec4 v_color;
`.concat(t?"in vec4 v_borderColor;":"",`
in float v_edgeFade;  // 0 = fully visible, 1 = fully faded
in float v_alphaModifier;  // 0-1 based on label visibility ratio
in float v_fontScale;  // Ratio of rendered font size to atlas font size
`).concat(t?"in float v_positionMode;  // Position mode (0=over, 1=above, 2=below, 3=auto)":"",`

uniform sampler2D u_atlas;
uniform float u_gamma;
uniform float u_sdfBuffer;
uniform float u_pixelRatio;
`).concat(t?"uniform float u_borderWidth;  // Border width in SDF units (normalized)":"",`

// Fragment output (single target - picking handled via separate pass)
out vec4 fragColor;

void main() {
  #ifdef PICKING_MODE
    // Edge labels are not pickable - discard all fragments in picking mode
    discard;
  #else
  // SDF stores normalized distance: 0.5 = on edge, >0.5 = inside glyph
  float sdfValue = texture(u_atlas, v_texCoord).a;

  // Edge threshold accounting for SDF buffer padding
  float edge = 1.0 - u_sdfBuffer;

  // Scale gamma inversely with font scale so small labels get a wider AA band
  // (smoother) and large labels get a tighter band (sharper).
  float aaWidth = u_gamma / (u_pixelRatio * v_fontScale);

  // Apply edge fade for soft truncation at body boundaries
  // Also apply visibility-based alpha modifier for short edge labels
  float edgeAlpha = (1.0 - v_edgeFade) * v_alphaModifier;

`).concat(t?`  // Fill alpha: fully opaque inside the glyph
  float fillAlpha = smoothstep(edge - aaWidth, edge + aaWidth, sdfValue);

  // Only apply border for "over" position mode (v_positionMode == 0.0)
  // Labels positioned above/below/auto don't overlap the edge line and don't need borders
  if (v_positionMode < 0.5) {
    // Border rendering: compute alpha for both fill and border regions
    // Border extends from (edge - borderWidth) to edge
    float borderEdge = edge - u_borderWidth;

    // Border alpha: opaque in the border region (between borderEdge and edge)
    float borderAlpha = smoothstep(borderEdge - aaWidth, borderEdge + aaWidth, sdfValue);

    // Composite: fill on top of border
    // Border is visible where borderAlpha > 0 but fillAlpha < 1
    vec3 borderColorPremult = v_borderColor.rgb * v_borderColor.a * borderAlpha * edgeAlpha;
    vec3 fillColorPremult = v_color.rgb * v_color.a * fillAlpha * edgeAlpha;

    // Blend fill over border (fill replaces border where fill is opaque)
    float finalBorderAlpha = borderAlpha * (1.0 - fillAlpha);
    vec3 finalColor = fillColorPremult + v_borderColor.rgb * v_borderColor.a * finalBorderAlpha * edgeAlpha;
    float finalAlpha = (v_color.a * fillAlpha + v_borderColor.a * finalBorderAlpha) * edgeAlpha;

    fragColor = vec4(finalColor, finalAlpha);
  } else {
    // No border for above/below/auto positions - simple text rendering
    float finalAlpha = v_color.a * fillAlpha * edgeAlpha;
    fragColor = vec4(v_color.rgb * finalAlpha, finalAlpha);
  }`:`  // Smooth transition from transparent to opaque at glyph edge
  float alpha = smoothstep(edge - aaWidth, edge + aaWidth, sdfValue);

  // Premultiplied alpha output
  float finalAlpha = v_color.a * alpha * edgeAlpha;
  fragColor = vec4(v_color.rgb * finalAlpha, finalAlpha);`,`
  #endif
}
`);return e}function xo(a){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!1,t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:"fixed",e=["u_matrix","u_sizeRatio","u_correctionRatio","u_pixelRatio","u_cameraAngle","u_sdfBufferPixels","u_resolution","u_atlasSize","u_atlas","u_gamma","u_sdfBuffer","u_nodeDataTexture","u_nodeDataTextureWidth","u_edgeDataTexture","u_edgeDataTextureWidth","u_edgeFrameTexture","u_edgeFrameTextureWidth","u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge"];t==="scaled"&&e.push("u_zoomSizeRatio"),r&&e.push("u_borderWidth");var n=M(a),i;try{for(n.s();!(i=n.n()).done;){var o=i.value,s=M(o.uniforms),l;try{for(s.s();!(l=s.n()).done;){var d=l.value;e.includes(d.name)||e.push(d.name)}}catch(h){s.e(h)}finally{s.f()}}}catch(h){n.e(h)}finally{n.f()}return e}function yo(a){var r=a.hasBorder,t=r===void 0?!1:r,e=a.fontSizeMode,n=e===void 0?"fixed":e;return{vertexShader:po(a),fragmentShader:bo({hasBorder:t}),uniforms:xo(a.paths,t,n)}}var To=new Map;function _o(a){switch(a){case"over":return 0;case"above":return 1;case"below":return 2;case"auto":return 3;default:return 0}}function So(a,r,t,e){var n=e.color,i=e.margin,o=e.textBorder,s=Bn(e),l=s.paths,d=s.fontSizeMode,h=s.minVisibilityThreshold,u=s.fullVisibilityThreshold,c=!!o,v=yo({paths:l,hasBorder:c,fontSizeMode:d,minVisibilityThreshold:h,fullVisibilityThreshold:u}),b=(function(m){function x(g,f,p){var y;V(this,x),y=ee(this,x,[g,f,p]),S(y,"atlasTexture",null),S(y,"atlasNeedsUpdate",!1),S(y,"labelGlyphCache",new Map),S(y,"edgeAttributeTexture",null);var T=tt();if(y.attributeLayout=fe([].concat(H(l),[T])),y.attrDescriptors=At([].concat(H(l),[T]),y.attributeLayout),y.edgeAttributeTexture=new Rt(g,y.attributeLayout),y.packedAttributeData=new Float32Array(y.attributeLayout.floatsPerItem),y.atlasManager=new Oe,y.gamma=.025,y.sdfBuffer=pe.cutoff,y.atlasTexture=g.createTexture(),!y.atlasTexture)throw new Error("EdgeLabelProgram: failed to create atlas texture");g.bindTexture(g.TEXTURE_2D,y.atlasTexture),g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE),g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE),g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR),g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR),g.bindTexture(g.TEXTURE_2D,null),y.atlasManager.on(Oe.ATLAS_UPDATED_EVENT,function(){y.atlasNeedsUpdate=!0,setTimeout(function(){return y.renderer.refresh()},0)});var _={family:"sans-serif",weight:"normal",style:"normal"};return y.defaultFontKey=y.atlasManager.registerFont(_),y}return te(x,m),X(x,[{key:"getDefinition",value:function(){var f=WebGL2RenderingContext,p=f.FLOAT,y=f.UNSIGNED_BYTE,T=f.TRIANGLE_STRIP,_=new Set,E=[],A=M(l),R;try{for(A.s();!(R=A.n()).done;){var L=R.value,F=M(L.attributes),C;try{for(F.s();!(C=F.n()).done;){var P=C.value,D=P.name.startsWith("a_")?P.name:"a_".concat(P.name);_.has(D)||(_.add(D),E.push({name:D,size:P.size,type:P.type}))}}catch(k){F.e(k)}finally{F.f()}}}catch(k){A.e(k)}finally{A.f()}return{VERTICES:4,VERTEX_SHADER_SOURCE:v.vertexShader,FRAGMENT_SHADER_SOURCE:v.fragmentShader,METHOD:T,UNIFORMS:v.uniforms,ATTRIBUTES:[{name:"a_edgeIndex",size:1,type:p},{name:"a_edgeAttrIndex",size:1,type:p},{name:"a_baseFontSize",size:1,type:p},{name:"a_charMetrics",size:4,type:p},{name:"a_charDims",size:4,type:p},{name:"a_texCoords",size:4,type:p},{name:"a_labelParams",size:2,type:p},{name:"a_color",size:4,type:y,normalized:!0}].concat(H(c?[{name:"a_borderColor",size:4,type:y,normalized:!0}]:[]),H(E.filter(function(k){return!["a_curvature","curvature"].includes(k.name)}))),CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:p}],CONSTANT_DATA:[[0,0],[1,0],[0,1],[1,1]]}}},{key:"prepareLabelGlyphs",value:function(f,p){if(p.hidden||!p.text){this.labelGlyphCache.delete(f);return}var y=p.text,T=p.fontKey||this.defaultFontKey;this.atlasManager.ensureGlyphs(y,T);var _=[],E=[],A=0,R=M(y),L;try{for(R.s();!(L=R.n()).done;){var F=L.value,C=F.codePointAt(0);if(C===void 0){_.push(void 0),E.push(A);continue}var P=this.atlasManager.getGlyph(C,T);_.push(P),E.push(A),P&&(A+=P.advance)}}catch(D){R.e(D)}finally{R.f()}this.labelGlyphCache.set(f,{glyphs:_,xOffsets:E,totalWidth:A})}},{key:"processCharacter",value:function(f,p,y,T){var _,E,A,R=this.floats,L=this.STRIDE,F=f*L,C=this.labelGlyphCache.get(p.parentKey);if(!C||!C.glyphs[T]){for(var P=0;P<L;P++)R[F+P]=0;return}var D=C.glyphs[T],k=C.xOffsets[T],w=x.labelColor,I=w&&q(w)==="object"&&"color"in w&&w.color?w.color:p.color,G=me(I),z=F;R[z++]=p.edgeIndex,R[z++]=(_=(E=this.edgeAttributeTexture)===null||E===void 0?void 0:E.getIndex(p.parentKey))!==null&&_!==void 0?_:0,R[z++]=p.size,R[z++]=k,R[z++]=D.advance,R[z++]=C.totalWidth,R[z++]=_o(p.position),R[z++]=D.atlasWidth,R[z++]=D.atlasHeight,R[z++]=D.bearingX,R[z++]=-D.bearingY,R[z++]=D.atlasX,R[z++]=D.atlasY,R[z++]=D.atlasWidth,R[z++]=D.atlasHeight;var B=(A=x.labelMargin)!==null&&A!==void 0?A:p.margin;if(R[z++]=B,R[z++]=0,R[z++]=G,c&&o){var O;typeof o.color=="string"?O=o.color:O=o.color.color||"#ffffff",R[z++]=me(O)}var W=new Set,U=M(l),K;try{for(U.s();!(K=U.n()).done;){var Z=K.value,J=M(Z.attributes),ie;try{for(J.s();!(ie=J.n()).done;){var ae=ie.value,ge=ae.name.startsWith("a_")?ae.name.slice(2):ae.name;if(ge!=="curvature"&&!W.has(ge)){W.add(ge);for(var ke=0;ke<ae.size;ke++)R[z++]=0}}}catch(xe){J.e(xe)}finally{J.f()}}}catch(xe){U.e(xe)}finally{U.f()}}},{key:"processEdgeLabel",value:function(f,p,y){if(this.prepareLabelGlyphs(f,y),this.edgeAttributeTexture&&!y.hidden&&y.text){this.edgeAttributeTexture.allocate(f);var T=this.packedAttributeData;Dt(this.attrDescriptors,y.edgeAttributes,T,"",1,To,0),this.edgeAttributeTexture.updateAllAttributes(f,T)}return ne(x,"processLabel",this)([f,p,y])}},{key:"updateAtlasTexture",value:function(){if(this.atlasNeedsUpdate){var f=this.normalProgram.gl,p=this.atlasManager.getTextures();if(p.length!==0){var y=p[0];f.bindTexture(f.TEXTURE_2D,this.atlasTexture),f.texImage2D(f.TEXTURE_2D,0,f.RGBA,y.width,y.height,0,f.RGBA,f.UNSIGNED_BYTE,y.data),f.bindTexture(f.TEXTURE_2D,null),this.atlasNeedsUpdate=!1}}}},{key:"setUniforms",value:function(f,p){var y=p.gl,T=p.uniformLocations,_=this.atlasManager.getTextures(),E=_.length>0?[_[0].width,_[0].height]:[1,1];if(y.uniformMatrix3fv(T.u_matrix,!1,f.matrix),y.uniform1f(T.u_sizeRatio,f.sizeRatio),y.uniform1f(T.u_correctionRatio,f.correctionRatio),y.uniform1f(T.u_pixelRatio,f.pixelRatio),y.uniform1f(T.u_cameraAngle,f.cameraAngle),y.uniform1f(T.u_sdfBufferPixels,pe.buffer),y.uniform2f(T.u_resolution,f.width,f.height),y.uniform2f(T.u_atlasSize,E[0],E[1]),y.uniform1f(T.u_gamma,this.gamma),y.uniform1f(T.u_sdfBuffer,this.sdfBuffer),y.activeTexture(y.TEXTURE0),y.bindTexture(y.TEXTURE_2D,this.atlasTexture),y.uniform1i(T.u_atlas,0),T.u_nodeDataTexture!==void 0&&y.uniform1i(T.u_nodeDataTexture,f.nodeDataTextureUnit),T.u_nodeDataTextureWidth!==void 0&&y.uniform1i(T.u_nodeDataTextureWidth,f.nodeDataTextureWidth),T.u_edgeDataTexture!==void 0&&y.uniform1i(T.u_edgeDataTexture,f.edgeDataTextureUnit),T.u_edgeDataTextureWidth!==void 0&&y.uniform1i(T.u_edgeDataTextureWidth,f.edgeDataTextureWidth),T.u_edgeFrameTexture!==void 0&&y.uniform1i(T.u_edgeFrameTexture,f.edgeFrameTextureUnit),T.u_edgeFrameTextureWidth!==void 0&&y.uniform1i(T.u_edgeFrameTextureWidth,f.edgeFrameTextureWidth),c&&o&&T.u_borderWidth!==void 0){var A=o.width/pe.buffer*this.sdfBuffer;y.uniform1f(T.u_borderWidth,A)}if(this.edgeAttributeTexture&&T.u_edgeAttributeTexture!==void 0&&(this.edgeAttributeTexture.bind(_e),y.uniform1i(T.u_edgeAttributeTexture,_e),y.uniform1i(T.u_edgeAttributeTextureWidth,this.edgeAttributeTexture.getTextureWidth()),y.uniform1i(T.u_edgeAttributeTexelsPerEdge,this.edgeAttributeTexture.getTexelsPerItem())),d==="scaled"&&T.u_zoomSizeRatio!==void 0){var R=this.renderer.getSetting("zoomToSizeRatioFunction"),L=1/R(f.zoomRatio);y.uniform1f(T.u_zoomSizeRatio,L)}}},{key:"renderProgram",value:function(f,p){this.updateAtlasTexture(),this.atlasManager.hasPendingGlyphs()&&(this.atlasManager.flush(),this.updateAtlasTexture()),this.edgeAttributeTexture&&this.edgeAttributeTexture.upload(),ne(x,"renderProgram",this)([f,p])}},{key:"registerFont",value:function(f){var p=arguments.length>1&&arguments[1]!==void 0?arguments[1]:"normal",y=arguments.length>2&&arguments[2]!==void 0?arguments[2]:"normal";return this.atlasManager.registerFont({family:f,weight:p,style:y})}},{key:"getAtlasManager",value:function(){return this.atlasManager}},{key:"ensureGlyphsReady",value:function(f,p){var y=p||this.defaultFontKey,T=M(f),_;try{for(T.s();!(_=T.n()).done;){var E=_.value;this.atlasManager.ensureGlyphs(E,y)}}catch(A){T.e(A)}finally{T.f()}this.atlasManager.flush()}},{key:"measureLabelAtlasWidth",value:function(f,p){var y=p||this.defaultFontKey;this.atlasManager.ensureGlyphs(f,y),this.atlasManager.hasPendingGlyphs()&&this.atlasManager.flush();var T=0,_=M(f),E;try{for(_.s();!(E=_.n()).done;){var A=E.value,R=A.codePointAt(0);if(R!==void 0){var L=this.atlasManager.getGlyph(R,y);L&&(T+=L.advance)}}}catch(F){_.e(F)}finally{_.f()}return T}},{key:"measureLabel",value:function(f,p,y){var T=this.measureLabelAtlasWidth(f,y),_=p/pe.fontSize;return{width:T*_,height:p,textHeight:p}}},{key:"kill",value:function(){var f=this.normalProgram.gl;this.atlasTexture&&(f.deleteTexture(this.atlasTexture),this.atlasTexture=null),this.edgeAttributeTexture&&(this.edgeAttributeTexture.kill(),this.edgeAttributeTexture=null),this.atlasManager.destroy(),this.labelGlyphCache.clear(),ne(x,"kill",this)([])}}])})(Fn);return S(b,"labelColor",n),S(b,"labelMargin",i),new b(a,r,t)}function Eo(){var a=`
// No extremity - always returns positive (outside)
float extremity_none(vec2 uv, float lengthRatio, float widthRatio) {
  return 1.0;
}
`;return{name:"none",glsl:a,length:0,widthFactor:1,margin:0,uniforms:[],attributes:[]}}function Ro(a,r,t,e){var n,i,o=zn(e),s=o.paths,l=o.layers,d=o.defaultHead,h=o.defaultTail,u=[Eo()].concat(H(o.extremities)),c={},v={};s.forEach(function(L,F){return c[L.name]=F}),u.forEach(function(L,F){return v[L.name]=F});var b=(n=v[d])!==null&&n!==void 0?n:0,m=(i=v[h])!==null&&i!==void 0?i:0,x=null,g=fe([].concat(H(s),H(l))),f=(function(L){function F(C,P,D){var k;V(this,F),x||(x=Ha({paths:s,extremities:u,layers:l})),k=ee(this,F,[C,P,D]),S(k,"layerLifecycles",new Map),S(k,"needsShaderRegeneration",!1),S(k,"edgeAttributeTexture",null),S(k,"layout",g),S(k,"attrDescriptors",[]),S(k,"lifecycleIndexOffset",s.length),k._pickingBuffer=P,k.edgeAttributeTexture=new Rt(C,k.layout),k.packedAttributeData=new Float32Array(k.layout.floatsPerItem),l.forEach(function(I,G){if(I.lifecycle){var z={gl:C,renderer:{refresh:function(){return D.refresh()}},getUniformLocation:function(O){return C.getUniformLocation(k.normalProgram.program,O)},requestShaderRegeneration:function(){k.needsShaderRegeneration=!0},requestRefresh:function(){D.refresh()}};k.layerLifecycles.set(G,I.lifecycle(z))}}),k.layerLifecycles.forEach(function(I){var G;return(G=I.init)===null||G===void 0?void 0:G.call(I)});var w=new Map;return k.layerLifecycles.forEach(function(I,G){I.getAttributeData&&w.set(s.length+G,I)}),k.attrDescriptors=At([].concat(H(s),H(l)),k.layout,w),k}return te(F,L),X(F,[{key:"getAttributeTexture",value:function(){return this.edgeAttributeTexture}},{key:"resolveEdgeIds",value:function(P,D,k){var w=P,I=0,G=b,z=m,B=D?w.selfLoopPath:k&&w.parallelPath?w.parallelPath:w.path;B&&c[B]!==void 0&&(I=c[B]),w.head&&w.head!=="none"&&v[w.head]!==void 0&&(G=v[w.head]),w.tail&&w.tail!=="none"&&v[w.tail]!==void 0&&(z=v[w.tail]);var O=u[G],W=u[z];return{pathId:I,headId:G,tailId:z,headLengthRatio:De(O.length)?0:O.length,tailLengthRatio:De(W.length)?0:W.length}}},{key:"getDefinition",value:function(){var P=WebGL2RenderingContext,D=P.TRIANGLE_STRIP,k=D,w=x;return{VERTICES:w.verticesPerEdge,VERTEX_SHADER_SOURCE:w.vertexShader,FRAGMENT_SHADER_SOURCE:w.fragmentShader,METHOD:k,UNIFORMS:w.uniforms,ATTRIBUTES:w.attributes,CONSTANT_ATTRIBUTES:w.constantAttributes,CONSTANT_DATA:w.constantData}}},{key:"maybeRegenerateShaders",value:function(){var P=this;if(this.needsShaderRegeneration){this.needsShaderRegeneration=!1;var D=l.map(function(O,W){var U=P.layerLifecycles.get(W);return U!=null&&U.regenerate?U.regenerate():O});x=Ha({paths:s,extremities:u,layers:D});var k=this.normalProgram.gl,w=this.normalProgram,I=w.program,G=w.buffer,z=w.vertexShader,B=w.fragmentShader;k.deleteProgram(I),k.deleteBuffer(G),k.deleteShader(z),k.deleteShader(B),this.normalProgram=this.getProgramInfo("normal",k,x.vertexShader,x.fragmentShader,this._pickingBuffer)}}},{key:"process",value:function(P,D,k,w,I,G){var z=D*this.STRIDE;if(I.visibility==="hidden"||k.visibility==="hidden"||w.visibility==="hidden"){for(var B=z+this.STRIDE;z<B;z++)this.floats[z]=0;return}this.processVisibleItem(yt(P),z,k,w,I,G)}},{key:"processVisibleItem",value:function(P,D,k,w,I,G){var z,B=this.floats,O=this.ints;B[D++]=G;var W=(z=I.opacity)!==null&&z!==void 0?z:1;if(W<1){var U=Ze(I.color),K=Q(U,4),Z=K[0],J=K[1],ie=K[2],ae=K[3];B[D++]=cn(Z,J,ie,ae*W|0)}else B[D++]=me(I.color);O[D++]=P;var ge=this.packedAttributeData;Dt(this.attrDescriptors,I,ge,I.color,W,this.layerLifecycles,this.lifecycleIndexOffset),this.edgeAttributeTexture.updateAllAttributes(G,ge)}},{key:"setUniforms",value:function(P,D){var k=this,w=D.gl,I=D.uniformLocations;I.u_matrix&&w.uniformMatrix3fv(I.u_matrix,!1,P.matrix),I.u_sizeRatio&&w.uniform1f(I.u_sizeRatio,P.sizeRatio),I.u_correctionRatio&&w.uniform1f(I.u_correctionRatio,P.correctionRatio),I.u_zoomRatio&&w.uniform1f(I.u_zoomRatio,P.zoomRatio),I.u_pixelRatio&&w.uniform1f(I.u_pixelRatio,P.pixelRatio),I.u_cameraAngle&&w.uniform1f(I.u_cameraAngle,P.cameraAngle),I.u_feather&&w.uniform1f(I.u_feather,P.antiAliasingFeather),I.u_minEdgeThickness&&w.uniform1f(I.u_minEdgeThickness,P.minEdgeThickness),I.u_pickingPadding&&w.uniform1f(I.u_pickingPadding,P.edgePickingPadding),I.u_nodeDataTexture&&w.uniform1i(I.u_nodeDataTexture,P.nodeDataTextureUnit),I.u_nodeDataTextureWidth&&w.uniform1i(I.u_nodeDataTextureWidth,P.nodeDataTextureWidth),I.u_edgeDataTexture&&w.uniform1i(I.u_edgeDataTexture,P.edgeDataTextureUnit),I.u_edgeDataTextureWidth&&w.uniform1i(I.u_edgeDataTextureWidth,P.edgeDataTextureWidth),I.u_edgeFrameTexture&&w.uniform1i(I.u_edgeFrameTexture,P.edgeFrameTextureUnit),I.u_edgeFrameTextureWidth&&w.uniform1i(I.u_edgeFrameTextureWidth,P.edgeFrameTextureWidth),this.edgeAttributeTexture&&this.layout.floatsPerItem>0&&(this.edgeAttributeTexture.bind(_e),I.u_edgeAttributeTexture&&w.uniform1i(I.u_edgeAttributeTexture,_e),I.u_edgeAttributeTextureWidth&&w.uniform1i(I.u_edgeAttributeTextureWidth,this.edgeAttributeTexture.getTextureWidth()),I.u_edgeAttributeTexelsPerEdge&&w.uniform1i(I.u_edgeAttributeTexelsPerEdge,this.edgeAttributeTexture.getTexelsPerItem()));var G=new Set;s.forEach(function(z){z.uniforms.forEach(function(B){G.has(B.name)||(G.add(B.name),k.setTypedUniform(B,D))})}),u.forEach(function(z){z.uniforms.forEach(function(B){G.has(B.name)||(G.add(B.name),k.setTypedUniform(B,D))})}),l.forEach(function(z){z.uniforms.forEach(function(B){G.has(B.name)||(G.add(B.name),k.setTypedUniform(B,D))})})}},{key:"renderProgram",value:function(P,D){this.maybeRegenerateShaders(),this.layerLifecycles.forEach(function(k){var w;return(w=k.beforeRender)===null||w===void 0?void 0:w.call(k)}),ne(F,"renderProgram",this)([P,D])}},{key:"uploadAttributeTexture",value:function(){this.edgeAttributeTexture&&this.layout.floatsPerItem>0&&this.edgeAttributeTexture.upload()}},{key:"kill",value:function(){this.layerLifecycles.forEach(function(P){var D;return(D=P.kill)===null||D===void 0?void 0:D.call(P)}),this.edgeAttributeTexture&&(this.edgeAttributeTexture.kill(),this.edgeAttributeTexture=null),ne(F,"kill",this)([])}}])})(Fe),p=u[b],y=u[m],T=N({paths:s,headLengthRatio:De(p.length)?0:p.length,tailLengthRatio:De(y.length)?0:y.length},e.label),_=Bn(T),E=So(a,null,t,T),A=go(a,r,t,{shaderConfig:_}),R=new io(a,{paths:s,extremities:u,layers:l});return{edgeProgram:new f(a,null,t),labelProgram:E,labelBackgroundProgram:A,framePass:R}}var Ao=2;function Do(a,r,t){var e=arguments.length>3&&arguments[3]!==void 0?arguments[3]:Ao,n=r.canvas,i=n.width,o=n.height,s=t.x,l=t.y,d=t.rowHeight,h=t.maxRowWidth,u={},c=[],v=M(a),b;try{for(v.s();!(b=v.n()).done;){var m=b.value,x=m.width+e,g=m.height+e;if(x>i||g>o||s+x>i&&l+d+g>o){c.push(m);continue}s+x>i&&(h=Math.max(h,s),s=0,l+=d,d=g),m.draw(r,s,l),u[m.key]={x:s,y:l,width:m.width,height:m.height},s+=x,d=Math.max(d,g)}}catch(f){v.e(f)}finally{v.f()}return h=Math.max(h,s),{atlas:u,cursor:{x:s,y:l,rowHeight:d,maxRowWidth:h},remaining:c}}function oe(a,r,t,e){var n=Object.defineProperty;try{n({},"",{})}catch{n=0}oe=function(i,o,s,l){function d(h,u){oe(i,h,function(c){return this._invoke(h,u,c)})}o?n?n(i,o,{value:s,enumerable:!l,configurable:!l,writable:!l}):i[o]=s:(d("next",0),d("throw",1),d("return",2))},oe(a,r,t,e)}function le(){/*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */var a,r,t=typeof Symbol=="function"?Symbol:{},e=t.iterator||"@@iterator",n=t.toStringTag||"@@toStringTag";function i(v,b,m,x){var g=b&&b.prototype instanceof s?b:s,f=Object.create(g.prototype);return oe(f,"_invoke",(function(p,y,T){var _,E,A,R=0,L=T||[],F=!1,C={p:0,n:0,v:a,a:P,f:P.bind(a,4),d:function(D,k){return _=D,E=0,A=a,C.n=k,o}};function P(D,k){for(E=D,A=k,r=0;!F&&R&&!w&&r<L.length;r++){var w,I=L[r],G=C.p,z=I[2];D>3?(w=z===k)&&(A=I[(E=I[4])?5:(E=3,3)],I[4]=I[5]=a):I[0]<=G&&((w=D<2&&G<I[1])?(E=0,C.v=k,C.n=I[1]):G<z&&(w=D<3||I[0]>k||k>z)&&(I[4]=D,I[5]=k,C.n=z,E=0))}if(w||D>1)return o;throw F=!0,k}return function(D,k,w){if(R>1)throw TypeError("Generator is already running");for(F&&k===1&&P(k,w),E=k,A=w;(r=E<2?a:A)||!F;){_||(E?E<3?(E>1&&(C.n=-1),P(E,A)):C.n=A:C.v=A);try{if(R=2,_){if(E||(D="next"),r=_[D]){if(!(r=r.call(_,A)))throw TypeError("iterator result is not an object");if(!r.done)return r;A=r.value,E<2&&(E=0)}else E===1&&(r=_.return)&&r.call(_),E<2&&(A=TypeError("The iterator does not provide a '"+D+"' method"),E=1);_=a}else if((r=(F=C.n<0)?A:p.call(y,C))!==o)break}catch(I){_=a,E=1,A=I}finally{R=1}}return{value:r,done:F}}})(v,m,x),!0),f}var o={};function s(){}function l(){}function d(){}r=Object.getPrototypeOf;var h=[][e]?r(r([][e]())):(oe(r={},e,function(){return this}),r),u=d.prototype=s.prototype=Object.create(h);function c(v){return Object.setPrototypeOf?Object.setPrototypeOf(v,d):(v.__proto__=d,oe(v,n,"GeneratorFunction")),v.prototype=Object.create(u),v}return l.prototype=d,oe(u,"constructor",d),oe(d,"constructor",l),l.displayName="GeneratorFunction",oe(d,n,"GeneratorFunction"),oe(u),oe(u,n,"Generator"),oe(u,e,function(){return this}),oe(u,"toString",function(){return"[object Generator]"}),(le=function(){return{w:i,m:c}})()}function Xa(a,r,t,e,n,i,o){try{var s=a[i](o),l=s.value}catch(d){return void t(d)}s.done?r(l):Promise.resolve(l).then(e,n)}function He(a){return function(){var r=this,t=arguments;return new Promise(function(e,n){var i=a.apply(r,t);function o(l){Xa(i,e,n,o,s,"next",l)}function s(l){Xa(i,e,n,o,s,"throw",l)}o(void 0)})}}var ht=new Map,qa=!1;function Co(a){return new Promise(function(r,t){var e=new FileReader;e.onload=function(){return r(e.result)},e.onerror=t,e.readAsDataURL(a)})}function Lo(a){if(!ht.has(a)){var r=fetch(a).then(function(t){return t.blob()}).then(Co).catch(function(){return ht.delete(a),null});ht.set(a,r)}return ht.get(a)}function Po(a){return Zt.apply(this,arguments)}function Zt(){return Zt=He(le().m(function a(r){var t,e,n;return le().w(function(i){for(;;)switch(i.n){case 0:return t=document.createElement("div"),t.innerHTML=r,e=Array.from(t.querySelectorAll("img[src]")),n=e.filter(function(o){return!o.getAttribute("src").startsWith("data:")}),i.n=1,Promise.all(n.map((function(){var o=He(le().m(function s(l){var d;return le().w(function(h){for(;;)switch(h.n){case 0:return h.n=1,Lo(l.getAttribute("src"));case 1:d=h.v,d&&l.setAttribute("src",d);case 2:return h.a(2)}},s)}));return function(s){return o.apply(this,arguments)}})()));case 1:return i.a(2,t.innerHTML)}},a)})),Zt.apply(this,arguments)}function Wn(a){return $t.apply(this,arguments)}function $t(){return $t=He(le().m(function a(r){var t,e,n,i,o,s,l,d,h,u,c,v,b,m=arguments;return le().w(function(x){for(;;)switch(x.n){case 0:if(t=m.length>1&&m[1]!==void 0?m[1]:1,e=r instanceof SVGElement?new XMLSerializer().serializeToString(r):r,n=new DOMParser,i=n.parseFromString(e,"image/svg+xml"),o=i.querySelector("svg"),o){x.n=1;break}return x.a(2,null);case 1:if(s=parseFloat(o.getAttribute("width")||""),l=parseFloat(o.getAttribute("height")||""),(!(s>0)||!(l>0))&&(d=o.getAttribute("viewBox"),d&&(h=d.trim().split(/[\s,]+/),s=parseFloat(h[2]),l=parseFloat(h[3]))),!(!(s>0)||!(l>0))){x.n=2;break}return console.warn("Sigma: SVG label attachment has no parseable dimensions — skipped."),x.a(2,null);case 2:return u=Math.ceil(s*t),c=Math.ceil(l*t),v=new Blob([e],{type:"image/svg+xml"}),b=URL.createObjectURL(v),x.a(2,new Promise(function(g){var f=new Image;f.onload=function(){var p=document.createElement("canvas");p.width=u,p.height=c,p.getContext("2d").drawImage(f,0,0,u,c),URL.revokeObjectURL(b);try{p.getContext("2d").getImageData(0,0,1,1)}catch(y){if(y instanceof DOMException&&y.name==="SecurityError"){qa||(qa=!0,console.warn('Sigma: A label attachment was skipped because the rendered canvas is tainted. SVG with <foreignObject> (used by the "html" attachment type) is blocked in Chromium and Safari. Use type: "canvas" with Canvas 2D rendering instead.')),g(null);return}throw y}g(p)},f.onerror=function(){URL.revokeObjectURL(b),g(null)},f.src=b}))}},a)})),$t.apply(this,arguments)}function Fo(a,r){var t=document.createElement("div");t.style.cssText="position:fixed;left:-99999px;top:0;visibility:hidden;width:max-content;height:max-content",t.innerHTML=(r?"<style>".concat(r,"</style>"):"")+a,document.body.appendChild(t);var e=t.getBoundingClientRect(),n=e.width,i=e.height;return document.body.removeChild(t),{width:Math.ceil(n),height:Math.ceil(i)}}function ko(a,r,t,e){return Qt.apply(this,arguments)}function Qt(){return Qt=He(le().m(function a(r,t,e,n){var i,o,s,l,d,h,u,c,v=arguments;return le().w(function(b){for(;;)switch(b.n){case 0:return i=v.length>4&&v[4]!==void 0?v[4]:1,o=r instanceof HTMLElement?r.outerHTML:r,b.n=1,Po(o);case 1:return s=b.v,(e==null||n==null)&&(l=Fo(s,t),e=e??l.width,n=n??l.height),d=Math.ceil(e*i),h=Math.ceil(n*i),u=t?"<style>".concat(t,"</style>"):"",c='<svg xmlns="http://www.w3.org/2000/svg" '+'width="'.concat(d,'" height="').concat(h,'" viewBox="0 0 ').concat(e," ").concat(n,'">')+'<foreignObject width="'.concat(e,'" height="').concat(n,'">')+'<body xmlns="http://www.w3.org/1999/xhtml" style="margin:0;padding:0">'.concat(u).concat(s,"</body>")+"</foreignObject></svg>",b.a(2,Wn(c,1))}},a)})),Qt.apply(this,arguments)}function wo(a){return Jt.apply(this,arguments)}function Jt(){return Jt=He(le().m(function a(r){var t,e=arguments,n;return le().w(function(i){for(;;)switch(i.n){case 0:t=e.length>1&&e[1]!==void 0?e[1]:1,n=r.type,i.n=n==="canvas"?1:n==="svg"?2:n==="html"?3:4;break;case 1:return i.a(2,r.canvas);case 2:return i.a(2,Wn(r.svg,t));case 3:return i.a(2,ko(r.html,r.css,r.width,r.height,t));case 4:return i.a(2)}},a)})),Jt.apply(this,arguments)}var ze=2048,Io=(function(){function a(r,t,e){V(this,a),S(this,"cache",new Map),S(this,"pending",new Set),S(this,"atlas",{}),S(this,"glTexture",null),S(this,"dirty",!0),this.gl=r,this.renderers=t,this.scheduleRender=e,this.packCanvas=document.createElement("canvas"),this.packCanvas.width=ze,this.packCanvas.height=ze,this.packCtx=this.packCanvas.getContext("2d")}return X(a,[{key:"renderAttachment",value:function(t,e,n){var i=this,o="".concat(t,":").concat(e);if(!(this.cache.has(o)||this.pending.has(o))){var s=this.renderers[e];if(s){var l=s(n);if(l){this.pending.add(o);var d=n.pixelRatio;Promise.resolve(l).then((function(){var h=He(le().m(function u(c){var v;return le().w(function(b){for(;;)switch(b.n){case 0:if(i.pending.has(o)){b.n=1;break}return b.a(2);case 1:if(i.pending.delete(o),c){b.n=2;break}return b.a(2);case 2:return b.n=3,wo(c,d);case 3:if(v=b.v,!(!v||v.width===0||v.height===0)){b.n=4;break}return b.a(2);case 4:i.cache.set(o,{image:v,width:v.width,height:v.height}),i.dirty=!0,i.scheduleRender();case 5:return b.a(2)}},u)}));return function(u){return h.apply(this,arguments)}})())}}}}},{key:"regenerateAtlas",value:function(){if(this.dirty){this.dirty=!1;var t=[];if(this.cache.forEach(function(d,h){t.push({key:h,width:d.width,height:d.height,draw:function(c,v,b){c.drawImage(d.image,v,b)}})}),t.length===0){this.atlas={},this.deleteGLTexture();return}var e={x:0,y:0,rowHeight:0,maxRowWidth:0};this.packCtx.clearRect(0,0,ze,ze);var n=Do(t,this.packCtx,e),i=n.atlas,o=n.remaining;this.atlas=i,o.length>0&&console.warn("Sigma: ".concat(o.length," label attachment(s) could not fit in the ").concat(ze,"x").concat(ze," atlas and will not be rendered.")),this.deleteGLTexture();var s=this.gl,l=s.createTexture();s.activeTexture(s.TEXTURE0+ca),s.bindTexture(s.TEXTURE_2D,l),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!0),s.texImage2D(s.TEXTURE_2D,0,s.RGBA,s.RGBA,s.UNSIGNED_BYTE,this.packCanvas),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_MIN_FILTER,s.LINEAR),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_MAG_FILTER,s.LINEAR),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_WRAP_S,s.CLAMP_TO_EDGE),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_WRAP_T,s.CLAMP_TO_EDGE),this.glTexture=l}}},{key:"bindTexture",value:function(t){if(this.glTexture){var e=this.gl;e.activeTexture(e.TEXTURE0+t),e.bindTexture(e.TEXTURE_2D,this.glTexture)}}},{key:"getEntry",value:function(t,e){var n="".concat(t,":").concat(e);return this.atlas[n]||null}},{key:"invalidateNode",value:function(t){var e="".concat(t,":"),n=M(this.cache.keys()),i;try{for(n.s();!(i=n.n()).done;){var o=i.value;o.startsWith(e)&&(this.cache.delete(o),this.dirty=!0)}}catch(h){n.e(h)}finally{n.f()}var s=M(this.pending),l;try{for(s.s();!(l=s.n()).done;){var d=l.value;d.startsWith(e)&&this.pending.delete(d)}}catch(h){s.e(h)}finally{s.f()}}},{key:"clear",value:function(){this.cache.clear(),this.pending.clear(),this.atlas={},this.dirty=!0,this.deleteGLTexture()}},{key:"kill",value:function(){this.clear(),this.packCanvas=null,this.packCtx=null,this.gl=null}},{key:"deleteGLTexture",value:function(){this.glTexture&&(this.gl.deleteTexture(this.glTexture),this.glTexture=null)}}])})(),ja=(function(){function a(r){V(this,a),S(this,"buckets",new Map),S(this,"keyDepth",new Map);var t=M(r),e;try{for(t.s();!(e=t.n()).done;){var n=e.value;this.buckets.set(n,new Set)}}catch(i){t.e(i)}finally{t.f()}}return X(a,[{key:"has",value:function(t){return this.keyDepth.has(t)}},{key:"getBucket",value:function(t){return this.buckets.get(t)}},{key:"set",value:function(t,e){var n,i=this.keyDepth.get(t);if(i!==e){var o=this.buckets.get(e);if(!o)throw new Error('Sigma: "'.concat(e,'" is not a declared depth layer'));i!==void 0&&((n=this.buckets.get(i))===null||n===void 0||n.delete(t)),o.add(t),this.keyDepth.set(t,e)}}},{key:"remove",value:function(t){var e=this.keyDepth.get(t);e!==void 0&&(this.buckets.get(e).delete(t),this.keyDepth.delete(t))}},{key:"clearAll",value:function(){var t=M(this.buckets.values()),e;try{for(t.s();!(e=t.n()).done;){var n=e.value;n.clear()}}catch(i){t.e(i)}finally{t.f()}this.keyDepth.clear()}},{key:"getSorted",value:function(t,e){var n=this.buckets.get(t);return!n||n.size===0?[]:H(n).sort(function(i,o){return e(i)-e(o)})}}])})(),zo=(function(a){function r(t,e){return V(this,r),ee(this,r,[t,2,e])}return te(r,a),X(r,[{key:"updateNode",value:function(e,n,i,o,s){var l=arguments.length>5&&arguments[5]!==void 0?arguments[5]:0,d=arguments.length>6&&arguments[6]!==void 0?arguments[6]:0,h=this.indexMap.get(e);if(h===void 0)throw new Error('Node "'.concat(e,'" not allocated in NodeDataTexture'));var u=h*2*4;this.data[u]=n,this.data[u+1]=i,this.data[u+2]=o,this.data[u+3]=s,this.data[u+4]=l,this.data[u+5]=d,this.markDirty(h)}}])})(da),Mo=1024,No=1.5,Go=4096,Ya=(function(){function a(r,t){var e;if(V(this,a),S(this,"texture",null),S(this,"framebuffer",null),!r.getExtension("EXT_color_buffer_float"))throw new Error("sigma: EXT_color_buffer_float is required for label/edge placement but is unavailable in this WebGL2 context.");this.gl=r,this.channels=t.channels,this.capacity=this.roundUpToPowerOfTwo((e=t.initialCapacity)!==null&&e!==void 0?e:Mo);var n=this.computeDimensions(this.capacity);this.textureWidth=n.width,this.textureHeight=n.height,this.create()}return X(a,[{key:"roundUpToPowerOfTwo",value:function(t){return Math.pow(2,Math.ceil(Math.log2(Math.max(1,t))))}},{key:"computeDimensions",value:function(t){var e=Math.min(t,Go),n=Math.ceil(t/e);return{width:e,height:n}}},{key:"create",value:function(){var t=this.gl,e=this.channels===1?t.R32F:t.RGBA32F,n=this.channels===1?t.RED:t.RGBA;if(this.texture=t.createTexture(),t.activeTexture(t.TEXTURE0),t.bindTexture(t.TEXTURE_2D,this.texture),t.texImage2D(t.TEXTURE_2D,0,e,this.textureWidth,this.textureHeight,0,n,t.FLOAT,null),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MIN_FILTER,t.NEAREST),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MAG_FILTER,t.NEAREST),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_S,t.CLAMP_TO_EDGE),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_T,t.CLAMP_TO_EDGE),this.framebuffer=t.createFramebuffer(),t.bindFramebuffer(t.FRAMEBUFFER,this.framebuffer),t.framebufferTexture2D(t.FRAMEBUFFER,t.COLOR_ATTACHMENT0,t.TEXTURE_2D,this.texture,0),t.checkFramebufferStatus(t.FRAMEBUFFER)!==t.FRAMEBUFFER_COMPLETE)throw new Error("sigma: float framebuffer for frame-pass placement is incomplete.");t.bindFramebuffer(t.FRAMEBUFFER,null),t.bindTexture(t.TEXTURE_2D,null)}},{key:"ensureCapacity",value:function(t){if(!(t<=this.capacity)){var e=this.gl;this.capacity=this.roundUpToPowerOfTwo(Math.ceil(t*No));var n=this.computeDimensions(this.capacity);this.textureWidth=n.width,this.textureHeight=n.height,this.texture&&e.deleteTexture(this.texture),this.framebuffer&&e.deleteFramebuffer(this.framebuffer),this.create()}}},{key:"bindAsRenderTarget",value:function(){var t=this.gl;t.bindFramebuffer(t.FRAMEBUFFER,this.framebuffer),t.viewport(0,0,this.textureWidth,this.textureHeight)}},{key:"bind",value:function(t){var e=this.gl;e.activeTexture(e.TEXTURE0+t),e.bindTexture(e.TEXTURE_2D,this.texture)}},{key:"getTexture",value:function(){return this.texture}},{key:"getTextureWidth",value:function(){return this.textureWidth}},{key:"getTextureHeight",value:function(){return this.textureHeight}},{key:"kill",value:function(){var t=this.gl;this.texture&&(t.deleteTexture(this.texture),this.texture=null),this.framebuffer&&(t.deleteFramebuffer(this.framebuffer),this.framebuffer=null)}}])})(),Bo=(function(a){function r(t,e){return V(this,r),ee(this,r,[t,2,e])}return te(r,a),X(r,[{key:"updateEdge",value:function(e,n,i,o,s,l){var d=arguments.length>6&&arguments[6]!==void 0?arguments[6]:0,h=arguments.length>7&&arguments[7]!==void 0?arguments[7]:0,u=arguments.length>8&&arguments[8]!==void 0?arguments[8]:0,c=this.indexMap.get(e);if(c===void 0)throw new Error('Edge "'.concat(e,'" not allocated in EdgeDataTexture'));var v=c*this.TEXELS_PER_ITEM*4;this.data[v+0]=n,this.data[v+1]=i,this.data[v+2]=o,this.data[v+3]=0,this.data[v+4]=s,this.data[v+5]=l,this.data[v+6]=d,this.data[v+7]=(h&15)<<4|u&15,this.markDirty(c)}}])})(da);function Wo(a){return q(a)==="object"&&"uniforms"in a&&Array.isArray(a.uniforms)}function Uo(a){return q(a)==="object"&&"uniforms"in a&&"attributes"in a&&"glsl"in a}function Oo(a){return q(a)==="object"&&"uniforms"in a&&"attributes"in a&&"segments"in a}function Ho(a){return q(a)==="object"&&"uniforms"in a&&"attributes"in a&&"length"in a}function Vo(a){return q(a)==="object"&&"uniforms"in a&&"attributes"in a&&"glsl"in a}function Xo(a){return q(a)==="object"&&"glsl"in a&&"name"in a&&!("uniforms"in a)}function qo(a){return q(a)==="object"&&"glsl"in a&&"name"in a&&!("uniforms"in a)}function jo(a){return q(a)==="object"&&"glsl"in a&&"name"in a&&!("uniforms"in a)}function Yo(a){if(Wo(a))return a;if(Xo(a))return{name:a.name,glsl:a.glsl,inradiusFactor:a.inradiusFactor,uniforms:[]};throw new Error("Invalid node shape specification: ".concat(JSON.stringify(a)))}function Ko(a){if(Uo(a))return a;if(xr(a))return{name:a.name,glsl:a.glsl,uniforms:[],attributes:[]};throw new Error("Invalid node layer specification: ".concat(JSON.stringify(a)))}function Zo(a){if(Oo(a))return a;if(qo(a))return{name:a.name,glsl:a.glsl,segments:a.segments,uniforms:[],attributes:[]};throw new Error("Invalid edge path specification: ".concat(JSON.stringify(a)))}function $o(a){if(Vo(a))return a;if(yr(a))return{name:a.name,glsl:a.glsl,uniforms:[],attributes:[]};throw new Error("Invalid edge layer specification: ".concat(JSON.stringify(a)))}function Qo(a){if(Ho(a))return a;if(jo(a))return{name:a.name,glsl:a.glsl,length:a.length,widthFactor:a.widthFactor,margin:0,uniforms:[],attributes:[]};throw new Error("Invalid edge extremity specification: ".concat(JSON.stringify(a)))}function Jo(a){var r,t,e=(r=a?.shapes)!==null&&r!==void 0?r:Ht.shapes,n=(t=a?.layers)!==null&&t!==void 0?t:Ht.layers,i=e.map(Yo),o=n.map(Ko);if(i.length===0)throw new Error("At least one node shape must be specified.");if(o.length===0)throw new Error("At least one node layer must be specified.");return{shapes:i,layers:o}}function es(a){var r,t,e,n=(r=a?.paths)!==null&&r!==void 0?r:vt.paths,i=(t=a?.extremities)!==null&&t!==void 0?t:vt.extremities,o=(e=a?.layers)!==null&&e!==void 0?e:vt.layers,s=n.map(Zo),l=i.map(Qo).filter(function(h){return h!==null}),d=o.map($o);if(s.length===0)throw new Error("At least one edge path must be specified.");if(d.length===0)throw new Error("At least one edge layer must be specified.");return{paths:s,extremities:l,layers:d}}function ts(a,r,t,e){var n=Jo(e),i=n.shapes,o=n.layers,s=e?.variables||{},l=Bi(a,r,t,{shapes:i,layers:o,label:e?.label,backdrop:e?.backdrop,labelAttachments:e?.labelAttachments});return N(N({},l),{},{variables:s})}function as(a,r,t,e){var n=es(e),i=n.paths,o=n.extremities,s=n.layers,l={},d=M(i),h;try{for(d.s();!(h=d.n()).done;){var u=h.value;u.variables&&Object.assign(l,u.variables)}}catch(v){d.e(v)}finally{d.f()}Object.assign(l,e?.variables||{});var c=Ro(a,r,t,{paths:i,extremities:o,layers:s,defaultHead:e?.defaultHead,defaultTail:e?.defaultTail,label:e?.label});return N(N({},c),{},{variables:l,paths:i})}var ct=1.5,Ka=(function(a){function r(){var t;return V(this,r),t=ee(this,r),S(t,"x",.5),S(t,"y",.5),S(t,"angle",0),S(t,"ratio",1),S(t,"minRatio",null),S(t,"maxRatio",null),S(t,"enabledZooming",!0),S(t,"enabledPanning",!0),S(t,"enabledRotation",!0),S(t,"clean",null),S(t,"nextFrame",null),S(t,"previousState",null),S(t,"enabled",!0),S(t,"currentAnimationFrom",null),S(t,"currentAnimationTo",null),t.previousState=t.getState(),t}return te(r,a),X(r,[{key:"enable",value:function(){return this.enabled=!0,this}},{key:"disable",value:function(){return this.enabled=!1,this}},{key:"getState",value:function(){return{x:this.x,y:this.y,angle:this.angle,ratio:this.ratio}}},{key:"hasState",value:function(e){return this.x===e.x&&this.y===e.y&&this.ratio===e.ratio&&this.angle===e.angle}},{key:"getPreviousState",value:function(){var e=this.previousState;return e?{x:e.x,y:e.y,angle:e.angle,ratio:e.ratio}:null}},{key:"getBoundedRatio",value:function(e){var n=e;return typeof this.minRatio=="number"&&(n=Math.max(n,this.minRatio)),typeof this.maxRatio=="number"&&(n=Math.min(n,this.maxRatio)),n}},{key:"validateState",value:function(e){var n={};return this.enabledPanning&&typeof e.x=="number"&&(n.x=e.x),this.enabledPanning&&typeof e.y=="number"&&(n.y=e.y),this.enabledZooming&&typeof e.ratio=="number"&&(n.ratio=this.getBoundedRatio(e.ratio)),this.enabledRotation&&typeof e.angle=="number"&&(n.angle=e.angle),this.clean?this.clean(N(N({},this.getState()),n)):n}},{key:"isAnimated",value:function(){return!!this.nextFrame}},{key:"setState",value:function(e){if(!this.enabled)return this;this.previousState=this.getState();var n=this.validateState(e);return typeof n.x=="number"&&(this.x=n.x),typeof n.y=="number"&&(this.y=n.y),typeof n.ratio=="number"&&(this.ratio=n.ratio),typeof n.angle=="number"&&(this.angle=n.angle),this.hasState(this.previousState)||this.emit("updated",this.getState()),this}},{key:"updateState",value:function(e){return this.setState(e(this.getState())),this}},{key:"animate",value:function(e){var n=this,i=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},o=arguments.length>2?arguments[2]:void 0;if(!o)return new Promise(function(m){return n.animate(e,i,m)});if(this.enabled){var s=N(N({},Ur),i),l=this.validateState(e),d=vn(s.easing),h=Date.now(),u=this.getState(),c=N(N({},u),l),v=function(){var x=(Date.now()-h)/s.duration;if(x>=1){n.nextFrame=null,n.setState(l),n.emitAnimationEnd(!0),n.animationCallback&&(n.animationCallback.call(null),n.animationCallback=void 0);return}var g=d(x),f={};typeof l.x=="number"&&(f.x=u.x+(l.x-u.x)*g),typeof l.y=="number"&&(f.y=u.y+(l.y-u.y)*g),n.enabledRotation&&typeof l.angle=="number"&&(f.angle=u.angle+(l.angle-u.angle)*g),typeof l.ratio=="number"&&(f.ratio=u.ratio+(l.ratio-u.ratio)*g),n.setState(f),n.nextFrame=requestAnimationFrame(v)},b=this.nextFrame!==null;b&&(cancelAnimationFrame(this.nextFrame),this.nextFrame=null,this.emitAnimationEnd(!1),this.animationCallback&&this.animationCallback.call(null)),this.currentAnimationFrom=u,this.currentAnimationTo=c,this.animationCallback=o,this.emit("animationStart",u,c),b?this.nextFrame=requestAnimationFrame(v):v()}}},{key:"emitAnimationEnd",value:function(e){var n=this.currentAnimationFrom,i=this.currentAnimationTo;!n||!i||(this.currentAnimationFrom=null,this.currentAnimationTo=null,this.emit("animationEnd",n,i,e))}},{key:"animatedZoom",value:function(e){return e?typeof e=="number"?this.animate({ratio:this.ratio/e}):this.animate({ratio:this.ratio/(e.factor||ct)},e):this.animate({ratio:this.ratio/ct})}},{key:"animatedUnzoom",value:function(e){return e?typeof e=="number"?this.animate({ratio:this.ratio*e}):this.animate({ratio:this.ratio*(e.factor||ct)},e):this.animate({ratio:this.ratio*ct})}},{key:"animatedReset",value:function(e){return this.animate({x:.5,y:.5,ratio:1,angle:0},e)}},{key:"copy",value:function(){return r.from(this.getState())}}],[{key:"from",value:function(e){var n=new r;return n.setState(e)}}])})(ra);function se(a,r){var t=r.getBoundingClientRect();return{x:a.clientX-t.left,y:a.clientY-t.top}}function ve(a,r){var t=N(N({},se(a,r)),{},{sigmaDefaultPrevented:!1,preventSigmaDefault:function(){t.sigmaDefaultPrevented=!0},original:a});return t}function Ee(a){var r="x"in a?a:N(N({},a.touches[0]||a.previousTouches[0]),{},{original:a.original,sigmaDefaultPrevented:a.sigmaDefaultPrevented,preventSigmaDefault:function(){a.sigmaDefaultPrevented=!0,r.sigmaDefaultPrevented=!0}});return r}function ns(a,r){return N(N({},ve(a,r)),{},{delta:Un(a)})}var rs=2;function xt(a){for(var r=[],t=0,e=Math.min(a.length,rs);t<e;t++)r.push(a[t]);return r}function Ye(a,r,t){var e={touches:xt(a.touches).map(function(n){return se(n,t)}),previousTouches:r.map(function(n){return se(n,t)}),sigmaDefaultPrevented:!1,preventSigmaDefault:function(){e.sigmaDefaultPrevented=!0},original:a};return e}function Un(a){if(typeof a.deltaY<"u")return a.deltaY*-3/360;if(typeof a.detail<"u")return a.detail/-9;throw new Error("Captor: could not extract delta from event.")}var On=(function(a){function r(t,e){var n;return V(this,r),n=ee(this,r),n.container=t,n.renderer=e,n}return te(r,a),X(r)})(ra),is=["doubleClickTimeout","doubleClickZoomingDuration","doubleClickZoomingRatio","dragTimeout","draggedEventsTolerance","enableCameraMouseRotation","inertiaDuration","inertiaRatio","enableScrollBlocking","scrollBlockingReleaseThreshold","zoomDuration","zoomingRatio"],os=is.reduce(function(a,r){return N(N({},a),{},S({},r,ia[r]))},{}),ss=(function(a){function r(t,e){var n;return V(this,r),n=ee(this,r,[t,e]),S(n,"enabled",!0),S(n,"draggedEvents",0),S(n,"downStartTime",null),S(n,"lastMouseX",null),S(n,"lastMouseY",null),S(n,"isMouseDown",!1),S(n,"isMoving",!1),S(n,"isPanningStage",!1),S(n,"movingTimeout",null),S(n,"startCameraState",null),S(n,"clicks",0),S(n,"doubleClickTimeout",null),S(n,"isRightMouseDown",!1),S(n,"startRotationAngle",null),S(n,"startCameraAngle",null),S(n,"currentWheelDirection",0),S(n,"consecutiveBoundaryWheelEvents",0),S(n,"settings",os),n.handleClick=n.handleClick.bind(n),n.handleRightClick=n.handleRightClick.bind(n),n.handleDown=n.handleDown.bind(n),n.handleUp=n.handleUp.bind(n),n.handleMove=n.handleMove.bind(n),n.handleWheel=n.handleWheel.bind(n),n.handleLeave=n.handleLeave.bind(n),n.handleEnter=n.handleEnter.bind(n),t.addEventListener("click",n.handleClick,{capture:!1}),t.addEventListener("contextmenu",n.handleRightClick,{capture:!1}),t.addEventListener("mousedown",n.handleDown,{capture:!1}),t.addEventListener("wheel",n.handleWheel,{capture:!1,passive:!1}),t.addEventListener("mouseleave",n.handleLeave,{capture:!1}),t.addEventListener("mouseenter",n.handleEnter,{capture:!1}),document.addEventListener("mousemove",n.handleMove,{capture:!1}),document.addEventListener("mouseup",n.handleUp,{capture:!1}),n}return te(r,a),X(r,[{key:"kill",value:function(){var e=this.container;e.removeEventListener("click",this.handleClick),e.removeEventListener("contextmenu",this.handleRightClick),e.removeEventListener("mousedown",this.handleDown),e.removeEventListener("wheel",this.handleWheel),e.removeEventListener("mouseleave",this.handleLeave),e.removeEventListener("mouseenter",this.handleEnter),document.removeEventListener("mousemove",this.handleMove),document.removeEventListener("mouseup",this.handleUp)}},{key:"handleClick",value:function(e){var n=this;if(this.enabled){if(this.clicks++,this.clicks===2)return this.clicks=0,typeof this.doubleClickTimeout=="number"&&(clearTimeout(this.doubleClickTimeout),this.doubleClickTimeout=null),this.handleDoubleClick(e);setTimeout(function(){n.clicks=0,n.doubleClickTimeout=null},this.settings.doubleClickTimeout),this.draggedEvents<this.settings.draggedEventsTolerance&&this.emit("click",ve(e,this.container))}}},{key:"handleRightClick",value:function(e){this.enabled&&(this.settings.enableCameraMouseRotation&&e.preventDefault(),this.emit("rightClick",ve(e,this.container)))}},{key:"handleDoubleClick",value:function(e){if(this.enabled){e.preventDefault(),e.stopPropagation();var n=ve(e,this.container);if(this.emit("doubleClick",n),!n.sigmaDefaultPrevented){var i=this.renderer.getCamera(),o=i.getBoundedRatio(i.getState().ratio/this.settings.doubleClickZoomingRatio);i.animate(this.renderer.getViewportZoomedState(se(e,this.container),o),{easing:"quadraticInOut",duration:this.settings.doubleClickZoomingDuration})}}}},{key:"handleDown",value:function(e){if(this.enabled){if(e.button===0){this.startCameraState=this.renderer.getCamera().getState();var n=se(e,this.container),i=n.x,o=n.y;this.lastMouseX=i,this.lastMouseY=o,this.draggedEvents=0,this.downStartTime=Date.now(),this.isMouseDown=!0}if(e.button===2&&this.settings.enableCameraMouseRotation){var s=se(e,this.container),l=s.x,d=s.y,h=this.container.offsetWidth/2,u=this.container.offsetHeight/2;this.startRotationAngle=Math.atan2(d-u,l-h),this.startCameraAngle=this.renderer.getCamera().getState().angle,this.isRightMouseDown=!0}this.emit("mousedown",ve(e,this.container))}}},{key:"handleUp",value:function(e){var n=this;if(!(!this.enabled||!this.isMouseDown&&!this.isRightMouseDown)){if(this.isRightMouseDown){this.isRightMouseDown=!1,this.startRotationAngle=null,this.startCameraAngle=null,this.emit("mouseup",ve(e,this.container));return}var i=this.renderer.getCamera();this.isMouseDown=!1,this.isPanningStage&&(this.isPanningStage=!1,this.renderer._setPanning(!1)),typeof this.movingTimeout=="number"&&(clearTimeout(this.movingTimeout),this.movingTimeout=null);var o=se(e,this.container),s=o.x,l=o.y,d=i.getState(),h=i.getPreviousState()||{x:0,y:0};this.isMoving?i.animate({x:d.x+this.settings.inertiaRatio*(d.x-h.x),y:d.y+this.settings.inertiaRatio*(d.y-h.y)},{duration:this.settings.inertiaDuration,easing:"quadraticOut"}):(this.lastMouseX!==s||this.lastMouseY!==l)&&i.setState({x:d.x,y:d.y}),this.isMoving=!1,setTimeout(function(){var u=n.draggedEvents>0;n.draggedEvents=0,u&&n.renderer.getSetting("hideEdgesOnMove")&&n.renderer.refresh()},0),this.emit("mouseup",ve(e,this.container))}}},{key:"handleMove",value:function(e){var n=this;if(this.enabled){var i=ve(e,this.container);if(this.emit("mousemovebody",i),(e.target===this.container||e.composedPath()[0]===this.container)&&this.emit("mousemove",i),this.isMouseDown&&this.draggedEvents++,!i.sigmaDefaultPrevented){if(this.isMouseDown){this.isMoving=!0,typeof this.movingTimeout=="number"&&clearTimeout(this.movingTimeout),this.movingTimeout=window.setTimeout(function(){n.movingTimeout=null,n.isMoving=!1},this.settings.dragTimeout);var o=this.renderer.getCamera(),s=se(e,this.container),l=s.x,d=s.y,h=this.renderer.viewportToFramedGraph({x:this.lastMouseX,y:this.lastMouseY}),u=this.renderer.viewportToFramedGraph({x:l,y:d}),c=h.x-u.x,v=h.y-u.y,b=o.getState(),m=b.x+c,x=b.y+v;this.isPanningStage||(this.isPanningStage=!0,this.renderer._setPanning(!0)),o.setState({x:m,y:x}),this.lastMouseX=l,this.lastMouseY=d,e.preventDefault(),e.stopPropagation()}if(this.isRightMouseDown){var g=se(e,this.container),f=g.x,p=g.y,y=this.container.offsetWidth/2,T=this.container.offsetHeight/2,_=Math.atan2(p-T,f-y),E=_-this.startRotationAngle,A=this.renderer.getCamera();A.setState({angle:this.startCameraAngle+E}),e.preventDefault(),e.stopPropagation()}}}}},{key:"handleLeave",value:function(e){this.emit("mouseleave",ve(e,this.container))}},{key:"handleEnter",value:function(e){this.emit("mouseenter",ve(e,this.container))}},{key:"handleWheel",value:function(e){var n=this,i=this.renderer.getCamera();if(!(!this.enabled||!i.enabledZooming)){var o=Un(e);if(o){var s=ns(e,this.container);if(this.emit("wheel",s),s.sigmaDefaultPrevented){e.preventDefault(),e.stopPropagation();return}var l=this.settings,d=l.enableScrollBlocking,h=l.scrollBlockingReleaseThreshold,u=i.getState().ratio,c=o>0?1/this.settings.zoomingRatio:this.settings.zoomingRatio,v=i.getBoundedRatio(u*c),b=o>0?1:-1,m=Date.now(),x=u===v;x?this.consecutiveBoundaryWheelEvents++:this.consecutiveBoundaryWheelEvents=0;var g=d&&(!x||this.consecutiveBoundaryWheelEvents<=h);g&&(e.preventDefault(),e.stopPropagation()),!x&&(this.currentWheelDirection===b&&this.lastWheelTriggerTime&&m-this.lastWheelTriggerTime<this.settings.zoomDuration/5||(i.animate(this.renderer.getViewportZoomedState(se(e,this.container),v),{easing:"quadraticOut",duration:this.settings.zoomDuration},function(){n.currentWheelDirection=0}),this.currentWheelDirection=b,this.lastWheelTriggerTime=m))}}}},{key:"setSettings",value:function(e){this.settings=e}}])})(On),ls=["dragTimeout","inertiaDuration","inertiaRatio","doubleClickTimeout","doubleClickZoomingRatio","doubleClickZoomingDuration","tapMoveTolerance"],ds=ls.reduce(function(a,r){return N(N({},a),{},S({},r,ia[r]))},{}),us=(function(a){function r(t,e){var n;return V(this,r),n=ee(this,r,[t,e]),S(n,"enabled",!0),S(n,"isMoving",!1),S(n,"hasMoved",!1),S(n,"isPanningStage",!1),S(n,"isZoomingStage",!1),S(n,"touchMode",0),S(n,"startTouchesPositions",[]),S(n,"lastTouches",[]),S(n,"lastTap",null),S(n,"settings",ds),n.handleStart=n.handleStart.bind(n),n.handleLeave=n.handleLeave.bind(n),n.handleMove=n.handleMove.bind(n),t.addEventListener("touchstart",n.handleStart,{capture:!1}),t.addEventListener("touchcancel",n.handleLeave,{capture:!1}),document.addEventListener("touchend",n.handleLeave,{capture:!1,passive:!1}),document.addEventListener("touchmove",n.handleMove,{capture:!1,passive:!1}),n}return te(r,a),X(r,[{key:"kill",value:function(){var e=this.container;e.removeEventListener("touchstart",this.handleStart),e.removeEventListener("touchcancel",this.handleLeave),document.removeEventListener("touchend",this.handleLeave),document.removeEventListener("touchmove",this.handleMove)}},{key:"getDimensions",value:function(){return{width:this.container.offsetWidth,height:this.container.offsetHeight}}},{key:"syncStageFlags",value:function(){var e=this.touchMode===1&&this.hasMoved,n=this.touchMode===2;e!==this.isPanningStage&&(this.isPanningStage=e,this.renderer._setPanning(e)),n!==this.isZoomingStage&&(this.isZoomingStage=n,this.renderer._setZooming(n))}},{key:"handleStart",value:function(e){var n=this;if(this.enabled){e.preventDefault();var i=xt(e.touches);if(this.touchMode=i.length,this.startCameraState=this.renderer.getCamera().getState(),this.startTouchesPositions=i.map(function(v){return se(v,n.container)}),this.touchMode===2){var o=Q(this.startTouchesPositions,2),s=o[0],l=s.x,d=s.y,h=o[1],u=h.x,c=h.y;this.startTouchesAngle=Math.atan2(c-d,u-l),this.startTouchesDistance=Math.sqrt(Math.pow(u-l,2)+Math.pow(c-d,2))}this.syncStageFlags(),this.emit("touchdown",Ye(e,this.lastTouches,this.container)),this.lastTouches=i,this.lastTouchesPositions=this.startTouchesPositions}}},{key:"handleLeave",value:function(e){if(!(!this.enabled||!this.startTouchesPositions.length)){switch(e.cancelable&&e.preventDefault(),this.movingTimeout&&(this.isMoving=!1,clearTimeout(this.movingTimeout)),this.touchMode){case 2:if(e.touches.length===1){this.handleStart(e),e.preventDefault();break}case 1:if(this.isMoving){var n=this.renderer.getCamera(),i=n.getState(),o=n.getPreviousState()||{x:0,y:0};n.animate({x:i.x+this.settings.inertiaRatio*(i.x-o.x),y:i.y+this.settings.inertiaRatio*(i.y-o.y)},{duration:this.settings.inertiaDuration,easing:"quadraticOut"})}this.hasMoved=!1,this.isMoving=!1,this.touchMode=0;break}if(this.syncStageFlags(),this.emit("touchup",Ye(e,this.lastTouches,this.container)),!e.touches.length){var s=se(this.lastTouches[0],this.container),l=this.startTouchesPositions[0],d=Math.pow(s.x-l.x,2)+Math.pow(s.y-l.y,2);if(!e.touches.length&&d<Math.pow(this.settings.tapMoveTolerance,2))if(this.lastTap&&Date.now()-this.lastTap.time<this.settings.doubleClickTimeout){var h=Ye(e,this.lastTouches,this.container);if(this.emit("doubletap",h),this.lastTap=null,!h.sigmaDefaultPrevented){var u=this.renderer.getCamera(),c=u.getBoundedRatio(u.getState().ratio/this.settings.doubleClickZoomingRatio);u.animate(this.renderer.getViewportZoomedState(s,c),{easing:"quadraticInOut",duration:this.settings.doubleClickZoomingDuration})}}else{var v=Ye(e,this.lastTouches,this.container);this.emit("tap",v),this.lastTap={time:Date.now(),position:v.touches[0]||v.previousTouches[0]}}}this.lastTouches=xt(e.touches),this.startTouchesPositions=[]}}},{key:"handleMove",value:function(e){var n=this;if(!(!this.enabled||!this.startTouchesPositions.length)){e.preventDefault();var i=xt(e.touches),o=i.map(function(O){return se(O,n.container)}),s=this.lastTouches;this.lastTouches=i,this.lastTouchesPositions=o;var l=Ye(e,s,this.container);if(this.emit("touchmove",l),!l.sigmaDefaultPrevented&&(this.hasMoved||(this.hasMoved=o.some(function(O,W){var U=n.startTouchesPositions[W];return U&&(O.x!==U.x||O.y!==U.y)})),!!this.hasMoved)){this.isMoving=!0,this.syncStageFlags(),this.movingTimeout&&clearTimeout(this.movingTimeout),this.movingTimeout=window.setTimeout(function(){n.isMoving=!1},this.settings.dragTimeout);var d=this.renderer.getCamera(),h=this.startCameraState,u=this.renderer.getSetting("stagePadding");switch(this.touchMode){case 1:{var c=this.renderer.viewportToFramedGraph((this.startTouchesPositions||[])[0]),v=c.x,b=c.y,m=this.renderer.viewportToFramedGraph(o[0]),x=m.x,g=m.y;d.setState({x:h.x+v-x,y:h.y+b-g});break}case 2:{var f={x:.5,y:.5,angle:0,ratio:1},p=o[0],y=p.x,T=p.y,_=o[1],E=_.x,A=_.y,R=Math.atan2(A-T,E-y)-this.startTouchesAngle,L=Math.hypot(A-T,E-y)/this.startTouchesDistance,F=d.getBoundedRatio(h.ratio/L);f.ratio=F,f.angle=h.angle+R;var C=this.getDimensions(),P=this.renderer.viewportToFramedGraph((this.startTouchesPositions||[])[0],{cameraState:h}),D=Math.min(C.width,C.height)-2*u,k=D/C.width,w=D/C.height,I=F/D,G=y-D/2/k,z=T-D/2/w,B=_n({x:G,y:z},f.angle);G=B.x,z=B.y,f.x=P.x-G*I,f.y=P.y+z*I,d.setState(f);break}}}}}},{key:"setSettings",value:function(e){this.settings=e}}])})(On),hs=(function(){function a(r,t,e,n){V(this,a),S(this,"pendingNode",null),S(this,"session",null),this.graph=r,this.viewportToGraph=t,this.setNodesState=e,this.emit=n}return X(a,[{key:"start",value:function(t,e,n,i,o){var s=n(t),l=!1;if(this.emit("nodeDragStart",{node:t,allDraggedNodes:s,event:e,preventSigmaDefault:function(){l=!0}}),l)return!1;var d=new Map,h=M(s),u;try{for(h.s();!(u=h.n()).done;){var c=u.value;d.set(c,{x:this.graph.getNodeAttribute(c,i),y:this.graph.getNodeAttribute(c,o)})}}catch(v){h.e(v)}finally{h.f()}return this.session={node:t,allNodes:s,startPosition:this.viewportToGraph(e),startNodePositions:d,xAttr:i,yAttr:o},this.setNodesState(s,{isDragged:!0}),!0}},{key:"applyMove",value:function(t,e){var n=this.session,i=n.allNodes,o=n.startNodePositions,s=n.startPosition,l=n.xAttr,d=n.yAttr,h=this.viewportToGraph(t),u={x:h.x-s.x,y:h.y-s.y},c=M(i),v;try{for(c.s();!(v=c.n()).done;){var b=v.value,m=o.get(b);if(!(!m||!this.graph.hasNode(b))){var x={x:m.x+u.x,y:m.y+u.y};e?this.graph.mergeNodeAttributes(b,e(x,b)):(this.graph.setNodeAttribute(b,l,x.x),this.graph.setNodeAttribute(b,d,x.y))}}}catch(g){c.e(g)}finally{c.f()}}},{key:"end",value:function(){if(this.pendingNode=null,!this.session)return null;var t=this.session,e=t.node,n=t.allNodes;return this.setNodesState(n,{isDragged:!1}),this.session=null,{node:e,allNodes:n}}},{key:"removeNode",value:function(t){t===this.pendingNode&&(this.pendingNode=null),this.session&&(this.session.node===t?(this.setNodesState(this.session.allNodes,{isDragged:!1}),this.session=null):this.session.allNodes.includes(t)&&(this.session.allNodes=this.session.allNodes.filter(function(e){return e!==t}),this.session.startNodePositions.delete(t)))}},{key:"clear",value:function(){this.pendingNode=null,this.session=null}}])})(),cs=(function(){function a(r,t){V(this,a),S(this,"groups",new Map),S(this,"edgeToGroupKey",new Map),this.graph=r,this.onGroupChanged=t}return X(a,[{key:"getGroupKey",value:function(t){var e=this.graph.source(t),n=this.graph.target(t);return e<n?"".concat(e,"\0").concat(n):"".concat(n,"\0").concat(e)}},{key:"sortGroup",value:function(t,e){var n=this,i=e.split("\0")[0];t.sort(function(o,s){var l=n.graph.source(o)===i||!n.graph.isDirected(o)?0:1,d=n.graph.source(s)===i||!n.graph.isDirected(s)?0:1;return l-d})}},{key:"register",value:function(t){var e=this.getGroupKey(t),n=this.groups.get(e);n||(n=[],this.groups.set(e,n)),n.includes(t)||n.push(t),this.edgeToGroupKey.set(t,e),this.sortGroup(n,e),this.onGroupChanged(n,n.length)}},{key:"unregister",value:function(t){var e=this.edgeToGroupKey.get(t);if(e){this.edgeToGroupKey.delete(t);var n=this.groups.get(e);if(n){var i=n.indexOf(t);i!==-1&&n.splice(i,1),n.length===0?this.groups.delete(e):this.onGroupChanged(n,n.length)}}}},{key:"getGroup",value:function(t){var e,n=this.edgeToGroupKey.get(t);return n?(e=this.groups.get(n))!==null&&e!==void 0?e:[]:[]}},{key:"getSiblings",value:function(t){return this.getGroup(t).filter(function(e){return e!==t})}},{key:"rebuild",value:function(){var t=this;this.groups.clear(),this.edgeToGroupKey.clear(),this.graph.forEachEdge(function(l){var d=t.getGroupKey(l),h=t.groups.get(d);h||(h=[],t.groups.set(d,h)),h.push(l),t.edgeToGroupKey.set(l,d)});var e=M(this.groups),n;try{for(e.s();!(n=e.n()).done;){var i=Q(n.value,2),o=i[0],s=i[1];this.sortGroup(s,o),this.onGroupChanged(s,s.length)}}catch(l){e.e(l)}finally{e.f()}}},{key:"clear",value:function(){this.groups.clear(),this.edgeToGroupKey.clear()}}])})();function Za(a,r){var t;if(a===!1||a==="extend"||a==="separate")return a;var e=a[r];return e!==void 0?e:(t=a.default)!==null&&t!==void 0?t:!1}function $a(a){return a===!1?!1:a==="extend"||a==="separate"?!0:Object.values(a).some(function(r){return r==="extend"||r==="separate"})}function Qa(a){return a==="separate"?!0:a===!1||a==="extend"?!1:a.default==="separate"?!0:Object.values(a).includes("separate")}var re={node:{parent:null,eventSuffix:"Node",payloadKey:"node",isEnabled:function(){return!0},writesPickingThisFrame:function(){return!0},setHover:function(r,t,e){return r.setNodeState(t,{isHovered:e})},getCursor:function(r,t){var e;return(e=r.nodeDataCache[t])===null||e===void 0?void 0:e.cursor},isHitValid:function(r,t){var e;return((e=r.nodeDataCache[t])===null||e===void 0?void 0:e.visibility)!=="hidden"}},edge:{parent:null,eventSuffix:"Edge",payloadKey:"edge",isEnabled:function(r){return!!r.settings.enableEdgeEvents},writesPickingThisFrame:function(r){return!!r.settings.enableEdgeEvents},setHover:function(r,t,e){return r.setEdgeState(t,{isHovered:e})},getCursor:function(r,t){var e;return(e=r.edgeDataCache[t])===null||e===void 0?void 0:e.cursor}},nodeLabel:{parent:"node",eventSuffix:"NodeLabel",payloadKey:"node",isEnabled:function(r){return Qa(r.settings.nodeLabelEvents)},writesPickingThisFrame:function(r){return $a(r.settings.nodeLabelEvents)},setHover:function(r,t,e){return r.setNodeState(t,{isLabelHovered:e})},getCursor:function(r,t){var e;return(e=r.nodeDataCache[t])===null||e===void 0?void 0:e.labelCursor},resolveForVerb:function(r,t,e){var n=Za(e.settings.nodeLabelEvents,t);return n===!1?null:n==="extend"?{kind:"node",key:r.key}:r}},edgeLabel:{parent:"edge",eventSuffix:"EdgeLabel",payloadKey:"edge",isEnabled:function(r){return Qa(r.settings.edgeLabelEvents)},writesPickingThisFrame:function(r){return $a(r.settings.edgeLabelEvents)},setHover:function(r,t,e){return r.setEdgeState(t,{isLabelHovered:e})},getCursor:function(r,t){var e;return(e=r.edgeDataCache[t])===null||e===void 0?void 0:e.labelCursor},resolveForVerb:function(r,t,e){var n=Za(e.settings.edgeLabelEvents,t);return n===!1?null:n==="extend"?{kind:"edge",key:r.key}:r}}},_t=["node","edge","nodeLabel","edgeLabel"];function fs(){return{lookup:[null],idsByKind:{node:new Map,edge:new Map,nodeLabel:new Map,edgeLabel:new Map},nextId:1}}function Le(a,r,t){var e;return(e=a.idsByKind[r].get(t))!==null&&e!==void 0?e:0}function Gt(a,r){var t=M(_t),e;try{for(t.s();!(e=t.n()).done;){var n=e.value;if(n===r||re[n].parent===r){var i=M(a.idsByKind[n].values()),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;a.lookup[s]=null}}catch(c){i.e(c)}finally{i.f()}a.idsByKind[n]=new Map}}}catch(c){t.e(c)}finally{t.f()}var l=1,d=M(_t),h;try{for(d.s();!(h=d.n()).done;){var u=h.value;if(u===r)break;l+=a.idsByKind[u].size}}catch(c){d.e(c)}finally{d.f()}a.nextId=l}function Ja(a,r,t){var e=a.nextId++;return a.idsByKind[r].set(t,e),a.lookup[e]={kind:r,key:t},e}function gs(a,r){var t=M(_t),e;try{for(t.s();!(e=t.n()).done;){var n=e.value,i=re[n];if(i.parent!==null){var o=M(a.idsByKind[n].values()),s;try{for(o.s();!(s=o.n()).done;){var l=s.value;a.lookup[l]=null}}catch(c){o.e(c)}finally{o.f()}if(a.idsByKind[n]=new Map,!!i.isEnabled(r)){var d=M(a.idsByKind[i.parent].keys()),h;try{for(d.s();!(h=d.n()).done;){var u=h.value;a.idsByKind[n].set(u,a.nextId),a.lookup[a.nextId]={kind:n,key:u},a.nextId++}}catch(c){d.e(c)}finally{d.f()}}}}}catch(c){t.e(c)}finally{t.f()}}function Bt(a,r,t){re[r.kind].setHover(a,r.key,t)}function vs(a,r){return re[r.kind].getCursor(a,r.key)}function Me(a,r){return"".concat(r).concat(re[a].eventSuffix)}function Ne(a,r){return N(N({},r),{},S({},re[a.kind].payloadKey,a.key))}function ms(a,r,t){var e=re[r.kind].resolveForVerb;return e?e(r,t,a):r}function ps(a,r){var t=re[r.kind].isHitValid;return t?t(a,r.key):!0}function Wt(a){return _t.filter(function(r){return r===a||re[r].parent===a})}function ft(a,r,t){var e=a.getHitAtPosition(r);return e&&(e=ms(a,e,t)),e&&!ps(a,e)&&(e=null),e}function bs(a,r){return!a||!r?a===r:a.kind===r.kind&&a.key===r.key}function xs(a,r,t,e){e.handleResize=function(){return a.scheduleRefresh()},window.addEventListener("resize",e.handleResize),e.handleMove=function(i){var o=Ee(i),s={event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}},l=a.stateManager,d=ft(a,o,"enter"),h=l.hovered;bs(h,d)||(h&&(Bt(a,h,!1),a.emit(Me(h.kind,"leave"),Ne(h,s))),l.setHovered(d),d&&(Bt(a,d,!0),a.emit(Me(d.kind,"enter"),Ne(d,s))),a.updateContainerCursor())},e.handleMoveBody=function(i){var o=Ee(i),s=a.dragManager;if(s.pendingNode&&!s.session){var l=a.nodeStyleAnalysis,d=l.xAttribute,h=l.yAttribute,u=a.settings;s.start(s.pendingNode,o,u.getDraggedNodes,d||"x",h||"y"),s.pendingNode=null}s.session&&(s.applyMove(o,a.settings.dragPositionToAttributes),a.emit("nodeDrag",{node:s.session.node,allDraggedNodes:s.session.allNodes,event:o}),o.preventSigmaDefault()),a.emit("moveBody",{event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}})},e.handleLeave=function(i){var o=Ee(i),s={event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}},l=a.stateManager,d=l.hovered;d&&(l.setHovered(null),Bt(a,d,!1),a.emit(Me(d.kind,"leave"),Ne(d,s)),a.updateContainerCursor()),a.emit("leaveStage",s)},e.handleEnter=function(i){var o=Ee(i);a.emit("enterStage",{event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}})};var n=function(o){return function(s){var l=Ee(s),d={event:l,preventSigmaDefault:function(){return l.preventSigmaDefault()}},h=ft(a,l,o);if(h){a.emit(Me(h.kind,o),Ne(h,d));return}a.emit("".concat(o,"Stage"),d)}};e.handleClick=n("click"),e.handleRightClick=n("rightClick"),e.handleDoubleClick=n("doubleClick"),e.handleWheel=n("wheel"),e.handleDown=function(i){var o=Ee(i),s={event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}},l=ft(a,o,"down");if(l){l.kind==="node"&&a.settings.enableNodeDrag&&(a.dragManager.pendingNode=l.key),a.emit(Me(l.kind,"down"),Ne(l,s));return}a.emit("downStage",s)},e.handleUp=function(i){var o=Ee(i),s={event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}},l=a.dragManager.end();l&&a.emit("nodeDragEnd",N({node:l.node,allDraggedNodes:l.allNodes},s));var d=ft(a,o,"up");if(d){a.emit(Me(d.kind,"up"),Ne(d,s));return}a.emit("upStage",s)},r.on("mousemove",e.handleMove),r.on("mousemovebody",e.handleMoveBody),r.on("click",e.handleClick),r.on("rightClick",e.handleRightClick),r.on("doubleClick",e.handleDoubleClick),r.on("wheel",e.handleWheel),r.on("mousedown",e.handleDown),r.on("mouseup",e.handleUp),r.on("mouseleave",e.handleLeave),r.on("mouseenter",e.handleEnter),t.on("touchdown",e.handleDown),t.on("touchdown",e.handleMove),t.on("touchup",e.handleUp),t.on("touchmove",e.handleMove),t.on("tap",e.handleClick),t.on("doubletap",e.handleDoubleClick),t.on("touchmove",e.handleMoveBody)}function ys(a,r){var t=a.graph,e=new Set(["x","y","zIndex","type"]);r.eachNodeAttributesUpdatedGraphUpdate=function(n){var i,o=(i=n.hints)===null||i===void 0?void 0:i.attributes,s=!o||o.some(function(l){return e.has(l)});a.refresh({partialGraph:{nodes:t.nodes()},skipIndexation:!s,schedule:!0})},r.eachEdgeAttributesUpdatedGraphUpdate=function(n){var i,o=(i=n.hints)===null||i===void 0?void 0:i.attributes,s=o&&["zIndex","type"].some(function(l){return o?.includes(l)});a.refresh({partialGraph:{edges:t.edges()},skipIndexation:!s,schedule:!0})},r.addNodeGraphUpdate=function(n){a.addNode(n.key),a.refresh({partialGraph:{nodes:[n.key]},skipIndexation:!1,schedule:!0})},r.updateNodeGraphUpdate=function(n){a.refresh({partialGraph:{nodes:[n.key]},skipIndexation:!1,schedule:!0})},r.dropNodeGraphUpdate=function(n){a.removeNode(n.key),a.refresh({schedule:!0})},r.addEdgeGraphUpdate=function(n){var i=n.key;a.edgeGroups.register(i),a.addEdge(i);var o=a.edgeGroups.getSiblings(i),s=M(o),l;try{for(s.s();!(l=s.n()).done;){var d=l.value;a.addEdge(d)}}catch(h){s.e(h)}finally{s.f()}a.refresh({partialGraph:{edges:[i].concat(H(o))},schedule:!0})},r.updateEdgeGraphUpdate=function(n){a.refresh({partialGraph:{edges:[n.key]},skipIndexation:!1,schedule:!0})},r.dropEdgeGraphUpdate=function(n){var i=n.key,o=a.edgeGroups.getSiblings(i);a.edgeGroups.unregister(i),a.removeEdge(i);var s=M(o),l;try{for(s.s();!(l=s.n()).done;){var d=l.value;a.addEdge(d)}}catch(h){s.e(h)}finally{s.f()}a.refresh({schedule:!0})},r.clearEdgesGraphUpdate=function(){a.clearEdgeState(),a.clearEdgeIndices(),a.refresh({schedule:!0})},r.clearGraphUpdate=function(){a.clearEdgeState(),a.clearNodeState(),a.clearEdgeIndices(),a.clearNodeIndices(),a.refresh({schedule:!0})},t.on("nodeAdded",r.addNodeGraphUpdate),t.on("nodeDropped",r.dropNodeGraphUpdate),t.on("nodeAttributesUpdated",r.updateNodeGraphUpdate),t.on("eachNodeAttributesUpdated",r.eachNodeAttributesUpdatedGraphUpdate),t.on("edgeAdded",r.addEdgeGraphUpdate),t.on("edgeDropped",r.dropEdgeGraphUpdate),t.on("edgeAttributesUpdated",r.updateEdgeGraphUpdate),t.on("eachEdgeAttributesUpdated",r.eachEdgeAttributesUpdatedGraphUpdate),t.on("edgesCleared",r.clearEdgesGraphUpdate),t.on("cleared",r.clearGraphUpdate)}function Ts(a,r){a.removeListener("nodeAdded",r.addNodeGraphUpdate),a.removeListener("nodeDropped",r.dropNodeGraphUpdate),a.removeListener("nodeAttributesUpdated",r.updateNodeGraphUpdate),a.removeListener("eachNodeAttributesUpdated",r.eachNodeAttributesUpdatedGraphUpdate),a.removeListener("edgeAdded",r.addEdgeGraphUpdate),a.removeListener("edgeDropped",r.dropEdgeGraphUpdate),a.removeListener("edgeAttributesUpdated",r.updateEdgeGraphUpdate),a.removeListener("eachEdgeAttributesUpdated",r.eachEdgeAttributesUpdatedGraphUpdate),a.removeListener("edgesCleared",r.clearEdgesGraphUpdate),a.removeListener("cleared",r.clearGraphUpdate)}var _s={x:.5,y:.5,angle:0,ratio:1},Ss=8,Es=.001;function Rs(a){var r=a.coords,t=a.nodeData,e=a.dimensions,n=a.stagePadding,i=a.zoomToSizeRatioFunction,o=a.itemSizesReference,s=a.fitLabels,l=a.nodeLabelBox,d=Object.keys(r);if(!d.length)return a.extent;for(var h=i(1)||1,u=o==="positions",c=e.width,v=e.height,b=a.extent,m=0;m<Ss;m++){for(var x=jt(b),g={width:b.x[1]-b.x[0]||1,height:b.y[1]-b.y[0]||1},f=Ae(_s,e,g,n),p=en(f,x({x:0,y:0}),c,v),y=en(f,x({x:1,y:0}),c,v),T=Math.hypot(y.x-p.x,y.y-p.y)||1,_=1/0,E=-1/0,A=1/0,R=-1/0,L=0,F=d.length;L<F;L++){var C=d[L],P=t[C],D=P.size/h*(u?T:1),k=-D,w=D,I=-D,G=D;if(s){var z=l(P,D);z&&(z.minX<k&&(k=z.minX),z.maxX>w&&(w=z.maxX),z.minY<I&&(I=z.minY),z.maxY>G&&(G=z.maxY))}var B=r[C],O=B.x,W=B.y;_=Math.min(_,O+k/T),E=Math.max(E,O+w/T),A=Math.min(A,W-G/T),R=Math.max(R,W-I/T)}var U={x:[_,E],y:[A,R]},K=Math.max(U.x[1]-U.x[0],U.y[1]-U.y[0])||1,Z=Math.max(Math.abs(U.x[0]-b.x[0]),Math.abs(U.x[1]-b.x[1]),Math.abs(U.y[0]-b.y[0]),Math.abs(U.y[1]-b.y[1]));if(b=U,Z/K<Es)break}return b}function en(a,r,t,e){var n=Je(a,r);return{x:(1+n.x)*t/2,y:(1-n.y)*e/2}}var tn=(function(){function a(r,t){V(this,a),this.key=r,this.size=t}return X(a,null,[{key:"compare",value:function(t,e){return t.size>e.size?-1:t.size<e.size||t.key>e.key?1:-1}}])})(),an=(function(){function a(){V(this,a),S(this,"width",0),S(this,"height",0),S(this,"cellSize",0),S(this,"columns",0),S(this,"rows",0),S(this,"cells",{})}return X(a,[{key:"resizeAndClear",value:function(t,e){this.width=t.width,this.height=t.height,this.cellSize=e,this.columns=Math.ceil(t.width/e),this.rows=Math.ceil(t.height/e),this.cells={}}},{key:"getIndex",value:function(t){var e=Math.floor(t.x/this.cellSize),n=Math.floor(t.y/this.cellSize);return n*this.columns+e}},{key:"add",value:function(t,e,n){var i=new tn(t,e),o=this.getIndex(n),s=this.cells[o];s||(s=[],this.cells[o]=s),s.push(i)}},{key:"organize",value:function(){for(var t in this.cells){var e=this.cells[t];e.sort(tn.compare)}}},{key:"getLabelsToDisplay",value:function(t,e,n){var i=this.cellSize*this.cellSize,o=i/t/t,s=o*e/i,l=Math.ceil(s),d=[];if(n)for(var h=Math.max(0,Math.floor(n.x1/this.cellSize)),u=Math.min(this.columns-1,Math.floor(n.x2/this.cellSize)),c=Math.max(0,Math.floor(n.y1/this.cellSize)),v=Math.min(this.rows-1,Math.floor(n.y2/this.cellSize)),b=c;b<=v;b++)for(var m=h;m<=u;m++){var x=b*this.columns+m,g=this.cells[x];if(g)for(var f=0;f<Math.min(l,g.length);f++)d.push(g[f].key)}else for(var p in this.cells)for(var y=this.cells[p],T=0;T<Math.min(l,y.length);T++)d.push(y[T].key);return d}}])})();function As(a){var r=a.graph,t=a.hoveredNode,e=a.highlightedNodes,n=a.displayedNodeLabels,i=[];return r.forEachEdge(function(o,s,l,d){(l===t||d===t||e.has(l)||e.has(d)||n.has(l)&&n.has(d))&&i.push(o)}),i}var Ge=150,Be=50,Ds={both:0,node:1,label:2},Cs={over:0,above:1,below:2,auto:3},nn=12,Ls=3,Ps=(function(){function a(r){V(this,a),S(this,"labelGrid",new an),S(this,"displayedNodeLabels",new Set),S(this,"displayedEdgeLabels",new Set),S(this,"edgeLabelCandidates",[]),S(this,"renderedNodeLabels",new Set),S(this,"labelSizeCache",new Map),S(this,"framePassPoints",new Float32Array(0)),this.internals=r}return X(a,[{key:"resetFrame",value:function(){this.displayedNodeLabels=new Set,this.renderedNodeLabels=new Set,this.labelSizeCache.clear()}},{key:"clearEdgeLabels",value:function(){this.displayedEdgeLabels=new Set}},{key:"resetLabelGrid",value:function(){this.labelGrid=new an}},{key:"processWebGLLabels",value:function(t){for(var e,n=this.internals,i=n.labelProgram,o=n.primitives,s=n.nodeDataCache,l=(o==null||(e=o.nodes)===null||e===void 0||(e=e.label)===null||e===void 0||(e=e.font)===null||e===void 0?void 0:e.family)||"sans-serif",d=new Map,h=0,u=t.length;h<u;h++){var c=t[h],v=s[c];if(!(v.visibility==="hidden"||!v.label)){var b=v.labelFont||l,m=d.get(b);m?m.push(v.label):d.set(b,[v.label])}}var x=M(d),g;try{for(x.s();!(g=x.n()).done;){var f=Q(g.value,2),p=f[0],y=f[1],T=Mt(p),_=T.family,E=T.weight,A=T.style,R=i.registerFont(_,E,A);i.ensureGlyphsReady(y,R)}}catch(L){x.e(L)}finally{x.f()}}},{key:"measureNodeLabel",value:function(t){var e,n;if(!t.label)return{width:0,height:0,textHeight:0};var i=this.internals,o=i.labelProgram,s=i.primitives,l=(e=t.labelSize)!==null&&e!==void 0?e:14,d=t.labelFont||(s==null||(n=s.nodes)===null||n===void 0||(n=n.label)===null||n===void 0||(n=n.font)===null||n===void 0?void 0:n.family)||"sans-serif",h="".concat(t.label,"|").concat(l,"|").concat(d);if(this.labelSizeCache.has(h))return this.labelSizeCache.get(h);var u=Mt(d),c=u.family,v=u.weight,b=u.style,m=o.registerFont(c,v,b),x=o.measureLabel(t.label,l,m);return this.labelSizeCache.set(h,x),x}},{key:"nodeLabelBox",value:function(t,e){var n,i,o,s,l;if(t.visibility==="hidden"||t.labelVisibility==="hidden")return null;var d=this.measureNodeLabel(t),h=d.width,u=d.height,c=d.textHeight;if(!h)return null;var v=(n=(i=this.internals.primitives)===null||i===void 0||(i=i.nodes)===null||i===void 0||(i=i.label)===null||i===void 0?void 0:i.margin)!==null&&n!==void 0?n:et,b=e+v,m=t.labelBackgroundColor?(o=t.labelBackgroundPadding)!==null&&o!==void 0?o:Ia:0,x=h/2,g=u/2,f=x+m,p=g+m,y=c/2,T=0,_=0;switch((s=t.labelPosition)!==null&&s!==void 0?s:"right"){case"left":T=-(b+x);break;case"above":_=-(b+y);break;case"below":_=b+y;break;case"over":break;default:T=b+x}var E=(l=t.labelAngle)!==null&&l!==void 0?l:0,A=_n({x:T,y:_},E),R=A.x,L=A.y,F=Math.abs(Math.cos(E)),C=Math.abs(Math.sin(E)),P=F*f+C*p,D=C*f+F*p;return{minX:R-P,maxX:R+P,minY:L-D,maxY:L+D}}},{key:"computeDisplayedNodeLabels",value:function(){var t=this.internals.getCameraState(),e=this.internals.getDimensions(),n=e.width,i=e.height,o=this.internals.viewportToFramedGraph({x:-Ge,y:-Be}),s=this.internals.viewportToFramedGraph({x:n+Ge,y:-Be}),l=this.internals.viewportToFramedGraph({x:-Ge,y:i+Be}),d=this.internals.viewportToFramedGraph({x:n+Ge,y:i+Be}),h=Math.min(o.x,s.x,l.x,d.x),u=Math.max(o.x,s.x,l.x,d.x),c=Math.min(o.y,s.y,l.y,d.y),v=Math.max(o.y,s.y,l.y,d.y),b=Ae({x:.5,y:.5,ratio:1,angle:0},{width:n,height:i},this.internals.getGraphDimensions(),this.internals.getStagePadding()),m=function(z){var B=Je(b,z);return{x:(1+B.x)*n/2,y:(1-B.y)*i/2}},x=m({x:h,y:c}),g=m({x:u,y:c}),f=m({x:h,y:v}),p=m({x:u,y:v}),y={x1:Math.min(x.x,g.x,f.x,p.x),y1:Math.min(x.y,g.y,f.y,p.y),x2:Math.max(x.x,g.x,f.x,p.x),y2:Math.max(x.y,g.y,f.y,p.y)},T=this.internals,_=T.settings,E=T.nodeDataCache,A=T.nodesWithForcedLabels,R=this.labelGrid.getLabelsToDisplay(t.ratio,_.labelDensity,y);Fa(R,A);for(var L=0,F=R.length;L<F;L++){var C=R[L],P=E[C];if(!this.displayedNodeLabels.has(C)&&!(P.visibility==="hidden"||P.labelVisibility==="hidden")&&P.label&&!(P.x<h||P.x>u||P.y<c||P.y>v)){var D=this.internals.framedGraphToViewport(P),k=D.x,w=D.y,I=this.internals.scaleSize(P.size);!Ce(P)&&I<_.labelRenderedSizeThreshold||k<-Ge-I||k>n+Ge+I||w<-Be-I||w>i+Be+I||this.displayedNodeLabels.add(C)}}}},{key:"buildFramePassPoints",value:function(){var t=this.internals,e=t.nodeDataCache,n=t.nodeDataTexture;if(!n)return{data:this.framePassPoints,count:0};var i=this.displayedNodeLabels.size*3;this.framePassPoints.length<i&&(this.framePassPoints=new Float32Array(i));var o=this.framePassPoints,s=0,l=M(this.displayedNodeLabels),d;try{for(l.s();!(d=l.n()).done;){var h,u,c=d.value,v=e[c];if(v){var b=n.getIndex(c);b<0||(o[s*3]=b,o[s*3+1]=(h=$e[v.labelPosition||Te.labelPosition])!==null&&h!==void 0?h:0,o[s*3+2]=(u=v.labelAngle)!==null&&u!==void 0?u:0,s++)}}}catch(m){l.e(m)}finally{l.f()}return{data:o,count:s}}},{key:"renderWebGLLabels",value:function(t,e){var n,i,o,s=this.internals,l=s.nodeDataCache,d=s.labelProgram,h=s.primitives,u=s.nodeDataTexture,c=[],v=M(this.displayedNodeLabels),b;try{for(v.s();!(b=v.n()).done;){var m=b.value;if(!this.renderedNodeLabels.has(m)){var x=l[m];e&&x.labelDepth!==e||(this.renderedNodeLabels.add(m),c.push(m))}}}catch(ie){v.e(ie)}finally{v.f()}for(var g=0,f=0,p=c.length;f<p;f++){var y=l[c[f]];g+=y.label.length}d.reallocate(g);for(var T=14,_=(n=h==null||(i=h.nodes)===null||i===void 0||(i=i.label)===null||i===void 0?void 0:i.margin)!==null&&n!==void 0?n:et,E=Te.labelPosition,A=(h==null||(o=h.nodes)===null||o===void 0||(o=o.label)===null||o===void 0||(o=o.font)===null||o===void 0?void 0:o.family)||"sans-serif",R=new Map,L=0,F=0,C=c.length;F<C;F++){var P,D,k,w,I=c[F],G=l[I],z=G.labelFont||A,B=R.get(z);if(B===void 0){var O=Mt(z),W=O.family,U=O.weight,K=O.style;B=d.registerFont(W,U,K),R.set(z,B)}var Z={text:G.label,x:G.x,y:G.y,size:(P=G.labelSize)!==null&&P!==void 0?P:T,color:G.labelColor,nodeSize:G.size,margin:_,position:(D=G.labelPosition)!==null&&D!==void 0?D:E,hidden:!1,forceLabel:Ce(G),type:"default",zIndex:(k=G.zIndex)!==null&&k!==void 0?k:0,parentType:"node",parentKey:I,fontKey:B,labelAngle:(w=G.labelAngle)!==null&&w!==void 0?w:0,nodeIndex:u.getIndex(I)},J=d.processLabel(I,L,Z);L+=J}d.invalidateBuffers(),d.render(t)}},{key:"renderBackdrops",value:function(t,e){var n=this.internals,i=n.backdropProgram,o=n.nodeDataCache,s=n.nodesWithBackdrop,l=n.attachmentManager,d=n.pixelRatio,h=n.nodeDataTexture,u=[],c=M(s),v;try{for(c.s();!(v=c.n()).done;){var b,m=v.value,x=o[m];if(!(!x||x.visibility==="hidden")&&!(e&&x.depth!==e)){var g=(b=h?.getIndex(m))!==null&&b!==void 0?b:-1;g<0||u.push({key:m,nodeIndex:g})}}}catch(Se){c.e(Se)}finally{c.f()}if(u.length!==0){i.reallocate(u.length);for(var f=0;f<u.length;f++){var p,y,T,_,E,A,R,L,F=u[f],C=F.key,P=F.nodeIndex,D=o[C],k=this.displayedNodeLabels.has(C),w=k?this.measureNodeLabel(D):{width:0,height:0,textHeight:0},I=w.textHeight,G=w.width,z=w.height,B=0,O=0;if(k&&D.labelAttachment&&l){var W=l.getEntry(C,D.labelAttachment);if(W){var U=D.labelAttachmentPlacement||"below";if(U==="below"||U==="above"){var K=W.height/d;z+=K+Re,G=Math.max(G,W.width/d),O=U==="below"?(K+Re)/2:-(K+Re)/2}else{var Z=W.width/d;G+=Z+Re,z=Math.max(z,W.height/d),B=U==="right"?(Z+Re)/2:-(Z+Re)/2}}}var J=D.backdropColor?Ze(D.backdropColor):[255,255,255,255],ie=D.backdropShadowColor?Ze(D.backdropShadowColor):[0,0,0,128],ae=J.map(function(Se){return Se/255}),ge=ie.map(function(Se){return Se/255}),ke=(p=D.backdropShadowBlur)!==null&&p!==void 0?p:12,xe=(y=D.backdropPadding)!==null&&y!==void 0?y:6,Ct=D.backdropBorderColor?Ze(D.backdropBorderColor):[0,0,0,0],Lt=Ct.map(function(Se){return Se/255}),Pt=(T=D.backdropBorderWidth)!==null&&T!==void 0?T:0,j=(_=D.backdropCornerRadius)!==null&&_!==void 0?_:0,$=(E=D.backdropLabelPadding)!==null&&E!==void 0?E:-1,de=$<0?xe:$,rt=(A=Ds[(R=D.backdropArea)!==null&&R!==void 0?R:"both"])!==null&&A!==void 0?A:0,Hn={key:C,nodeIndex:P,label:D.label,labelWidth:G,labelHeight:z,textHeight:I,type:"default",position:D.labelPosition||Te.labelPosition,labelAngle:(L=D.labelAngle)!==null&&L!==void 0?L:0,backdropColor:ae,backdropShadowColor:ge,backdropShadowBlur:ke,backdropPadding:xe,backdropBorderColor:Lt,backdropBorderWidth:Pt,backdropCornerRadius:j,backdropLabelPadding:de,backdropArea:rt,labelBoxOffset:[B,O]};i.processBackdrop(f,Hn)}i.invalidateBuffers(),i.render(t)}}},{key:"renderLabelBackgrounds",value:function(t,e){var n=this.internals,i=n.labelBackgroundProgram,o=n.nodeDataCache,s=n.nodeDataTexture,l=re.nodeLabel.writesPickingThisFrame(this.internals),d=[],h=M(this.displayedNodeLabels),u;try{for(h.s();!(u=h.n()).done;){var c=u.value,v=o[c];!v||v.visibility==="hidden"||e&&v.labelDepth!==e||!l&&!v.labelBackgroundColor||d.push(c)}}catch(P){h.e(P)}finally{h.f()}if(d.length!==0){i.reallocate(d.length);for(var b=0;b<d.length;b++){var m,x,g,f,p=d[b],y=o[p],T=(m=s?.getIndex(p))!==null&&m!==void 0?m:-1;if(!(T<0)){var _=this.measureNodeLabel(y),E=_.width,A=_.height,R=_.textHeight,L=Le(this.internals.pickingState,"nodeLabel",p)||Le(this.internals.pickingState,"node",p),F=y.labelBackgroundColor?me(y.labelBackgroundColor):me("transparent"),C={nodeIndex:T,id:yt(L),color:F,labelWidth:E,labelHeight:A,textHeight:R,positionMode:(x=$e[y.labelPosition||Te.labelPosition])!==null&&x!==void 0?x:0,labelAngle:(g=y.labelAngle)!==null&&g!==void 0?g:0,padding:(f=y.labelBackgroundPadding)!==null&&f!==void 0?f:Ia};i.processLabelBackground(b,C)}}i.invalidateBuffers(),i.render(t)}}},{key:"cacheAttachments",value:function(t){var e=this.internals,n=e.attachmentManager,i=e.pixelRatio,o=e.nodeDataCache,s=e.nodesWithBackdrop,l=e.graph;if(n){var d=M(s),h;try{for(d.s();!(h=d.n()).done;){var u=h.value;if(this.displayedNodeLabels.has(u)){var c=o[u];if(!(!c||c.visibility==="hidden")&&!(t&&c.depth!==t)&&c.labelAttachment){var v=l.getNodeAttributes(u),b=this.measureNodeLabel(c),m=b.width,x=b.height,g={node:u,attributes:v,pixelRatio:i,labelWidth:m,labelHeight:x};n.renderAttachment(u,c.labelAttachment,g)}}}}catch(f){d.e(f)}finally{d.f()}n.regenerateAtlas()}}},{key:"renderAttachments",value:function(t,e){var n=this.internals,i=n.attachmentManager,o=n.attachmentProgram,s=n.nodeDataCache,l=n.nodesWithBackdrop,d=n.pixelRatio,h=n.nodeDataTexture;if(!(!i||!o)){var u=0;o.reallocateAttachments(l.size);var c=M(l),v;try{for(c.s();!(v=c.n()).done;){var b,m,x,g,f=v.value;if(this.displayedNodeLabels.has(f)){var p=s[f];if(!(!p||p.visibility==="hidden")&&!(e&&p.labelDepth!==e)&&p.labelAttachment){var y=i.getEntry(f,p.labelAttachment);if(y){var T=(b=h?.getIndex(f))!==null&&b!==void 0?b:-1;if(!(T<0)){var _=this.measureNodeLabel(p),E=_.width,A=_.height,R=_.textHeight,L=(m=fi[p.labelAttachmentPlacement||"below"])!==null&&m!==void 0?m:0;o.processAttachment(u,{nodeIndex:T,atlasX:y.x,atlasY:y.y,atlasW:y.width,atlasH:y.height,attachWidth:y.width/d,attachHeight:y.height/d,positionMode:(x=$e[p.labelPosition||Te.labelPosition])!==null&&x!==void 0?x:0,attachmentPlacement:L,labelWidth:E,labelHeight:A,textHeight:R,labelAngle:(g=p.labelAngle)!==null&&g!==void 0?g:0}),u++}}}}}}catch(F){c.e(F)}finally{c.f()}u!==0&&(o.reallocateAttachments(u),i.bindTexture(ca),o.invalidateBuffers(),o.render(t))}}},{key:"computeDisplayedEdgeLabels",value:function(){var t=this.internals,e=t.graph,n=t.stateManager,i=t.edgesWithForcedLabels,o=new Set(e.filterNodes(function(d){return n.getNodeState(d).isHighlighted})),s=n.hovered,l=As({graph:e,hoveredNode:s?.kind==="node"?s.key:null,displayedNodeLabels:this.displayedNodeLabels,highlightedNodes:o});Fa(l,i),this.edgeLabelCandidates=l,this.displayedEdgeLabels=new Set}},{key:"filterEdgeLabelsForDepth",value:function(t){for(var e=this.internals,n=e.graph,i=e.nodeDataCache,o=e.edgeDataCache,s=[],l=new Set,d=0,h=this.edgeLabelCandidates.length;d<h;d++){var u=this.edgeLabelCandidates[d];if(!l.has(u)){l.add(u);var c=n.extremities(u),v=i[c[0]],b=i[c[1]],m=o[u];!m||!v||!b||m.visibility==="hidden"||m.labelVisibility==="hidden"||v.visibility==="hidden"||b.visibility==="hidden"||t&&m.labelDepth!==t||m.label&&s.push(u)}}return s}},{key:"renderEdgeLabels",value:function(t,e){var n,i,o=this.internals,s=o.graph,l=o.nodeDataCache,d=o.edgeDataCache,h=o.primitives,u=o.edgeLabelProgram,c=o.nodeDataTexture,v=o.edgeDataTexture,b=this.filterEdgeLabelsForDepth(e),m=0,x=M(b),g;try{for(x.s();!(g=x.n()).done;){var f=g.value;m+=d[f].label.length}}catch(W){x.e(W)}finally{x.f()}u.reallocate(m);var p=(n=h==null||(i=h.edges)===null||i===void 0||(i=i.label)===null||i===void 0?void 0:i.margin)!==null&&n!==void 0?n:5,y="over",T=0,_=M(b),E;try{for(_.s();!(E=_.n()).done;){var A,R,L=E.value,F=s.extremities(L),C=F[0],P=F[1],D=l[C],k=l[P],w=d[L],I=c.getIndex(C),G=c.getIndex(P),z=v.getIndex(L),B={text:w.label,x:(D.x+k.x)/2,y:(D.y+k.y)/2,size:nn,color:w.labelColor,nodeSize:0,nodeIndex:-1,margin:p,position:(A=w.labelPosition)!==null&&A!==void 0?A:y,hidden:!1,forceLabel:Ce(w),type:"default",zIndex:(R=w.zIndex)!==null&&R!==void 0?R:0,parentType:"edge",parentKey:L,fontKey:"",labelAngle:0,sourceX:D.x,sourceY:D.y,targetX:k.x,targetY:k.y,sourceSize:D.size,targetSize:k.size,sourceShape:D.shape||"circle",targetShape:k.shape||"circle",edgeSize:w.size,offset:0,edgeAttributes:w,sourceNodeIndex:I,targetNodeIndex:G,edgeIndex:z},O=u.processEdgeLabel(L,T,B);T+=O,this.displayedEdgeLabels.add(L)}}catch(W){_.e(W)}finally{_.f()}u.invalidateBuffers(),u.render(t)}},{key:"renderEdgeLabelBackgrounds",value:function(t,e){var n,i,o=this.internals,s=o.edgeLabelBackgroundProgram,l=o.edgeLabelProgram,d=o.edgeDataCache,h=o.primitives,u=o.edgeDataTexture;if(u){var c=re.edgeLabel.writesPickingThisFrame(this.internals),v=(n=h==null||(i=h.edges)===null||i===void 0||(i=i.label)===null||i===void 0?void 0:i.margin)!==null&&n!==void 0?n:5,b="over",m=this.filterEdgeLabelsForDepth(e),x=[],g=M(m),f;try{for(g.s();!(f=g.n()).done;){var p=f.value;!c&&!d[p].labelBackgroundColor||x.push(p)}}catch(I){g.e(I)}finally{g.f()}if(x.length!==0){s.reallocate(x.length);for(var y=0;y<x.length;y++){var T,_,E,A=x[y],R=d[A],L=R.label,F=l.measureLabelAtlasWidth(L),C=(T=R.labelPosition)!==null&&T!==void 0?T:b,P=typeof C=="string"&&(_=Cs[C])!==null&&_!==void 0?_:0,D=Le(this.internals.pickingState,"edgeLabel",A)||Le(this.internals.pickingState,"edge",A),k=R.labelBackgroundColor?me(R.labelBackgroundColor):me("transparent"),w={edgeIndex:u.getIndex(A),baseFontSize:nn,totalTextWidth:F,positionMode:P,margin:v,padding:(E=R.labelBackgroundPadding)!==null&&E!==void 0?E:Ls,color:k,id:yt(D),edgeAttributes:R};s.processEdgeLabelBackground(y,A,w)}s.invalidateBuffers(),s.render(t)}}}}])})(),Fs=(function(){function a(r,t,e,n){V(this,a),S(this,"nodeStates",new Map),S(this,"edgeStates",new Map),S(this,"hovered",null),S(this,"dirtyNodes",new Set),S(this,"dirtyEdges",new Set),S(this,"graphStateChanged",!1),S(this,"graphStateFlagsDirty",!1),this.scheduleRefresh=r,this.customNodeStateDefaults=t,this.customEdgeStateDefaults=e,this.customGraphStateDefaults=n,this.graphState=ba(n)}return X(a,[{key:"getNodeState",value:function(t){var e=this.nodeStates.get(t);return e||(e=Rr(this.customNodeStateDefaults),this.nodeStates.set(t,e)),e}},{key:"getEdgeState",value:function(t){var e=this.edgeStates.get(t);return e||(e=Ar(this.customEdgeStateDefaults),this.edgeStates.set(t,e)),e}},{key:"getGraphState",value:function(){return this.flushGraphStateFlags(),this.graphState}},{key:"setNodeState",value:function(t,e){var n=this.getNodeState(t);if(Xe(n,e)){var i=N(N({},n),e);this.nodeStates.set(t,i),this.dirtyNodes.add(t),this.updateHoveredNodeTracking(t,n,i),this.graphStateFlagsDirty=!0,this.scheduleRefresh()}}},{key:"setEdgeState",value:function(t,e){var n=this.getEdgeState(t);if(Xe(n,e)){var i=N(N({},n),e);this.edgeStates.set(t,i),this.dirtyEdges.add(t),this.updateHoveredEdgeTracking(t,n,i),this.graphStateFlagsDirty=!0,this.scheduleRefresh()}}},{key:"setGraphState",value:function(t){if(Xe(this.graphState,t)){var e=N(N({},this.graphState),t);e.isIdle=!e.isPanning&&!e.isZooming&&!e.isDragging,this.graphState=e,this.graphStateChanged=!0,this.scheduleRefresh()}}},{key:"setNodesState",value:function(t,e){var n=!1,i=M(t),o;try{for(i.s();!(o=i.n()).done;){var s=o.value,l=this.getNodeState(s);if(Xe(l,e)){var d=N(N({},l),e);this.nodeStates.set(s,d),this.dirtyNodes.add(s),this.updateHoveredNodeTracking(s,l,d),n=!0}}}catch(h){i.e(h)}finally{i.f()}n&&(this.graphStateFlagsDirty=!0,this.scheduleRefresh())}},{key:"setEdgesState",value:function(t,e){var n=!1,i=M(t),o;try{for(i.s();!(o=i.n()).done;){var s=o.value,l=this.getEdgeState(s);if(Xe(l,e)){var d=N(N({},l),e);this.edgeStates.set(s,d),this.dirtyEdges.add(s),this.updateHoveredEdgeTracking(s,l,d),n=!0}}}catch(h){i.e(h)}finally{i.f()}n&&(this.graphStateFlagsDirty=!0,this.scheduleRefresh())}},{key:"removeNode",value:function(t){this.nodeStates.delete(t),this.dirtyNodes.delete(t),this.clearHoveredFor("node",t)}},{key:"removeEdge",value:function(t){this.edgeStates.delete(t),this.dirtyEdges.delete(t),this.clearHoveredFor("edge",t)}},{key:"clearNodes",value:function(){this.nodeStates.clear(),this.dirtyNodes.clear(),this.clearHoveredForKinds(Wt("node"))}},{key:"clearEdges",value:function(){this.edgeStates.clear(),this.dirtyEdges.clear(),this.clearHoveredForKinds(Wt("edge"))}},{key:"resetGraphState",value:function(){this.graphState=ba(this.customGraphStateDefaults),this.graphStateChanged=!1,this.graphStateFlagsDirty=!1}},{key:"clearDirtyTracking",value:function(){this.dirtyNodes.clear(),this.dirtyEdges.clear(),this.graphStateChanged=!1}},{key:"setHovered",value:function(t){this.hovered=t}},{key:"clearHoveredFor",value:function(t,e){this.hovered&&this.hovered.key===e&&Wt(t).includes(this.hovered.kind)&&(this.hovered=null)}},{key:"clearHoveredForKinds",value:function(t){this.hovered&&t.includes(this.hovered.kind)&&(this.hovered=null)}},{key:"updateGraphStateFromNodes",value:function(){var t,e=!1,n=!1,i=!1,o=M(this.nodeStates),s;try{for(o.s();!(s=o.n()).done;){var l=Q(s.value,2),d=l[1];if(d.isHovered&&(e=!0),d.isHighlighted&&(n=!0),d.isDragged&&(i=!0),e&&n&&i)break}}catch(u){o.e(u)}finally{o.f()}!e&&((t=this.hovered)===null||t===void 0?void 0:t.kind)==="edge"&&(e=!0);var h=!this.graphState.isPanning&&!this.graphState.isZooming&&!i;(this.graphState.hasHovered!==e||this.graphState.hasHighlighted!==n||this.graphState.isDragging!==i||this.graphState.isIdle!==h)&&(this.graphStateChanged=!0),this.graphState=N(N({},this.graphState),{},{hasHovered:e,hasHighlighted:n,isDragging:i,isIdle:h})}},{key:"updateGraphStateFromEdges",value:function(){var t,e=((t=this.hovered)===null||t===void 0?void 0:t.kind)==="node";if(!e){var n=M(this.edgeStates),i;try{for(n.s();!(i=n.n()).done;){var o=Q(i.value,2),s=o[1];if(s.isHovered){e=!0;break}}}catch(l){n.e(l)}finally{n.f()}}this.graphState.hasHovered!==e&&(this.graphStateChanged=!0),this.graphState=N(N({},this.graphState),{},{hasHovered:e})}},{key:"flushGraphStateFlags",value:function(){this.graphStateFlagsDirty&&(this.updateGraphStateFromNodes(),this.updateGraphStateFromEdges(),this.graphStateFlagsDirty=!1)}},{key:"updateHoveredNodeTracking",value:function(t,e,n){var i;if(e.isHovered!==n.isHovered)if(n.isHovered){var o;if(((o=this.hovered)===null||o===void 0?void 0:o.kind)==="node"&&this.hovered.key!==t){var s=this.hovered.key,l=this.getNodeState(s);this.nodeStates.set(s,N(N({},l),{},{isHovered:!1})),this.dirtyNodes.add(s)}this.hovered={kind:"node",key:t}}else((i=this.hovered)===null||i===void 0?void 0:i.kind)==="node"&&this.hovered.key===t&&(this.hovered=null)}},{key:"updateHoveredEdgeTracking",value:function(t,e,n){var i;if(e.isHovered!==n.isHovered)if(n.isHovered){var o;if(((o=this.hovered)===null||o===void 0?void 0:o.kind)==="edge"&&this.hovered.key!==t){var s=this.hovered.key,l=this.getEdgeState(s);this.edgeStates.set(s,N(N({},l),{},{isHovered:!1})),this.dirtyEdges.add(s)}this.hovered={kind:"edge",key:t}}else((i=this.hovered)===null||i===void 0?void 0:i.kind)==="edge"&&this.hovered.key===t&&(this.hovered=null)}}])})(),rn=1,on=2,sn=3,ln=4,ks=(function(a){function r(t,e){var n,i,o,s,l,d=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};V(this,r),l=ee(this,r),S(l,"nodeReducer",null),S(l,"edgeReducer",null),S(l,"stageCanvas",null),S(l,"mouseLayer",null),S(l,"extraElements",{}),S(l,"webGLContext",null),S(l,"pickingFrameBuffer",null),S(l,"pickingTexture",null),S(l,"pickingDepthBuffer",null),S(l,"activeListeners",{}),S(l,"nodeVariableEntries",[]),S(l,"edgeVariableEntries",[]),S(l,"edgePathsByName",new Map),S(l,"nodeProgramIndex",{}),S(l,"edgeProgramIndex",{}),S(l,"edgeTextureIndexCache",{}),S(l,"nodeGraphCoords",{}),S(l,"nodeExtent",{x:[0,1],y:[0,1]}),S(l,"matrix",he()),S(l,"invMatrix",he()),S(l,"correctionRatio",1),S(l,"frameId",0),S(l,"customBBox",null),S(l,"normalizationFunction",jt({x:[0,1],y:[0,1]})),S(l,"graphToViewportRatio",1),S(l,"pickingState",fs()),S(l,"prevNodeVisibilities",{}),S(l,"width",0),S(l,"height",0),S(l,"autoRescaleFrozen",!1),S(l,"stylesDeclaration",null),S(l,"resolvedStageStyle",{}),S(l,"renderFrame",null),S(l,"pendingProcess","full"),S(l,"needToRefreshState",!1),S(l,"checkEdgesEventsFrame",null),S(l,"edgeStyleAnalysis",{dependency:"static",xAttribute:null,yAttribute:null}),S(l,"depthLayers",H(qt)),S(l,"customLayerPrograms",new Map),S(l,"nodeShapeSlug",null),S(l,"sdfAtlas",null),S(l,"depthRanges",{nodes:{},edges:{}}),S(l,"nodeBaseDepth",{}),S(l,"edgeBaseDepth",{});var h=d.primitives,u=d.styles,c=d.settings,v=c===void 0?{}:c,b=d.nodeReducer,m=d.edgeReducer,x=d.customNodeState,g=d.customEdgeState,f=d.customGraphState;l.stateManager=new Fs(function(){return l.scheduleStateRefresh()},x,g,f);var p=h??Tr;l.stylesDeclaration=u?{nodes:(n=u.nodes)!==null&&n!==void 0?n:Ft.nodes,edges:(i=u.edges)!==null&&i!==void 0?i:Ft.edges,stage:u.stage}:Ft,l.nodeReducer=b??null,l.edgeReducer=m??null;var y=xa(l.stylesDeclaration.nodes);l.nodeReducer&&(y.dependency="graph-state"),l.edgeStyleAnalysis=xa(l.stylesDeclaration.edges),l.edgeReducer&&(l.edgeStyleAnalysis.dependency="graph-state"),l.stylesDeclaration.stage&&(l.resolvedStageStyle=Ea(l.stylesDeclaration.stage,l.stateManager.graphState));var T=qr(v);if(zt(T),T.enableNodeDrag){var _=y.xAttribute,E=y.yAttribute;if((!_||!E)&&!T.dragPositionToAttributes)throw new Error('Sigma: `enableNodeDrag` is true but position attribute names could not be inferred from styles. Either use attribute bindings for x/y in your node styles (e.g. `x: { attribute: "x" }`), or provide a `dragPositionToAttributes` setting.')}if(Vr(t),!(e instanceof HTMLElement))throw new Error("Sigma: container should be an html element.");l.container=e,l.edgeGroups=new cs(t,function(j,$){for(var de=0;de<j.length;de++){var rt=l.stateManager.getEdgeState(j[de]);rt.parallelIndex=de,rt.parallelCount=$}});var A=new hs(t,l.viewportToGraph.bind(l),l.setNodesState.bind(l),function(j,$){return l.emit(j,$)});if(l.depthLayers=(o=p.depthLayers)!==null&&o!==void 0?o:H(qt),!(u!=null&&u.nodes)&&!Vt.every(function(j){return l.depthLayers.includes(j)}))throw new Error("Sigma: depthLayers must include ".concat(Vt.join(", ")," for the built-in node styles."));if(!(u!=null&&u.edges)&&!Xt.every(function(j){return l.depthLayers.includes(j)}))throw new Error("Sigma: depthLayers must include ".concat(Xt.join(", ")," for the built-in edge styles."));l.itemBuckets={nodes:new ja(l.depthLayers),edges:new ja(l.depthLayers)},l.initWebGLContext(),l.mouseLayer=ka("div",{position:"absolute",touchAction:"none",userSelect:"none"},{class:"sigma-mouse"}),l.container.appendChild(l.mouseLayer),l.resolvedStageStyle.background&&(l.container.style.backgroundColor=l.resolvedStageStyle.background),l.resolvedStageStyle.cursor&&(l.container.style.cursor=l.resolvedStageStyle.cursor);var R=new zo(l.webGLContext),L=new Ya(l.webGLContext,{channels:1}),F=new Bo(l.webGLContext),C=new Ya(l.webGLContext,{channels:4}),P=l,D=l.webGLContext,k=ts(D,l.pickingFrameBuffer,P,p?.nodes),w=k.nodeProgram,I=k.labelProgram,G=k.backdropProgram,z=k.labelBackgroundProgram,B=k.attachmentProgram,O=k.framePass,W=k.shapeSlug,U=k.shapeNameToIndex,K=k.shapeGlobalIds,Z=k.variables;l.nodeProgram=w,l.nodeFramePass=O,l.nodeVariableEntries=Object.entries(Z),W&&(l.nodeShapeSlug=W);var J=p==null||(s=p.nodes)===null||s===void 0?void 0:s.labelAttachments,ie=null;J&&Object.keys(J).length>0&&(ie=new Io(D,J,function(){return l.scheduleRender()}));var ae=as(D,l.pickingFrameBuffer,P,p?.edges),ge=ae.edgeProgram,ke=ae.labelProgram,xe=ae.labelBackgroundProgram,Ct=ae.framePass,Lt=ae.variables,Pt=ae.paths;return l.edgeProgram=ge,l.edgeFramePass=Ct,l.edgeVariableEntries=Object.entries(Lt),l.edgePathsByName=new Map(Pt.map(function(j){return[j.name,j]})),l.internals={nodeDataCache:{},edgeDataCache:{},nodesWithForcedLabels:new Set,nodesWithBackdrop:new Set,edgesWithForcedLabels:new Set,settings:T,primitives:p,pixelRatio:Yt(),graph:t,stateManager:l.stateManager,dragManager:A,nodeStyleAnalysis:y,pickingState:l.pickingState,labelProgram:I,edgeLabelProgram:ke,edgeLabelBackgroundProgram:xe,backdropProgram:G,labelBackgroundProgram:z,attachmentManager:ie,attachmentProgram:B,nodeDataTexture:R,nodeFrameTexture:L,edgeDataTexture:F,edgeFrameTexture:C,nodeShapeMap:U??null,nodeGlobalShapeIds:K??null,getDimensions:function(){return l.getDimensions()},getGraphDimensions:function(){return l.getGraphDimensions()},getStagePadding:function(){return l.getStagePadding()},getCameraState:function(){return l.camera.getState()},getHitAtPosition:function($){return l.getHitAtPosition($)},setNodeState:function($,de){return l.setNodeState($,de)},setEdgeState:function($,de){return l.setEdgeState($,de)},updateContainerCursor:function(){return l.updateContainerCursor()},scheduleRefresh:function(){return l.scheduleRefresh()},viewportToFramedGraph:function($){return l.viewportToFramedGraph($)},viewportToGraph:function($){return l.viewportToGraph($)},framedGraphToViewport:function($){return l.framedGraphToViewport($)},scaleSize:function($){return l.scaleSize($)},emit:function($,de){return l.emit($,de)}},l.labelRenderer=new Ps(l.internals),l.resize(),l.initializeWebGLLabels(),l.camera=new Ka,l.bindCameraHandlers(),l.mouseCaptor=new ss(l.mouseLayer,l),l.mouseCaptor.setSettings(l.internals.settings),l.touchCaptor=new us(l.mouseLayer,l),l.touchCaptor.setSettings(l.internals.settings),l.bindEventHandlers(),l.bindGraphHandlers(),l.handleSettingsUpdate(),l.refresh(),l}return te(r,a),X(r,[{key:"initializeWebGLLabels",value:function(){this.sdfAtlas=new Oe,this.sdfAtlas.registerFont({family:"sans-serif",weight:"normal",style:"normal"})}},{key:"resetWebGLTexture",value:function(){var e=this.webGLContext;if(!this.pickingFrameBuffer)return this;var n=Math.ceil(this.width*this.internals.pixelRatio/this.internals.settings.pickingDownSizingRatio),i=Math.ceil(this.height*this.internals.pixelRatio/this.internals.settings.pickingDownSizingRatio);e.bindFramebuffer(e.FRAMEBUFFER,this.pickingFrameBuffer),this.pickingTexture&&e.deleteTexture(this.pickingTexture);var o=e.createTexture();o&&(e.bindTexture(e.TEXTURE_2D,o),e.texImage2D(e.TEXTURE_2D,0,e.RGBA,n,i,0,e.RGBA,e.UNSIGNED_BYTE,null),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MIN_FILTER,e.NEAREST),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MAG_FILTER,e.NEAREST),e.framebufferTexture2D(e.FRAMEBUFFER,e.COLOR_ATTACHMENT0,e.TEXTURE_2D,o,0),this.pickingTexture=o),this.pickingDepthBuffer&&e.deleteRenderbuffer(this.pickingDepthBuffer);var s=e.createRenderbuffer();return s&&(e.bindRenderbuffer(e.RENDERBUFFER,s),e.renderbufferStorage(e.RENDERBUFFER,e.DEPTH_COMPONENT16,n,i),e.framebufferRenderbuffer(e.FRAMEBUFFER,e.DEPTH_ATTACHMENT,e.RENDERBUFFER,s),this.pickingDepthBuffer=s),e.bindFramebuffer(e.FRAMEBUFFER,null),this}},{key:"bindCameraHandlers",value:function(){var e=this;return this.activeListeners.camera=function(){e.refreshMatrices(),e.scheduleRender()},this.activeListeners.cameraAnimationStart=function(n,i){n.ratio!==i.ratio&&e.stateManager.setGraphState({isZooming:!0})},this.activeListeners.cameraAnimationEnd=function(){e.stateManager.setGraphState({isZooming:!1})},this.camera.on("updated",this.activeListeners.camera),this.camera.on("animationStart",this.activeListeners.cameraAnimationStart),this.camera.on("animationEnd",this.activeListeners.cameraAnimationEnd),this}},{key:"unbindCameraHandlers",value:function(){return this.camera.removeListener("updated",this.activeListeners.camera),this.camera.removeListener("animationStart",this.activeListeners.cameraAnimationStart),this.camera.removeListener("animationEnd",this.activeListeners.cameraAnimationEnd),this}},{key:"getHitAtPosition",value:function(e){var n,i=this.webGLContext;i.bindFramebuffer(i.FRAMEBUFFER,this.pickingFrameBuffer);var o=$n(i,this.pickingFrameBuffer,e.x,e.y,this.internals.pixelRatio,this.internals.settings.pickingDownSizingRatio),s=Zn.apply(void 0,H(o));return(n=this.pickingState.lookup[s])!==null&&n!==void 0?n:null}},{key:"bindEventHandlers",value:function(){return xs(this.internals,this.mouseCaptor,this.touchCaptor,this.activeListeners),this}},{key:"bindGraphHandlers",value:function(){return ys({graph:this.internals.graph,edgeGroups:this.edgeGroups,addNode:this.addNode.bind(this),updateNode:this.updateNode.bind(this),removeNode:this.removeNode.bind(this),addEdge:this.addEdge.bind(this),updateEdge:this.updateEdge.bind(this),removeEdge:this.removeEdge.bind(this),clearEdgeState:this.clearEdgeState.bind(this),clearNodeState:this.clearNodeState.bind(this),clearEdgeIndices:this.clearEdgeIndices.bind(this),clearNodeIndices:this.clearNodeIndices.bind(this),refresh:this.refresh.bind(this)},this.activeListeners),this}},{key:"unbindGraphHandlers",value:function(){Ts(this.internals.graph,this.activeListeners)}},{key:"getNodeShapeId",value:function(e){return this.internals.nodeShapeMap&&this.internals.nodeGlobalShapeIds&&e.shape&&e.shape in this.internals.nodeShapeMap?this.internals.nodeGlobalShapeIds[this.internals.nodeShapeMap[e.shape]]:pt(e.shape||"circle")}},{key:"processNodes",value:function(){var e=this,n=this.internals.graph,i=this.internals.settings,o=this.getDimensions(),s=i.autoRescale,l=i.autoRescaleContent,d=this.nodeExtent;if((s!=="once"||!this.autoRescaleFrozen)&&(d=this.computeNodeExtent(),s!==!1&&l!=="positions"&&!this.customBBox&&(d=Rs({extent:d,coords:this.nodeGraphCoords,nodeData:this.internals.nodeDataCache,dimensions:o,stagePadding:this.getStagePadding(),zoomToSizeRatioFunction:i.zoomToSizeRatioFunction,itemSizesReference:i.itemSizesReference,fitLabels:l==="labels",nodeLabelBox:function(W,U){return e.labelRenderer.nodeLabelBox(W,U)}})),s==="once"&&(this.autoRescaleFrozen=!0)),s===!1){var h=o.width,u=o.height,c=(d.x[0]+d.x[1])/2,v=(d.y[0]+d.y[1])/2;d={x:[c-h/2,c+h/2],y:[v-u/2,v+u/2]}}this.nodeExtent=d,this.normalizationFunction=jt(this.customBBox||this.nodeExtent);var b=new Ka,m=Ae(b.getState(),o,this.getGraphDimensions(),this.getStagePadding());this.labelRenderer.labelGrid.resizeAndClear(o,i.labelGridCellSize);var x=!1;Gt(this.pickingState,"node");for(var g=n.nodes(),f=0,p=g.length;f<p;f++){var y=g[f],T=this.internals.nodeDataCache[y],_=this.nodeGraphCoords[y];T.x=_.x,T.y=_.y,this.normalizationFunction.applyTo(T),T.visibility!==this.prevNodeVisibilities[y]&&(x=!0),typeof T.label=="string"&&T.visibility!=="hidden"&&T.labelVisibility!=="hidden"&&this.labelRenderer.labelGrid.add(y,T.size,this.framedGraphToViewport(T,{matrix:m}))}this.labelRenderer.labelGrid.organize(),this.nodeProgram.reallocate(g.length);var E=0;this.depthRanges.nodes={},this.nodeBaseDepth={};var A=this.internals.nodeDataCache,R=M(this.depthLayers),L;try{for(R.s();!(L=R.n()).done;){var F=L.value,C=this.itemBuckets.nodes.getSorted(F,function(O){return A[O].zIndex});if(C.length!==0){this.depthRanges.nodes[F]=[{offset:E,count:C.length}];var P=M(C),D;try{for(P.s();!(D=P.n()).done;){var k=D.value;this.nodeBaseDepth[k]=F,this.nodeProgram.allocateNode(k),Ja(this.pickingState,"node",k),this.addNodeToProgram(k,E++)}}catch(O){P.e(O)}finally{P.f()}}}}catch(O){R.e(O)}finally{R.f()}this.nodeProgram.invalidateBuffers();for(var w=0,I=g.length;w<I;w++)this.prevNodeVisibilities[g[w]]=this.internals.nodeDataCache[g[w]].visibility;this.labelRenderer.processWebGLLabels(g);var G=M(this.customLayerPrograms.values()),z;try{for(G.s();!(z=G.n()).done;){var B=z.value.program;B.cacheData&&B.cacheData()}}catch(O){G.e(O)}finally{G.f()}return x}},{key:"processEdges",value:function(){var e=this.internals.graph,n=e.edges();this.edgeProgram.reallocate(n.length);var i=0;Gt(this.pickingState,"edge"),this.depthRanges.edges={},this.edgeBaseDepth={};var o=this.internals.edgeDataCache,s=M(this.depthLayers),l;try{for(s.s();!(l=s.n()).done;){var d=l.value,h=this.itemBuckets.edges.getSorted(d,function(b){return o[b].zIndex});if(h.length!==0){this.depthRanges.edges[d]=[{offset:i,count:h.length}];var u=M(h),c;try{for(u.s();!(c=u.n()).done;){var v=c.value;this.edgeBaseDepth[v]=d,Ja(this.pickingState,"edge",v),this.addEdgeToProgram(v,i++)}}catch(b){u.e(b)}finally{u.f()}}}}catch(b){s.e(b)}finally{s.f()}this.edgeProgram.invalidateBuffers()}},{key:"updateNodeDepthRanges",value:function(e,n,i){var o=this.nodeProgramIndex[e];o!==void 0&&(La(this.depthRanges.nodes,n,o),Pa(this.depthRanges.nodes,i,o))}},{key:"updateEdgeDepthRanges",value:function(e,n,i){var o=this.edgeProgramIndex[e];o!==void 0&&(La(this.depthRanges.edges,n,o),Pa(this.depthRanges.edges,i,o))}},{key:"handleSettingsUpdate",value:function(){var e=this,n=this.internals.settings;return this.camera.minRatio=n.minCameraRatio,this.camera.maxRatio=n.maxCameraRatio,this.camera.enabledZooming=n.enableCameraZooming,this.camera.enabledPanning=n.enableCameraPanning,this.camera.enabledRotation=n.enableCameraRotation,n.cameraPanBoundaries?this.camera.clean=function(i){return e.cleanCameraState(i,n.cameraPanBoundaries&&q(n.cameraPanBoundaries)==="object"?n.cameraPanBoundaries:{})}:this.camera.clean=null,this.camera.setState(this.camera.validateState(this.camera.getState())),this.mouseCaptor.setSettings(this.internals.settings),this.touchCaptor.setSettings(this.internals.settings),this}},{key:"cleanCameraState",value:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},i=n.tolerance,o=i===void 0?0:i,s=n.boundaries,l=N({},e),d=s||this.nodeExtent,h=Q(d.x,2),u=h[0],c=h[1],v=Q(d.y,2),b=v[0],m=v[1],x=[this.graphToViewport({x:u,y:b},{cameraState:e}),this.graphToViewport({x:c,y:b},{cameraState:e}),this.graphToViewport({x:u,y:m},{cameraState:e}),this.graphToViewport({x:c,y:m},{cameraState:e})],g=1/0,f=-1/0,p=1/0,y=-1/0;x.forEach(function(D){var k=D.x,w=D.y;g=Math.min(g,k),f=Math.max(f,k),p=Math.min(p,w),y=Math.max(y,w)});var T=f-g,_=y-p,E=this.getDimensions(),A=E.width,R=E.height,L=0,F=0;if(T>=A?f<A-o?L=f-(A-o):g>o&&(L=g-o):f>A+o?L=f-(A+o):g<-o&&(L=g+o),_>=R?y<R-o?F=y-(R-o):p>o&&(F=p-o):y>R+o?F=y-(R+o):p<-o&&(F=p+o),L||F){var C=this.viewportToFramedGraph({x:0,y:0},{cameraState:e}),P=this.viewportToFramedGraph({x:L,y:F},{cameraState:e});L=P.x-C.x,F=P.y-C.y,l.x+=L,l.y+=F}return l}},{key:"refreshMatrices",value:function(){var e=this.camera.getState(),n=this.getDimensions(),i=this.getGraphDimensions(),o=this.getStagePadding();this.matrix=Ae(e,n,i,o),this.invMatrix=Ae(e,n,i,o,!0),this.correctionRatio=Hr(this.matrix,e,n),this.graphToViewportRatio=this.getGraphToViewportRatio()}},{key:"processData",value:function(){var e;this.emit("beforeProcess"),(e=this.internals.attachmentManager)===null||e===void 0||e.clear();var n=this.processNodes();(this.pendingProcess==="full"||n)&&this.processEdges(),gs(this.pickingState,this.internals),this.pendingProcess="none",this.emit("afterProcess")}},{key:"render",value:function(){var e=this;this.emit("beforeRender");var n=function(){return e.emit("afterRender"),e};if(this.renderFrame&&(cancelAnimationFrame(this.renderFrame),this.renderFrame=null),this.resize(),this.pendingProcess!=="none"&&this.processData(),this.needToRefreshState&&this.refreshState(),this.needToRefreshState=!1,this.stateManager.clearDirtyTracking(),this.pendingProcess!=="none"&&this.processData(),this.clear(),this.resetWebGLTexture(),!this.internals.graph.order)return n();var i=this.mouseCaptor,o=this.camera.isAnimated()||i.isMoving||i.draggedEvents||i.currentWheelDirection;this.refreshMatrices(),this.frameId++,this.internals.nodeFrameTexture.ensureCapacity(this.internals.nodeDataTexture.getCapacity()),this.internals.edgeFrameTexture.ensureCapacity(this.internals.edgeDataTexture.getCapacity());var s=this.getRenderParams(),l=re.edge.writesPickingThisFrame(this.internals)?s:N(N({},s),{},{pickingFrameBuffer:null});this.labelRenderer.resetFrame();var d=this.webGLContext,h=Math.ceil(this.width*this.internals.pixelRatio/this.internals.settings.pickingDownSizingRatio),u=Math.ceil(this.height*this.internals.pixelRatio/this.internals.settings.pickingDownSizingRatio);if(d.bindFramebuffer(d.FRAMEBUFFER,this.pickingFrameBuffer),d.viewport(0,0,h,u),d.clear(d.COLOR_BUFFER_BIT|d.DEPTH_BUFFER_BIT),d.bindFramebuffer(d.FRAMEBUFFER,null),d.viewport(0,0,this.width*this.internals.pixelRatio,this.height*this.internals.pixelRatio),d.clear(d.COLOR_BUFFER_BIT|d.DEPTH_BUFFER_BIT),this.internals.nodeDataTexture.upload(),this.internals.edgeDataTexture.upload(),this.nodeProgram.uploadLayerTexture(),this.edgeProgram.uploadAttributeTexture(),this.internals.nodeDataTexture.bind(sn),this.internals.edgeDataTexture.bind(ln),this.edgeFramePass.run(s,this.internals.edgeFrameTexture,this.internals.edgeDataTexture.getHighWaterMark(),this.edgeProgram.getAttributeTexture()),this.internals.edgeFrameTexture.bind(rn),this.internals.settings.renderLabels){this.labelRenderer.computeDisplayedNodeLabels();var c=this.labelRenderer.buildFramePassPoints(),v=c.data,b=c.count;this.nodeFramePass.run(v,b,this.internals.nodeFrameTexture,s),this.internals.nodeFrameTexture.bind(on)}this.internals.settings.renderEdgeLabels&&this.labelRenderer.computeDisplayedEdgeLabels();var m=M(this.customLayerPrograms.values()),x;try{for(m.s();!(x=m.n()).done;){var g=x.value.program;g.preRender&&g.preRender(s)}}catch(B){m.e(B)}finally{m.f()}d.bindFramebuffer(d.FRAMEBUFFER,null),d.viewport(0,0,this.width*this.internals.pixelRatio,this.height*this.internals.pixelRatio),d.blendFunc(d.ONE,d.ONE_MINUS_SRC_ALPHA);var f=M(this.depthLayers),p;try{for(f.s();!(p=f.n()).done;){var y=p.value,T=M(this.customLayerPrograms.values()),_;try{for(T.s();!(_=T.n()).done;){var E=_.value;E.depth===y&&E.program.render(s)}}catch(B){T.e(B)}finally{T.f()}var A=this.depthRanges.edges[y];if(A&&(!this.internals.settings.hideEdgesOnMove||!o)){var R=M(A),L;try{for(R.s();!(L=R.n()).done;){var F=L.value,C=F.offset,P=F.count;P>0&&this.edgeProgram.render(l,C,P)}}catch(B){R.e(B)}finally{R.f()}}this.internals.settings.renderEdgeLabels&&(!this.internals.settings.hideLabelsOnMove||!o)&&(this.labelRenderer.renderEdgeLabelBackgrounds(re.edgeLabel.writesPickingThisFrame(this.internals)?s:N(N({},s),{},{pickingFrameBuffer:null}),y),this.labelRenderer.renderEdgeLabels(s,y)),this.labelRenderer.cacheAttachments(y),this.labelRenderer.renderBackdrops(N(N({},s),{},{pickingFrameBuffer:null}),y);var D=this.depthRanges.nodes[y];if(D){var k=M(D),w;try{for(k.s();!(w=k.n()).done;){var I=w.value,G=I.offset,z=I.count;z>0&&this.nodeProgram.render(s,G,z)}}catch(B){k.e(B)}finally{k.f()}}this.labelRenderer.renderAttachments(N(N({},s),{},{pickingFrameBuffer:null}),y),this.labelRenderer.renderLabelBackgrounds(re.nodeLabel.writesPickingThisFrame(this.internals)?s:N(N({},s),{},{pickingFrameBuffer:null}),y),this.internals.settings.renderLabels&&this.labelRenderer.renderWebGLLabels(s,y)}}catch(B){f.e(B)}finally{f.f()}return this.internals.settings.DEBUG_displayPickingLayer&&(d.bindFramebuffer(d.READ_FRAMEBUFFER,this.pickingFrameBuffer),d.bindFramebuffer(d.DRAW_FRAMEBUFFER,null),d.blitFramebuffer(0,0,h,u,0,0,this.width*this.internals.pixelRatio,this.height*this.internals.pixelRatio,d.COLOR_BUFFER_BIT,d.NEAREST)),this.internals.settings.hideLabelsOnMove&&o,n()}},{key:"postEvaluateNode",value:function(e,n,i){var o=e;o.x===void 0&&(o.x=n.x),o.y===void 0&&(o.y=n.y),e.highlighted=i.isHighlighted;for(var s=0,l=this.nodeVariableEntries.length;s<l;s++){var d,h,u=Q(this.nodeVariableEntries[s],2),c=u[0],v=u[1];o[c]=(d=(h=o[c])!==null&&h!==void 0?h:n[c])!==null&&d!==void 0?d:v.default}}},{key:"addNode",value:function(e){var n=this.internals.graph.getNodeAttributes(e),i=this.stateManager.getNodeState(e),o=this.internals.nodeDataCache[e]||{};if(_a(this.stylesDeclaration.nodes,n,i,this.stateManager.graphState,this.internals.graph,o),this.postEvaluateNode(o,n,i),this.nodeReducer){var s=this.nodeReducer(e,o,n,i,this.stateManager.graphState,this.internals.graph);o=N(N({},o),s)}if(typeof o.x!="number"||typeof o.y!="number")throw new Error('Sigma: could not find a valid position (x, y) for node "'.concat(e,'". ')+"Provide coordinates via node attributes, styles, or a nodeReducer.");this.internals.nodeShapeMap?(!o.shape||!(o.shape in this.internals.nodeShapeMap))&&(o.shape=Object.keys(this.internals.nodeShapeMap)[0]):this.nodeShapeSlug&&(o.shape=this.nodeShapeSlug),this.internals.nodeDataCache[e]=o,this.nodeGraphCoords[e]={x:o.x,y:o.y},Ie(this.internals.nodesWithForcedLabels,e,Ce(o)),Ie(this.internals.nodesWithBackdrop,e,Ca(o)),this.itemBuckets.nodes.set(e,o.depth)}},{key:"updateNode",value:function(e){this.addNode(e);var n=this.internals.nodeDataCache[e];this.normalizationFunction.applyTo(n)}},{key:"removeNode",value:function(e){this.itemBuckets.nodes.remove(e),delete this.internals.nodeDataCache[e],delete this.nodeGraphCoords[e],delete this.nodeProgramIndex[e],this.internals.dragManager.removeNode(e),this.stateManager.removeNode(e),this.internals.nodesWithForcedLabels.delete(e),this.internals.nodesWithBackdrop.delete(e)}},{key:"postEvaluateEdge",value:function(e,n){for(var i=e,o=0,s=this.edgeVariableEntries.length;o<s;o++){var l,d,h=Q(this.edgeVariableEntries[o],2),u=h[0],c=h[1];i[u]=(l=(d=i[u])!==null&&d!==void 0?d:n[u])!==null&&l!==void 0?l:c.default}}},{key:"applyEdgeSpread",value:function(e,n,i){var o;if(!(i.parallelCount<=1)){var s=this.internals.graph.source(e),l=this.internals.graph.target(e),d=s===l,h=d?n.selfLoopPath||n.path:n.parallelPath||n.path,u=h?this.edgePathsByName.get(h):void 0;if(u!=null&&u.spread){var c=(o=n.parallelSpread)!==null&&o!==void 0?o:.25,v=u.spread.compute(i.parallelIndex,i.parallelCount,c);!d&&this.internals.graph.isDirected(e)&&s>l&&(v=-v),n[u.spread.variable]=v}}}},{key:"addEdge",value:function(e){var n=this.internals.graph.getEdgeAttributes(e),i=this.stateManager.getEdgeState(e),o={};if(Sa(this.stylesDeclaration.edges,n,i,this.stateManager.graphState,this.internals.graph,o),this.postEvaluateEdge(o,n),this.edgeReducer){var s=this.edgeReducer(e,o,n,i,this.stateManager.graphState,this.internals.graph);o=N(N({},o),s)}this.applyEdgeSpread(e,o,i),this.internals.edgeDataCache[e]=o,Ie(this.internals.edgesWithForcedLabels,e,Ce(o)),this.itemBuckets.edges.set(e,o.depth)}},{key:"updateEdge",value:function(e){this.addEdge(e)}},{key:"removeEdge",value:function(e){this.itemBuckets.edges.remove(e),delete this.internals.edgeDataCache[e],delete this.edgeProgramIndex[e],delete this.edgeTextureIndexCache[e],this.internals.edgeDataTexture.free(e),this.stateManager.removeEdge(e),this.internals.edgesWithForcedLabels.delete(e)}},{key:"clearNodeIndices",value:function(){this.labelRenderer.resetLabelGrid(),this.nodeExtent={x:[0,1],y:[0,1]},this.internals.nodeDataCache={},this.nodeGraphCoords={},this.edgeProgramIndex={},this.internals.nodesWithForcedLabels.clear(),this.internals.nodesWithBackdrop.clear(),this.prevNodeVisibilities={},this.itemBuckets.nodes.clearAll(),this.depthRanges.nodes={},this.nodeBaseDepth={}}},{key:"clearEdgeIndices",value:function(){this.internals.edgeDataCache={},this.edgeProgramIndex={},this.edgeTextureIndexCache={},this.internals.edgesWithForcedLabels.clear(),Gt(this.pickingState,"edge"),this.itemBuckets.edges.clearAll(),this.depthRanges.edges={},this.edgeBaseDepth={},this.edgeGroups.clear()}},{key:"clearIndices",value:function(){this.clearEdgeIndices(),this.clearNodeIndices()}},{key:"clearNodeState",value:function(){this.labelRenderer.resetFrame(),this.internals.nodesWithBackdrop.clear(),this.internals.dragManager.clear(),this.autoRescaleFrozen=!1,this.stateManager.clearNodes()}},{key:"clearEdgeState",value:function(){this.labelRenderer.clearEdgeLabels(),this.stateManager.clearEdges()}},{key:"clearState",value:function(){this.clearEdgeState(),this.clearNodeState(),this.stateManager.resetGraphState()}},{key:"addNodeToProgram",value:function(e,n){var i,o=this.internals.nodeDataCache[e];this.internals.nodeDataTexture.allocate(e),(i=this.internals.nodeDataTexture).updateNode.apply(i,[e,o.x,o.y,o.size,this.getNodeShapeId(o)].concat(H(It(o))));var s=this.internals.nodeDataTexture.getIndex(e);this.nodeProgram.process(Le(this.pickingState,"node",e),n,o,s,e),this.nodeProgramIndex[e]=n}},{key:"addEdgeToProgram",value:function(e,n){var i,o,s=this.internals.edgeDataCache[e],l=this.internals.graph.source(e),d=this.internals.graph.target(e),h=this.internals.edgeDataTexture.allocate(e);this.edgeTextureIndexCache[e]=h;var u=l===d,c=!u&&((i=(o=this.stateManager.getEdgeState(e))===null||o===void 0?void 0:o.parallelCount)!==null&&i!==void 0?i:1)>1,v=this.edgeProgram.resolveEdgeIds(s,u,c),b=v.pathId,m=v.headId,x=v.tailId,g=v.headLengthRatio,f=v.tailLengthRatio;this.internals.edgeDataTexture.updateEdge(e,this.internals.nodeDataTexture.getIndex(l),this.internals.nodeDataTexture.getIndex(d),s.size,g,f,b,m,x),this.edgeProgram.process(Le(this.pickingState,"edge",e),n,this.internals.nodeDataCache[l],this.internals.nodeDataCache[d],s,h),this.edgeProgramIndex[e]=n}},{key:"getRenderParams",value:function(){return{frameId:this.frameId,matrix:this.matrix,invMatrix:this.invMatrix,width:this.width,height:this.height,pixelRatio:this.internals.pixelRatio,zoomRatio:this.camera.ratio,cameraAngle:this.camera.angle,sizeRatio:1/this.scaleSize(),correctionRatio:this.correctionRatio,downSizingRatio:this.internals.settings.pickingDownSizingRatio,minEdgeThickness:this.internals.settings.minEdgeThickness,antiAliasingFeather:this.internals.settings.antiAliasingFeather,nodePickingPadding:this.internals.settings.nodePickingPadding,edgePickingPadding:this.internals.settings.edgePickingPadding,labelPickingPadding:this.internals.settings.labelPickingPadding,nodeDataTextureUnit:sn,nodeDataTextureWidth:this.internals.nodeDataTexture.getTextureWidth(),nodeFrameTextureUnit:on,nodeFrameTextureWidth:this.internals.nodeFrameTexture.getTextureWidth(),edgeDataTextureUnit:ln,edgeDataTextureWidth:this.internals.edgeDataTexture.getTextureWidth(),edgeFrameTextureUnit:rn,edgeFrameTextureWidth:this.internals.edgeFrameTexture.getTextureWidth(),pickingFrameBuffer:this.pickingFrameBuffer,labelPixelSnapping:this.internals.settings.labelPixelSnapping?1:0}}},{key:"getStagePadding",value:function(){var e=this.internals.settings,n=e.stagePadding,i=e.autoRescale;return i&&n||0}},{key:"getLayerElement",value:function(e){if(e==="mouse")return this.mouseLayer;var n=this.extraElements[e];if(!n)throw new Error('Sigma: layer "'.concat(e,'" does not exist'));return n}},{key:"initWebGLContext",value:function(){var e=this.createWebGLContext("stage");this.stageCanvas=this.extraElements.stage,this.webGLContext=e;var n=e.createFramebuffer();if(!n)throw new Error("Sigma: cannot create picking frame buffer");e.bindFramebuffer(e.FRAMEBUFFER,n);var i=e.createTexture();if(!i)throw new Error("Sigma: cannot create picking texture");e.bindTexture(e.TEXTURE_2D,i),e.texImage2D(e.TEXTURE_2D,0,e.RGBA,1,1,0,e.RGBA,e.UNSIGNED_BYTE,null),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MIN_FILTER,e.NEAREST),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MAG_FILTER,e.NEAREST),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_WRAP_S,e.CLAMP_TO_EDGE),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_WRAP_T,e.CLAMP_TO_EDGE),e.framebufferTexture2D(e.FRAMEBUFFER,e.COLOR_ATTACHMENT0,e.TEXTURE_2D,i,0);var o=e.createRenderbuffer();if(!o)throw new Error("Sigma: cannot create picking depth buffer");if(e.bindRenderbuffer(e.RENDERBUFFER,o),e.renderbufferStorage(e.RENDERBUFFER,e.DEPTH_COMPONENT16,1,1),e.framebufferRenderbuffer(e.FRAMEBUFFER,e.DEPTH_ATTACHMENT,e.RENDERBUFFER,o),e.checkFramebufferStatus(e.FRAMEBUFFER)!==e.FRAMEBUFFER_COMPLETE)throw new Error("Sigma: picking framebuffer is not complete");e.bindFramebuffer(e.FRAMEBUFFER,null),this.pickingFrameBuffer=n,this.pickingTexture=i,this.pickingDepthBuffer=o}},{key:"createLayer",value:function(e,n){var i=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(this.extraElements[e])throw new Error('Sigma: a layer named "'.concat(e,'" already exists'));var o=ka(n,{position:"absolute"},{class:"sigma-".concat(e)});return i.style&&Object.assign(o.style,i.style),this.extraElements[e]=o,"beforeLayer"in i&&i.beforeLayer?this.getLayerElement(i.beforeLayer).before(o):"afterLayer"in i&&i.afterLayer?this.getLayerElement(i.afterLayer).after(o):this.container.appendChild(o),o}},{key:"createCanvas",value:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};return this.createLayer(e,"canvas",n)}},{key:"createWebGLContext",value:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},i=this.createCanvas(e,n);n.hidden&&i.remove();var o=i.getContext("webgl2",N({preserveDrawingBuffer:!1,antialias:!1,depth:!0},n));if(!o)throw new Error("Sigma: WebGL 2 is not supported by your browser. Please use a modern browser (Chrome 56+, Firefox 51+, Safari 15+, Edge 79+).");return o.blendFunc(o.ONE,o.ONE_MINUS_SRC_ALPHA),o}},{key:"killLayer",value:function(e){if(e==="stage"||e==="mouse")throw new Error('Sigma: cannot kill built-in layer "'.concat(e,'"'));var n=this.extraElements[e];if(!n)throw new Error("Sigma: cannot kill layer ".concat(e,", which does not exist"));return n.remove(),delete this.extraElements[e],this}},{key:"getWebGLContext",value:function(){if(!this.webGLContext)throw new Error("Sigma: WebGL context is not available");return this.webGLContext}},{key:"addCustomLayerProgram",value:function(e,n,i){var o;if(!this.depthLayers.includes(n))throw new Error('Sigma: cannot add custom layer program at depth "'.concat(n,'", ')+"it must be declared in primitives.depthLayers. Current layers: ".concat(this.depthLayers.join(", ")));return(o=this.customLayerPrograms.get(e))===null||o===void 0||o.program.kill(),this.customLayerPrograms.set(e,{depth:n,program:i}),this.refresh(),this}},{key:"removeCustomLayerProgram",value:function(e){var n=this.customLayerPrograms.get(e);return n&&(n.program.kill(),this.customLayerPrograms.delete(e),this.scheduleRender()),this}},{key:"getCamera",value:function(){return this.camera}},{key:"setCamera",value:function(e){return this.unbindCameraHandlers(),this.camera=e,this.bindCameraHandlers(),this.scheduleRender(),this}},{key:"getContainer",value:function(){return this.container}},{key:"getGraph",value:function(){return this.internals.graph}},{key:"setGraph",value:function(e){if(e===this.internals.graph)return this;var n=this.stateManager.hovered;if(n){var i,o=(i=re[n.kind].parent)!==null&&i!==void 0?i:n.kind,s=o==="node"?e.hasNode(n.key):e.hasEdge(n.key);s||this.stateManager.setHovered(null)}return this.unbindGraphHandlers(),this.checkEdgesEventsFrame!==null&&(cancelAnimationFrame(this.checkEdgesEventsFrame),this.checkEdgesEventsFrame=null),this.internals.graph=e,this.bindGraphHandlers(),this.refresh(),this}},{key:"getMouseCaptor",value:function(){return this.mouseCaptor}},{key:"getTouchCaptor",value:function(){return this.touchCaptor}},{key:"getDimensions",value:function(){return{width:this.width,height:this.height}}},{key:"getGraphDimensions",value:function(){var e=this.customBBox||this.nodeExtent;return{width:e.x[1]-e.x[0]||1,height:e.y[1]-e.y[0]||1}}},{key:"getNodeDisplayData",value:function(e){var n=this.internals.nodeDataCache[e];return n?Object.assign({},n):void 0}},{key:"getEdgeDisplayData",value:function(e){var n=this.internals.edgeDataCache[e];return n?Object.assign({},n):void 0}},{key:"getNodeState",value:function(e){return this.stateManager.getNodeState(e)}},{key:"getEdgeState",value:function(e){return this.stateManager.getEdgeState(e)}},{key:"getGraphState",value:function(){return this.stateManager.getGraphState()}},{key:"setNodeState",value:function(e,n){return this.stateManager.setNodeState(e,n),this}},{key:"setEdgeState",value:function(e,n){return this.stateManager.setEdgeState(e,n),this}},{key:"setGraphState",value:function(e){return this.stateManager.setGraphState(e),this}},{key:"_setPanning",value:function(e){this.stateManager.setGraphState({isPanning:e})}},{key:"_setZooming",value:function(e){this.stateManager.setGraphState({isZooming:e})}},{key:"setNodesState",value:function(e,n){return this.stateManager.setNodesState(e,n),this}},{key:"setEdgesState",value:function(e,n){return this.stateManager.setEdgesState(e,n),this}},{key:"updateContainerCursor",value:function(){var e=this.stateManager.hovered,n=this.resolvedStageStyle.cursor||"";this.container.style.cursor=e&&vs(this.internals,e)||n}},{key:"refreshStageStyle",value:function(){this.resolvedStageStyle=Ea(this.stylesDeclaration.stage,this.stateManager.graphState),this.resolvedStageStyle.background!==void 0&&(this.container.style.backgroundColor=this.resolvedStageStyle.background),this.updateContainerCursor()}},{key:"getNodeDisplayedLabels",value:function(){return new Set(this.labelRenderer.displayedNodeLabels)}},{key:"getEdgeDisplayedLabels",value:function(){return new Set(this.labelRenderer.displayedEdgeLabels)}},{key:"getSettings",value:function(){return N({},this.internals.settings)}},{key:"getSetting",value:function(e){return this.internals.settings[e]}},{key:"setSetting",value:function(e,n){return this.internals.settings[e]=n,zt(this.internals.settings),this.handleSettingsUpdate(),this.scheduleRefresh(),this}},{key:"updateSetting",value:function(e,n){return this.setSetting(e,n(this.internals.settings[e])),this}},{key:"setSettings",value:function(e){return this.internals.settings=N(N({},this.internals.settings),e),zt(this.internals.settings),this.handleSettingsUpdate(),this.scheduleRefresh(),this}},{key:"resize",value:function(e){var n=this.width,i=this.height;if(this.width=this.container.offsetWidth,this.height=this.container.offsetHeight,this.internals.pixelRatio=Yt(),this.width===0)if(this.internals.settings.allowInvalidContainer)this.width=1;else throw new Error("Sigma: Container has no width. You can set the allowInvalidContainer setting to true to stop seeing this error.");if(this.height===0)if(this.internals.settings.allowInvalidContainer)this.height=1;else throw new Error("Sigma: Container has no height. You can set the allowInvalidContainer setting to true to stop seeing this error.");if(!e&&n===this.width&&i===this.height)return this;for(var o=0,s=[this.mouseLayer].concat(H(Object.values(this.extraElements)));o<s.length;o++){var l=s[o];l.style.width=this.width+"px",l.style.height=this.height+"px"}return this.webGLContext&&(this.stageCanvas.setAttribute("width",this.width*this.internals.pixelRatio+"px"),this.stageCanvas.setAttribute("height",this.height*this.internals.pixelRatio+"px"),this.webGLContext.viewport(0,0,this.width*this.internals.pixelRatio,this.height*this.internals.pixelRatio)),this.emit("resize"),this}},{key:"clear",value:function(){return this.emit("beforeClear"),this.webGLContext.bindFramebuffer(WebGLRenderingContext.FRAMEBUFFER,null),this.webGLContext.clear(WebGLRenderingContext.COLOR_BUFFER_BIT),this.emit("afterClear"),this}},{key:"scheduleStateRefresh",value:function(){this.needToRefreshState=!0,this.scheduleRender()}},{key:"refreshState",value:function(){var e=this,n;this.stateManager.flushGraphStateFlags();var i=this.stateManager.graphStateChanged&&this.internals.nodeStyleAnalysis.dependency==="graph-state",o=this.stateManager.graphStateChanged&&this.edgeStyleAnalysis.dependency==="graph-state",s=!1;if(i)this.internals.graph.forEachNode(function(b){e.refreshNodeState(b)&&(s=!0)});else if(this.internals.nodeStyleAnalysis.dependency!=="static"){var l=M(this.stateManager.dirtyNodes),d;try{for(l.s();!(d=l.n()).done;){var h=d.value;this.refreshNodeState(h)&&(s=!0)}}catch(b){l.e(b)}finally{l.f()}}if(o)this.internals.graph.forEachEdge(function(b){e.refreshEdgeState(b)&&(s=!0)});else if(this.edgeStyleAnalysis.dependency!=="static"){var u=M(this.stateManager.dirtyEdges),c;try{for(u.s();!(c=u.n()).done;){var v=c.value;this.refreshEdgeState(v)&&(s=!0)}}catch(b){u.e(b)}finally{u.f()}}this.stateManager.graphStateChanged&&(n=this.stylesDeclaration)!==null&&n!==void 0&&n.stage&&this.refreshStageStyle(),this.stateManager.clearDirtyTracking(),s&&(this.pendingProcess="full")}},{key:"refreshNodeState",value:function(e){var n=this.internals.nodeDataCache[e];if(!n||this.nodeReducer){var i,o,s,l,d=(i=this.internals.nodeDataCache[e])===null||i===void 0?void 0:i.depth,h=(o=this.internals.nodeDataCache[e])===null||o===void 0?void 0:o.zIndex,u=(s=this.internals.nodeDataCache[e])===null||s===void 0?void 0:s.labelAttachment;this.updateNode(e);var c=this.internals.nodeDataCache[e];this.internals.attachmentManager&&c.labelAttachment!==u&&this.internals.attachmentManager.invalidateNode(e);var v;this.internals.nodeShapeMap&&this.internals.nodeGlobalShapeIds&&c.shape&&c.shape in this.internals.nodeShapeMap?v=this.internals.nodeGlobalShapeIds[this.internals.nodeShapeMap[c.shape]]:v=pt(c.shape||"circle"),(l=this.internals.nodeDataTexture).updateNode.apply(l,[e,c.x,c.y,c.size,v].concat(H(It(c)))),d&&c.depth!==d&&this.updateNodeDepthRanges(e,d,c.depth);var b=this.nodeProgramIndex[e];return b!==void 0&&(this.addNodeToProgram(e,b),this.nodeProgram.invalidateBuffers()),h!==void 0&&c.zIndex!==h}var m=this.internals.graph.getNodeAttributes(e),x=this.stateManager.getNodeState(e),g=n.size,f=n.shape,p=n.depth,y=n.zIndex,T=n.labelAttachment,_=n.rotationAlignment,E=n.labelRotationAlignment;_a(this.stylesDeclaration.nodes,m,x,this.stateManager.graphState,this.internals.graph,n),this.postEvaluateNode(n,m,x);var A=this.nodeGraphCoords[e],R=n.x!==A.x||n.y!==A.y;if(R&&(A.x=n.x,A.y=n.y),this.normalizationFunction.applyTo(n),this.internals.nodeShapeMap?(!n.shape||!(n.shape in this.internals.nodeShapeMap))&&(n.shape=Object.keys(this.internals.nodeShapeMap)[0]):this.nodeShapeSlug&&(n.shape=this.nodeShapeSlug),this.internals.attachmentManager&&n.labelAttachment!==T&&this.internals.attachmentManager.invalidateNode(e),Ie(this.internals.nodesWithForcedLabels,e,Ce(n)),Ie(this.internals.nodesWithBackdrop,e,Ca(n)),R||n.size!==g||n.shape!==f||n.rotationAlignment!==_||n.labelRotationAlignment!==E){var L,F;this.internals.nodeShapeMap&&this.internals.nodeGlobalShapeIds&&n.shape&&n.shape in this.internals.nodeShapeMap?F=this.internals.nodeGlobalShapeIds[this.internals.nodeShapeMap[n.shape]]:F=pt(n.shape||"circle"),(L=this.internals.nodeDataTexture).updateNode.apply(L,[e,n.x,n.y,n.size,F].concat(H(It(n))))}this.itemBuckets.nodes.set(e,n.depth),n.depth!==p&&this.updateNodeDepthRanges(e,p,n.depth);var C=this.nodeProgramIndex[e];return C!==void 0&&(this.addNodeToProgram(e,C),this.nodeProgram.invalidateBuffers()),n.zIndex!==y}},{key:"refreshEdgeState",value:function(e){var n=this.internals.edgeDataCache[e];if(!n||this.edgeReducer){var i=n?.depth,o=n?.zIndex;this.updateEdge(e);var s=this.internals.edgeDataCache[e];i&&s.depth!==i&&this.updateEdgeDepthRanges(e,i,s.depth);var l=this.edgeProgramIndex[e];return l!==void 0&&(this.addEdgeToProgram(e,l),this.edgeProgram.invalidateBuffers()),o!==void 0&&s.zIndex!==o}var d=this.internals.graph.getEdgeAttributes(e),h=this.stateManager.getEdgeState(e),u=n.depth,c=n.zIndex,v=n.size,b=n.path,m=n.selfLoopPath,x=n.parallelPath,g=n.head,f=n.tail;Sa(this.stylesDeclaration.edges,d,h,this.stateManager.graphState,this.internals.graph,n),this.postEvaluateEdge(n,d),this.applyEdgeSpread(e,n,h),Ie(this.internals.edgesWithForcedLabels,e,Ce(n)),this.itemBuckets.edges.set(e,n.depth),n.depth!==u&&this.updateEdgeDepthRanges(e,u,n.depth);var p=this.edgeProgramIndex[e];if(p!==void 0){var y=n.size!==v||n.path!==b||n.selfLoopPath!==m||n.parallelPath!==x||n.head!==g||n.tail!==f;if(y)this.addEdgeToProgram(e,p),this.edgeProgram.invalidateBuffers();else{var T=this.internals.graph.source(e),_=this.internals.graph.target(e),E=this.internals.nodeDataCache[T],A=this.internals.nodeDataCache[_],R=this.edgeTextureIndexCache[e];this.edgeProgram.process(Le(this.pickingState,"edge",e),p,E,A,n,R),this.edgeProgram.invalidateBuffers()}}return n.zIndex!==c}},{key:"refresh",value:function(e){var n=this,i=e?.skipIndexation!==void 0?e?.skipIndexation:!1,o=e?.schedule!==void 0?e.schedule:!1,s=!e||!e.partialGraph;if(s)this.clearEdgeIndices(),this.clearNodeIndices(),this.internals.graph.forEachNode(function(E){return n.addNode(E)}),this.edgeGroups.rebuild(),this.internals.graph.forEachEdge(function(E){return n.addEdge(E)}),this.pendingProcess="full";else{for(var l,d,h=((l=e.partialGraph)===null||l===void 0?void 0:l.nodes)||[],u=0,c=h?.length||0;u<c;u++){var v,b,m=h[u],x=(v=this.internals.nodeDataCache[m])===null||v===void 0?void 0:v.labelAttachment;if(this.updateNode(m),this.internals.attachmentManager&&((b=this.internals.nodeDataCache[m])!==null&&b!==void 0&&b.labelAttachment||x)&&this.internals.attachmentManager.invalidateNode(m),i){var g=this.nodeProgramIndex[m];if(g===void 0)throw new Error('Sigma: node "'.concat(m,`" can't be repaint`));this.addNodeToProgram(m,g)}}i&&h.length>0&&this.nodeProgram.invalidateBuffers();for(var f=(e==null||(d=e.partialGraph)===null||d===void 0?void 0:d.edges)||[],p=0,y=f.length;p<y;p++){var T=f[p];if(this.updateEdge(T),i){var _=this.edgeProgramIndex[T];if(_===void 0)throw new Error('Sigma: edge "'.concat(T,`" can't be repaint`));this.addEdgeToProgram(T,_)}}i&&f.length>0&&this.edgeProgram.invalidateBuffers(),!i&&this.pendingProcess!=="full"&&(this.pendingProcess=f.length>0?"full":"nodes")}return o?this.scheduleRender():this.render(),this}},{key:"scheduleRender",value:function(){var e=this;return this.renderFrame||(this.renderFrame=requestAnimationFrame(function(){e.render()})),this}},{key:"scheduleRefresh",value:function(e){return this.refresh(N(N({},e),{},{schedule:!0}))}},{key:"getViewportZoomedState",value:function(e,n){var i=this.camera.getState(),o=i.ratio,s=i.angle,l=i.x,d=i.y,h=this.internals.settings,u=h.minCameraRatio,c=h.maxCameraRatio;typeof c=="number"&&(n=Math.min(n,c)),typeof u=="number"&&(n=Math.max(n,u));var v=n/o,b={x:this.width/2,y:this.height/2},m=this.viewportToFramedGraph(e),x=this.viewportToFramedGraph(b);return{angle:s,x:(m.x-x.x)*(1-v)+l,y:(m.y-x.y)*(1-v)+d,ratio:n}}},{key:"viewRectangle",value:function(){var e=this.viewportToFramedGraph({x:0,y:0}),n=this.viewportToFramedGraph({x:this.width,y:0}),i=this.viewportToFramedGraph({x:0,y:this.height});return{x1:e.x,y1:e.y,x2:n.x,y2:n.y,height:n.y-i.y}}},{key:"framedGraphToViewport",value:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},i=!!n.cameraState||!!n.viewportDimensions||!!n.graphDimensions||!!n.padding,o=n.matrix||(i?Ae(n.cameraState||this.camera.getState(),n.viewportDimensions||this.getDimensions(),n.graphDimensions||this.getGraphDimensions(),n.padding||this.getStagePadding()):this.matrix),s=Je(o,e);return{x:(1+s.x)*this.width/2,y:(1-s.y)*this.height/2}}},{key:"viewportToFramedGraph",value:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},i=!!n.cameraState||!!n.viewportDimensions||!!n.graphDimensions||!!n.padding,o=n.matrix||(i?Ae(n.cameraState||this.camera.getState(),n.viewportDimensions||this.getDimensions(),n.graphDimensions||this.getGraphDimensions(),n.padding||this.getStagePadding(),!0):this.invMatrix),s=Je(o,{x:e.x/this.width*2-1,y:1-e.y/this.height*2});return isNaN(s.x)&&(s.x=0),isNaN(s.y)&&(s.y=0),s}},{key:"viewportToGraph",value:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};return this.normalizationFunction.inverse(this.viewportToFramedGraph(e,n))}},{key:"graphToViewport",value:function(e){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};return this.framedGraphToViewport(this.normalizationFunction(e),n)}},{key:"getGraphToViewportRatio",value:function(){var e={x:0,y:0},n={x:1,y:1},i=Math.sqrt(Math.pow(e.x-n.x,2)+Math.pow(e.y-n.y,2)),o=this.graphToViewport(e),s=this.graphToViewport(n),l=Math.sqrt(Math.pow(o.x-s.x,2)+Math.pow(o.y-s.y,2));return l/i}},{key:"computeNodeExtent",value:function(){var e=this.nodeGraphCoords,n=Object.keys(e);if(!n.length)return{x:[0,1],y:[0,1]};for(var i=1/0,o=-1/0,s=1/0,l=-1/0,d=0,h=n.length;d<h;d++){var u=e[n[d]],c=u.x,v=u.y;c<i&&(i=c),c>o&&(o=c),v<s&&(s=v),v>l&&(l=v)}return{x:[i,o],y:[s,l]}}},{key:"getBBox",value:function(){return this.nodeExtent}},{key:"getCustomBBox",value:function(){return this.customBBox}},{key:"setCustomBBox",value:function(e){return this.customBBox=e,this.scheduleRender(),this}},{key:"kill",value:function(){var e,n;this.emit("kill"),this.removeAllListeners(),this.unbindCameraHandlers(),window.removeEventListener("resize",this.activeListeners.handleResize),this.mouseCaptor.kill(),this.touchCaptor.kill(),this.unbindGraphHandlers(),this.clearIndices(),this.clearState(),this.internals.nodeDataCache={},this.internals.edgeDataCache={},this.renderFrame&&(cancelAnimationFrame(this.renderFrame),this.renderFrame=null);for(var i=this.container;i.firstChild;)i.removeChild(i.firstChild);this.nodeProgram.kill(),this.nodeFramePass.kill(),this.edgeProgram.kill(),this.edgeFramePass.kill(),this.internals.labelProgram.kill(),this.internals.edgeLabelProgram.kill(),this.internals.edgeLabelBackgroundProgram.kill(),this.internals.backdropProgram.kill(),this.internals.labelBackgroundProgram.kill(),(e=this.internals.attachmentProgram)===null||e===void 0||e.kill(),(n=this.internals.attachmentManager)===null||n===void 0||n.kill(),this.internals.attachmentProgram=null,this.internals.attachmentManager=null;var o=M(this.customLayerPrograms.values()),s;try{for(o.s();!(s=o.n()).done;){var l=s.value.program;l.kill()}}catch(u){o.e(u)}finally{o.f()}if(this.customLayerPrograms.clear(),this.sdfAtlas&&(this.sdfAtlas=null),this.internals.nodeDataTexture&&(this.internals.nodeDataTexture.kill(),this.internals.nodeDataTexture=null),this.internals.nodeFrameTexture&&(this.internals.nodeFrameTexture.kill(),this.internals.nodeFrameTexture=null),this.internals.edgeDataTexture&&(this.internals.edgeDataTexture.kill(),this.internals.edgeDataTexture=null),this.internals.edgeFrameTexture&&(this.internals.edgeFrameTexture.kill(),this.internals.edgeFrameTexture=null),this.webGLContext){var d;(d=this.webGLContext.getExtension("WEBGL_lose_context"))===null||d===void 0||d.loseContext(),this.webGLContext=null}this.mouseLayer.remove();for(var h in this.extraElements)this.extraElements[h].remove();this.extraElements={}}},{key:"scaleSize",value:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:1,n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:this.camera.ratio;return e/this.internals.settings.zoomToSizeRatioFunction(n)*(this.getSetting("itemSizesReference")==="positions"?n*this.graphToViewportRatio:1)}},{key:"getStageCanvas",value:function(){return this.stageCanvas}},{key:"getMouseLayer",value:function(){return this.mouseLayer}}])})(ra),zs=ks;export{zs as S,q as _,Is as c};

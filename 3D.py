#!/usr/bin/env python3
"""Atlas 3D game-generation policy and quality guard.

This module is intentionally dependency-free. server.py loads it dynamically
because the published filename is "3D.py".
"""

from __future__ import annotations

import re
from typing import Dict, List


GAME_QUALITY_DEFAULT = "max"
GAME_ENGINE = "Three.js"
GAME_THINKING_SECONDS = 30
GAME_AUTO_REPAIR = True
GAME_MAX_REPAIR_PASSES = 2
GAME_BROWSER_TEST_SECONDS = 7
GAME_BROWSER_TEST_TIMEOUT_SECONDS = 18


GAME_3D_SYSTEM_PROMPT = r"""
# ATLAS 3D GAME CREATION — MAX QUALITY AGENT

You are Atlas acting as a 3D game-building agent, not merely a code autocomplete system.
The user activated Create Game. Your job is to build the complete playable browser game requested by the user.

## PRIMARY QUALITY TARGET
- Quality mode is ALWAYS `MAX` by default.
- Treat words such as realistic, realistic 3D, photorealistic, hyperrealistic, cinematic, AAA, detailed,
  high fidelity, lifelike, product-rendered, or similar requests as explicit requests for the highest
  visual fidelity that a single browser file can reasonably deliver.
- Never intentionally downgrade a realistic request into a blockout, wireframe, placeholder scene, or
  collection of colored cubes just because primitives are easier.
- A few simple primitives are allowed for invisible colliders, tiny hidden helpers, debug-only objects,
  or distant background details. They must NOT be the primary visible representation of a requested hero
  object such as a car, character, building, aircraft, weapon, furniture item, or other focal asset.

## REALISM-FIRST DECISION TREE
When the user asks for a realistic hero object:
1. Prefer a real, reachable GLTF/GLB model when a trustworthy public asset URL is known or supplied by live search context.
2. Use Three.js GLTFLoader with the same pinned Three.js version as the core import.
3. When the asset benefits from compression, use matching Draco/KTX2/Meshopt decoders available from the same Three.js version.
4. Validate the asset at runtime and keep a robust procedural fallback so the game still opens if an external asset fails to load.
5. For vehicle requests, do NOT claim a procedural mesh is equivalent to an authored AAA vehicle asset. Spend the model budget on smooth surfacing, materials, lighting, and camera rather than decorative code that does not improve the rendered result.
6. For the fallback, use curved / continuous geometry rather than box stacks:
   - ExtrudeGeometry
   - LatheGeometry
   - TubeGeometry
   - CatmullRomCurve3
   - custom BufferGeometry
   - rounded/high-segment primitives only where visually appropriate
5. Never replace the requested object with a cube merely because an external model failed.


## THREE.JS COMPATIBILITY CONTRACT
- Pin one Three.js version for the entire generated file; never use `@latest` and never mix addon versions.
- Use WebGL2 with `WebGLRenderer` as the default browser compatibility baseline. Do not make WebGPU required.
- `GLTFLoader`, `OrbitControls`, `EffectComposer`, and other examples components are addons and must be imported explicitly from the matching Three.js addon path at the same version as core Three.js.
- Use `GLTFLoader` for glTF 2.0 assets and register Draco/KTX2/Meshopt decoders only when the asset actually needs them.
- Use `EffectComposer` only with `WebGLRenderer`, and make post-processing optional when it threatens stability or frame rate.
- Treat WebGPU as optional; if a WebGPU feature is used, retain a reliable WebGL2 fallback.
- Do not use Node.js-only APIs, npm imports, bundler-only paths, local module files, or server-side Three.js APIs inside the generated page.
- Prefer browser-safe APIs: WebGL2, requestAnimationFrame/setAnimationLoop, DOM events, Pointer Lock, Web Audio, Fetch, Canvas, and standard JavaScript.
- Keep every loader, control, material, post-processing pass, and renderer feature mutually compatible with the pinned version.

## PBR MATERIALS
For realistic scenes:
- Prefer MeshStandardMaterial or MeshPhysicalMaterial.
- Use physically meaningful roughness and metalness values.
- Use normal maps, roughness maps, metalness maps, emissive maps, clearcoat, sheen, transmission,
  or environment reflections when appropriate and when the chosen asset provides them.
- Use sRGB color handling for color textures and correct output color space.
- Use tone mapping suitable for a cinematic/high-fidelity scene.
- Avoid flat unlit MeshBasicMaterial for hero objects.
- Do not make every object equally glossy; material response should match metal, paint, rubber, glass,
  leather, fabric, plastic, stone, vegetation, and other surfaces.

## LIGHTING + ENVIRONMENT
For MAX visual quality:
- Use a coherent key/fill/rim or sun/ambient lighting design.
- Prefer environment lighting / HDRI when available.
- Configure renderer shadows deliberately and use soft/PCF-style shadow settings when supported.
- Add contact-shadow cues through real shadows, AO-style techniques, or carefully designed geometry.
- Use fog/atmospheric depth only when it improves the scene.
- Keep the background, sky, exposure, color grading, and reflections coherent with the scene.

## CAMERA + PRESENTATION
- Use a cinematic camera where appropriate.
- Compose the requested hero object as the visual focal point.
- Use realistic perspective and sensible camera distance.
- For speed requests such as 220 km/h, model believable vehicle speed and translate the request into camera/framing/shutter/motion cues rather than treating the number as an image-resolution setting.
- For “expensive camera” language, translate it into cinematic sensor/framing, focal length, exposure, depth of field, motion blur, and color response; camera price itself is not a rendering parameter.
- Add subtle camera motion only when it improves the experience.
- Preserve a stable responsive camera on resize.

## HERO VEHICLES: REALISTIC CAR / FERRARI RULES
When the user asks for a realistic sports car, supercar, Ferrari, or similar vehicle:
- Treat the vehicle as the hero asset and give it the majority of the visual-detail budget.
- Prefer a real high-detail GLB/GLTF over procedural geometry whenever a credible, reachable asset is available.
- Preserve authored textures/materials from the asset; do not replace them with one flat body color.
- For Ferrari requests, use a recognizable, model-specific automotive silhouette if an exact or clearly identified model is requested. Do not substitute an unrelated generic car while calling it Ferrari.
- The car must visibly read as a real automotive form, not stacked boxes.
- Prefer a validated GLB/GLTF vehicle asset when one is confidently available.
- If no reliable asset is available, build a procedural supercar body with smooth curves and continuous
  surfaces. Use a detailed body shell, hood, roofline, fenders, side skirts, bumpers, intakes,
  headlights, glass, mirrors, wheels, tires, rims, brakes, and interior cues.
- Use separate materials for painted bodywork, rubber tires, glass, metal rims/brakes, and dark trim.
- Wheels should be round, high-segment, correctly oriented, and visibly attached to the body.
- Use realistic proportions, panel gaps/line cues, reflections, and contact with the ground.
- Never represent the main car body with BoxGeometry stacks. BoxGeometry is allowed for tiny hidden helpers or colliders, but the visible hero body must use smooth/curved geometry or a validated GLB/GLTF, with structurally obvious body, wheel/tire, lights/glass, and trim components.

## CHARACTER / ENVIRONMENT RULES
For characters, prefer animated GLB/GLTF models when available. For environments, use layered terrain,
modular architectural pieces, vegetation instances, props, and atmospheric lighting rather than a few
large cubes. Procedural geometry is welcome when it is smooth, detailed, and materially coherent.

## ASSET LOADING RULES
- If a public GLB/GLTF asset is used, use a stable URL only when it is known/credible.
- Do NOT invent URLs just to satisfy this rule.
- The game must remain runnable if the asset cannot load.
- Put loading/error handling in the game and switch to the procedural fallback cleanly.
- Do not split the final result into multiple local files.

## HIGH-END RENDERING CHECKLIST
For realistic 3D / vehicle requests, also consider when compatible with the generated scene:
- WebGL2 as the reliability baseline, with WebGPU only when the chosen APIs/imports are actually compatible.
- Correct renderer pixel-ratio limits and adaptive quality so mobile devices remain usable.
- ACES/AgX/Neutral tone mapping as appropriate to the pinned Three.js version.
- PMREM-prefiltered environment lighting for physically based reflections.
- MeshPhysicalMaterial clearcoat for automotive paint, realistic glass transmission when appropriate, and distinct rubber/metal materials.
- Soft shadows, contact cues, and coherent exposure.
- Optional post-processing only when the implementation is stable and performance-conscious.
- No fake “4K” labels: maximize actual render quality through geometry, textures, lighting, and output resolution instead.

## INTERNAL GAME-ARCHITECTURE PASS
Before writing code, silently design the game as a small production-ready system. Do not expose this planning text. Identify the genre, core loop, player goal, win/lose conditions, scene architecture, asset strategy, gameplay systems, UI, audio, and performance budget. Decide which requested features need real physics, collisions, animation, AI, navigation, particles, audio, or post-processing. Allocate detail to the hero object and gameplay-critical environment first. Choose stable browser-compatible APIs and design fallbacks before optional external assets.

## GAMEPLAY SYSTEMS
When the request implies a real game, implement the actual core loop rather than fake interactions: input -> simulation/physics -> AI/interactions -> camera -> render -> UI/audio feedback. Use frame-rate-independent movement with delta time. Implement requested collisions, gravity, friction, vehicle handling, projectiles, triggers, or other physics functionally. Make controls discoverable and show relevant state. Never ship TODOs, dead buttons, fake progress, or interactions that only look functional.

## NPC + AI SYSTEMS
When enemies, traffic, pedestrians, animals, companions, or other agents are requested, implement a lightweight real behavior/state system. Use appropriate states such as idle, patrol, chase, attack, flee, search, return, or disabled. Use waypoint/path logic or steering where navigation is requested, with perception/range/cooldowns and simple avoidance when appropriate. Keep AI updates efficient.

## CAMERA + FEEDBACK SYSTEMS
Choose camera behavior from the genre: racing uses smooth chase/follow framing and speed-aware feedback; FPS uses stable first-person framing; platformers use smooth follow/look-ahead; third-person/action uses orbit/follow with collision avoidance. Add subtle UI/audio/screen feedback for important gameplay events when appropriate.

## AUDIO
When sound or music is requested or clearly useful, implement a lightweight event-driven audio system with mute/volume control. Do not invent unavailable asset URLs; use safe Web Audio synthesis or known browser-safe resources when appropriate.

## RESPONSIVE + DEVICE QUALITY
Adapt pixel ratio, shadow quality, LOD, particles, and repeated-object detail to device constraints without destroying requested quality. Keep desktop quality high while preventing mobile from becoming unusable. Handle resize and visibility changes gracefully.

## AUTOMATED SELF-TEST MINDSET
Before final output, silently verify first-frame rendering, immediate player start, requested controls, game-state transitions, collisions/game rules, NPC state transitions, camera resize behavior, UI state feedback, asset fallbacks, and obvious console/runtime failures. Repair failures before returning the game.

## PERFORMANCE WITHOUT SACRIFICING QUALITY
MAX does not mean careless:
- Prefer instancing for repeated vegetation/props.
- Reuse materials and geometries where possible.
- Avoid creating new allocations every animation frame.
- Use reasonable texture sizes for mobile browsers.
- Use LOD or lower-detail distant objects when useful.
- Keep shadows limited to important lights/objects.
- Use efficient animation loops and event handlers.
- Do not disable quality features merely to make the implementation shorter.

## GAMEPLAY
The result must be an actual playable experience when the request implies gameplay:
- controls should be obvious
- the animation loop must be stable
- interactions must work
- collisions/physics/game rules must be implemented when requested
- UI should communicate controls/state
- no TODOs, placeholder comments, fake buttons, dead controls, or omitted sections

## SINGLE-FILE CONTRACT
Return one complete runnable `index.html` inside exactly one fenced HTML code block.
The response is shown in chat, so format it in three parts in this exact order:
1. INTRODUCTION — 1 to 3 concise sentences describing the app/game you built.
2. CODE — exactly one fenced `html` block containing the complete `index.html`.
3. ENDING — 1 to 3 concise sentences explaining what you implemented and the important working features.
Do not put executable code outside the single HTML fence. Do not create additional source files.

The HTML itself must contain:
- doctype
- HTML
- CSS
- JavaScript
- scene setup
- assets/loading logic
- lighting
- animation/game loop
- controls
- gameplay
- UI
- responsive resize handling
- error/fallback handling

Use a pinned Three.js CDN import and matching example-module imports when needed.
The final file must run directly in a modern browser without npm, a bundler, or additional local source files.

## PRE-DELIVERY SELF-CHECK
Before finalizing, mentally verify:
- The HTML parses as a complete document and contains runnable JavaScript.
- The main scene initializes without relying on unavailable local files.
- External GLB/GLTF loading has a visible runtime error/fallback path.
- The first frame can render even when an optional asset or enhancement fails.
- Requested controls, gameplay, resize handling, and UI are wired to live code rather than placeholders.
- No console/runtime error is intentionally left unresolved.

## ANTI-BLOCKOUT CHECK
Before finalizing, mentally inspect the generated scene:
- Is the requested hero object represented by recognizable, smooth, detailed 3D geometry or a real GLB/GLTF?
- Are PBR materials used for realistic objects?
- Are lighting, reflections, shadows, camera composition, and environment intentionally designed?
- Would a user looking at the preview immediately describe it as a detailed 3D scene rather than a greybox/blockout?
- For a realistic car, does the first-frame composition make the vehicle immediately recognizable with believable reflections, materials, wheels, glass, and contact with the road?
If not, improve it before returning the final file.

## OUTPUT DISCIPLINE
The application will hold the response until the complete model response is finished.
Do not narrate hidden reasoning or progress.
Return exactly three visible parts in this order:
1. A brief introduction about the app/game.
2. One and only one fenced `html` code block containing the complete runnable `index.html`.
3. A brief ending explaining what the AI implemented.
Keep the introduction and ending outside the code fence. Never return multiple HTML/code fences.
"""


def split_game_response(text: str) -> Dict[str, str]:
    """Parse a Create Game reply into visible prose plus the complete HTML document."""
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        raise ValueError("Atlas returned an empty game response.")

    # Prefer a fenced HTML block. Intro/ending are whatever visible prose surrounds it.
    match = re.search(r"```(?:html?|xhtml)?[ \t]*(?:\n|$)([\s\S]*?)```", raw, re.I)
    if match:
        code = match.group(1).strip()
        intro = raw[:match.start()].strip()
        ending = raw[match.end():].strip()
    else:
        # Be tolerant of a model that omitted fences, as long as it returned a full document.
        doctype = re.search(r"<!doctype\s+html\b", raw, re.I)
        html_open = re.search(r"<html(?:\s[^>]*)?>", raw, re.I)
        html_close = re.search(r"</html\s*>", raw[doctype.start():] if doctype else raw, re.I)
        if not doctype or not html_open or not html_close:
            raise ValueError("Generated game HTML was incomplete.")
        start = doctype.start()
        after = raw[start:]
        close = re.search(r"</html\s*>", after, re.I)
        if not close:
            raise ValueError("Generated game HTML was incomplete.")
        end = start + close.end()
        code = raw[start:end].strip()
        intro = raw[:start].strip()
        ending = raw[end:].strip()

    if not re.search(r"<!doctype\s+html\b", code, re.I) or not re.search(r"<html(?:\s|>)", code, re.I) or not re.search(r"</html\s*>", code, re.I):
        raise ValueError("Generated game HTML was incomplete.")

    return {"intro": intro, "html": code, "ending": ending}


def extract_game_html(text: str) -> str:
    return split_game_response(text)["html"]


def is_realism_request(prompt: str) -> bool:
    return bool(re.search(
        r"\b(realistic|hyperrealistic|photorealistic|photoreal|cinematic|lifelike|high[- ]fidelity|aaa|"
        r"ultra[- ]realistic|detailed|real[- ]world|real[- ]looking)\b",
        str(prompt or ""), re.I
    ))


def is_vehicle_request(prompt: str) -> bool:
    return bool(re.search(
        r"\b(car|vehicle|ferrari|lamborghini|porsche|supercar|sports car|automobile|roadster|coupe|sedan)\b",
        str(prompt or ""), re.I
    ))


def inspect_game_code(html: str, prompt: str = "") -> Dict[str, object]:
    code = str(html or "")
    low = code.lower()
    realism = is_realism_request(prompt)
    vehicle = is_vehicle_request(prompt)
    issues: List[str] = []

    box_count = len(re.findall(r"\b(?:new\s+)?THREE\.BoxGeometry\b", code, re.I))
    rich_geometry = bool(re.search(r"\b(?:ExtrudeGeometry|LatheGeometry|TubeGeometry|CatmullRomCurve3|BufferGeometry|GLTFLoader)\b", code, re.I))
    pbr = bool(re.search(r"\b(?:MeshStandardMaterial|MeshPhysicalMaterial)\b", code))
    lighting = bool(re.search(r"\b(?:DirectionalLight|HemisphereLight|RectAreaLight|SpotLight|PointLight)\b", code))
    shadows = bool(re.search(r"\b(?:castShadow|receiveShadow|shadow\.mapSize)\b", code))
    tone = bool(re.search(r"\b(?:toneMapping|ACESFilmicToneMapping|outputColorSpace|SRGBColorSpace)\b", code))
    renderer = bool(re.search(r"\bWebGLRenderer\b", code))
    loop = bool(re.search(r"\brequestAnimationFrame\b|\bsetAnimationLoop\b", code))
    gltf = "gltfloader" in low
    external_asset = bool(re.search(r"https?://[^\s\"']+\.(?:glb|gltf)(?:[?#][^\s\"']*)?", code, re.I))
    fallback = bool(re.search(r"\b(?:fallback|onError|catch\s*\(|loadError|failed to load)\b", code, re.I))
    controls = bool(re.search(r"(?:addEventListener\s*\(\s*[\"'](?:keydown|keyup|pointerdown|pointerup|mousedown|mouseup|touchstart|touchend)|PointerLockControls|OrbitControls|KeyboardEvent)", code, re.I))
    resize = bool(re.search(r"(?:addEventListener\s*\(\s*[\"']resize[\"']|onresize|setSize\s*\()", code, re.I))
    ui = bool(re.search(r"(?:<button\b|<div\b[^>]*(?:hud|ui|controls|score|health)|innerHTML\s*=|textContent\s*=)", code, re.I))
    physics = bool(re.search(r"(?:velocity|gravity|acceleration|friction|collision|collider|raycast|rigidbody|rapier|cannon|ammo|physics)", low, re.I))
    ai = bool(re.search(r"(?:npc|enemy|patrol|waypoint|chase|attack|flee|pathfinding|state\s*machine)", low, re.I))
    audio = bool(re.search(r"(?:AudioContext|Howler|playSound|sound|music|sfx)", code, re.I))
    if not re.search(r"<!doctype\s+html\b", code, re.I):
        issues.append("missing doctype")
    if not renderer:
        issues.append("missing WebGL renderer")
    if not loop:
        issues.append("missing stable animation loop")
    # Reject unstable Three.js delivery patterns that commonly break generated single-file games.
    if re.search(r"three@latest|three\.min\.js\?[^\n]*latest|jsdelivr\.com/npm/three@latest", code, re.I):
        issues.append("Three.js import is unpinned; use one fixed Three.js version")
    if re.search(r"(?:WebGPU|WebGPURenderer)\b", code, re.I) and not re.search(r"WebGLRenderer", code, re.I):
        issues.append("WebGPU is required without a WebGLRenderer fallback")
    if gltf and not re.search(r"three/addons/loaders/GLTFLoader\.js|examples/jsm/loaders/GLTFLoader\.js", code, re.I):
        issues.append("GLTFLoader import is not using a standard Three.js addon path")

    if realism:
        if not pbr:
            issues.append("realistic request without PBR materials")
        if not lighting:
            issues.append("realistic request without deliberate 3D lighting")
        if not shadows:
            issues.append("realistic request without shadow setup")
        if not tone:
            issues.append("realistic request without color-management/tone-mapping setup")
        if not rich_geometry:
            issues.append("realistic request without smooth/hero geometry or GLTF loading")
        if box_count >= 8 and not rich_geometry:
            issues.append("scene appears blockout-like because BoxGeometry dominates")

    if vehicle:
        # Vehicle validation must recognize normal Three.js naming and geometry patterns without
        # rejecting a valid model simply because it uses different camelCase/plural names.
        component_patterns = [
            r"\b(?:front|rear|left|right|all)?(?:[_-]?(?:wheel|wheels)|wheel(?:fl|fr|rl|rr|[0-9]+))\b",
            r"\b(?:front|rear|left|right|all)?(?:[_-]?(?:tire|tires|tyre|tyres))\b",
            r"\b(?:front|rear|left|right)?[_-]?(?:headlight|headlights|headlamp|headlamps)\b",
            r"\b(?:front|rear)?[_-]?(?:windshield|windshields|windscreen|windscreens)\b",
            r"\b(?:front|rear|left|right)?[_-]?(?:fender|fenders|wing|wings)\b",
            r"\b(?:hood|bonnet)\b",
            r"\b(?:front|rear)?[_-]?(?:bumper|bumpers)\b",
            r"\b(?:side|door)?[_-]?(?:mirror|mirrors|sideMirrors)\b",
            r"\b(?:roof|cockpit|cabin|interior)\b",
            r"\b(?:body|bodyShell|chassis|shell|frame)\b",
            r"\b(?:grille|grill|spoiler|diffuser|exhaust|brake|brakes|rim|rims)\b",
        ]
        hero_terms = sum(bool(re.search(p, code, re.I)) for p in component_patterns)
        curved_geometry = bool(re.search(
            r"\b(?:CylinderGeometry|SphereGeometry|TorusGeometry|CapsuleGeometry|RoundedBoxGeometry|\n            ExtrudeGeometry|LatheGeometry|TubeGeometry|CatmullRomCurve3|CurvePath|ShapeGeometry|ParametricGeometry)\b",
            code, re.I | re.X
        ))
        custom_geometry = bool(re.search(r"\bBufferGeometry\b|\b(?:vertices|positionAttribute|setAttribute)\b", code, re.I))
        asset_structure_ok = bool(gltf and external_asset and fallback)
        vehicle_structure_ok = asset_structure_ok or hero_terms >= 3 or curved_geometry or custom_geometry

        # Only fail this check when the candidate exposes essentially no recognizable vehicle
        # structure at all. A real GLB may keep all component names inside the asset.
        if not vehicle_structure_ok:
            issues.append("vehicle lacks enough recognizable component structure")

        # A few BoxGeometry nodes are normal for colliders/trim. Treat boxes as a blockout only
        # when they dominate a vehicle candidate and there is no curved/custom/model geometry.
        primitive_only = (
            box_count >= 8
            and not gltf
            and not curved_geometry
            and not custom_geometry
            and hero_terms < 6
        )
        if primitive_only:
            issues.append("vehicle is likely represented by primitive blocks")
        if external_asset and not fallback:
            issues.append("external vehicle asset has no obvious fallback/error path")

    prompt_low = str(prompt or '').lower()
    gameplay_request = bool(re.search(r"\b(game|playable|race|racing|drive|shoot|platform|fight|combat|survive|collect|enemy|npc|traffic|mission|level|score|win|lose)\b", prompt_low))
    physics_request = bool(re.search(r"\b(physics|collision|collisions|gravity|suspension|drift|drifting|friction|rigid body|rigidbody|vehicle handling)\b", prompt_low))
    ai_request = bool(re.search(r"\b(enemy|enemies|npc|traffic|pedestrian|companion|ai opponents|bots|patrol|chase)\b", prompt_low))
    audio_request = bool(re.search(r"\b(sound|sounds|audio|music|sfx|engine sound|footsteps)\b", prompt_low))
    if gameplay_request and not controls: issues.append("gameplay request without recognizable input/control handling")
    if gameplay_request and not resize: issues.append("gameplay request without responsive resize handling")
    if gameplay_request and not ui: issues.append("playable game without recognizable gameplay UI/state feedback")
    if physics_request and not physics: issues.append("requested physics/collision system not recognizable")
    if ai_request and not ai: issues.append("requested NPC/AI behavior not recognizable")
    if audio_request and not audio: issues.append("requested audio system not recognizable")

    # Strong but non-failing hints for any 3D game.
    if not pbr and realism:
        pass

    return {
        "ok": not issues,
        "issues": issues,
        "box_count": box_count,
        "realism_request": realism,
        "vehicle_request": vehicle,
        "has_gltf_loader": gltf,
        "has_curved_geometry": curved_geometry if vehicle else False,
        "has_custom_geometry": custom_geometry if vehicle else False,
        "vehicle_component_terms": hero_terms if vehicle else 0,
        "has_pbr": pbr,
        "has_shadows": shadows,
        "has_tone_mapping": tone,
        "has_controls": controls,
        "has_resize": resize,
        "has_ui": ui,
        "has_physics": physics,
        "has_ai": ai,
        "has_audio": audio,
        "gameplay_request": gameplay_request,
        "physics_request": physics_request,
        "ai_request": ai_request,
        "audio_request": audio_request,
        "score": len(issues),
        "needs_repair": bool(issues) and (realism or vehicle or gameplay_request or physics_request or ai_request or audio_request),
    }


def build_repair_prompt(user_prompt: str, html: str, report: Dict[str, object]) -> str:
    issues = ", ".join(str(x) for x in report.get("issues") or [])
    runtime_errors = str(report.get("runtime_errors") or "").strip()
    runtime_section = ("\nBrowser/runtime test findings:\n" + runtime_errors) if runtime_errors else ""
    return f"""
# ATLAS 3D QUALITY REPAIR — MAX QUALITY

THREE.JS COMPATIBILITY REQUIREMENTS
- Use one pinned Three.js version and matching addon versions. Never use @latest.
- Prefer WebGLRenderer/WebGL2 as the stable baseline; WebGPU must never be the only renderer.
- Import GLTFLoader, OrbitControls, EffectComposer, and other addons from the matching standard addon path.
- Keep external asset loading behind a robust fallback; never leave the first frame dependent on an optional asset.

The first game draft needs a visual-quality repair before delivery.

User request:
{str(user_prompt or "").strip()}

Detected issues:
{issues}{runtime_section}

Repair requirements:
- Keep the requested concept and every useful working feature.
- Do NOT rewrite into a blockout.
- Make realistic hero objects use GLTF/GLB or smooth continuous procedural geometry.
- Use PBR materials, deliberate lighting, correct tone mapping/color space, realistic shadows,
  coherent camera composition, reflections/environment lighting, and responsive presentation.
- For a realistic car/Ferrari, ensure the main body is smooth and continuous, with believable
  wheels/tires/rims, lights, glass, trim, proportions, and materials. Do not build the hero car
  from stacked cubes.
- Preserve actual gameplay and controls.
- If the report identifies missing controls, resize handling, UI/state feedback, physics/collision behavior, NPC/AI behavior, or audio, repair those systems as functional implementations rather than cosmetic placeholders.
- Preserve the existing working game architecture and repair only what is necessary; do not replace working systems with simplified demos.
- Keep the final result as one self-contained runnable index.html.
- Do not invent asset URLs. If an asset URL is uncertain, use a strong procedural fallback instead.
- Return a brief introduction, then exactly one fenced HTML code block, then a brief ending. Do not put code outside the fence.

CURRENT GAME:
```html
{html}
```
""".strip()


__all__ = [
    "GAME_QUALITY_DEFAULT",
    "GAME_ENGINE",
    "GAME_THINKING_SECONDS",
    "GAME_AUTO_REPAIR",
    "GAME_MAX_REPAIR_PASSES",
    "GAME_3D_SYSTEM_PROMPT",
    "split_game_response",
    "extract_game_html",
    "inspect_game_code",
    "build_repair_prompt",
]

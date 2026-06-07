from __future__ import annotations

import json
import os
import re
import socket
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .errors import PipelineError
from .input_parser import clean_text
from .validator import validate_script


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.6-plus"
DEFAULT_TIMEOUT_SECONDS = 240
DEFAULT_MAX_SOURCE_CHARS = 12000
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def generate_script_with_llm(source: str, title: str, script_format: str) -> dict[str, Any]:
    config = LLMConfig.from_env()
    cleaned = clean_text(source)
    if not cleaned:
        raise PipelineError("输入文本为空。")

    payload = {
        "model": config.model,
        "messages": build_messages(cleaned, title, script_format, config.max_source_chars),
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }
    response = post_chat_completion(config, payload)
    content = extract_message_content(response)
    script = parse_script_json(content)
    script = repair_script(script, cleaned, title, script_format)
    errors = validate_script(script)
    if errors:
        raise PipelineError("在线模型返回结果未通过 Schema 校验：" + "；".join(errors))
    return script


class LLMConfig:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        provider: str,
        ssl_cert_file: str = "",
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_source_chars: int = DEFAULT_MAX_SOURCE_CHARS,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider = provider
        self.ssl_cert_file = ssl_cert_file
        self.timeout_seconds = timeout_seconds
        self.max_source_chars = max_source_chars

    @classmethod
    def from_env(cls) -> "LLMConfig":
        env_file = load_dotenv()
        api_key = read_config_value("LLM_API_KEY", env_file).strip()
        if not api_key:
            raise PipelineError(
                "缺少 LLM_API_KEY。请在启动后端的同一个终端 export LLM_API_KEY，"
                "或在项目根目录创建 .env。"
            )
        return cls(
            api_key=api_key,
            base_url=read_config_value("LLM_BASE_URL", env_file).strip() or DEFAULT_BASE_URL,
            model=read_config_value("LLM_MODEL", env_file).strip() or DEFAULT_MODEL,
            provider=read_config_value("LLM_PROVIDER", env_file).strip() or "qwen",
            ssl_cert_file=resolve_ssl_cert_file(env_file),
            timeout_seconds=read_int_config(
                "LLM_TIMEOUT_SECONDS", env_file, DEFAULT_TIMEOUT_SECONDS
            ),
            max_source_chars=read_int_config(
                "LLM_MAX_SOURCE_CHARS", env_file, DEFAULT_MAX_SOURCE_CHARS
            ),
        )


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists() or not env_path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def read_config_value(name: str, dotenv_values: dict[str, str]) -> str:
    return os.getenv(name, dotenv_values.get(name, ""))


def read_int_config(name: str, dotenv_values: dict[str, str], default: int) -> int:
    value = read_config_value(name, dotenv_values).strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def resolve_ssl_cert_file(dotenv_values: dict[str, str]) -> str:
    configured = read_config_value("SSL_CERT_FILE", dotenv_values).strip()
    if configured:
        return configured
    try:
        import certifi
    except ImportError:
        return ""
    return certifi.where()


def build_messages(
    source: str,
    title: str,
    script_format: str,
    max_source_chars: int = DEFAULT_MAX_SOURCE_CHARS,
) -> list[dict[str, str]]:
    source_for_prompt = source[:max_source_chars]
    if len(source) > max_source_chars:
        source_for_prompt += "\n\n[提示：原文过长，当前在线请求已截取前段文本用于生成初稿。]"
    system_prompt = (
        "你是一位顶级剧本医生和电影导演。你的任务是将小说文本改编为具有高度电影感的、分镜导向的结构化剧本 JSON。\n\n"
        "【核心创作准则（必须严格遵守）】:\n"
        "1. 视觉驱动：严禁描写人物内心活动（如：感到、认为、意识到、想起）。所有心理必须转化为：肢体动作、环境互动、道具细节、微表情或镜头调度。\n"
        "2. 潜台词博弈：人物在对话时必须带有隐藏目的。绝不能直接陈述事实，必须通过侧面迂回、试探、反问或沉默来揭示意图。让对话在“说事”的同时完成“关系博弈”。\n"
        "3. 镜头语言：禁止使用“特写转中景”这类万能模板。根据场景的环境氛围（如：阴冷、嘈杂、压抑）设计具体的构图、光影及运镜方式（例如：低角度仰拍突出压迫感、手持长镜头捕捉不安感）。\n"
        "4. 一致性锚点：在所有 action beat 中，必须嵌入人物的 visual_anchor（视觉识别特征），确保角色在不同场景间具有视觉连续性。\n"
        "5. 结构化思维：每个场景必须具备：明确的行为动机 (motivation)、场景冲突焦点 (subtext_conflict)、以及独特的视觉叙事策略 (visual_narrative_plan)。"
        "【分镜设计多样化准则 (必须严格执行)】:\n"
        "1. 禁止同质化：绝不允许每个场景都使用“特写转中景”。\n"
        "2. 强制视觉设计：在撰写每个 scene 时，必须从以下视觉菜单中选择一套方案，或进行创造性的组合：\n"
        "   - 方案A（压抑感）：低角度仰拍，阴影遮盖人物半张脸，固定机位，长镜头。\n"
        "   - 方案B（不安感）：手持晃动感，快速剪辑，特写物品（如水滴、裂痕），浅景深模糊背景。\n"
        "   - 方案C（对峙感）：过肩镜头（OTS），对称式构图，冷暖对比色调。\n"
        "   - 方案D（孤独感）：大广角空镜，人物被巨大空间包围，极度缓慢的推镜头。\n"
        "方案E（恐惧感）：低角度仰拍结合突然的快速变焦推进，狭窄空间内幽闭的构图，单一冷色光源（如蓝绿或暗红），人物瞳孔特写与环境死寂的空镜快速交替。\n"
        "方案F（悬疑感）：倾斜构图，缓慢且安静的轨道横移，半透明遮挡物（如磨砂玻璃、薄纱）后的模糊人影，长焦镜头压缩空间让观众感到被窥视，细节特写（如门锁转动、烟灰掉落）拉长时间。\n"

        "方案G（悲伤感）：柔光、低饱和度甚至褪色，固定机位拍摄人物侧面或背影，空镜长拍（如空椅、枯叶、缓慢坠落的雨滴），浅景深分离人物与环境，溶解式转场。\n"

        "方案H（浪漫感）：柔焦与逆光光晕，暖色调（琥珀金、柔粉），浅景深双人特写交替，极慢的推轨靠近角色，手持微晃但呈呼吸感，对称式眼神交汇构图。\n"

        "方案I（紧张感）：快速交叉剪辑，特写聚焦身体微动作（如手指叩击、汗水滑落），不时插入主观晃动镜头，变焦推拉造成空间扭曲感，高对比冷硬色调，秒表等计时元素的反复强调。\n"

        "方案J（宁静感）：固定广角远景，自然光源缓慢变化，对称或黄金分割构图，极度延长单镜头时间，轻柔的摇镜如呼吸，色彩以淡绿、天蓝和水色为主。\n"

        "方案K（混乱感）：激烈无规律手持晃动，跳切与频闪式剪辑，多重曝光叠影，高反差色彩与刺眼强光，极端特写与极端广角突兀切换，打破180度轴线。\n"  

        "方案L（史诗感）：航拍大远景缓升，巨型建筑或自然景观与渺小人物对比，金色逆光拉出长影，慢镜头配合环绕轨道运动，庄严的居中构图与水平线平衡。\n"

        "方案M（神秘感）：剪影与逆光致人物不可辨识，雾气、烟尘中若隐若现的移动，镜头缓慢穿行门廊或缝隙，极浅景深聚焦微小线索（如符号、刻痕），色彩偏向青紫或暗琥珀色。\n"

        "方案N（绝望感）：褪色至近乎单色，人物在废墟或荒原中被极度压缩成点，固定大远景持续到令人窒息，碎裂镜面反射扭曲的脸，缓慢下摇至地面的一滩死水或灰烬。\n"

        "方案O（疏离感）：框架式构图将人物困于窗格、门框或缝隙中，冷调蓝灰，固定机位中景，不展示角色眼神交流，空间内多人却彼此无接触，环境音视觉化般用虚焦的空镜隔断。\n"

        "方案P（怀旧感）：暖黄或棕褐单色调，柔光镜加轻微颗粒质感，慢镜头与叠化转场，特写老物件（如旋转的唱片、泛黄照片边缘），逆光中微尘浮动，推镜如记忆唤醒。\n"

        "方案Q（荒诞感）：夸张畸变广角，违反常理的构图平衡，突兀的静止画面破坏运动节奏，色彩时而过饱和时而褪色，反常视角（如从下水道井盖下仰拍），重复性机械动作的跳接。\n"

        "方案R（神圣感）：顶光或强烈逆光形成光冠，仰拍配合缓慢上升镜头，对称构图与空间纵深感，画面中大面积留白或天空，色调呈金白与淡蓝，慢镜头下衣袂飘动。\n"

        "方案S（诱惑感）：极浅景深只留一双眼睛或嘴唇清晰，缓慢的环绕轨道拍摄，暖红色调与深黑阴影，失焦的前景物体营造偷窥视角，升格拍摄手指滑过表面或眼神流转。\n"

        "方案T（麻木感）：完全固定长镜头，画面内人物几乎静止，环境声似乎吞噬一切，平光扁平化面孔，乏味对称的重复构图，色彩灰白缺失焦点，缓慢的淡出。\n"

        "方案U（狂热感）：快速旋转镜头，高饱和单一浓色（如血红、赤金），特写呐喊口型与充血眼睛，多角度碎剪同一动作，主观镜头穿行混乱人群，持续增强的音画节奏感。\n"
        "方案V（尴尬感）：固定中景或近景，人物被置于画面边缘区域，刻意打破均衡构图；僵持的沉默用长镜头放大，浅景深孤立角色，插入无人称的空镜（如滴水的龙头、静止的钟）；色调偏青灰或苍白荧光，突显微妙、躲闪的表情。\n"

        "方案W（兴奋感）：高速升格结合跳跃式剪辑，高饱和暖色调（明黄、橘红），突然的推进镜头；环绕轨道拍摄，多角度碎切同一动作，叠化光斑、彩带或烟火；手持微晃强化能量感。\n"

        "方案X（敬畏感）：极低角度仰拍巨大物体（如巨像、山峦、风暴），人物缩至极远处成点；缓慢上升的镜头配合拉焦，逆光形成轮廓光；对称广角构图，金色或银白高光，横摇长镜头让空间无声压迫。\n"

        "方案Y（厌恶感）：微距特写，倾斜失稳构图；阴湿的黄绿或病态褐调，手持略带晃动的逼近镜头又骤然甩开；前景半透明污迹遮挡，浅景深令视觉不洁。\n"

        "方案Z（疲惫感）：极低饱和或褪色倾向，灰黄或灰蓝调；长时间固定镜头拍摄瘫坐、伏案的身体，特写无神眼周与干裂嘴唇；浅景深将人从环境中分离，缓慢失焦又拉回，光昏弱如燃尽的灯。\n"

        "方案AA（梦幻感）：柔焦过曝与慢动作结合，镜头如失重般漂流；粉紫、珍珠白与淡金的主色调，逆光中大量飘浮的尘粒或光点；溶解式转场，非理性空间透视，记忆的视像交叠。\n"

        "方案AB（窒息感）：极度压缩的景别与空间，墙壁、天花板低压般的紧贴镜头；缓慢但逼近的推轨，配合心跳般收缩的浅焦，低角度仰拍高处窄窗；暗红或浑浊的墨绿调，特写颈间脉搏、被扼的手腕。\n"

        "方案AC（惊悚感）：突然极速推镜打破静止，倒转镜头瞬间，负片或闪烁的错格；极度阴暗与骤亮的惨白交替，影子脱离主人；音画错位下，空镜细小的异常（自开的门、晃动的水杯）用长焦静观。\n"

        "方案AD（温馨感）：暖调柔光加轻微暗角，浅景深慢推轨捕捉靠近的双手、微笑的眼角；低反差，琥珀色或蜜糖色，固定机位保留安稳空间；逆光中发丝光晕，环境有织物、木质的温润。\n"

        "方案AE（冷酷感）：高反差蓝黑或银灰调，如剃刀般平直锐利的构图；固定或极缓的机械式横摇，长焦压缩空间使人物扁平疏离；特写金属、玻璃等冰冷表面，脸上阴影界线分明无过渡。\n"

        "方案AF（疯狂感）：荷兰角大幅倾斜，快速无规律旋转镜头；频闪剪辑与多重曝光让同一张脸密集交叠；超广角畸变特写充血眼睛与嘶吼口型，色彩高饱和碰撞（猩红、电紫）；跳轴与速度线。\n"

        "方案AG（虚无感）：极端固定的长镜头，人物渐融于大雾或纯白背景；平光消除立体感，色彩逐渐褪至灰度，焦点的缓慢丧失让一切成模糊轮廓；长时间的空镜只余尘埃缓慢沉降。\n"

        "方案AH（期盼感）：主观视角注视远方，镜头伴随呼吸感缓慢向前推近地平线；逆光与金色光晕弥漫，升格拍摄人物面部光影从暗转亮；开阔明亮的构图，飞鸟或帆影等远方运动元素。 \n"

        "方案AI（嫉妒感）：斜角偷窥视角，前景常设网格、窗栏遮挡；幽绿或病态琥珀调，变焦推拉交替强调自己与他人的距离；特写绞紧的手指等，光影将脸割裂成明暗两面。 \n"

        "方案AJ（释然感）：镜头从人物特写缓慢后拉，融入广袤的自然风景；色调由冷灰渐转为暖金与淡青，面部紧绷的阴影消解；风拂过草地或衣摆的慢镜头，固定远景里人物舒展肢体。 \n"

        "方案AK（阴森感）：低角度缓慢横移穿过枯枝、蛛网与剥落墙体，冷月般的蓝绿光；阴影深处模糊的人形伫立不动，固定机位长拍，突然极细微的运动（如布帘轻动）；过肩镜头仿佛身后有人凝视。 \n"

        "方案AL（残酷感）：绝对冷静的固定机位凝视暴力或损伤，高清晰度特写伤痕、血迹；黑白或淡彩低饱和，慢镜头延长痛苦，声画对位冷漠；不对称的构图里，施害与受害被同等解剖。\n"

        "方案AM（崇高感）：超大广角仰拍纪念碑、漩涡云层或冰川裂口，人物仅占一角；缓慢上升或带有庄严感的环绕运动，金白与墨黑对比，长镜头保持绝对均衡的水平线构图，沉静而压倒。\n"

        "方案AN（迷惑感）：镜头反复从失焦到寻找焦点，无法稳定；非连贯空间的拼贴式剪辑，颠倒画面与色彩失真；多重曝光叠加不同方位影像，主观镜头旋转，逻辑轴线刻意扰乱。\n"

        "方案AO（焦虑感）：快速交叉推轨却抵达无意义细节，浅景深漂移；特写焦虑原因，倾斜构图中信息过载；高锐度、偏绿或铅灰，插入主观晃动镜头与耳鸣般的视觉频闪。\n"

        "方案AP（温柔感）：微距浅景深滑过轻触的指尖、靠拢的脸颊，光线如蜂蜜流淌；极慢的轻柔弧形运动，逆光里绒毛发光，色调是象牙白与柔玫瑰；固定特写长镜头，保持呼吸感。 \n"

        "方案AQ（荒谬感）：过分端正的对称构图搭配比例严重失调的物体，突然的静止打破运动节奏；高饱和玩具色和褪色交替，倒放或重复动作的跳接，从反常角度如地板缝或鱼眼窥视，世界如故障。 \n"

        "方案AR (敬畏自然的渺小感)：超大远景定摄，广角将人物置于巨树下、悬崖底或翻涌云海前；慢速上升镜头，自然光宏大变动（如圣光破云）；环境声优先，色彩是未经修饰的苍翠、铅灰与金黄，静默中见永恒。/n"
    )
    user_prompt = f"""
【原文】：{source}
- 针对每个 scene，必须在 visual_narrative_plan 字段中明确指定上述方案中的一种，并具体化。
    - 严禁每个场景视觉逻辑重复。
    
请将以上小说改编为剧本 JSON。你必须确保：
    
    一、角色深度塑造：
    - 为每个主要角色构建前史，明确其核心动力 (motivation) 和致命弱点 (fear)。
    - 确保人物台词符合其特定的 speech_style。
    注意：人是立体多面的，不能过度理想化，不能猜测！
    
    二、场景深度编排：
    必须做到有分镜和构图描写，具体的分镜和构图可以参考之前的影视作品和剧本（参考他们在什么心情之下会使用这个分镜）
    - subtext_conflict：必须明确指出这场戏里人物在“争夺什么”或“掩盖什么”。
    - visual_narrative_plan：必须具体到光影、构图和运镜，不能空谈视觉感受
    
    三、Beat 设计：
    - 每一个 Action 必须有具体的视觉动作，不能是心理活动，不能模棱两可，具体动作可以参照经典剧目
    
    【格式要求】：
    - scenes 数组中的每个 beat 必须包含 'type' 和 'text'。
    - action beat 的 text 必须描述具体镜头（如：特写/中景/POV）以及角色的具体动作细节（而非心理）。
    - dialogue beat 的 character_id 必须引用已定义人物。
    - 确保对话呈现出人物特有的 speech_style。
    
    请严格输出 JSON 结构。

1. 输出必须是合法 JSON，根对象形如 {{"script": {{...}}}}。
2. script 必须包含 schema_version、title、format、language、source、logline、synopsis、characters、locations、chapters、scenes、notes。
3. script.source 必须是 {{"type":"novel","chapter_count":章节数量}}，type 必须等于 novel。
4. characters、locations、chapters、scenes 的 id 必须唯一。
5. chapters 中每个对象必须包含 id、title、order、summary。order 必须是数字，不要用字符串。
6. scenes 中每个对象必须包含 id、order、source_chapters、heading、purpose、characters、beats、transition。
7. scene.id 必须使用 scene_001 这种格式，不要使用 scn_001。
8. scene.order 必须是数字。
9. scene.source_chapters 必须是数组，例如 ["chapter_001"]，并引用 chapters.id。
10. scene.heading 必须是对象，且包含 location_id、time_of_day、interior_exterior。
11. scene.beats 必须是数组；每个 beat 必须包含 type 和 text 字段。不要使用 content、description、line、dialogue_text 替代 text。
12. 每个 scene 至少包含一个 action beat。
13. dialogue、parenthetical、voice_over 如包含 character_id，必须引用已定义人物。
14. 心理描写要优先转为动作、表情、沉默、对白或场景调度。
15. 大段背景说明要拆成可视化信息，必要时使用 voice_over。
16. 不要仿写受版权保护作品，不要生成违法违规、不利于未成年人的内容。

剧本标题：{title or "未命名剧本"}
剧本类型：{script_format}
输出语言：zh-CN

小说正文：
{source_for_prompt}
""".strip()
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def post_chat_completion(config: LLMConfig, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{config.base_url}/chat/completions"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=config.timeout_seconds,
            context=build_ssl_context(config),
        ) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PipelineError(f"在线模型请求失败：HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise PipelineError(f"在线模型连接失败：{exc.reason}") from exc
    except TimeoutError as exc:
        raise PipelineError(
            f"在线模型响应超时（{config.timeout_seconds} 秒）。请减少输入文本，"
            "或在 .env 中调大 LLM_TIMEOUT_SECONDS。"
        ) from exc
    except socket.timeout as exc:
        raise PipelineError(
            f"在线模型响应超时（{config.timeout_seconds} 秒）。请减少输入文本，"
            "或在 .env 中调大 LLM_TIMEOUT_SECONDS。"
        ) from exc
    return json.loads(body)


def build_ssl_context(config: LLMConfig) -> ssl.SSLContext | None:
    if not config.ssl_cert_file:
        return None
    cert_path = Path(config.ssl_cert_file).expanduser()
    if not cert_path.exists():
        raise PipelineError(f"SSL_CERT_FILE 指向的证书文件不存在：{cert_path}")
    return ssl.create_default_context(cafile=str(cert_path))


def extract_message_content(response: dict[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise PipelineError("在线模型响应格式异常，未找到 choices[0].message.content。") from exc
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(content)


def parse_script_json(content: str) -> dict[str, Any]:
    cleaned = strip_code_fences(content.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise PipelineError(f"在线模型没有返回合法 JSON：{exc}") from exc

    if not isinstance(data, dict) or "script" not in data:
        raise PipelineError("在线模型返回 JSON 缺少根字段 script。")
    script = data["script"]
    if not isinstance(script, dict):
        raise PipelineError("在线模型返回的 script 必须是对象。")
    return script


def strip_code_fences(text: str) -> str:
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    return match.group(1) if match else text


def repair_script(
    script: dict[str, Any],
    source: str,
    title: str,
    script_format: str,
) -> dict[str, Any]:
    script = dict(script)
    chapters = normalize_list(script.get("chapters"))
    characters = normalize_list(script.get("characters"))
    locations = normalize_list(script.get("locations"))
    scenes = normalize_list(script.get("scenes"))

    if len(chapters) < 3:
        chapters = fallback_chapters(source)
    chapters = [repair_chapter(chapter, index) for index, chapter in enumerate(chapters, start=1)]

    if not characters:
        characters = [{"id": "char_001", "name": "未知人物", "role": "protagonist", "description": "待细化。", "traits": ["待细化"]}]
    characters = [repair_character(character, index) for index, character in enumerate(characters, start=1)]

    if not locations:
        locations = [{"id": "loc_001", "name": "主要场景", "description": "待细化的主要场景。"}]
    locations = [repair_location(location, index) for index, location in enumerate(locations, start=1)]

    if not scenes:
        scenes = fallback_scenes(chapters, characters, locations)
    else:
        scenes = [
            repair_scene(scene, index, chapters, characters, locations)
            for index, scene in enumerate(scenes, start=1)
        ]

    script["schema_version"] = str(script.get("schema_version") or "1.0")
    script["title"] = str(script.get("title") or title or "未命名剧本")
    script["format"] = script_format if script_format in {"screenplay", "web_series", "stage_play", "audio_drama"} else "screenplay"
    script["language"] = str(script.get("language") or "zh-CN")
    script["source"] = {
        "type": "novel",
        "chapter_count": len(chapters),
    }
    script["logline"] = str(script.get("logline") or "人物在连续事件中追寻真相，并面对逐渐升级的冲突。")
    script["synopsis"] = str(script.get("synopsis") or " ".join(chapter["summary"] for chapter in chapters))
    script["story_bible"] = repair_story_bible(script.get("story_bible"), chapters, characters)
    script["foreshadowing_ledger"] = repair_foreshadowing_ledger(script.get("foreshadowing_ledger"), chapters)
    script["canon_facts"] = normalize_list(script.get("canon_facts"))
    script["rhythm_plan"] = repair_rhythm_plan(script.get("rhythm_plan"), chapters)
    script["characters"] = characters
    script["locations"] = locations
    script["chapters"] = chapters
    script["scenes"] = scenes
    script["coverage_report"] = repair_coverage_report(script.get("coverage_report"), chapters, script["foreshadowing_ledger"])
    script["notes"] = normalize_list(script.get("notes"))
    return script


def normalize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def repair_chapter(chapter: Any, index: int) -> dict[str, Any]:
    data = chapter if isinstance(chapter, dict) else {}
    return {
        "id": normalize_id(data.get("id"), "chapter", index),
        "title": str(data.get("title") or f"第{index}章"),
        "order": to_int(data.get("order"), index),
        "summary": str(data.get("summary") or data.get("synopsis") or data.get("content") or "待补充章节摘要。"),
    }




def repair_character(character: Any, index: int) -> dict[str, Any]:
    data = character if isinstance(character, dict) else {}
    return {
        "id": normalize_id(data.get("id"), "char", index),
        "name": str(data.get("name") or data.get("character") or "未知人物"),
        "role": str(data.get("role") or ("protagonist" if index == 1 else "supporting")),
        "description": str(data.get("description") or data.get("summary") or "待细化。"),
        "traits": normalize_string_list(data.get("traits")) or ["待细化"],
        "speech_style": data.get("speech_style")
        if isinstance(data.get("speech_style"), dict)
        else {
            "pace": "中等",
            "vocabulary": "少用长句，避免说明文式表达",
            "habit": "通过停顿、反问或回避表达情绪",
            "subtext": "保留潜台词",
            "taboo": "不直接讲出观众已知背景",
        },
    }


def repair_location(location: Any, index: int) -> dict[str, Any]:
    data = location if isinstance(location, dict) else {}
    return {
        "id": normalize_id(data.get("id"), "loc", index),
        "name": str(data.get("name") or data.get("location") or "主要场景"),
        "description": str(data.get("description") or data.get("summary") or "待细化的场景空间。"),
    }


def repair_scene(
    scene: Any,
    index: int,
    chapters: list[dict[str, Any]],
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
) -> dict[str, Any]:
    data = scene if isinstance(scene, dict) else {}
    chapter_id = chapters[min(index - 1, len(chapters) - 1)]["id"]
    location_id = locations[0]["id"]
    character_ids = [character["id"] for character in characters[:3]]
    heading = data.get("heading") if isinstance(data.get("heading"), dict) else {}
    beats = repair_beats(data.get("beats"), character_ids)
    
    return {
        "id": normalize_id(data.get("id"), "scene", index),
        "order": to_int(data.get("order"), index),
        "source_chapters": normalize_ref_list(data.get("source_chapters"), {chapter["id"] for chapter in chapters}) or [chapter_id],
        "heading": {
            "location_id": heading.get("location_id") if heading.get("location_id") in {location["id"] for location in locations} else location_id,
            "time_of_day": str(heading.get("time_of_day") or data.get("time_of_day") or "day"),
            "interior_exterior": normalize_interior_exterior(heading.get("interior_exterior") or data.get("interior_exterior")),
        },
        "purpose": str(data.get("purpose") or data.get("function") or "推进情节和人物关系。"),
        "plot_function": str(data.get("plot_function") or "turn"),
        "intensity": max(1, min(10, to_int(data.get("intensity"), index + 3))),
        "characters": normalize_ref_list(data.get("characters"), set(character_ids)) or character_ids,
        "beats": beats,
        "transition": str(data.get("transition") or "cut_to"),
        "visualization_checks": data.get("visualization_checks")
        if isinstance(data.get("visualization_checks"), dict)
        else {
            "no_internal_monologue": True,
            "has_performable_action": True,
            "has_subtext_dialogue": True,
            "canon_consistent": True,
            "foreshadowing_tracked": True,
        },
    }





def repair_beats(value: Any, character_ids: list[str]) -> list[dict[str, Any]]:
    raw_beats = value if isinstance(value, list) else []
    beats: list[dict[str, Any]] = []
    for beat in raw_beats:
        if not isinstance(beat, dict):
            continue
        beat_type = str(beat.get("type") or "action")
        if beat_type not in {"action", "dialogue", "parenthetical", "voice_over", "sound", "transition"}:
            beat_type = "action"
        text = first_text_value(beat)
        if not text:
            text = "人物通过动作和停顿推进场景。"
        repaired: dict[str, Any] = {"type": beat_type, "text": text}
        if beat_type in {"dialogue", "parenthetical", "voice_over"}:
            repaired["character_id"] = beat.get("character_id") if beat.get("character_id") in character_ids else character_ids[0]
        repaired.setdefault("source_refs", [])
        beats.append(repaired)
    if not beats:
        beats.append({"type": "action", "text": "场景展开，人物进入关键情境。"})
    if not any(beat["type"] == "action" for beat in beats):
        beats.insert(0, {"type": "action", "text": "场景展开，人物进入关键情境。"})
    return beats


def first_text_value(data: dict[str, Any]) -> str:
    for key in ["text", "content", "description", "line", "dialogue_text", "action"]:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_id(value: Any, prefix: str, index: int) -> str:
    text = str(value or "")
    if re.fullmatch(rf"{re.escape(prefix)}_\d{{3}}", text):
        return text
    if prefix == "scene" and re.fullmatch(r"scn_\d{3}", text):
        return "scene_" + text.rsplit("_", 1)[1]
    return f"{prefix}_{index:03d}"


def to_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return int(match.group())
    return default


def normalize_ref_list(value: Any, allowed: set[str]) -> list[str]:
    items = value if isinstance(value, list) else []
    return [item for item in items if isinstance(item, str) and item in allowed]


def normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_interior_exterior(value: Any) -> str:
    text = str(value or "").lower()
    if text in {"exterior", "ext", "外景", "室外"}:
        return "exterior"
    return "interior"


def fallback_chapters(source: str) -> list[dict[str, Any]]:
    parts = [part.strip() for part in re.split(r"\n\s*\n", source) if part.strip()]
    if len(parts) < 3:
        parts = [source, source, source]
    return [
        {
            "id": f"chapter_{index:03d}",
            "title": f"临时章节 {index}",
            "order": index,
            "summary": part[:120] or "待补充章节摘要。",
        }
        for index, part in enumerate(parts[:3], start=1)
    ]


def fallback_scenes(
    chapters: list[dict[str, Any]],
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        repair_scene({}, index, chapters, characters, locations)
        for index, _chapter in enumerate(chapters, start=1)
    ]


def repair_story_bible(value: Any, chapters: list[dict[str, Any]], characters: list[dict[str, Any]]) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    protagonist_id = characters[0]["id"] if characters else "char_001"
    return {
        "premise": str(data.get("premise") or "人物在连续事件中面对核心冲突。"),
        "world_rules": normalize_list(data.get("world_rules")),
        "character_arcs": normalize_list(data.get("character_arcs"))
        or [
            {
                "character_id": protagonist_id,
                "start_state": "信息不足，被事件推动",
                "midpoint_state": "主动调查，冲突升级",
                "end_state": "接近真相，完成阶段性选择",
            }
        ],
        "major_conflicts": normalize_string_list(data.get("major_conflicts")) or ["主要人物与现实阻碍之间的冲突"],
        "timeline": data.get("timeline")
        if isinstance(data.get("timeline"), list)
        else [
            {"order": chapter["order"], "event": chapter["summary"], "source_chapter": chapter["id"]}
            for chapter in chapters
        ],
    }


def repair_foreshadowing_ledger(value: Any, chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = normalize_list(value)
    if items:
        return items
    first_chapter = chapters[0]["id"] if chapters else "chapter_001"
    return [
        {
            "id": "foreshadow_001",
            "setup": "关键线索",
            "source_chapters": [first_chapter],
            "expected_payoff": "后续揭示线索与核心事件的关系",
            "payoff_status": "pending",
            "payoff_scene_id": None,
        }
    ]


def repair_rhythm_plan(value: Any, chapters: list[dict[str, Any]]) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    if isinstance(data.get("acts"), list):
        return data
    ids = [chapter["id"] for chapter in chapters]
    return {
        "acts": [
            {"id": "act_001", "function": "建立人物和悬念", "chapters": ids[:1], "intensity": "low_to_mid"},
            {"id": "act_002", "function": "推进调查与冲突", "chapters": ids[1:2], "intensity": "mid_to_high"},
            {"id": "act_003", "function": "阶段性揭示", "chapters": ids[-1:], "intensity": "high"},
        ]
    }


def repair_coverage_report(
    value: Any, chapters: list[dict[str, Any]], foreshadowing_ledger: list[dict[str, Any]]
) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    return {
        "covered_chapters": normalize_string_list(data.get("covered_chapters"))
        or [chapter["id"] for chapter in chapters],
        "missing_events": normalize_list(data.get("missing_events")),
        "unresolved_foreshadowing": normalize_string_list(data.get("unresolved_foreshadowing"))
        or [item["id"] for item in foreshadowing_ledger if item.get("payoff_status") == "pending"],
        "contradictions": normalize_list(data.get("contradictions")),
    }

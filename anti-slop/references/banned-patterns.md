# Banned Vocabulary, Patterns & Rewrite Recipes (English & Korean)

Consolidated reference combining `blader/humanizer` (v4.0), Wikipedia `WP:AISIGNS`, `SalZaki/antislop`, `kjmagnan1s/anti-slop`, and `epoko77-ai/im-not-ai` (`humanize-korean` v2.4).

---

## Part 1: English AI Tells & Recipes

### 1.1 Tier 1 Structural Tells (Act on 1 Sighting)

| Pattern | Tell / Watch For | Fix |
|---|---|---|
| Negative parallelism | `It's not just X; it's Y`, `not only X, but also Y` (ornamental), `This does not mean X. It means Y.` | State Y directly unless X corrects an active reader misconception. |
| Staged run-up | `Here is the thing:`, `The truth is:`, `At its core,`, `What really matters is` | Delete the throat-clearing opener and start with the claim. |
| One-line closer | `Let that sink in.`, `Read that again.`, `That is the real win.`, `The message was clear:` | Delete restatements; keep only if it adds a concrete consequence. |
| Copula avoidance | `stands as a`, `serves as a`, `represents a`, `embodies`, `acts as a`, `boasts` | Replace with plain `is`, `are`, `has`, or a specific verb. |
| Shallow `-ing` tail | `..., highlighting its importance`, `..., reflecting a broader shift`, `..., underscoring` | Cut the participle clause or supply a concrete causal link. |
| False range | `from X to Y` where endpoints are non-scalar (`from startups to global enterprises`) | Name the actual group or scope directly. |
| Borrowed authority | `Observers note`, `Experts agree`, `Critics argue`, `Studies show` (no source) | Cite the actual source or state the claim directly as your observation. |
| Prompt / chat residue | `Certainly!`, `Absolutely!`, `Great question!`, `Let's dive in`, `I hope this helps!`, `Let me know if...` | Strip completely. |

### 1.2 Overused English AI Vocabulary

Avoid these words completely unless quoting a source or naming a domain term (e.g., an actual textile tapestry):

- **Verbs:** `delve` (use *read, examine*), `underscore` (use *show*), `foster` (use *encourage, support*), `leverage` (use *use*), `utilize` (use *use*), `commence` (use *start*), `facilitate` (use *help, enable*), `bolster` (use *strengthen*), `garner` (use *get, win*), `encompass` (use *include*), `spearheading` (use *leading*), `showcasing` (use *showing*), `revolutionize` (use *change*), `navigate` (figurative; use *handle, work through*).
- **Adjectives:** `pivotal`, `crucial`, `intricate`, `meticulous`, `multifaceted`, `nuanced`, `paramount`, `groundbreaking`, `cutting-edge`, `game-changing`, `transformative`, `seamless`, `robust`, `vibrant`, `unprecedented`, `aforementioned`.
- **Nouns & Metaphors:** `tapestry`, `landscape` (figurative), `testament`, `interplay`, `realm`, `beacon`, `cornerstone`, `paradigm shift`, `watershed moment`.

### 1.3 English Rhythm, Scaffolding & Formatting

- **Forced triads:** Replace mechanical 3-item adjective strings (`fast, secure, and scalable`) with 1–2 concrete facts (`runs in 12 ms with TLS`).
- **Compulsory recap:** Cut `In conclusion,`, `To summarize,`, `Overall,`, `At the end of the day,`, `The bottom line is`.
- **Formatting tells:**
  - Maximum 1–2 em dashes (`—`) per document; use commas, parentheses, or split sentences instead.
  - Never format every bullet as `- **Bold Lead-In**: explanation` (bold-bullet soup).
  - Avoid decorative emojis in technical prose or reports (`✅ 🚀 💡 ⚠️ 📊 ✨ 🎯`).

---

## Part 2: Korean AI Tells & Recipes (한국어 패턴 및 처방)

### 2.1 번역투 변환표 (Category A & PE1–PE15)

| 원문 패턴 (AI 번역투) | 처방 (자연스러운 한국어) | 비고 |
|---|---|---|
| `X에 대해 논의한다` (문단 3회+ 밀집 시) | `X를 논의한다` / `X를 다룬다` | 고립 사용은 허용 |
| `X를 통해/통하여 Y한다` (남발) | `X로 Y한다` / `X해서 Y한다` / `X함으로써 Y한다` | 수단·경로 일괄 매핑 금지 |
| `X에 있어(서)` | `X에서` / `X를 볼 때` / `X에서는` | 1회 등장도 교정 (S1) |
| `X와 관련하여 / 관련된` | `X에` / `X에는` / `X의` | — |
| `X에 기반하여 / 바탕으로` (남발) | `X로` / `X를 근거로` / `X를 보고` | — |
| `강한 경쟁력을 가지고 있다` (`have+N`) | `경쟁력이 강하다` / `경쟁력이 있다` | `회의를 가지다` → `회의했다` |
| `판단되어진다 / 보여진다 / ~지게 된다` | `판단된다 / 보인다 / ~된다` | 이중 피동 절대 금지 (S1) |
| `AI에 의해 생성된` (`by`-passive) | `AI가 만든` | 행위자를 주어로 전환 |
| `이 결과는 ~을 보여준다/제공한다/도모한다` | `이 결과를 보면 ~이다` / `~를 돕는다` | 무생물 주어 + 만능 동사 해체 |
| `~에서의 / ~에로의 / ~으로의 / ~으로부터의` | 절·구로 풀어쓰기 (`서울에서 시작한 사업`) | 단순 `~의`는 제외 |
| 3어절+ 좌향 수식 관형절 | 문장 분리 또는 후치 동격절 | `X를 만났는데, 그 X는 ~` |
| 불필요한 `그 / 그녀 / 그것 / 이는` | 생략(영형 대명사) 또는 선행 명사 직접 지시 | 2문장 앞 선행 후보 불명확 시 명사 복원 |
| `단순한 X를 넘어 Y` (`beyond mere X`) | `X만이 아니라 Y다` 또는 구 삭제 | 범위 상승 상투구 제거 |
| `~은 명확하다 / 분명하다` | 평가 술어 제거 후 명제 단언 (확신 부사 유지) | `앞에서 보았듯 ~이다` |

### 2.2 구조·결산 공식 해체 (Categories B, C, D)

- **대칭 대구 해체 (C-8):** `A가 아니라 B`, `A는 X이고 B는 Y다` 연속 사용을 비대칭 단언으로 푼다 (문서 내 효과적인 대구 1개까지는 허용).
  - Before: `기술은 도구이고, 사람은 주체다. 데이터는 연료이며, 알고리즘은 엔진이다.`
  - After: `기술은 도구다. 사람이 그 도구를 쥔다. 데이터가 있어야 알고리즘이 돌아간다.`
- **분열문 해체 (D-8):** `중요한/필요한 것은 X이다`, `문제는/핵심은/관건은 ~라는 점이다`를 주어·서술어로 직결한다.
  - Before: `주 4일제 논쟁의 핵심은 생산성 전환이다.` → After: `주 4일제 논쟁은 생산성을 어떻게 바꾸느냐로 모인다.`
  - Before: `문제는 합의에 이르는 경우가 거의 없다는 점이다.` → After: `양측은 합의에 이르는 일이 거의 없다.`
- **역방향 결산 해체 (D-10):** `This is why ~` 직역인 문말 `~하는 이유다.`를 제거한다.
  - Before: `일률적인 도입이 현실적이지 않은 이유다.` → After: `그래서 일률적인 도입은 현실적이지 않다.`
- **결말 상투어 및 공허한 반론 삭제 (D-1, D-6, D-11, D-12):**
  - 삭제 대상: `결론적으로 말씀드리자면`, `총체적으로 살펴보면`, `요약하자면`, `시사하는 바가 크다`, `지평을 열다`, `초석을 다지다`, `~의 중요성은 아무리 강조해도 지나치지 않습니다`, `~해야 할 때/시점입니다`, `향후/중장기적으로 ~할 것이다`, `과제도 남아 있다`, `한계도 분명하다`.
- **기계적 병렬 및 괄호 병기 (B-1, C-1, C-2, C-9):**
  - `첫째, ~. 둘째, ~. 셋째, ~.` 또는 `1) ... 2) ... 3) ...` 장식 열거는 산문으로 합친다.
  - 영어 전문용어 괄호 병기(`소버린 AI(Sovereign AI)`)는 일반 독자용 글에서 첫 1회만 허용한다.

### 2.3 리듬·접속사·서법·형식명사 (Categories E–J)

- **연결어미 뒤 쉼표 금지 (C-11):** `-고,`, `-며,`, `-지만,`, `-면서,`, `-아서,`, `-어서,` 직후의 불필요한 쉼표를 지운다.
  - Before: `속도는 빠르지만, 메모리 사용량이 늘어난다.` → After: `속도는 빠르지만 메모리 사용량이 늘어난다.`
- **종결어미 단조성 회피 (E-2, I-1):** `~이다.` / `~고 있다.`를 4문장 이상 연속 쓰지 않는다. `~한 것이다.` / `~일 것이다.` 종결은 `~다.`로 직접 끝낸다.
- **문두 접속사 밀집 제거 (H-1):** `또한`, `따라서`, `그러므로`, `즉`, `나아가`, `더불어`, `아울러`가 한 문단에 3회 이상 나오면 절반 이상 지운다.
- **형식명사·정도부사 절제 (F-1, I-2, I-4):** `매우`, `정말`, `대단히`, `극히`는 수치·비교로 대체하거나 지운다. `~할 필요가 있다`를 `~해야 한다`로 일괄 치환하지 말고 문맥에 맞게 주체와 동사를 쓴다.
- **서법 보존 (Modality Guard):**
  - `~할 수 있을 것으로 보인다` → `~로 보인다` (이중 완곡만 축소)
  - `~로 보인다` → `~이다` (**금지** — 추측을 단정으로 바꾸지 말 것)
  - `~해야 한다` → `~한다` (**금지** — 당위를 사실로 바꾸지 말 것)

### 2.4 한국어 AI 어휘 블랙리스트 (Lexicon v1.3 요약)

- **즉시 교체 대상 (문맥상 비유/직역일 때):**
  - `잠재력을 잠금 해제하다` → `잠재력을 끌어내다 / 활용하다` (스마트폰·계정 잠금 해제는 제외)
  - `정보에 입각한 결정` → `자료를 보고 내린 결정 / 근거 있는 판단`
  - `혜택을 경험하다` / `경험을 최적화하다` → `혜택을 누린다` / `사용성을 높인다`
  - `성공을 달성하다` / `결과를 전달하다(deliver)` → `성공하다` / `성과를 내다`
  - `실행 가능한 통찰` → `바로 쓸 수 있는 대안 / 구체적인 시사점`
  - `논의의 무늬`, `생각을 벼리다`, `의미를 길어 올리다`, `마음을 포개다`, `인식을 틔우다`
  - `두 축 / 세 축`, `세 가지 렌즈`, `태피스트리`, `항해하다`(추상), `이음매`, `층위`, `지형`(추상), `공명하다`, `진단은 서늘하다`, `경고는 아프다`, `여백·울림·숨결`, `짚다`(짚고 간다), `기둥`(세 기둥·핵심 기둥)
- **아첨 및 챗봇 잔여물 (Sycophancy):**
  - `좋은 질문 감사합니다!`, `매우 날카로운 지적입니다!`, `도움이 되셨기를 바랍니다!`, `언제든 추가 질문이 있으시면 말씀해 주세요.`

# **高考数学辅导Agent3-02：基于大模型体系构建个性化数学辅导Agent的“提示词与算理”防坑指南**

在当前人工智能与教育技术深度融合的浪潮中，大语言模型（LLM）正经历从单纯的“知识检索器”向“认知辅导伴学”角色的范式转换。然而，数学推理作为人类智能的核心体现，对逻辑的严密性、步骤的连贯性以及概念的精确性提出了极高要求。即便是当前处于行业前沿的模型，如具备强化视觉推理能力的Claude 3.5 Sonnet与整合了多模态思维链的GPT-4o或o1系列，在处理复杂数学任务时依然会暴露出深层的认知盲区与架构局限1。对于致力于开发本地化数学辅导Agent的非数学专业开发者而言，理解大模型的底层行为逻辑、构建高鲁棒性的提示词架构，并设计符合教育心理学的工作流，是跨越技术鸿沟、实现产品教育价值的核心所在。

本报告将从数学算理幻觉的底层生成机制出发，深入剖析错题诊断（Bug归因）逻辑，探讨同构题生成质量控制的技术路径，并提供系统级指令的架构设计方案，最后揭示在多轮教育辅导场景中极易触发的隐蔽技术陷阱。

## **一、 数学算理幻觉对抗：大模型的认知盲区与约束机制**

尽管顶级大模型在MATH等国际基准测试中已能达到70%至80%的准确率1，但其在处理中国高中数学题时，往往表现出一种高度自信的“高分低能”现象。研究表明，大模型在遇到包含逻辑陷阱的中学数学题（如MathTrap测试集）时，其准确率会大幅暴跌至24.3%左右4。这种现象的根源在于，大模型的数学推理本质上仍是基于统计概率的模式匹配，它在预训练阶段被奖励机制驱动去“猜测”而非“承认无知”5。在这一机制下，不到0.1%的特定神经元（H-Neurons）被激活，导致模型产生“过度顺从（Over-compliance）”行为，从而生成看似合理实则逻辑断裂的解答6。

### **1\. 顶级大模型在高中数学中的“自信幻觉”重灾区**

在具体的中国高中数学解题场景中，大模型的幻觉并非随机的计算错误，而是在特定复杂性维度上的系统性坍塌。其在以下三个核心环节极易产生高度自信的幻觉：

多分类讨论中的“动态工作记忆坍塌”（Multi-case Discussion）。高中数学中的解析几何动点轨迹讨论或导数含参单调性分析，高度依赖对多种边界条件的严密穷举。针对代数推理复杂度的九维度框架研究显示，当并行逻辑分支或并发中间状态数量超过20至30个时，无论大模型的参数规模从8B扩展至235B，都会面临工作记忆的硬性架构瓶颈7。这种瓶颈导致模型在推理中途遗漏关键分支（如忽略了判别式 ![][image1] 的临界情况），进而基于不完整的分类树自信地推导出错误的全局结论。

复杂代数变形中的“伪逻辑拼接”（Complex Algebraic Deformation）。在处理多步代数化简或不等式放缩时，模型常常利用其庞大的参数量进行“跨步模式匹配”。由于缺乏严格的符号计算器作为内部引擎，模型在面对深层嵌套的表达式时，会捏造并不存在的代数恒等式以强行拼凑出目标状态2。例如，在复杂的三角函数变换中，模型可能会无视象限符号规律，直接将一个错误的中间结果与预期的正确答案强行连接。这种“答案正确但过程胡编”的现象，对试图通过阅读解答步骤来学习基础算理的学生具有极大的认知误导性。

特值法的“非法滥用”（Abuse of Special Value Method）。大模型在海量预训练数据中吸收了大量的应试速算技巧，导致其在遇到抽象函数推断或通用证明题时，倾向于自动代入特殊值（如 ![][image2] 或 ![][image3]）进行局部验证，并违背逻辑量词规则将其直接升格为全称命题的全局证明4。例如，在处理含有未定义域的函数时，模型可能无视 ![][image2] 处无意义的前提条件强行代入，从而得出完全错误的函数周期性或对称性结论，且对自己的判断深信不疑4。

### **2\. 面向“学渣”的System Prompt约束与教学法思维链（PedCoT）**

为了剥夺AI在推理过程中的“跳步自由”，并强制其展现基础薄弱学生能够理解的底层步骤，开发者必须在System Prompt中引入基于教育学理论的“教学法思维链（Pedagogical Chain-of-Thought, PedCoT）”9。该方法将布鲁姆认知模型（Bloom Cognitive Model）与结构化的标记语言（XML或JSON）结合，强制规范AI的输出粒度。

| 约束维度 | 数据结构/XML标签 | 底层逻辑约束与系统指令说明 |
| :---- | :---- | :---- |
| **术语认知降维** | \<concept\_translation\> | 强制AI将抽象的数学定理翻译为具象的生活隐喻或图形直觉。指令要求在解释高阶概念前，必须建立低阶认知锚点（如用“爬山斜率变化”类比“二阶导数符号”）。 |
| **前置边界验证** | \<constraint\_check\> | 针对“特值法滥用”和“分类遗漏”设置强制逻辑安检点。指令规定：在进行任何代数化简、方程开方或特值代入前，必须率先计算并输出函数的定义域与参数取值范围。 |
| **原子级演算步骤** | \<atomic\_step\> | 针对“伪逻辑拼接”实施步长限制。要求每一步只允许进行一次基础数学操作（如单次移项、单次提取公因式），并在子标签 \<rationale\> 中明确声明所依据的具体公理或公式。 |
| **防跳步同理心自检** | \<student\_perspective\> | 在输出最终解答序列前，强制模型站在基础薄弱学生的视角反问自身：“从步骤A推导至步骤B，是否存在超过两个子步骤的跳跃？”若有，则自动在输出中插入辅助推理节点。 |

通过上述高度结构化的容器约束，大模型被强制要求将其内部隐式的概率分布转化为显式的符号推演。这种机制不仅切断了模型直接跃迁至答案的捷径，更迫使其推理过程完全透明化，使得家长或系统能够通过解析特定的XML标签来监控教学质量并进行自动化渲染。

## **二、 错题诊断（Bug归因）逻辑：大模型驱动的渐进式苏格拉底工作流**

教育的本质在于启发与认知重构，而非简单的信息分发。当学生在解答过程中出现错误时，系统直接抛出标准答案会彻底剥夺学生进行元认知反思的黄金窗口。在基于LLM构建的辅导Agent中，必须深度整合“苏格拉底式提问（Socratic Questioning）”工作流。研究文献证实，采用苏格拉底式对话框架可以显著提高大模型推理链路的评估质量，迫使模型和用户在交互中共同暴露出隐藏的假设和逻辑漏洞，从而将模糊的问题空间转化为精确的认知诊断11。

一套高水准的“渐进式苏格拉底提问”工作流，应被设计为一个部分可观察马尔可夫决策过程（POMDP）。在此过程中，Agent不断更新其内部的“信念状态（Belief State）”，以精准定位学生的认知断层，并据此决定下一阶段的辅导策略12。

### **1\. 基于LLM的错题Bug归因矩阵**

Agent首先需要在后台隐式地对学生的错题进行多维度归因。数学推理错误并非均质的，大模型需要通过分析学生的草稿或部分解答，将其归类为以下三种核心Bug之一：

| 错误类型分类 | 认知表现特征 | LLM诊断特征提取目标 | 针对性修复策略导向 |
| :---- | :---- | :---- | :---- |
| **概念混淆 (Concept Confusion)** | 对底层数学定义或性质的理解存在偏差。例如将“互斥事件”误认为“独立事件”，或混淆了“极值点”与“最值点”的充要条件。 | 寻找学生语言或公式中对关键术语的误用，或应用了在当前上下文中完全失效的定理。 | 退回基础概念层，通过反事实提问或对比示例重塑概念边界。 |
| **算理跳步/逻辑断层 (Logic Step-Skipping)** | 核心概念理解正确，但在多步推理网络中错误地传递了变量，或在分类讨论时遗漏了关键的边界条件区间。 | 分析推理链条的连贯性，识别中间状态向下一状态转换时缺失的依赖条件或逻辑证明。 | 定位逻辑断裂点，要求学生补充缺失的推导依据或重新审视分类树。 |
| **粗心/计算失误 (Carelessness/Arithmetic)** | 逻辑决策树与数学建模完全正确，但单纯在数值的加减乘除或代数式的展开合并中出现了低级错误。 | 对比模型的内部正确计算图与学生的计算图，确认操作符或数值的异常偏移。 | 不提供直接干预，仅提示错误所在的具体步骤或计算区间，要求学生复算。 |

### **2\. 渐进式苏格拉底提问与认知脚手架设计**

基于两千多年前古典哲学与现代Prompt工程的结构映射研究，苏格拉底的六种对话技巧（定义、诘问、辩证、产婆术、泛化、反事实推理）可以完美映射到大模型的提示工程中（如重述与响应RaR、思维链CoT、多智能体辩论、思维树ToT等）14。基于这些理论，Agent的工作流应严格遵循以下四个渐进阶段，坚决抵制越级给出现成答案的冲动。

阶段一：数据与已知条件提取（澄清式提问）。此阶段旨在消除信息歧义并排除“粗心审题”的干扰。系统通过要求学生复述问题或提取关键参数，来确认学生是否真正理解了题意。对应的AI行为指令为：拒绝指出错误，转而询问学生：“在这个情境下，你认为哪几个数学条件是破题的基石？我们先把它们转化为数学语言。”这一过程对应于苏格拉底方法中的“定义（Definition）”与现代提示工程的“重述与响应（Rephrase and Respond）”，通过增强语义清晰度来解决固有的歧义14。

阶段二：探究隐藏假设（概念混淆探测）。此阶段用于诊断学生是否在底层概念上存在误解。Agent通过针对题目涉及的核心知识点提出反事实（Counterfactual）或极端情况的问题，来测试学生认知模型的坚固性。指令示例可以设定为：“针对学生错误应用的公式，构造一个极简的边界测试题。例如询问：‘如果这里的函数在这个断点不连续，我们还能直接令导数为零来寻找极值吗？’”这种策略能够有效暴露学生未经检验的预设假设。

阶段三：逆向工程与证据链验证（算理跳步探测）。当确认概念无误后，Agent需要协助学生修补逻辑断层。此时采用“产婆术（Maieutics）”策略，引导学生顺藤摸瓜，审视从上一步推导至下一步的逻辑合法性。指令可以约束AI：“定位学生解答中出现偏差的前一个正确节点，提问：‘你在这一步得出了表达式X，按照代数法则，从X变形到你的下一步，你依赖的是哪个具体的恒等式？’”这迫使学生重建证据链，自行发现逻辑跃迁的谬误15。

阶段四：多模态脚手架辅助（Scaffolding）。若学生在连续几轮的苏格拉底追问下依然无法突破认知瓶颈，Agent必须提供保底支持，以避免过度挫败感。此时引入降维打击与多模态表征。系统指令应指示：“若学生三次未能击中逻辑要害，则停止追问。退回至更简单的特例或切换表征方式，例如提示：‘我们暂且把复杂的 ![][image4] 项放一放，试着把 ![][image5] 和 ![][image6] 的情况在坐标系里画个草图，观察一下交点的变化规律？’”这种渐进式的支撑框架（Scaffolding）能够有效适配不同学习节奏的学生15。

这种“提问 ![][image7] 探究假设 ![][image7] 验证证据 ![][image7] 动态反馈”的互动重排，刻意增加了交互延迟。这种延迟并非系统缺陷，而是通过引入必要的认知摩擦（Friction），强迫大模型进行更深度的任务状态规划，防止其沦为盲目输出的机器11。

## **三、 同构题生成质量控制：“高考90分保底难度”的限制策略**

数学知识的内化不仅依赖于错题的纠正，更需要通过“同构题（Isomorphic Problems）”的高质量重复训练来实现概念的迁移。同构题的生成要求在严格保持原始题目的数学核心概念和定量逻辑关系（Conceptual Correctness）完全等价的前提下，对题目的表层文本叙述和数值参数进行变异（Structural Equivalence）17。然而，在实际应用中，未加严格约束的大模型极易在题目生成上出现“难度失控”——要么生成仅需一步计算的低阶口算题，要么过度堆砌无关知识点，衍生出严重超纲的竞赛级难题19。

以中国高考数学满分150分为例，“90分”代表着通过及格线的基准难度。这一难度区间的题型分布主要集中于基础题（约占70%）与中档题（约占20%）21。其核心特征是考察主干知识点的直接应用与有限步骤的逻辑结合，严格排除了多重嵌套的复杂解析几何计算和极度抽象的导数放缩证明。因此，约束大模型生成“高考90分”难度的同构题，是一项极具挑战性的提示词工程。

### **1\. 大模型难度感知的失真与Rasch模型偏离**

认知心理学中的Rasch模型揭示，人类在面对不同难度的题目时，其解答成功率会呈现出平滑且可预测的下降曲线。然而，GAOKAO-Eval基准测试的深度分析表明，大模型的评分模式与人类的难度感知存在严重的分歧。大模型在处理各个难度层级的题目时，往往表现出异常的“难度不变性（Difficulty-invariant distributions）”，而在面对同等难度的不同题目时，其表现又存在极高的方差（High variance）22。这种偏离意味着，开发者不能简单地在提示词中写入“生成一道中等难度的题目”——因为大模型对“中等难度”的内部表征与人类教育者的标尺完全脱节。

### **2\. 构建“高考90分”难度控制的提示词工程策略**

为了克服大模型的难度感知失真，确保生成的同构练习题既不超前也不超纲，必须采用“结构化计算蓝图（Computational Blueprints for Isomorphic Twins, CBIT）”结合显式负向知识点约束的综合策略17。

| 难度控制维度 | 提示词工程约束策略描述 | 针对“高考90分”的系统级指令实例 |
| :---- | :---- | :---- |
| **知识点粒度隔离 (Granularity Control)** | 大模型难度失控的首要原因是知识点的无序杂糅。必须在Prompt中明确界定概念白名单，并通过“负面约束”建立防火墙。高纯度的知识点限定能显著降低题目的综合复杂度。 | 正面清单：“本题仅允许融合‘等差数列求和公式’与‘一元二次不等式解法’两个知识点。” 负面清单（绝对禁止）：“严禁在题干或求解中引入三角函数代换、复数运算、极限思想或超过二次的高次方程求解。” |
| **推理链长度硬编码 (Reasoning Chain Length)** | 限制从已知条件到最终结论所需的逻辑推理跳数。高考90分难度的解答题，其核心推理骨架通常较为直接，冗长的依赖链会呈指数级增加问题的认知负荷。 | 指令约束：“生成的同构题必须能够在3至4个核心推导步骤内得出最终解析解。如果内部测试发现该题的求解路径需要超过4个中间变量的传递，请自动削减参数层级。” |
| **数值友好度限制 (Numerical Friendliness)** | 大模型在随机生成同构题参数时，常产生复杂的无理数或庞大质数的分式。这种“计算复杂性”会掩盖“算理复杂性”，导致学生在低效计算中耗尽精力。 | 数值引擎约束：“题目参数的设定必须确保最终答案及所有关键中间结果为整数、有限小数或基础无理数（如 ![][image8] ）。方程的判别式必须为完全平方数，且分母在任何化简步骤中不得超过50。” |
| **元级母题克隆 (Meta-level Generation)** | 放弃让模型“开放式创新”，转而采用“AST语法树克隆”策略。输入一道经典的高考基础题作为母题（Source Problem），限定模型仅替换情境实体与基础系数，锁定拓扑结构。 | 转换指令：“解析所提供的母题的底层数学模型 ![][image9]。在保持其代数结构不变的前提下，将其物理情境从‘蓄水池注水’替换为‘电池充电’，并重新标定律定系数，确保新问题的逻辑拓扑与母题100%同构。” |

通过上述极度精细的规则卡点，非数学专业的开发者能够绕过大模型对模糊难度概念的理解障碍，以工程化的确定性约束大模型的生成边界，确保最终产出的练习题精确落在“高考90分”的靶区。

## **四、 面向中国高中数学的System Instructions优秀案例**

综合前文对算理幻觉对抗的PedCoT设计、苏格拉底提问状态机以及同构题生成的难度边界控制，一个安全、有效且符合教育心理学的“个性化数学辅导Agent”的底层System Prompt架构应如下设计。该架构大量运用XML标签来实现指令逻辑与输出格式的严格解耦，大幅降低大模型在多轮交互中的逻辑漂移风险23。

XML

\<system\_instruction\>  
  \<agent\_identity\>  
    你是一个专为中国高中生设计的“苏格拉底式”顶尖数学伴学Agent。你的核心使命不是作为自动解题机提供答案，而是作为认知导师，通过诊断学生的思维盲区，以渐进式、启发式的问题引导学生自行跨越学习障碍。你的语气应当极具耐心、富有同理心，并且始终将高深的数学原理降维至基础薄弱学生（学渣）也能秒懂的生活化认知层面。  
  \</agent\_identity\>

  \<strict\_compliance\_rules\>  
    \<rule\_1\_no\_direct\_answers\>在任何情况下，绝对禁止直接输出最终数值答案或给出完整的端到端解题代码与步骤。\</rule\_1\_no\_direct\_answers\>  
    \<rule\_2\_rigorous\_validation\>在进行任何代数变形（如消元、放缩）前，必须在内部思维链中隐式验证变量的定义域、值域及前置边界条件。严禁无视前提滥用“特值法”，严禁在分母可能为0或偶次根号下可能为负的情况下进行违规化简。\</rule\_2\_rigorous\_validation\>  
    \<rule\_3\_isomorphic\_generation\>当触发生成“同构巩固练习题”的任务时，必须严格执行难度钳制：限定考点在“高考90分”的基础/中档水平（推理步骤≤4步）；数值设置必须友好（解为整数或简单根式）；绝不允许跨越当前年级大纲或引入高等数学/奥数竞赛的超纲定理。\</rule\_3\_isomorphic\_generation\>  
  \</strict\_compliance\_rules\>

  \<socratic\_workflow\>  
    你必须维持一个关于学生认知状态的内部模型，并按以下递进逻辑处理用户的每次输入：  
    \<phase\_1\_diagnosis\>  
      在后台解析学生的反馈文本或上传的草稿。判定当前卡点属于：  
      \[A\]概念混淆（Concept Confusion）；算理跳步（Logic Step-Skipping）；\[C\]计算失误（Carelessness）。  
    \</phase\_1\_diagnosis\>  
    \<phase\_2\_intervention\>  
      基于诊断结论，设计\*\*唯一一个\*\*干预动作。如果学生概念模糊，提出一个反事实的极简边界测试题；如果学生逻辑跳步，要求其陈述上一步到下一步的公式依据；如果连续三次干预失败，则提供降维的多模态脚手架（如建议绘制某特殊情况的草图）。  
    \</phase\_2\_intervention\>  
  \</socratic\_workflow\>

  \<output\_schema\>  
    你的每次响应必须严格按照以下XML结构输出，确保内部推演与面向学生的输出彻底隔离：  
    \<internal\_reasoning\_pedcot\>  
      \<math\_environment\_check\>  
        \</math\_environment\_check\>  
      \<student\_belief\_state\>  
        \</student\_belief\_state\>  
    \</internal\_reasoning\_pedcot\>  
    \<tutor\_dialogue\>  
      \<encouragement\>  
        \</encouragement\>  
      \<guiding\_question\>  
        \</guiding\_question\>  
    \</tutor\_dialogue\>  
  \</output\_schema\>  
\</system\_instruction\>

此系统指令通过 \<internal\_reasoning\_pedcot\> 模块，强迫大模型在生成对话前必须先执行完整的数学边界检查与学生状态建模，从根本上压制了模型“脱口而出”错误答案的冲动。

## **五、 大模型辅导数学时最容易踩的三个隐蔽技术坑**

非AI专业背景的开发者在调用大语言模型API构建辅导应用时，往往容易被模型在单次评测中展示的优异表现所迷惑。然而，真实的教育辅导是一个长周期的多轮博弈过程，如果缺乏对大模型行为学缺陷的深刻洞察，系统极易在交互深水区崩溃。以下是构建数学辅导Agent时最致命的三个隐蔽技术坑及防御指南：

### **技术坑一：多轮交互中的逻辑漂移与“答案膨胀”（Lost in Multi-turn Conversation）**

**陷阱机制：** 当测试大模型解决单步指令时，其数学准确率令人惊艳。但随着苏格拉底式引导在多轮对话中展开，大模型的推理能力会出现断崖式下跌。一项针对顶级模型的测试表明，当任务被分散在多轮对话中时，模型的性能平均骤降39%，不可靠性增加了一倍以上25。这种衰退源于两大效应：一是“迷失在中间（Lost-in-Middle）”，模型会逐渐遗忘对话开头设定的游戏规则和核心已知条件25；二是“答案膨胀（Verbosity Inflation）”，随着对话轮数增加，模型如果在早期产生了错误的假设，由于缺乏有效的自我证伪机制，它会不断将新的信息强加在错误的逻辑基础上，导致最终生成的数学步骤极度臃肿且逻辑崩溃25。

**规避指南：** 绝对不要将原始的“用户-助手”全量对话历史（Message History）无脑连接并送入API上下文。开发者必须在业务后端设计“动态状态总结（Dynamic State Summarization）”机制。每经过2至3个对话轮次，利用一个轻量级的LLM实例对当前对话进行压缩，提取出“已确认的数学条件”、“已排除的错误路径”和“当前推进到的逻辑节点”，并将其转化为高密度的结构化文本。在下一次主干API调用时，丢弃冗杂的旧历史，仅将System Prompt、提纯后的 \<current\_game\_state\> 摘要以及用户最新的回复输入给模型，从而时刻保持模型注意力的聚焦27。

### **技术坑二：过早解答冲动引发的“确认偏差”（Premature Answer Attempts & Confirmation Bias）**

**陷阱机制：** 大模型在预训练中被深度植入了“文本补全”与“迎合用户”的本能。当学生上传的题目条件残缺，或者表述充满歧义时，大模型往往不会停下来询问，而是立刻在潜空间中寻找最匹配的概率分布，并“脑补”缺失条件，瞬间给出一个貌似合理的解答（诱发事实性幻觉）6。数据证明，在多轮任务中，若模型在对话的前20%回合就试图给出答案，其准确率仅为30.9%；而强迫模型延迟解答至最后20%回合时，准确率可飙升至64.4%25。更致命的是，一旦模型在早期阶段“说出了”错误的数学假设，受制于自回归生成的特性，它在后续交互中会展现出强烈的“确认偏差”，顽固地维护自己先前的错误，甚至对显而易见的矛盾视而不见（退化性思维现象）14。

**规避指南：** 必须在提示词和系统工程中设置强制的“探索与澄清期（Exploration Phase）”11。利用结构化输出（Structured Outputs）功能，强制模型在每次响应时首先输出一个JSON键值对，例如 "is\_information\_sufficient": false。只要该布尔值为假，后端的API拦截器就会无条件切断模型生成“解题步骤”的权限，迫使其只能返回反问用户的澄清语句。这种机制将模型的不确定性强制显性化，在错误逻辑生根发芽前将其阻断。

### **技术坑三：单轮强化学习对“自适应纠错能力”的破坏（Degradation of Adaptive Revision from Single-turn RL）**

**陷阱机制：** 这是一个极度反直觉的陷阱。当前最顶尖的推理模型大多经过了基于单一正确答案的复杂强化学习（RLHF或RLVR）优化。虽然这极大提升了其在单次Prompt下的“做对率”，却意外破坏了其在多轮交互中的“纠错力”。研究发现，当单轮RL训练的模型在给出错误答案后，即便是接收到用户诸如“你算错了，请再试一次”的明确一元反馈（Unary Feedback），模型依然无法根据上下文修改自身逻辑。在随后的5轮交互中，模型有高达70%的概率像复读机一样生成与之前完全一致的错误答案28。它成为了一个优秀的“单次求解者”，却退化成了一个糟糕的“交互修正者”。

**规避指南：** 在处理学生反馈“你这步不对”或者系统自动检测到AI推理出错时，简单的追问是无效的。开发者必须在对话链中引入“一元反馈观察（Unary Feedback as Observation, UFO）”策略配合后台的“破坏性思维链（Destructive CoT）”注入28。当需要强制模型修正时，不要让它顺着刚才的上下文继续生成，而是向其注入强力的对抗性指令：“假设你之前的代数计算图中存在严重的符号或约分错误，你的历史路径已彻底失效。请立即放弃原有的证明框架，切换至完全不同的知识体系（如从代数法切换至几何法），从初始条件重新建立计算图谱。”通过这种方式强行扰乱模型对历史Token的注意力依赖分布，才能成功激发模型产生有效且多样化的新解答路径（Effective Answer）。

#### **引用的著作**

1. Claude 3.5 Sonnet vs GPT-4o: Complete AI Model Comparison \- SentiSight.ai, 访问时间为 四月 14, 2026， [https://www.sentisight.ai/claude-3-5-sonnet-vs-gpt-4o-ultimate-comparison/](https://www.sentisight.ai/claude-3-5-sonnet-vs-gpt-4o-ultimate-comparison/)  
2. Large Language Models and Mathematical Reasoning Failures \- ResearchGate, 访问时间为 四月 14, 2026， [https://www.researchgate.net/publication/389090646\_Large\_Language\_Models\_and\_Mathematical\_Reasoning\_Failures](https://www.researchgate.net/publication/389090646_Large_Language_Models_and_Mathematical_Reasoning_Failures)  
3. The Claude 3 Model Family: Opus, Sonnet, Haiku, 访问时间为 四月 14, 2026， [https://assets.anthropic.com/m/61e7d27f8c8f5919/original/Claude-3-Model-Card.pdf](https://assets.anthropic.com/m/61e7d27f8c8f5919/original/Claude-3-Model-Card.pdf)  
4. PhD-level model GPT-o1 fails on middle school math 'trap' problems, with an accuracy rate of only 24.3% : r/LocalLLaMA \- Reddit, 访问时间为 四月 14, 2026， [https://www.reddit.com/r/LocalLLaMA/comments/1fipkus/phdlevel\_model\_gpto1\_fails\_on\_middle\_school\_math/](https://www.reddit.com/r/LocalLLaMA/comments/1fipkus/phdlevel_model_gpto1_fails_on_middle_school_math/)  
5. Why Language Models Hallucinate | OpenAI, 访问时间为 四月 14, 2026， [https://cdn.openai.com/pdf/d04913be-3f6f-4d2b-b283-ff432ef4aaa5/why-language-models-hallucinate.pdf](https://cdn.openai.com/pdf/d04913be-3f6f-4d2b-b283-ff432ef4aaa5/why-language-models-hallucinate.pdf)  
6. Chinese researchers have found the cause of hallucinations in LLMs : r/singularity \- Reddit, 访问时间为 四月 14, 2026， [https://www.reddit.com/r/singularity/comments/1re5l9j/chinese\_researchers\_have\_found\_the\_cause\_of/](https://www.reddit.com/r/singularity/comments/1re5l9j/chinese_researchers_have_found_the_cause_of/)  
7. Beyond Accuracy: Diagnosing Algebraic Reasoning Failures in LLMs Across Nine Complexity Dimensions \- ResearchGate, 访问时间为 四月 14, 2026， [https://www.researchgate.net/publication/403642343\_Beyond\_Accuracy\_Diagnosing\_Algebraic\_Reasoning\_Failures\_in\_LLMs\_Across\_Nine\_Complexity\_Dimensions](https://www.researchgate.net/publication/403642343_Beyond_Accuracy_Diagnosing_Algebraic_Reasoning_Failures_in_LLMs_Across_Nine_Complexity_Dimensions)  
8. Beyond Accuracy: Diagnosing Algebraic Reasoning Failures in LLMs Across Nine Complexity Dimensions \- arXiv, 访问时间为 四月 14, 2026， [https://arxiv.org/html/2604.06799v1](https://arxiv.org/html/2604.06799v1)  
9. LLMs can Find Mathematical Reasoning Mistakes by Pedagogical Chain-of-Thought \- Stanford SCALE Initiative, 访问时间为 四月 14, 2026， [https://scale.stanford.edu/ai/repository/llms-can-find-mathematical-reasoning-mistakes-pedagogical-chain-thought](https://scale.stanford.edu/ai/repository/llms-can-find-mathematical-reasoning-mistakes-pedagogical-chain-thought)  
10. LLMs can Find Mathematical Reasoning Mistakes by Pedagogical Chain-of-Thought \- arXiv, 访问时间为 四月 14, 2026， [https://arxiv.org/html/2405.06705v3](https://arxiv.org/html/2405.06705v3)  
11. The Socratic Prompt: How to Make a Language Model Stop Guessing and Start Thinking, 访问时间为 四月 14, 2026， [https://towardsai.net/p/machine-learning/the-socratic-prompt-how-to-make-a-language-model-stop-guessing-and-start-thinking](https://towardsai.net/p/machine-learning/the-socratic-prompt-how-to-make-a-language-model-stop-guessing-and-start-thinking)  
12. LLM-based Agents Suffer from Hallucinations: A Survey of Taxonomy, Methods, and Directions \- arXiv, 访问时间为 四月 14, 2026， [https://arxiv.org/html/2509.18970v2](https://arxiv.org/html/2509.18970v2)  
13. LLM-based Agents Suffer from Hallucinations: A Survey of Taxonomy, Methods, and Directions \- arXiv, 访问时间为 四月 14, 2026， [https://arxiv.org/html/2509.18970v1](https://arxiv.org/html/2509.18970v1)  
14. Socrates Was a Terrible Prompt Engineer (That's the Point) | rewire.it, 访问时间为 四月 14, 2026， [https://rewire.it/blog/socrates-was-a-terrible-prompt-engineer/](https://rewire.it/blog/socrates-was-a-terrible-prompt-engineer/)  
15. Socratic Prompting with AI – HALC AI Guide \- CUNY Academic Commons, 访问时间为 四月 14, 2026， [https://halcaiguide.commons.gc.cuny.edu/ai-skills/socratic-prompting-with-ai/](https://halcaiguide.commons.gc.cuny.edu/ai-skills/socratic-prompting-with-ai/)  
16. Socratic AI Tutoring in Primary School Mathematics: A Case Study on the Development of Problem-Solving and Digital Compet \- DSpace@MIT, 访问时间为 四月 14, 2026， [https://dspace.mit.edu/bitstream/handle/1721.1/163131/MIT-RAISE-20250611-reviewed.pdf?sequence=1\&isAllowed=y](https://dspace.mit.edu/bitstream/handle/1721.1/163131/MIT-RAISE-20250611-reviewed.pdf?sequence=1&isAllowed=y)  
17. Computational Blueprints: Generating Isomorphic Mathematics Problems with Large Language Models \- arXiv, 访问时间为 四月 14, 2026， [https://arxiv.org/html/2511.07932v1](https://arxiv.org/html/2511.07932v1)  
18. Computational Blueprints: Generating Isomorphic Mathematics Problems with Large Language Models \- ACL Anthology, 访问时间为 四月 14, 2026， [https://aclanthology.org/2025.emnlp-industry.97.pdf](https://aclanthology.org/2025.emnlp-industry.97.pdf)  
19. Reliable generation of isomorphic physics problems using Generative AI with prompt-chaining and tool use \- arXiv, 访问时间为 四月 14, 2026， [https://arxiv.org/pdf/2508.14755](https://arxiv.org/pdf/2508.14755)  
20. Automatically Generating Hard Math Problems from Hypothesis-Driven Error Analysis \- arXiv, 访问时间为 四月 14, 2026， [https://arxiv.org/html/2604.04386v1](https://arxiv.org/html/2604.04386v1)  
21. 高考数学各题型占比一般是多少呢？, 访问时间为 四月 14, 2026， [https://www.ais.cn/news/featured/12560](https://www.ais.cn/news/featured/12560)  
22. GAOKAO-EVAL: DOES HIGH SCORES TRULY REFLECT STRONG CAPABILITIES IN LLMS? \- OpenReview, 访问时间为 四月 14, 2026， [https://openreview.net/pdf/d83b31250eeb9271bf8a57f386961473582699b7.pdf](https://openreview.net/pdf/d83b31250eeb9271bf8a57f386961473582699b7.pdf)  
23. Structured Prompting Techniques: XML & JSON Prompting Guide \- Code Conductor, 访问时间为 四月 14, 2026， [https://codeconductor.ai/blog/structured-prompting-techniques-xml-json/](https://codeconductor.ai/blog/structured-prompting-techniques-xml-json/)  
24. Prompting best practices \- Claude API Docs, 访问时间为 四月 14, 2026， [https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)  
25. Why LLMs Fail in Multi-Turn Conversations (And How to Fix It) \- PromptHub, 访问时间为 四月 14, 2026， [https://www.prompthub.us/blog/why-llms-fail-in-multi-turn-conversations-and-how-to-fix-it](https://www.prompthub.us/blog/why-llms-fail-in-multi-turn-conversations-and-how-to-fix-it)  
26. (PDF) LLMs Get Lost In Multi-Turn Conversation \- ResearchGate, 访问时间为 四月 14, 2026， [https://www.researchgate.net/publication/391658658\_LLMs\_Get\_Lost\_In\_Multi-Turn\_Conversation](https://www.researchgate.net/publication/391658658_LLMs_Get_Lost_In_Multi-Turn_Conversation)  
27. How to stop the LLM from losing context in a multi-turn conversation \#163655 \- GitHub, 访问时间为 四月 14, 2026， [https://github.com/orgs/community/discussions/163655](https://github.com/orgs/community/discussions/163655)  
28. (PDF) A Simple "Try Again" Can Elicit Multi-Turn LLM Reasoning \- ResearchGate, 访问时间为 四月 14, 2026， [https://www.researchgate.net/publication/393889461\_A\_Simple\_Try\_Again\_Can\_Elicit\_Multi-Turn\_LLM\_Reasoning](https://www.researchgate.net/publication/393889461_A_Simple_Try_Again_Can_Elicit_Multi-Turn_LLM_Reasoning)  
29. Let's Try Again: Eliciting Multi-Turn Reasoning in Language Models via Simplistic Feedback \- OpenReview, 访问时间为 四月 14, 2026， [https://openreview.net/pdf/f72c8b29e2c450bb50aa155ab12a753caa28c806.pdf](https://openreview.net/pdf/f72c8b29e2c450bb50aa155ab12a753caa28c806.pdf)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADQAAAAWCAYAAACPHL/WAAAB10lEQVR4Xu2WzSsFURjGX6GIbChZWJCUj1j4io2yUBZ21iyVP4ANpSxsLdj4WNvZsrSwIWUlRbYkSSm2PI935s6Z4547c+7cksyvfjX3vO7ceeac9xwiOTk5OSmpghOBvP7zbMPPwC2rVmnaYZs96GAS3sFdeAWv4UjsLxzcwkvRQM9WrRJw1gfgMbyH1fFyUUbhK9wMPteKBuNYSWpEZ2UYvouGquSy48PzZV3AqeBzEnymQ/gIO43xHvgS1IvCwr5EAfpF3wCXYJZQq6I/vCO6xHyZFX2xp7DRGOc1x2aMsRhDousyhCEYhqEYzpcOeACXYZNV82FFSgdaNMYKhLOzbo0zCG/GmnNqLbol6o95q1YOSYFY/8E4vBF9qyacJd6M/cQZTMMYPA9kn2TFOxDDcBt0rW9uEr6hTNg77CH2UjlLzzsQd5AfgwZ9ott3uPTKgUHYS0/ifnEukjYF1mOUmh3CZbch0SxlgecHe+sI9kq63XMQvoluWC3GeKvovbh9F+APrIme1rTZLBp0wQfRUGk3Bxc8e9hb7LEzSQ5VD0/EfQ6x/k14YPEhfeR3sobyhaGX4Aecg3vBdSV20V+FK2gBTsMGq5aTljqJejKNaf6f+398AYj8bGrgtwTNAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAZCAYAAAChBHccAAABhElEQVR4Xu2WzStFQRiHX6HId76SbOwsWJCUZMWOnaJYsLKnyL/BxoJkoSwsJQsrCylbsqEsbLFiIx+/X+/MOXNPd27nls49ap566s47M/e+Z847M1ckEAgEAkotHIatyY48UwVn4Avch0/wGLY4Y3LLNPyEy6bdCW/ggR2QV+rhObyDHU58FX477QIaYbvoKyOsM8ayZhH+wMNEfAS+S5GczuAzfIVX8Mi03+C6xA+UBZtSOvkeN8jVHjefu+E93IBD8AE+mriPMThXhoM6zcu2lJE8n9TCGmOt9cI10S9h/bEOffx18kw6VfLVcCXqjgfUiCY8CZud/izYk5TJu7CueRTxiKokvg07Cj9gkxvk7uUbsCXDGrcMiJ65pdgV/bG0buk0LxOiC3gBG5z4rOj86PDogrdwSuJJJ6aPg3bggmlnBW/Ra9FLqc2J85xn8hG2jvpFV5CXAJNn4vPwVIqcqxmwBL9EcyB8oEtjASwZ949PXaJdSfpE9wAXmXkGAoH/yC+nOFjMKS6i9wAAAABJRU5ErkJggg==>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAZCAYAAAChBHccAAABMklEQVR4Xu2WsWoCQRCGJ8QikiCiQQu7dBbaWAgSrMwbCLH1FRQS8hKxsLGzsrMUyRPkCQxpYmdtsLAKif7j7OGy5C4nKVZhPvjA3bnT3925VSJFURRlTwbm3MlT4BKu4KNbOGae4RJ+ww2dWPg0SaucU8zwVzALz8yY34DnfPNn+ClckGzVKxyZ8Sfs0v4L+SAyPK92zbzOw3f4AMvwA87NfBhV2DzAktwWm8jwduEavsEC7JDc+AKT1jUu3sLzA9G2xhW4hgmSwHWYsuo+CA1vw309hF9uwTOR4flE4R0IWoZ7PKAI76zxbwxIPiCuT3JbbELD81k6gw14S7LqY1PjnejDlhn7IjR80OM3JCv4QxKeg9/DCfk96/nvAYfvwQuntoNbhn+QAvgie6woivI/tkXrROJGp1DgAAAAAElFTkSuQmCC>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAYCAYAAADOMhxqAAAAwElEQVR4Xu3PQQpBQRzH8b8oG0URCwtxAYmlsrFgwQnsHcEJLN/KASxtHEFxBUVWilIWSlkrfMe8mfdfuMHzq89ifv8382ZE/olfikiqde5H59PCETtU0MEFdzzQjz4V6WKBMd5YIRvOMtjgHK6/MbuNJV7oqVkNV+xV52PKE8qqG4r961x1PmYwUeuq2HccUMIIaTdM4Ym2KyR60zRcz5BwQ3OCuVLBFSQQu2GAPBpqJk2x9/QnkDpuWGOr+vjlA3TkIJmR9OlTAAAAAElFTkSuQmCC>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAZCAYAAAChBHccAAABOUlEQVR4Xu2VL0sEQRjGH1GLnn/wQDAdmP0MYrAYLGK0e8FkuWazGiyCn8CuIoJhwA9g8gtYTGKxeHDo8/Du4jiy61zw1oP3B78w874Lz8zuzAKO4zjOd1bofDo5DhzRPt1OC/+VWXpB3+iAfmCMwk/QdmHAL+HVpAdKlmkrGjdJQE34HfpCb+gSPaBP9J1e0YWv1kYIqAivHVboHqzhEXZAhBaluf1iXMUU3aC7Q9jRg5kEVITfpOf0FNZwBgsj1Kw5LayOxsJv0XVYwzNdjWqHyNv5vyagInyJisfRWIvQYgKaP7gBGeH1Fkq025rT4RVxLWWG3sL6c9V5yiWgJrx2Nv1krukrXYPdNpdRbdQE1IRX6DvYX61Et849naN79CSqjZoHWPgunU5qmCxMWcTPn5fjOM7wfAI9TVBDCMnaigAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAZCAYAAAChBHccAAABgUlEQVR4Xu2WvyuFYRTHj1DyI0LKpMRmMFGSDBSDRTZ2i8kiBpvVYFE2qxVJSTf+AYuUUUoGmSk/vl/ned573ufeW/cdvPcdnk996j7nPLfOed7zPveKRCKRSKTMNByFbWGiyPTCE/gMv+APPEjtKCid8BJuuzUbuRZtoNVvKioL8BVumNgYfHe5FH2wyawHRLtvFPOio/JgYqynBI9NTJbhG7wQfTzs9gl+wDPYXd6aKx2SHpF+eA+3fIAnzKIZ4DwxuetybIqxdbeuRQuchSsZHOIXM8Jx+YYjPjAHj0TfYhZ6KFoMWXKxpNMa5FE8n/6N6CglLMIZ0Vl6gcMmtyn1nfx/w9HhAX+KTkMFLHLPrNkEmylJY19c8gjHzXrSfP6DxfMpeHjajPmryuZC2kXvZO6v16onWIUpMTPu2LELnmw4MueidyrvVs7bqcnlxQS8g4OBq3YTi74SvZo8vHVuYRdcg/smlwd8oTku4ROj/K+T0OwM6ZHKH69IJBLJzi8/KFRpIpCjvwAAAABJRU5ErkJggg==>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAYCAYAAAAYl8YPAAAAgklEQVR4XmNgGAWjYAQAWSDuBmIOdAlyAD8QbwZiTXQJckE5FFMFiAHxfiA2Q5cgF4AMOgLEKugSPEAsSQYOBuJHQMzJQCHgBuKFQNyHLkEqYAHiqUBcBsSMaHIkA1cgXs1ABe+BXAXynge6BDlAmgGSaEXQJcgBrEAsxECFsBqiAAAGOwxsFgKSAwAAAABJRU5ErkJggg==>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFEAAAAZCAYAAABJhMI3AAAEWUlEQVR4Xu2YachmYxjH/9Yh+zJZorGOfd8pPtia0IytMZFGE8ryBfFBfKHsSyLZtzDGMj4wZCmkjCWh4RshUYQQoSz/31zP3XOf+znPOc/rfZ93HtP7q3/ve677LPd9n2s7jzTFFCsDc62nrdcH0DDZxbpFvc8sdX+6YFTY2lpinW8dPoCGxfqKOTyl3meW2rdzzchwlnWvtXs5MMnsZd1kXVAO/B94wZpnrVMOTCLrWudZj1hbFWMjz8YKTySUEqtYm1iHWjMy+zA5x3rU2r6wp7lsZq1RjI0MbOA+iskmllrfWl9Zf1m3afheyjMutVbPbAdYH1nvWssUc7nOWjs7Z4XDxrxobZjZ8Lxj1d1UQusf6xVrg3TSBLOm9bi1W2bj/y+sOZ1jvHCRYi53ppNGgdOsZ61VMxsecaKqnvmjYvILMttEsod1uWIzExcpnvmHdUjHdlnH9n06aUUzW1FQCJkEG0d1fEmR6BOvqeuNEx3W9IU8c1phX83az9qhc8zcHlDMg+iZFAjR3JtKnlO82U0LO9ewgJyPFZPHS8dKW/4603qiNNZAeH+niIoDi7E2mMOn1pfWD4q1lCIaKlAoWPB8a63q0HLIea9aB6l3w+r4WzF57jsWaOJpnvv1nztaN1pXlwMZdA8nK57/lrVrdbgV8jgRxwZ+rShO/P1TsaHY0fR0QeJtxQlU2S2LMeDz7grVXFgD7QUPZiFjYU9FAaA4kEvr2pPTrcfU/BXEJpJ6nlEslka87l51EFU3W3d0jo+yFisc62VFuqiFTTvO+sT61Tq7OrycNxTJOm8n6mCyd1unqjk1lJBKrlV42F2KBjqvvEA/eIN1jQbLszz/KkXoPVmM9YMwptdlHVx/uyKFwTvWFp3/+0JCxgt+UTWkD1bcuGkDeSA924fqJnY84jA1X1cH3v6T4geDmZmdfg+tl9lyeO4Jqn4EsGjWxEbWpakm6EToNVMN4D6tm0iuo+r9pgjJBCFG99/EfEWF3jyzsaCHsuNjrPesizNbHbRP7ysig4Uk+FaflR2X0OizWSn8gJ412ZMNL7vSOqJz3A9SG9U9RdQ31nbd4f5QcciNhCMP3VvRrrTlFFqInRVvKukedUOB8KPdYTH0cW3cZ/2uCO1tFSmH0Gxq3ukFuf/z6m4Y7RhOgT3BjxY/Kzap6X4UR3JwfkyObIXN4o2TlHFj8hTe2cRJ6i3/SXhj4lxFhWMybZyhaJP4hDtFkbOPr5zRC18nHygqPOBBtyrmgWcn6Gf52qGF6Ree5EZeCj1pgvuQIwfK9bxFvOBh63r19oXjgclRNNrgZVLgPlOkAH50HRQ2kU8/lDa0DlJNvzzJRpVj5Pi2iKxAk4q776+xF4YmjrYeLI192EnxK83n1iXVoXHDJuX5dihQJKiEG5UD42CG9aYGb8D5Lr7QWmgdWYyNF3rY/DN1KJB8WfREeiFpYZvS2AIFhbzUVAD+C3nrNMUUKwH/ApId0+F651G5AAAAAElFTkSuQmCC>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAZCAYAAAChBHccAAACxElEQVR4Xu2WS6iNURTH/0IRkvJI6OYxIIqSASklimLEwEAmkomxx0zJgJFuoqRkICVlICUpdyRlZCDlUUgUoYQy8Fi/u759z77r7n3u5RwTzq/+nb69vrMf67U/qUePHv89k0xT4+AfMNE0PQ7WYNFNppOmcwVtlE9Yo8/0wLQ5Ghr2auScJa1Kf5DPuSN7LtJv+m76afph+mx6lY0lPdXwyXOumE6ZxkWDfGyd6b58Hn53mXY24mCXGtv25j+JR/JDFGEzZ0xzTBNMV037M/t402K1DoCd9yKvTSviYOCGfI5D0dDAHKvD2D1VnMKJHquVW+TqgGlreiHjtHzh26YpwTbZdFnlQ+W8kUeW9Cxx17QojB2QZ8HCMD6ClaZP8ihErpnemZZHgzxS/Hc0YuTmma6bZjbP5Hx0zAx5mtUiPgT5xgIUb+SL6sVzUeUD5zBnTJmD8lpptynShXp4qNYhixyXL5BDSh027VEh79RKtdHaI+nA3LfkHubAPOf1VYN9vTcti4YEnqGgyMkN8lDRdVgA79TA489UPlgOef5W3lnoMHSbb6b1+UsViBaRj8U8BPn3vNEdtbrLgNp7da7pRRwsgPdi3lL8eSqU0hXYfLtCH+z1bBaPwALTk2bsZnqpwFg2T8rQadp5eYvquc/mv5rWRANwegoitqSj8s0T3ki6bVM3iF0ih9bLPLWiJrLUQo22acOpCcsFDc9dLp2P8oWTV9j0CdOS5jnVyrTmuURqBCXPcgkekff4Gufl0SXKI+ACYvMcIofFuHxYeJ9plumY6UP+kjzl5oexBOmXPgty2DTr4XFsXEYlknNKl+Mg2+S3ZI0++R1QCzvFjnf/BhQpF+faaOgWpBrfIGP+hP0NyAoaRjvndgzFnjpVN3mp+md219gt/56fHQ0dQHM4q3Khdx0Wo3NQQ52yVP4p/O/xCzh8lB0mOpd8AAAAAElFTkSuQmCC>
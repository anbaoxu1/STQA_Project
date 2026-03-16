Project README
本项目包含多智能体与多任务场景下的实验代码与数据，包括主实验、消融实验（Ground Truth）、QA 数据生成与预测、SQL 查询验证、以及时序预测与股票趋势预测等模块。

环境配置
依赖环境通过 requirements.txt 管理，请使用如下命令安装：

bash
pip install -r requirements.txt
主实验入口
主实验脚本：main_test_agent_all_template.py

功能：作为整体多智能体路由 / 工作流实验的主入口，用于调度各类子任务与模板代码，实现端到端实验流程（如调用不同的 prompt、数据模板及模型推理代码）。

消融实验：Ground Truth 模块
Ground Truth 脚本：llm_tranformer_stock_qwen_ground_truth_wf_template.py

功能：

实现消融实验中 Ground Truth 相关的工作流，用于对比「直接 LLM 预测」和「基于 Ground Truth / 结构化流程」的性能差异。

适用于股票相关任务（例如行情、趋势、问答等）的参考工作流设定。

QA 相关模块
1. BERT 微调
文件：bert_train_test_template.py

功能：

基于 QA 数据集对 BERT 模型进行微调与评估。

支持对 train / validation / test 等划分数据进行训练与测试。

2. QA 查询类模板
文件：query_template.py

功能：

定义 QA 查询类数据集模板，主要用于“提问-回答”式的任务建模。

3. QA 预测类模板
文件：template_predict_QA.py

功能：

定义 QA 预测类数据集模板，主要用于“提问-回答”式的任务建模。

将原始 query / question 转换为模型可接受的输入格式，并生成相应的标签或目标字段。

4. QA 改写模板
文件：replace_rewrite_template.py

功能：

针对 QA 数据进行问句改写、同义表达重写等操作。

可用于构造多样化问法的数据集，以提升模型对不同表达方式的鲁棒性。

5. QA 生成数据集模板（所有意图）
文件：template_generate_template.py

功能：

针对**所有意图（多任务、多类型 QA）**生成统一格式的数据集。

支持将不同类型任务（如预测类、查询类、SQL 类等）统一转化为统一 schema 的 QA/指令式数据，便于统一训练或评测。

SQL 查询与验证模块
文件：sql_verify_template.py

功能：

实现 SQL 查询的生成与执行验证逻辑。

用于从自然语言问题生成 SQL，执行后验证结果是否正确或可用。

时序预测与股票趋势模块
1. Time-MoE 时序预测
文件：Train-Timemoe_template.ipynb

功能：

实现基于 Time-MoE 模型的时序预测实验。

适用于时间序列数据如行情、指标序列的建模与预测。

2. 股票趋势预测数据填充
文件：Stock Trend Prediction_template.py

功能：

针对预测类意图数据集进行填充与构造，例如：

股票趋势预测

指标上升/下降判断

将原始行情/标签信息组织成可用于训练预测模型的样本。

QA 数据集说明
项目中的 QA 数据集主要包含三部分：

训练集：train_merged.json

验证集：val_merged.json

测试集：test_merged.json

这三份文件共同构成完整的 QA 任务数据，用于 BERT 微调、LLM 任务训练或评测等场景。

Prompt 配置说明
Prompt 文件位于 Prompt/ 目录下，不同文件对应不同实验与意图：

direct_pred_prompt_baseline_english.json

用途：

消融实验中 通过 LLM 直接预测 的 baseline prompt。

不依赖中间结构化流程或辅助模块，直接用 LLM 进行任务回答或预测。

history_sql_prompt_english.json

用途：

对应 “history_sql” 相关任务的 prompt 模板。

面向带历史信息的 SQL 生成/查询场景（如根据历史问答或上下文构造 SQL）。

sql_prompt_english.json

用途：

用于SQL 查询生成的 prompt 模板。

输入为自然语言问题，输出为对应的 SQL 语句，引导 LLM 按格式生成可执行 SQL。

典型使用流程（示例）
安装依赖

bash
pip install -r requirements.txt
准备数据

将 train_merged.json, val_merged.json, test_merged.json 放置于指定数据目录（与代码对应）。

QA 相关实验

使用 bert_train_test_template.py 对 BERT 进行 QA 微调与评估。

使用 query_template.py / replace_rewrite_template.py / template_generate_template.py 完成不同意图的 QA 数据构造与改写。

SQL 相关实验

使用 sql_verify_template.py + sql_prompt_english.json / history_sql_prompt_english.json 进行 SQL 生成与验证实验。

时序与股票相关实验

使用 Train-Timemoe_template.ipynb 进行 Time-MoE 时序预测实验。

使用 Stock Trend Prediction_template.py 构建股票趋势预测相关数据集与任务。

主实验与消融实验

通过 main_test_agent_all_template.py 运行整体多智能体工作流实验。

使用 llm_tranformer_stock_qwen_ground_truth_wf_template.py 运行 Ground Truth 消融实验，与 direct_pred_prompt_baseline_english.json 的直接预测结果进行对比。


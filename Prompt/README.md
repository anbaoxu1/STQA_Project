
## Prompt Design Guidelines
When editing or extending prompt files, follow these guidelines:
### 1. Preserve Valid JSON Syntax
- Use double quotation marks.
- Do not add trailing commas.
- Escape special characters when necessary.
- Ensure that all braces and brackets are correctly closed.
### 2. Keep Placeholder Names Consistent
Placeholders such as:
```text
{input}
{question}
{history}
{schema}
{table_name}
{output_format}
```
must match the variables used by the corresponding Python scripts.
### 3. Specify the Output Format Clearly
For structured tasks, explicitly define the expected output format.
For SQL generation, specify whether the model should return:
- Only the SQL statement
- A JSON object containing SQL
- SQL together with an explanation
If the output is automatically parsed or executed, returning only the required structured content is recommended.
### 4. Avoid Unnecessary Explanations for SQL Tasks
If generated SQL is directly passed to an execution module, instruct the model not to include:
- Markdown code fences
- Natural-language explanations
- Additional notes
- Multiple alternative SQL statements
A suitable instruction is:
```text
Return only the executable SQL statement without Markdown formatting or additional explanation.
```
### 5. Maintain Consistency Across Experiments
When comparing the direct-prediction baseline with a structured workflow, keep the following settings consistent whenever possible:
- Input samples
- Model configuration
- Temperature
- Maximum output length
- Evaluation metrics
- Output parsing rules
This ensures that the comparison focuses on the difference in workflow or prompting strategy.
---
## Adding a New Prompt File
To add a new prompt configuration:
1. Create a new JSON file under the `Prompt/` directory.
2. Define the task instructions, input placeholders, and output requirements.
3. Ensure that the file contains valid JSON.
4. Add the prompt-loading logic to the corresponding Python script.
5. Test the prompt on a small number of samples.
6. Add the new prompt file to the mapping table in this README.
For example:
```text
Prompt/
└── new_task_prompt_english.json
```
Then load it in Python:
```python
import json
prompt_path = "Prompt/new_task_prompt_english.json"
with open(prompt_path, "r", encoding="utf-8") as file:
    prompt_config = json.load(file)
```
---
## Validation
Before running an experiment, validate the prompt JSON files.
For example:
```bash
python -m json.tool Prompt/direct_pred_prompt_baseline_english.json
python -m json.tool Prompt/history_sql_prompt_english.json
python -m json.tool Prompt/sql_prompt_english.json
```
If a file is valid, the command prints the formatted JSON content. Otherwise, it reports the location of the syntax error.
---
## Notes
- Do not rename prompt files unless the corresponding paths in the Python scripts are also updated.
- Keep the prompt language consistent with the target dataset and evaluation setting.
- Ensure that all placeholders expected by the code are included in the prompt file.
- SQL prompts should be consistent with the actual database schema.
- Direct-prediction and structured-workflow experiments should use the same input data for a fair comparison.
- Do not store API keys, passwords, database credentials, or other sensitive information in prompt files.

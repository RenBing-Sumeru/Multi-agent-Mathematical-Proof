
"""存放所有用于与LLM交互的Prompt模板"""

DEFINITION_GEN_PROMPT = """
You are an expert in mathematics. Below is a mathematical definition. I need you to produce 6 similar but incorrect definitions by modifying 1 to 3 places of the original definition. Some possible methods to do so are replacing keywords and conditions with similar but incorrect ones, or changing the formulas to similar but incorrect ones (but you are also encouraged to use methods other than these).
You should only make mathematical modifications, and avoid those non-mathematical modifications. In particular, modifications related to references such as changing things inside a \\ref{}, or changing the index of a refered lemma should not be made.
Your goal is to make the incorrect definitions undistinguishable to non-experts, so non-experts cannot tell whether the incorrect definitions are correct or not. Thus you should make your modifications as subtle as possible.
Please double check to ensure all the incorrect definitions you produce are indeed incorrect.

Output format: Only output the 6 incorrect definitions and nothing else. You don't need to provide any explanations. The incorrect definitions should be placed inside [incorrect_definition_i-start] and [incorrect_definition_i-end], so your output should be formatted as:
[incorrect_definition_1-start]
"incorrect_definition_1"
[incorrect_definition_1-end]
[incorrect_definition_2-start]
"incorrect_definition_2"
[incorrect_definition_2-end]
...
[incorrect_definition_6-start]
"incorrect_definition_6"
[incorrect_definition_6-end]
"""

PROOF_GEN_PROMPT = """
You are an expert in mathematics. Below is a mathematical proposition and its proof. I need you to produce 6 similar but incorrect proofs by modifying 1 to 3 places of the original proof. Some possible methods to do so are replacing keywords and conditions with similar but incorrect ones, or changing the formulas to similar but incorrect ones (but you are also encouraged to use methods other than these).
You should only make mathematical modifications, and avoid those non-mathematical modifications. In particular, modifications related to references such as changing things inside a \\ref{}, or changing the index of a refered lemma should not be made.
Your goal is to make the incorrect proofs undistinguishable to non-experts, so non-experts cannot tell whether the incorrect proofs are correct or not. Thus you should make your modifications as subtle as possible.
Please double check to ensure all the incorrect proofs you produce are indeed incorrect.

Output format: Only output the 6 incorrect proofs and nothing else. You don't need to provide any explanations. The incorrect proofs should be placed inside [incorrect_proof_i-start] and [incorrect_proof_i-end], so your output should be formatted as:
[incorrect_proof_1-start]
"incorrect_proof_1"
[incorrect_proof_1-end]
[incorrect_proof_2-start]
"incorrect_proof_2"
[incorrect_proof_2-end]
...
[incorrect_proof_6-start]
"incorrect_proof_6"
[incorrect_proof_6-end]
"""

DEFINITION_EVAL_PROMPT = """
Below is a mathematical definition. Please think step by step and judge whether it is a correct definition or not. Here "correct" means mathematically correct, so you should only focus on whether the mathematics and logic in it are correct, and your judge should not be influenced by those non-mathematical things. In particular, your judge should not be influenced by things related to references such as things inside a \\ref{}, or the index of a refered lemma.
\nOutput format: you should put your final judge inside a \\boxed{}, and put it at the end of your output. So you should return \\boxed{T} if you think the definition is correct, and \\boxed{F} if you think the definition is incorrect.
\nHere is the definition:
"""

PROOF_EVAL_PROMPT = """
Below is a mathematical proposition and its proof. Please think step by step and judge whether the proof is correct or not. Here "correct" means mathematically correct, so you should only focus on whether the mathematics and logic in it are correct, and your judge should not be influenced by those non-mathematical things. In particular, your judge should not be influenced by things related to references such as things inside a \\ref{}, or the index of a refered lemma.
\nOutput format: you should put your final judge inside a \\boxed{}, and put it at the end of your output. So you should return \\boxed{T} if you think the proof is correct, and \\boxed{F} if you think the proof is incorrect.
\nHere is the proposition:
"""
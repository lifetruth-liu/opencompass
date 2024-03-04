from mmengine.config import read_base

with read_base():
    from .models.chatglm.hf_chatglm3_6b import models
    # from .datasets.humaneval.humaneval_gen_a82cae import humaneval_datasets
    from .datasets.mbpp.mbpp_gen_1e1056 import mbpp_datasets
    from .datasets.mmlu.mmlu_ppl_ac766d import mmlu_datasets

    from .summarizers.groups.mmlu import mmlu_summary_groups

datasets = sum((v for k, v in locals().items() if k.endswith('_datasets')), [])

summarizer = dict(
    dataset_abbrs=[
        '--------- 考试 Exam ---------',  # category
        # 'Mixed', # subcategory
        'mmlu',
        'cmmlu',
        '--------- 推理 Reasoning ---------',  # category
        # '代码', # subcategory
        'mbpp',
    ],
    summary_groups=sum(
        [v for k, v in locals().items() if k.endswith("_summary_groups")], []),
)
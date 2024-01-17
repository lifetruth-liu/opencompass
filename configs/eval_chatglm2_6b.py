from mmengine.config import read_base

with read_base():
    from .models.chatglm.hf_chatglm2_6b import models
    from .datasets.humaneval.humaneval_gen_a82cae import humaneval_datasets
    from .datasets.mbpp.mbpp_gen_1e1056 import mbpp_datasets
    from .datasets.mmlu.mmlu_ppl_ac766d import mmlu_datasets

datasets = sum((v for k, v in locals().items() if k.endswith('_datasets')), [])
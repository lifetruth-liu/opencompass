from mmengine.config import read_base

with read_base():
    from configs.datasets.mmlu.mmlu_ppl_ac766d import mmlu_datasets
    from configs.datasets.triviaqa.triviaqa_wiki_gen_d18bf4 import triviaqa_datasets
    from configs.datasets.nq.nq_open_gen_e93f8a import nq_datasets
    from configs.datasets.gsm8k.gsm8k_gen_3309bd import gsm8k_datasets
    from configs.datasets.humaneval.humaneval_gen_a82cae import humaneval_datasets
    from configs.datasets.agieval.agieval_mixed_2f14ad import agieval_datasets
    from configs.datasets.SuperGLUE_BoolQ.SuperGLUE_BoolQ_ppl_314797 import BoolQ_datasets
    from configs.datasets.hellaswag.hellaswag_ppl_a6e128 import hellaswag_datasets
    from configs.datasets.obqa.obqa_ppl_6aac9e import obqa_datasets
    from configs.datasets.winogrande.winogrande_ll_c5cf57 import winogrande_datasets
    from configs.models.hf_llama.hf_llama2_7b import models
    from configs.summarizers.example import summarizer

datasets = sum([v for k, v in locals().items() if k.endswith("_datasets") or k == 'datasets'], [])
work_dir = './outputs/llama2/'

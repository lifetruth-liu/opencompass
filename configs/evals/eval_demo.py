from mmengine.config import read_base

with read_base():
    from configs.datasets.siqa.siqa_gen import siqa_datasets
    from configs.datasets.winograd.winograd_ppl import winograd_datasets
    from configs.models.opt.hf_opt_125m import opt125m
    from configs.models.opt.hf_opt_350m import opt350m

datasets = [*siqa_datasets, *winograd_datasets]
models = [opt125m, opt350m]

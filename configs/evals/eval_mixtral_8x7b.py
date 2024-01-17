from mmengine.config import read_base

with read_base():
    from configs.datasets.collections.base_medium_llama import piqa_datasets, siqa_datasets
    from configs.models.mixtral.mixtral_8x7b_32k import models


datasets = [*piqa_datasets, *siqa_datasets]

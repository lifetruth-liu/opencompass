from mmengine.config import read_base

with read_base():
    # choose a list of datasets
    from configs.datasets.collections.base_medium import datasets
    # choose a model of interest
    from configs.models.internlm.internlm_7b import models
    # and output the results in a choosen format
    from configs.summarizers.medium import summarizer

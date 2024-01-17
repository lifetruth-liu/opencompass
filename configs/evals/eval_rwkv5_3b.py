from mmengine.config import read_base

with read_base():
    from configs.models.rwkv.rwkv5_3b import models
    from configs.datasets.collections.base_medium_llama import datasets
    from configs.summarizers.leaderboard import summarizer

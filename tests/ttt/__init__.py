# -*- coding    : utf-8 -*-
# @Time         : 2024/1/12 10:23
# @Author       : 领悟悟悟
# @Email        : lsz4123@163.com
# @Comment      :

from configs.datasets.mbpp.mbpp_gen_1e1056 import mbpp_datasets
from configs.datasets.bbh.bbh_gen_5bf00b import bbh_datasets

datasets = sum((v for k, v in locals().items() if k.endswith('_datasets')), [])

print(datasets)
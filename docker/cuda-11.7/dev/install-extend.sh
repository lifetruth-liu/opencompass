#!/usr/bin/env bash

cd /root
git clone https://githubfast.com/openai/human-eval.git
mv human-eval .human-eval
cd .human-eval
rm -rf .git .github
sed -i 's/#  / /g' human_eval/execution.py
pip install -r requirements.txt
pip install -e .

cd /root
git clone https://githubfast.com/facebookresearch/llama.git
mv llama .llama
cd .llama
rm -rf .git .github
pip install -r requirements.txt
pip install -e .

cd /root
git clone https://githubfast.com/Dao-AILab/flash-attention.git
cd flash-attention
cd csrc
rm -rf cutlass
git clone https://githubfast.com/NVIDIA/cutlass.git
rm -rf cutlass/.git cutlass/.github
cd ..
pip install packaging ninja
python setup.py install
cd csrc/layer_norm
python setup.py install
cd ../rotary
python setup.py install

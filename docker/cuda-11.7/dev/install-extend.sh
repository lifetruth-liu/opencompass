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
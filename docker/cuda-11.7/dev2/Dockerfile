FROM cuda:python-3.10.13-cuda-11.7.1-cudnn8-devel-ubuntu22.04

ENV HF_ENDPOINT="https://hf-mirror.com"
ENV HF_DATASETS_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1
ENV HF_EVALUATE_OFFLINE=1
ENV NUM_GPUS=auto
ENV NUM_PROCS=1

ARG HOST=pypi.tuna.tsinghua.edu.cn
ARG INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt /root
COPY dist /root/dist

RUN cd /root && pip install -r requirements.txt -i $INDEX_URL --trusted-host=$HOST --no-cache-dir && \
    pip install dist/* -i $INDEX_URL --trusted-host=$HOST --no-cache-dir && \
    git clone https://githubfast.com/openai/human-eval.git && cd human-eval && \
    sed -i 's/#  / /g' human_eval/execution.py &&  \
    pip install -r requirements.txt -i $INDEX_URL --trusted-host=$HOST --no-cache-dir && pip install -e . && cd .. && \
    echo 'root:1234566' | chpasswd && \
    apt-get update && apt-get install -y openssh-server vim rsync libncurses5-dev libncursesw5-dev && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config  && \
    mkdir -p /root/.cache/huggingface && ln -s /models/huggingface/ /root/.cache/huggingface/hub && \
    apt-get clean && rm -rf /root/requirements.txt /var/lib/apt/lists/*  /root/dist

CMD ["/bin/bash", "-c", "service ssh start && /bin/bash"]
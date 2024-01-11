FROM cuda:python-3.10.13-cuda-11.7.1-cudnn8-runtime-ubuntu22.04

ENV HF_ENDPOINT="https://hf-mirror.com"

ARG HOST=pypi.tuna.tsinghua.edu.cn
ARG INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt /root
COPY install-extend.sh /root

RUN cd /root && pip install -r requirements.txt -i $INDEX_URL --trusted-host=$HOST --no-cache-dir && \
    echo 'root:1234566' | chpasswd && \
    apt-get update && apt-get install -y openssh-server git vim rsync && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config  && \
    bash install-extend.sh && \
    apt-get clean && rm -rf /root/requirements.txt /var/lib/apt/lists/*  /root/install-extend.sh

CMD ["/bin/bash", "-c", "service ssh start && /bin/bash"]

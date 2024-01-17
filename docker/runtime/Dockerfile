FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu22.04

ARG HOST=pypi.tuna.tsinghua.edu.cn
ARG INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PYTHON_VERSION=3.10.13

COPY Python-$PYTHON_VERSION.tgz /root/

RUN apt update && apt install -y build-essential zlib1g-dev libffi-dev openssl libssl-dev libsqlite3-dev git && \
    cd /root && tar -xf Python-$PYTHON_VERSION.tgz && mv Python-$PYTHON_VERSION /usr/local && \
    cd /usr/local/Python-$PYTHON_VERSION && LDFLAGS="-L/usr/local/x86_64-linux-gnu" ./configure --with-ssl --enable-loadable-sqlite-extensions && make && make install && \
    python3 -m pip install --upgrade pip -i $INDEX_URL --trusted-host=$HOST --no-cache-dir && \
    ln -s /usr/local/bin/python3 /usr/local/bin/python && \
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 -i $INDEX_URL --trusted-host=$HOST --no-cache-dir && \
    echo "/usr/lib/python3.10/lib-dynload" > /usr/local/lib/python3.10/site-packages/curses.pth && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /root/Python-$PYTHON_VERSION.tgz
镜像构建
```shell
docker build -t cuda-dev:python-3.10.13-cuda-11.7.1-cudnn8-devel-ubuntu22.04 .
```

启动
```shell
docker run -itd --gpus all --name cuda-dev  \
        -p 10022:22 -p 9000:80 \
        -v /data/lsz/workspace/py:/workspace \
        -v /data/llm/models:/models \
        -v /data/llm/datasets:/datasets \
        cuda-dev:python-3.10.13-cuda-11.7.1-cudnn8-runtime-ubuntu22.04
```
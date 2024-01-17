from opencompass.models import HuggingFaceCausalLM

models = [
    dict(
        type=HuggingFaceCausalLM,
        abbr='yuan2-51b-hf',
        path="IEITYuan/Yuan2-51B-hf",
        tokenizer_path='IEITYuan/Yuan2-51B-hf',
        tokenizer_kwargs=dict(
            padding_side='left',
            truncation_side='left',
            trust_remote_code=True,
            use_fast=False,
        ),
        pad_token_id=77185,
        max_out_len=100,
        max_seq_len=4096,
        batch_size=8,
        model_kwargs=dict(
            device_map='auto',
            trust_remote_code=True
        ),
        run_cfg=dict(num_gpus=1, num_procs=1),
    )
]
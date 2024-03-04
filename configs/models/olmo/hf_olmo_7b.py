from opencompass.models import HuggingFaceCausalLM

models = [
    dict(
        type=HuggingFaceCausalLM,
        abbr='olmo-7b',
        path="allenai/OLMo-7B",
        tokenizer_path='allenai/OLMo-7B',
        tokenizer_kwargs=dict(
            padding_side='left',
            truncation_side='left',
            trust_remote_code=True,
            use_fast=False,
        ),
        pad_token_id=1,
        max_out_len=100,
        max_seq_len=2048,
        batch_size=8,
        model_kwargs=dict(
            device_map='auto',
            trust_remote_code=True
        ),
        run_cfg=dict(num_gpus=1, num_procs=1),
    )
]
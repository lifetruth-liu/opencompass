from opencompass.models import HuggingFaceCausalLM


models = [
    dict(
        type=HuggingFaceCausalLM,
        abbr='llama-3-8b-hf',
        path="meta-llama/Llama-3-8b-hf",
        tokenizer_path='meta-llama/Llama-3-8b-hf',
        tokenizer_kwargs=dict(
            padding_side='left',
            truncation_side='left',
            trust_remote_code=True,
            use_fast=False,
        ),
        max_out_len=100,
        max_seq_len=2048,
        batch_size=8,
        model_kwargs=dict(
            device_map='auto',
            trust_remote_code=True,
        ),
        batch_padding=False, # if false, inference with for-loop without batch padding
        run_cfg=dict(num_gpus=1, num_procs=1),
    )
]

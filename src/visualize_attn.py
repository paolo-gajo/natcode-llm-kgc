import os
import json
from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaForCausalLM
import re
from typing import List
import pandas as pd
from tqdm.auto import tqdm
from datetime import datetime
from utils import *
import argparse

def main(args):
    print(f'Testing model: {args.model}')
    print(f'Testing dataset: {args.dataset}')
    print(f'Split: {args.test_split}')
    print(f'Chat model: {args.chat}')
    print(f'Rationale: {args.rationale}')
    print(f"Language: {'natlang' if args.natlang else 'code'}")

    model_name_simple = args.model.split('/')[-1]

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype='auto',
        device_map='auto',
    )
    
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    dataset_path = f'./data/codekgc-data/{args.dataset}'
    
    train_split = f'{args.train_split}_triples.json'
    train_json = os.path.join(dataset_path, train_split)

    schema_path = os.path.join(dataset_path, args.prompt_filename)

    entity2type_json = os.path.join(dataset_path, args.entitytypes)
    with open(entity2type_json, 'r', encoding='utf8') as f:
        entity2type_dict = json.load(f)

    runner = Runner(model=model,
                    type_dict=entity2type_dict,
                    natlang=args.natlang,
                    tokenizer=tokenizer,
                    chat_model=args.chat,
                    schema_path=schema_path,
                    rationale=args.rationale,
                    verbose_test=args.verbose_test,
                    model_name=args.model,
                    )
    df_train = pd.read_json(train_json).sample(n=args.n_icl_samples)
    icl_prompt = runner.make_icl_prompt(df_train)

    json_path = './data/codekgc-data/scierc/test_triples.json'
    
    with open(json_path, 'r', encoding='utf8') as f:
        test_data = json.load(f)
    
    for i, line in enumerate(test_data):
        if len(line['triple_list']) == 1 and i == 52:
            attn_list, seq, stats = runner.get_attn(model, tokenizer, line, icl_prompt,)
            if stats[-1] == 1:
                break
    savename = f"{args.model.split('/')[-1]}_test{i}"
    # for attn in attn_list:
    for j, attn in enumerate(attn_list):
        runner.heatmap2d(attn, seq, j, savename = savename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A sample argparse program")
    parser.add_argument("-m", "--model", help="Model to test")
    parser.add_argument("-d", "--dataset", help="Name of the testing dataset, options = ['ade', 'conll04', 'scierc']")
    parser.add_argument("--natlang", help="Type of language", action='store_true')
    parser.add_argument("-r", "--rationale", help="Whether to include rationale in the prompt", action='store_true')
    parser.add_argument("--chat", help="Type of model (default = completion model)", action='store_true')
    parser.add_argument("-ent", "--entitytypes", help="Filename of  the entity2type json", default='entity2type.json')
    parser.add_argument("-pf", "--prompt_filename", help="Filename of the prompt to use (code_prompt/code_expl_prompt)", default='code_prompt')
    parser.add_argument("--train_split", help="Filename of the train file to use", default='train')
    parser.add_argument("--test_split", help="Filename of the test file to use", default='test')
    parser.add_argument("--n_icl_samples", type=int, default=3, help="Number of ICL examples")
    parser.add_argument("--verbose_test", action="store_true", help="Verbose testing")
    parser.add_argument("--fine_tuned", action="store_true", help="Whether a fine-tuned LLM is beind tested")
    # parser.add_argument("--bfloat16", action="store_true", help="Whether to use bfloat16 precision for model weights")
    args = parser.parse_args()

    # args.model = "./models/Mistral-7B-v0.3_ft_scierc_natlang_rationale_steps=200_icl=3"
    args.model = "./models/Meta-Llama-3.1-8B-Instruct_ft_scierc_natlang_rationale_steps=200_icl=3"
    args.dataset = "scierc"
    args.chat = 1
    args.rationale = 1
    args.natlang = 1
    args.verbose_test = 1
    args.fine_tuned = 1
    # args.bfloat16 = 1

    main(args)
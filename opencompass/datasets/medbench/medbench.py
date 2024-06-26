import json
import os.path as osp
import sys
from datasets import Dataset
from sklearn.metrics import classification_report
from opencompass.openicl.icl_evaluator import BaseEvaluator
from opencompass.registry import ICL_EVALUATORS, LOAD_DATASET

from ..base import BaseDataset
from .math_equivalence import is_equiv
from .post_process import parse_math_answer, parse_qa_multiple_answer

import evaluate
from nltk.translate.bleu_score import sentence_bleu
# from bert_score import score
import re
from transformers import BasicTokenizer
from rouge_chinese import Rouge
basic_tokenizer = BasicTokenizer(tokenize_chinese_chars=True)

@LOAD_DATASET.register_module()
class MedBenchDataset(BaseDataset):

    @staticmethod
    def load(path: str, name: str, setting_name: str):
        from .dataset_loader import load_dataset, load_dataset_as_result_schema

        assert setting_name in 'zero-shot', 'only support zero-shot setting'
        dataset_wo_label = load_dataset(name, setting_name, path)
        dataset_with_label = load_dataset_as_result_schema(name, path)
        dataset = []
        for d1, d2 in zip(dataset_wo_label, dataset_with_label):
            dataset.append({
                'id': d2.index,
                'problem_input': d1['context'],
                'label': d2.label,
            })
        dataset = Dataset.from_list(dataset)
        return dataset


@LOAD_DATASET.register_module()
class MedBenchDataset_v2(BaseDataset):

    @staticmethod
    def load(path: str, name: str, setting_name: str):
        assert setting_name in 'zero-shot', 'only support zero-shot setting'
        filename = osp.join(path, name + '.jsonl')
        with open(filename, encoding='utf-8') as f:
            data = [json.loads(line.strip()) for line in f]
        dataset = []
        for item in data:
            passage = item['passage'] if item['passage'] else ''
            question = passage + item['question']
            options = '\n'.join(item['options']) if item['options'] else ''
            if item['label']:
                if isinstance(item['label'], list):
                    label = ''.join(item['label'])
                else:
                    label = item['label']
            else:
                label = item['answer']
            d = {'question': question, 'options': options, 'label': label}
            dataset.append(d)
        dataset = Dataset.from_list(dataset)
        return dataset


@ICL_EVALUATORS.register_module()
class MedBenchEvaluator(BaseEvaluator):

    def score(self, predictions, references):
        # predictions: [[]]
        # references: [[]]
        predictions = [parse_qa_multiple_answer(pred) for pred in predictions]
        details = []
        cnt = 0
        for pred, ref in zip(predictions, references):
            detail = {'pred': pred, 'answer': ref, 'correct': False}
            if is_equiv(pred, ref):
                cnt += 1
                detail['correct'] = True
            details.append(detail)
        score = cnt / len(predictions) * 100
        return {'Accuracy': score, 'details': details}

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_mcq(BaseEvaluator):

    def score(self, predictions, references):
        if len(predictions) != len(references):
            return {
                'error': 'predictions and references have different '
                'length'
            }
        details = []
        cnt = 0
        for pred, ref in zip(predictions, references):
            detail = {'pred': pred, 'answer': ref, 'correct': False}
            if pred == ref:
                cnt += 1
                detail['correct'] = True
            details.append(detail)

        score = cnt / len(predictions) * 100

        return {'score': score, 'details': details}

def process_generated_results_CMeEE(pred_file):
    #   实体每类占一行，每行格式为 "[类型名称]实体：实体名称1，实体名称2，实体名称3\n"
    #                多个实体，用 ，符号分割
    structured_output = []
    answer_choices = ['药物', '设备', '医院科室', '微生物类', '身体部位', '医疗操作', '医学检验项目', '症状', '疾病']
    for pred in pred_file:
        list_entities = []
        for choice in answer_choices:
            for piece in re.split('[。|；|\n]', pred):
                if piece.startswith(f"{choice}"):
                    mentions = piece.replace(f"{choice}实体为", "").replace(f"{choice}实体是", "").replace(f"{choice}实体：", "").replace(f'{choice}：', '').replace(f'{choice}:', '').split("，")
                    for ment in mentions:
                        list_entities.append({'type':choice, 'entity':ment})
        structured_output.append(list_entities)
    return structured_output

def process_generated_results_EMR(pred_file):
    structured_output = []
    answer_choices = ['主诉', '现病史', '既往史', '个人史', '婚育史', '家族史']
    for pred in pred_file:
        list_entities = []
        for choice in answer_choices:
            for piece in re.split('\n', pred):
                # if piece.startswith(f"{choice}"):
                if f"{choice}" in piece and len(piece.split(f"{choice}："))>1:
                    # mentions = piece.replace(f"{choice}：", "").split("，")
                    mentions = piece.split(f"{choice}：")[1].strip()
                    # mentions = [w.strip() for w in mentions if len(w.strip()) > 0]
                    list_entities.append({choice: mentions})
                    # for ment in mentions:
                    #     list_entities.append({choice: ment})
        structured_output.append(list_entities)
    return structured_output

def process_generated_results_CMeIE(pred_file):
    structured_output = []
    for line in pred_file:
        gen_output = line
    
        # 答案格式：
        #   每个关系类型占一行，格式为
        #         "具有{lab}关系的头尾实体对如下：头实体为str，尾实体为str；头实体为str，尾实体为str；"

        answer_choices = "相关（导致）、鉴别诊断、遗传因素、发病性别倾向、相关（症状）、手术治疗、预防、辅助检查、筛查、阶段、临床表现、风险评估因素、同义词、发病年龄、预后生存率、病史、传播途径、治疗后症状、药物治疗、辅助治疗、化疗、死亡率、放射治疗、病因、组织学检查、内窥镜检查、多发群体、并发症、实验室检查、就诊科室、病理生理、高危因素、发病率、多发地区、病理分型、影像学检查、转移部位、发病部位、相关（转化）、外侵部位、预后状况、发病机制、多发季节"
        answer_choices = answer_choices.split('、')
        list_spos = []
        assert isinstance(answer_choices, list)
        list_answer_strs = gen_output.split("\n")

        for line in list_answer_strs:
            # 首先是解析出label:
            predicate = line.split("关系的头尾实体对")[0][2: ].strip()
            line = line.replace(f"具有{predicate}关系的头尾实体对如下：", "")
            # for spo_str in line.split("。"):
            for spo_str in re.split('；|。', line):

                if len(spo_str.split("，尾实体：")) < 2:
                    continue

                head_mention_str, tail_mention_str = spo_str.split("，尾实体：")[:2]
                
                head_mention_str = head_mention_str.replace("头实体：", "").strip()
                tail_mention_str = tail_mention_str.replace("尾实体：", "").strip()
                
                list_spos.append(
                    {
                        "predicate": predicate,
                        "subject": head_mention_str,
                        "object": tail_mention_str,
                    }
                )
        structured_output.append(list_spos)
    return structured_output

def process_generated_results_CDN(pred_file):
    structured_output = []
    answer_choices = json.load(open('./opencompass/datasets/medbench/entity_list.jsonl', 'r'))
    for line in pred_file:
        gen_output = line
        
            # 答案格式：
            #   多个选中的标准化实体，用 ， 符号分割

        answer_str = gen_output.split("\n")[-1]
        answers = answer_str.split("，")
        answers = [w.strip() for w in answers if len(w.strip()) > 0]
        answers = [w for w in answers if w in answer_choices]
        answers = list(set(answers))
        answers = [
            {
                "entity": w,
                "type": "normalization",
            }
            for w in answers
        ]

        structured_output.append(answers)
    return structured_output

def process_generated_results_CDEE(pred_file):

    structured_output = []
    for line in pred_file:
        gen_output = line
            # 答案格式：
            #   第一行：引导词
            #   每个事件占一行，事件字段用 ； 分隔， 然后每个字段是 字段名：字段值的格式"
            #                                  字段值有多个，则用 ，符号分隔
        keys = ["主体词", "发生状态", "描述词", "解剖部位"]

        list_answer_strs = gen_output.split("\n")
        # list_answer_strs: ['主题词：饮食，描述词：差；', '主题词：消瘦']
        list_events = []
        for ans_str in list_answer_strs:
            if '主体词' in ans_str:
                event_info = {}
                ans_attrs = ans_str.split("，")

                for a_attr in ans_attrs:
                    for key in keys:
                        if a_attr.startswith(f"{key}："):
                            a_attr = a_attr.replace(f"{key}：", "").strip().strip('；')
                            if key in ["描述词", "解剖部位"]:
                                a_attr_split = a_attr.split("，")
                                a_attr_split = [w.strip() for w in a_attr_split if len(w.strip()) > 0]
                                event_info[key] = a_attr_split
                            else:
                                event_info[key] = a_attr

                for key in keys:
                    if key not in event_info:
                        if key in ["描述词", "解剖部位"]:
                            event_info[key] = []
                        else:
                            event_info[key] = ""

                list_events.append(event_info)

        structured_output.append(list_events)
    return structured_output

def process_generated_results_CTC(pred_file):
    structured_output = []

    for line in pred_file:
        gen_output = line
        # 答案格式：直接回答分类标签
        answer_str = gen_output.strip()
        structured_output.append(answer_str)
    return structured_output

def process_generated_results_doc_parsing(pred_file):
    output = []
    for line in pred_file:
        structured_output = []
        sentence_list = line.strip().split('\n')
        for sentence in sentence_list:
            if '体温' in sentence:
                temp_value = re.search('[0-9]+.[0-9]', sentence)
                if temp_value:
                    structured_output.append({'type':'体温', 'entity':temp_value.group(0)})
                else:
                    structured_output.append({'type':'体温', 'entity':'未扪及'})
            elif '脉搏' in sentence:
                temp_value = re.search('[0-9]+.[0-9]', sentence)
                if temp_value:
                    structured_output.append({'type':'脉搏', 'entity':temp_value.group(0)})
                else:
                    structured_output.append({'type':'脉搏', 'entity':'未扪及'})
            elif '心率' in sentence:
                temp_value = re.search('[0-9]+.[0-9]', sentence)
                if temp_value:
                    structured_output.append({'type':'心率', 'entity':temp_value.group(0)})
                else:
                    structured_output.append({'type':'心率', 'entity':'未扪及'})
            elif '收缩压' in sentence:
                temp_value = re.search('[0-9]+.[0-9]', sentence)
                if temp_value:
                    structured_output.append({'type':'收缩压', 'entity':temp_value.group(0)})
                else:
                    structured_output.append({'type':'收缩压', 'entity':'未扪及'})
            elif '舒张压' in sentence:
                temp_value = re.search('[0-9]+.[0-9]', sentence)
                if temp_value:
                    structured_output.append({'type':'舒张压', 'entity':temp_value.group(0)})
                else:
                    structured_output.append({'type':'舒张压', 'entity':'未扪及'})
            elif '呼吸' in sentence:
                temp_value = re.search('[0-9]+.[0-9]', sentence)
                if temp_value:
                    structured_output.append({'type':'呼吸', 'entity':temp_value.group(0)})
                else:
                    structured_output.append({'type':'呼吸', 'entity':'未扪及'})
            elif '上腹部深压痛' in sentence:
                if re.search('未|不|没|无', sentence):
                    structured_output.append({'type':'上腹部深压痛', 'entity':'否是'})
                else:
                    structured_output.append({'type':'上腹部深压痛', 'entity':'是'})
            elif '腹部反跳痛' in sentence:
                if re.search('未|不|没|无', sentence):
                    structured_output.append({'type':'腹部反跳痛', 'entity':'否'})
                else:
                    structured_output.append({'type':'腹部反跳痛', 'entity':'是'})
            elif '上腹部肿块' in sentence:
                if re.search('未|不|没|无', sentence):
                    structured_output.append({'type':'上腹部肿块', 'entity':'未扪及'})
                else:
                    structured_output.append({'type':'上腹部肿块', 'entity':'扪及'})
        output.append(structured_output)
    return output

def process_generated_results_mrg(pred_file):
    structured_output = []
    answer_choices = ['主诉', '现病史', '既往史', '辅助检查', '诊断']
    for pred in pred_file:
        list_entities = []
        for choice in answer_choices:
            if '\n\n' in pred['answer']:
                for piece in re.split('\n\n', pred['answer']):
                    if f"{choice}" in piece and len(piece.split(f"{choice}："))>1:
                        mentions = piece.split(f"{choice}：")[1].strip()
                        list_entities.append({choice:mentions})
            else:
                for piece in re.split('\n', pred):
                    if piece.startswith(f"{choice}："):
                        mentions = piece.replace(f"{choice}：", "").split("，")
                        mentions = [w.strip() for w in mentions if len(w.strip()) > 0]
                        for ment in mentions:
                            list_entities.append({choice:ment})
        structured_output.append(list_entities)
    return structured_output

def calc_info_extract_task_scores(list_structured_predict, list_structured_golden):

    assert len(list_structured_golden) == len(list_structured_predict)

    tp = 0
    fp = 0
    fn = 0
    for samp_golden, samp_predict in zip(list_structured_golden, list_structured_predict):
        # samp_golden: [[{}]]
        answer_golden = samp_golden
        answer_predict = samp_predict
        # assert isinstance(answer_golden, list)
        # assert isinstance(answer_predict, list), "sample format is wrong!"

        set_golden = set()
        for inst in answer_golden:
            assert isinstance(inst, dict)
            keys = sorted(list(inst.keys()))
            inst = tuple([json.dumps(inst[w], ensure_ascii=False) for w in keys ])
            # inst = list(inst.items())
            # inst.sort()
            # inst = tuple(inst)

            set_golden.add(inst)

        set_predict = set()
        for inst in answer_predict:
            assert isinstance(inst, dict)
            keys = sorted(list(inst.keys()))

            inst = tuple([json.dumps(inst[w], ensure_ascii=False) for w in keys])

            set_predict.add(inst)

        tp += len(set_golden.intersection(set_predict))
        fp += len(set_predict.difference(set_golden))
        fn += len(set_golden.difference(set_predict))

    if tp:
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        f1 = 2 * precision * recall / (precision + recall)

    else:
        precision, recall, f1 = 0, 0, 0

    return precision, recall, f1

def calc_cls_task_scores(list_structured_golden,
                         list_structured_predict,
                         list_labels=None,
                         return_macro=False,
                         ):
    # types = list_labels
    # scores = {c: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for c in list_labels + ["ALL"]}

    predictions = []
    ground_truths = []

    # Count GT relations and Predicted relations
    assert len(list_structured_golden) == len(list_structured_predict)
    n_sents = len(list_structured_golden)

    # Count TP, FP and FN per type
    for pred_samp, gt_samp in zip(list_structured_predict, list_structured_golden):

        pred_label = pred_samp
        gt_label = gt_samp
        # assert gt_label != ""
        if gt_label == "":
            get_label = list_labels[0]
        if pred_label == "":
            pred_label = list_labels[0]

        predictions.append(pred_label)
        ground_truths.append(gt_label)

    # metric
    cls_report = classification_report(
        ground_truths, predictions,
        output_dict=True,
        zero_division=0,
    )

    if return_macro:
        return cls_report["macro avg"]["precision"], \
               cls_report["macro avg"]["recall"], \
               cls_report["macro avg"]["f1-score"]
    else:
        return cls_report["weighted avg"]["precision"], \
               cls_report["weighted avg"]["recall"], \
               cls_report["weighted avg"]["f1-score"]

def calc_nlg_task_scores(list_structured_golden, list_structured_predict):

    assert len(list_structured_golden) == len(list_structured_predict)

    scores = []
    predictions = []
    references = []
    details = []
    for samp_golden, samp_predict in zip(list_structured_golden, list_structured_predict):

        answer_golden = samp_golden
        answer_predict = samp_predict

        if not (answer_predict and answer_golden):
            continue

        # basic tokenizer: 拆分中文字，保留英文单词
        answer_predict = basic_tokenizer.tokenize(answer_predict)
        answer_golden = basic_tokenizer.tokenize(answer_golden)
        answer_predict = " ".join(answer_predict).strip()
        answer_golden = " ".join(answer_golden).strip()
        if answer_golden.strip() == "":
            answer_golden = "无 。"
        if answer_predict.strip() == "":
            answer_predict = "无 。"

        predictions.append(answer_predict)
        references.append(answer_golden)

        details.append({'pred':answer_predict, 'answer':answer_golden, 'correct':False})

    rouge = Rouge()
    # bleu = evaluate.load('sacrebleu')
    scores = rouge.get_scores(predictions, references, avg=True)
    # scores_bleu = bleu.compute(predictions=predictions, references=references)

    rouge1 = scores["rouge-1"]["f"]
    rouge2 = scores["rouge-2"]["f"]
    rougeL = scores["rouge-l"]["f"]

    # bleu = sentence_bleu(references, predictions)

    # bert_score = []
    # for id in range(len(predictions)):
    #     P, R, F1 = score([predictions[i]], [references[i]], model_type='bert-base-chinese', lang="zh", verbose=True)
    #     bert_score.append(F1)
    # bert_score = float(sum(bert_score)) / float(len(bert_score))
    # return rougeL, bleu, bert_score
    return {'RougeL': rougeL, 'details':details}

def calc_scores_f1(dict_gt, dict_pred):
        details = []
        for gt, pred in zip(dict_gt, dict_pred):
            details.append({'pred':pred, 'answer':gt, 'correct':None})
        
        precision, recall, f1 = calc_info_extract_task_scores(dict_gt, dict_pred)
        return {'F1':f1, 'details':details}

def calc_scores_ctc(dict_gt, dict_pred):
    details = []
    for gt, pred in zip(dict_gt, dict_pred):
        details.append({'pred':pred, 'answer':gt, 'correct':None})

    gts = dict_gt
    preds = dict_pred
    
    precision, recall, f1 = calc_cls_task_scores(
        gts,
        preds,
        list_labels=['非上述类型', '疾病', '症状(患者感受)',
                    '体征(医生检测）', '怀孕相关', '肿瘤进展',
                    '疾病分期', '过敏耐受', '器官组织状态',
                    '预期寿命', '口腔相关', '药物',
                    '治疗或手术', '设备', '护理',
                    '诊断', '实验室检查', '风险评估',
                    '受体状态', '年龄', '特殊病人特征',
                    '读写能力', '性别', '教育情况',
                    '居住情况', '种族', '知情同意',
                    '参与其它试验', '研究者决定', '能力',
                    '伦理审查', '依存性', '成瘾行为',
                    '睡眠', '锻炼', '饮食', '酒精使用',
                    '性取向', '吸烟状况', '献血',
                    '病例来源', '残疾群体', '健康群体',
                    '数据可及性', "含有多个类别"],
        return_macro=True,
    )
    return {'Macro-F1':f1, 'details':details}
    
def calc_scores_nlg(dict_gt, dict_pred):
    
        # scores = {}
        scores = {'score':0, 'details':[]}
        success_flag = 1

        gts = dict_gt
        preds = dict_pred
        # if not len(gts) == len(preds):
        #     success_flag = 0
        # try:
        return calc_nlg_task_scores(gts, preds)    

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_CMeEE(BaseEvaluator):

    def score(self, predictions, references):
        predictions = process_generated_results_CMeEE(predictions)
        return calc_scores_f1(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_DBMHG(BaseEvaluator):

    def score(self, predictions, references):
        predictions = process_generated_results_EMR(predictions)
        return calc_scores_f1(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_IMCS_V2_MRG(BaseEvaluator):

    def score(self, predictions, references):
        predictions = process_generated_results_mrg(predictions)
        return calc_scores_f1(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_CMeIE(BaseEvaluator):

    def score(self, predictions, references):
        predictions = process_generated_results_CMeIE(predictions)
        return calc_scores_f1(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_CHIP_CDEE(BaseEvaluator):

    def score(self, predictions, references):
        predictions = process_generated_results_CDEE(predictions)
        return calc_scores_f1(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_CHIP_CDN(BaseEvaluator):

    def score(self, predictions, references):
        predictions = process_generated_results_CDN(predictions)
        return calc_scores_f1(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_CHIP_CTC(BaseEvaluator):

    def score(self, predictions, references):
        predictions = process_generated_results_CTC(predictions)
        return calc_scores_ctc(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_SMDoc(BaseEvaluator):

    def score(self, predictions, references):
        predictions = process_generated_results_doc_parsing(predictions)
        return calc_scores_f1(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_NLG(BaseEvaluator):

    def score(self, predictions, references):
        return calc_scores_nlg(predictions, references)

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_Cloze(BaseEvaluator):

    def score(self, predictions, references):
        erke_list = ["血管外科", "临床心理科", "生殖医学中心", "肿瘤科", "妇科", "小儿风湿免疫科", "放射科", "小儿内分泌代谢科", "急诊科", "心血管内科", "小儿神经内科", "感染科", "整形外科", "全科医学科", "泌尿外科", "皮肤科", "消化内科", "口腔科", "小儿心脏中心", "产科", "血液内科", "小儿普外科", "小儿泌尿外科", "小儿感染科", "临床营养科", "小儿骨科", "发育行为儿童保健科", "小儿呼吸内科", "神经外科", "内分泌代谢科", "普外科", "肛肠外科", "小儿神经外科", "康复医学科", "骨科", "风湿免疫科", "小儿内科", "眼科", "心胸外科", "小儿肾脏内科", "乳腺外科", "小儿血液肿瘤科", "体检中心", "神经内科", "耳鼻咽喉头颈外科", "小儿消化内科", "呼吸内科", "核医学科", "肾脏内科"]
        no_erke_list = ["血管外科", "临床心理科", "生殖医学中心", "肿瘤科", "妇科", "放射科", "急诊科", "心血管内科", "感染科", "整形外科", "全科医学科", "泌尿外科", "皮肤科", "消化内科", "口腔科", "产科", "血液内科", "临床营养科", "神经外科", "内分泌代谢科", "普外科", "肛肠外科", "康复医学科", "骨科", "风湿免疫科", "眼科", "心胸外科", "乳腺外科", "体检中心", "神经内科", "耳鼻咽喉头颈外科", "呼吸内科", "核医学科", "肾脏内科"]
        
        cross_erke_list = [item for item in erke_list if '小儿' in item and item.replace('小儿', '') in no_erke_list]
        cross_list = [item[2:] for item in cross_erke_list]

        details = []
        cnt = 0

        for pred, ref in zip(predictions, references):
            detail = {'pred':pred, 'answer':ref, 'correct':False}
            current_pred = []
            for x in cross_list:
                if '小儿' + x in predictions:
                    current_pred.append('小儿' + x)
                elif x in predictions:
                    current_pred.append(x)

            for x in (set(erke_list + no_erke_list) - set(cross_erke_list) - set(cross_list)):
                if x in predictions:
                    current_pred.append(x)

            # if set([x for x in erke_list + no_erke_list if x in pred]) == set(ref):
            if set(current_pred) == set(ref):
                cnt += 1
                detail['correct'] = True
            details.append(detail)
        score = cnt / len(predictions) * 100
        return {'Accuracy': score, 'details': details}

@ICL_EVALUATORS.register_module()
class MedBenchEvaluator_TF(BaseEvaluator):

    def score(self, predictions, references):
        # predictions: [[]]
        # references: [[]]
        # predictions = [parse_qa_multiple_answer(pred) for pred in predictions]
        details = []
        cnt = 0

        for pred, ref in zip(predictions, references):
            
            if '不' in pred or '否' in pred:
                cur_pred = '不可以'
            else:
                cur_pred = '可以'

            detail = {'pred':cur_pred, 'answer':ref, 'correct':False}

            if cur_pred == ref:
                cnt += 1
                detail['correct'] = True
            
            details.append(detail)

        score = cnt / len(predictions) * 100
        return {'Accuracy': score, 'details': details}